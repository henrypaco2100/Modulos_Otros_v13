# ESI - Informes de Producción v13

Módulo técnico: `esi_produccion_report_v13`.

## Funciones
- Wizard en Fabricación > Informes > Informes de Producción.
- Rango por día, mes, año o fechas personalizadas.
- Filtro por fecha planificada o fecha finalizada y por estado.
- Agrupación por OF, producto terminado, semana, mes, responsable y, si existe Multi Store, sucursal.
- Vista HTML, PDF y Excel.
- Resumen de producción: planificado vs producido, cumplimiento, materiales con sobreconsumo/bajo consumo y mermas.
- Consumo de materia prima: LdM/planificado vs consumo real, variación absoluta y porcentual.
- Costos y margen potencial para Responsable de Producción/Administrador.
- Reporte individual desde **Imprimir > Análisis de Producción ESI**.
- Si existe `stock_account`, intenta usar capas de valoración; si no, usa costo estándar actual como aproximación.
- Integración opcional con `esi_mrp_mejoras_v13`, sin convertirla en dependencia dura.

## Integración nueva con tiempos y destajo ESI
Cuando `esi_mrp_mejoras_v13` está instalado, el análisis individual de la OF incorpora por operación:
- Área/etapa y operador.
- Tiempo estándar en segundos por par.
- Minutos estándar del lote y minutos reales registrados.
- Tarifa de destajo por par.
- Destajo planificado y destajo registrado en los partes.
- Estado de medición.
- Costos técnicos/centro de trabajo usados en los totales.

El módulo conserva compatibilidad con instalaciones donde las mejoras ESI no estén instaladas: comprueba dinámicamente la existencia de los campos adicionales.
