"""
Aplicación web (Flask) - RF1 (Carga), RF2 (Limpieza), RF3 (Árbol),
RF4 (Asociación), RF5 (Informes) y RF6 (Dashboard).
"""
from datetime import datetime
import json
import os
import sys
import uuid
import pandas as pd
from flask import Flask, Response, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from analisis.validacion import TAMANO_MAXIMO_MB, validar_csv
from analisis.limpieza import ejecutar_limpieza
from analisis.arbol import entrenar_arbol
from analisis.asociacion import generar_reglas_asociacion
from analisis.dashboard import construir_datos_dashboard

CARPETA_SUBIDAS = os.path.join(RAIZ, "datos", "subidos")
os.makedirs(CARPETA_SUBIDAS, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambiar-clave")
app.config["MAX_CONTENT_LENGTH"] = TAMANO_MAXIMO_MB * 1024 * 1024


def _cargar_metadatos(id_dataset: str) -> dict | None:
    ruta_meta = os.path.join(CARPETA_SUBIDAS, f"{secure_filename(id_dataset)}.json")
    if not os.path.exists(ruta_meta):
        return None
    with open(ruta_meta, encoding="utf-8") as f:
        datos = json.load(f)
    datos.setdefault("modelos_entrenados", [])
    datos.setdefault("analisis_asociacion", [])
    datos.setdefault("notas_informe", "")
    return datos


def _guardar_metadatos(id_dataset: str, datos: dict) -> None:
    ruta_meta = os.path.join(CARPETA_SUBIDAS, f"{secure_filename(id_dataset)}.json")
    with open(ruta_meta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, default=str)


def _cargar_df_limpio(id_dataset: str) -> pd.DataFrame:
    ruta_csv = os.path.join(CARPETA_SUBIDAS, f"{secure_filename(id_dataset)}.csv")
    return pd.read_csv(ruta_csv)


@app.route("/")
def inicio():
    return render_template("index.html", tamano_maximo=TAMANO_MAXIMO_MB)


@app.route("/subir", methods=["POST"])
def subir():
    archivo = request.files.get("archivo")
    if archivo is None or archivo.filename == "":
        flash("Selecciona un archivo CSV.", "danger")
        return redirect(url_for("inicio"))

    nombre_original = secure_filename(archivo.filename) or "archivo.csv"
    id_dataset = uuid.uuid4().hex[:12]
    ruta = os.path.join(CARPETA_SUBIDAS, f"{id_dataset}.csv")
    archivo.save(ruta)

    resultado = validar_csv(ruta, nombre_original)
    if not resultado.valido:
        os.remove(ruta)
        for error in resultado.errores:
            flash(error, "danger")
        return redirect(url_for("inicio"))

    df_limpio, resumen_limpieza = ejecutar_limpieza(resultado.dataframe)
    df_limpio.to_csv(ruta, index=False)

    metadatos = {
        "id": id_dataset,
        "nombre_original": nombre_original,
        "resumen_limpieza": resumen_limpieza,
        "columnas_limpias": [str(c) for c in df_limpio.columns],
        "modelos_entrenados": [],
        "analisis_asociacion": [],
        "notas_informe": "",
        **resultado.resumen(),
    }
    _guardar_metadatos(id_dataset, metadatos)
    flash("Limpieza automática completada. Configura tu modelo o explora los módulos.", "success")
    return redirect(url_for("configurar", id_dataset=id_dataset))


@app.route("/configurar/<id_dataset>")
def configurar(id_dataset):
    datos = _cargar_metadatos(id_dataset)
    if not datos:
        return redirect(url_for("inicio"))
    columnas = datos.get("columnas_limpias") or datos.get("encabezados", [])
    return render_template("configurar.html", d=datos, columnas=columnas)


@app.route("/entrenar/<id_dataset>", methods=["POST"])
def entrenar(id_dataset):
    datos = _cargar_metadatos(id_dataset)
    if not datos:
        return redirect(url_for("inicio"))

    target_col = request.form.get("target")
    predictoras = request.form.getlist("predictoras")
    criterio = request.form.get("criterio", "gini")
    profundidad = request.form.get("profundidad")
    profundidad = int(profundidad) if profundidad else None
    test_size = float(request.form.get("test_size", 30)) / 100.0

    if not predictoras or target_col in predictoras:
        flash("Debes elegir variables predictoras distintas al objetivo.", "danger")
        return redirect(url_for("configurar", id_dataset=id_dataset))

    df = _cargar_df_limpio(id_dataset)
    id_modelo, metricas, grafico = entrenar_arbol(
        df, target_col, predictoras, test_size, criterio, profundidad
    )
    nuevo_modelo = {
        "id_modelo": id_modelo,
        "target": target_col,
        "predictoras": predictoras,
        "parametros": {"criterio": criterio, "profundidad": profundidad, "test_size": test_size},
        "metricas": metricas,
        "grafico": grafico,
    }
    datos["modelos_entrenados"].append(nuevo_modelo)
    _guardar_metadatos(id_dataset, datos)
    flash("Árbol de decisión entrenado y guardado correctamente.", "success")
    return redirect(url_for("resultados", id_dataset=id_dataset))


@app.route("/asociacion/<id_dataset>", methods=["GET", "POST"])
def asociacion(id_dataset):
    datos = _cargar_metadatos(id_dataset)
    if not datos:
        return redirect(url_for("inicio"))

    df = _cargar_df_limpio(id_dataset)
    columnas = [str(c) for c in df.columns]

    if request.method == "POST":
        accion = request.form.get("accion", "generar")
        if accion == "eliminar":
            id_regla = request.form.get("id_analisis", "")
            datos["analisis_asociacion"] = [
                a for a in datos["analisis_asociacion"] if a.get("id_analisis") != id_regla
            ]
            _guardar_metadatos(id_dataset, datos)
            flash("Resultado de asociación eliminado.", "info")
            return redirect(url_for("asociacion", id_dataset=id_dataset))

        columnas_sel = request.form.getlist("columnas") or columnas
        algoritmo = request.form.get("algoritmo", "apriori")
        soporte_min = float(request.form.get("soporte_min", 0.2))
        confianza_min = float(request.form.get("confianza_min", 0.6))
        lift_min = float(request.form.get("lift_min", 1.0))

        try:
            id_analisis, reglas = generar_reglas_asociacion(
                df,
                columnas=columnas_sel,
                soporte_min=soporte_min,
                confianza_min=confianza_min,
                lift_min=lift_min,
                algoritmo=algoritmo,
            )
            registro = {
                "id_analisis": id_analisis,
                "algoritmo": algoritmo,
                "columnas": columnas_sel,
                "parametros": {
                    "soporte_min": soporte_min,
                    "confianza_min": confianza_min,
                    "lift_min": lift_min,
                },
                "total_reglas": len(reglas),
                "reglas": reglas,
            }
            datos["analisis_asociacion"].append(registro)
            _guardar_metadatos(id_dataset, datos)
            flash(f"Se generaron {len(reglas)} regla(s) de asociación.", "success")
        except Exception as exc:
            flash(f"No se pudieron generar reglas: {exc}", "danger")

        return redirect(url_for("asociacion", id_dataset=id_dataset))

    filtro_texto = request.args.get("buscar", "").strip().lower()
    ordenar_por = request.args.get("orden", "lift")
    if ordenar_por not in ("lift", "confianza", "soporte"):
        ordenar_por = "lift"

    lotes = []
    for lote in reversed(datos["analisis_asociacion"]):
        copia = dict(lote)
        reglas_filtradas = list(copia.get("reglas", []))
        if filtro_texto:
            reglas_filtradas = [
                r for r in reglas_filtradas
                if filtro_texto in r.get("antecedentes_str", "").lower()
                or filtro_texto in r.get("consecuentes_str", "").lower()
            ]
        reglas_filtradas.sort(key=lambda r: r.get(ordenar_por, 0), reverse=True)
        copia["reglas_filtradas"] = reglas_filtradas
        lotes.append(copia)

    return render_template(
        "asociacion.html",
        d=datos,
        columnas=columnas,
        lotes=lotes,
        buscar=filtro_texto,
        orden=ordenar_por,
    )


@app.route("/dashboard/<id_dataset>")
def dashboard(id_dataset):
    datos = _cargar_metadatos(id_dataset)
    if not datos:
        return redirect(url_for("inicio"))

    df = _cargar_df_limpio(id_dataset)
    filtro_col = request.args.get("columna", "")
    filtro_val = request.args.get("valor", "__TODOS__")

    dash = construir_datos_dashboard(
        df,
        modelos_entrenados=datos.get("modelos_entrenados", []),
        filtro_columna=filtro_col,
        filtro_valor=filtro_val,
    )
    return render_template("dashboard.html", d=datos, dash=dash)


@app.route("/informe/<id_dataset>", methods=["GET", "POST"])
def informe(id_dataset):
    datos = _cargar_metadatos(id_dataset)
    if not datos:
        return redirect(url_for("inicio"))

    if request.method == "POST":
        datos["notas_informe"] = request.form.get("notas_informe", "").strip()
        _guardar_metadatos(id_dataset, datos)
        flash("Conclusiones del informe guardadas.", "success")
        return redirect(url_for("informe", id_dataset=id_dataset))

    fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M")
    return render_template("informe.html", d=datos, fecha_emision=fecha_emision)


@app.route("/informe/<id_dataset>/exportar")
def exportar_informe_html(id_dataset):
    datos = _cargar_metadatos(id_dataset)
    if not datos:
        return redirect(url_for("inicio"))

    fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M")
    html_renderizado = render_template("informe.html", d=datos, fecha_emision=fecha_emision, exportado=True)
    nombre_archivo = f"informe_{datos.get('id', id_dataset)}.html"
    return Response(
        html_renderizado,
        mimetype="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )


@app.route("/resultados/<id_dataset>")
def resultados(id_dataset):
    datos = _cargar_metadatos(id_dataset)
    if not datos:
        return redirect(url_for("inicio"))
    return render_template("resultados.html", d=datos)


@app.route("/datos/<id_dataset>")
def vista_previa(id_dataset):
    datos = _cargar_metadatos(id_dataset)
    if not datos:
        return redirect(url_for("inicio"))
    return render_template("vista_previa.html", d=datos)


@app.route("/datos")
def listar():
    datasets = []
    for nombre in sorted(os.listdir(CARPETA_SUBIDAS), reverse=True):
        if nombre.endswith(".json"):
            with open(os.path.join(CARPETA_SUBIDAS, nombre), encoding="utf-8") as f:
                datasets.append(json.load(f))
    return render_template("listar.html", datasets=datasets)


if __name__ == "__main__":
    app.run(debug=True)