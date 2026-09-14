# -*- coding: utf-8 -*-
"""Carga de datos demostrativos para la fábrica de calzado.

La fuente de tiempos/destajo es la planilla entregada por el cliente:
"CALCULO DE TIEMPOS Y COSTOS DE DESTAJO.xlsx".

Los datos comerciales/contables que no existen en la planilla son explícitamente
DEMO y se crean sólo para mostrar un ciclo empresarial completo en Odoo 13.
"""
from datetime import datetime, timedelta, time

from odoo import api, fields, models, _


# Hoja "BOTA DE LONA", filas 3..61.
# (fila, operador, area, trabajo, segundos_promedio, pago_destajo_por_par)
LONA_OPERATIONS = [
    (3, 'FRANCISCO', 'CORTADO', 'LONA CAÑA', 50.0, 0.20),
    (4, 'FRANCISCO', 'CORTADO', 'LONA CUELLO', 30.0, 0.15),
    (5, 'FRANCISCO', 'CORTADO', 'LONA LENGUA', 30.0, 0.15),
    (6, 'FRANCISCO', 'CORTADO', 'SUEDE OJAL', 30.0, 0.15),
    (7, 'FRANCISCO', 'CORTADO', 'SUEDE TALON', 30.0, 0.15),
    (8, 'FRANCISCO', 'CORTADO', 'ESPUMA CUELLO', 30.0, 0.15),
    (9, 'FRANCISCO', 'CORTADO', 'CINTA LATERAL', 30.0, 0.15),
    (10, 'FRANCISCO', 'CORTADO', 'FORRO LOBO MARINO', 120.0, 0.50),
    (11, 'FRANCISCO', 'CORTADO', 'PEKA FORRO CAPELLADA', 30.0, 0.15),
    (12, 'FRANCISCO', 'CORTADO', 'TERMO+TUBOX PUNTERA', 15.0, 0.10),
    (13, 'MIGUEL', 'CORTADO', 'TERMO+TUBOX TALON', 15.0, 0.10),
    (14, 'SANTOS', 'CORTADO', 'CUERO CAPELLADA', 48.0, 0.30),
    (15, 'MIGUEL', 'CORTADO', 'CUERO OJAL', 43.0, 0.25),
    (16, 'SANTOS', 'CORTADO', 'CUERO TALON', 41.0, 0.25),
    (17, 'SANTOS', 'CORTADO', 'CUERO PATITAS', 35.0, 0.20),
    (18, 'SANTOS', 'CORTADO', 'TOCUYO REFUERZO', 15.0, 0.10),
    (19, 'MIGUEL', 'CORTADO', 'PLANTILLA DE ARMAR', 30.0, 0.15),
    (20, 'JUAN', 'CORTADO', 'RETACON', 17.0, 0.10),
    (21, 'JUAN', 'CORTADO', 'UNION RETACON+PLANTILLA', 43.0, 0.25),
    (22, 'MARY', 'APARADO', 'PEGADO DE CAPELLADAS', 250.0, 1.00),
    (23, False, 'APARADO', 'DESBASTADO', 0.0, 0.50),
    (24, 'MARY', 'APARADO', 'CUELLO+ESPUMA', 168.0, 0.80),
    (25, False, 'APARADO', 'PEGADO DE FORROS', 0.0, 1.50),
    (26, 'MARY', 'APARADO', 'CAÑA+CINTAS', 520.0, 2.00),
    (27, 'MARY', 'APARADO', 'NUMERACION +COSTURA', 132.0, 0.50),
    (28, 'MARY', 'APARADO', 'RIVETEADO', 127.0, 0.30),
    (29, 'MARY', 'APARADO', 'ATRAQUE', 1286.0, 0.80),
    (30, 'MARY', 'APARADO', 'CERRADO', 1284.0, 2.00),
    (31, False, 'APARADO', 'DECORADO', 0.0, 1.50),
    (32, 'MARY', 'APARADO', 'RECORTADO+CORTAR HILOS', 25.0, 0.15),
    (33, False, 'APARADO', 'REMACHE', 0.0, 0.50),
    (34, 'FERNANDA', 'CONFORMADO', 'PEGAR TALON TERMO+TUBOX', 44.0, 0.20),
    (35, 'FERNANDA', 'CONFORMADO', 'EMPASTAR +PONER TALON', 53.0, 0.40),
    (36, 'FERNANDA', 'CONFORMADO', 'CONFORMAR', 105.0, 0.40),
    (37, 'FERNANDA', 'CONFORMADO', 'PLANCHAR', 50.0, 0.30),
    (38, 'FERNANDA', 'CONFORMADO', 'PERFORADO DE JALADOR', 85.0, 0.50),
    (39, 'FERNANDA', 'CONFORMADO', 'PONER JALADORES', 193.0, 1.10),
    (40, 'FERNANDA', 'CONFORMADO', 'REMACHAR JALADORES', 45.0, 0.25),
    (41, 'FERNANDA', 'CONFORMADO', 'PERFORADO DE OJALILLO', 54.0, 0.30),
    (42, 'FERNANDA', 'CONFORMADO', 'PONER OJALILLOS', 40.0, 0.25),
    (43, 'BRAYAN', 'SOLADO', 'EMPLANTILLADO', 38.63, 0.20),
    (44, 'RAUL', 'SOLADO', 'ARMADO', 169.8, 0.95),
    (45, 'RAUL', 'SOLADO', 'LIMPIADO', 82.8, 0.45),
    (46, 'RAUL', 'SOLADO', 'CLEFEADO', 69.0, 0.40),
    (47, 'RAUL', 'SOLADO', 'CERRADO', 38.93, 0.20),
    (48, 'RAUL', 'SOLADO', 'ACENTADO', 30.6, 0.20),
    (49, 'RAUL', 'SOLADO', 'RASQUETEADO', 30.6, 0.20),
    (50, 'RAUL', 'SOLADO', 'SACAR GRAMPAS', 28.1, 0.15),
    (51, 'RAUL', 'SOLADO', 'PVC PRIMERA', 37.95, 0.20),
    (52, 'RAUL', 'SOLADO', 'PVC SEGUNDA', 38.0, 0.20),
    (53, 'RAUL', 'SOLADO', 'SOBRECHEADO', 241.8, 1.20),
    (54, 'RAUL', 'SOLADO', 'SACADO DE HORMA', 60.5, 0.35),
    (55, 'HERMINIA', 'TERMINADO', 'LIMPIADO+REQUEMADO+EMBOLSADO', 252.0, 1.45),
    (56, 'EDITH', 'PLANTAS', 'REBARBEADO', 83.0, 0.50),
    (57, 'LIMBER', 'PLANTAS', 'LIJADO', 120.0, 0.70),
    (58, 'LIMBER', 'PLANTAS', 'SOPLETEADO', 20.0, 0.10),
    (59, 'LIMBER', 'PLANTAS', 'HALOGENADO', 21.97, 0.15),
    (60, 'LIMBER', 'PLANTAS', 'PVC PRIMERA', 40.32, 0.25),
    (61, 'LIMBER', 'PLANTAS', 'PVC SEGUNDA', 57.99, 0.35),
]

