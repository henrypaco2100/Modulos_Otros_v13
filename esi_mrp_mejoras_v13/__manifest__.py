# -*- coding: utf-8 -*-
{
    'name': 'ESI - Mejoras MRP Calzado',
    'version': '13.0.1.1.2',
    'summary': 'Tiempos estándar, operadores, destajo y partes de producción para fabricación de calzado',
    'author': 'ESI - Especialistas en Sistemas Integrados',
    'category': 'Manufacturing',
    'license': 'LGPL-3',
    'depends': ['mrp'],
    'data': [
        'security/esi_mrp_security.xml',
        'security/ir.model.access.csv',
        'views/mrp_operator_views.xml',
        'views/mrp_routing_views.xml',
        'views/mrp_workorder_views.xml',
        'views/mrp_productivity_views.xml',
        'views/mrp_piecework_note_views.xml',
        'views/res_company_views.xml',
    ],
    'installable': True,
    'application': False,
}
