# Hemodiálisis - Demo Clínico para Odoo

Prototipo de prueba basado en los requerimientos de la reunión NIMBO: hoja de sesión de hemodiálisis con bloques pre, intra y post, matriz repetitiva y checklist de insumos.

## Objetivo técnico

- Odoo 13.0 (las vistas de lista usan `<tree>` y las condiciones dinámicas usan `attrs`).
- Dependencias: `base`, `product`.
- No mueve inventario automáticamente: las líneas de insumos permiten mapear un `product.product` para una fase posterior.

## Instalación rápida

1. Copiar la carpeta `dialysis_demo` dentro de un directorio incluido en `addons_path`.
2. Reiniciar Odoo.
3. Activar modo desarrollador y actualizar la lista de aplicaciones.
4. Buscar **Hemodiálisis - Demo Clínico** e instalar.

Por línea de comandos:

```bash
./odoo-bin -c /etc/odoo.conf -d NOMBRE_BD -i dialysis_demo --stop-after-init
```

## Flujo de prueba

1. Crear un contacto de Odoo para el paciente.
2. Hemodiálisis > Pacientes > Nuevo.
3. Registrar peso seco y acceso vascular.
4. Hemodiálisis > Sesiones > Nuevo.
5. Seleccionar paciente, turno y sillón.
6. Pulsar **Iniciar diálisis**. Se generan controles cada 30/60 min e insumos sugeridos.
7. Completar la matriz intra-diálisis y los datos post-diálisis.
8. Marcar todos los insumos como usados/confirmados.
9. Pulsar **Completar sesión**.

## Límites del prototipo

No incluye Kt/V, PRU, gráficos de ganancia interdialítica, seguimiento detallado del acceso vascular, webhook NIMBO/n8n, lectura automática de máquinas ni movimientos reales de inventario. Esos elementos se plantean para una segunda fase.

> Este módulo es un prototipo de software. Antes de uso clínico real se requiere validación de flujo, permisos por rol, auditoría, privacidad, respaldo, integridad de datos y cumplimiento normativo aplicable.
