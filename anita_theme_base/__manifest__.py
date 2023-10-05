# -*- coding: utf-8 -*-
{
    'name': "anita_theme_base",

    'summary': """
        Base for anita odoo themes
    """,

    'description': """
        Odoo Login, 
        Odoo login page, 
        Odoo login theme
        Login, 
        Anita Theme Base,
        Anita Theme,
        Awesome Theme,
        Multi tab theme,
        Pop form theme
    """,

    'author': "Funenc Crax",

    'website': "https://odoo.funenc.com",
    'live_test_url': 'https://odoo.funenc.com',

    'license': 'OPL-1',
    'images': ['static/description/screen_shot.png', 'static/description/banner.png'],
    'support': 'supports@funenc.com',
    'live_chat': 'supports@funenc.com',
    'maintainer': 'Funenc Odoo Team',
    'category': 'Theme/Backend',
    'version': '13.0.0.6',

    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 0.00,

    'depends': ['base', 'web'],
    
    'data': [
        "views/anita_web.xml",
        "views/assets.xml",
    ]
}
