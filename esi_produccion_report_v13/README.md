# ESI Producción Report v13

Actualización orientada a `esi_calzados_v13`.

## Reportes en Orden de Fabricación > Imprimir
1. **ESI - Ficha de costo de producción**
   - Cantidad requerida por unidad.
   - Cantidad total.
   - Costo unitario capturado.
   - Costo material por unidad.
   - Costo estimado total.
   - Cantidad y costo real cuando existen capas de valoración.
   - Destajos y valoración automática del producto terminado.

2. **ESI - Faltantes de materiales y costo**
   - Requerido, disponible, faltante.
   - Proveedor sugerido.
   - Precio estimado de compra.
   - Costo total faltante.

3. **ESI - Resumen de destajos**
   - Resumen por trabajador: registros, cantidad y total destajo.
   - Detalle: fecha, operador, actividad, cantidad, tarifa, importe y estado.

## Reporte global de destajos
Fabricación > Informes > **Reporte de Destajos** permite filtrar por fechas, OF, producto, operador y estado.

## Corrección de costo
La versión usa primero los campos de costo capturados por `esi_calzados_v13` y, cuando la OF ya está valorizada, toma el valor real de `stock.valuation.layer`. Esto evita el problema anterior de reportes que mostraban costo en cero aun existiendo valoración.
