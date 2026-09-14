# -*- coding: utf-8 -*-
import base64
import logging

from odoo import api, fields, SUPERUSER_ID
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)
MODULE = 'esi_demo_insumos_v13'
DEMO_DATE = '2026-09-14'
DEMO_DATETIME = '2026-09-14 12:00:00'


PRODUCTS = [
    {'code': 'LIM-001', 'name': 'Detergente líquido — bidón de 5 litros', 'category': 'Limpieza', 'cost': 45.0, 'price': 65.0, 'qty': 30.0},
    {'code': 'LIM-002', 'name': 'Lavandina — botella de 1 litro', 'category': 'Limpieza', 'cost': 6.0, 'price': 10.0, 'qty': 100.0},
    {'code': 'LIM-003', 'name': 'Desinfectante para pisos — bidón de 5 litros', 'category': 'Limpieza', 'cost': 32.0, 'price': 48.0, 'qty': 40.0},
    {'code': 'LIM-004', 'name': 'Jabón líquido para manos — botella de 1 litro', 'category': 'Limpieza', 'cost': 14.0, 'price': 22.0, 'qty': 60.0},
    {'code': 'LIM-005', 'name': 'Papel higiénico industrial — paquete de 6 rollos', 'category': 'Limpieza', 'cost': 48.0, 'price': 68.0, 'qty': 25.0},
    {'code': 'EMB-001', 'name': 'Cinta de embalaje transparente — rollo de 48 mm × 100 m', 'category': 'Embalaje', 'cost': 8.0, 'price': 13.0, 'qty': 120.0},
    {'code': 'EMB-002', 'name': 'Film stretch transparente — rollo de 50 cm × 300 m', 'category': 'Embalaje', 'cost': 55.0, 'price': 78.0, 'qty': 25.0},
    {'code': 'EMB-003', 'name': 'Caja de cartón corrugado — 40 × 30 × 30 cm', 'category': 'Embalaje', 'cost': 5.0, 'price': 9.0, 'qty': 200.0},
    {'code': 'EMB-004', 'name': 'Bolsas de polietileno — paquete de 100, tamaño 30 × 40 cm', 'category': 'Embalaje', 'cost': 18.0, 'price': 28.0, 'qty': 50.0},
    {'code': 'EMB-005', 'name': 'Sobres acolchados — paquete de 10, tamaño 25 × 35 cm', 'category': 'Embalaje', 'cost': 20.0, 'price': 32.0, 'qty': 40.0},
    {'code': 'SEG-001', 'name': 'Guantes de nitrilo, talla M — caja de 100 unidades', 'category': 'Seguridad', 'cost': 32.0, 'price': 48.0, 'qty': 40.0},
    {'code': 'SEG-002', 'name': 'Barbijos descartables — caja de 50 unidades', 'category': 'Seguridad', 'cost': 10.0, 'price': 18.0, 'qty': 60.0},
    {'code': 'SEG-003', 'name': 'Lentes de seguridad transparentes', 'category': 'Seguridad', 'cost': 12.0, 'price': 20.0, 'qty': 30.0},
    {'code': 'SEG-004', 'name': 'Casco de seguridad amarillo', 'category': 'Seguridad', 'cost': 28.0, 'price': 42.0, 'qty': 20.0},
    {'code': 'SEG-005', 'name': 'Chaleco reflectivo naranja, talla L', 'category': 'Seguridad', 'cost': 18.0, 'price': 30.0, 'qty': 25.0},
]

