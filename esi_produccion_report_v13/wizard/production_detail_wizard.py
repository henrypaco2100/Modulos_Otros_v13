# -*- coding: utf-8 -*-
# ESI - Vista de análisis individual de una Orden de Producción.
# ESI corrección/mejora: permite VER el análisis antes de descargar PDF o Excel.

import base64
import io
from html import escape

from odoo import fields, models, _
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:  # pragma: no cover
    xlsxwriter = None


class EsiProductionDetailWizard(models.TransientModel):
    _name = 'esi.production.detail.wizard'
    _description = 'ESI - Análisis Individual de Producción'

    production_id = fields.Many2one(
        'mrp.production', string='Orden de Producción', required=True, readonly=True,
    )
    preview_html = fields.Html(
        string='Análisis de Producción', sanitize=False, readonly=True,
    )
    excel_file = fields.Binary(string='Excel', readonly=True)
    excel_filename = fields.Char(string='Archivo Excel', readonly=True)

    def _fmt_date(self, value):
        if not value:
            return ''
        try:
            return fields.Datetime.to_string(value)
        except Exception:
            return str(value)

    def _build_preview_html(self):
        self.ensure_one()
        mo = self.production_id
        if not mo:
            return '<div>No se encontró la Orden de Producción.</div>'

        d = mo._esi_report_detail_data(include_costs=True)
        company = mo.company_id
        currency = company.currency_id
        state_label = d.get('state') or ''
        store = d.get('store') or ''

        # ESI: se usan f-strings para que los porcentajes de CSS (100%) no sean
        # interpretados por el operador de formato "%" de Python.
        html = [
            '<div style="font-family:Arial,sans-serif;color:#222;background:#fff;padding:12px;">',
            '<div style="display:flex;justify-content:space-between;align-items:flex-start;">',
            f'<div><img src="/web/image/res.company/{company.id}/logo" style="max-height:70px;max-width:220px;"/></div>',
            f'<div style="text-align:right;font-size:12px;"><b>{escape(company.display_name or "")}</b><br/>{escape(company.country_id.name or "")}</div>',
            '</div>',
            '<h2 style="text-align:center;margin:18px 0 12px;color:#3f4b57;">ANÁLISIS DE PRODUCCIÓN</h2>',
            '<table style="width:100%;font-size:12px;margin-bottom:12px;">',
            f'<tr><td><b>Orden:</b> {escape(d.get("reference") or "")}</td><td><b>Producto:</b> {escape(d.get("product") or "")}</td><td><b>Estado:</b> {escape(state_label)}</td></tr>',
            f'<tr><td><b>LdM:</b> {escape(d.get("bom") or "")}</td><td><b>Responsable:</b> {escape(d.get("responsible") or "")}</td><td><b>Almacén:</b> {escape(d.get("warehouse") or "")}</td></tr>',
        ]
        if store:
            html.append(f'<tr><td><b>Sucursal:</b> {escape(store)}</td><td colspan="2"></td></tr>')
        html.append('</table>')

        html += [
            '<table style="border-collapse:collapse;width:100%;font-size:11px;margin-bottom:12px;">',
            '<thead><tr style="background:#eef3f7;font-weight:bold;">',
            '<th style="border:1px solid #89949e;padding:6px;">PLANIFICADO</th>',
            '<th style="border:1px solid #89949e;padding:6px;">PRODUCIDO</th>',
            '<th style="border:1px solid #89949e;padding:6px;">DIFERENCIA</th>',
            '<th style="border:1px solid #89949e;padding:6px;">CUMPLIMIENTO</th>',
            '<th style="border:1px solid #89949e;padding:6px;">DURACIÓN REAL</th>',
            '<th style="border:1px solid #89949e;padding:6px;">MERMAS</th>',
            '</tr></thead><tbody><tr>',
            f'<td style="border:1px solid #aab2b9;padding:6px;text-align:right;">{mo._esi_report_fmt_qty(d["planned_qty"])} {escape(d.get("uom") or "")}</td>',
            f'<td style="border:1px solid #aab2b9;padding:6px;text-align:right;">{mo._esi_report_fmt_qty(d["produced_qty"])} {escape(d.get("uom") or "")}</td>',
            f'<td style="border:1px solid #aab2b9;padding:6px;text-align:right;">{mo._esi_report_fmt_qty(d["output_variance"])}</td>',
            f'<td style="border:1px solid #aab2b9;padding:6px;text-align:right;">{mo._esi_report_fmt_pct(d["efficiency"])}%</td>',
            f'<td style="border:1px solid #aab2b9;padding:6px;text-align:right;">{mo._esi_report_fmt(d["duration_hours"], 2)} h</td>',
            f'<td style="border:1px solid #aab2b9;padding:6px;text-align:center;">{d["scrap_count"]}</td>',
            '</tr></tbody></table>',
            '<h3 style="margin:14px 0 6px;color:#3f4b57;">Consumo de Materia Prima: LdM vs Real</h3>',
            '<table style="border-collapse:collapse;width:100%;font-size:10px;">',
            '<thead><tr style="background:#e7edf3;">',
            '<th style="border:1px solid #89949e;padding:5px;text-align:left;">MATERIA PRIMA</th>',
            '<th style="border:1px solid #89949e;padding:5px;">UDM</th>',
            '<th style="border:1px solid #89949e;padding:5px;">PLANIFICADO</th>',
            '<th style="border:1px solid #89949e;padding:5px;">REAL</th>',
            '<th style="border:1px solid #89949e;padding:5px;">VARIACIÓN</th>',
            '<th style="border:1px solid #89949e;padding:5px;">VAR. %</th>',
        ]
        if d['can_costs']:
            html += [
                '<th style="border:1px solid #89949e;padding:5px;">COSTO PLAN.</th>',
                '<th style="border:1px solid #89949e;padding:5px;">COSTO REAL</th>',
                '<th style="border:1px solid #89949e;padding:5px;">VAR. COSTO</th>',
            ]
        html.append('</tr></thead><tbody>')

        if not d['material_rows']:
            colspan = 9 if d['can_costs'] else 6
            html.append(f'<tr><td colspan="{colspan}" style="border:1px solid #aab2b9;padding:14px;text-align:center;">No hay consumos de materia prima registrados.</td></tr>')
        else:
            for r in d['material_rows']:
                variance = r['variance_qty'] or 0.0
                status = 'Sobreconsumo' if variance > 0 else ('Bajo consumo' if variance < 0 else 'Según plan')
                html += [
                    '<tr>',
                    f'<td style="border:1px solid #aab2b9;padding:4px;">{escape(r.get("product") or "")}<br/><span style="font-size:9px;color:#666;">{status}</span></td>',
                    f'<td style="border:1px solid #aab2b9;padding:4px;text-align:center;">{escape(r.get("uom") or "")}</td>',
                    f'<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">{mo._esi_report_fmt_qty(r["planned_qty"])}</td>',
                    f'<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">{mo._esi_report_fmt_qty(r["actual_qty"])}</td>',
                    f'<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">{mo._esi_report_fmt_qty(r["variance_qty"])}</td>',
                    f'<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">{mo._esi_report_fmt_pct(r["variance_pct"])}%</td>',
                ]
                if d['can_costs']:
                    html += [
                        f'<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">{mo._esi_report_fmt_money(r["planned_cost"])}</td>',
                        f'<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">{mo._esi_report_fmt_money(r["actual_cost"])}</td>',
                        f'<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">{mo._esi_report_fmt_money(r["cost_variance"])}</td>',
                    ]
                html.append('</tr>')
        html.append('</tbody></table>')
        html.append(
            f'<div style="font-size:11px;margin:7px 0 12px;">'
            f'<b>Materiales con sobreconsumo:</b> {d["over_material_count"]} &nbsp;&nbsp; '
            f'<b>Materiales por debajo de lo planificado:</b> {d["under_material_count"]}</div>'
        )

        if mo.workorder_ids:
            html += [
                '<h3 style="margin:14px 0 6px;color:#3f4b57;">Operaciones / Centros de Trabajo</h3>',
                '<table style="border-collapse:collapse;width:100%;font-size:10px;">',
                '<thead><tr style="background:#e7edf3;">',
                '<th style="border:1px solid #89949e;padding:5px;">OPERACIÓN</th>',
                '<th style="border:1px solid #89949e;padding:5px;">CENTRO DE TRABAJO</th>',
                '<th style="border:1px solid #89949e;padding:5px;">DURACIÓN (MIN)</th>',
            ]
            if d['can_costs']:
                html.append('<th style="border:1px solid #89949e;padding:5px;">COSTO/HORA</th>')
            html.append('</tr></thead><tbody>')
            for wo in mo.workorder_ids:
                html += [
                    '<tr>',
                    f'<td style="border:1px solid #aab2b9;padding:4px;">{escape(wo.name or "")}</td>',
                    f'<td style="border:1px solid #aab2b9;padding:4px;">{escape(wo.workcenter_id.display_name or "")}</td>',
                    f'<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">{mo._esi_report_fmt(getattr(wo, "duration", 0.0), 2)}</td>',
                ]
                if d['can_costs']:
                    html.append(f'<td style="border:1px solid #aab2b9;padding:4px;text-align:right;">{mo._esi_report_fmt_money(getattr(wo.workcenter_id, "costs_hour", 0.0))}</td>')
                html.append('</tr>')
            html.append('</tbody></table>')

        if d['can_costs']:
            html += [
                '<h3 style="margin:14px 0 6px;color:#3f4b57;">Costo y Margen Potencial</h3>',
                '<table style="border-collapse:collapse;width:100%;font-size:10px;">',
                '<thead><tr style="background:#eef3f7;">',
                '<th style="border:1px solid #89949e;padding:5px;">COSTO MATERIALES</th>',
                '<th style="border:1px solid #89949e;padding:5px;">COSTO OPERACIONES</th>',
                '<th style="border:1px solid #89949e;padding:5px;">COSTO TOTAL</th>',
                '<th style="border:1px solid #89949e;padding:5px;">COSTO/UD</th>',
                '<th style="border:1px solid #89949e;padding:5px;">PVP LISTA</th>',
                '<th style="border:1px solid #89949e;padding:5px;">VALOR POTENCIAL</th>',
                '<th style="border:1px solid #89949e;padding:5px;">MARGEN POTENCIAL</th>',
                '<th style="border:1px solid #89949e;padding:5px;">MARGEN %</th>',
                '</tr></thead><tbody><tr>',
                f'<td style="border:1px solid #aab2b9;padding:5px;text-align:right;">{mo._esi_report_fmt_money(d["material_actual_cost"])}</td>',
                f'<td style="border:1px solid #aab2b9;padding:5px;text-align:right;">{mo._esi_report_fmt_money(d["operation_cost"])}</td>',
                f'<td style="border:1px solid #aab2b9;padding:5px;text-align:right;">{mo._esi_report_fmt_money(d["total_cost"])}</td>',
                f'<td style="border:1px solid #aab2b9;padding:5px;text-align:right;">{mo._esi_report_fmt_money(d["unit_cost"])}</td>',
                f'<td style="border:1px solid #aab2b9;padding:5px;text-align:right;">{mo._esi_report_fmt_money(d["sale_price"])}</td>',
                f'<td style="border:1px solid #aab2b9;padding:5px;text-align:right;">{mo._esi_report_fmt_money(d["potential_revenue"])}</td>',
                f'<td style="border:1px solid #aab2b9;padding:5px;text-align:right;">{mo._esi_report_fmt_money(d["potential_margin"])}</td>',
                f'<td style="border:1px solid #aab2b9;padding:5px;text-align:right;">{mo._esi_report_fmt_pct(d["margin_pct"])}%</td>',
                '</tr></tbody></table>',
                f'<p style="font-size:9px;color:#666;margin-top:6px;">Moneda: {escape(currency.name or "")}. El margen es potencial: utiliza PVP de lista y no confirma que esta producción haya sido vendida.</p>',
            ]

        html.append('</div>')
        return ''.join(html)

    def action_refresh_preview(self):
        self.ensure_one()
        self.preview_html = self._build_preview_html()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Análisis de Producción'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('esi_produccion_report_v13.view_esi_production_detail_wizard_form').id,
            'target': 'current',
        }

    def action_print_pdf(self):
        self.ensure_one()
        if not self.production_id:
            raise UserError(_('No se encontró la Orden de Producción.'))
        return self.env.ref('esi_produccion_report_v13.action_report_esi_production_detail').report_action(self.production_id)

    def action_export_excel(self):
        self.ensure_one()
        if xlsxwriter is None:
            raise UserError(_('No está instalada la librería Python xlsxwriter en el servidor.'))
        mo = self.production_id
        if not mo:
            raise UserError(_('No se encontró la Orden de Producción.'))

        d = mo._esi_report_detail_data(include_costs=True)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        fmt_title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
        fmt_label = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#EEF3F7'})
        fmt_header = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#DDE7F0', 'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        fmt_text = workbook.add_format({'border': 1})
        fmt_center = workbook.add_format({'border': 1, 'align': 'center'})
        fmt_qty = workbook.add_format({'border': 1, 'num_format': '#,##0.' + ('0' * mo._esi_report_qty_digits())})
        fmt_money = workbook.add_format({'border': 1, 'num_format': '#,##0.' + ('0' * mo._esi_report_money_digits())})
        fmt_pct = workbook.add_format({'border': 1, 'num_format': '0.00%'})
        fmt_note = workbook.add_format({'italic': True, 'font_size': 9, 'font_color': '#666666', 'text_wrap': True})

        # Hoja 1: Resumen de la OF
        sh = workbook.add_worksheet('Resumen')
        sh.hide_gridlines(2)
        sh.merge_range(0, 0, 0, 3, 'ANÁLISIS DE PRODUCCIÓN - %s' % (mo.name or ''), fmt_title)
        summary = [
            ('Orden', d['reference']),
            ('Producto', d['product']),
            ('Estado', d['state']),
            ('Lista de Materiales', d['bom']),
            ('Responsable', d['responsible']),
            ('Almacén', d['warehouse']),
            ('Sucursal', d['store']),
            ('Planificado', d['planned_qty']),
            ('Producido', d['produced_qty']),
            ('Diferencia', d['output_variance']),
            ('Cumplimiento %', d['efficiency'] / 100.0),
            ('Duración real (h)', d['duration_hours']),
            ('Mermas', d['scrap_count']),
            ('Materiales con sobreconsumo', d['over_material_count']),
            ('Materiales bajo plan', d['under_material_count']),
        ]
        if d['can_costs']:
            summary += [
                ('Costo materiales', d['material_actual_cost']),
                ('Costo operaciones', d['operation_cost']),
                ('Costo total', d['total_cost']),
                ('Costo por unidad', d['unit_cost']),
                ('PVP lista', d['sale_price']),
                ('Valor potencial', d['potential_revenue']),
                ('Margen potencial', d['potential_margin']),
                ('Margen %', d['margin_pct'] / 100.0),
            ]
        row = 2
        for label, value in summary:
            sh.write(row, 0, label, fmt_label)
            if label in ('Planificado', 'Producido', 'Diferencia'):
                sh.write_number(row, 1, value or 0.0, fmt_qty)
            elif label in ('Cumplimiento %', 'Margen %'):
                sh.write_number(row, 1, value or 0.0, fmt_pct)
            elif label.startswith('Costo') or label in ('PVP lista', 'Valor potencial', 'Margen potencial'):
                sh.write_number(row, 1, value or 0.0, fmt_money)
            elif isinstance(value, (int, float)):
                sh.write_number(row, 1, value or 0.0)
            else:
                sh.write(row, 1, value or '')
            row += 1
        sh.set_column(0, 0, 28)
        sh.set_column(1, 1, 42)

        # Hoja 2: Materia prima
        sm = workbook.add_worksheet('Materia Prima')
        sm.hide_gridlines(2)
        headers = ['Materia Prima', 'UDM', 'Planificado', 'Real', 'Variación', 'Var. %', 'Estado']
        if d['can_costs']:
            headers += ['Costo Plan.', 'Costo Real', 'Var. Costo']
        for col, title in enumerate(headers):
            sm.write(0, col, title, fmt_header)
        for ridx, r in enumerate(d['material_rows'], 1):
            variance = r['variance_qty'] or 0.0
            status = 'Sobreconsumo' if variance > 0 else ('Bajo consumo' if variance < 0 else 'Según plan')
            sm.write(ridx, 0, r['product'] or '', fmt_text)
            sm.write(ridx, 1, r['uom'] or '', fmt_center)
            sm.write_number(ridx, 2, r['planned_qty'] or 0.0, fmt_qty)
            sm.write_number(ridx, 3, r['actual_qty'] or 0.0, fmt_qty)
            sm.write_number(ridx, 4, r['variance_qty'] or 0.0, fmt_qty)
            sm.write_number(ridx, 5, (r['variance_pct'] or 0.0) / 100.0, fmt_pct)
            sm.write(ridx, 6, status, fmt_text)
            if d['can_costs']:
                sm.write_number(ridx, 7, r['planned_cost'] or 0.0, fmt_money)
                sm.write_number(ridx, 8, r['actual_cost'] or 0.0, fmt_money)
                sm.write_number(ridx, 9, r['cost_variance'] or 0.0, fmt_money)
        sm.set_column(0, 0, 42)
        sm.set_column(1, 1, 12)
        sm.set_column(2, len(headers) - 1, 16)

        # Hoja 3: Operaciones, si existen
        if mo.workorder_ids:
            so = workbook.add_worksheet('Operaciones')
            so.hide_gridlines(2)
            op_headers = ['Operación', 'Centro de Trabajo', 'Duración (min)']
            if d['can_costs']:
                op_headers += ['Costo/Hora', 'Costo Operación']
            for col, title in enumerate(op_headers):
                so.write(0, col, title, fmt_header)
            for ridx, wo in enumerate(mo.workorder_ids, 1):
                duration = getattr(wo, 'duration', 0.0) or 0.0
                cost_hour = getattr(wo.workcenter_id, 'costs_hour', 0.0) or 0.0
                so.write(ridx, 0, wo.name or '', fmt_text)
                so.write(ridx, 1, wo.workcenter_id.display_name or '', fmt_text)
                so.write_number(ridx, 2, duration, fmt_qty)
                if d['can_costs']:
                    so.write_number(ridx, 3, cost_hour, fmt_money)
                    so.write_number(ridx, 4, (duration / 60.0) * cost_hour, fmt_money)
            so.set_column(0, 1, 34)
            so.set_column(2, len(op_headers) - 1, 16)

        if d['can_costs']:
            sh.merge_range(row + 1, 0, row + 2, 3,
                           'Margen potencial: usa el PVP de lista actual y no confirma que la producción haya sido vendida.',
                           fmt_note)

        workbook.close()
        output.seek(0)
        filename = 'Analisis_Produccion_%s.xlsx' % ((mo.name or 'OF').replace('/', '_'))
        self.write({
            'excel_file': base64.b64encode(output.read()),
            'excel_filename': filename,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model=%s&id=%s&field=excel_file&filename_field=excel_filename&download=true' % (self._name, self.id),
            'target': 'self',
        }

    def action_back_to_production(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.production_id.name or _('Orden de Producción'),
            'res_model': 'mrp.production',
            'res_id': self.production_id.id,
            'view_mode': 'form',
            'view_id': self.env.ref('mrp.mrp_production_form_view').id,
            'target': 'current',
        }
