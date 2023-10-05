# Copyright 2019 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    show_qtys = fields.Boolean(
        "Show Product Qtys", help="Show Product Qtys in POS", default=True
    )
    default_location_src_id = fields.Many2one(
        "stock.location", related="picking_type_id.default_location_src_id"
    )

    # def actualizar_cantidad_productos(self, location_id):
    #     location_interno = self.env['stock.location'].sudo().browse(location_id)
    #     if location_interno.usage == 'internal':
    #         query = """
    #             UPDATE product_product
    #             SET sd_qty_available = (
    #                 SELECT COALESCE(SUM(quantity), 0.0)
    #                 FROM stock_quant
    #                 WHERE product_id = product_product.id AND location_id = %s
    #             )
    #             WHERE type = 'product'
    #         """
    #         self.env.cr.execute(query, (location_id,))
    # def actualizar_cantidad_productos(self, location_id):
    #     location_interno = self.env['stock.location'].sudo().browse(location_id)
    #     if location_interno.usage == 'internal':
    #         query = """
    #             UPDATE product_product
    #             SET sd_qty_available = (
    #                 SELECT COALESCE(SUM(quantity), 0.0)
    #                 FROM stock_quant
    #                 WHERE product_id = product_product.id AND location_id = %s
    #             )
    #             WHERE product_product.type = 'product'
    #         """
    #         self.env.cr.execute(query, (location_id,))
    def actualizar_cantidad_productos(self, location_id):
        # print('location_id',location_id)
        location_interno = self.env['stock.location'].sudo().browse(location_id)
        if location_interno.usage == 'internal':
            query = """
                UPDATE product_product AS p
                SET sd_qty_available = (
                    SELECT COALESCE(SUM(quantity), 0.0)
                    FROM stock_quant
                    WHERE product_id = p.id AND location_id = %s
                )
            """
            # print('entro stock disponible')
            self.env.cr.execute(query, (location_id,))
        self.sudo().limpiar_cache()
    
    def limpiar_cache(self,):
        # print(' user_id',self.env.user)
        config_ids = self.env['pos.config'].search([])
        # print('config_ids',config_ids)
        for config_id in config_ids.filtered(lambda x:x.current_user_id.id ==self.env.user.id ):
            # print('config_id name',config_id.name,config_id.current_user_id)
            config_id.delete_cache()

    # def actualizar_cantidad_productos(self, location_id):
    #     location_interno = self.env['stock.location'].sudo().browse(location_id)
    #     if location_interno.usage == 'internal':
    #         query = """
    #             UPDATE product_product
    #             SET sd_qty_available = sub.total_quantity
    #             FROM (
    #                 SELECT p.id AS product_id, COALESCE(SUM(sq.quantity), 0.0) AS total_quantity
    #                 FROM product_product AS p
    #                 LEFT JOIN stock_quant sq ON p.id = sq.product_id AND %s = sq.location_id
    #                 GROUP BY p.id
    #             ) AS sub
    #             WHERE product_product.id = sub.product_id
    #         """
    #         self.env.cr.execute(query, (location_id,))


    # def actualizar_cantidad_productos(self, location_id):
    #     location_interno = self.env['stock.location'].sudo().browse(location_id)
    #     if location_interno.usage == 'internal':
    #         producto_ids = self.env['product.product'].sudo().search([('type', '=', 'product')])
    #         print('entro actualizar prod desde js')
    #         for product_id in producto_ids:
    #             stock = self.env['stock.quant'].read_group(
    #                 [('product_id', '=', product_id.id), ('location_id', '=', location_id)],
    #                 ['quantity:sum'],
    #                 []
    #             )[0].get('quantity', 0.0)
    #             product_id.sudo().write({
    #                 'sd_qty_available': stock
    #             })
    #