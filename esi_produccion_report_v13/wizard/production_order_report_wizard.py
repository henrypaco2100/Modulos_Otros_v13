# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class EsiProductionOrderReportWizard(models.TransientModel):
    _name = 'esi.production.order.report.wizard'
    _description = 'ESI - Reportes por Orden de Producción'

    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company
    )
    production_id = fields.Many2one(
        'mrp.production', string='Orden de producción', required=True,
        domain="[('company_id', '=', company_id), ('state', '!=', 'cancel')]"
    )
    report_type = fields.Selection([
        ('cost', 'Ficha de costo de producción'),
        ('shortage', 'Faltantes de materiales y costo'),
        ('piecework', 'Resumen de destajos de la OF'),
        ('analysis', 'Análisis de producción ESI'),
    ], string='Reporte', required=True, default='cost')

    def action_print_pdf(self):
        self.ensure_one()
        if not self.production_id:
            raise UserError(_('Seleccione una orden de producción.'))
        report_xmlids = {
            'cost': 'esi_produccion_report_v13.action_report_esi_production_cost',
            'shortage': 'esi_produccion_report_v13.action_report_esi_material_shortage',
            'piecework': 'esi_produccion_report_v13.action_report_esi_destajo_mo',
            'analysis': 'esi_produccion_report_v13.action_report_esi_production_detail',
        }
        action = self.env.ref(report_xmlids[self.report_type])
        return action.report_action(self.production_id)
