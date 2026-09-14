# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    esi_operator_id = fields.Many2one(
        'esi.mrp.operator', string='Operador real', check_company=True)
    esi_area = fields.Char(string='Área / Etapa')
    esi_qty_processed = fields.Float(
        string='Cantidad procesada', digits='Product Unit of Measure')
    esi_piece_rate = fields.Float(string='Destajo por par', digits=(16, 4))
    esi_piece_amount = fields.Float(
        string='Importe destajo', compute='_compute_esi_piece_amount',
        store=True, digits=(16, 4))
    esi_source = fields.Selection([
        ('manual', 'Manual'),
        ('demo', 'Demo ESI'),
        ('workorder', 'Orden de trabajo'),
    ], string='Origen', default='manual')

    @api.depends('esi_qty_processed', 'esi_piece_rate')
    def _compute_esi_piece_amount(self):
        for line in self:
            line.esi_piece_amount = (
                (line.esi_qty_processed or 0.0) * (line.esi_piece_rate or 0.0)
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Completar datos ESI también cuando Odoo crea el tiempo automáticamente.

        El botón estándar ``Empezar a trabajar`` crea directamente un registro
        ``mrp.workcenter.productivity``. En ese flujo no se ejecuta el onchange
        del formulario, por eso las versiones anteriores dejaban Operador real,
        Área, Destajo y Cantidad en blanco/0.

        Aquí copiamos los metadatos de la orden de trabajo. La cantidad se deja
        inicialmente en 0 para no duplicar el destajo cuando el operario pausa y
        reanuda varias veces. La cantidad se asigna al registrar producción o al
        finalizar la orden de trabajo.
        """
        prepared = []
        for original_vals in vals_list:
            vals = dict(original_vals)
            workorder_id = vals.get('workorder_id') or self.env.context.get('default_workorder_id')
            if workorder_id:
                wo = self.env['mrp.workorder'].browse(workorder_id).exists()
                if wo:
                    if not vals.get('esi_operator_id') and wo.esi_operator_id:
                        vals['esi_operator_id'] = wo.esi_operator_id.id
                    if not vals.get('esi_area') and wo.esi_area:
                        vals['esi_area'] = wo.esi_area
                    if 'esi_piece_rate' not in vals:
                        vals['esi_piece_rate'] = wo.esi_piece_rate or 0.0
                    # No copiar toda la cantidad aquí: cada pausa/reanudación
                    # genera una línea y se duplicaría el destajo.
                    vals.setdefault('esi_qty_processed', 0.0)
                    vals.setdefault('esi_source', 'workorder')
            prepared.append(vals)
        return super(MrpWorkcenterProductivity, self).create(prepared)

    def copy(self, default=None):
        """Evitar duplicar cantidad/destajo cuando Odoo divide una línea de tiempo.

        Odoo 13 puede copiar una línea productiva al separar tiempo productivo y
        pérdida de rendimiento. Si copiáramos también la cantidad procesada,
        tendríamos el mismo destajo dos veces.
        """
        self.ensure_one()
        default = dict(default or {})
        if self.esi_source == 'workorder':
            default.setdefault('esi_qty_processed', 0.0)
        return super(MrpWorkcenterProductivity, self).copy(default)

    @api.onchange('workorder_id')
    def _onchange_esi_workorder(self):
        for line in self:
            wo = line.workorder_id
            if wo:
                line.esi_operator_id = wo.esi_operator_id
                line.esi_area = wo.esi_area
                line.esi_piece_rate = wo.esi_piece_rate
                # En carga manual sí sugerimos la cantidad actual. Al guardar
                # puede modificarse si se está registrando sólo una parte.
                line.esi_qty_processed = wo.qty_produced or wo.qty_production

    @api.model
    def esi_backfill_from_workorders(self):
        """Reparar líneas antiguas creadas antes de esta corrección.

        Se ejecuta al instalar/actualizar el módulo y es idempotente. Completa
        Operador/Área/Tarifa faltantes. En órdenes ya terminadas que no tengan
        ninguna cantidad ESI registrada, asigna el total una sola vez a la última
        línea productiva, evitando duplicar importes.
        """
        lines = self.search([
            ('workorder_id', '!=', False),
            '|', '|', '|',
            ('esi_operator_id', '=', False),
            ('esi_area', 'in', [False, '']),
            ('esi_piece_rate', '=', 0.0),
            ('esi_source', '=', 'manual'),
        ])
        touched_wos = self.env['mrp.workorder']

        for line in lines:
            wo = line.workorder_id
            if not wo:
                continue
            vals = {}
            if not line.esi_operator_id and wo.esi_operator_id:
                vals['esi_operator_id'] = wo.esi_operator_id.id
            if not line.esi_area and wo.esi_area:
                vals['esi_area'] = wo.esi_area
            if not line.esi_piece_rate and wo.esi_piece_rate:
                vals['esi_piece_rate'] = wo.esi_piece_rate
            # Si faltaban datos ESI y es una línea vinculada a WO, se considera
            # una línea automática histórica del flujo de trabajo.
            if line.esi_source == 'manual' and vals:
                vals['esi_source'] = 'workorder'
            if vals:
                line.write(vals)
                touched_wos |= wo

        # Completar cantidad/destajo de órdenes ya terminadas sólo cuando no se
        # registró ninguna cantidad ESI previamente (manual o demo).
        for wo in touched_wos.filtered(lambda w: w.state == 'done'):
            all_lines = wo.time_ids
            if not all_lines:
                continue
            already_qty = sum(all_lines.mapped('esi_qty_processed'))
            if already_qty:
                continue
            candidates = all_lines.filtered(
                lambda l: l.esi_source != 'demo' and
                l.loss_type in ('productive', 'performance')
            ).sorted(key=lambda l: l.id)
            if not candidates:
                continue
            target_qty = wo.qty_produced or wo.qty_production or 0.0
            if target_qty > 0:
                target = candidates[-1]
                target.write({
                    'esi_operator_id': target.esi_operator_id.id or (wo.esi_operator_id.id if wo.esi_operator_id else False),
                    'esi_area': target.esi_area or wo.esi_area,
                    'esi_piece_rate': target.esi_piece_rate or wo.esi_piece_rate,
                    'esi_qty_processed': target_qty,
                    'esi_source': 'workorder',
                })
        return True
