# -*- coding: utf-8 -*-
{
    "name": "ESI - Comprobante Contable",
    "version": "13.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Comprobante contable dinámico con vista previa y PDF",
    "description": "Comprobante contable independiente para Odoo 13 Community.",
    "author": "ESI Bolivia",
    "website": "https://esibolivia.store",
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "views/account_move_views.xml",
        "report/comprobante_report.xml",
        "report/comprobante_template.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}

