# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    esi_remission_percentage = fields.Char(string="Porcentaje")

    def esi_date_in_words(self):
        self.ensure_one()
        date = self.date_done or self.scheduled_date
        months = ("", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE")
        return "%02d DE %s DEL %s" % (date.day, months[date.month], date.year) if date else ""

    def esi_report_moves(self):
        self.ensure_one()
        return self.move_ids_without_package.filtered(lambda move: self.esi_move_quantity(move)).sorted(key=lambda move: move.id)

    def esi_move_quantity(self, move):
        return move.quantity_done or move.product_uom_qty

    def esi_unit_cost(self, move):
        product = move.product_id.with_context(force_company=self.company_id.id)
        return product.standard_price

    def esi_line_cost_total(self, move):
        return self.esi_move_quantity(move) * self.esi_unit_cost(move)

    def esi_total_quantity(self):
        return sum(self.esi_move_quantity(move) for move in self.esi_report_moves())

    def esi_total_cost(self):
        return sum(self.esi_line_cost_total(move) for move in self.esi_report_moves())

    def esi_percentage_label(self):
        value = (self.esi_remission_percentage or "").strip()
        return value if not value or "%" in value else value + "%"

