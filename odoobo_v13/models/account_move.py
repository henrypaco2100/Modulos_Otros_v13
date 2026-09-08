# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    esi_show_line_date = fields.Boolean(string="Mostrar fecha", default=False)
    esi_show_analytic = fields.Boolean(string="Mostrar analítica", default=True)
    esi_check_number = fields.Char(string="Nro. de cheque")

    def esi_report_filename(self):
        self.ensure_one()
        if self.state != "posted":
            raise UserError(_("El asiento debe estar publicado para imprimir el comprobante."))
        return "Comprobante Contable - %s" % (self.name or "Borrador")

    def esi_date_in_words(self):
        self.ensure_one()
        date = self.invoice_date if self.type in ("out_invoice", "in_invoice", "out_refund", "in_refund") and self.invoice_date else self.date
        months = ("", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE")
        return "%02d DE %s DEL %s" % (date.day, months[date.month], date.year) if date else ""

    def esi_ordered_lines(self):
        self.ensure_one()
        return self.line_ids.sorted(key=lambda line: (line.date or self.date, line.id))

    def esi_total_debit(self):
        self.ensure_one()
        return sum(self.line_ids.mapped("debit"))

    def esi_total_credit(self):
        self.ensure_one()
        return sum(self.line_ids.mapped("credit"))

    def esi_amount_in_words(self):
        self.ensure_one()
        amount = self.esi_total_debit()
        currency = self.company_id.currency_id
        try:
            return currency.amount_to_text(amount).upper()
        except Exception:
            integer = int(amount)
            cents = int(round((amount - integer) * 100))
            return "%s %02d/100" % (integer, cents)

    def action_esi_comprobante_preview(self):
        self.ensure_one()
        return self.env.ref("odoobo_v13.action_comprobante_contable_html").report_action(self)

    def action_esi_comprobante_pdf(self):
        self.ensure_one()
        return self.env.ref("odoobo_v13.action_comprobante_contable_pdf").report_action(self)

