import pandas as pd
import numpy as np

def ejecutar_limpieza(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    resumen = {
        "filas_originales": len(df),
        "columnas_modificadas": [],
        "duplicados_eliminados": 0,
        "nulos_tratados": 0,
        "atipicos_tratados": 0
    }
    
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    duplicados = df.duplicated().sum()
    if duplicados > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        resumen["duplicados_eliminados"] = int(duplicados)
        
    nulos_totales = df.isna().sum().sum()
    if nulos_totales > 0:
        for col in df.columns:
            if df[col].isna().sum() > 0:
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
                else:
                    df = df.dropna(subset=[col])
        resumen["nulos_tratados"] = int(nulos_totales - df.isna().sum().sum())
        df = df.reset_index(drop=True)
        
    df = df.convert_dtypes()
    
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
            df[col] = np.where(df[col] < limite_inf, limite_inf, df[col])
            df[col] = np.where(df[col] > limite_sup, limite_sup, df[col])
            
    resumen["filas_finales"] = len(df)
    resumen["columnas_modificadas"] = list(set(resumen["columnas_modificadas"]))
    
    return df, resumen