"""
Aplicación web (Flask) - RF1: carga de datos.

Ejecutar desde la raíz del proyecto:
    python web/app.py
"""

import json
import os
import sys
import uuid

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

# Permite importar la carpeta /analisis estando dentro de /web
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from analisis.validacion import TAMANO_MAXIMO_MB, validar_csv  # noqa: E402

CARPETA_SUBIDAS = os.path.join(RAIZ, "datos", "subidos")
os.makedirs(CARPETA_SUBIDAS, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambiar-esta-clave-en-produccion")
# Flask rechaza (error 413) cualquier petición más grande que esto.
app.config["MAX_CONTENT_LENGTH"] = TAMANO_MAXIMO_MB * 1024 * 1024


@app.route("/")
def inicio():
    return render_template("index.html", tamano_maximo=TAMANO_MAXIMO_MB)


@app.route("/subir", methods=["POST"])
def subir():
    archivo = request.files.get("archivo")
    if archivo is None or archivo.filename == "":
        flash("Selecciona un archivo CSV antes de subir.", "danger")
        return redirect(url_for("inicio"))

    nombre_original = secure_filename(archivo.filename) or "archivo.csv"
    id_dataset = uuid.uuid4().hex[:12]
    ruta = os.path.join(CARPETA_SUBIDAS, f"{id_dataset}.csv")
    archivo.save(ruta)

    # La validación se hace en la capa de análisis (Python)
    resultado = validar_csv(ruta, nombre_original)

    if not resultado.valido:
        os.remove(ruta)  # no guardamos archivos inválidos
        for error in resultado.errores:
            flash(error, "danger")
        return redirect(url_for("inicio"))

    # Guardamos los metadatos para la vista previa y para los siguientes módulos (limpieza, árbol...)
    metadatos = {"id": id_dataset, "nombre_original": nombre_original, **resultado.resumen()}
    with open(os.path.join(CARPETA_SUBIDAS, f"{id_dataset}.json"), "w", encoding="utf-8") as f:
        json.dump(metadatos, f, ensure_ascii=False, default=str)

    flash("Archivo cargado y validado correctamente.", "success")
    return redirect(url_for("vista_previa", id_dataset=id_dataset))


@app.route("/datos/<id_dataset>")
def vista_previa(id_dataset):
    ruta_meta = os.path.join(CARPETA_SUBIDAS, f"{secure_filename(id_dataset)}.json")
    if not os.path.exists(ruta_meta):
        flash("No se encontró ese conjunto de datos.", "warning")
        return redirect(url_for("inicio"))
    with open(ruta_meta, encoding="utf-8") as f:
        datos = json.load(f)
    return render_template("vista_previa.html", d=datos)


@app.route("/datos")
def listar():
    datasets = []
    for nombre in sorted(os.listdir(CARPETA_SUBIDAS), reverse=True):
        if nombre.endswith(".json"):
            with open(os.path.join(CARPETA_SUBIDAS, nombre), encoding="utf-8") as f:
                m = json.load(f)
            datasets.append(m)
    return render_template("listar.html", datasets=datasets)


@app.errorhandler(413)
def archivo_muy_grande(_error):
    flash(f"El archivo supera el tamaño máximo de {TAMANO_MAXIMO_MB} MB.", "danger")
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)
