# Software de Administración de Minería de Datos

Aplicación web desarrollada en Python (**B&L™**) que reproduce las funcionalidades principales de Orange Data Mining: carga de datos, limpieza automática, modelado con árboles de decisión interactivos, reglas de asociación, dashboard y generación de informes.

- **Capa de análisis:** Python (`pandas`, `numpy`, `scikit-learn`, `joblib`, `matplotlib`, `mlxtend`) → carpeta `/analisis`.
- **Capa web:** Python con Flask + Bootstrap 5 + Plotly → carpeta `/web`.

## Comunicación entre capas

Ambas capas están desarrolladas en Python, por lo que la aplicación web (`web/app.py`) importa directamente los módulos de la carpeta `/analisis` (`validacion.py`, `limpieza.py`, `arbol.py`, `asociacion.py` y `dashboard.py`) y persiste los datasets limpios y metadatos de análisis en `datos/subidos/`.

## Estructura del repositorio

```text
mineria-datos/
├── analisis/              # Capa de procesamiento y análisis (Python)
│   ├── __init__.py
│   ├── validacion.py      # RF1: validación de formato, tamaño, codificación y separador
│   ├── limpieza.py        # RF2: limpieza automática (nulos, duplicados, atípicos IQR)
│   ├── arbol.py           # RF3: entrenamiento de árboles de decisión, gráficos y métricas
│   ├── asociacion.py      # RF4: reglas de asociación con mlxtend (Apriori / FP-Growth)
│   └── dashboard.py       # RF6: cálculos de distribuciones, correlaciones y resumen de modelos
├── web/                   # Capa de aplicación web (Flask)
│   ├── app.py             # Controladores y rutas (RF1–RF6)
│   ├── templates/         # Vistas HTML (Jinja2)
│   └── static/            # Archivos estáticos (CSS, gráficos generados y exportación de informes)
├── datos/
│   ├── ejemplos/          # Archivos CSV de prueba (incluye dataset_maestro_demo.csv)
│   ├── subidos/           # Historial, datasets limpios y metadatos JSON (ignorado por Git)
│   └── modelos/           # Persistencia física de modelos .pkl (ignorado por Git)
├── tests/                 # Pruebas unitarias con pytest
├── requirements.txt
└── README.md

Instalación y ejecuciónBash
# 1. Crear y activar entorno virtual
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación web
python web/app.py

Abre el navegador en http://127.0.0.1:5000.
Estado de los módulos

Requerimiento funcional                 Estado
RF1. Carga de datos                       ✅ Completado
RF2. Limpieza automática                  ✅ Completado
RF3. Árbol de decisión                    ✅ Completado
RF4. Asociación                           ✅ Completado
RF5. Informes                             ✅ Completado (HTML y vista imprimible/PDF)RF6. Dashboard                            ✅ Completado

Integrantes del equipo
Byron Carrasco
Leonardo Pérez