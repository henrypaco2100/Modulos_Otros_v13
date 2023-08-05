from odoo import api, fields, models,_

class InheritProductProductStockUbicacion(models.Model):
    _inherit = "product.product"

    sd_qty_available = fields.Float(string='Cantidad_por_ubicacion')
    # type = fields.Selection([('consu', 'Consumible'),('service', 'Servicio'),('product', 'Almacenable')], store=True)


class InheritProductTemplaStockUbicacion(models.Model):
    _inherit = "product.template"

    sd_qty_available = fields.Float(string='Cantidad_por_ubicacion')