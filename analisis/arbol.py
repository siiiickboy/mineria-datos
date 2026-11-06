import os
import pandas as pd
import matplotlib
matplotlib.use('Agg') # Requerido para servidores web (evita errores de GUI)
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score
from sklearn.preprocessing import LabelEncoder

def entrenar_arbol(df: pd.DataFrame, target_col: str, test_size: float = 0.3, criterion: str = 'gini', max_depth: int = None):
    """Entrena un árbol de decisión (RF3) y retorna modelo, métricas y ruta del gráfico."""
    df_modelo = df.copy()
    
    # Separar predictoras (X) de variable objetivo (y)
    predictoras = [c for c in df_modelo.columns if c != target_col]
    X = df_modelo[predictoras]
    y = df_modelo[target_col]

    # Convertir categóricas a numéricas para scikit-learn
    X = pd.get_dummies(X, drop_first=True)
    if not pd.api.types.is_numeric_dtype(y):
        le = LabelEncoder()
        y = le.fit_transform(y)
        clases_nombres = [str(cls) for cls in le.classes_]
    else:
        clases_nombres = [str(cls) for cls in y.unique()]

    # División de datos
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    # Entrenamiento
    modelo = DecisionTreeClassifier(criterion=criterion, max_depth=max_depth, random_state=42)
    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)

    # Métricas
    metricas = {
        "exactitud": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
        "matriz_confusion": confusion_matrix(y_test, y_pred).tolist()
    }

    # Visualización
    ruta_img_relativa = "img/arbol.png"
    ruta_img_absoluta = os.path.join("web", "static", "img", "arbol.png")
    os.makedirs(os.path.dirname(ruta_img_absoluta), exist_ok=True)
    
    plt.figure(figsize=(14, 8))
    plot_tree(modelo, feature_names=X.columns, class_names=clases_nombres, filled=True, rounded=True, fontsize=10)
    plt.tight_layout()
    plt.savefig(ruta_img_absoluta, format="png")
    plt.close()

    return modelo, metricas, ruta_img_relativa