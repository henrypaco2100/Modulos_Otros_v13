# ESI Demo Insumos — Odoo 13 Community

Módulo instalable construido a partir de `Libro(4).xlsx`.

## Qué crea automáticamente

- 15 productos stockables con sus imágenes originales del Excel.
- 3 categorías: Limpieza, Embalaje y Seguridad.
- Método de coste **Promedio (AVCO)** en las tres categorías.
- 1 proveedor ficticio.
- 4 clientes ficticios.
- 36 cuentas contables del plan básico entregado en el Excel.
- Orden de compra `DEMO-OC-001`: 865 unidades por Bs 13.555.
- Recepción completa de la compra.
- Factura de proveedor por Bs 13.555 y pago al contado.
- 4 órdenes de venta por Bs 7.900 en total.
- Entregas completas de las 4 ventas.
- Facturas de cliente y pagos según el escenario del Excel.
- Cobrado: Bs 4.960.
- Saldo por cobrar: Bs 2.940.
- Asiento manual de costo de ventas por Bs 5.091.
- Inventario final físico luego de las ventas: 542 unidades.

## Flujo de la demo

1. **Contactos**: revisar proveedor y cuatro clientes.
2. **Compras**: abrir `DEMO-OC-001`, factura y recepción.
3. **Inventario**: revisar existencias de los 15 productos.
4. **Ventas**: revisar `DEMO-V-001` a `DEMO-V-004`.
5. **Facturación/Contabilidad**: revisar facturas, pagos, saldos y el asiento `DEMO-COGS-001`.

## Totales esperados

| Concepto | Total |
|---|---:|
| Compra inicial | Bs 13.555 |
| Ventas | Bs 7.900 |
| Cobrado clientes | Bs 4.960 |
| Por cobrar | Bs 2.940 |
| Costo de ventas | Bs 5.091 |
| Margen bruto | Bs 2.809 |
| Inventario final valorizado al costo | Bs 8.464 |

## Importante

- Está pensado para una **base de datos de demostración** de Odoo 13 Community.
- Las cantidades de “Stock inicial” del Excel son las mismas cantidades de la compra inicial; por eso no se duplican. El stock entra mediante la recepción de `DEMO-OC-001`.
- La valoración de inventario se deja en **Manual periódica**, pero con costo **Promedio**, para evitar exigir cuentas puente de valoración automática no incluidas en el plan básico del Excel. El costo de ventas se registra con un asiento demo separado.
- Los productos no usan impuestos para que los importes sean exactamente los del Excel.
- Antes de presentar la demo, se recomienda que la moneda de la compañía sea BOB/Bs.

## Instalación

1. Copiar la carpeta `esi_demo_insumos_v13` dentro del directorio de addons personalizados.
2. Reiniciar Odoo 13.
3. Activar modo desarrollador y actualizar la lista de aplicaciones.
4. Buscar **ESI Demo Insumos**.
5. Instalar.

Al terminar la instalación, todos los datos y operaciones ya estarán generados.
