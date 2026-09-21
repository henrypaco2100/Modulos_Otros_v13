# -*- coding: utf-8 -*-
from collections import OrderedDict
from odoo import api, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def esi_report_material_rows(self):
        """Filas de materiales para reportes.

        El costo estimado usa el costo capturado por esi_calzados_v13.
        Si la OF ya generó capas de valoración, el costo real usa esas capas.
        De esta forma el reporte no queda en cero cuando existe valoración automática.
        """
        self.ensure_one()
        rows = []
        for move in self.move_raw_ids.filtered(lambda m: m.state != 'cancel'):
            planned_qty = move.product_uom_qty or 0.0
            actual_qty = move.quantity_done or 0.0
            unit_cost = move.esi_unit_cost or 0.0
            planned_cost = move.esi_total_material_cost or (planned_qty * unit_cost)
            svl_value = abs(sum(move.sudo().stock_valuation_layer_ids.mapped('value'))) if move.stock_valuation_layer_ids else 0.0
            actual_cost = svl_value if svl_value else actual_qty * unit_cost
            actual_unit_cost = actual_cost / actual_qty if actual_qty else unit_cost
            rows.append({
                'move_id': move.id,
                'group': dict(move._fields['esi_material_group'].selection).get(move.esi_material_group, '') if move.esi_material_group else '',
                'product': move.product_id.display_name,
                'uom': move.product_uom.name or '',
                'qty_per_unit': move.esi_qty_per_unit or 0.0,
                'planned_qty': planned_qty,
                'actual_qty': actual_qty,
                'unit_cost': unit_cost,
                'actual_unit_cost': actual_unit_cost,
                'unit_material_cost': move.esi_unit_material_cost or 0.0,
                'planned_cost': planned_cost,
                'actual_cost': actual_cost,
                'available_qty': move.esi_available_qty or 0.0,
                'missing_qty': move.esi_missing_qty or 0.0,
                'purchase_unit_cost': move.esi_purchase_unit_cost or unit_cost,
                'missing_cost': move.esi_missing_cost or 0.0,
                'supplier': move.esi_get_supplier_name(),
            })
        return rows

    def esi_report_shortage_rows(self):
        self.ensure_one()
        return [row for row in self.esi_report_material_rows() if row['missing_qty'] > 0.000001]

    def esi_report_destajo_rows(self):
        self.ensure_one()
        rows = []
        for line in self.esi_destajo_ids.sorted(key=lambda d: (d.date or '', d.id)):
            rows.append({
                'date': line.date,
                'worker': line.partner_id.display_name or '',
                'activity': line.activity_id.display_name or '',
                'description': line.description or '',
                'quantity': line.quantity or 0.0,
                'uom': line.uom_id.name or '',
                'unit_price': line.unit_price or 0.0,
                'amount': line.amount or 0.0,
                'state': dict(line._fields['state'].selection).get(line.state, line.state or ''),
            })
        return rows

    def esi_report_destajo_summary(self):
        self.ensure_one()
        grouped = OrderedDict()
        for line in self.esi_destajo_ids:
            key = line.partner_id.id or 0
            if key not in grouped:
                grouped[key] = {
                    'worker': line.partner_id.display_name or 'Sin operador',
                    'records': 0,
                    'quantity': 0.0,
                    'amount': 0.0,
                }
            grouped[key]['records'] += 1
            grouped[key]['quantity'] += line.quantity or 0.0
            grouped[key]['amount'] += line.amount or 0.0
        return list(grouped.values())

    def esi_report_cost_summary(self):
        self.ensure_one()
        material_rows = self.esi_report_material_rows()
        material_estimated = sum(row['planned_cost'] for row in material_rows)
        material_actual = sum(row['actual_cost'] for row in material_rows)
        destajo_all = sum(self.esi_destajo_ids.mapped('amount'))
        destajo_confirmed = sum(self.esi_destajo_ids.filtered(lambda d: d.state in ('confirmed', 'paid')).mapped('amount'))
        estimated_total = material_estimated + destajo_all + (self.esi_other_cost or 0.0)
        confirmed_total = material_actual + destajo_confirmed + (self.esi_other_cost or 0.0)

        finished_moves = self.move_finished_ids.filtered(
            lambda m: m.product_id == self.product_id and m.state != 'cancel'
        )
        finished_value = sum(
            svl.value for svl in finished_moves.sudo().mapped('stock_valuation_layer_ids') if svl.value > 0
        )
        finished_qty = sum(finished_moves.filtered(lambda m: m.state == 'done').mapped('quantity_done'))
        valued_unit = finished_value / finished_qty if finished_qty else 0.0

        return {
            'material_estimated': material_estimated,
            'material_actual': material_actual,
            'destajo_all': destajo_all,
            'destajo_confirmed': destajo_confirmed,
            'other_cost': self.esi_other_cost or 0.0,
            'estimated_total': estimated_total,
            'estimated_unit': estimated_total / self.product_qty if self.product_qty else 0.0,
            'confirmed_total': confirmed_total,
            'confirmed_unit': confirmed_total / self.product_qty if self.product_qty else 0.0,
            'finished_valuation': finished_value,
            'finished_valuation_unit': valued_unit,
            'missing_cost': sum(row['missing_cost'] for row in material_rows),
        }
