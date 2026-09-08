from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DialysisSession(models.Model):
    _name = "dialysis.session"
    _description = "Sesión de Hemodiálisis"
    _order = "session_date desc, id desc"

    name = fields.Char(
        string="Sesión",
        required=True,
        copy=False,
        readonly=True,
        default="Nuevo",
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Borrador"),
            ("in_progress", "En diálisis"),
            ("done", "Completada"),
            ("cancelled", "Cancelada"),
        ],
        string="Estado",
        default="draft",
        required=True,
        index=True,
    )
    patient_id = fields.Many2one(
        "dialysis.patient",
        string="Paciente",
        required=True,
        ondelete="restrict",
        index=True,
    )
    session_date = fields.Datetime(
        string="Fecha y hora de inicio",
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    nurse_id = fields.Many2one(
        "res.users",
        string="Responsable",
        required=True,
        default=lambda self: self.env.user,
    )
    shift = fields.Selection(
        [("1", "Turno 1"), ("2", "Turno 2"), ("3", "Turno 3")],
        string="Turno",
    )
    chair = fields.Selection(
        [(str(i), f"Sillón {i}") for i in range(1, 11)],
        string="Sillón",
    )

    # PRE-DIÁLISIS
    initial_weight = fields.Float(string="Peso inicial (kg)", digits=(16, 2))
    dry_weight = fields.Float(string="Peso seco (kg)", digits=(16, 2))
    interdialytic_gain = fields.Float(
        string="Ganancia interdialítica (kg)",
        compute="_compute_interdialytic_gain",
        store=True,
        digits=(16, 2),
    )
    pre_bp_systolic = fields.Integer(string="PA sistólica entrada")
    pre_bp_diastolic = fields.Integer(string="PA diastólica entrada")
    pre_heart_rate = fields.Integer(string="FC entrada (bpm)")
    vascular_access = fields.Selection(
        [
            ("fistula", "Fístula AV"),
            ("catheter", "Catéter venoso central"),
        ],
        string="Acceso vascular",
    )
    fremitus_present = fields.Boolean(string="Frémito presente")
    no_infection_signs = fields.Boolean(string="Sin signos de infección")
    programmed_minutes = fields.Integer(
        string="Tiempo programado (min)", default=240, required=True
    )
    monitoring_interval = fields.Selection(
        [("30", "Cada 30 min"), ("60", "Cada 60 min")],
        string="Intervalo de monitoreo",
        default="30",
        required=True,
    )
    dialyzer = fields.Char(string="Dializador asignado")
    initial_heparin = fields.Float(string="Heparina inicial (UI)")
    uf_target = fields.Float(string="Meta UF (L)", digits=(16, 2))

    # INTRA-DIÁLISIS
    monitoring_line_ids = fields.One2many(
        "dialysis.monitoring.line", "session_id", string="Matriz de monitoreo"
    )

    # POST-DIÁLISIS
    final_weight = fields.Float(string="Peso final (kg)", digits=(16, 2))
    post_bp_systolic = fields.Integer(string="PA sistólica salida")
    post_bp_diastolic = fields.Integer(string="PA diastólica salida")
    post_heart_rate = fields.Integer(string="FC salida (bpm)")
    uf_total = fields.Float(string="UF total lograda (L)", digits=(16, 2))

    epo_2000 = fields.Boolean(string="Eritropoyetina 2000 UI")
    epo_4000 = fields.Boolean(string="Eritropoyetina 4000 UI")
    iron_sucrose = fields.Boolean(string="Hierro sacarato")
    vitamin_d3 = fields.Boolean(string="Vitamina D3")

    supply_line_ids = fields.One2many(
        "dialysis.supply.line", "session_id", string="Checklist de insumos"
    )
    closing_notes = fields.Text(string="Observaciones de cierre")

    @api.depends("initial_weight", "dry_weight")
    def _compute_interdialytic_gain(self):
        for record in self:
            if record.initial_weight and record.dry_weight:
                record.interdialytic_gain = record.initial_weight - record.dry_weight
            else:
                record.interdialytic_gain = 0.0

    @api.onchange("patient_id")
    def _onchange_patient_id(self):
        if self.patient_id:
            self.dry_weight = self.patient_id.dry_weight
            self.vascular_access = self.patient_id.vascular_access

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "Nuevo") == "Nuevo":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "dialysis.session"
                ) or "Nuevo"
            patient_id = vals.get("patient_id")
            if patient_id:
                patient = self.env["dialysis.patient"].browse(patient_id)
                if "dry_weight" not in vals:
                    vals["dry_weight"] = patient.dry_weight
                if "vascular_access" not in vals:
                    vals["vascular_access"] = patient.vascular_access
        return super().create(vals_list)

    def action_generate_monitoring_lines(self):
        for record in self:
            if record.monitoring_line_ids:
                continue
            interval = int(record.monitoring_interval or "30")
            duration = max(record.programmed_minutes or 240, interval)
            base_dt = record.session_date or fields.Datetime.now()
            vals_list = []
            for minute in range(0, duration + 1, interval):
                vals_list.append(
                    {
                        "session_id": record.id,
                        "minute": minute,
                        "control_datetime": base_dt + timedelta(minutes=minute),
                    }
                )
            self.env["dialysis.monitoring.line"].create(vals_list)
        return True

    def action_prepare_supplies(self):
        for record in self:
            if record.supply_line_ids:
                continue
            supplies = [
                ("Dializador Vego HF18", 1.0),
                ("Set líneas de sangre", 1.0),
            ]
            if record.vascular_access == "catheter":
                supplies.append(("Kit catéter", 1.0))
            else:
                supplies.append(("Agujas fístula", 2.0))
            self.env["dialysis.supply.line"].create(
                [
                    {
                        "session_id": record.id,
                        "description": description,
                        "quantity": qty,
                    }
                    for description, qty in supplies
                ]
            )
        return True

    def action_start(self):
        for record in self:
            if record.state != "draft":
                continue
            if not record.patient_id:
                raise UserError(_("Debe seleccionar un paciente."))
            record.action_generate_monitoring_lines()
            record.action_prepare_supplies()
            record.state = "in_progress"
        return True

    def action_complete(self):
        for record in self:
            if record.state != "in_progress":
                raise UserError(_("Solo puede completar una sesión en diálisis."))
            missing = []
            if not record.monitoring_line_ids:
                missing.append("matriz de monitoreo")
            if not record.final_weight:
                missing.append("peso final")
            if not record.post_bp_systolic or not record.post_bp_diastolic:
                missing.append("presión arterial final")
            if not record.post_heart_rate:
                missing.append("frecuencia cardíaca final")
            if not record.supply_line_ids:
                missing.append("checklist de insumos")
            elif any(not line.used for line in record.supply_line_ids):
                missing.append("confirmación de todos los insumos")
            if missing:
                raise UserError(
                    _("No se puede completar la sesión. Falta: %s")
                    % ", ".join(missing)
                )
            record.state = "done"
        return True

    def action_cancel(self):
        self.filtered(lambda r: r.state != "done").write({"state": "cancelled"})
        return True

    def action_reset_draft(self):
        self.write({"state": "draft"})
        return True


