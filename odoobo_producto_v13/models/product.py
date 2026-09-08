# -*- coding: utf-8 -*-
from odoo import fields, models


LABEL_KEYS = {
    "esi_extra_field_1": ("odoobo_producto.field_1_label", "Campo adicional 1"),
    "esi_extra_field_2": ("odoobo_producto.field_2_label", "Campo adicional 2"),
    "esi_extra_field_3": ("odoobo_producto.field_3_label", "Campo adicional 3"),
    "esi_extra_field_4": ("odoobo_producto.field_4_label", "Campo adicional 4"),
    "esi_extra_field_5": ("odoobo_producto.field_5_label", "Campo adicional 5"),
}


class ProductLabelMixin(models.AbstractModel):
    _name = "odoobo.product.label.mixin"
    _description = "Etiquetas dinámicas ESI para productos"

    def fields_get(self, allfields=None, attributes=None):
        result = super(ProductLabelMixin, self).fields_get(allfields=allfields, attributes=attributes)
        parameters = self.env["ir.config_parameter"].sudo()
        for field_name, (key, default) in LABEL_KEYS.items():
            if field_name in result:
                result[field_name]["string"] = parameters.get_param(key, default) or default
        return result


class ProductTemplate(models.Model):
    _name = "product.template"
    _inherit = ["product.template", "odoobo.product.label.mixin"]

    esi_extra_field_1 = fields.Char(string="Campo adicional 1")
    esi_extra_field_2 = fields.Char(string="Campo adicional 2")
    esi_extra_field_3 = fields.Char(string="Campo adicional 3")
    esi_extra_field_4 = fields.Char(string="Campo adicional 4")
    esi_extra_field_5 = fields.Char(string="Campo adicional 5")


class ProductProduct(models.Model):
    _name = "product.product"
    _inherit = ["product.product", "odoobo.product.label.mixin"]

    esi_extra_field_1 = fields.Char(related="product_tmpl_id.esi_extra_field_1", readonly=False, store=True)
    esi_extra_field_2 = fields.Char(related="product_tmpl_id.esi_extra_field_2", readonly=False, store=True)
    esi_extra_field_3 = fields.Char(related="product_tmpl_id.esi_extra_field_3", readonly=False, store=True)
    esi_extra_field_4 = fields.Char(related="product_tmpl_id.esi_extra_field_4", readonly=False, store=True)
    esi_extra_field_5 = fields.Char(related="product_tmpl_id.esi_extra_field_5", readonly=False, store=True)
