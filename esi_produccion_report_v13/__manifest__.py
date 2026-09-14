# -*- coding: utf-8 -*-
{
    'name': 'ESI - Informes de Producción',
    'version': '13.0.1.1.0',
    'summary': 'Resumen, consumo LdM vs real, costos y margen potencial de producción',
    'author': 'ESI - Especialistas en Sistemas Integrados',
    'category': 'Manufacturing/Reporting',
    'license': 'LGPL-3',
    'depends': ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/production_report_views.xml',
        'report/production_report_templates.xml',
    ],
    'installable': True,
    'application': False,
}
