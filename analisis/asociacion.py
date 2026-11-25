"""
RF4 - Módulo de Reglas de Asociación con mlxtend.
Genera itemsets frecuentes y reglas (soporte, confianza y lift) a partir de un DataFrame.
"""
import uuid
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth


def _preparar_transacciones(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Convierte columnas seleccionadas en una matriz booleana (True/False) para mlxtend."""
    cols_validas = [c for c in columnas if c in df.columns]
    if not cols_validas:
        raise ValueError("No se encontraron columnas válidas para reglas de asociación.")

    sub = df[cols_validas].copy()
    for col in cols_validas:
        if pd.api.types.is_numeric_dtype(sub[col]):
            unicos = sub[col].dropna().nunique()
            if unicos > 6:
                sub[col] = pd.qcut(
                    sub[col],
                    q=3,
                    labels=["bajo", "medio", "alto"],
                    duplicates="drop",
                ).astype(str)
            else:
                sub[col] = sub[col].astype(str)
        else:
            sub[col] = sub[col].fillna("sin_dato").astype(str)

    codificado = pd.get_dummies(sub, prefix_sep="=")
    return codificado.astype(bool)


def generar_reglas_asociacion(
    df: pd.DataFrame,
    columnas: list[str],
    soporte_min: float = 0.2,
    confianza_min: float = 0.6,
    lift_min: float = 1.0,
    algoritmo: str = "apriori",
) -> tuple[str, list[dict]]:
    """
    Ejecuta Apriori o FP-Growth y devuelve (id_analisis, lista_de_reglas).
    Cada regla incluye antecedentes, consecuentes, soporte, confianza y lift.
    """
    if df.empty:
        raise ValueError("El dataset está vacío; no se pueden generar reglas.")

    matriz = _preparar_transacciones(df, columnas)
    if matriz.empty or matriz.shape[1] == 0:
        raise ValueError("No se pudieron generar ítems para las columnas seleccionadas.")

    alg = (algoritmo or "apriori").lower().strip()
    if alg == "fpgrowth":
        frecuentes = fpgrowth(matriz, min_support=float(soporte_min), use_colnames=True)
    else:
        alg = "apriori"
        frecuentes = apriori(matriz, min_support=float(soporte_min), use_colnames=True)

    if frecuentes.empty:
        return uuid.uuid4().hex[:8], []

    reglas_df = association_rules(
        frecuentes,
        metric="confidence",
        min_threshold=float(confianza_min),
    )

    if reglas_df.empty:
        return uuid.uuid4().hex[:8], []

    if lift_min is not None:
        reglas_df = reglas_df[reglas_df["lift"] >= float(lift_min)]

    reglas_df = reglas_df.sort_values(by=["lift", "confidence", "support"], ascending=False)

    reglas_formateadas = []
    for _, fila in reglas_df.iterrows():
        antecedentes = sorted([str(x) for x in fila["antecedents"]])
        consecuentes = sorted([str(x) for x in fila["consequents"]])
        reglas_formateadas.append({
            "antecedentes": antecedentes,
            "consecuentes": consecuentes,
            "antecedentes_str": ", ".join(antecedentes),
            "consecuentes_str": ", ".join(consecuentes),
            "soporte": round(float(fila["support"]), 4),
            "confianza": round(float(fila["confidence"]), 4),
            "lift": round(float(fila["lift"]), 4),
            "algoritmo": alg,
        })

    return uuid.uuid4().hex[:8], reglas_formateadas