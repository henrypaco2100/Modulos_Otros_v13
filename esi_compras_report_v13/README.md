# ESI - Informes de Compras v13

Versión 13.0.2.0.0

- Funciona de forma independiente con `purchase`.
- Detecta automáticamente `store_id` (Sucursal) si está instalado Multi Store.
- Detecta automáticamente `work_process_order_id` (Tipo de Compra) si está instalado el módulo de tipos ESI.
- Wizard por rango, día, mes o año.
- Vista previa HTML, PDF y Excel en todos los análisis.
- Los importes de distintas monedas se convierten a la moneda de la compañía usando la fecha de la orden.

## Tipos de análisis

1. **Resumen de Compras**
   - Agrupa por producto, comprador/responsable, proveedor, mes y, cuando existen, sucursal y tipo de compra.
   - Columnas: Producto, UDM, Cantidad y Total Compra.

2. **Ranking / Concentración de Compras**
   - Ranking por proveedor, producto, comprador/responsable y, cuando existen, sucursal y tipo de compra.
   - Top configurable (0 = todos).
   - Órdenes, cantidad, compra total, compra promedio, participación, acumulado y clasificación ABC.
   - Útil para detectar concentración y dependencia de proveedores/productos.

3. **Evolución y Tendencia de Compras**
   - Agrupación automática por día, semana o mes, o selección manual.
   - Compara cada período con el anterior.
   - Órdenes, cantidad, compra total, compra promedio, variación monetaria y variación %.

4. **Variación de Precio por Producto**
   - Precio promedio, mínimo, máximo y último precio de compra, normalizados a la UDM base.
   - Rango de precio %, último precio vs promedio %, cantidad de proveedores, último proveedor y última fecha.
   - Total comprado por producto.

## Corrección 13.0.2.1.0
- Corregido error `ValueError: unsupported format character ';'` al usar **Ver** en el informe estándar de compras.
- La causa era el `width:100%` de CSS dentro de una cadena formateada con el operador `%` de Python.