# Hoja "BOTA INDUSTRIAL", filas cuyo nombre de trabajo sí es legible.
# Los tiempos de esta zona de la hoja contienen vacíos/inconsistencias/#REF!,
# por eso se cargan como pendientes de medición y NO se inventa tiempo.
INDUSTRIAL_OPERATIONS = [
    (43, 'BRAYAN', 'SOLADO', 'EMPLANTILLADO'),
    (44, 'RAUL', 'SOLADO', 'ARMADO'),
    (45, 'RAUL', 'SOLADO', 'LIMPIADO'),
    (46, 'RAUL', 'SOLADO', 'CLEFEADO 1'),
    (47, 'RAUL', 'SOLADO', 'ENCASQUILLADO'),
    (48, 'RAUL', 'SOLADO', 'CLEFEADO 2'),
    (49, 'RAUL', 'SOLADO', 'CERRADO PUNTA'),
    (50, 'RAUL', 'SOLADO', 'JALADO TALON'),
    (51, 'RAUL', 'SOLADO', 'LIMPIADO 2'),
    (52, 'RAUL', 'SOLADO', 'CLEFEADO 3'),
    (53, 'RAUL', 'SOLADO', 'CERRADO TALÓN'),
    (54, 'RAUL', 'SOLADO', 'ACENTADO'),
    (55, 'HERMINIA', 'TERMINADO', 'RASQUETADO 1'),
    (56, 'EDITH', 'PLANTAS', 'MARCADO'),
    (57, 'LIMBER', 'PLANTAS', 'RASQUETADO 2'),
    (58, 'LIMBER', 'PLANTAS', 'PVC 1'),
    (59, 'LIMBER', 'PLANTAS', 'PVC 2'),
    (60, 'LIMBER', 'PLANTAS', 'PEGADO'),
    (61, 'LIMBER', 'PLANTAS', 'SACADO HORMA'),
]


# Hoja "BOTA DE LONA", apuntes adicionales filas 67..69.
# (fila, concepto, area, cantidad, tarifa)
EXTRA_PIECEWORK_NOTES = [
    (67, 'SOBRECHADO', 'SOLADO', 62.0, 1.00),
    (68, 'ARMADO', 'SOLADO', 58.0, 0.70),
    (69, 'PLANTAS COMPLETOP', 'PLANTAS', 16.0, 1.15),
]

AREA_SEQUENCE = {
    'CORTADO': 10,
    'APARADO': 20,
    'CONFORMADO': 30,
    'SOLADO': 40,
    'TERMINADO': 50,
    'PLANTAS': 60,
}

RAW_PRODUCTS = [
    # code, name, cost, stock target, uom-key
    ('MP-CUERO', 'CUERO HUNTING', 42.00, 300.0, 'unit'),
    ('MP-LONA', 'LONA PARA CALZADO', 24.00, 400.0, 'meter'),
    ('MP-ESPUMA', 'FIBRA ESPUMA', 18.00, 180.0, 'meter'),
    ('MP-LOBO', 'LOBO MARINO / FORRO', 22.00, 250.0, 'meter'),
    ('MP-PK', 'PK / PEKA PARA FORRO', 12.00, 250.0, 'meter'),
    ('MP-SUEDE', 'SUEDE / SINTÉTICO', 26.00, 220.0, 'meter'),
    ('MP-TERMO', 'TERMOPLÁSTICO', 30.00, 120.0, 'unit'),
    ('MP-TOCUYO', 'TOCUYO', 10.00, 250.0, 'meter'),
    ('MP-TUBOX', 'TUBOX', 16.00, 160.0, 'unit'),
    ('MP-PEG', 'PEGAMENTO PARA CALZADO', 38.00, 120.0, 'kg'),
    ('MP-CORDON', 'CORDONES', 4.50, 500.0, 'unit'),
    ('MP-HILO', 'HILO POLIÉSTER', 0.35, 5000.0, 'meter'),
    ('MP-PLANT', 'PLANTILLA DE ARMAR', 8.00, 500.0, 'unit'),
    ('MP-SUELA', 'SUELA', 22.00, 500.0, 'unit'),
    ('MP-OJAL', 'OJALES / OJALILLOS', 0.35, 5000.0, 'unit'),
    ('MP-AGUJ', 'AGUJETAS / JALADORES', 0.80, 1500.0, 'unit'),
    ('MP-CASQ', 'CASQUILLO SEGURIDAD BOTA INDUSTRIAL', 28.00, 250.0, 'unit'),
]

# Cantidades DEMO por par. La planilla entregada no contiene una LdM de materiales.
BOM_LONA = [
    ('MP-CUERO', 0.65), ('MP-LONA', 0.80), ('MP-ESPUMA', 0.15),
    ('MP-LOBO', 0.30), ('MP-PK', 0.20), ('MP-SUEDE', 0.25),
    ('MP-TERMO', 0.08), ('MP-TOCUYO', 0.15), ('MP-TUBOX', 0.08),
    ('MP-PEG', 0.12), ('MP-CORDON', 1.00), ('MP-HILO', 8.00),
    ('MP-PLANT', 1.00), ('MP-SUELA', 1.00), ('MP-OJAL', 12.00), ('MP-AGUJ', 2.00),
]
BOM_INDUSTRIAL = [
    ('MP-CUERO', 1.10), ('MP-LOBO', 0.35), ('MP-TERMO', 0.10),
    ('MP-TUBOX', 0.10), ('MP-PEG', 0.16), ('MP-HILO', 10.00),
    ('MP-PLANT', 1.00), ('MP-SUELA', 1.00), ('MP-OJAL', 12.00),
    ('MP-AGUJ', 2.00), ('MP-CASQ', 1.00),
]


