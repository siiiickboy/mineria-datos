"""
RF1 - Validación de archivos CSV.

Valida formato, tamaño, codificación y separador de un archivo CSV
y genera la información para la vista previa.

Uso:
    from analisis.validacion import validar_csv
    resultado = validar_csv("datos.csv")
    if resultado.valido:
        df = resultado.dataframe
"""

import csv
import io
import os
from dataclasses import dataclass, field

import pandas as pd

# --- Configuración de la validación ---------------------------------------
TAMANO_MAXIMO_MB = 10
EXTENSIONES_PERMITIDAS = {".csv"}
# Orden importa: latin-1 acepta cualquier byte, por eso va al final.
CODIFICACIONES = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
SEPARADORES = [",", ";", "\t", "|"]
NOMBRES_SEPARADOR = {",": "coma (,)", ";": "punto y coma (;)", "\t": "tabulación", "|": "barra (|)"}
FILAS_VISTA_PREVIA = 20


@dataclass
class ResultadoValidacion:
    valido: bool = False
    errores: list = field(default_factory=list)
    advertencias: list = field(default_factory=list)
    codificacion: str | None = None
    separador: str | None = None
    tamano_bytes: int = 0
    dataframe: pd.DataFrame | None = None

    def resumen(self) -> dict:
        """Devuelve un diccionario serializable a JSON (sin el DataFrame)."""
        datos = {
            "valido": self.valido,
            "errores": self.errores,
            "advertencias": self.advertencias,
            "codificacion": self.codificacion,
            "separador": self.separador,
            "separador_nombre": NOMBRES_SEPARADOR.get(self.separador, self.separador),
            "tamano_kb": round(self.tamano_bytes / 1024, 2),
        }
        if self.dataframe is not None:
            datos.update(info_vista_previa(self.dataframe))
        return datos


# --- Validaciones individuales --------------------------------------------
def validar_extension(nombre_archivo: str) -> str | None:
    ext = os.path.splitext(nombre_archivo)[1].lower()
    if ext not in EXTENSIONES_PERMITIDAS:
        return f"Formato no permitido ({ext or 'sin extensión'}). Solo se aceptan archivos .csv."
    return None


def validar_tamano(tamano_bytes: int) -> str | None:
    if tamano_bytes == 0:
        return "El archivo está vacío."
    if tamano_bytes > TAMANO_MAXIMO_MB * 1024 * 1024:
        return f"El archivo supera el tamaño máximo de {TAMANO_MAXIMO_MB} MB."
    return None


def es_binario(contenido: bytes) -> bool:
    """Un CSV es texto: si tiene bytes nulos, probablemente es otro tipo de archivo (xlsx, imagen...)."""
    return b"\x00" in contenido[:8192]


def detectar_codificacion(contenido: bytes) -> tuple[str, str]:
    """Prueba las codificaciones en orden y devuelve (codificacion, texto)."""
    for cod in CODIFICACIONES:
        try:
            return cod, contenido.decode(cod)
        except UnicodeDecodeError:
            continue
    raise ValueError("No se pudo determinar la codificación del archivo.")


def detectar_separador(texto: str) -> str:
    """Detecta el separador con csv.Sniffer y, si falla, contando apariciones."""
    muestra = "\n".join(texto.splitlines()[:50])
    try:
        return csv.Sniffer().sniff(muestra, delimiters="".join(SEPARADORES)).delimiter
    except csv.Error:
        primera_linea = texto.splitlines()[0] if texto.strip() else ""
        conteos = {sep: primera_linea.count(sep) for sep in SEPARADORES}
        mejor = max(conteos, key=conteos.get)
        return mejor if conteos[mejor] > 0 else ","


