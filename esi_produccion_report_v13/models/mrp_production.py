# -*- coding: utf-8 -*-
# ESI - utilidades de análisis por Orden de Producción.

from odoo import fields, models


def _esi_selection_label(record, field_name, value, default=''):
    """Devuelve la etiqueta de un Selection de forma segura en Odoo 13.

    Los campos related Selection pueden exponer ``field.selection`` como una
    función. Convertir directamente ``dict(field.selection)`` provoca
    TypeError: 'function' object is not iterable.
    """
    if not value:
        return default
    field = record._fields.get(field_name)
    if not field:
        return value or default
    try:
        selection = field._description_selection(record.env)
    except Exception:
        selection = field.selection
        if isinstance(selection, str):
            selection = getattr(record, selection)()
        elif callable(selection):
            try:
                selection = selection(record)
            except TypeError:
                selection = selection(record.env[record._name])
    try:
        return dict(selection or []).get(value, value or default)
    except (TypeError, ValueError):
        return value or default



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

    def _esi_report_standard_cost(self, product, move=None):
        self.ensure_one()
        if move is not None and 'esi_unit_cost' in move._fields and move.esi_unit_cost:
            return move.esi_unit_cost
        return product.sudo().with_context(force_company=self.company_id.id).standard_price

    def _esi_report_move_actual_cost(self, move, actual_qty_default):
        """Costo real si existe capa de valoración; caso contrario costo estándar aproximado."""
        self.ensure_one()
        if 'stock_valuation_layer_ids' in move._fields and move.stock_valuation_layer_ids:
            layers = move.sudo().stock_valuation_layer_ids
            value = sum(layers.mapped('value'))
            if value:
                return abs(value)
        return actual_qty_default * self._esi_report_standard_cost(move.product_id, move=move)

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
                planned_cost = (move.esi_total_material_cost if 'esi_total_material_cost' in move._fields and move.esi_total_material_cost else planned * self._esi_report_standard_cost(product, move=move))
                actual_cost = self._esi_report_move_actual_cost(move, actual)
                row.update({
                    'planned_cost': planned_cost,
                    'actual_cost': actual_cost,
                    'cost_variance': actual_cost - planned_cost,
                })
            rows.append(row)
        rows.sort(key=lambda r: (r['product'] or '').lower())
        return rows


    def _esi_report_operation_rows(self):
        """Detalle de operaciones compatible con instalaciones con/sin esi_mrp_mejoras_v13."""
        self.ensure_one()
        rows = []
        for wo in self.workorder_ids.sorted(key=lambda w: ((w.operation_id.sequence if w.operation_id else 999999), w.id)):
            operation = wo.operation_id
            time_lines = wo.time_ids
            custom_time = bool(time_lines and 'esi_piece_amount' in time_lines._fields)
            registered_piecework = sum(time_lines.mapped('esi_piece_amount')) if custom_time else 0.0
            registered_qty = sum(time_lines.mapped('esi_qty_processed')) if custom_time and 'esi_qty_processed' in time_lines._fields else 0.0
            standard_seconds = operation.esi_standard_seconds if operation and 'esi_standard_seconds' in operation._fields else 0.0
            piece_rate = operation.esi_piece_rate if operation and 'esi_piece_rate' in operation._fields else 0.0
            labor_cost_pair = operation.esi_labor_cost_pair if operation and 'esi_labor_cost_pair' in operation._fields else 0.0
            operator = ''
            area = ''
            measurement = ''
            source_sheet = ''
            source_row = 0
            if operation:
                if 'esi_operator_id' in operation._fields and operation.esi_operator_id:
                    operator = operation.esi_operator_id.display_name or ''
                if 'esi_area' in operation._fields:
                    area = operation.esi_area or ''
                if 'esi_measurement_status' in operation._fields:
                    measurement = _esi_selection_label(operation, 'esi_measurement_status', operation.esi_measurement_status, '')
                if 'esi_source_sheet' in operation._fields:
                    source_sheet = operation.esi_source_sheet or ''
                if 'esi_source_row' in operation._fields:
                    source_row = operation.esi_source_row or 0
            planned_qty = wo.qty_production or self.product_qty or 0.0
            rows.append({
                'name': wo.name or (operation.name if operation else ''),
                'workcenter': wo.workcenter_id.display_name or '',
                'area': area,
                'operator': operator,
                'measurement_status': measurement,
                'source_sheet': source_sheet,
                'source_row': source_row,
                'standard_seconds_pair': standard_seconds,
                'standard_minutes_pair': standard_seconds / 60.0 if standard_seconds else 0.0,
                'standard_minutes_total': (standard_seconds * planned_qty / 60.0) if standard_seconds else 0.0,
                'actual_minutes': wo.duration or 0.0,
                'piece_rate': piece_rate,
                'planned_piecework': piece_rate * planned_qty,
                'registered_piecework': registered_piecework,
                'registered_qty': registered_qty,
                'labor_cost_pair': labor_cost_pair,
                'planned_labor_cost': labor_cost_pair * planned_qty,
                'workcenter_cost_hour': wo.workcenter_id.costs_hour or 0.0,
                'actual_workcenter_cost': ((wo.duration or 0.0) / 60.0) * (wo.workcenter_id.costs_hour or 0.0),
            })
        return rows

    def _esi_report_detail_data(self, include_costs=False):
        self.ensure_one()
        can_costs = bool(include_costs and self._esi_report_can_view_costs())
        planned_qty = self._esi_report_qty_to_default_uom(self.product_qty, self.product_uom_id, self.product_id)
        produced_qty = self._esi_report_qty_to_default_uom(self.qty_produced, self.product_uom_id, self.product_id)
        material_rows = self._esi_report_material_rows(include_costs=can_costs)
        material_planned_cost = sum(r['planned_cost'] for r in material_rows) if can_costs else 0.0
        material_actual_cost = sum(r['actual_cost'] for r in material_rows) if can_costs else 0.0
        operation_rows = self._esi_report_operation_rows()
        operation_cost = (sum(self.esi_destajo_ids.filtered(lambda d: d.state in ('confirmed', 'paid')).mapped('amount')) if can_costs and 'esi_destajo_ids' in self._fields else (self._esi_report_workorder_cost() if can_costs else 0.0))
        piecework_planned_total = sum(r['planned_piecework'] for r in operation_rows)
        piecework_registered_total = sum(r['registered_piecework'] for r in operation_rows)
        standard_operation_minutes = sum(r['standard_minutes_total'] for r in operation_rows)
        actual_operation_minutes = sum(r['actual_minutes'] for r in operation_rows)
        standard_labor_cost = sum(r['planned_labor_cost'] for r in operation_rows)
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
            'state': _esi_selection_label(self, 'state', self.state, self.state),
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
            'operation_rows': operation_rows,
            'has_esi_operations': any(r['area'] or r['operator'] or r['piece_rate'] or r['standard_seconds_pair'] for r in operation_rows),
            'piecework_planned_total': piecework_planned_total,
            'piecework_registered_total': piecework_registered_total,
            'standard_operation_minutes': standard_operation_minutes,
            'actual_operation_minutes': actual_operation_minutes,
            'standard_labor_cost': standard_labor_cost,
            'operation_cost': operation_cost,
            'total_cost': total_cost,
            'unit_cost': (total_cost / produced_qty) if produced_qty else 0.0,
            'sale_price': sale_price,
            'potential_revenue': potential_revenue,
            'potential_margin': potential_margin,
            'margin_pct': margin_pct,
        }