SALES = [
    {
        'name': 'DEMO-V-001',
        'partner': 'Hotel Las Palmeras',
        'term_days': 0,
        'note': 'Compra insumos para limpiar habitaciones y áreas comunes. Pago total al contado mediante transferencia bancaria.',
        'payment_amount': 1890.0,
        'payment_journal': 'bank',
        'payment_memo': 'DEMO-V-001 - Transferencia bancaria',
        'lines': [('LIM-001', 10, 65), ('LIM-002', 20, 10), ('LIM-003', 10, 48), ('LIM-004', 10, 22), ('LIM-005', 5, 68)],
    },
    {
        'name': 'DEMO-V-002',
        'partner': 'Tienda Online Oriente',
        'term_days': 15,
        'note': 'Compra materiales para empacar pedidos. Crédito a 15 días. Sin pago inicial. Vencimiento: 29/09/2026.',
        'payment_amount': 0.0,
        'payment_journal': None,
        'payment_memo': None,
        'lines': [('EMB-001', 30, 13), ('EMB-002', 5, 78), ('EMB-003', 80, 9), ('EMB-004', 10, 28), ('EMB-005', 10, 32)],
    },
    {
        'name': 'DEMO-V-003',
        'partner': 'Constructora Nuevo Horizonte',
        'term_days': 30,
        'note': 'Compra insumos de seguridad. Abono de Bs 500 mediante QR; saldo Bs 840 a 30 días. Vencimiento: 14/10/2026.',
        'payment_amount': 500.0,
        'payment_journal': 'bank',
        'payment_memo': 'DEMO-V-003 - Abono QR',
        'lines': [('SEG-001', 5, 48), ('SEG-002', 10, 18), ('SEG-003', 10, 20), ('SEG-004', 10, 42), ('SEG-005', 10, 30)],
    },
    {
        'name': 'DEMO-V-004',
        'partner': 'Limpieza Integral Brisa',
        'term_days': 0,
        'note': 'Compra insumos para oficinas y locales comerciales. Pago total al contado en efectivo.',
        'payment_amount': 2570.0,
        'payment_journal': 'cash',
        'payment_memo': 'DEMO-V-004 - Pago en efectivo',
        'lines': [('LIM-001', 8, 65), ('LIM-002', 30, 10), ('LIM-003', 10, 48), ('LIM-004', 15, 22), ('LIM-005', 5, 68), ('SEG-001', 8, 48), ('SEG-002', 12, 18)],
    },
]

ACCOUNT_PLAN = [
    ('111001', 'Caja moneda nacional', 'liquidity'),
    ('111002', 'Caja chica', 'liquidity'),
    ('111003', 'Banco moneda nacional', 'liquidity'),
    ('112001', 'Cuentas por cobrar a clientes', 'receivable'),
    ('113001', 'Anticipos a proveedores', 'current_assets'),
    ('114001', 'IVA crédito fiscal', 'current_assets'),
    ('115001', 'Inventario de insumos de limpieza', 'current_assets'),
    ('115002', 'Inventario de insumos de embalaje', 'current_assets'),
    ('115003', 'Inventario de insumos de seguridad', 'current_assets'),
    ('121001', 'Muebles y enseres', 'fixed_assets'),
    ('121002', 'Equipos de computación', 'fixed_assets'),
    ('211001', 'Proveedores de mercaderías por pagar', 'payable'),
    ('211002', 'Proveedores de servicios por pagar', 'payable'),
    ('213001', 'IVA débito fiscal', 'current_liabilities'),
    ('213002', 'IVA por pagar', 'current_liabilities'),
    ('214001', 'Sueldos y salarios por pagar', 'current_liabilities'),
    ('215001', 'Préstamos bancarios a corto plazo', 'current_liabilities'),
    ('216001', 'Anticipos de clientes', 'current_liabilities'),
    ('311001', 'Capital social', 'equity'),
    ('331001', 'Utilidades acumuladas', 'equity'),
    ('331002', 'Pérdidas acumuladas', 'equity'),
    ('411001', 'Ventas de insumos de limpieza', 'revenue'),
    ('411002', 'Ventas de insumos de embalaje', 'revenue'),
    ('411003', 'Ventas de insumos de seguridad', 'revenue'),
    ('412001', 'Devoluciones sobre ventas', 'revenue'),
    ('511001', 'Costo de ventas de limpieza', 'direct_costs'),
    ('511002', 'Costo de ventas de embalaje', 'direct_costs'),
    ('511003', 'Costo de ventas de seguridad', 'direct_costs'),
    ('611001', 'Sueldos y salarios administrativos', 'expenses'),
    ('611004', 'Alquiler de local y almacén', 'expenses'),
    ('611005', 'Servicios básicos: agua y electricidad', 'expenses'),
    ('611006', 'Telefonía e internet', 'expenses'),
    ('611007', 'Papelería y útiles de oficina', 'expenses'),
    ('611009', 'Sistema, hosting y soporte', 'expenses'),
    ('612004', 'Publicidad y promoción', 'expenses'),
    ('612005', 'Transporte y distribución', 'expenses'),
]

