# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    esi_operator_id = fields.Many2one('esi.mrp.operator', string='Operador real', check_company=True)
    esi_area = fields.Char(string='Área / Etapa')
    esi_qty_processed = fields.Float(string='Cantidad procesada', digits='Product Unit of Measure')
    esi_piece_rate = fields.Float(string='Destajo por par', digits=(16, 4))
    esi_piece_amount = fields.Float(string='Importe destajo', compute='_compute_esi_piece_amount', store=True, digits=(16, 4))
    esi_source = fields.Selection([
        ('manual', 'Manual'),
        ('demo', 'Demo ESI'),
        ('workorder', 'Orden de trabajo'),
    ], string='Origen', default='manual')

    @api.depends('esi_qty_processed', 'esi_piece_rate')
    def _compute_esi_piece_amount(self):
        for line in self:
            line.esi_piece_amount = (line.esi_qty_processed or 0.0) * (line.esi_piece_rate or 0.0)

    @api.onchange('workorder_id')
    def _onchange_esi_workorder(self):
        for line in self:
            wo = line.workorder_id
            if wo:
                line.esi_operator_id = wo.esi_operator_id
                line.esi_area = wo.esi_area
                line.esi_piece_rate = wo.esi_piece_rate
                line.esi_qty_processed = wo.qty_produced or wo.qty_production
