# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import float_compare


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    esi_operator_id = fields.Many2one(
        'esi.mrp.operator', string='Operador', check_company=True,
        compute='_compute_esi_operation_defaults', store=True, readonly=False)
    esi_area = fields.Char(
        string='Área / Etapa', compute='_compute_esi_operation_defaults',
        store=True, readonly=False)
    esi_standard_seconds = fields.Float(
        string='Tiempo estándar (seg/par)', compute='_compute_esi_operation_defaults',
        store=True, readonly=False, digits=(16, 4))
    esi_piece_rate = fields.Float(
        string='Destajo por par', compute='_compute_esi_operation_defaults',
        store=True, readonly=False, digits=(16, 4))
    esi_piece_qty = fields.Float(
        string='Cantidad para destajo', compute='_compute_esi_piece_amount',
        store=True, readonly=False, digits='Product Unit of Measure')
    esi_piece_amount = fields.Float(
        string='Importe destajo', compute='_compute_esi_piece_amount',
        store=True, digits=(16, 4))

    @api.depends(
        'operation_id', 'operation_id.esi_operator_id', 'operation_id.esi_area',
        'operation_id.esi_standard_seconds', 'operation_id.esi_piece_rate')
    def _compute_esi_operation_defaults(self):
        for wo in self:
            operation = wo.operation_id
            if operation:
                wo.esi_operator_id = operation.esi_operator_id
                wo.esi_area = operation.esi_area
                wo.esi_standard_seconds = operation.esi_standard_seconds
                wo.esi_piece_rate = operation.esi_piece_rate
            else:
                wo.esi_operator_id = False
                wo.esi_area = False
                wo.esi_standard_seconds = 0.0
                wo.esi_piece_rate = 0.0

    @api.depends('qty_produced', 'qty_production', 'esi_piece_rate')
    def _compute_esi_piece_amount(self):
        for wo in self:
            qty = wo.qty_produced or wo.qty_production or 0.0
            wo.esi_piece_qty = qty
            wo.esi_piece_amount = qty * (wo.esi_piece_rate or 0.0)

    def _esi_complete_time_metadata(self):
        """Completar metadatos ESI en líneas de tiempo de estas WO."""
        for wo in self:
            for line in wo.time_ids.filtered(lambda l: l.esi_source != 'demo'):
                vals = {}
                if not line.esi_operator_id and wo.esi_operator_id:
                    vals['esi_operator_id'] = wo.esi_operator_id.id
                if not line.esi_area and wo.esi_area:
                    vals['esi_area'] = wo.esi_area
                if not line.esi_piece_rate and wo.esi_piece_rate:
                    vals['esi_piece_rate'] = wo.esi_piece_rate
                if line.esi_source == 'manual' and vals:
                    vals['esi_source'] = 'workorder'
                if vals:
                    line.write(vals)
        return True

    def _esi_allocate_piecework_until(self, target_qty=None):
        """Asignar sólo la cantidad aún no contabilizada a la última línea.

        Esto evita pagar dos veces el destajo si el operario pausa/reanuda o si
        ya existe un parte DEMO con producción parcial.
        """
        for wo in self:
            wo._esi_complete_time_metadata()

            if target_qty is None:
                target = wo.qty_produced or wo.qty_production or 0.0
            else:
                target = target_qty

            all_lines = wo.time_ids
            already = sum(all_lines.mapped('esi_qty_processed'))
            rounding = (wo.product_uom_id.rounding or 0.01) if wo.product_uom_id else 0.01
            remaining = max((target or 0.0) - (already or 0.0), 0.0)
            if float_compare(remaining, 0.0, precision_rounding=rounding) <= 0:
                continue

            candidates = all_lines.filtered(
                lambda l: l.esi_source != 'demo' and
                l.loss_type in ('productive', 'performance')
            ).sorted(key=lambda l: l.id)
            if not candidates:
                continue

            # Preferir la última línea: normalmente es la que Odoo acaba de cerrar
            # con el botón Hecho/Finalizar.
            line = candidates[-1]
            line.write({
                'esi_operator_id': line.esi_operator_id.id or (wo.esi_operator_id.id if wo.esi_operator_id else False),
                'esi_area': line.esi_area or wo.esi_area,
                'esi_piece_rate': line.esi_piece_rate or wo.esi_piece_rate,
                'esi_qty_processed': (line.esi_qty_processed or 0.0) + remaining,
                'esi_source': 'workorder',
            })
        return True

    def button_start(self):
        res = super(MrpWorkorder, self).button_start()
        # create() de mrp.workcenter.productivity ya copia los datos; esta pasada
        # también cubre líneas creadas por personalizaciones de terceros.
        self._esi_complete_time_metadata()
        return res

    def record_production(self):
        """Registrar destajo acumulado cuando se produce parcialmente."""
        res = super(MrpWorkorder, self).record_production()
        for wo in self:
            # qty_produced ya contiene la producción acumulada después del super.
            wo._esi_allocate_piecework_until(wo.qty_produced or 0.0)
        return res

    def button_finish(self):
        res = super(MrpWorkorder, self).button_finish()
        for wo in self:
            target_qty = wo.qty_produced or wo.qty_production or 0.0
            wo._esi_allocate_piecework_until(target_qty)
        return res

    def button_done(self):
        res = super(MrpWorkorder, self).button_done()
        for wo in self:
            target_qty = wo.qty_produced or wo.qty_production or 0.0
            wo._esi_allocate_piecework_until(target_qty)
        return res
