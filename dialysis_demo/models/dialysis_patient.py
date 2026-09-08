from odoo import api, fields, models


class DialysisPatient(models.Model):
    _name = "dialysis.patient"
    _description = "Paciente de Hemodiálisis"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Nombre", compute="_compute_name", store=True, index=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(
        "res.partner",
        string="Paciente / contacto",
        required=True,
        ondelete="restrict",
        index=True,
    )
    medical_record_number = fields.Char(string="N.º historia clínica", index=True)
    dry_weight = fields.Float(string="Peso seco (kg)", digits=(16, 2))
    vascular_access = fields.Selection(
        [
            ("fistula", "Fístula AV"),
            ("catheter", "Catéter venoso central"),
        ],
        string="Acceso vascular habitual",
    )
    clinical_notes = fields.Text(string="Observaciones clínicas")
    session_ids = fields.One2many(
        "dialysis.session", "patient_id", string="Sesiones"
    )

    @api.depends("partner_id", "partner_id.name", "medical_record_number")
    def _compute_name(self):
        for record in self:
            base_name = record.partner_id.display_name or "Paciente"
            if record.medical_record_number:
                record.name = f"{base_name} [{record.medical_record_number}]"
            else:
                record.name = base_name
