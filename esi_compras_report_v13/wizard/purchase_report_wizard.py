# -*- coding: utf-8 -*-
# ESI - Informes de Compras Odoo 13
# Módulo independiente. Las integraciones con Sucursal y Tipo de Compra se detectan dinámicamente.

import base64
import calendar
import io
from collections import OrderedDict
from datetime import datetime, time, timedelta
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


class EsiPurchaseReportWizard(models.TransientModel):
    _name = 'esi.purchase.report.wizard'
    _description = 'ESI - Wizard Informe de Compras'

    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company,
    )
    period_mode = fields.Selection([
        ('range', 'Rango de fechas'),
        ('day', 'Día'),
        ('month', 'Mes'),
        ('year', 'Año'),
    ], string='Período', default='month', required=True)
    date_from = fields.Date(string='Desde')
    date_to = fields.Date(string='Hasta')
    day_date = fields.Date(string='Día', default=fields.Date.context_today)
    month = fields.Selection(MONTHS, string='Mes', default=lambda self: str(fields.Date.context_today(self).month))
    year = fields.Integer(string='Año', default=lambda self: fields.Date.context_today(self).year)

    # ESI: resumen + 3 análisis adicionales para control de compras.
    analysis_type = fields.Selection([
        ('standard', 'Resumen de Compras'),
        ('ranking', 'Ranking / Concentración de Compras'),
        ('evolution', 'Evolución y Tendencia de Compras'),
        ('price_variation', 'Variación de Precio por Producto'),
    ], string='Tipo de análisis', default='standard', required=True)

    group_by = fields.Selection(selection='_selection_group_by', string='Agrupar por', default='product', required=True)
    ranking_by = fields.Selection(selection='_selection_ranking_by', string='Ranking por', default='supplier')
    top_n = fields.Integer(string='Top', default=20, help='0 = mostrar todos los resultados.')
    evolution_granularity = fields.Selection([
        ('auto', 'Automático'),
        ('day', 'Día'),
        ('week', 'Semana'),
        ('month', 'Mes'),
    ], string='Agrupar tendencia por', default='auto')

    amount_basis = fields.Selection([
        ('total', 'Total con impuestos'),
        ('untaxed', 'Total sin impuestos'),
    ], string='Importe del reporte', default='total', required=True)
    state_filter = fields.Selection([
        ('confirmed', 'Compras confirmadas'),
        ('all_open', 'Todas excepto canceladas'),
        ('cancelled', 'Solo canceladas'),
    ], string='Estado', default='confirmed', required=True)

    product_ids = fields.Many2many('product.product', string='Productos')
    partner_ids = fields.Many2many('res.partner', string='Proveedores')
    user_ids = fields.Many2many('res.users', string='Compradores / Responsables')

    preview_html = fields.Html(string='Vista previa', sanitize=False, readonly=True)
    excel_file = fields.Binary(string='Excel', readonly=True)
    excel_filename = fields.Char(string='Archivo Excel', readonly=True)

    @api.model
    def _selection_group_by(self):
        options = [
            ('product', 'Producto'),
            ('buyer', 'Comprador / Responsable'),
            ('supplier', 'Proveedor'),
            ('month', 'Mes'),
        ]
        purchase_model = self.env['purchase.order']
        # ESI integración opcional con módulos Store/Automated.
        if 'store_id' in purchase_model._fields:
            options.append(('store', 'Sucursal'))
        if 'work_process_order_id' in purchase_model._fields:
            options.append(('purchase_type', 'Tipo de Compra'))
        return options

    @api.model
    def _selection_ranking_by(self):
        options = [
            ('supplier', 'Proveedor'),
            ('product', 'Producto'),
            ('buyer', 'Comprador / Responsable'),
        ]
        purchase_model = self.env['purchase.order']
        if 'store_id' in purchase_model._fields:
            options.append(('store', 'Sucursal'))
        if 'work_process_order_id' in purchase_model._fields:
            options.append(('purchase_type', 'Tipo de Compra'))
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
        elif self.period_mode == 'range':
            self.date_from = self.date_from or today.replace(day=1)
            self.date_to = self.date_to or today

    def _validate(self):
        self.ensure_one()
        self._apply_period_values()
        if not self.date_from or not self.date_to:
            raise UserError(_('Debe indicar el rango de fechas.'))
        if self.date_from > self.date_to:
            raise UserError(_('La fecha Desde no puede ser mayor que la fecha Hasta.'))
        if self.top_n < 0:
            raise UserError(_('El campo Top debe ser 0 o un número positivo.'))

    def _datetime_bounds_utc(self):
        self.ensure_one()
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        local_start = tz.localize(datetime.combine(self.date_from, time.min))
        local_end = tz.localize(datetime.combine(self.date_to, time.max))
        start = local_start.astimezone(pytz.UTC).replace(tzinfo=None)
        end = local_end.astimezone(pytz.UTC).replace(tzinfo=None)
        return fields.Datetime.to_string(start), fields.Datetime.to_string(end)

    def _order_domain(self):
        self.ensure_one()
        start, end = self._datetime_bounds_utc()
        domain = [
            ('company_id', '=', self.company_id.id),
            ('date_order', '>=', start),
            ('date_order', '<=', end),
        ]
        if self.state_filter == 'confirmed':
            domain.append(('state', 'in', ('purchase', 'done')))
        elif self.state_filter == 'all_open':
            domain.append(('state', '!=', 'cancel'))
        elif self.state_filter == 'cancelled':
            domain.append(('state', '=', 'cancel'))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))
        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))
        return domain

    def _get_orders(self):
        return self.env['purchase.order'].search(self._order_domain(), order='date_order asc, id asc')

    def _local_date(self, dt_value):
        if not dt_value:
            return False
        if isinstance(dt_value, str):
            dt_value = fields.Datetime.from_string(dt_value)
        return fields.Datetime.context_timestamp(self, dt_value).date()

    def _group_value(self, order, product):
        group = self.group_by
        if group == 'product':
            return ('product_all', 0), _('Productos')
        if group == 'buyer':
            return ('buyer', order.user_id.id or 0), order.user_id.name or _('Sin responsable')
        if group == 'supplier':
            return ('supplier', order.partner_id.id or 0), order.partner_id.display_name or _('Sin proveedor')
        if group == 'month':
            local_date = self._local_date(order.date_order)
            label = local_date.strftime('%m/%Y') if local_date else _('Sin fecha')
            return ('month', label), label
        if group == 'store':
            if 'store_id' not in order._fields:
                raise UserError(_('La agrupación por Sucursal requiere el módulo de sucursales.'))
            store = order.store_id
            return ('store', store.id or 0), store.display_name or _('Sin sucursal')
        if group == 'purchase_type':
            if 'work_process_order_id' not in order._fields:
                raise UserError(_('La agrupación por Tipo de Compra requiere el módulo Tipo de Compras.'))
            purchase_type = order.work_process_order_id
            return ('purchase_type', purchase_type.id or 0), purchase_type.display_name or _('Sin tipo de compra')
        return ('all', 0), _('General')

    def _ranking_value(self, order, line):
        ranking = self.ranking_by or 'supplier'
        if ranking == 'supplier':
            return ('supplier', order.partner_id.id or 0), order.partner_id.display_name or _('Sin proveedor')
        if ranking == 'product':
            return ('product', line.product_id.id), line.product_id.display_name
        if ranking == 'buyer':
            return ('buyer', order.user_id.id or 0), order.user_id.name or _('Sin responsable')
        if ranking == 'store':
            if 'store_id' not in order._fields:
                raise UserError(_('El ranking por Sucursal requiere el módulo de sucursales.'))
            store = order.store_id
            return ('store', store.id or 0), store.display_name or _('Sin sucursal')
        if ranking == 'purchase_type':
            if 'work_process_order_id' not in order._fields:
                raise UserError(_('El ranking por Tipo de Compra requiere el módulo Tipo de Compras.'))
            purchase_type = order.work_process_order_id
            return ('purchase_type', purchase_type.id or 0), purchase_type.display_name or _('Sin tipo de compra')
        return ('other', 0), _('General')

    def _line_qty_default_uom(self, line):
        if not line.product_id:
            return 0.0
        uom = line.product_uom
        if uom and uom != line.product_id.uom_id:
            return uom._compute_quantity(line.product_qty, line.product_id.uom_id)
        return line.product_qty

    def _convert_to_company_currency(self, order, amount):
        currency = order.currency_id
        company_currency = self.company_id.currency_id
        if not currency or currency == company_currency:
            return amount
        conv_date = order.date_order.date() if order.date_order else fields.Date.context_today(self)
        return currency._convert(amount, company_currency, self.company_id, conv_date)

    def _qty_digits(self):
        return self.env['decimal.precision'].precision_get('Product Unit of Measure') or 2

    def _money_digits(self):
        currency = self.company_id.currency_id
        if 'decimal_places' in currency._fields:
            return currency.decimal_places
        return 2

    def _fmt(self, value, digits=2):
        value = value or 0.0
        return ('{:,.%df}' % digits).format(value).replace(',', 'X').replace('.', ',').replace('X', '.')

    def _fmt_qty(self, value):
        return self._fmt(value, self._qty_digits())

    def _fmt_money(self, value):
        return self._fmt(value, self._money_digits())

    def _fmt_percent(self, value):
        return self._fmt(value, 2) + ' %'

    def _period_label(self):
        return '%s - %s' % (fields.Date.to_string(self.date_from), fields.Date.to_string(self.date_to))

    def _base_data(self, title):
        return {
            'title': title,
            'company': self.company_id,
            'currency': self.company_id.currency_id,
            'period': self._period_label(),
            'amount_label': dict(self._fields['amount_basis'].selection).get(self.amount_basis),
            'state_label': dict(self._fields['state_filter'].selection).get(self.state_filter),
            'analysis_label': dict(self._fields['analysis_type'].selection).get(self.analysis_type),
            'analysis_type': self.analysis_type,
            'groups': [], 'analysis_columns': [], 'analysis_rows': [], 'summary': [],
            'note': '', 'order_count': 0,
        }

    def _iter_valid_lines(self, orders):
        for order in orders:
            for line in order.order_line:
                if getattr(line, 'display_type', False) or not line.product_id:
                    continue
                if self.product_ids and line.product_id not in self.product_ids:
                    continue
                yield order, line

    # -------------------------------------------------------------------------
    # ESI - REPORTE 1: resumen consolidado original
    # -------------------------------------------------------------------------
    def _build_standard_data(self, orders):
        groups_map = OrderedDict()
        report_order_ids = set()

        for order, line in self._iter_valid_lines(orders):
            group_key, group_name = self._group_value(order, line.product_id)
            product_key = line.product_id.id
            if group_key not in groups_map:
                groups_map[group_key] = {'name': group_name, 'rows': OrderedDict(), 'qty': 0.0, 'amount': 0.0}
            group = groups_map[group_key]
            if product_key not in group['rows']:
                group['rows'][product_key] = {
                    'product_id': line.product_id.id,
                    'product': line.product_id.display_name,
                    'uom': line.product_id.uom_id.name or '',
                    'qty': 0.0,
                    'amount': 0.0,
                }
            row = group['rows'][product_key]
            qty = self._line_qty_default_uom(line)
            raw_amount = line.price_total if self.amount_basis == 'total' else line.price_subtotal
            amount = self._convert_to_company_currency(order, raw_amount)
            row['qty'] += qty
            row['amount'] += amount
            group['qty'] += qty
            group['amount'] += amount
            report_order_ids.add(order.id)

        groups = []
        totals = {'qty': 0.0, 'amount': 0.0}
        for group in groups_map.values():
            group['rows'] = list(group['rows'].values())
            group['rows'].sort(key=lambda r: (r['product'] or '').lower())
            groups.append(group)
            totals['qty'] += group['qty']
            totals['amount'] += group['amount']

        data = self._base_data(_('INFORME DE COMPRAS'))
        data.update({
            'group_label': dict(self._selection_group_by()).get(self.group_by, ''),
            'groups': groups,
            'totals': totals,
            'order_count': len(report_order_ids),
            'row_count': sum(len(g['rows']) for g in groups),
        })
        return data

    # -------------------------------------------------------------------------
    # ESI - ANÁLISIS 2: Ranking/Pareto, concentración y clasificación ABC
    # -------------------------------------------------------------------------
    def _build_ranking_data(self, orders):
        ranking_map = OrderedDict()
        all_order_ids = set()
        for order, line in self._iter_valid_lines(orders):
            key, name = self._ranking_value(order, line)
            if key not in ranking_map:
                ranking_map[key] = {'name': name, 'order_ids': set(), 'qty': 0.0, 'amount': 0.0}
            row = ranking_map[key]
            qty = self._line_qty_default_uom(line)
            raw_amount = line.price_total if self.amount_basis == 'total' else line.price_subtotal
            amount = self._convert_to_company_currency(order, raw_amount)
            row['qty'] += qty
            row['amount'] += amount
            row['order_ids'].add(order.id)
            all_order_ids.add(order.id)

        rows_all = list(ranking_map.values())
        rows_all.sort(key=lambda r: r['amount'], reverse=True)
        grand_amount = sum(r['amount'] for r in rows_all)
        cumulative = 0.0
        rows = []
        for pos, row in enumerate(rows_all, 1):
            share = row['amount'] / grand_amount * 100.0 if grand_amount else 0.0
            cumulative += share
            abc = 'A' if cumulative <= 80.0 else ('B' if cumulative <= 95.0 else 'C')
            order_count = len(row['order_ids'])
            rows.append({
                'pos': pos,
                'concept': row['name'],
                'orders': order_count,
                'qty': row['qty'],
                'amount': row['amount'],
                'avg_order': row['amount'] / order_count if order_count else 0.0,
                'share': share,
                'cumulative': cumulative,
                'abc': abc,
            })
        if self.top_n:
            rows = rows[:self.top_n]

        columns = [
            {'key': 'pos', 'label': 'POS', 'type': 'int', 'align': 'center'},
            {'key': 'concept', 'label': dict(self._selection_ranking_by()).get(self.ranking_by, 'CONCEPTO').upper(), 'type': 'text', 'align': 'left'},
            {'key': 'orders', 'label': 'ÓRDENES', 'type': 'int', 'align': 'right'},
            {'key': 'qty', 'label': 'CANTIDAD', 'type': 'qty', 'align': 'right'},
            {'key': 'amount', 'label': 'TOTAL COMPRA', 'type': 'money', 'align': 'right'},
            {'key': 'avg_order', 'label': 'COMPRA PROM.', 'type': 'money', 'align': 'right'},
            {'key': 'share', 'label': 'PARTICIPACIÓN', 'type': 'percent', 'align': 'right'},
            {'key': 'cumulative', 'label': 'ACUMULADO', 'type': 'percent', 'align': 'right'},
            {'key': 'abc', 'label': 'ABC', 'type': 'text', 'align': 'center'},
        ]
        data = self._base_data(_('RANKING / CONCENTRACIÓN DE COMPRAS'))
        data.update({
            'analysis_columns': columns,
            'analysis_rows': rows,
            'order_count': len(all_order_ids),
            'summary': [
                {'label': 'Elementos analizados', 'value': len(rows_all), 'type': 'int'},
                {'label': 'Órdenes', 'value': len(all_order_ids), 'type': 'int'},
                {'label': 'Compra total', 'value': grand_amount, 'type': 'money'},
            ],
            'note': _('La clasificación ABC ayuda a detectar concentración: A hasta 80% acumulado, B hasta 95% y C el resto. La cantidad puede mezclar UDM cuando el ranking no es por producto.'),
        })
        return data

    # -------------------------------------------------------------------------
    # ESI - ANÁLISIS 3: evolución por día/semana/mes y variación vs período previo
    # -------------------------------------------------------------------------
    def _effective_granularity(self):
        if self.evolution_granularity and self.evolution_granularity != 'auto':
            return self.evolution_granularity
        days = (self.date_to - self.date_from).days + 1
        if days <= 31:
            return 'day'
        if days <= 150:
            return 'week'
        return 'month'

    def _bucket_info(self, local_date, granularity):
        if granularity == 'day':
            return local_date, local_date.strftime('%d/%m/%Y')
        if granularity == 'week':
            start = local_date - timedelta(days=local_date.weekday())
            end = start + timedelta(days=6)
            return start, 'Semana %s - %s' % (start.strftime('%d/%m'), end.strftime('%d/%m/%Y'))
        start = local_date.replace(day=1)
        return start, start.strftime('%m/%Y')

    def _build_evolution_data(self, orders):
        granularity = self._effective_granularity()
        buckets = OrderedDict()
        all_order_ids = set()
        for order, line in self._iter_valid_lines(orders):
            local_date = self._local_date(order.date_order)
            if not local_date:
                continue
            key, label = self._bucket_info(local_date, granularity)
            if key not in buckets:
                buckets[key] = {'period': label, 'order_ids': set(), 'qty': 0.0, 'amount': 0.0}
            bucket = buckets[key]
            qty = self._line_qty_default_uom(line)
            raw_amount = line.price_total if self.amount_basis == 'total' else line.price_subtotal
            amount = self._convert_to_company_currency(order, raw_amount)
            bucket['qty'] += qty
            bucket['amount'] += amount
            bucket['order_ids'].add(order.id)
            all_order_ids.add(order.id)

        rows = []
        previous_amount = None
        for key in sorted(buckets.keys()):
            bucket = buckets[key]
            order_count = len(bucket['order_ids'])
            variation = 0.0 if previous_amount is None else bucket['amount'] - previous_amount
            variation_pct = 0.0
            if previous_amount not in (None, 0.0):
                variation_pct = variation / previous_amount * 100.0
            rows.append({
                'period': bucket['period'],
                'orders': order_count,
                'qty': bucket['qty'],
                'amount': bucket['amount'],
                'avg_order': bucket['amount'] / order_count if order_count else 0.0,
                'previous': previous_amount or 0.0,
                'variation': variation,
                'variation_pct': variation_pct,
            })
            previous_amount = bucket['amount']

        total_amount = sum(r['amount'] for r in rows)
        total_qty = sum(r['qty'] for r in rows)
        columns = [
            {'key': 'period', 'label': 'PERÍODO', 'type': 'text', 'align': 'left'},
            {'key': 'orders', 'label': 'ÓRDENES', 'type': 'int', 'align': 'right'},
            {'key': 'qty', 'label': 'CANTIDAD', 'type': 'qty', 'align': 'right'},
            {'key': 'amount', 'label': 'TOTAL COMPRA', 'type': 'money', 'align': 'right'},
            {'key': 'avg_order', 'label': 'COMPRA PROM.', 'type': 'money', 'align': 'right'},
            {'key': 'previous', 'label': 'PERÍODO ANTERIOR', 'type': 'money', 'align': 'right'},
            {'key': 'variation', 'label': 'VARIACIÓN', 'type': 'money', 'align': 'right'},
            {'key': 'variation_pct', 'label': 'VARIACIÓN %', 'type': 'percent', 'align': 'right'},
        ]
        gran_label = dict(self._fields['evolution_granularity'].selection).get(granularity, granularity)
        data = self._base_data(_('EVOLUCIÓN Y TENDENCIA DE COMPRAS'))
        data.update({
            'analysis_columns': columns,
            'analysis_rows': rows,
            'order_count': len(all_order_ids),
            'summary': [
                {'label': 'Agrupación', 'value': gran_label, 'type': 'text'},
                {'label': 'Órdenes', 'value': len(all_order_ids), 'type': 'int'},
                {'label': 'Cantidad', 'value': total_qty, 'type': 'qty'},
                {'label': 'Compra total', 'value': total_amount, 'type': 'money'},
            ],
            'note': _('La variación compara cada período con el período inmediatamente anterior dentro del rango seleccionado.'),
        })
        return data

    # -------------------------------------------------------------------------
    # ESI - ANÁLISIS 4: variación real del precio de compra por producto
    # -------------------------------------------------------------------------
    def _build_price_variation_data(self, orders):
        products = OrderedDict()
        all_order_ids = set()
        for order, line in self._iter_valid_lines(orders):
            qty = self._line_qty_default_uom(line)
            if not qty:
                continue
            product_id = line.product_id.id
            if product_id not in products:
                products[product_id] = {
                    'product': line.product_id.display_name,
                    'uom': line.product_id.uom_id.name or '',
                    'qty': 0.0, 'untaxed': 0.0, 'amount': 0.0,
                    'min_price': None, 'max_price': None,
                    'last_price': 0.0, 'last_date': None, 'last_supplier': '',
                    'supplier_ids': set(), 'order_ids': set(),
                }
            row = products[product_id]
            untaxed = self._convert_to_company_currency(order, line.price_subtotal)
            raw_amount = line.price_total if self.amount_basis == 'total' else line.price_subtotal
            amount = self._convert_to_company_currency(order, raw_amount)
            unit_price = untaxed / qty if qty else 0.0
            row['qty'] += qty
            row['untaxed'] += untaxed
            row['amount'] += amount
            row['min_price'] = unit_price if row['min_price'] is None else min(row['min_price'], unit_price)
            row['max_price'] = unit_price if row['max_price'] is None else max(row['max_price'], unit_price)
            row['supplier_ids'].add(order.partner_id.id)
            row['order_ids'].add(order.id)
            all_order_ids.add(order.id)
            local_date = self._local_date(order.date_order)
            if row['last_date'] is None or (local_date and local_date >= row['last_date']):
                row['last_date'] = local_date
                row['last_price'] = unit_price
                row['last_supplier'] = order.partner_id.display_name or ''

        rows = []
        for row in products.values():
            avg_price = row['untaxed'] / row['qty'] if row['qty'] else 0.0
            min_price = row['min_price'] or 0.0
            max_price = row['max_price'] or 0.0
            range_pct = ((max_price - min_price) / min_price * 100.0) if min_price else 0.0
            last_vs_avg_pct = ((row['last_price'] - avg_price) / avg_price * 100.0) if avg_price else 0.0
            rows.append({
                'product': row['product'],
                'uom': row['uom'],
                'qty': row['qty'],
                'avg_price': avg_price,
                'min_price': min_price,
                'max_price': max_price,
                'last_price': row['last_price'],
                'range_pct': range_pct,
                'last_vs_avg_pct': last_vs_avg_pct,
                'suppliers': len(row['supplier_ids']),
                'last_supplier': row['last_supplier'],
                'last_date': row['last_date'],
                'amount': row['amount'],
            })
        rows.sort(key=lambda r: r['amount'], reverse=True)

        columns = [
            {'key': 'product', 'label': 'PRODUCTO', 'type': 'text', 'align': 'left'},
            {'key': 'uom', 'label': 'UDM', 'type': 'text', 'align': 'center'},
            {'key': 'qty', 'label': 'CANTIDAD', 'type': 'qty', 'align': 'right'},
            {'key': 'avg_price', 'label': 'PRECIO PROM.', 'type': 'money', 'align': 'right'},
            {'key': 'min_price', 'label': 'PRECIO MÍN.', 'type': 'money', 'align': 'right'},
            {'key': 'max_price', 'label': 'PRECIO MÁX.', 'type': 'money', 'align': 'right'},
            {'key': 'last_price', 'label': 'ÚLTIMO PRECIO', 'type': 'money', 'align': 'right'},
            {'key': 'range_pct', 'label': 'RANGO PRECIO %', 'type': 'percent', 'align': 'right'},
            {'key': 'last_vs_avg_pct', 'label': 'ÚLTIMO VS PROM. %', 'type': 'percent', 'align': 'right'},
            {'key': 'suppliers', 'label': 'PROVEEDORES', 'type': 'int', 'align': 'right'},
            {'key': 'last_supplier', 'label': 'ÚLTIMO PROVEEDOR', 'type': 'text', 'align': 'left'},
            {'key': 'last_date', 'label': 'ÚLTIMA FECHA', 'type': 'date', 'align': 'center'},
            {'key': 'amount', 'label': 'TOTAL COMPRA', 'type': 'money', 'align': 'right'},
        ]
        total_amount = sum(r['amount'] for r in rows)
        total_qty = sum(r['qty'] for r in rows)
        data = self._base_data(_('ANÁLISIS DE VARIACIÓN DE PRECIOS DE COMPRA'))
        data.update({
            'analysis_columns': columns,
            'analysis_rows': rows,
            'order_count': len(all_order_ids),
            'summary': [
                {'label': 'Productos', 'value': len(rows), 'type': 'int'},
                {'label': 'Órdenes', 'value': len(all_order_ids), 'type': 'int'},
                {'label': 'Cantidad', 'value': total_qty, 'type': 'qty'},
                {'label': 'Compra total', 'value': total_amount, 'type': 'money'},
            ],
            'note': _('Los precios se calculan sin impuestos y normalizados a la UDM base del producto. Rango de precio = diferencia entre máximo y mínimo respecto al mínimo; Último vs Promedio muestra si el último costo subió o bajó frente al promedio del rango.'),
        })
        return data

    def _build_report_data(self):
        self.ensure_one()
        self._validate()
        orders = self._get_orders()
        if self.analysis_type == 'ranking':
            return self._build_ranking_data(orders)
        if self.analysis_type == 'evolution':
            return self._build_evolution_data(orders)
        if self.analysis_type == 'price_variation':
            return self._build_price_variation_data(orders)
        return self._build_standard_data(orders)

    # -------------------------------------------------------------------------
    # ESI - formateo genérico para HTML/PDF/Excel de los análisis nuevos
    # -------------------------------------------------------------------------
    def _format_analysis_value(self, value, value_type):
        if value_type == 'money':
            return self._fmt_money(value)
        if value_type == 'qty':
            return self._fmt_qty(value)
        if value_type == 'percent':
            return self._fmt_percent(value)
        if value_type == 'int':
            return str(int(value or 0))
        if value_type == 'date':
            return fields.Date.to_string(value) if value else ''
        return str(value or '')

    def _build_analysis_html(self, data):
        company = data['company']
        currency = data['currency']
        html = ['<div style="font-family:Arial,sans-serif;color:#222;background:#fff;padding:12px;">']
        html.append('<div style="display:flex;justify-content:space-between;align-items:flex-start;">')
        html.append('<div><img src="/web/image/res.company/%s/logo" style="max-height:70px;max-width:220px;"/></div>' % company.id)
        html.append('<div style="text-align:right;font-size:12px;"><b>%s</b><br/>%s</div>' % (escape(company.display_name or ''), escape(company.country_id.name or '')))
        html.append('</div>')
        html.append('<h2 style="text-align:center;margin:18px 0 12px;color:#3f4b57;">%s</h2>' % escape(data['title']))
        html.append('<table style="width:100%;font-size:12px;margin-bottom:10px;"><tr>')
        html.append('<td><b>Compañía:</b> %s</td><td><b>Rango:</b> %s</td></tr>' % (escape(company.display_name or ''), escape(data['period'])))
        html.append('<tr><td><b>Análisis:</b> %s</td><td><b>Importe:</b> %s &nbsp; | &nbsp; <b>Estado:</b> %s</td></tr></table>' % (
            escape(data['analysis_label'] or ''), escape(data['amount_label'] or ''), escape(data['state_label'] or '')))
        html.append('<div style="font-size:12px;margin:8px 0;"><b>Órdenes incluidas:</b> %s &nbsp;&nbsp; <b>Moneda:</b> %s</div>' % (data['order_count'], escape(currency.name or '')))
        if data.get('summary'):
            html.append('<table style="border-collapse:collapse;width:100%;font-size:11px;margin:8px 0 12px;"><tr>')
            for item in data['summary']:
                html.append('<td style="border:1px solid #b8c3cc;background:#f4f7f9;padding:6px;"><b>%s:</b> %s</td>' % (
                    escape(item['label']), escape(self._format_analysis_value(item['value'], item['type']))))
            html.append('</tr></table>')
        if not data['analysis_rows']:
            html.append('<div style="padding:25px;border:1px solid #ddd;text-align:center;">No se encontraron compras con los filtros seleccionados.</div>')
        else:
            html.append('<table style="border-collapse:collapse;width:100%;font-size:10px;">')
            html.append('<thead><tr style="background:#e7edf3;">')
            for col in data['analysis_columns']:
                html.append('<th style="border:1px solid #89949e;padding:5px;text-align:%s;">%s</th>' % (col.get('align', 'left'), escape(col['label'])))
            html.append('</tr></thead><tbody>')
            for row in data['analysis_rows']:
                html.append('<tr>')
                for col in data['analysis_columns']:
                    text = self._format_analysis_value(row.get(col['key']), col['type'])
                    html.append('<td style="border:1px solid #aab2b9;padding:4px;text-align:%s;">%s</td>' % (col.get('align', 'left'), escape(text)))
                html.append('</tr>')
            html.append('</tbody></table>')
        if data.get('note'):
            html.append('<p style="font-size:10px;color:#666;margin-top:10px;">%s</p>' % escape(data['note']))
        html.append('</div>')
        return ''.join(html)

    def _build_standard_html(self, data):
        company = data['company']
        currency = data['currency']
        show_group = self.group_by != 'product'
        html = ['<div style="font-family:Arial,sans-serif;color:#222;background:#fff;padding:12px;">']
        html.append('<div style="display:flex;justify-content:space-between;align-items:flex-start;">')
        html.append('<div><img src="/web/image/res.company/%s/logo" style="max-height:70px;max-width:220px;"/></div>' % company.id)
        html.append('<div style="text-align:right;font-size:12px;"><b>%s</b><br/>%s</div>' % (escape(company.display_name or ''), escape(company.country_id.name or '')))
        html.append('</div>')
        html.append('<h2 style="text-align:center;margin:18px 0 12px;color:#3f4b57;">%s</h2>' % escape(data['title']))
        html.append('<table style="width:100%;font-size:12px;margin-bottom:10px;"><tr>')
        html.append('<td><b>Compañía:</b> %s</td><td><b>Rango:</b> %s</td></tr>' % (escape(company.display_name or ''), escape(data['period'])))
        html.append('<tr><td><b>Agrupado por:</b> %s</td><td><b>Importe:</b> %s &nbsp; | &nbsp; <b>Estado:</b> %s</td></tr></table>' % (escape(data['group_label']), escape(data['amount_label'] or ''), escape(data['state_label'] or '')))
        html.append('<div style="font-size:12px;margin:8px 0;"><b>Órdenes incluidas:</b> %s &nbsp;&nbsp; <b>Moneda:</b> %s</div>' % (data['order_count'], escape(currency.name or '')))
        for group in data['groups']:
            if show_group:
                html.append('<div style="background:#eef3f7;border:1px solid #b8c3cc;padding:6px 8px;margin-top:12px;font-weight:bold;">%s: %s</div>' % (escape(data['group_label']), escape(group['name'] or '')))
            html.append('<table style="border-collapse:collapse;width:100%;font-size:11px;">')
            html.append('<thead><tr style="background:#e7edf3;"><th style="border:1px solid #89949e;padding:5px;width:35px;">Nro</th><th style="border:1px solid #89949e;padding:5px;text-align:left;">PRODUCTO</th><th style="border:1px solid #89949e;padding:5px;">UDM</th><th style="border:1px solid #89949e;padding:5px;text-align:right;">CANTIDAD</th><th style="border:1px solid #89949e;padding:5px;text-align:right;">TOTAL COMPRA</th></tr></thead><tbody>')
            for idx, row in enumerate(group['rows'], 1):
                html.append('<tr><td style="border:1px solid #aab2b9;padding:4px;text-align:center;">%s</td><td style="border:1px solid #aab2b9;padding:4px;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:center;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td><td style="border:1px solid #aab2b9;padding:4px;text-align:right;">%s</td></tr>' % (idx, escape(row['product'] or ''), escape(row['uom'] or ''), self._fmt_qty(row['qty']), self._fmt_money(row['amount'])))
            html.append('<tr style="font-weight:bold;background:#f7f8f9;"><td colspan="3" style="border:1px solid #89949e;padding:5px;text-align:right;">SUBTOTAL</td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td><td style="border:1px solid #89949e;padding:5px;text-align:right;">%s</td></tr></tbody></table>' % (self._fmt_qty(group['qty']), self._fmt_money(group['amount'])))
        if not data['groups']:
            html.append('<div style="padding:25px;border:1px solid #ddd;text-align:center;">No se encontraron compras con los filtros seleccionados.</div>')
        else:
            html.append('<table style="border-collapse:collapse;width:100%;font-size:12px;margin-top:15px;font-weight:bold;"><tr style="background:#dfe7ee;"><td style="border:1px solid #7f8b94;padding:7px;">TOTAL GENERAL</td><td style="border:1px solid #7f8b94;padding:7px;text-align:right;">Cantidad: %s</td><td style="border:1px solid #7f8b94;padding:7px;text-align:right;">Compra: %s %s</td></tr></table>' % (self._fmt_qty(data['totals']['qty']), self._fmt_money(data['totals']['amount']), escape(currency.name or '')))
        html.append('</div>')
        return ''.join(html)

    def _build_html(self, data):
        if data['analysis_type'] == 'standard':
            return self._build_standard_html(data)
        return self._build_analysis_html(data)

    def action_view_report(self):
        self.ensure_one()
        data = self._build_report_data()
        self.preview_html = self._build_html(data)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Informe de Compras'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_print_pdf(self):
        self.ensure_one()
        self._validate()
        return self.env.ref('esi_compras_report_v13.action_report_esi_purchase_pdf').report_action(self)

    def _excel_format_for_type(self, value_type, formats):
        if value_type == 'money':
            return formats['money']
        if value_type == 'qty':
            return formats['qty']
        if value_type == 'percent':
            return formats['percent']
        if value_type == 'int':
            return formats['int']
        if value_type == 'date':
            return formats['date']
        return formats['text']

    def _write_analysis_excel(self, workbook, sheet, data):
        fmt_title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
        fmt_label = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#EEF3F7'})
        fmt_header = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#DDE7F0', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        formats = {
            'text': workbook.add_format({'border': 1}),
            'int': workbook.add_format({'border': 1, 'num_format': '0'}),
            'qty': workbook.add_format({'border': 1, 'num_format': '#,##0.' + ('0' * self._qty_digits())}),
            'money': workbook.add_format({'border': 1, 'num_format': '#,##0.' + ('0' * self._money_digits())}),
            'percent': workbook.add_format({'border': 1, 'num_format': '0.00" %"'}),
            'date': workbook.add_format({'border': 1, 'num_format': 'dd/mm/yyyy'}),
        }
        last_col = max(len(data['analysis_columns']) - 1, 4)
        sheet.merge_range(0, 0, 0, last_col, data['title'], fmt_title)
        sheet.write(2, 0, 'Compañía', fmt_label)
        sheet.write(2, 1, data['company'].display_name or '')
        sheet.write(2, 3, 'Rango', fmt_label)
        sheet.write(2, 4, data['period'])
        sheet.write(3, 0, 'Análisis', fmt_label)
        sheet.write(3, 1, data['analysis_label'])
        sheet.write(3, 3, 'Importe', fmt_label)
        sheet.write(3, 4, data['amount_label'])
        sheet.write(4, 0, 'Estado', fmt_label)
        sheet.write(4, 1, data['state_label'])
        sheet.write(4, 3, 'Moneda', fmt_label)
        sheet.write(4, 4, data['currency'].name or '')

        row_idx = 6
        if data.get('summary'):
            for idx, item in enumerate(data['summary']):
                col = (idx % 3) * 2
                if idx and idx % 3 == 0:
                    row_idx += 1
                sheet.write(row_idx, col, item['label'], fmt_label)
                value = item['value']
                vtype = item['type']
                fmt = self._excel_format_for_type(vtype, formats)
                if vtype in ('money', 'qty', 'percent', 'int'):
                    sheet.write_number(row_idx, col + 1, value or 0.0, fmt)
                elif vtype == 'date' and value:
                    sheet.write_datetime(row_idx, col + 1, datetime.combine(value, time.min), fmt)
                else:
                    sheet.write(row_idx, col + 1, str(value or ''), fmt)
            row_idx += 2

        header_row = row_idx
        for c, col in enumerate(data['analysis_columns']):
            sheet.write(row_idx, c, col['label'], fmt_header)
        row_idx += 1
        for row in data['analysis_rows']:
            for c, col in enumerate(data['analysis_columns']):
                value = row.get(col['key'])
                fmt = self._excel_format_for_type(col['type'], formats)
                if col['type'] in ('money', 'qty', 'percent', 'int'):
                    sheet.write_number(row_idx, c, value or 0.0, fmt)
                elif col['type'] == 'date' and value:
                    sheet.write_datetime(row_idx, c, datetime.combine(value, time.min), fmt)
                else:
                    sheet.write(row_idx, c, str(value or ''), fmt)
            row_idx += 1
        sheet.freeze_panes(header_row + 1, 0)
        sheet.set_column(0, 0, 10)
        if data['analysis_columns']:
            sheet.set_column(1, 1, 30)
            sheet.set_column(2, len(data['analysis_columns']) - 1, 15)
            # Último proveedor requiere más espacio en el análisis de precios.
            if self.analysis_type == 'price_variation' and len(data['analysis_columns']) > 10:
                sheet.set_column(10, 10, 30)
        if data.get('note'):
            fmt_note = workbook.add_format({'italic': True, 'font_size': 9, 'font_color': '#666666'})
            row_idx += 1
            sheet.merge_range(row_idx, 0, row_idx, max(len(data['analysis_columns']) - 1, 1), data['note'], fmt_note)

    def _write_standard_excel(self, workbook, sheet, data):
        sheet.freeze_panes(7, 0)
        fmt_title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'})
        fmt_label = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#EEF3F7'})
        fmt_header = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#DDE7F0', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        fmt_text = workbook.add_format({'border': 1})
        fmt_center = workbook.add_format({'border': 1, 'align': 'center'})
        fmt_qty = workbook.add_format({'border': 1, 'num_format': '#,##0.' + ('0' * self._qty_digits())})
        fmt_money = workbook.add_format({'border': 1, 'num_format': '#,##0.' + ('0' * self._money_digits())})
        fmt_group = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#EEF3F7'})
        fmt_sub = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#F7F8F9'})
        fmt_total = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#DDE7F0'})

        columns = ['Nro', 'Producto', 'UDM', 'Cantidad', 'Total Compra']
        last_col = len(columns) - 1
        sheet.merge_range(0, 0, 0, last_col, data['title'], fmt_title)
        sheet.write(2, 0, 'Compañía', fmt_label)
        sheet.write(2, 1, data['company'].display_name or '')
        sheet.write(2, 3, 'Rango', fmt_label)
        sheet.write(2, 4, data['period'])
        sheet.write(3, 0, 'Agrupado por', fmt_label)
        sheet.write(3, 1, data['group_label'])
        sheet.write(3, 3, 'Importe', fmt_label)
        sheet.write(3, 4, data['amount_label'])
        sheet.write(4, 0, 'Estado', fmt_label)
        sheet.write(4, 1, data['state_label'])
        sheet.write(4, 3, 'Moneda', fmt_label)
        sheet.write(4, 4, data['currency'].name or '')
        sheet.write(5, 0, 'Órdenes incluidas', fmt_label)
        sheet.write_number(5, 1, data['order_count'])

        row_idx = 7
        show_group = self.group_by != 'product'
        for group in data['groups']:
            if show_group:
                sheet.merge_range(row_idx, 0, row_idx, last_col, '%s: %s' % (data['group_label'], group['name']), fmt_group)
                row_idx += 1
            for c, title in enumerate(columns):
                sheet.write(row_idx, c, title, fmt_header)
            row_idx += 1
            for idx, row in enumerate(group['rows'], 1):
                sheet.write_number(row_idx, 0, idx, fmt_center)
                sheet.write(row_idx, 1, row['product'], fmt_text)
                sheet.write(row_idx, 2, row['uom'], fmt_center)
                sheet.write_number(row_idx, 3, row['qty'], fmt_qty)
                sheet.write_number(row_idx, 4, row['amount'], fmt_money)
                row_idx += 1
            sheet.merge_range(row_idx, 0, row_idx, 2, 'SUBTOTAL', fmt_sub)
            sheet.write_number(row_idx, 3, group['qty'], fmt_sub)
            sheet.write_number(row_idx, 4, group['amount'], fmt_sub)
            row_idx += 2

        if data['groups']:
            sheet.merge_range(row_idx, 0, row_idx, 2, 'TOTAL GENERAL', fmt_total)
            sheet.write_number(row_idx, 3, data['totals']['qty'], fmt_total)
            sheet.write_number(row_idx, 4, data['totals']['amount'], fmt_total)

        sheet.set_column(0, 0, 7)
        sheet.set_column(1, 1, 42)
        sheet.set_column(2, 2, 12)
        sheet.set_column(3, last_col, 18)

    def action_export_excel(self):
        self.ensure_one()
        if xlsxwriter is None:
            raise UserError(_('No está instalada la librería Python xlsxwriter en el servidor.'))
        data = self._build_report_data()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Compras')
        sheet.hide_gridlines(2)

        if data['analysis_type'] == 'standard':
            self._write_standard_excel(workbook, sheet, data)
        else:
            self._write_analysis_excel(workbook, sheet, data)

        workbook.close()
        output.seek(0)
        analysis_slug = self.analysis_type or 'standard'
        filename = 'Informe_Compras_%s_%s_%s.xlsx' % (
            analysis_slug, fields.Date.to_string(self.date_from), fields.Date.to_string(self.date_to))
        self.write({'excel_file': base64.b64encode(output.read()), 'excel_filename': filename})
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=%s&id=%s&field=excel_file&filename_field=excel_filename&download=true' % (self._name, self.id),
            'target': 'self',
        }
