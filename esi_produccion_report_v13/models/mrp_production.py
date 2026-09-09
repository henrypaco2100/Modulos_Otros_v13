# -*- coding: utf-8 -*-
# ESI - utilidades de análisis por Orden de Producción.

from odoo import fields, models, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _esi_report_can_view_costs(self):
        return bool(
            self.env.user.has_group('mrp.group_mrp_manager')
            or self.env.user.has_group('base.group_system')
        )

    def _esi_report_qty_to_default_uom(self, qty, from_uom, product):
        if not product or not from_uom:
            return qty or 0.0
        if from_uom != product.uom_id:
            return from_uom._compute_quantity(qty or 0.0, product.uom_id)
        return qty or 0.0


    def _esi_report_qty_digits(self):
        return self.env['decimal.precision'].precision_get('Product Unit of Measure') or 2

    def _esi_report_money_digits(self):
        self.ensure_one()
        currency = self.company_id.currency_id
        return currency.decimal_places if 'decimal_places' in currency._fields else 2

    def _esi_report_fmt(self, value, digits=2):
        value = value or 0.0
        return ('{:,.%df}' % digits).format(value).replace(',', 'X').replace('.', ',').replace('X', '.')

    def _esi_report_fmt_qty(self, value):
        return self._esi_report_fmt(value, self._esi_report_qty_digits())

    def _esi_report_fmt_money(self, value):
        return self._esi_report_fmt(value, self._esi_report_money_digits())

    def _esi_report_fmt_pct(self, value):
        return self._esi_report_fmt(value, 2)

    def _esi_report_standard_cost(self, product):
        self.ensure_one()
        return product.sudo().with_context(force_company=self.company_id.id).standard_price

    def _esi_report_move_actual_cost(self, move, actual_qty_default):
        """Costo real si existe capa de valoración; caso contrario costo estándar aproximado."""
        self.ensure_one()
        if 'stock_valuation_layer_ids' in move._fields and move.stock_valuation_layer_ids:
            layers = move.sudo().stock_valuation_layer_ids
            value = sum(layers.mapped('value'))
            if value:
                return abs(value)
        return actual_qty_default * self._esi_report_standard_cost(move.product_id)

    def _esi_report_workorder_cost(self):
        self.ensure_one()
        total = 0.0
        for wo in self.workorder_ids:
            duration = getattr(wo, 'duration', 0.0) or 0.0  # minutos en Odoo 13
            workcenter = wo.workcenter_id
            cost_hour = getattr(workcenter, 'costs_hour', 0.0) or 0.0
            total += (duration / 60.0) * cost_hour
        return total

    def _esi_report_store_name(self):
        self.ensure_one()
        warehouse = self.picking_type_id.warehouse_id
        if warehouse and 'store_id' in warehouse._fields:
            return warehouse.store_id.display_name or ''
        return ''

    def _esi_report_material_rows(self, include_costs=False):
        self.ensure_one()
        rows = []
        for move in self.move_raw_ids.filtered(lambda m: m.state != 'cancel' and m.product_id):
            product = move.product_id
            planned = self._esi_report_qty_to_default_uom(move.product_uom_qty, move.product_uom, product)
            actual = self._esi_report_qty_to_default_uom(move.quantity_done, move.product_uom, product)
            variance = actual - planned
            variance_pct = (variance / planned * 100.0) if planned else (100.0 if actual else 0.0)
            row = {
                'product_id': product.id,
                'product': product.display_name,
                'uom': product.uom_id.name or '',
                'planned_qty': planned,
                'actual_qty': actual,
                'variance_qty': variance,
                'variance_pct': variance_pct,
                'planned_cost': 0.0,
                'actual_cost': 0.0,
                'cost_variance': 0.0,
            }
            if include_costs:
                planned_cost = planned * self._esi_report_standard_cost(product)
                actual_cost = self._esi_report_move_actual_cost(move, actual)
                row.update({
                    'planned_cost': planned_cost,
                    'actual_cost': actual_cost,
                    'cost_variance': actual_cost - planned_cost,
                })
            rows.append(row)
        rows.sort(key=lambda r: (r['product'] or '').lower())
        return rows

    def _esi_report_detail_data(self, include_costs=False):
        self.ensure_one()
        can_costs = bool(include_costs and self._esi_report_can_view_costs())
        planned_qty = self._esi_report_qty_to_default_uom(self.product_qty, self.product_uom_id, self.product_id)
        produced_qty = self._esi_report_qty_to_default_uom(self.qty_produced, self.product_uom_id, self.product_id)
        material_rows = self._esi_report_material_rows(include_costs=can_costs)
        material_planned_cost = sum(r['planned_cost'] for r in material_rows) if can_costs else 0.0
        material_actual_cost = sum(r['actual_cost'] for r in material_rows) if can_costs else 0.0
        operation_cost = self._esi_report_workorder_cost() if can_costs else 0.0
        total_cost = material_actual_cost + operation_cost
        sale_price = self.product_id.lst_price if can_costs else 0.0
        potential_revenue = produced_qty * sale_price if can_costs else 0.0
        potential_margin = potential_revenue - total_cost if can_costs else 0.0
        margin_pct = (potential_margin / potential_revenue * 100.0) if potential_revenue else 0.0
        efficiency = (produced_qty / planned_qty * 100.0) if planned_qty else 0.0
        duration_hours = 0.0
        if self.date_start and self.date_finished:
            duration_hours = (self.date_finished - self.date_start).total_seconds() / 3600.0
        elif self.workorder_ids:
            duration_hours = sum((getattr(wo, 'duration', 0.0) or 0.0) for wo in self.workorder_ids) / 60.0

        return {
            'production': self,
            'reference': self.name,
            'product': self.product_id.display_name,
            'uom': self.product_id.uom_id.name or '',
            'bom': self.bom_id.display_name or '',
            'state': dict(self._fields['state'].selection).get(self.state, self.state),
            'responsible': self.user_id.name or '',
            'warehouse': self.picking_type_id.warehouse_id.display_name or '',
            'store': self._esi_report_store_name(),
            'planned_qty': planned_qty,
            'produced_qty': produced_qty,
            'output_variance': produced_qty - planned_qty,
            'efficiency': efficiency,
            'duration_hours': duration_hours,
            'scrap_count': len(self.scrap_ids),
            'material_rows': material_rows,
            'over_material_count': len([r for r in material_rows if r['variance_qty'] > 0]),
            'under_material_count': len([r for r in material_rows if r['variance_qty'] < 0]),
            'can_costs': can_costs,
            'material_planned_cost': material_planned_cost,
            'material_actual_cost': material_actual_cost,
            'material_cost_variance': material_actual_cost - material_planned_cost,
            'operation_cost': operation_cost,
            'total_cost': total_cost,
            'unit_cost': (total_cost / produced_qty) if produced_qty else 0.0,
            'sale_price': sale_price,
            'potential_revenue': potential_revenue,
            'potential_margin': potential_margin,
            'margin_pct': margin_pct,
        }


    # ESI mejora: smart button para VER el análisis individual antes de descargarlo.
    def action_open_esi_production_analysis(self):
        self.ensure_one()
        wizard = self.env['esi.production.detail.wizard'].create({
            'production_id': self.id,
        })
        wizard.preview_html = wizard._build_preview_html()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Análisis de Producción - %s') % (self.name or ''),
            'res_model': 'esi.production.detail.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'view_id': self.env.ref('esi_produccion_report_v13.view_esi_production_detail_wizard_form').id,
            'target': 'current',
        }
