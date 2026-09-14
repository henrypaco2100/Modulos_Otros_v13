# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    esi_operator_id = fields.Many2one('esi.mrp.operator', string='Operador', check_company=True, compute='_compute_esi_operation_defaults', store=True, readonly=False)
    esi_area = fields.Char(string='Área / Etapa', compute='_compute_esi_operation_defaults', store=True, readonly=False)
    esi_standard_seconds = fields.Float(string='Tiempo estándar (seg/par)', compute='_compute_esi_operation_defaults', store=True, readonly=False, digits=(16, 4))
    esi_piece_rate = fields.Float(string='Destajo por par', compute='_compute_esi_operation_defaults', store=True, readonly=False, digits=(16, 4))
    esi_piece_qty = fields.Float(string='Cantidad para destajo', compute='_compute_esi_piece_amount', store=True, readonly=False, digits='Product Unit of Measure')
    esi_piece_amount = fields.Float(string='Importe destajo', compute='_compute_esi_piece_amount', store=True, digits=(16, 4))

    @api.depends('operation_id', 'operation_id.esi_operator_id', 'operation_id.esi_area', 'operation_id.esi_standard_seconds', 'operation_id.esi_piece_rate')
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
