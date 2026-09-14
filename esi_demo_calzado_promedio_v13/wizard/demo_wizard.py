# -*- coding: utf-8 -*-
from odoo import fields, models, _


class EsiDemoCalzadoPromedioWizard(models.TransientModel):
    _name = 'esi.demo.calzado.promedio.wizard'
    _description = 'Cargar / actualizar demo de calzado ESI AVCO'

    result = fields.Text(string='Resultado', readonly=True)

    def action_run(self):
        self.ensure_one()
        data = self.env['esi.demo.calzado.promedio.loader'].sudo().with_context(
            esi_demo_request_uid=self.env.user.id
        ).run_demo()
        lines = [
            _('Demo ESI de calzado AVCO cargada/actualizada correctamente.'),
            _('Compañía: %s') % data.get('company_name', ''),
            _('Operadores: %s') % data.get('operators', 0),
            _('Centros de trabajo: %s') % data.get('workcenters', 0),
            _('Operaciones Bota de Lona: %s') % data.get('lona_operations', 0),
            _('Operaciones Bota Industrial: %s') % data.get('industrial_operations', 0),
            _('Apuntes adicionales de destajo: %s (Total Bs %.2f)') % (
                data.get('piecework_notes', 0), data.get('piecework_notes_total', 0.0)),
            _('Productos: %s') % data.get('products', 0),
            _('Órdenes de fabricación demo: %s') % data.get('manufacturing_orders', 0),
            _('Compras demo: %s') % data.get('purchase_orders', 0),
            _('Recepciones de compra validadas: %s') % data.get('received_pickings', 0),
            _('Método de coste: %s') % data.get('cost_method', ''),
            _('Costos promedio de muestra: %s') % ', '.join(data.get('avco_samples', [])),
            _('Ventas demo: %s') % data.get('sale_orders', 0),
            _('Asientos demo: %s') % data.get('account_moves', 0),
            '',
            _('Nota AVCO: las compras 001 y 002 están recibidas; la compra 003 queda confirmada y pendiente para demostrar en vivo cómo cambia el costo promedio al validar su recepción.'),
            _('Nota producción: los tiempos dañados/#REF! de BOTA INDUSTRIAL se conservaron como pendientes de medición; no se inventaron valores.'),
        ]
        self.result = '\n'.join(lines)
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