# -----------------------------------------------------------------------------
# ESI CALZADOS - reportes por Orden de Fabricación
# Se mantienen los informes históricos del módulo y se agregan los nuevos
# reportes de costo, faltantes y destajos.
# -----------------------------------------------------------------------------
from collections import OrderedDict as EsiOrderedDict


class MrpProductionCalzadoReports(models.Model):
    _inherit = 'mrp.production'

    def esi_report_material_rows(self):
        """Filas de materiales para la ficha de costo / faltantes.

        Prioridad del costo:
        1) costo histórico capturado en la OF por esi_calzados_v13;
        2) costo estándar/AVCO vigente;
        3) capa de valoración para costo real cuando el movimiento ya fue hecho.
        """
        self.ensure_one()
        rows = []
        for move in self.move_raw_ids.filtered(lambda m: m.state != 'cancel' and m.product_id):
            planned_qty = move.product_uom_qty or 0.0
            actual_qty = move.quantity_done or 0.0
            if 'esi_unit_cost' in move._fields:
                unit_cost = move.esi_unit_cost or 0.0
            else:
                product = move.product_id.sudo().with_context(force_company=self.company_id.id)
                unit_cost = product.standard_price or 0.0
            if 'esi_total_material_cost' in move._fields:
                planned_cost = move.esi_total_material_cost or (planned_qty * unit_cost)
            else:
                planned_cost = planned_qty * unit_cost
            svl_value = 0.0
            if 'stock_valuation_layer_ids' in move._fields and move.stock_valuation_layer_ids:
                svl_value = abs(sum(move.sudo().stock_valuation_layer_ids.mapped('value')))
            actual_cost = svl_value if svl_value else actual_qty * unit_cost
            actual_unit_cost = actual_cost / actual_qty if actual_qty else unit_cost
            rows.append({
                'move_id': move.id,
                'group': _esi_selection_label(move, 'esi_material_group', move.esi_material_group, '') if 'esi_material_group' in move._fields and move.esi_material_group else '',
                'product': move.product_id.display_name,
                'uom': move.product_uom.name or '',
                'qty_per_unit': move.esi_qty_per_unit if 'esi_qty_per_unit' in move._fields else ((planned_qty / self.product_qty) if self.product_qty else 0.0),
                'planned_qty': planned_qty,
                'actual_qty': actual_qty,
                'unit_cost': unit_cost,
                'actual_unit_cost': actual_unit_cost,
                'unit_material_cost': move.esi_unit_material_cost if 'esi_unit_material_cost' in move._fields else ((planned_qty / self.product_qty) * unit_cost if self.product_qty else 0.0),
                'planned_cost': planned_cost,
                'actual_cost': actual_cost,
                'available_qty': move.esi_available_qty if 'esi_available_qty' in move._fields else 0.0,
                'missing_qty': move.esi_missing_qty if 'esi_missing_qty' in move._fields else 0.0,
                'purchase_unit_cost': move.esi_purchase_unit_cost if 'esi_purchase_unit_cost' in move._fields else unit_cost,
                'missing_cost': move.esi_missing_cost if 'esi_missing_cost' in move._fields else 0.0,
                'supplier': move.esi_get_supplier_name() if hasattr(move, 'esi_get_supplier_name') else '',
            })
        return rows

    def esi_report_shortage_rows(self):
        self.ensure_one()
        return [row for row in self.esi_report_material_rows() if row['missing_qty'] > 0.000001]

    def esi_report_destajo_rows(self):
        self.ensure_one()
        rows = []
        destajos = self.esi_destajo_ids if 'esi_destajo_ids' in self._fields else self.env['esi.calzado.destajo']
        for line in destajos.sorted(key=lambda d: (d.date or '', d.id)):
            rows.append({
                'date': line.date,
                'worker': line.partner_id.display_name or '',
                'activity': line.activity_id.display_name or '',
                'description': line.description or '',
                'quantity': line.quantity or 0.0,
                'uom': line.uom_id.name or '',
                'unit_price': line.unit_price or 0.0,
                'amount': line.amount or 0.0,
                'state': _esi_selection_label(line, 'state', line.state, line.state or ''),
            })
        return rows

    def esi_report_destajo_summary(self):
        self.ensure_one()
        grouped = EsiOrderedDict()
        destajos = self.esi_destajo_ids if 'esi_destajo_ids' in self._fields else self.env['esi.calzado.destajo']
        for line in destajos:
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
        destajos = self.esi_destajo_ids if 'esi_destajo_ids' in self._fields else self.env['esi.calzado.destajo']
        destajo_all = sum(destajos.mapped('amount'))
        destajo_confirmed = sum(destajos.filtered(lambda d: d.state in ('confirmed', 'paid')).mapped('amount'))
        other_cost = self.esi_other_cost if 'esi_other_cost' in self._fields else 0.0
        estimated_total = material_estimated + destajo_all + (other_cost or 0.0)
        confirmed_total = material_actual + destajo_confirmed + (other_cost or 0.0)

        finished_moves = self.move_finished_ids.filtered(
            lambda m: m.product_id == self.product_id and m.state != 'cancel'
        )
        finished_value = 0.0
        if finished_moves and 'stock_valuation_layer_ids' in finished_moves._fields:
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
            'other_cost': other_cost or 0.0,
            'estimated_total': estimated_total,
            'estimated_unit': estimated_total / self.product_qty if self.product_qty else 0.0,
            'confirmed_total': confirmed_total,
            'confirmed_unit': confirmed_total / self.product_qty if self.product_qty else 0.0,
            'finished_valuation': finished_value,
            'finished_valuation_unit': valued_unit,
            'missing_cost': sum(row['missing_cost'] for row in material_rows),
        }
