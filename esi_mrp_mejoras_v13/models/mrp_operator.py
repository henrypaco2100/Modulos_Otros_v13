# -*- coding: utf-8 -*-
from odoo import fields, models


class EsiMrpOperator(models.Model):
    _name = 'esi.mrp.operator'
    _description = 'ESI - Operador de Producción'
    _order = 'name'
    _check_company_auto = True

    name = fields.Char(string='Operador', required=True, index=True)
    code = fields.Char(string='Código')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company, index=True)
    user_id = fields.Many2one(
        'res.users', string='Usuario Odoo', check_company=True,
        help='Opcional. Permite relacionar al operario con un usuario de Odoo sin obligar a crear un usuario por cada trabajador.')
    notes = fields.Text(string='Observaciones')

    _sql_constraints = [
        ('esi_mrp_operator_company_name_uniq', 'unique(name, company_id)', 'Ya existe un operador con este nombre en esta compañía.'),
    ]