TYPE_XMLIDS = {
    'liquidity': 'account.data_account_type_liquidity',
    'receivable': 'account.data_account_type_receivable',
    'payable': 'account.data_account_type_payable',
    'current_assets': 'account.data_account_type_current_assets',
    'fixed_assets': 'account.data_account_type_fixed_assets',
    'current_liabilities': 'account.data_account_type_current_liabilities',
    'equity': 'account.data_account_type_equity',
    'revenue': 'account.data_account_type_revenue',
    'direct_costs': 'account.data_account_type_direct_costs',
    'expenses': 'account.data_account_type_expenses',
}

CATEGORY_ACCOUNT_MAP = {
    'Limpieza': {'inventory': '115001', 'income': '411001', 'cogs': '511001'},
    'Embalaje': {'inventory': '115002', 'income': '411002', 'cogs': '511002'},
    'Seguridad': {'inventory': '115003', 'income': '411003', 'cogs': '511003'},
}


def _register_xmlid(env, name, record):
    imd = env['ir.model.data'].sudo()
    existing = imd.search([('module', '=', MODULE), ('name', '=', name)], limit=1)
    if not existing:
        imd.create({
            'module': MODULE,
            'name': name,
            'model': record._name,
            'res_id': record.id,
            'noupdate': True,
        })
    return record


def _image_b64(code):
    path = get_module_resource(MODULE, 'static', 'src', 'img', 'products', '%s.png' % code)
    if not path:
        return False
    try:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read())
    except Exception:
        _logger.exception('No se pudo cargar la imagen del producto %s', code)
        return False


def _account(env, company, code, name=None, type_key=None):
    rec = env['account.account'].sudo().search([('company_id', '=', company.id), ('code', '=', code)], limit=1)
    if rec:
        return rec
    vals = {
        'code': code,
        'name': name,
        'company_id': company.id,
        'user_type_id': env.ref(TYPE_XMLIDS[type_key]).id,
        'reconcile': type_key in ('receivable', 'payable'),
    }
    rec = env['account.account'].sudo().create(vals)
    return _register_xmlid(env, 'account_%s' % code, rec)


def _journal(env, company, code, name, jtype, debit_account, credit_account):
    rec = env['account.journal'].sudo().search([('company_id', '=', company.id), ('code', '=', code)], limit=1)
    if rec:
        return rec
    vals = {
        'name': name,
        'code': code,
        'type': jtype,
        'company_id': company.id,
        'default_debit_account_id': debit_account.id,
        'default_credit_account_id': credit_account.id,
    }
    rec = env['account.journal'].sudo().create(vals)
    return _register_xmlid(env, 'journal_%s' % code.lower(), rec)


