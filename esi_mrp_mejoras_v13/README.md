# ESI - Mejoras MRP Calzado v13

Módulo técnico: `esi_mrp_mejoras_v13`.

## Objetivo
Extender Fabricación de Odoo 13 para representar el control de tiempos y pago por destajo usado en la planilla **CALCULO DE TIEMPOS Y COSTOS DE DESTAJO.xlsx**.

## Funciones principales
- Maestro de **Operadores ESI** por compañía.
- En cada operación de ruta: área/etapa, operador estándar, segundos por par, minutos por par, costo técnico por par, pago de destajo por par, cantidad de serie y cálculos para la serie.
- Estado de medición: **Medido / Pendiente / Estimado**.
- Trazabilidad a **hoja y fila de origen** de la planilla.
- En cada orden de trabajo: operador, etapa, tiempo estándar y destajo.
- En los partes de tiempo (`mrp.workcenter.productivity`): operador real, cantidad procesada, tarifa e importe de destajo.
- Menú **Fabricación > Informes > Partes de Producción ESI**.
- Menú **Fabricación > Informes > Apuntes de Destajo ESI** para notas independientes de una OF.
- Parámetros por compañía tomados de la hoja: costo laboral mensual, días/mes, horas/día, costo/día, costo/hora, costo/minuto y referencia pares/día/persona.

## Valores iniciales de la planilla
- Costo laboral promedio mensual: **Bs 3.300**.
- 26 días laborales/mes.
- 8 horas/día.
- Costo día: **Bs 126,9230769**.
- Costo hora: **Bs 15,8653846**.
- Costo minuto: **Bs 0,2644231**.
- Referencia informativa: **5 pares/día/persona**.

Estos parámetros son editables. No se usan como bloqueo de producción.
