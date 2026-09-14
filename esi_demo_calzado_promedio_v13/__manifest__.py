# -*- coding: utf-8 -*-
{
    'name': 'ESI - Demo Calzado AVCO Odoo 13',
    'version': '13.0.1.0.1',
    'summary': 'Demo fábrica de calzado con costo promedio AVCO, compras recibidas, MRP, ventas y contabilidad',
    'author': 'ESI - Especialistas en Sistemas Integrados',
    'category': 'Manufacturing',
    'license': 'LGPL-3',
    'depends': [
        'esi_mrp_mejoras_v13',
        'esi_produccion_report_v13',
        'sale_management',
        'sale_stock',
        'purchase',
        'purchase_stock',
        'account',
        'stock_account',
        'stock',
        'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/demo_wizard_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
}
