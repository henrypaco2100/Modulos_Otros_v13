# -*- coding: utf-8 -*-
{
    'name': 'ESI - Informes de Ventas',
    'version': '13.0.2.0.0',
    'summary': 'Ventas: resumen, Pareto ABC, tendencias y análisis de precios/margen en HTML, PDF y Excel',
    'author': 'ESI - Especialistas en Sistemas Integrados',
    'category': 'Sales/Reporting',
    'license': 'LGPL-3',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_report_views.xml',
        'report/sale_report_templates.xml',
    ],
    'installable': True,
    'application': False,
}
