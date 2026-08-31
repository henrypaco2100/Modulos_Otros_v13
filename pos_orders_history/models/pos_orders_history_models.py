# Copyright 2017-2018 Dinar Gabbasov <https://it-projects.info/team/GabbasovDinar>
# Copyright 2018 Artem Losev
# License MIT (https://opensource.org/licenses/MIT).

import re

from odoo import api, fields, models

CHANNEL = "pos_orders_history"


class PosConfig(models.Model):
    _inherit = "pos.config"

    orders_history = fields.Boolean(
        "Orders History", help="Show all orders list in POS", default=True
    )
    load_barcode_order_only = fields.Boolean(
        "Load Specific Orders only",
        help="Load an order after scan the barcode only rather than all existing orders",
        default=False,
    )

    load_orders_of_last_n_days = fields.Boolean(
        "Orders of last 'n' days", default=False
    )
    number_of_days = fields.Integer(
        "Number of days", default=0, help="0 - load orders of current day"
    )

    show_cancelled_orders = fields.Boolean("Show Cancelled Orders", default=True)
    show_posted_orders = fields.Boolean("Show Posted Orders", default=False)
    show_barcode_in_receipt = fields.Boolean("Show Barcode in Receipt", default=True)

    # ir.actions.server methods:
    @api.model
    def notify_orders_updates(self):
        """Notify only the POS configuration that owns each updated order.

        The original module sent every order update to every POS configuration
        (`self.search([])`), so with two or more shops each POS could receive
        history updates that belonged to another shop.
        """
        ids = self.env.context.get("active_ids", [])
        if not ids:
            return

        orders = self.env["pos.order"].browse(ids).exists()
        orders_by_config = {}
        for order in orders:
            if not order.config_id:
                continue
            orders_by_config.setdefault(order.config_id.id, []).append(order.id)

        for config_id, order_ids in orders_by_config.items():
            message = {"updated_orders": order_ids}
            self.browse(config_id)._send_to_channel(CHANNEL, message)


class PosOrder(models.Model):
    _inherit = "pos.order"

    pos_name = fields.Char(related="config_id.name", string="Point of Sale Name")
    pos_history_reference_uid = fields.Char(
        compute="_compute_pos_history_reference_uid", readonly=True, store=True
    )

    @api.depends("pos_reference")
    def _compute_pos_history_reference_uid(self):
        for r in self:
            reference = r.pos_reference and re.search(
                r"\d{1,}-\d{1,}-\d{1,}", r.pos_reference
            )
            r.pos_history_reference_uid = reference and reference.group(0) or ""
