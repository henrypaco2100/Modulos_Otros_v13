# -*- coding: utf-8 -*-
{
    'name': 'ESI - Informes de Producción Calzado',
    'version': '13.0.5.1.0',
    'summary': 'Informes de producción, costos, faltantes, grupos de producción y destajos independientes',
    'author': 'ESI - Especialistas en Sistemas Integrados',
    'category': 'Manufacturing/Reporting',
    'license': 'LGPL-3',
    'depends': ['esi_calzados_v13', 'mrp_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/production_report_views.xml',
        'views/production_order_report_wizard_views.xml',
        'views/destajo_report_wizard_views.xml',
        'report/production_report_templates.xml',
        'views/production_group_report_views.xml',
    ],
    'installable': True,
    'application': False,
}
