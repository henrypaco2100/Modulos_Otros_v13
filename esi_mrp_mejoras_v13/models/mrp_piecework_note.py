# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EsiMrpPieceworkNote(models.Model):
    _name = 'esi.mrp.piecework.note'
    _description = 'Apunte de Destajo ESI'
    _order = 'date desc, id desc'
    _check_company_auto = True

    name = fields.Char(string='Trabajo / Concepto', required=True, index=True)
    date = fields.Date(string='Fecha', default=fields.Date.context_today, required=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True,
    )
    production_id = fields.Many2one(
        'mrp.production', string='Orden de fabricación', check_company=True,
        help='Opcional. Déjelo vacío cuando el apunte original no identifique una OF concreta.',
    )
    operator_id = fields.Many2one('esi.mrp.operator', string='Operador', check_company=True)
    area = fields.Char(string='Área / Etapa')
    quantity = fields.Float(string='Cantidad', digits=(16, 4), required=True, default=1.0)
    rate = fields.Float(string='Tarifa destajo', digits=(16, 4), required=True, default=0.0)
    amount = fields.Float(string='Importe', compute='_compute_amount', store=True, digits=(16, 4))
    source_sheet = fields.Char(string='Hoja origen')
    source_row = fields.Integer(string='Fila origen')
    source_note = fields.Text(string='Observación / Fuente')

    @api.depends('quantity', 'rate')
    def _compute_amount(self):
        for rec in self:
            rec.amount = (rec.quantity or 0.0) * (rec.rate or 0.0)