def _payment_term(env, company, days):
    xmlid = {0: 'account.account_payment_term_immediate', 15: 'account.account_payment_term_15days', 30: 'account.account_payment_term_30days'}[days]
    term = env.ref(xmlid, raise_if_not_found=False)
    if term and (not term.company_id or term.company_id == company):
        return term
    name = 'DEMO - Contado' if days == 0 else 'DEMO - %s días' % days
    term = env['account.payment.term'].sudo().search([('name', '=', name), '|', ('company_id', '=', False), ('company_id', '=', company.id)], limit=1)
    if term:
        return term
    term = env['account.payment.term'].sudo().create({
        'name': name,
        'company_id': company.id,
        'line_ids': [(5, 0, 0), (0, 0, {'value': 'balance', 'value_amount': 0.0, 'sequence': 500, 'days': days, 'option': 'day_after_invoice_date'})],
    })
    return _register_xmlid(env, 'payment_term_%s' % days, term)


def _partner(env, company, name, is_supplier=False, comment=''):
    rec = env['res.partner'].sudo().search([('name', '=', name), ('company_id', 'in', [False, company.id])], limit=1)
    vals = {
        'name': name,
        'company_type': 'company',
        'company_id': False,
        'comment': comment,
    }
    if 'customer_rank' in env['res.partner']._fields:
        vals['customer_rank'] = 0 if is_supplier else 1
    if 'supplier_rank' in env['res.partner']._fields:
        vals['supplier_rank'] = 1 if is_supplier else 0
    if rec:
        rec.sudo().write({k: v for k, v in vals.items() if k in rec._fields and k != 'company_id'})
    else:
        rec = env['res.partner'].sudo().create(vals)
        safe = name.lower().replace(' ', '_').replace('.', '').replace('-', '_')[:40]
        _register_xmlid(env, 'partner_%s' % safe, rec)
    return rec


def _validate_picking(picking, when):
    if not picking or picking.state in ('done', 'cancel'):
        return
    if picking.state == 'draft':
        picking.action_confirm()
    picking.action_assign()
    for move in picking.move_lines.filtered(lambda m: m.state not in ('done', 'cancel')):
        move.quantity_done = move.product_uom_qty
    result = picking.button_validate()
    if isinstance(result, dict) and result.get('res_model') == 'stock.immediate.transfer' and result.get('res_id'):
        picking.env['stock.immediate.transfer'].browse(result['res_id']).process()
    elif isinstance(result, dict) and result.get('res_model') == 'stock.backorder.confirmation' and result.get('res_id'):
        picking.env['stock.backorder.confirmation'].browse(result['res_id']).process_cancel_backorder()
    if picking.state == 'done':
        picking.sudo().write({'date_done': when})
        picking.move_lines.sudo().write({'date': when, 'date_expected': when})


