# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    esi_avg_monthly_labor_cost = fields.Float(string='Costo laboral promedio mensual', default=3300.0)
    esi_workdays_month = fields.Float(string='Días laborales/mes', default=26.0)
    esi_hours_day = fields.Float(string='Horas laborales/día', default=8.0)
    esi_reference_pairs_day = fields.Float(
        string='Referencia pares/día/persona',
        default=5.0,
        help='Referencia tomada de la hoja de cálculo entregada; es informativa y no limita la producción.',
    )
    esi_cost_day = fields.Float(
        string='Costo laboral promedio/día', compute='_compute_esi_labor_costs', store=True, digits=(16, 6)
    )
    esi_cost_hour = fields.Float(
        string='Costo laboral promedio/hora', compute='_compute_esi_labor_costs', store=True, digits=(16, 6)
    )
    esi_cost_minute = fields.Float(
        string='Costo laboral promedio/minuto', compute='_compute_esi_labor_costs', store=True, digits=(16, 6)
    )

    @api.depends('esi_avg_monthly_labor_cost', 'esi_workdays_month', 'esi_hours_day')
    def _compute_esi_labor_costs(self):
        for company in self:
            workdays = company.esi_workdays_month or 0.0
            hours = company.esi_hours_day or 0.0
            company.esi_cost_day = (company.esi_avg_monthly_labor_cost / workdays) if workdays else 0.0
            company.esi_cost_hour = (company.esi_cost_day / hours) if hours else 0.0
            company.esi_cost_minute = (company.esi_cost_hour / 60.0) if company.esi_cost_hour else 0.0
