# ESI Demo Calzado AVCO - Odoo 13

Demo independiente basada en la demo de producción de calzado ESI, con método de coste **Promedio (AVCO)**.

## Diferencias principales
- Compañía: **Calzados ESI DEMO PROMEDIO S.R.L.**
- Categorías separadas para no modificar la demo original.
- `property_cost_method = average` en materias primas y productos terminados.
- Productos con código `AVCO-*`.
- No se inyecta stock inicial de materias primas por `stock.quant`.
- Compra 001: 60% de la cantidad objetivo al 90% del costo de referencia, recibida.
- Compra 002: 40% de la cantidad objetivo al 120% del costo de referencia, recibida.
- Compra 003: CUERO, LONA y SUELA al 130%, confirmada pero pendiente de recepción para demostrar el recálculo AVCO en vivo.
- Después de las dos primeras recepciones, el costo teórico de cada MP es 102% del costo de referencia (antes de redondeos).

## Flujo sugerido para la demostración
1. Cambiar a la compañía **Calzados ESI DEMO PROMEDIO S.R.L.**.
2. Ir a Inventario > Configuración > Categorías de producto y verificar **Costo Promedio (AVCO)**.
3. Abrir `AVCO-MP-CUERO`, `AVCO-MP-LONA` o `AVCO-MP-SUELA` y anotar el costo.
4. Abrir la compra `ESI-AVCO-COMPRA-003-PENDIENTE`.
5. Abrir su recepción y validar todas las cantidades.
6. Volver al producto: Odoo habrá recalculado el costo promedio con la nueva entrada.

La lógica de producción, destajo, rutas, centros de trabajo, órdenes de fabricación, ventas y contabilidad permanece equivalente a la demo original.
