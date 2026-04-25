import pandas as pd
import io
from typing import Tuple


COLUMNAS_REQUERIDAS = ["actividad", "peso", "indicador_recurso"]


def leer_archivo(file) -> Tuple[pd.DataFrame | None, str]:
    """
    Lee un archivo Excel o CSV subido desde Streamlit.
    Retorna (DataFrame, mensaje_error). Si hay error, DataFrame es None.

    Formato esperado:
    - Columna 'actividad': nombre de la actividad
    - Columna 'peso': peso presupuestario (%)
    - Columna 'indicador_recurso': HH/m², kg/m², etc.
    - Columnas 'mes_0', 'mes_1', ..., 'mes_N': distribución % del avance
    """
    try:
        nombre = getattr(file, "name", "")
        if nombre.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        for col in COLUMNAS_REQUERIDAS:
            if col not in df.columns:
                return None, f"Falta la columna requerida: '{col}'"

        mes_cols = sorted([c for c in df.columns if c.startswith("mes_")])
        if len(mes_cols) < 2:
            return None, "Se requieren al menos columnas 'mes_0', 'mes_1', ..., 'mes_N'"

        df["peso"] = pd.to_numeric(df["peso"], errors="coerce").fillna(0)
        df["indicador_recurso"] = pd.to_numeric(df["indicador_recurso"], errors="coerce").fillna(1)
        for col in mes_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        return df, ""

    except Exception as e:
        return None, f"Error al leer el archivo: {str(e)}"


def df_a_actividades(df: pd.DataFrame) -> list[dict]:
    """
    Convierte el DataFrame leído a la lista de dicts que usan los módulos de lógica.
    """
    mes_cols = sorted([c for c in df.columns if c.startswith("mes_")])
    actividades = []
    for _, row in df.iterrows():
        actividades.append({
            "nombre": str(row["actividad"]),
            "peso": float(row["peso"]),
            "indicador": float(row["indicador_recurso"]),
            "distribucion": [float(row[c]) for c in mes_cols],
        })
    return actividades


def generar_template_excel(num_meses: int = 12, num_actividades: int = 5) -> bytes:
    """
    Genera un archivo Excel de plantilla para descargar.
    """
    meses = [f"mes_{i}" for i in range(num_meses + 1)]
    rows = []
    nombres = list("ABCDEFGHIJKLMNOP")
    for i in range(num_actividades):
        row = {
            "actividad": nombres[i],
            "peso": round(100 / num_actividades, 1),
            "indicador_recurso": 1.0,
        }
        for m in meses:
            row[m] = 0.0
        rows.append(row)

    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="actividades")

        # Hoja de instrucciones
        instrucciones = pd.DataFrame({
            "Campo": ["actividad", "peso", "indicador_recurso", "mes_0 ... mes_N"],
            "Descripción": [
                "Nombre de la actividad (texto)",
                "Peso presupuestario en % (suma recomendada: 100)",
                "Recurso por unidad (HH/m², kg/m², etc.)",
                "Distribución porcentual del avance en cada mes (suma por fila recomendada: 100)",
            ],
            "Ejemplo": ["Fundaciones", "25", "1.5", "0 / 5 / 20 / 30 / 25 / 20 / 0 ..."],
        })
        instrucciones.to_excel(writer, index=False, sheet_name="instrucciones")

    return buf.getvalue()


def actividades_a_df(actividades: list[dict]) -> pd.DataFrame:
    """
    Convierte lista de actividades a DataFrame exportable.
    """
    if not actividades:
        return pd.DataFrame()
    num_meses = len(actividades[0]["distribucion"])
    rows = []
    for act in actividades:
        row = {
            "actividad": act["nombre"],
            "peso": act["peso"],
            "indicador_recurso": act["indicador"],
        }
        for m, v in enumerate(act["distribucion"]):
            row[f"mes_{m}"] = v
        rows.append(row)
    return pd.DataFrame(rows)
