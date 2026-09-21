# -*- coding: utf-8 -*-
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EsiDestajoReportWizard(models.TransientModel):
    _name = 'esi.destajo.report.wizard'
    _description = 'ESI - Reporte de Destajos'

    date_from = fields.Date(string='Desde')
    date_to = fields.Date(string='Hasta')
    production_id = fields.Many2one('mrp.production', string='Orden de fabricación')
    product_tmpl_id = fields.Many2one('product.template', string='Producto')
    partner_id = fields.Many2one('res.partner', string='Operador / Destajista')
    state_filter = fields.Selection([
        ('all', 'Todos'),
        ('draft', 'Borrador'),
        ('confirmed', 'Confirmado'),
        ('paid', 'Pagado'),
    ], string='Estado', default='all', required=True)
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, required=True)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.date_from > wizard.date_to:
                raise UserError(_('La fecha Desde no puede ser mayor que Hasta.'))

    def _destajo_domain(self):
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id)]
        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        if self.production_id:
            domain.append(('production_id', '=', self.production_id.id))
        if self.product_tmpl_id:
            domain.append(('product_id.product_tmpl_id', '=', self.product_tmpl_id.id))
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        if self.state_filter != 'all':
            domain.append(('state', '=', self.state_filter))
        return domain

    def esi_get_destajos(self):
        self.ensure_one()
        return self.env['esi.calzado.destajo'].search(self._destajo_domain(), order='date asc, partner_id asc, id asc')

    def esi_get_summary(self):
        self.ensure_one()
        grouped = OrderedDict()
        for line in self.esi_get_destajos():
            key = line.partner_id.id or 0
            if key not in grouped:
                grouped[key] = {
                    'worker': line.partner_id.display_name or _('Sin operador'),
                    'records': 0,
                    'quantity': 0.0,
                    'amount': 0.0,
                }
            grouped[key]['records'] += 1
            grouped[key]['quantity'] += line.quantity or 0.0
            grouped[key]['amount'] += line.amount or 0.0
        return list(grouped.values())

    def esi_state_label(self, line):
        if not line or not line.state:
            return ''
        field = line._fields.get('state')
        try:
            selection = field._description_selection(line.env) if field else []
            return dict(selection or []).get(line.state, line.state)
        except Exception:
            return line.state

    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref('esi_produccion_report_v13.action_report_esi_destajo_global').report_action(self)
