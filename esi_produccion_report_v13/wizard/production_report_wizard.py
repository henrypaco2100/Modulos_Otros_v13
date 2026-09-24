# -*- coding: utf-8 -*-
# ESI - Informes de Producción Odoo 13

import base64
import calendar
import io
from collections import OrderedDict
from datetime import datetime, time
from html import escape

import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:  # pragma: no cover
    xlsxwriter = None


MONTHS = [
    ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'), ('4', 'Abril'),
    ('5', 'Mayo'), ('6', 'Junio'), ('7', 'Julio'), ('8', 'Agosto'),
    ('9', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre'),
]


class EsiProductionReportWizard(models.TransientModel):
    _name = 'esi.production.report.wizard'
    _description = 'ESI - Wizard Informe de Producción'

    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)
    report_type = fields.Selection(selection='_selection_report_type', string='Tipo de informe', default='summary', required=True)
    period_mode = fields.Selection([
        ('range', 'Rango de fechas'), ('day', 'Día'), ('month', 'Mes'), ('year', 'Año')
    ], string='Período', default='month', required=True)
    date_from = fields.Date(string='Desde')
    date_to = fields.Date(string='Hasta')
    day_date = fields.Date(string='Día', default=fields.Date.context_today)
    month = fields.Selection(MONTHS, string='Mes', default=lambda self: str(fields.Date.context_today(self).month))
    year = fields.Integer(string='Año', default=lambda self: fields.Date.context_today(self).year)
    date_basis = fields.Selection([
        ('planned', 'Fecha planificada'),
        ('finished', 'Fecha de finalización'),
    ], string='Fecha a evaluar', default='planned', required=True)
    state_filter = fields.Selection([
        ('done', 'Finalizadas'),
        ('active_done', 'En proceso y finalizadas'),
        ('all_open', 'Todas excepto canceladas'),
        ('cancelled', 'Solo canceladas'),
    ], string='Estado', default='active_done', required=True)
    group_by = fields.Selection(selection='_selection_group_by', string='Agrupar por', default='week', required=True)
    product_ids = fields.Many2many('product.product', string='Productos terminados')
    user_ids = fields.Many2many('res.users', string='Responsables')
    preview_html = fields.Html(string='Vista previa', sanitize=False, readonly=True)
    excel_file = fields.Binary(string='Excel', readonly=True)
    excel_filename = fields.Char(string='Archivo Excel', readonly=True)

    @api.model
    def _selection_report_type(self):
        options = [
            ('summary', 'Resumen de Producción'),
            ('materials', 'Consumo de Materia Prima (LdM vs Real)'),
        ]
        if self.env.user.has_group('mrp.group_mrp_manager') or self.env.user.has_group('base.group_system'):
            options.append(('cost_margin', 'Costos y Margen Potencial'))
        return options

    @api.model
    def _selection_group_by(self):
        options = [
            ('production', 'Orden de Producción'),
            ('product', 'Producto terminado'),
            ('week', 'Semana'),
            ('month', 'Mes'),
            ('responsible', 'Responsable'),
        ]
        warehouse_model = self.env['stock.warehouse']
        if 'store_id' in warehouse_model._fields:
            options.append(('store', 'Sucursal'))
        return options

    @api.onchange('period_mode', 'day_date', 'month', 'year')
    def _onchange_period(self):
        for wizard in self:
            wizard._apply_period_values()

    def _apply_period_values(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        if self.period_mode == 'day':
            ref = self.day_date or today
            self.date_from = ref
            self.date_to = ref
        elif self.period_mode == 'month':
            year = self.year or today.year
            month = int(self.month or today.month)
            self.date_from = datetime(year, month, 1).date()
            self.date_to = datetime(year, month, calendar.monthrange(year, month)[1]).date()
        elif self.period_mode == 'year':
            year = self.year or today.year
            self.date_from = datetime(year, 1, 1).date()
            self.date_to = datetime(year, 12, 31).date()
        else:
            self.date_from = self.date_from or today.replace(day=1)
            self.date_to = self.date_to or today

    def _validate(self):
        self.ensure_one()
        self._apply_period_values()
        if not self.date_from or not self.date_to:
            raise UserError(_('Debe indicar el rango de fechas.'))
        if self.date_from > self.date_to:
            raise UserError(_('La fecha Desde no puede ser mayor que la fecha Hasta.'))
        if self.report_type == 'cost_margin' and not self._can_view_costs():
            raise UserError(_('El informe de costos y margen potencial requiere permisos de Responsable de Producción o Administrador.'))

    def _can_view_costs(self):
        return bool(self.env.user.has_group('mrp.group_mrp_manager') or self.env.user.has_group('base.group_system'))

    def _datetime_bounds_utc(self):
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        local_start = tz.localize(datetime.combine(self.date_from, time.min))
        local_end = tz.localize(datetime.combine(self.date_to, time.max))
        start = local_start.astimezone(pytz.UTC).replace(tzinfo=None)
        end = local_end.astimezone(pytz.UTC).replace(tzinfo=None)
        return fields.Datetime.to_string(start), fields.Datetime.to_string(end)

    def _production_domain(self):
        start, end = self._datetime_bounds_utc()
        date_field = 'date_finished' if self.date_basis == 'finished' else 'date_planned_start'
        domain = [
            ('company_id', '=', self.company_id.id),
            (date_field, '>=', start),
            (date_field, '<=', end),
        ]
        if self.state_filter == 'done':
            domain.append(('state', '=', 'done'))
        elif self.state_filter == 'active_done':
            domain.append(('state', 'in', ('confirmed', 'planned', 'progress', 'to_close', 'done')))
        elif self.state_filter == 'all_open':
            domain.append(('state', '!=', 'cancel'))
        elif self.state_filter == 'cancelled':
            domain.append(('state', '=', 'cancel'))
        if self.product_ids:
            domain.append(('product_id', 'in', self.product_ids.ids))
        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))

        # ESI integración opcional Multi Store: MRP no trae una regla por sucursal
        # en los módulos recibidos. Aplicamos el mismo criterio usado en Ventas/Compras
        # para que un usuario no consolide producción de sucursales fuera de su acceso.
        warehouse_model = self.env['stock.warehouse']
        user = self.env.user
        if 'store_id' in warehouse_model._fields and 'store_id' in user._fields:
            if user.store_id:
                allowed_store_roots = [user.store_id.id]
            elif 'store_ids' in user._fields:
                allowed_store_roots = user.store_ids.ids
            else:
                allowed_store_roots = []
            domain += [
                '|',
                ('picking_type_id.warehouse_id.store_id', '=', False),
                ('picking_type_id.warehouse_id.store_id', 'child_of', allowed_store_roots),
            ]
        return domain

    def _local_date(self, dt_value):
        if not dt_value:
            return False
        if isinstance(dt_value, str):
            dt_value = fields.Datetime.from_string(dt_value)
        return fields.Datetime.context_timestamp(self, dt_value).date()

    def _mo_date(self, mo):
        return mo.date_finished if self.date_basis == 'finished' else mo.date_planned_start

    def _group_value(self, mo):
        group = self.group_by
        if group == 'production':
            return ('production', mo.id), mo.name
        if group == 'product':
            return ('product', mo.product_id.id), mo.product_id.display_name
        if group == 'responsible':
            return ('responsible', mo.user_id.id or 0), mo.user_id.name or _('Sin responsable')
        if group == 'store':
            warehouse = mo.picking_type_id.warehouse_id
            if 'store_id' not in warehouse._fields:
                raise UserError(_('La agrupación por Sucursal requiere el módulo de sucursales.'))
            store = warehouse.store_id
            return ('store', store.id or 0), store.display_name or _('Sin sucursal')
        local_date = self._local_date(self._mo_date(mo))
        if group == 'week':
            if not local_date:
                return ('week', 'none'), _('Sin fecha')
            iso = local_date.isocalendar()
            label = _('Semana %s - %s') % (iso[1], iso[0])
            return ('week', iso[0], iso[1]), label
        if group == 'month':
            label = local_date.strftime('%m/%Y') if local_date else _('Sin fecha')
            return ('month', label), label
        return ('all', 0), _('General')

    def _qty_digits(self):
        return self.env['decimal.precision'].precision_get('Product Unit of Measure') or 2

    def _money_digits(self):
        currency = self.company_id.currency_id
        return currency.decimal_places if 'decimal_places' in currency._fields else 2

    def _fmt(self, value, digits=2):
        value = value or 0.0
        return ('{:,.%df}' % digits).format(value).replace(',', 'X').replace('.', ',').replace('X', '.')

    def _fmt_qty(self, value):
        return self._fmt(value, self._qty_digits())

    def _fmt_money(self, value):
        return self._fmt(value, self._money_digits())

    def _fmt_pct(self, value):
        return self._fmt(value, 2) + '%'

    def _period_label(self):
        return '%s - %s' % (fields.Date.to_string(self.date_from), fields.Date.to_string(self.date_to))

    def _build_summary_data(self, mos):
        groups_map = OrderedDict()
        for mo in mos:
            detail = mo._esi_report_detail_data(include_costs=False)
            group_key, group_name = self._group_value(mo)
            if group_key not in groups_map:
                groups_map[group_key] = {'name': group_name, 'rows': OrderedDict(), 'mo_ids': set()}
            group = groups_map[group_key]
            pkey = mo.product_id.id
            if pkey not in group['rows']:
                group['rows'][pkey] = {
                    'product': mo.product_id.display_name,
                    'uom': mo.product_id.uom_id.name or '',
                    'mo_count': 0,
                    'planned_qty': 0.0,
                    'produced_qty': 0.0,
                    'difference_qty': 0.0,
                    'efficiency': 0.0,
                    'over_lines': 0,
                    'under_lines': 0,
                    'scrap_count': 0,
                }
            row = group['rows'][pkey]
            row['mo_count'] += 1
            row['planned_qty'] += detail['planned_qty']
            row['produced_qty'] += detail['produced_qty']
            row['difference_qty'] = row['produced_qty'] - row['planned_qty']
            row['efficiency'] = (row['produced_qty'] / row['planned_qty'] * 100.0) if row['planned_qty'] else 0.0
            row['over_lines'] += detail['over_material_count']
            row['under_lines'] += detail['under_material_count']
            row['scrap_count'] += detail['scrap_count']
            group['mo_ids'].add(mo.id)
        groups = []
        for group in groups_map.values():
            group['rows'] = sorted(group['rows'].values(), key=lambda r: (r['product'] or '').lower())
            group['mo_count'] = len(group['mo_ids'])
            groups.append(group)
        return groups

    def _build_material_data(self, mos):
        include_costs = self._can_view_costs()
        groups_map = OrderedDict()
        for mo in mos:
            group_key, group_name = self._group_value(mo)
            if group_key not in groups_map:
                groups_map[group_key] = {
                    'name': group_name, 'rows': OrderedDict(), 'mo_ids': set(),
                    'planned_cost': 0.0, 'actual_cost': 0.0, 'cost_variance': 0.0,
                    'over_lines': 0, 'under_lines': 0,
                }
            group = groups_map[group_key]
            for item in mo._esi_report_material_rows(include_costs=include_costs):
                pkey = item['product_id']
                if pkey not in group['rows']:
                    group['rows'][pkey] = {
                        'product': item['product'], 'uom': item['uom'],
                        'planned_qty': 0.0, 'actual_qty': 0.0, 'variance_qty': 0.0,
                        'variance_pct': 0.0, 'planned_cost': 0.0, 'actual_cost': 0.0, 'cost_variance': 0.0,
                    }
                row = group['rows'][pkey]
                row['planned_qty'] += item['planned_qty']
                row['actual_qty'] += item['actual_qty']
                row['variance_qty'] = row['actual_qty'] - row['planned_qty']
                row['variance_pct'] = (row['variance_qty'] / row['planned_qty'] * 100.0) if row['planned_qty'] else (100.0 if row['actual_qty'] else 0.0)
                if include_costs:
                    row['planned_cost'] += item['planned_cost']
                    row['actual_cost'] += item['actual_cost']
                    row['cost_variance'] = row['actual_cost'] - row['planned_cost']
            group['mo_ids'].add(mo.id)
        groups = []
        for group in groups_map.values():
            group['rows'] = sorted(group['rows'].values(), key=lambda r: (r['product'] or '').lower())
            group['mo_count'] = len(group['mo_ids'])
            group['planned_cost'] = sum(r['planned_cost'] for r in group['rows'])
            group['actual_cost'] = sum(r['actual_cost'] for r in group['rows'])
            group['cost_variance'] = group['actual_cost'] - group['planned_cost']
            group['over_lines'] = len([r for r in group['rows'] if r['variance_qty'] > 0])
            group['under_lines'] = len([r for r in group['rows'] if r['variance_qty'] < 0])
            groups.append(group)
        return groups

    def _build_cost_margin_data(self, mos):
        groups_map = OrderedDict()
        for mo in mos:
            detail = mo._esi_report_detail_data(include_costs=True)
            group_key, group_name = self._group_value(mo)
            if group_key not in groups_map:
                groups_map[group_key] = {'name': group_name, 'rows': OrderedDict(), 'mo_ids': set()}
            group = groups_map[group_key]
            pkey = mo.product_id.id
            if pkey not in group['rows']:
                group['rows'][pkey] = {
                    'product': mo.product_id.display_name,
                    'uom': mo.product_id.uom_id.name or '',
                    'mo_count': 0, 'produced_qty': 0.0,
                    'material_cost': 0.0, 'operation_cost': 0.0, 'total_cost': 0.0,
                    'unit_cost': 0.0, 'sale_price': mo.product_id.lst_price,
                    'potential_revenue': 0.0, 'potential_margin': 0.0, 'margin_pct': 0.0,
                }
            row = group['rows'][pkey]
            row['mo_count'] += 1
            row['produced_qty'] += detail['produced_qty']
            row['material_cost'] += detail['material_actual_cost']
            row['operation_cost'] += detail['operation_cost']
            row['total_cost'] += detail['total_cost']
            row['potential_revenue'] += detail['potential_revenue']
            row['potential_margin'] += detail['potential_margin']
            row['unit_cost'] = (row['total_cost'] / row['produced_qty']) if row['produced_qty'] else 0.0
            row['margin_pct'] = (row['potential_margin'] / row['potential_revenue'] * 100.0) if row['potential_revenue'] else 0.0
            group['mo_ids'].add(mo.id)
        groups = []
        for group in groups_map.values():
            group['rows'] = sorted(group['rows'].values(), key=lambda r: (r['product'] or '').lower())
            group['mo_count'] = len(group['mo_ids'])
            group['material_cost'] = sum(r['material_cost'] for r in group['rows'])
            group['operation_cost'] = sum(r['operation_cost'] for r in group['rows'])
            group['total_cost'] = sum(r['total_cost'] for r in group['rows'])
            group['potential_revenue'] = sum(r['potential_revenue'] for r in group['rows'])
            group['potential_margin'] = sum(r['potential_margin'] for r in group['rows'])
            groups.append(group)
        return groups

    def _build_report_data(self):
        self.ensure_one()
        self._validate()
        mos = self.env['mrp.production'].search(self._production_domain(), order='date_planned_start asc, id asc')
        if self.report_type == 'materials':
            groups = self._build_material_data(mos)
            title = _('ANÁLISIS DE CONSUMO DE MATERIA PRIMA')
        elif self.report_type == 'cost_margin':
            groups = self._build_cost_margin_data(mos)
            title = _('COSTOS Y MARGEN POTENCIAL DE PRODUCCIÓN')
        else:
            groups = self._build_summary_data(mos)
            title = _('RESUMEN DE PRODUCCIÓN')
        return {
            'title': title,
            'company': self.company_id,
            'currency': self.company_id.currency_id,
            'period': self._period_label(),
            'date_basis_label': dict(self._fields['date_basis'].selection).get(self.date_basis),
            'state_label': dict(self._fields['state_filter'].selection).get(self.state_filter),
            'group_label': dict(self._selection_group_by()).get(self.group_by, ''),
            'report_type': self.report_type,
            'groups': groups,
            'mo_count': len(mos),
            'can_costs': self._can_view_costs(),
            'note': _('Costos aproximados: se usa valoración real de stock cuando existe; en su defecto costo estándar actual. El margen potencial usa el PVP de lista actual y no garantiza que la producción haya sido vendida.') if self._can_view_costs() else '',
        }

    def _html_header(self, data):
        company = data['company']
        return ''.join([
            '<div style="display:flex;justify-content:space-between;align-items:flex-start;">',
            '<div><img src="/web/image/res.company/%s/logo" style="max-height:70px;max-width:220px;"/></div>' % company.id,
            '<div style="text-align:right;font-size:12px;"><b>%s</b><br/>%s</div>' % (escape(company.display_name or ''), escape(company.country_id.name or '')),
            '</div>',
            '<h2 style="text-align:center;margin:18px 0 12px;color:#3f4b57;">%s</h2>' % escape(data['title']),
            '<table style="width:100%;font-size:12px;margin-bottom:10px;">',
            '<tr><td><b>Compañía:</b> %s</td><td><b>Rango:</b> %s</td></tr>' % (escape(company.display_name or ''), escape(data['period'])),
            '<tr><td><b>Agrupado por:</b> %s</td><td><b>Fecha:</b> %s &nbsp; | &nbsp; <b>Estado:</b> %s</td></tr>' % (escape(data['group_label']), escape(data['date_basis_label'] or ''), escape(data['state_label'] or '')),
            '</table>',
            '<div style="font-size:12px;margin:8px 0;"><b>Órdenes de producción incluidas:</b> %s</div>' % data['mo_count'],
        ])

    def _build_html(self, data):
        html = ['<div style="font-family:Arial,sans-serif;color:#222;background:#fff;padding:12px;">', self._html_header(data)]
        if not data['groups']:
            html.append('<div style="padding:25px;border:1px solid #ddd;text-align:center;">No se encontraron órdenes de producción con los filtros seleccionados.</div>')
        for group in data['groups']:
            html.append('<div style="background:#eef3f7;border:1px solid #b8c3cc;padding:6px 8px;margin-top:12px;font-weight:bold;">%s: %s</div>' % (escape(data['group_label']), escape(group['name'] or '')))
            if data['report_type'] == 'materials':
                html.append(self._html_material_table(group, data))
            elif data['report_type'] == 'cost_margin':
                html.append(self._html_cost_table(group, data))
            else:
                html.append(self._html_summary_table(group, data))
        if data['note']:
            html.append('<p style="font-size:10px;color:#666;margin-top:10px;">%s</p>' % escape(data['note']))
        html.append('</div>')
        return ''.join(html)

    def _html_summary_table(self, group, data):
        out = ['<table style="border-collapse:collapse;width:100%;font-size:11px;">']
        out.append('<thead><tr style="background:#e7edf3;"><th style="border:1px solid #89949e;padding:5px;">PRODUCTO</th><th style="border:1px solid #89949e;padding:5px;">UDM</th><th style="border:1px solid #89949e;padding:5px;"># OF</th><th style="border:1px solid #89949e;padding:5px;">PLANIFICADO</th><th style="border:1px solid #89949e;padding:5px;">PRODUCIDO</th><th style="border:1px solid #89949e;padding:5px;">DIFERENCIA</th><th style="border:1px solid #89949e;padding:5px;">CUMPLIMIENTO</th><th style="border:1px solid #89949e;padding:5px;">MAT. SOBRECONSUMO</th><th style="border:1px solid #89949e;padding:5px;">MAT. BAJO CONSUMO</th><th style="border:1px solid #89949e;padding:5px;">MERMAS</th></tr></thead><tbody>')
        for row in group['rows']:
            out.append('<tr><td style="border:1px solid #aab2b9;padding:4px;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:center;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:center;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:center;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:center;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:center;">%s</td></tr>' % (escape(row['product']), escape(row['uom']), row['mo_count'], self._fmt_qty(row['planned_qty']), self._fmt_qty(row['produced_qty']), self._fmt_qty(row['difference_qty']), self._fmt_pct(row['efficiency']), row['over_lines'], row['under_lines'], row['scrap_count']))
        out.append('</tbody></table>')
        return ''.join(out)

    def _html_material_table(self, group, data):
        out = ['<table style="border-collapse:collapse;width:100%;font-size:11px;">']
        out.append('<thead><tr style="background:#e7edf3;"><th style="border:1px solid #89949e;padding:5px;">MATERIA PRIMA</th><th style="border:1px solid #89949e;padding:5px;">UDM</th><th style="border:1px solid #89949e;padding:5px;">PLANIFICADO LdM</th><th style="border:1px solid #89949e;padding:5px;">CONSUMO REAL</th><th style="border:1px solid #89949e;padding:5px;">VARIACIÓN</th><th style="border:1px solid #89949e;padding:5px;">VAR. %</th>')
        if data['can_costs']:
            out.append('<th style="border:1px solid #89949e;padding:5px;">COSTO PLAN.</th><th style="border:1px solid #89949e;padding:5px;">COSTO REAL</th><th style="border:1px solid #89949e;padding:5px;">VAR. COSTO</th>')
        out.append('</tr></thead><tbody>')
        for row in group['rows']:
            out.append('<tr><td style="border:1px solid #aab2b9;padding:4px;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:center;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td>' % (escape(row['product']), escape(row['uom']), self._fmt_qty(row['planned_qty']), self._fmt_qty(row['actual_qty']), self._fmt_qty(row['variance_qty']), self._fmt_pct(row['variance_pct'])))
            if data['can_costs']:
                out.append('<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td>' % (self._fmt_money(row['planned_cost']), self._fmt_money(row['actual_cost']), self._fmt_money(row['cost_variance'])))
            out.append('</tr>')
        if data['can_costs']:
            out.append('<tr style="font-weight:bold;background:#f7f8f9;"><td colspan="6" style="border:1px solid #89949e;padding:5px;text-align:right;">COSTO DEL GRUPO</td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td></tr>' % (self._fmt_money(group['planned_cost']), self._fmt_money(group['actual_cost']), self._fmt_money(group['cost_variance'])))
        out.append('</tbody></table>')
        out.append('<div style="font-size:10px;margin:5px 0;"><b>Materiales sobreconsumidos:</b> %s &nbsp; <b>Materiales por debajo de lo planificado:</b> %s</div>' % (group['over_lines'], group['under_lines']))
        return ''.join(out)

    def _html_cost_table(self, group, data):
        out = ['<table style="border-collapse:collapse;width:100%;font-size:10px;">']
        out.append('<thead><tr style="background:#e7edf3;"><th style="border:1px solid #89949e;padding:4px;">PRODUCTO</th><th style="border:1px solid #89949e;padding:4px;">UDM</th><th style="border:1px solid #89949e;padding:4px;"># OF</th><th style="border:1px solid #89949e;padding:4px;">PRODUCIDO</th><th style="border:1px solid #89949e;padding:4px;">COSTO MATERIAL</th><th style="border:1px solid #89949e;padding:4px;">OTROS COSTOS</th><th style="border:1px solid #89949e;padding:4px;">COSTO TOTAL</th><th style="border:1px solid #89949e;padding:4px;">COSTO/UD</th><th style="border:1px solid #89949e;padding:4px;">PVP LISTA</th><th style="border:1px solid #89949e;padding:4px;">VALOR POTENCIAL</th><th style="border:1px solid #89949e;padding:4px;">MARGEN POTENCIAL</th><th style="border:1px solid #89949e;padding:4px;">MARGEN %</th></tr></thead><tbody>')
        for row in group['rows']:
            out.append('<tr><td style="border:1px solid #aab2b9;padding:3px;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:center;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:center;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:3px;text-align:right;">%s</td></tr>' % (escape(row['product']), escape(row['uom']), row['mo_count'], self._fmt_qty(row['produced_qty']), self._fmt_money(row['material_cost']), self._fmt_money(row['operation_cost']), self._fmt_money(row['total_cost']), self._fmt_money(row['unit_cost']), self._fmt_money(row['sale_price']), self._fmt_money(row['potential_revenue']), self._fmt_money(row['potential_margin']), self._fmt_pct(row['margin_pct'])))
        out.append('<tr style="font-weight:bold;background:#f7f8f9;"><td colspan="4" style="border:1px solid #89949e;padding:5px;text-align:right;">TOTALES DEL GRUPO</td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td><td colspan="2" style="border:1px solid #89949e;padding:5px;"></td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td><td style="border:1px solid #89949e;padding:5px;"></td></tr>' % (self._fmt_money(group['material_cost']), self._fmt_money(group['operation_cost']), self._fmt_money(group['total_cost']), self._fmt_money(group['potential_revenue']), self._fmt_money(group['potential_margin'])))
        out.append('</tbody></table>')
        return ''.join(out)

    def action_view_report(self):
        self.ensure_one()
        data = self._build_report_data()
        self.preview_html = self._build_html(data)
        return {'type': 'ir.actions.act_window', 'name': _('Informes de Producción'), 'res_model': self._name, 'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_print_pdf(self):
        self.ensure_one()
        self._validate()
        return self.env.ref('esi_produccion_report_v13.action_report_esi_production_pdf').report_action(self)

    def action_export_excel(self):
        self.ensure_one()
        if xlsxwriter is None:
            raise UserError(_('No está instalada la librería Python xlsxwriter en el servidor.'))
        data = self._build_report_data()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Producción')
        sheet.hide_gridlines(2)
        fmt_title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
        fmt_label = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#EEF3F7'})
        fmt_header = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#DDE7F0', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        fmt_text = workbook.add_format({'border': 1})
        fmt_center = workbook.add_format({'border': 1, 'align': 'center'})
        fmt_qty = workbook.add_format({'border': 1, 'num_format': '#,##0.' + ('0' * self._qty_digits())})
        fmt_money = workbook.add_format({'border': 1, 'num_format': '#,##0.' + ('0' * self._money_digits())})
        fmt_pct = workbook.add_format({'border': 1, 'num_format': '0.00%'} )
        fmt_group = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#EEF3F7'})
        fmt_sub = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#F7F8F9'})
        fmt_note = workbook.add_format({'italic': True, 'font_size': 9, 'font_color': '#666666', 'text_wrap': True})

        if data['report_type'] == 'materials':
            columns = ['Materia Prima', 'UDM', 'Planificado LdM', 'Consumo Real', 'Variación', 'Var. %']
            if data['can_costs']:
                columns += ['Costo Plan.', 'Costo Real', 'Var. Costo']
        elif data['report_type'] == 'cost_margin':
            columns = ['Producto', 'UDM', '# OF', 'Producido', 'Costo Material', 'Otros costos', 'Costo Total', 'Costo/UD', 'PVP Lista', 'Valor Potencial', 'Margen Potencial', 'Margen %']
        else:
            columns = ['Producto', 'UDM', '# OF', 'Planificado', 'Producido', 'Diferencia', 'Cumplimiento', 'Mat. Sobreconsumo', 'Mat. Bajo Consumo', 'Mermas']
        last_col = len(columns) - 1
        sheet.merge_range(0, 0, 0, last_col, data['title'], fmt_title)
        sheet.write(2, 0, 'Compañía', fmt_label); sheet.write(2, 1, data['company'].display_name or '')
        sheet.write(2, 3, 'Rango', fmt_label); sheet.write(2, 4, data['period'])
        sheet.write(3, 0, 'Agrupado por', fmt_label); sheet.write(3, 1, data['group_label'])
        sheet.write(3, 3, 'Fecha', fmt_label); sheet.write(3, 4, data['date_basis_label'])
        sheet.write(4, 0, 'Estado', fmt_label); sheet.write(4, 1, data['state_label'])
        sheet.write(4, 3, 'Órdenes incluidas', fmt_label); sheet.write_number(4, 4, data['mo_count'])
        row_idx = 6
        for group in data['groups']:
            sheet.merge_range(row_idx, 0, row_idx, last_col, '%s: %s' % (data['group_label'], group['name']), fmt_group)
            row_idx += 1
            for c, title in enumerate(columns):
                sheet.write(row_idx, c, title, fmt_header)
            row_idx += 1
            for row in group['rows']:
                if data['report_type'] == 'materials':
                    vals = [row['product'], row['uom'], row['planned_qty'], row['actual_qty'], row['variance_qty'], row['variance_pct'] / 100.0]
                    if data['can_costs']:
                        vals += [row['planned_cost'], row['actual_cost'], row['cost_variance']]
                    for c, val in enumerate(vals):
                        if c in (0, 1): sheet.write(row_idx, c, val, fmt_text if c == 0 else fmt_center)
                        elif c == 5: sheet.write_number(row_idx, c, val, fmt_pct)
                        elif c >= 6: sheet.write_number(row_idx, c, val, fmt_money)
                        else: sheet.write_number(row_idx, c, val, fmt_qty)
                elif data['report_type'] == 'cost_margin':
                    vals = [row['product'], row['uom'], row['mo_count'], row['produced_qty'], row['material_cost'], row['operation_cost'], row['total_cost'], row['unit_cost'], row['sale_price'], row['potential_revenue'], row['potential_margin'], row['margin_pct'] / 100.0]
                    for c, val in enumerate(vals):
                        if c == 0: sheet.write(row_idx, c, val, fmt_text)
                        elif c == 1: sheet.write(row_idx, c, val, fmt_center)
                        elif c == 2: sheet.write_number(row_idx, c, val, fmt_center)
                        elif c == 3: sheet.write_number(row_idx, c, val, fmt_qty)
                        elif c == 11: sheet.write_number(row_idx, c, val, fmt_pct)
                        else: sheet.write_number(row_idx, c, val, fmt_money)
                else:
                    vals = [row['product'], row['uom'], row['mo_count'], row['planned_qty'], row['produced_qty'], row['difference_qty'], row['efficiency'] / 100.0, row['over_lines'], row['under_lines'], row['scrap_count']]
                    for c, val in enumerate(vals):
                        if c == 0: sheet.write(row_idx, c, val, fmt_text)
                        elif c == 1: sheet.write(row_idx, c, val, fmt_center)
                        elif c in (2, 7, 8, 9): sheet.write_number(row_idx, c, val, fmt_center)
                        elif c == 6: sheet.write_number(row_idx, c, val, fmt_pct)
                        else: sheet.write_number(row_idx, c, val, fmt_qty)
                row_idx += 1
            if data['report_type'] == 'materials' and data['can_costs']:
                sheet.merge_range(row_idx, 0, row_idx, 5, 'COSTO DEL GRUPO', fmt_sub)
                sheet.write_number(row_idx, 6, group['planned_cost'], fmt_sub)
                sheet.write_number(row_idx, 7, group['actual_cost'], fmt_sub)
                sheet.write_number(row_idx, 8, group['cost_variance'], fmt_sub)
                row_idx += 1
            elif data['report_type'] == 'cost_margin':
                sheet.merge_range(row_idx, 0, row_idx, 3, 'TOTALES DEL GRUPO', fmt_sub)
                sheet.write_number(row_idx, 4, group['material_cost'], fmt_sub)
                sheet.write_number(row_idx, 5, group['operation_cost'], fmt_sub)
                sheet.write_number(row_idx, 6, group['total_cost'], fmt_sub)
                sheet.write_number(row_idx, 9, group['potential_revenue'], fmt_sub)
                sheet.write_number(row_idx, 10, group['potential_margin'], fmt_sub)
                row_idx += 1
            row_idx += 1
        if data['note']:
            sheet.merge_range(row_idx, 0, row_idx + 1, last_col, data['note'], fmt_note)
        sheet.set_column(0, 0, 38)
        sheet.set_column(1, 1, 11)
        sheet.set_column(2, last_col, 16)
        workbook.close()
        output.seek(0)
        filename = 'Informe_Produccion_%s_%s.xlsx' % (fields.Date.to_string(self.date_from), fields.Date.to_string(self.date_to))
        self.write({'excel_file': base64.b64encode(output.read()), 'excel_filename': filename})
        return {'type': 'ir.actions.act_url', 'url': '/web/content/?model=%s&id=%s&field=excel_file&filename_field=excel_filename&download=true' % (self._name, self.id), 'target': 'self'}