class DialysisMonitoringLine(models.Model):
    _name = "dialysis.monitoring.line"
    _description = "Monitoreo Intra-diálisis"
    _order = "minute, id"

    session_id = fields.Many2one(
        "dialysis.session",
        string="Sesión",
        required=True,
        ondelete="cascade",
        index=True,
    )
    minute = fields.Integer(string="Minuto")
    control_datetime = fields.Datetime(string="Hora de control")
    bp_systolic = fields.Integer(string="PA sist.")
    bp_diastolic = fields.Integer(string="PA diast.")
    heart_rate = fields.Integer(string="FC")
    qb = fields.Float(string="Qb (mL/min)")
    qd = fields.Float(string="Qd (mL/min)")
    venous_pressure = fields.Float(string="P. venosa (mmHg)")
    arterial_pressure = fields.Float(string="P. arterial (mmHg)")
    tmp = fields.Float(string="TMP (mmHg)")
    uf_accumulated = fields.Float(string="UF acum. (L)", digits=(16, 2))
    incident = fields.Selection(
        [
            ("none", "Sin novedades"),
            ("hypotension", "Hipotensión"),
            ("cramps", "Calambres"),
            ("clotting", "Coagulación del circuito"),
            ("other", "Otro"),
        ],
        string="Incidencia",
        default="none",
    )
    notes = fields.Char(string="Nota breve")


class DialysisSupplyLine(models.Model):
    _name = "dialysis.supply.line"
    _description = "Insumo de Sesión de Hemodiálisis"
    _order = "id"

    session_id = fields.Many2one(
        "dialysis.session",
        string="Sesión",
        required=True,
        ondelete="cascade",
        index=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Producto Odoo",
        help="Opcional. Permite mapear el insumo con Inventario en una fase posterior.",
    )
    description = fields.Char(string="Insumo", required=True)
    quantity = fields.Float(string="Cantidad", default=1.0, required=True)
    used = fields.Boolean(string="Usado / confirmado")
