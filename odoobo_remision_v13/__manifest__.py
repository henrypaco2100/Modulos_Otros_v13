# -*- coding: utf-8 -*-
{
    "name": "ESI - Reportes de Remisión",
    "version": "13.0.1.3.0",
    "category": "Inventory/Inventory",
    "summary": "Remisión, consignaciones, materiales y devoluciones",
    "description": "Seis reportes independientes para transferencias de inventario en Odoo 13 Community.",
    "author": "ESI Bolivia",
    "website": "https://esibolivia.store",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": ["views/stock_picking_views.xml", "report/report_actions.xml", "report/report_templates.xml"],
    "installable": True,
    "application": False,
    "auto_install": False,
}

