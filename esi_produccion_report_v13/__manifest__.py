# -*- coding: utf-8 -*-
{
    'name': 'ESI - Informes de Producción Calzado',
    'version': '13.0.3.0.0',
    'summary': 'Ficha de costo, faltantes con costo y reporte de destajos para esi_calzados_v13',
    'author': 'ESI - Especialistas en Sistemas Integrados',
    'category': 'Manufacturing/Reporting',
    'license': 'LGPL-3',
    'depends': ['esi_calzados_v13', 'mrp_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/destajo_report_wizard_views.xml',
        'report/production_report_templates.xml',
    ],
    'installable': True,
    'application': False,
}
