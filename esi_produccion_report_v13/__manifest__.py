# -*- coding: utf-8 -*-
{
    'name': 'ESI - Informes de Producción Calzado',
    'version': '13.0.4.0.1',
    'summary': 'Informes generales de producción + ficha de costo, faltantes y destajos para esi_calzados_v13',
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
    ],
    'installable': True,
    'application': False,
}
