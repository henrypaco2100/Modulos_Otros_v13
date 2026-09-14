# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    esi_operator_id = fields.Many2one('esi.mrp.operator', string='Operador estándar', check_company=True)
    esi_area = fields.Char(string='Área / Etapa', index=True)
    esi_standard_seconds = fields.Float(string='Tiempo promedio (seg/par)', digits=(16, 4))
    esi_standard_minutes = fields.Float(string='Tiempo promedio (min/par)', compute='_compute_esi_piecework', store=True, digits=(16, 6))
    esi_labor_cost_pair = fields.Float(string='Costo técnico por par', compute='_compute_esi_piecework', store=True, digits=(16, 6))
    esi_piece_rate = fields.Float(string='Pago destajo por par', digits=(16, 4))
    esi_batch_qty = fields.Float(string='Cantidad serie', default=50.0)
    esi_batch_minutes = fields.Float(string='Tiempo serie (min)', compute='_compute_esi_piecework', store=True, digits=(16, 4))
    esi_batch_cost = fields.Float(string='Costo técnico serie', compute='_compute_esi_piecework', store=True, digits=(16, 4))
    esi_piecework_batch_amount = fields.Float(string='Destajo serie', compute='_compute_esi_piecework', store=True, digits=(16, 4))
    esi_measurement_status = fields.Selection([
        ('measured', 'Medido'),
        ('pending', 'Pendiente de medición'),
        ('estimated', 'Estimado'),
    ], string='Estado de medición', default='measured', required=True)
    esi_source_sheet = fields.Char(string='Hoja de origen')
    esi_source_row = fields.Integer(string='Fila de origen')
    esi_source_note = fields.Char(string='Fuente / Nota')

    @api.depends('esi_standard_seconds', 'esi_batch_qty', 'esi_piece_rate', 'workcenter_id.costs_hour')
    def _compute_esi_piecework(self):
        for operation in self:
            minutes = (operation.esi_standard_seconds or 0.0) / 60.0
            operation.esi_standard_minutes = minutes
            cost_hour = operation.workcenter_id.costs_hour or 0.0
            operation.esi_labor_cost_pair = (minutes / 60.0) * cost_hour
            operation.esi_batch_minutes = minutes * (operation.esi_batch_qty or 0.0)
            operation.esi_batch_cost = operation.esi_labor_cost_pair * (operation.esi_batch_qty or 0.0)
            operation.esi_piecework_batch_amount = (operation.esi_piece_rate or 0.0) * (operation.esi_batch_qty or 0.0)

    @api.onchange('esi_standard_seconds')
    def _onchange_esi_standard_seconds(self):
        for operation in self:
            if operation.esi_standard_seconds:
                operation.time_mode = 'manual'
                operation.time_cycle_manual = operation.esi_standard_seconds / 60.0
