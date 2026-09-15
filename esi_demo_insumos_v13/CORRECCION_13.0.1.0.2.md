# Corrección 13.0.1.0.2

## Error corregido

Odoo 13 mostraba:

> El tipo de cuenta de crédito / débito predeterminada del diario no debe ser "por cobrar" o "por pagar".

La causa estaba en la creación de los diarios contables de la demo:

- `DSAL - DEMO Ventas` usaba `112001 - Cuentas por cobrar a clientes` como cuenta predeterminada.
- `DPUR - DEMO Compras` usaba `211001 - Proveedores de mercaderías por pagar` como cuenta predeterminada.

En Odoo 13 esas cuentas no pueden ser cuentas predeterminadas débito/crédito de un diario de ventas/compras. Las cuentas por cobrar y por pagar corresponden al partner y Odoo las utiliza como contrapartida en facturas.

## Solución aplicada

- `DSAL - DEMO Ventas` usa `411001 - Ventas de insumos de limpieza` como cuenta predeterminada válida.
- `DPUR - DEMO Compras` usa `511001 - Costo de ventas de limpieza` como cuenta predeterminada válida.
- `112001` continúa asignada como cuenta por cobrar de los clientes demo.
- `211001` continúa asignada como cuenta por pagar del proveedor demo.
- `_journal()` ahora valida defensivamente el tipo interno de las cuentas y nunca asigna `receivable` / `payable` como cuenta predeterminada de un diario.
- Si encuentra un diario DEMO existente con una cuenta predeterminada inválida, intenta sanearla de forma segura.

## Versión

`13.0.1.0.2`
