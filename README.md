# Software de Administración de Minería de Datos

Aplicación web desarrollada en Python que reproduce las funcionalidades
principales de Orange Data Mining: carga de datos, limpieza automática,
modelado con árboles de decisión interactivos, gestión de modelos,
informes y dashboard.

-   **Capa de análisis:** Python (`pandas`, `numpy`, `scikit-learn`,
    `joblib`) → carpeta `/analisis`.
-   **Capa web:** Python con Flask + Bootstrap → carpeta `/web`.

## Comunicación entre capas

Ambas capas están desarrolladas en Python, por lo que la aplicación web
(`web/app.py`) importa directamente los módulos de la carpeta
`/analisis`. No se requiere una pasarela de API REST: Flask recibe el
archivo CSV, llama directamente a las funciones de validación, limpieza
y machine learning, y procesa los resultados para mostrarlos en las
plantillas HTML mediante Jinja2.

## Estructura del repositorio

``` text
mineria-datos/
├── analisis/              # Capa de procesamiento y análisis (Python)
│   ├── __init__.py
│   ├── validacion.py      # RF1: validación de formato, tamaño, codificación y separador
│   ├── limpieza.py        # RF2: limpieza automática (nulos, duplicados, atípicos IQR)
│   └── arbol.py           # RF3: entrenamiento de árboles de decisión y métricas
├── web/                   # Capa de aplicación web (Flask)
│   ├── app.py             # Controladores y rutas de la aplicación
│   ├── templates/         # Vistas HTML (Jinja2: index, configurar, resultados, listar, vista_previa)
│   └── static/            # Archivos estáticos (CSS y gráficos generados)
├── datos/
│   ├── ejemplos/          # Archivos CSV de prueba
│   ├── subidos/           # Historial y datasets dinámicos (ignorado por Git)
│   └── modelos/           # Persistencia física de modelos .pkl (ignorado por Git)
├── tests/                 # Pruebas unitarias con pytest (test_validacion.py)
├── requirements.txt
└── README.md
```

## Instalación

### Requisitos previos

-   Python 3.10 o superior.
-   Git.

### Pasos

``` bash
# 1. Clonar el repositorio
git clone https://github.com/siiiickboy/mineria-datos.git
cd mineria-datos

# 2. Crear y activar el entorno virtual
python -m venv venv

# En Windows (PowerShell)
venv\Scripts\activate

# En Linux o macOS
# source venv/bin/activate

# 3. Instalar las dependencias
pip install -r requirements.txt
```

## Uso

Para iniciar la aplicación web localmente, ejecuta:

``` bash
python web/app.py
```

Abre el navegador e ingresa a:

``` text
http://127.0.0.1:5000
```

Sube un archivo CSV. Puedes utilizar los archivos de ejemplo ubicados en
`datos/ejemplos/` y seguir el flujo interactivo de configuración y
resultados.

## Pruebas unitarias

Para ejecutar las pruebas del sistema de validación con `pytest`,
utiliza:

``` bash
pytest
```

## Estado de los módulos --- Entrega de avance (13 de noviembre)

  Requerimiento funcional        Estado
  ------------------------------ ------------------------------
  **RF1. Carga de datos**        ✅ Completado
  **RF2. Limpieza automática**   ✅ Completado
  **RF3. Árbol de decisión**     ✅ Completado
  **RF4. Asociación**            ⏳ Pendiente (entrega final)
  **RF5. Informes**              ⏳ Pendiente (entrega final)
  **RF6. Dashboard**             ⏳ Pendiente (entrega final)

### Descripción de módulos implementados

**RF1. Carga de datos**

Validación de extensiones (`.csv`), límite de tamaño de hasta 10 MB,
detección automática de codificación (`utf-8`, `cp1252`, `latin-1`) y
delimitadores (coma, punto y coma, tabulación y barra vertical). Incluye
una vista previa interactiva con conteo de valores nulos, duplicados y
tipos de datos.

**RF2. Limpieza automática**

Estandarización de cabeceras, eliminación de duplicados, imputación de
valores nulos (mediana para variables numéricas y eliminación de filas
para variables categóricas) y tratamiento de valores atípicos mediante
el Rango Intercuartílico (IQR) con winsorización.

**RF3. Árbol de decisión**

Módulo interactivo que permite seleccionar dinámicamente la variable
objetivo (target), las variables predictoras y configurar
hiperparámetros de entrenamiento (`criterion`, `max_depth`,
`test_size`). Calcula métricas de clasificación (exactitud, precisión,
recall y matriz de confusión), grafica el árbol y persiste los modelos
utilizando `joblib`.

## Flujo de trabajo con Git

El desarrollo se gestiona mediante Git utilizando ramas funcionales
(`feature/`), una rama de integración (`develop`) y la rama principal de
entregas (`main`).

``` bash
# Cambiar a la rama de integración
git checkout develop

# Crear una rama para una nueva funcionalidad
git checkout -b feature/nombre-funcionalidad

# Trabajar y registrar los cambios mediante commits

# Enviar la rama a GitHub
git push -u origin feature/nombre-funcionalidad

# Crear un Pull Request hacia develop para revisión de código
```

## Integrantes del equipo

-   Byron Carrasco
-   Leonardo Perez