class EsiDemoCalzadoLoader(models.AbstractModel):
    _name = 'esi.demo.calzado.promedio.loader'
    _description = 'Cargador Demo ESI - Fábrica de Calzado AVCO'

    @api.model
    def _company_env(self, company):
        ctx = dict(self.env.context)
        ctx.update(force_company=company.id, allowed_company_ids=[company.id])
        return self.with_context(ctx).env

    @api.model
    def _xmlref(self, env, xmlid, model=None):
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec and (not model or rec._name == model):
            return rec
        return env[model] if model else False

    @api.model
    def _get_or_create_company(self):
        Company = self.env['res.company'].sudo()
        company = Company.search([('name', '=', 'Calzados ESI DEMO PROMEDIO S.R.L.')], limit=1)
        bob = self.env['res.currency'].sudo().search([('name', '=', 'BOB')], limit=1)
        country = self.env.ref('base.bo', raise_if_not_found=False)
        vals = {
            'name': 'Calzados ESI DEMO PROMEDIO S.R.L.',
            'esi_avg_monthly_labor_cost': 3300.0,
            'esi_workdays_month': 26.0,
            'esi_hours_day': 8.0,
            'esi_reference_pairs_day': 5.0,
        }
        if bob:
            vals['currency_id'] = bob.id
        if country:
            vals['country_id'] = country.id
        if not company:
            company = Company.create(vals)
        else:
            company.write({k: v for k, v in vals.items() if k.startswith('esi_')})

        # La compañía queda disponible para administradores/MRP managers sin
        # cambiarles su compañía actual.
        users = self.env['res.users'].sudo().search([
            ('active', '=', True),
            '|',
            ('groups_id', 'in', self.env.ref('base.group_system').id),
            ('groups_id', 'in', self.env.ref('mrp.group_mrp_manager').id),
        ])
        request_uid = self.env.context.get('esi_demo_request_uid')
        if request_uid:
            users |= self.env['res.users'].sudo().browse(request_uid).exists()
        for user in users:
            if company not in user.company_ids:
                user.sudo().write({'company_ids': [(4, company.id)]})
        return company

    @api.model
    def _get_or_create_warehouse(self, env, company):
        Warehouse = env['stock.warehouse'].sudo()
        warehouse = Warehouse.search([('company_id', '=', company.id)], limit=1)
        if not warehouse:
            warehouse = Warehouse.create({
                'name': 'Almacén Calzados ESI DEMO AVCO',
                'code': 'AVCO',
                'company_id': company.id,
            })
        return warehouse

    @api.model
    def _get_uoms(self, env):
        unit = self._xmlref(env, 'uom.product_uom_unit', 'uom.uom')
        if not unit:
            unit = env['uom.uom'].sudo().search([], limit=1)
        meter = self._xmlref(env, 'uom.product_uom_meter', 'uom.uom') or unit
        kg = self._xmlref(env, 'uom.product_uom_kgm', 'uom.uom') or unit

        cat = env['uom.category'].sudo().search([('name', '=', 'ESI Demo AVCO - Pares de Calzado')], limit=1)
        if not cat:
            cat = env['uom.category'].sudo().create({'name': 'ESI Demo AVCO - Pares de Calzado'})
        pair = env['uom.uom'].sudo().search([('name', '=', 'Par'), ('category_id', '=', cat.id)], limit=1)
        if not pair:
            pair = env['uom.uom'].sudo().create({
                'name': 'Par',
                'category_id': cat.id,
                'uom_type': 'reference',
                'rounding': 1.0,
            })
        return {'unit': unit, 'meter': meter, 'kg': kg, 'pair': pair}

    @api.model
    def _get_or_create_categories(self, env):
        """Categorías aisladas para la demo AVCO.

        property_cost_method es company_dependent en Odoo 13, por lo que la
        escritura se realiza con force_company de la compañía demo.
        """
        Category = env['product.category'].sudo()
        root = Category.search([('name', '=', 'ESI DEMO AVCO - Calzado')], limit=1)
        if not root:
            root = Category.create({'name': 'ESI DEMO AVCO - Calzado'})
        raw = Category.search([('name', '=', 'Materias Primas ESI DEMO AVCO'), ('parent_id', '=', root.id)], limit=1)
        if not raw:
            raw = Category.create({'name': 'Materias Primas ESI DEMO AVCO', 'parent_id': root.id})
        finished = Category.search([('name', '=', 'Producto Terminado ESI DEMO AVCO'), ('parent_id', '=', root.id)], limit=1)
        if not finished:
            finished = Category.create({'name': 'Producto Terminado ESI DEMO AVCO', 'parent_id': root.id})

        # Costo Promedio (AVCO) en TODAS las categorías de la demo.
        # Dejamos valoración contable manual para no exigir cuentas de stock
        # antes de crear el plan contable demo; AVCO funciona igualmente sobre
        # las capas de valoración y actualiza standard_price al recibir compras.
        for category in (root, raw, finished):
            vals = {}
            if 'property_cost_method' in category._fields:
                vals['property_cost_method'] = 'average'
            if 'property_valuation' in category._fields:
                vals['property_valuation'] = 'manual_periodic'
            if vals:
                category.with_context(force_company=env.context.get('force_company')).sudo().write(vals)
        return raw, finished

    @api.model
    def _get_or_create_products(self, env, company, uoms, categories):
        Product = env['product.product'].sudo()
        raw_cat, finished_cat = categories
        products = {}
        for code, name, _cost, _stock, uom_key in RAW_PRODUCTS:
            avco_code = 'AVCO-' + code
            product = Product.search([('default_code', '=', avco_code), ('company_id', '=', company.id)], limit=1)
            vals = {
                'name': '%s [AVCO]' % name,
                'default_code': avco_code,
                'type': 'product',
                'categ_id': raw_cat.id,
                'uom_id': uoms[uom_key].id,
                'uom_po_id': uoms[uom_key].id,
                'company_id': company.id,
                'purchase_ok': True,
                'sale_ok': False,
            }
            if not product:
                # El costo arranca en cero. Las recepciones de compra son las
                # que deben formar el costo promedio de la demo.
                vals['standard_price'] = 0.0
                product = Product.create(vals)
            else:
                # Idempotencia: nunca resetear standard_price al recargar la
                # demo porque destruiría el promedio ya calculado por Odoo.
                product.write({k: v for k, v in vals.items() if k != 'standard_price'})
            products[code] = product

        final_defs = [
            ('PT-BOTA-LONA', 'BOTA DE LONA M-L-01 [AVCO]', 185.00),
            ('PT-BOTA-IND', 'BOTA INDUSTRIAL ESI DEMO [AVCO]', 260.00),
        ]
        for code, name, price in final_defs:
            avco_code = 'AVCO-' + code
            product = Product.search([('default_code', '=', avco_code), ('company_id', '=', company.id)], limit=1)
            vals = {
                'name': name,
                'default_code': avco_code,
                'type': 'product',
                'categ_id': finished_cat.id,
                'uom_id': uoms['pair'].id,
                'uom_po_id': uoms['pair'].id,
                'lst_price': price,
                'company_id': company.id,
                'sale_ok': True,
                'purchase_ok': False,
                'description_sale': 'Producto DEMO ESI AVCO. El método de coste de su categoría es Promedio. Procesos/tiempos de Bota de Lona provienen de la planilla entregada.',
            }
            if not product:
                vals['standard_price'] = 0.0
                product = Product.create(vals)
            else:
                product.write({k: v for k, v in vals.items() if k != 'standard_price'})
            products[code] = product
        return products

    @api.model
    def _set_target_stock(self, env, warehouse, products):
        # En la demo AVCO NO inyectamos materias primas directamente en quants.
        # El inventario debe nacer de compras/recepciones para que el costo
        # promedio se calcule con movimientos reales de inventario.
        return True

    @api.model
    def _get_or_create_operators(self, env, company):
        names = sorted(set([x[1] for x in LONA_OPERATIONS if x[1]] + [x[1] for x in INDUSTRIAL_OPERATIONS if x[1]]))
        result = {}
        Operator = env['esi.mrp.operator'].sudo()
        for i, name in enumerate(names, 1):
            op = Operator.search([('name', '=', name), ('company_id', '=', company.id)], limit=1)
            if not op:
                op = Operator.create({
                    'name': name,
                    'code': 'OP%02d' % i,
                    'company_id': company.id,
                    'notes': 'Operador cargado desde la planilla de tiempos/destajo ESI.',
                })
            result[name] = op
        return result

    @api.model
    def _get_or_create_workcenters(self, env, company):
        Workcenter = env['mrp.workcenter'].sudo()
        result = {}
        cost_hour = 3300.0 / 26.0 / 8.0
        calendar = company.resource_calendar_id
        for area in sorted(AREA_SEQUENCE, key=lambda a: AREA_SEQUENCE[a]):
            name = '%s - ESI DEMO' % area.title()
            wc = Workcenter.search([('name', '=', name), ('company_id', '=', company.id)], limit=1)
            vals = {
                'name': name,
                'code': 'ESI-%s' % area[:4],
                'company_id': company.id,
                'costs_hour': cost_hour,
                'time_efficiency': 100.0,
                'capacity': 1.0,
                'sequence': AREA_SEQUENCE[area],
            }
            if calendar:
                vals['resource_calendar_id'] = calendar.id
            if not wc:
                wc = Workcenter.create(vals)
            else:
                wc.write({'costs_hour': cost_hour, 'sequence': AREA_SEQUENCE[area]})
            result[area] = wc
        return result

    @api.model
    def _get_or_create_routing(self, env, company, name, code):
        Routing = env['mrp.routing'].sudo()
        routing = Routing.search([('name', '=', name), ('company_id', '=', company.id)], limit=1)
        if not routing:
            routing = Routing.create({'name': name, 'code': code, 'company_id': company.id})
        return routing

    @api.model
    def _load_lona_operations(self, env, routing, workcenters, operators):
        Operation = env['mrp.routing.workcenter'].sudo()
        keep_ids = []
        for index, (row, operator_name, area, job, seconds, piece_rate) in enumerate(LONA_OPERATIONS, 1):
            domain = [
                ('routing_id', '=', routing.id),
                ('esi_source_sheet', '=', 'BOTA DE LONA'),
                ('esi_source_row', '=', row),
            ]
            op = Operation.search(domain, limit=1)
            vals = {
                'name': '%02d. %s' % (index, job),
                'sequence': index * 10,
                'routing_id': routing.id,
                'workcenter_id': workcenters[area].id,
                'time_mode': 'manual',
                'time_cycle_manual': (seconds / 60.0) if seconds else 0.0,
                'batch': 'no',
                'esi_operator_id': operators[operator_name].id if operator_name else False,
                'esi_area': area,
                'esi_standard_seconds': seconds,
                'esi_piece_rate': piece_rate,
                'esi_batch_qty': 50.0,
                'esi_measurement_status': 'measured' if seconds else 'pending',
                'esi_source_sheet': 'BOTA DE LONA',
                'esi_source_row': row,
                'esi_source_note': 'CALCULO DE TIEMPOS Y COSTOS DE DESTAJO.xlsx%s' % (' - tiempo no registrado en origen' if not seconds else ''),
            }
            if not op:
                op = Operation.create(vals)
            else:
                op.write(vals)
            keep_ids.append(op.id)
        return Operation.browse(keep_ids)

    @api.model
    def _load_industrial_operations(self, env, routing, workcenters, operators):
        Operation = env['mrp.routing.workcenter'].sudo()
        keep_ids = []
        for index, (row, operator_name, area, job) in enumerate(INDUSTRIAL_OPERATIONS, 1):
            op = Operation.search([
                ('routing_id', '=', routing.id),
                ('esi_source_sheet', '=', 'BOTA INDUSTRIAL'),
                ('esi_source_row', '=', row),
            ], limit=1)
            vals = {
                'name': '%02d. %s' % (index, job),
                'sequence': index * 10,
                'routing_id': routing.id,
                'workcenter_id': workcenters[area].id,
                'time_mode': 'manual',
                'time_cycle_manual': 0.0,
                'batch': 'no',
                'esi_operator_id': operators[operator_name].id if operator_name else False,
                'esi_area': area,
                'esi_standard_seconds': 0.0,
                'esi_piece_rate': 0.0,
                'esi_batch_qty': 50.0,
                'esi_measurement_status': 'pending',
                'esi_source_sheet': 'BOTA INDUSTRIAL',
                'esi_source_row': row,
                'esi_source_note': 'Planilla origen con tiempos incompletos/inconsistentes/#REF!: pendiente de medición, sin inventar valores.',
            }
            if not op:
                op = Operation.create(vals)
            else:
                op.write(vals)
            keep_ids.append(op.id)
        return Operation.browse(keep_ids)

    @api.model
    def _get_or_create_bom(self, env, company, product, routing, components, products, warehouse):
        Bom = env['mrp.bom'].sudo()
        bom = Bom.search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('company_id', '=', company.id),
            ('routing_id', '=', routing.id),
        ], limit=1)
        picking_type = env['stock.picking.type'].sudo().search([
            ('code', '=', 'mrp_operation'),
            ('warehouse_id', '=', warehouse.id),
            ('company_id', '=', company.id),
        ], limit=1)
        if not picking_type:
            picking_type = env['stock.picking.type'].sudo().search([
                ('code', '=', 'mrp_operation'), ('company_id', '=', company.id)
            ], limit=1)
        vals = {
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_id': product.id,
            'product_qty': 1.0,
            'product_uom_id': product.uom_id.id,
            'type': 'normal',
            'routing_id': routing.id,
            'company_id': company.id,
        }
        if picking_type:
            vals['picking_type_id'] = picking_type.id
        if not bom:
            bom = Bom.create(vals)
        else:
            bom.write({'routing_id': routing.id})

        for code, qty in components:
            component = products[code]
            line = env['mrp.bom.line'].sudo().search([
                ('bom_id', '=', bom.id), ('product_id', '=', component.id)
            ], limit=1)
            line_vals = {
                'bom_id': bom.id,
                'product_id': component.id,
                'product_qty': qty,
                'product_uom_id': component.uom_id.id,
            }
            if not line:
                env['mrp.bom.line'].sudo().create(line_vals)
            else:
                line.write({'product_qty': qty, 'product_uom_id': component.uom_id.id})
        return bom

    @api.model
    def _productive_loss(self, env):
        Loss = env['mrp.workcenter.productivity.loss'].sudo()
        loss = Loss.search([('loss_type', '=', 'productive')], limit=1)
        if loss:
            return loss
        LossType = env['mrp.workcenter.productivity.loss.type'].sudo()
        loss_type = LossType.search([('loss_type', '=', 'productive')], limit=1)
        if not loss_type:
            loss_type = LossType.create({'loss_type': 'productive'})
        vals = {'name': 'Tiempo Productivo ESI DEMO AVCO', 'loss_id': loss_type.id, 'manual': False}
        return Loss.create(vals)

    @api.model
    def _create_workorders(self, env, mo, operations, scenario='planned'):
        """Crear/completar las órdenes de trabajo de la OF demo.

        En Odoo 13 ``mrp.workorder`` hereda de ``mrp.abstract.workorder`` y
        exige, entre otros, ``product_uom_id`` y ``consumption``.  La versión
        inicial del demo construía las órdenes manualmente y omitía esos
        campos.  Esta versión intenta primero el flujo estándar ``button_plan``
        y, si la planificación de calendario no puede ejecutarse, usa
        ``_prepare_workorder_vals`` de Odoo como fallback compatible.
        """
        Workorder = env['mrp.workorder'].sudo()
        Productivity = env['mrp.workcenter.productivity'].sudo()
        qty = mo.product_qty

        # 1) Preferir siempre la generación estándar de Odoo 13.
        workorders = mo.workorder_ids
        if not workorders and mo.routing_id and mo.state == 'confirmed':
            try:
                with env.cr.savepoint():
                    mo.button_plan()
            except Exception:
                # Un calendario incompleto o una personalización de planificación
                # no debe impedir instalar la demo. El fallback de abajo conserva
                # todos los campos obligatorios de mrp.workorder.
                pass
            workorders = mo.workorder_ids

        # 2) Fallback seguro: usar el preparador nativo de Odoo 13.
        if not workorders:
            workorders = Workorder.browse()
            for op in operations:
                duration_expected = (op.esi_standard_seconds or 0.0) * qty / 60.0

                if hasattr(mo, '_prepare_workorder_vals'):
                    vals = mo._prepare_workorder_vals(op, workorders, qty)
                else:
                    # Respaldo defensivo para instalaciones 13 personalizadas.
                    vals = {
                        'name': op.name,
                        'production_id': mo.id,
                        'workcenter_id': op.workcenter_id.id,
                        'operation_id': op.id,
                        'product_uom_id': mo.product_uom_id.id or mo.product_id.uom_id.id,
                        'qty_producing': qty,
                        'consumption': mo.bom_id.consumption or 'flexible',
                        'state': not workorders and 'ready' or 'pending',
                    }

                # Campos explícitos para bases con extensiones multi-compañía y
                # para mantener los tiempos/destajos de la planilla ESI.
                vals.update({
                    'company_id': mo.company_id.id,
                    'product_uom_id': vals.get('product_uom_id') or mo.product_uom_id.id or mo.product_id.uom_id.id,
                    'consumption': vals.get('consumption') or mo.bom_id.consumption or 'flexible',
                    'qty_producing': vals.get('qty_producing') or qty,
                    'duration_expected': duration_expected,
                    'esi_operator_id': op.esi_operator_id.id,
                    'esi_area': op.esi_area,
                    'esi_standard_seconds': op.esi_standard_seconds,
                    'esi_piece_rate': op.esi_piece_rate,
                })
                wo = Workorder.create(vals)
                if workorders:
                    previous = workorders[-1]
                    previous.write({'next_work_order_id': wo.id})
                    try:
                        previous._start_nextworkorder()
                    except Exception:
                        pass
                workorders |= wo

        # Orden lógico según la secuencia de la operación, no según el ID.
        workorders = mo.workorder_ids.sorted(
            key=lambda wo: ((wo.operation_id.sequence if wo.operation_id else 999999), wo.id)
        ) or workorders

        # Si fueron creadas por el planificador estándar, los campos ESI son
        # computed/store desde operation_id. Solo completamos de forma defensiva
        # órdenes no finalizadas que provengan de personalizaciones antiguas.
        for wo in workorders.filtered(lambda w: w.state not in ('done', 'cancel')):
            op = wo.operation_id
            if not op:
                continue
            vals = {}
            if not wo.product_uom_id:
                vals['product_uom_id'] = mo.product_uom_id.id or mo.product_id.uom_id.id
            if not wo.consumption:
                vals['consumption'] = mo.bom_id.consumption or 'flexible'
            if not wo.qty_producing:
                vals['qty_producing'] = qty
            # Mantener los datos de la hoja incluso si otro módulo cambió el compute.
            vals.update({
                'esi_operator_id': op.esi_operator_id.id,
                'esi_area': op.esi_area,
                'esi_standard_seconds': op.esi_standard_seconds,
                'esi_piece_rate': op.esi_piece_rate,
            })
            if vals:
                wo.write(vals)

        if scenario not in ('completed', 'progress'):
            return workorders

        # 3) Partes de producción DEMO. Idempotentes por workorder + esi_source.
        loss = self._productive_loss(env)
        cursor = datetime.combine(fields.Date.context_today(self), time(7, 30)) - timedelta(
            days=3 if scenario == 'completed' else 1
        )
        progress_limit = 13 if scenario == 'progress' else len(workorders)

        for idx, wo in enumerate(workorders, 1):
            if idx > progress_limit:
                continue
            op = wo.operation_id
            if not op:
                continue

            full_qty = qty
            part_qty = full_qty if scenario == 'completed' or idx < progress_limit else max(1.0, full_qty / 2.0)
            minutes = (op.esi_standard_seconds or 0.0) * part_qty / 60.0
            date_start = cursor
            date_end = cursor + timedelta(minutes=minutes)
            prod_vals = {
                'workorder_id': wo.id,
                'workcenter_id': wo.workcenter_id.id,
                'company_id': mo.company_id.id,
                'loss_id': loss.id,
                'user_id': env.user.id,
                'date_start': date_start,
                'date_end': date_end,
                'description': 'Parte de producción ESI DEMO AVCO - %s' % (op.name or ''),
                'esi_operator_id': op.esi_operator_id.id,
                'esi_area': op.esi_area,
                'esi_qty_processed': part_qty,
                'esi_piece_rate': op.esi_piece_rate,
                'esi_source': 'demo',
            }
            timeline = Productivity.search([
                ('workorder_id', '=', wo.id),
                ('esi_source', '=', 'demo'),
            ], limit=1)
            if timeline:
                timeline.write(prod_vals)
            else:
                Productivity.create(prod_vals)

            target_state = 'done'
            if scenario == 'progress' and idx == progress_limit:
                target_state = 'progress'

            # No reescribir órdenes ya terminadas: Odoo 13 bloquea cambios
            # distintos de time_ids en workorders con state='done'.
            if wo.state not in ('done', 'cancel'):
                wo_vals = {
                    'qty_produced': part_qty,
                    'state': target_state,
                    'date_start': date_start,
                }
                if target_state == 'done':
                    wo_vals['date_finished'] = date_end
                wo.write(wo_vals)

            # Mantener coherentes las fechas planificadas con los tiempos demo.
            # Odoo 13 impide finalizar una WO si date_planned_finished queda
            # antes de date_planned_start. En una WO histórica/en progreso, la
            # reserva del centro de trabajo no debe permanecer en una fecha futura.
            if wo.leave_id:
                planned_end = date_end
                if target_state == 'progress':
                    planned_end = max(date_end, datetime.now())
                if planned_end < date_start:
                    planned_end = date_start
                wo.leave_id.sudo().write({
                    'date_from': date_start,
                    'date_to': planned_end,
                })
            cursor = date_end
        return workorders

    @api.model
    def _get_or_create_mo(self, env, company, warehouse, product, bom, operations, origin, qty, scenario, offset_days):
        Production = env['mrp.production'].sudo()
        mo = Production.search([('origin', '=', origin), ('company_id', '=', company.id)], limit=1)

        if not mo:
            picking_type = env['stock.picking.type'].sudo().search([
                ('code', '=', 'mrp_operation'), ('warehouse_id', '=', warehouse.id), ('company_id', '=', company.id)
            ], limit=1)
            if not picking_type:
                picking_type = env['stock.picking.type'].sudo().search([
                    ('code', '=', 'mrp_operation'), ('company_id', '=', company.id)
                ], limit=1)
            planned = fields.Datetime.now() + timedelta(days=offset_days)
            vals = {
                'origin': origin,
                'product_id': product.id,
                'product_qty': qty,
                'product_uom_id': product.uom_id.id,
                'bom_id': bom.id,
                'company_id': company.id,
                'date_planned_start': planned,
                'date_start_wo': planned,
                'location_src_id': warehouse.lot_stock_id.id,
                'location_dest_id': warehouse.lot_stock_id.id,
            }
            if picking_type:
                vals['picking_type_id'] = picking_type.id
            mo = Production.with_context(import_file=True).create(vals)

        # Confirmar dentro de savepoint evita dejar la transacción PostgreSQL
        # abortada si una personalización impide la confirmación.
        if mo.state == 'draft':
            try:
                with env.cr.savepoint():
                    mo.action_confirm()
            except Exception:
                pass

        # Reservar materiales si es posible, sin hacer obligatoria la existencia
        # física de todo el stock para poder instalar una base de demostración.
        if mo.state not in ('draft', 'done', 'cancel'):
            try:
                with env.cr.savepoint():
                    mo.action_assign()
            except Exception:
                pass

        self._create_workorders(env, mo, operations, scenario=scenario)

        if scenario == 'completed' and mo.state not in ('done', 'cancel'):
            # Toda la simulación de cierre va dentro del savepoint. Si otra
            # personalización la rechaza, queda una OF demostrativa utilizable
            # sin contaminar la transacción de instalación.
            try:
                with env.cr.savepoint():
                    for move in mo.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                        move.quantity_done = move.product_uom_qty
                    for move in mo.move_finished_ids.filtered(
                            lambda m: m.product_id == product and m.state not in ('done', 'cancel')):
                        move.quantity_done = qty
                    mo.button_mark_done()
            except Exception:
                pass
        return mo

    @api.model
    def _create_piecework_notes(self, env, company):
        """Carga los tres apuntes adicionales de destajo de la hoja BOTA DE LONA.

        La planilla no identifica una OF para estos renglones; por fidelidad se
        guardan sin production_id y con su fila de origen.
        """
        Note = env['esi.mrp.piecework.note'].sudo()
        records = Note.browse()
        today = fields.Date.context_today(self)
        for row, name, area, quantity, rate in EXTRA_PIECEWORK_NOTES:
            note = Note.search([
                ('company_id', '=', company.id),
                ('source_sheet', '=', 'BOTA DE LONA'),
                ('source_row', '=', row),
            ], limit=1)
            vals = {
                'name': name,
                'date': today,
                'company_id': company.id,
                'area': area,
                'quantity': quantity,
                'rate': rate,
                'source_sheet': 'BOTA DE LONA',
                'source_row': row,
                'source_note': (
                    'Apunte adicional de CALCULO DE TIEMPOS Y COSTOS DE DESTAJO.xlsx. '
                    'La hoja no identifica una orden de fabricación concreta, por eso '
                    'se conserva sin vínculo forzado a una OF.'
                ),
            }
            if note:
                note.write(vals)
            else:
                note = Note.create(vals)
            records |= note
        return records

    @api.model
    def _get_or_create_partners(self, env, company):
        Partner = env['res.partner'].sudo()
        defs = [
            ('PROV-CUERO', 'Curtiembre Oriente DEMO', 'supplier'),
            ('PROV-INS', 'Insumos Calzados Bolivia DEMO', 'supplier'),
            ('CLI-MAY', 'Distribuidora Paso Firme DEMO', 'customer'),
            ('CLI-SEG', 'Seguridad Industrial Andina DEMO', 'customer'),
        ]
        result = {}
        for ref, name, kind in defs:
            partner = Partner.search([('ref', '=', ref), ('company_id', '=', company.id)], limit=1)
            vals = {
                'name': name,
                'ref': ref,
                'company_type': 'company',
                'company_id': company.id,
            }
            if 'supplier_rank' in Partner._fields:
                vals['supplier_rank'] = 1 if kind == 'supplier' else 0
            if 'customer_rank' in Partner._fields:
                vals['customer_rank'] = 1 if kind == 'customer' else 0
            if not partner:
                partner = Partner.create(vals)
            result[ref] = partner
        return result

    @api.model
    def _get_or_create_pricelist(self, env, company):
        Pricelist = env['product.pricelist'].sudo()
        pl = Pricelist.search([('name', '=', 'Tarifa ESI DEMO AVCO Bs'), ('company_id', '=', company.id)], limit=1)
        if not pl:
            pl = Pricelist.create({
                'name': 'Tarifa ESI DEMO AVCO Bs',
                'currency_id': company.currency_id.id,
                'company_id': company.id,
            })
        return pl

    @api.model
    def _receive_purchase(self, env, po):
        """Valida completamente las recepciones abiertas de una OC.

        En Odoo 13 el AVCO cambia cuando el movimiento de entrada queda DONE,
        no simplemente al confirmar la orden de compra.
        """
        done_count = 0
        for picking in po.picking_ids.filtered(lambda p: p.state not in ('done', 'cancel')):
            if picking.state == 'draft':
                picking.action_confirm()
            # En recepciones de proveedor no hace falta reservar stock. Al
            # asignar quantity_done Odoo crea/actualiza las líneas necesarias.
            for move in picking.move_lines.filtered(lambda m: m.state not in ('done', 'cancel')):
                move.quantity_done = move.product_uom_qty
            picking.with_context(skip_overprocessed_check=True).button_validate()
            if picking.state == 'done':
                done_count += 1
        return done_count

    @api.model
    def _create_purchases(self, env, company, warehouse, partners, products):
        Purchase = env['purchase.order'].sudo()

        # Dos recepciones completas forman el promedio inicial.
        # Lote 1: 60% de la cantidad objetivo al 90% del costo de referencia.
        # Lote 2: 40% de la cantidad objetivo al 120% del costo de referencia.
        # Resultado teórico antes de consumos: 102% del costo de referencia,
        # claramente diferente de ambos precios de compra.
        lot1 = []
        lot2 = []
        for code, _name, ref_cost, stock_target, _uom_key in RAW_PRODUCTS:
            lot1.append((code, stock_target * 0.60, ref_cost * 0.90))
            lot2.append((code, stock_target * 0.40, ref_cost * 1.20))

        # Tercera compra confirmada pero NO recibida: sirve para demostrar en
        # vivo cómo vuelve a cambiar AVCO al validar la recepción.
        pending = []
        for code in ('MP-CUERO', 'MP-LONA', 'MP-SUELA'):
            ref = next(x for x in RAW_PRODUCTS if x[0] == code)
            pending.append((code, max(10.0, ref[3] * 0.20), ref[2] * 1.30))

        defs = [
            ('ESI-AVCO-COMPRA-001-RECIBIDA', partners['PROV-CUERO'], lot1, True, True, 14),
            ('ESI-AVCO-COMPRA-002-RECIBIDA', partners['PROV-INS'], lot2, True, True, 10),
            ('ESI-AVCO-COMPRA-003-PENDIENTE', partners['PROV-CUERO'], pending, True, False, 1),
        ]
        orders = Purchase.browse()
        received_pickings = 0
        incoming = env['stock.picking.type'].sudo().search([
            ('code', '=', 'incoming'), ('warehouse_id', '=', warehouse.id), ('company_id', '=', company.id)
        ], limit=1)
        for ref, partner, lines, confirm, receive, days_ago in defs:
            po = Purchase.search([('partner_ref', '=', ref), ('company_id', '=', company.id)], limit=1)
            if not po:
                vals = {
                    'partner_id': partner.id,
                    'company_id': company.id,
                    'partner_ref': ref,
                    'date_order': fields.Datetime.now() - timedelta(days=days_ago),
                    'order_line': [(0, 0, {
                        'name': products[code].display_name,
                        'product_id': products[code].id,
                        'product_qty': qty,
                        'product_uom': products[code].uom_po_id.id,
                        'price_unit': price,
                        'date_planned': fields.Datetime.now() - timedelta(days=max(days_ago - 1, 0)),
                    }) for code, qty, price in lines],
                }
                if incoming:
                    vals['picking_type_id'] = incoming.id
                po = Purchase.create(vals)

            if confirm and po.state in ('draft', 'sent'):
                po.button_confirm()
            if receive:
                received_pickings += self._receive_purchase(env, po)
            orders |= po
        return orders, received_pickings

    @api.model
    def _create_sales(self, env, company, warehouse, partners, products, pricelist):
        Sale = env['sale.order'].sudo()
        defs = [
            ('ESI-AVCO-VENTA-001', partners['CLI-MAY'], [('PT-BOTA-LONA', 30.0, 185.0)], True),
            ('ESI-AVCO-VENTA-002', partners['CLI-SEG'], [('PT-BOTA-IND', 12.0, 260.0)], False),
        ]
        orders = Sale.browse()
        for ref, partner, lines, confirm in defs:
            so = Sale.search([('client_order_ref', '=', ref), ('company_id', '=', company.id)], limit=1)
            if not so:
                so = Sale.create({
                    'partner_id': partner.id,
                    'company_id': company.id,
                    'warehouse_id': warehouse.id,
                    'pricelist_id': pricelist.id,
                    'client_order_ref': ref,
                    'date_order': fields.Datetime.now() - timedelta(days=5 if confirm else 1),
                    'order_line': [(0, 0, {
                        'name': products[code].display_name,
                        'product_id': products[code].id,
                        'product_uom_qty': qty,
                        'product_uom': products[code].uom_id.id,
                        'price_unit': price,
                    }) for code, qty, price in lines],
                })
                if confirm:
                    try:
                        with env.cr.savepoint():
                            so.action_confirm()
                    except Exception:
                        pass
            orders |= so
        return orders

    @api.model
    def _account_type(self, env, xmlid, domain):
        rec = env.ref(xmlid, raise_if_not_found=False)
        if rec:
            return rec
        return env['account.account.type'].sudo().search(domain, limit=1)

    @api.model
    def _create_chart(self, env, company):
        types = {
            'receivable': self._account_type(env, 'account.data_account_type_receivable', [('type', '=', 'receivable')]),
            'payable': self._account_type(env, 'account.data_account_type_payable', [('type', '=', 'payable')]),
            'liquidity': self._account_type(env, 'account.data_account_type_liquidity', [('type', '=', 'liquidity')]),
            'asset': self._account_type(env, 'account.data_account_type_current_assets', [('internal_group', '=', 'asset')]),
            'liability': self._account_type(env, 'account.data_account_type_current_liabilities', [('internal_group', '=', 'liability')]),
            'equity': self._account_type(env, 'account.data_account_type_equity', [('internal_group', '=', 'equity')]),
            'income': self._account_type(env, 'account.data_account_type_revenue', [('internal_group', '=', 'income')]),
            'cost': self._account_type(env, 'account.data_account_type_direct_costs', [('internal_group', '=', 'expense')]),
            'expense': self._account_type(env, 'account.data_account_type_expenses', [('internal_group', '=', 'expense')]),
        }
        # Fallbacks para localizaciones que renombren/eliminaran tipos genéricos.
        any_type = env['account.account.type'].sudo().search([], limit=1)
        for key in types:
            types[key] = types[key] or any_type

        definitions = [
            ('110101', 'Caja General ESI DEMO', 'liquidity', False),
            ('110102', 'Banco BNB ESI DEMO', 'liquidity', False),
            ('110201', 'Cuentas por Cobrar Clientes', 'receivable', True),
            ('110301', 'Inventario Materia Prima', 'asset', False),
            ('110302', 'Producción en Proceso', 'asset', False),
            ('110303', 'Inventario Producto Terminado', 'asset', False),
            ('110401', 'IVA Crédito Fiscal', 'asset', False),
            ('110501', 'Anticipos a Proveedores', 'asset', False),
            ('210101', 'Cuentas por Pagar Proveedores', 'payable', True),
            ('210201', 'Sueldos y Destajos por Pagar', 'liability', False),
            ('210301', 'IVA Débito Fiscal', 'liability', False),
            ('210401', 'Aportes y Retenciones por Pagar', 'liability', False),
            ('310101', 'Capital Social', 'equity', False),
            ('320101', 'Resultados Acumulados', 'equity', False),
            ('410101', 'Ventas Bota de Lona', 'income', False),
            ('410102', 'Ventas Bota Industrial', 'income', False),
            ('419001', 'Otros Ingresos', 'income', False),
            ('510101', 'Consumo Materia Prima', 'cost', False),
            ('510102', 'Mano de Obra Directa - Destajo', 'cost', False),
            ('510103', 'Costos Indirectos de Fabricación', 'cost', False),
            ('510104', 'Variación de Producción', 'cost', False),
            ('520101', 'Costo de Ventas - Bota Lona', 'cost', False),
            ('520102', 'Costo de Ventas - Bota Industrial', 'cost', False),
            ('610101', 'Sueldos Administración', 'expense', False),
            ('610201', 'Servicios Básicos', 'expense', False),
            ('610301', 'Mantenimiento Maquinaria', 'expense', False),
            ('610401', 'Transporte y Distribución', 'expense', False),
            ('610501', 'Gastos Bancarios', 'expense', False),
        ]
        Account = env['account.account'].sudo()
        accounts = {}
        for code, name, type_key, reconcile in definitions:
            acc = Account.search([('code', '=', code), ('company_id', '=', company.id)], limit=1)
            vals = {
                'name': name,
                'code': code,
                'user_type_id': types[type_key].id,
                'company_id': company.id,
                'reconcile': reconcile,
            }
            if not acc:
                acc = Account.create(vals)
            else:
                acc.write({'name': name, 'user_type_id': types[type_key].id, 'reconcile': reconcile})
            accounts[code] = acc
        return accounts

    @api.model
    def _configure_demo_category_accounts(self, categories, accounts):
        raw, finished = categories
        for category in (raw, finished):
            vals = {}
            if 'property_account_income_categ_id' in category._fields:
                vals['property_account_income_categ_id'] = accounts['410101'].id
            if 'property_account_expense_categ_id' in category._fields:
                vals['property_account_expense_categ_id'] = accounts['510101'].id
            if vals:
                category.sudo().write(vals)

    @api.model
    def _create_journals(self, env, company, accounts):
        Journal = env['account.journal'].sudo()
        defs = [
            ('AVG', 'Diario General ESI DEMO AVCO', 'general', False),
            ('AVP', 'Producción ESI DEMO AVCO', 'general', False),
            ('AVS', 'Ventas ESI DEMO AVCO', 'sale', False),
            ('AVC', 'Compras ESI DEMO AVCO', 'purchase', False),
            ('AVB', 'Banco ESI DEMO AVCO', 'bank', accounts['110102']),
        ]
        result = {}
        for code, name, jtype, default_account in defs:
            journal = Journal.search([('code', '=', code), ('company_id', '=', company.id)], limit=1)
            vals = {'name': name, 'code': code, 'type': jtype, 'company_id': company.id}
            if default_account:
                if 'default_debit_account_id' in Journal._fields:
                    vals['default_debit_account_id'] = default_account.id
                    vals['default_credit_account_id'] = default_account.id
                elif 'default_account_id' in Journal._fields:
                    vals['default_account_id'] = default_account.id
            if not journal:
                journal = Journal.create(vals)
            result[code] = journal
        return result

    @api.model
    def _create_account_moves(self, env, company, accounts, journals, partners):
        Move = env['account.move'].sudo()
        today = fields.Date.context_today(self)
        entries = [
            ('ESI-AVCO-APERTURA', journals['AVG'], today - timedelta(days=30), [
                ('Capital inicial - Banco', '110102', 70000.0, 0.0, False),
                ('Capital inicial - Inventario MP', '110301', 30000.0, 0.0, False),
                ('Capital Social', '310101', 0.0, 100000.0, False),
            ]),
            ('ESI-AVCO-COMPRA-CONTABLE', journals['AVC'], today - timedelta(days=12), [
                ('Compra materias primas', '110301', 8700.0, 0.0, False),
                ('IVA Crédito Fiscal', '110401', 1131.0, 0.0, False),
                ('Proveedor por pagar', '210101', 0.0, 9831.0, partners['PROV-CUERO']),
            ]),
            ('ESI-AVCO-VENTA-CONTABLE', journals['AVS'], today - timedelta(days=6), [
                ('Cliente por cobrar', '110201', 16950.0, 0.0, partners['CLI-MAY']),
                ('Venta Bota de Lona', '410101', 0.0, 15000.0, False),
                ('IVA Débito Fiscal', '210301', 0.0, 1950.0, False),
            ]),
            ('ESI-AVCO-COSTO-VENTA', journals['AVP'], today - timedelta(days=6), [
                ('Costo de venta Bota de Lona', '520101', 7500.0, 0.0, False),
                ('Salida producto terminado', '110303', 0.0, 7500.0, False),
            ]),
            ('ESI-AVCO-DESTAJO-50P', journals['AVP'], today - timedelta(days=3), [
                ('Destajo serie 50 pares Bota de Lona (27 Bs/par)', '510102', 1350.0, 0.0, False),
                ('Destajos por pagar', '210201', 0.0, 1350.0, False),
            ]),
            ('ESI-AVCO-SERVICIOS', journals['AVG'], today - timedelta(days=4), [
                ('Servicios básicos fábrica', '610201', 950.0, 0.0, False),
                ('Pago desde banco', '110102', 0.0, 950.0, False),
            ]),
            ('ESI-AVCO-PAGO-PROVEEDOR', journals['AVG'], today - timedelta(days=2), [
                ('Pago parcial proveedor', '210101', 5000.0, 0.0, partners['PROV-CUERO']),
                ('Banco', '110102', 0.0, 5000.0, False),
            ]),
            ('ESI-AVCO-COBRO-CLIENTE', journals['AVG'], today - timedelta(days=1), [
                ('Banco', '110102', 8000.0, 0.0, False),
                ('Cobro parcial cliente', '110201', 0.0, 8000.0, partners['CLI-MAY']),
            ]),
        ]
        moves = Move.browse()
        for ref, journal, date, lines in entries:
            move = Move.search([('ref', '=', ref), ('company_id', '=', company.id)], limit=1)
            if not move:
                move_vals = {
                    'ref': ref,
                    'date': date,
                    'journal_id': journal.id,
                    'company_id': company.id,
                    'line_ids': [(0, 0, {
                        'name': label,
                        'account_id': accounts[code].id,
                        'debit': debit,
                        'credit': credit,
                        'partner_id': partner.id if partner else False,
                    }) for label, code, debit, credit, partner in lines],
                }
                if 'type' in Move._fields:
                    move_vals['type'] = 'entry'
                move = Move.create(move_vals)
                try:
                    with env.cr.savepoint():
                        move.action_post()
                except Exception:
                    pass
            moves |= move
        return moves

    @api.model
    def run_demo(self):
        company = self._get_or_create_company()
        env = self._company_env(company)

        warehouse = self._get_or_create_warehouse(env, company)
        uoms = self._get_uoms(env)
        categories = self._get_or_create_categories(env)
        products = self._get_or_create_products(env, company, uoms, categories)

        # En AVCO el inventario de MP nace de compras reales. Primero creamos
        # proveedores, confirmamos dos OC y validamos sus recepciones.
        partners = self._get_or_create_partners(env, company)
        pricelist = self._get_or_create_pricelist(env, company)
        purchases, received_pickings = self._create_purchases(env, company, warehouse, partners, products)

        operators = self._get_or_create_operators(env, company)
        workcenters = self._get_or_create_workcenters(env, company)

        routing_lona = self._get_or_create_routing(env, company, 'Ruta Bota de Lona - ESI DEMO AVCO', 'AVCO-LONA')
        routing_ind = self._get_or_create_routing(env, company, 'Ruta Bota Industrial - ESI DEMO AVCO', 'AVCO-IND')
        lona_ops = self._load_lona_operations(env, routing_lona, workcenters, operators)
        industrial_ops = self._load_industrial_operations(env, routing_ind, workcenters, operators)
        piecework_notes = self._create_piecework_notes(env, company)

        bom_lona = self._get_or_create_bom(env, company, products['PT-BOTA-LONA'], routing_lona, BOM_LONA, products, warehouse)
        bom_ind = self._get_or_create_bom(env, company, products['PT-BOTA-IND'], routing_ind, BOM_INDUSTRIAL, products, warehouse)

        mos = env['mrp.production'].sudo().browse()
        mos |= self._get_or_create_mo(env, company, warehouse, products['PT-BOTA-LONA'], bom_lona, lona_ops, 'ESI-AVCO-MRP-001-LOTE-50', 50.0, 'completed', -3)
        mos |= self._get_or_create_mo(env, company, warehouse, products['PT-BOTA-LONA'], bom_lona, lona_ops, 'ESI-AVCO-MRP-002-EN-PROCESO', 20.0, 'progress', -1)
        mos |= self._get_or_create_mo(env, company, warehouse, products['PT-BOTA-LONA'], bom_lona, lona_ops, 'ESI-AVCO-MRP-003-PLANIFICADA', 30.0, 'planned', 2)
        mos |= self._get_or_create_mo(env, company, warehouse, products['PT-BOTA-IND'], bom_ind, industrial_ops, 'ESI-AVCO-MRP-004-INDUSTRIAL', 20.0, 'planned', 4)

        sales = self._create_sales(env, company, warehouse, partners, products, pricelist)

        accounts = self._create_chart(env, company)
        self._configure_demo_category_accounts(categories, accounts)
        journals = self._create_journals(env, company, accounts)
        account_moves = self._create_account_moves(env, company, accounts, journals, partners)

        samples = []
        for code in ('MP-CUERO', 'MP-LONA', 'MP-SUELA'):
            product = products[code].with_context(force_company=company.id)
            samples.append('%s = Bs %.4f' % (product.default_code, product.standard_price))

        return {
            'company_id': company.id,
            'company_name': company.display_name,
            'operators': len(operators),
            'workcenters': len(workcenters),
            'lona_operations': len(lona_ops),
            'industrial_operations': len(industrial_ops),
            'piecework_notes': len(piecework_notes),
            'piecework_notes_total': sum(piecework_notes.mapped('amount')),
            'products': len(products),
            'manufacturing_orders': len(mos),
            'purchase_orders': len(purchases),
            'received_pickings': received_pickings,
            'sale_orders': len(sales),
            'account_moves': len(account_moves),
            'cost_method': categories[0].with_context(force_company=company.id).property_cost_method,
            'avco_samples': samples,
        }
