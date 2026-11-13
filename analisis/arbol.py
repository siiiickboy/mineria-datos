import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score
from sklearn.preprocessing import LabelEncoder
import joblib
import uuid

def entrenar_arbol(df: pd.DataFrame, target_col: str, predictoras: list, test_size: float = 0.3, criterion: str = 'gini', max_depth: int = None):
    df_modelo = df.copy()
    
    X = df_modelo[predictoras]
    y = df_modelo[target_col]

    X = pd.get_dummies(X, drop_first=True)
    if not pd.api.types.is_numeric_dtype(y):
        le = LabelEncoder()
        y = le.fit_transform(y)
        clases_nombres = [str(cls) for cls in le.classes_]
    else:
        clases_nombres = [str(cls) for cls in y.unique()]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42)

    modelo = DecisionTreeClassifier(criterion=criterion, max_depth=max_depth, random_state=42)
    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)

    metricas = {
        "exactitud": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, average='weighted', zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, average='weighted', zero_division=0), 4),
        "matriz_confusion": confusion_matrix(y_test, y_pred).tolist()
    }

    id_modelo = uuid.uuid4().hex[:8]
    
    ruta_modelo = os.path.join("datos", "modelos", f"modelo_{id_modelo}.pkl")
    os.makedirs(os.path.dirname(ruta_modelo), exist_ok=True)
    joblib.dump(modelo, ruta_modelo)

    nombre_img = f"arbol_{id_modelo}.png"
    ruta_img_absoluta = os.path.join("web", "static", "img", nombre_img)
    os.makedirs(os.path.dirname(ruta_img_absoluta), exist_ok=True)
    
    plt.figure(figsize=(12, 8))
    plot_tree(modelo, feature_names=X.columns, class_names=clases_nombres, filled=True, rounded=True, fontsize=10)
    plt.tight_layout()
    plt.savefig(ruta_img_absoluta, format="png")
    plt.close()

    return id_modelo, metricas, f"img/{nombre_img}"