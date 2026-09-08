# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    esi_product_field_1_label = fields.Char(string="Nombre del campo 1", config_parameter="odoobo_producto.field_1_label", default="Campo adicional 1", groups="base.group_system")
    esi_product_field_2_label = fields.Char(string="Nombre del campo 2", config_parameter="odoobo_producto.field_2_label", default="Campo adicional 2", groups="base.group_system")
    esi_product_field_3_label = fields.Char(string="Nombre del campo 3", config_parameter="odoobo_producto.field_3_label", default="Campo adicional 3", groups="base.group_system")
    esi_product_field_4_label = fields.Char(string="Nombre del campo 4", config_parameter="odoobo_producto.field_4_label", default="Campo adicional 4", groups="base.group_system")
    esi_product_field_5_label = fields.Char(string="Nombre del campo 5", config_parameter="odoobo_producto.field_5_label", default="Campo adicional 5", groups="base.group_system")

    def set_values(self):
        result = super(ResConfigSettings, self).set_values()
        views = self.env["ir.ui.view"]
        if hasattr(views, "clear_caches"):
            views.clear_caches()
        return result
