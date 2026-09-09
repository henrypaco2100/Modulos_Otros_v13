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

    # ESI corrección 2026-09-08:
    # El PVP mostrado en la remisión corresponde al precio de venta del producto.
    # IMPORTE TOTAL debe ser CANTIDAD x PVP, no CANTIDAD x COSTO.
    def esi_unit_pvp(self, move):
        product = move.product_id.with_context(force_company=self.company_id.id)
        return product.lst_price

    def esi_line_amount_total(self, move):
        return self.esi_move_quantity(move) * self.esi_unit_pvp(move)

    def esi_line_cost_total(self, move):
        # Se conserva por compatibilidad con posibles llamadas externas al módulo.
        return self.esi_move_quantity(move) * self.esi_unit_cost(move)

    def esi_total_quantity(self):
        return sum(self.esi_move_quantity(move) for move in self.esi_report_moves())

    def esi_total_amount(self):
        return sum(self.esi_line_amount_total(move) for move in self.esi_report_moves())

    def esi_total_cost(self):
        # Se conserva por compatibilidad; ya no se usa como IMPORTE TOTAL.
        return sum(self.esi_line_cost_total(move) for move in self.esi_report_moves())

    def esi_percentage_label(self):
        value = (self.esi_remission_percentage or "").strip()
        return value if not value or "%" in value else value + "%"

