# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    esi_piecework_total = fields.Float(string='Destajo total', compute='_compute_esi_time_piecework', digits=(16, 4))
    esi_time_part_count = fields.Integer(string='Partes de producción', compute='_compute_esi_time_piecework')
    esi_actual_minutes = fields.Float(string='Minutos reales registrados', compute='_compute_esi_time_piecework', digits=(16, 2))

    def _compute_esi_time_piecework(self):
        for production in self:
            lines = production.workorder_ids.mapped('time_ids')
            production.esi_piecework_total = sum(lines.mapped('esi_piece_amount')) if lines else 0.0
            production.esi_time_part_count = len(lines)
            production.esi_actual_minutes = sum(lines.mapped('duration')) if lines else 0.0
