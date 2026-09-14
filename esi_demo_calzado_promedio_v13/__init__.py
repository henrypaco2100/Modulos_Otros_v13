# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
from . import models
from . import wizard


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['esi.demo.calzado.promedio.loader'].sudo().run_demo()