def _create_payment(env, invoice, amount, journal, method, memo, date):
    if not amount:
        return False
    existing = env['account.payment'].sudo().search([
        ('partner_id', '=', invoice.partner_id.id),
        ('amount', '=', amount),
        ('communication', '=', memo),
    ], limit=1)
    if existing:
        return existing
    payment = env['account.payment'].sudo().with_context(active_model='account.move', active_ids=invoice.ids).create({
        'payment_type': 'inbound' if invoice.type == 'out_invoice' else 'outbound',
        'partner_type': 'customer' if invoice.type == 'out_invoice' else 'supplier',
        'partner_id': invoice.partner_id.id,
        'amount': amount,
        'currency_id': invoice.currency_id.id,
        'payment_date': date,
        'journal_id': journal.id,
        'payment_method_id': method.id,
        'communication': memo,
        'invoice_ids': [(6, 0, invoice.ids)],
    })
    payment.post()
    return payment


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    company = env.user.company_id

    # 1) Plan de cuentas del Excel.
    accounts = {}
    for code, name, type_key in ACCOUNT_PLAN:
        accounts[code] = _account(env, company, code, name, type_key)

    # 2) Diarios mínimos para facturas y pagos.
    bank_journal = _journal(env, company, 'DBNK', 'DEMO Banco / Transferencias / QR', 'bank', accounts['111003'], accounts['111003'])
    cash_journal = _journal(env, company, 'DCSH', 'DEMO Caja', 'cash', accounts['111001'], accounts['111001'])
    sale_journal = _journal(env, company, 'DSAL', 'DEMO Ventas', 'sale', accounts['112001'], accounts['411001'])
    purchase_journal = _journal(env, company, 'DPUR', 'DEMO Compras', 'purchase', accounts['115001'], accounts['211001'])
    general_journal = _journal(env, company, 'DGEN', 'DEMO Operaciones varias', 'general', accounts['511001'], accounts['115001'])

    manual_in = env.ref('account.account_payment_method_manual_in')
    manual_out = env.ref('account.account_payment_method_manual_out')
    bank_journal.write({'inbound_payment_method_ids': [(4, manual_in.id)], 'outbound_payment_method_ids': [(4, manual_out.id)]})
    cash_journal.write({'inbound_payment_method_ids': [(4, manual_in.id)], 'outbound_payment_method_ids': [(4, manual_out.id)]})

    term0 = _payment_term(env, company, 0)
    term15 = _payment_term(env, company, 15)
    term30 = _payment_term(env, company, 30)
    terms = {0: term0, 15: term15, 30: term30}

    # 3) Contactos.
    supplier = _partner(env, company, 'Distribuidora Integral Oriente S.R.L.', True, 'Proveedor ficticio de la demo. Condición de pago: al contado.')
    customers = {}
    for sale in SALES:
        customers[sale['partner']] = _partner(env, company, sale['partner'], False, sale['note'])

    # Cuentas por cobrar / pagar de los contactos demo.
    for partner in customers.values():
        partner.with_context(force_company=company.id).sudo().write({'property_account_receivable_id': accounts['112001'].id})
    supplier.with_context(force_company=company.id).sudo().write({'property_account_payable_id': accounts['211001'].id})

    # 4) Categorías con costo promedio (AVCO) y valoración manual para una demo estable.
    categories = {}
    for cat_name, amap in CATEGORY_ACCOUNT_MAP.items():
        cat = env['product.category'].sudo().search([('name', '=', 'DEMO - %s' % cat_name)], limit=1)
        if not cat:
            cat = env['product.category'].sudo().create({
                'name': 'DEMO - %s' % cat_name,
                'property_cost_method': 'average',
                'property_valuation': 'manual_periodic',
                'property_account_income_categ_id': accounts[amap['income']].id,
                'property_account_expense_categ_id': accounts[amap['cogs']].id,
            })
            _register_xmlid(env, 'category_%s' % cat_name.lower(), cat)
        else:
            cat.sudo().write({
                'property_cost_method': 'average',
                'property_valuation': 'manual_periodic',
                'property_account_income_categ_id': accounts[amap['income']].id,
                'property_account_expense_categ_id': accounts[amap['cogs']].id,
            })
        categories[cat_name] = cat

    uom_unit = env.ref('uom.product_uom_unit')
    product_records = {}
    for item in PRODUCTS:
        tmpl = env['product.template'].sudo().search([('default_code', '=', item['code'])], limit=1)
        vals = {
            'name': item['name'],
            'default_code': item['code'],
            'type': 'product',
            'categ_id': categories[item['category']].id,
            'standard_price': item['cost'],
            'list_price': item['price'],
            'uom_id': uom_unit.id,
            'uom_po_id': uom_unit.id,
            'purchase_ok': True,
            'sale_ok': True,
            'invoice_policy': 'order',
            'taxes_id': [(6, 0, [])],
            'supplier_taxes_id': [(6, 0, [])],
        }
        img = _image_b64(item['code'])
        if img:
            vals['image_1920'] = img
        if tmpl:
            tmpl.sudo().write(vals)
        else:
            tmpl = env['product.template'].sudo().create(vals)
            _register_xmlid(env, 'product_%s' % item['code'].lower().replace('-', '_'), tmpl)
        product_records[item['code']] = tmpl.product_variant_id

    # 5) Lista de precios de la demo.
    pricelist = env['product.pricelist'].sudo().search([('name', '=', 'DEMO - Precios en Bs'), ('currency_id', '=', company.currency_id.id)], limit=1)
    if not pricelist:
        pricelist = env['product.pricelist'].sudo().create({'name': 'DEMO - Precios en Bs', 'currency_id': company.currency_id.id, 'company_id': company.id})
        _register_xmlid(env, 'pricelist_demo', pricelist)

    # 6) Orden de compra inicial: las cantidades coinciden con el Stock Inicial del Excel.
    purchase = env['purchase.order'].sudo().search([('name', '=', 'DEMO-OC-001'), ('company_id', '=', company.id)], limit=1)
    if not purchase:
        po_lines = []
        for item in PRODUCTS:
            product = product_records[item['code']]
            po_lines.append((0, 0, {
                'product_id': product.id,
                'name': item['name'],
                'product_qty': item['qty'],
                'product_uom': product.uom_po_id.id,
                'price_unit': item['cost'],
                'date_planned': DEMO_DATETIME,
                'taxes_id': [(6, 0, [])],
            }))
        purchase = env['purchase.order'].sudo().create({
            'name': 'DEMO-OC-001',
            'partner_id': supplier.id,
            'currency_id': company.currency_id.id,
            'date_order': DEMO_DATETIME,
            'date_planned': DEMO_DATETIME,
            'payment_term_id': term0.id,
            'partner_ref': 'DEMO-OC-001',
            'notes': 'Compra inicial de 865 unidades. Total Bs 13.555. Condición de pago: al contado.',
            'company_id': company.id,
            'order_line': po_lines,
        })
        purchase.button_confirm()
        if purchase.state == 'to approve':
            purchase.button_approve()
        purchase.sudo().write({'date_order': DEMO_DATETIME, 'date_approve': DEMO_DATETIME})
        for picking in purchase.picking_ids:
            _validate_picking(picking, DEMO_DATETIME)

    # 7) Factura de proveedor asociada a la compra y pagada al contado.
    vendor_bill = env['account.move'].sudo().search([
        ('type', '=', 'in_invoice'), ('partner_id', '=', supplier.id), ('invoice_origin', '=', 'DEMO-OC-001')
    ], limit=1)
    if not vendor_bill:
        bill_lines = []
        pol_by_code = {line.product_id.default_code: line for line in purchase.order_line if line.product_id}
        for item in PRODUCTS:
            product = product_records[item['code']]
            inv_acc = accounts[CATEGORY_ACCOUNT_MAP[item['category']]['inventory']]
            bill_lines.append((0, 0, {
                'product_id': product.id,
                'name': item['name'],
                'quantity': item['qty'],
                'price_unit': item['cost'],
                'account_id': inv_acc.id,
                'tax_ids': [(6, 0, [])],
                'product_uom_id': product.uom_id.id,
                'purchase_line_id': pol_by_code[item['code']].id,
            }))
        vendor_bill = env['account.move'].sudo().with_context(default_type='in_invoice').create({
            'type': 'in_invoice',
            'partner_id': supplier.id,
            'invoice_date': DEMO_DATE,
            'date': DEMO_DATE,
            'invoice_origin': 'DEMO-OC-001',
            'ref': 'DEMO-OC-001',
            'invoice_payment_term_id': term0.id,
            'journal_id': purchase_journal.id,
            'currency_id': company.currency_id.id,
            'invoice_line_ids': bill_lines,
        })
        vendor_bill.post()
    _create_payment(env, vendor_bill, 13555.0, bank_journal, manual_out, 'DEMO-OC-001 - Pago al contado', DEMO_DATE)

    # 8) Ventas, entregas, facturas y cobros según el Excel.
    created_invoices = {}
    for sale_data in SALES:
        partner = customers[sale_data['partner']]
        order = env['sale.order'].sudo().search([('name', '=', sale_data['name']), ('company_id', '=', company.id)], limit=1)
        if not order:
            lines = []
            for code, qty, price in sale_data['lines']:
                product = product_records[code]
                lines.append((0, 0, {
                    'product_id': product.id,
                    'name': product.name,
                    'product_uom_qty': qty,
                    'product_uom': product.uom_id.id,
                    'price_unit': price,
                    'tax_id': [(6, 0, [])],
                }))
            order = env['sale.order'].sudo().create({
                'name': sale_data['name'],
                'partner_id': partner.id,
                'partner_invoice_id': partner.id,
                'partner_shipping_id': partner.id,
                'pricelist_id': pricelist.id,
                'payment_term_id': terms[sale_data['term_days']].id,
                'date_order': DEMO_DATETIME,
                'client_order_ref': sale_data['name'],
                'reference': sale_data['name'],
                'note': sale_data['note'],
                'company_id': company.id,
                'order_line': lines,
            })
            order.action_confirm()
            order.sudo().write({'date_order': DEMO_DATETIME})
            for picking in order.picking_ids:
                _validate_picking(picking, DEMO_DATETIME)

        invoice = env['account.move'].sudo().search([('type', '=', 'out_invoice'), ('invoice_origin', '=', order.name)], limit=1)
        if not invoice:
            invoice = order.sudo().with_context(default_journal_id=sale_journal.id)._create_invoices(grouped=True)
            invoice.sudo().write({
                'invoice_date': DEMO_DATE,
                'date': DEMO_DATE,
                'invoice_payment_term_id': terms[sale_data['term_days']].id,
                'ref': sale_data['name'],
                'invoice_payment_ref': sale_data['name'],
                'journal_id': sale_journal.id,
            })
            invoice.post()
        created_invoices[sale_data['name']] = invoice
        if sale_data['payment_amount']:
            journal = bank_journal if sale_data['payment_journal'] == 'bank' else cash_journal
            _create_payment(env, invoice, sale_data['payment_amount'], journal, manual_in, sale_data['payment_memo'], DEMO_DATE)

    # 9) Asiento de costo de ventas, porque la valoración de inventario es manual.
    cogs_entry = env['account.move'].sudo().search([('ref', '=', 'DEMO-COGS-001'), ('company_id', '=', company.id)], limit=1)
    if not cogs_entry:
        sold_qty = {}
        product_data = {x['code']: x for x in PRODUCTS}
        for sale_data in SALES:
            for code, qty, _price in sale_data['lines']:
                sold_qty[code] = sold_qty.get(code, 0.0) + qty
        totals = {'Limpieza': 0.0, 'Embalaje': 0.0, 'Seguridad': 0.0}
        for code, qty in sold_qty.items():
            item = product_data[code]
            totals[item['category']] += qty * item['cost']
        move_lines = []
        for cat_name in ('Limpieza', 'Embalaje', 'Seguridad'):
            amount = totals[cat_name]
            amap = CATEGORY_ACCOUNT_MAP[cat_name]
            move_lines += [
                (0, 0, {'name': 'Costo de ventas - %s' % cat_name, 'account_id': accounts[amap['cogs']].id, 'debit': amount, 'credit': 0.0}),
                (0, 0, {'name': 'Salida de inventario - %s' % cat_name, 'account_id': accounts[amap['inventory']].id, 'debit': 0.0, 'credit': amount}),
            ]
        cogs_entry = env['account.move'].sudo().create({
            'type': 'entry',
            'date': DEMO_DATE,
            'journal_id': general_journal.id,
            'ref': 'DEMO-COGS-001',
            'line_ids': move_lines,
        })
        cogs_entry.post()

    # Marcador para poder identificar rápidamente la base demo.
    env['ir.config_parameter'].sudo().set_param('esi_demo_insumos_v13.loaded', '1')
    env['ir.config_parameter'].sudo().set_param('esi_demo_insumos_v13.source_date', DEMO_DATE)
    _logger.info('ESI Demo Insumos v13 instalada correctamente.')
