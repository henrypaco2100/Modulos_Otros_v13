# -*- coding: utf-8 -*-
from collections import OrderedDict

from odoo import models


class EsiProductionGroupReport(models.Model):
    _inherit = 'esi.production.group'

    def esi_report_group_data(self):
        self.ensure_one()
        productions = self.production_ids.filtered(lambda p: p.state != 'cancel').sorted(key=lambda p: (p.name or '', p.id))
        rows = []
        material_map = OrderedDict()
        for production in productions:
            if hasattr(production, 'esi_report_cost_summary'):
                totals = production.esi_report_cost_summary()
                material_cost = totals.get('material_estimated', 0.0)
                actual_material_cost = totals.get('material_actual', 0.0)
                finished_valuation = totals.get('finished_valuation', 0.0)
            else:
                material_cost = production.esi_material_cost if 'esi_material_cost' in production._fields else 0.0
                actual_material_cost = material_cost
                finished_valuation = 0.0
            other_cost = production.esi_other_cost if 'esi_other_cost' in production._fields else 0.0
            rows.append({
                'production': production,
                'reference': production.name or '',
                'product': production.product_id.display_name or '',
                'qty': production.product_qty or 0.0,
                'uom': production.product_uom_id.name or '',
                'state': dict(production._fields['state']._description_selection(production.env)).get(production.state, production.state),
                'bom': production.bom_id.display_name or '',
                'material_cost': material_cost,
                'actual_material_cost': actual_material_cost,
                'missing_cost': production.esi_missing_cost if 'esi_missing_cost' in production._fields else 0.0,
                'other_cost': other_cost,
                'estimated_total': material_cost + other_cost,
                'finished_valuation': finished_valuation,
            })
            for move in production.move_raw_ids.filtered(lambda m: m.state != 'cancel' and m.product_id):
                key = (move.product_id.id, move.product_uom.id)
                if key not in material_map:
                    material_map[key] = {
                        'product': move.product_id.display_name,
                        'uom': move.product_uom.name or '',
                        'required': 0.0,
                        'actual': 0.0,
                        'missing': 0.0,
                        'estimated_cost': 0.0,
                    }
                item = material_map[key]
                item['required'] += move.product_uom_qty or 0.0
                item['actual'] += move.quantity_done or 0.0
                item['missing'] += move.esi_missing_qty if 'esi_missing_qty' in move._fields else 0.0
                item['estimated_cost'] += move.esi_total_material_cost if 'esi_total_material_cost' in move._fields else 0.0

        return {
            'group': self,
            'productions': rows,
            'materials': list(material_map.values()),
            'material_cost': sum(r['material_cost'] for r in rows),
            'actual_material_cost': sum(r['actual_material_cost'] for r in rows),
            'missing_cost': sum(r['missing_cost'] for r in rows),
            'other_cost': sum(r['other_cost'] for r in rows),
            'estimated_total': sum(r['estimated_total'] for r in rows),
            'finished_valuation': sum(r['finished_valuation'] for r in rows),
        }
