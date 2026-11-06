import pandas as pd
import numpy as np

def ejecutar_limpieza(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Realiza la limpieza automática (RF2) y devuelve el df limpio y un resumen."""
    resumen = {
        "filas_originales": len(df),
        "columnas_modificadas": [],
        "duplicados_eliminados": 0,
        "nulos_tratados": 0,
        "atipicos_tratados": 0
    }

    # 1. Normalización de nombres de columnas
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    # 2. Eliminación de duplicados
    duplicados = df.duplicated().sum()
    if duplicados > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        resumen["duplicados_eliminados"] = int(duplicados)

    # 3. Tratamiento de nulos
    nulos_totales = df.isna().sum().sum()
    if nulos_totales > 0:
        for col in df.columns:
            if df[col].isna().sum() > 0:
                # Imputar numéricos con la mediana, eliminar filas si es categórico
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
                else:
                    df = df.dropna(subset=[col])
        resumen["nulos_tratados"] = int(nulos_totales - df.isna().sum().sum())
        df = df.reset_index(drop=True)

    # 4. Corrección de tipos
    df = df.convert_dtypes()

    # 5. Detección y manejo de valores atípicos (Rango Intercuartílico - IQR)
    for col in df.select_dtypes(include=[np.number]).columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        limite_inf = Q1 - 1.5 * IQR
        limite_sup = Q3 + 1.5 * IQR
        
        atipicos = ((df[col] < limite_inf) | (df[col] > limite_sup)).sum()
        if atipicos > 0:
            resumen["atipicos_tratados"] += int(atipicos)
            resumen["columnas_modificadas"].append(col)
            # Winsorización: limitar a los bordes en lugar de eliminar
            df[col] = np.where(df[col] < limite_inf, limite_inf, df[col])
            df[col] = np.where(df[col] > limite_sup, limite_sup, df[col])

    resumen["filas_finales"] = len(df)
    resumen["columnas_modificadas"] = list(set(resumen["columnas_modificadas"]))
    
    return df, resumen