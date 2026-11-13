"""
Aplicación web (Flask) - RF1 (Carga), RF2 (Limpieza) y RF3 (Árbol Interactivo).
"""
import json
import os
import sys
import uuid
import pandas as pd

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from analisis.validacion import TAMANO_MAXIMO_MB, validar_csv
from analisis.limpieza import ejecutar_limpieza
from analisis.arbol import entrenar_arbol

CARPETA_SUBIDAS = os.path.join(RAIZ, "datos", "subidos")
os.makedirs(CARPETA_SUBIDAS, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambiar-clave")
app.config["MAX_CONTENT_LENGTH"] = TAMANO_MAXIMO_MB * 1024 * 1024

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
        "modelos_entrenados": [], 
        **resultado.resumen()
    }
    with open(os.path.join(CARPETA_SUBIDAS, f"{id_dataset}.json"), "w", encoding="utf-8") as f:
        json.dump(metadatos, f, ensure_ascii=False, default=str)

    flash("Limpieza automática completada. Configura tu modelo.", "success")
    return redirect(url_for("configurar", id_dataset=id_dataset))

@app.route("/configurar/<id_dataset>")
def configurar(id_dataset):
    ruta_meta = os.path.join(CARPETA_SUBIDAS, f"{secure_filename(id_dataset)}.json")
    if not os.path.exists(ruta_meta):
        return redirect(url_for("inicio"))
    with open(ruta_meta, encoding="utf-8") as f:
        datos = json.load(f)
    return render_template("configurar.html", d=datos)

@app.route("/entrenar/<id_dataset>", methods=["POST"])
def entrenar(id_dataset):
    ruta_meta = os.path.join(CARPETA_SUBIDAS, f"{secure_filename(id_dataset)}.json")
    with open(ruta_meta, encoding="utf-8") as f:
        datos = json.load(f)

    target_col = request.form.get("target")
    predictoras = request.form.getlist("predictoras")
    criterio = request.form.get("criterio", "gini")
    profundidad = request.form.get("profundidad")
    profundidad = int(profundidad) if profundidad else None
    test_size = float(request.form.get("test_size", 30)) / 100.0

    if not predictoras or target_col in predictoras:
        flash("Debes elegir variables predictoras distintas al objetivo.", "danger")
        return redirect(url_for("configurar", id_dataset=id_dataset))

    df = pd.read_csv(os.path.join(CARPETA_SUBIDAS, f"{id_dataset}.csv"))
    id_modelo, metricas, grafico = entrenar_arbol(df, target_col, predictoras, test_size, criterio, profundidad)

    nuevo_modelo = {
        "id_modelo": id_modelo,
        "target": target_col,
        "predictoras": predictoras,
        "parametros": {"criterio": criterio, "profundidad": profundidad, "test_size": test_size},
        "metricas": metricas,
        "grafico": grafico
    }
    datos["modelos_entrenados"].append(nuevo_modelo)
    
    with open(ruta_meta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, default=str)

    return redirect(url_for("resultados", id_dataset=id_dataset))

@app.route("/resultados/<id_dataset>")
def resultados(id_dataset):
    ruta_meta = os.path.join(CARPETA_SUBIDAS, f"{secure_filename(id_dataset)}.json")
    with open(ruta_meta, encoding="utf-8") as f:
        datos = json.load(f)
    return render_template("resultados.html", d=datos)

@app.route("/datos/<id_dataset>")
def vista_previa(id_dataset):
    ruta_meta = os.path.join(CARPETA_SUBIDAS, f"{secure_filename(id_dataset)}.json")
    if not os.path.exists(ruta_meta):
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
                datasets.append(json.load(f))
    return render_template("listar.html", datasets=datasets)

if __name__ == "__main__":
    app.run(debug=True)