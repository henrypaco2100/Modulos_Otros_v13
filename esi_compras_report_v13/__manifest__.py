# -*- coding: utf-8 -*-
{
    'name': 'ESI - Informes de Compras',
    'version': '13.0.2.0.0',
    'summary': 'Compras: resumen, Pareto ABC, tendencias y variación de precios en HTML, PDF y Excel',
    'author': 'ESI - Especialistas en Sistemas Integrados',
    'category': 'Purchases/Reporting',
    'license': 'LGPL-3',
    'depends': ['purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_report_views.xml',
        'report/purchase_report_templates.xml',
    ],
    'installable': True,
    'application': False,
}
