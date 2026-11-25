"""
RF6 - Cálculo de datos para Dashboard interactivo.
Prepara distribuciones, correlaciones y resumen de modelos a partir del DataFrame limpio.
"""
import numpy as np
import pandas as pd


def construir_datos_dashboard(
    df: pd.DataFrame,
    modelos_entrenados: list[dict] | None = None,
    filtro_columna: str | None = None,
    filtro_valor: str | None = None,
) -> dict:
    """Devuelve estructuras listas para gráficos, filtros dinámicos y métricas del dashboard."""
    df_filtrado = df.copy()
    columnas_disponibles = [str(c) for c in df.columns]

    valores_filtro = []
    if filtro_columna and filtro_columna in df.columns:
        valores_filtro = sorted(df[filtro_columna].dropna().astype(str).unique().tolist())[:50]
        if filtro_valor and filtro_valor != "__TODOS__":
            df_filtrado = df_filtrado[df_filtrado[filtro_columna].astype(str) == str(filtro_valor)]

    cols_numericas = df_filtrado.select_dtypes(include=[np.number]).columns.tolist()
    cols_categoricas = [c for c in df_filtrado.columns if c not in cols_numericas]

    distribuciones_numericas = {}
    for col in cols_numericas[:8]:
        serie = df_filtrado[col].dropna()
        if not serie.empty:
            conteos, bordes = np.histogram(serie, bins=min(8, max(3, serie.nunique())))
            etiquetas = [f"{round(float(bordes[i]), 2)}–{round(float(bordes[i+1]), 2)}" for i in range(len(conteos))]
            distribuciones_numericas[col] = {
                "etiquetas": etiquetas,
                "valores": [int(v) for v in conteos],
                "promedio": round(float(serie.mean()), 2),
                "mediana": round(float(serie.median()), 2),
            }

    distribuciones_categoricas = {}
    for col in cols_categoricas[:6]:
        vc = df_filtrado[col].fillna("sin_dato").astype(str).value_counts().head(8)
        distribuciones_categoricas[col] = {
            "etiquetas": vc.index.tolist(),
            "valores": [int(v) for v in vc.values],
        }

    correlacion = {"columnas": [], "matriz": []}
    if len(cols_numericas) >= 2:
        corr_df = df_filtrado[cols_numericas].corr().fillna(0.0).round(3)
        correlacion = {
            "columnas": corr_df.columns.tolist(),
            "matriz": corr_df.values.tolist(),
        }

    resumen_modelos = []
    for m in (modelos_entrenados or []):
        metricas = m.get("metricas", {})
        resumen_modelos.append({
            "id_modelo": m.get("id_modelo", ""),
            "target": m.get("target", ""),
            "exactitud": metricas.get("exactitud", 0),
            "precision": metricas.get("precision", 0),
            "recall": metricas.get("recall", 0),
        })

    return {
        "filas_filtradas": int(len(df_filtrado)),
        "filas_totales": int(len(df)),
        "columnas_totales": int(df.shape[1]),
        "columnas_disponibles": columnas_disponibles,
        "filtro_columna": filtro_columna or "",
        "filtro_valor": filtro_valor or "__TODOS__",
        "valores_filtro": valores_filtro,
        "distribuciones_numericas": distribuciones_numericas,
        "distribuciones_categoricas": distribuciones_categoricas,
        "correlacion": correlacion,
        "resumen_modelos": resumen_modelos,
    }