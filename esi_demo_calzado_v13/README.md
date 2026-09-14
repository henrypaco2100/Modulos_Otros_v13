# ESI - Demo Calzado Odoo 13

Módulo técnico: `esi_demo_calzado_v13`.

Instalar este módulo carga una demo integral en una compañía separada llamada **Calzados ESI DEMO S.R.L.**. No requiere crear una base nueva ni activar el checkbox de datos de demostración.

## Datos creados
- Plan contable demostrativo enfocado en fabricación de calzado.
- Diarios de operaciones generales, producción, ventas, compras y banco.
- 8 asientos contables demostrativos, incluidos apertura, compra, venta, costo de ventas, destajo, servicios, pago a proveedor y cobro a cliente.
- Clientes y proveedores DEMO.
- Materias primas, productos terminados e inventario inicial.
- 2 compras y 2 ventas.
- 6 centros de trabajo: Cortado, Aparado, Conformado, Solado, Terminado y Plantas.
- 11 operadores.
- Ruta **Bota de Lona** con 59 operaciones tomadas de la hoja de cálculo.
- Ruta **Bota Industrial** con las 19 operaciones cuyo nombre es legible; sus tiempos quedan pendientes porque la hoja contiene datos incompletos/inconsistentes/#REF!.
- 4 órdenes de fabricación de ejemplo: lote de 50 pares, lote en proceso, lote planificado y bota industrial.
- Partes de producción/destajo para los escenarios realizados.
- 3 apuntes adicionales de destajo de las filas 67-69 de `BOTA DE LONA`, total Bs 121.

## Fidelidad vs. datos demostrativos
Los **procesos, operadores, tiempos y tarifas de destajo de Bota de Lona** provienen de la planilla. Los clientes, proveedores, precios de venta, existencias iniciales y cantidades de la LdM no aparecen en esa planilla; se han creado como datos DEMO para poder mostrar el circuito completo y están identificados como tales.

La hoja `BOTA INDUSTRIAL` está incompleta. No se inventaron tiempos dañados o faltantes; se cargan como **Pendiente de medición**.

## Recarga / actualización
La carga es idempotente: busca registros por códigos/referencias y por hoja/fila para evitar duplicados. Puede ejecutarse otra vez desde:

**Fabricación > Configuración > Cargar Demo Calzado ESI**

## Importante sobre contabilidad
El plan contable incluido es demostrativo y útil para capacitación/venta de la solución. **No sustituye una localización contable/fiscal boliviana ni debe usarse como configuración legal de una empresa en producción sin revisión contable.**


## Corrección 13.0.1.1.1
- Corrige instalación en Odoo 13 cuando `mrp.workorder.product_uom_id` quedaba NULL.
- Las órdenes de trabajo usan primero `mrp.production.button_plan()` y, como fallback, `_prepare_workorder_vals()` estándar de Odoo 13.
- Se informan explícitamente `product_uom_id`, `qty_producing` y `consumption`.
- Confirmación, reserva, planificación y cierre usan savepoints para no dejar la transacción abortada ante personalizaciones de terceros.
- La creación de partes ESI DEMO es idempotente y no duplica líneas al recargar la demo.