# --- Validación completa --------------------------------------------------
def validar_csv(ruta: str, nombre_original: str | None = None) -> ResultadoValidacion:
    """Valida un CSV guardado en disco y, si es válido, lo carga en un DataFrame."""
    r = ResultadoValidacion()
    nombre = nombre_original or os.path.basename(ruta)

    # 1. Formato (extensión)
    error = validar_extension(nombre)
    if error:
        r.errores.append(error)
        return r

    # 2. Tamaño
    r.tamano_bytes = os.path.getsize(ruta)
    error = validar_tamano(r.tamano_bytes)
    if error:
        r.errores.append(error)
        return r

    with open(ruta, "rb") as f:
        contenido = f.read()

    if es_binario(contenido):
        r.errores.append("El archivo no es texto plano. ¿Es un Excel renombrado a .csv?")
        return r

    # 3. Codificación
    try:
        r.codificacion, texto = detectar_codificacion(contenido)
    except ValueError as e:
        r.errores.append(str(e))
        return r
    if r.codificacion in ("cp1252", "latin-1"):
        r.advertencias.append(f"El archivo no está en UTF-8; se leyó como {r.codificacion}.")

    if not texto.strip():
        r.errores.append("El archivo no contiene datos.")
        return r

    # 4. Separador
    r.separador = detectar_separador(texto)

    # 5. Lectura con pandas
    filas_malas = []
    try:
        df = pd.read_csv(
            io.StringIO(texto),
            sep=r.separador,
            engine="python",
            on_bad_lines=lambda linea: filas_malas.append(linea) and None,
        )
    except Exception as e:  # noqa: BLE001 - mostramos el error al usuario
        r.errores.append(f"No se pudo leer el CSV: {e}")
        return r

    # 6. Estructura mínima
    if df.shape[1] < 2:
        r.errores.append(
            "Se detectó una sola columna. Revisa que el separador sea coma, punto y coma, tabulación o barra."
        )
        return r

    # Filas donde TODAS las celdas están vacías (por ejemplo ",,,,,") no son datos.
    filas_vacias = int(df.isna().all(axis=1).sum())
    if filas_vacias:
        df = df.dropna(how="all").reset_index(drop=True)

    if df.empty:
        if filas_vacias:
            r.errores.append(
                f"El archivo tiene encabezado pero sus {filas_vacias} filas están completamente vacías (no hay datos)."
            )
        else:
            r.errores.append("El archivo tiene encabezado pero no tiene filas de datos.")
        return r

    if filas_vacias:
        r.advertencias.append(f"Se ignoraron {filas_vacias} fila(s) completamente vacías.")
    columnas_vacias = [str(c) for c in df.columns if df[c].isna().all()]
    if columnas_vacias:
        r.advertencias.append(f"Columnas sin ningún dato: {', '.join(columnas_vacias)}.")

    if filas_malas:
        r.advertencias.append(
            f"Se omitieron {len(filas_malas)} fila(s) con un número de columnas distinto al encabezado."
        )
    sin_nombre = [c for c in df.columns if str(c).startswith("Unnamed:")]
    if sin_nombre:
        r.advertencias.append(f"Hay {len(sin_nombre)} columna(s) sin nombre en el encabezado.")
    duplicadas = [c for c in df.columns if "." in str(c) and str(c).rsplit(".", 1)[0] in df.columns]
    if duplicadas:
        r.advertencias.append(f"Columnas con nombre repetido (pandas las renombró): {', '.join(map(str, duplicadas))}.")

    r.dataframe = df
    r.valido = True
    return r


# --- Vista previa ---------------------------------------------------------
def info_vista_previa(df: pd.DataFrame, n: int = FILAS_VISTA_PREVIA) -> dict:
    """Información para mostrar en la interfaz: dimensiones, columnas, tipos, nulos y primeras filas."""
    columnas = [
        {
            "nombre": str(col),
            "tipo": str(df[col].dtype),
            "nulos": int(df[col].isna().sum()),
            "unicos": int(df[col].nunique()),
        }
        for col in df.columns
    ]
    primeras = df.head(n).astype(object).where(df.head(n).notna(), None)
    return {
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
        "total_nulos": int(df.isna().sum().sum()),
        "duplicados": int(df.duplicated().sum()),
        "detalle_columnas": columnas,
        "encabezados": [str(c) for c in df.columns],
        "primeras_filas": primeras.values.tolist(),
    }
