# Software de Administración de Minería de Datos

Aplicación web que reproduce las funcionalidades principales de Orange Data Mining:
carga de datos, limpieza, árbol de decisión, reglas de asociación, informes y dashboard.

- **Capa de análisis:** Python (pandas, scikit-learn, mlxtend) → carpeta `/analisis`
- **Capa web:** Python con Flask + Bootstrap → carpeta `/web`

## Comunicación entre capas

Ambas capas están en Python, así que la aplicación web (`web/app.py`) **importa directamente**
los módulos de `/analisis` (por ejemplo `from analisis.validacion import validar_csv`).
No hace falta una API REST: Flask recibe el archivo, llama a la función de análisis
y muestra el resultado en las plantillas.

## Estructura del repositorio

```
mineria-datos/
├── analisis/              # Capa de procesamiento (Python)
│   ├── __init__.py
│   └── validacion.py      # RF1: validación del CSV y vista previa
├── web/                   # Capa de aplicación web (Flask)
│   ├── app.py
│   ├── templates/         # Vistas HTML (Jinja2)
│   └── static/            # CSS
├── datos/
│   ├── ejemplos/          # CSV de prueba
│   └── subidos/           # Archivos que suben los usuarios (ignorado por Git)
├── tests/                 # Pruebas con pytest
├── requirements.txt
└── README.md
```

## Instalación

Requisitos: Python 3.10 o superior y Git.

```bash
git clone https://github.com/USUARIO/mineria-datos.git
cd mineria-datos

python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / Mac:
source venv/bin/activate

pip install -r requirements.txt
```

## Uso

```bash
python web/app.py
```

Abrir <http://127.0.0.1:5000> en el navegador, subir un CSV (hay ejemplos en `datos/ejemplos/`)
y revisar la vista previa.

## Pruebas

```bash
pytest
```

## Módulos

| Requerimiento | Estado |
|---|---|
| RF1. Carga de datos | ✅ Listo |
| RF2. Limpieza automática | ⏳ Pendiente |
| RF3. Árbol de decisión | ⏳ Pendiente |
| RF4. Asociación | ⏳ Pendiente |
| RF5. Informes | ⏳ Pendiente |
| RF6. Dashboard | ⏳ Pendiente |

### RF1. Carga de datos

Al subir un archivo, `analisis/validacion.py` revisa:

| Validación | Cómo se hace |
|---|---|
| **Formato** | La extensión debe ser `.csv` y el contenido debe ser texto (se rechazan archivos binarios como un Excel renombrado). |
| **Tamaño** | Máximo 10 MB (`TAMANO_MAXIMO_MB`). Se revisa en el navegador, en Flask (`MAX_CONTENT_LENGTH`) y en Python. Se rechazan archivos vacíos. |
| **Codificación** | Se prueba UTF-8 (con y sin BOM), Windows-1252 y Latin-1, en ese orden. Si no es UTF-8 se muestra una advertencia. |
| **Separador** | Se detecta con `csv.Sniffer` entre coma, punto y coma, tabulación y barra. Si solo resulta una columna, se rechaza. |
| **Estructura** | Debe tener al menos 2 columnas y 1 fila de datos. Las filas con columnas de más se omiten y se avisa. |

La **vista previa** muestra filas, columnas, nulos, duplicados, el tipo de cada columna y las primeras 20 filas.

## Flujo de trabajo con Git

Ramas:
- `main`: versiones entregables (avance y entrega final).
- `develop`: integración del trabajo de ambos.
- `feature/<nombre>`: una rama por funcionalidad (por ejemplo `feature/carga-csv`, `feature/limpieza`).

```bash
git checkout develop
git checkout -b feature/limpieza
# ... trabajar y hacer commits ...
git push -u origin feature/limpieza
# Abrir un Pull Request de feature/limpieza hacia develop en GitHub
```

## Integrantes

- Integrante 1
- Integrante 2
