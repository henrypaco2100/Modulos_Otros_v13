# ESI - Informes de Producción v13

Módulo técnico: `esi_produccion_report_v13`.

## Funciones
- Wizard en Fabricación > Informes > Informes de Producción.
- Rango por día, mes, año o fechas personalizadas.
- Filtro por fecha planificada o fecha finalizada y por estado.
- Agrupación por OF, producto terminado, semana, mes, responsable y, si existe Multi Store, sucursal.
- Vista HTML, PDF y Excel.
- Resumen de producción: planificado vs producido, cumplimiento, materiales con sobreconsumo/bajo consumo y mermas.
- Consumo de materia prima: LdM/planificado vs consumo real, variación absoluta y porcentual. Los responsables de Producción/Administradores también ven variación de costo.
- Costos y margen potencial: disponible para Responsable de Producción/Administrador. Incluye costo material, costo de centros de trabajo, costo total, costo unitario, PVP, valor potencial y margen potencial.
- Reporte individual desde el menú **Imprimir** de cada Orden de Producción: `Análisis de Producción ESI`.
- Si existe `stock_account`, intenta usar capas de valoración para costo real de materiales; si no, usa costo estándar actual como aproximación.
- Si existe Multi Store, muestra/agrupa por sucursal sin agregar dependencia dura.
- Seguridad Multi Store: si los campos ESI están presentes, el wizard limita las OF por la sucursal activa/sucursales permitidas del usuario, además de las reglas nativas que ya apliquen.

## Actualización 13.0.2.0.0
- Smart button **Análisis Producción** en la Orden de Producción, con estilo `oe_stat_button` e icono de gráfico.
- Abre una vista HTML del análisis individual sin descargar automáticamente.
- Desde esa vista se puede descargar PDF y Excel.
- Excel individual con hojas Resumen, Materia Prima y Operaciones.
