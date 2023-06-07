# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import ValidationError

class ERPPOS(models.Model):
    _inherit = 'pos.config'

    can_join_pos = fields.Boolean(compute="_compute_can_join_pos")

    def _compute_can_join_pos(self):
        for rec in self:
            rec.can_join_pos = rec._validate_pos_join()

    def btn_join(self):
        if not self._validate_pos_join():
            raise ValidationError("You are not allowed to join this POS.")
        return self.open_ui()

    def _validate_pos_join(self):
        open_sessions = self.session_ids.filtered(lambda s: s.state != 'closed')
        return bool(open_sessions and not self.current_session_id and self.env['hr.employee'].search([('user_id', '=', self.env.uid), ('id', 'in', self.employee_ids.ids)], limit=1))