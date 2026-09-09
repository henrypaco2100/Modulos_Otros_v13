# ESI - Informes de Ventas v13

Versión 13.0.2.0.0

- Funciona de forma independiente con `sale_management`.
- Detecta automáticamente `store_id` (Sucursal) si está instalado el módulo Multi Store.
- Detecta automáticamente `work_process_order_id` (Tipo de Venta) si está instalado el módulo de tipos ESI.
- Wizard por rango, día, mes o año.
- Vista previa HTML, PDF y Excel en todos los análisis.

## Tipos de análisis

1. **Resumen de Ventas**
   - Agrupa por producto, vendedor/comercial, cliente, mes y, cuando existen, sucursal y tipo de venta.
   - Columnas base: Producto, UDM, Cantidad, Total Venta.
   - En modo administrador: Costo estimado y Margen aproximado.

2. **Ranking / Pareto Comercial**
   - Ranking por producto, cliente, vendedor/comercial y, cuando existen, sucursal y tipo de venta.
   - Top configurable (0 = todos).
   - Pedidos, cantidad, venta, ticket promedio, participación, acumulado y clasificación ABC.
   - En modo administrador: costo, margen y margen % aproximado.

3. **Evolución y Tendencia de Ventas**
   - Agrupación automática por día, semana o mes, o selección manual.
   - Compara cada período con el anterior.
   - Pedidos, cantidad, venta, ticket promedio, variación monetaria y variación %.
   - En modo administrador: margen aproximado y margen %.

4. **Precios, Descuentos y Margen por Producto**
   - Precio promedio neto, mínimo y máximo normalizado a la UDM base.
   - Descuento promedio estimado y descuento monetario estimado.
   - Total vendido.
   - En modo administrador: costo unitario estimado, margen unitario, margen total y margen %.

## Seguridad

- El menú `Informes de Ventas` respeta los accesos normales del usuario sobre `sale.order`.
- `Análisis de Ventas (Admin)` está restringido a `base.group_system`.
- El margen administrativo se calcula sobre ingreso sin impuestos contra costo estándar actual; por eso se identifica como aproximado.
