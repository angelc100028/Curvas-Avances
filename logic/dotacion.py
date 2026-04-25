import numpy as np
import pandas as pd


def calcular_equivalentes(actividades: list[dict], qty_total: float) -> pd.DataFrame:
    """
    Para cada actividad calcula el equivalente en unidades de avance parcial por mes.
    actividades: lista de dicts con keys: nombre, distribucion (list % por mes)
    qty_total: cantidad total de unidades del proyecto
    Retorna DataFrame [mes x actividad]
    """
    meses = len(actividades[0]["distribucion"])
    data = {}
    for act in actividades:
        data[act["nombre"]] = [
            (pct / 100.0) * qty_total for pct in act["distribucion"]
        ]
    df = pd.DataFrame(data, index=range(meses))
    df.index.name = "mes"
    return df


def calcular_hd(equiv_df: pd.DataFrame, actividades: list[dict]) -> pd.DataFrame:
    """
    Aplica el indicador de recurso a los equivalentes para obtener HD (recurso) por mes.
    """
    hd = equiv_df.copy()
    for act in actividades:
        hd[act["nombre"]] = equiv_df[act["nombre"]] * act["indicador"]
    return hd


def calcular_dotacion(hd_df: pd.DataFrame, dias_mes: int) -> pd.DataFrame:
    """
    Convierte HD a unidades de recurso (personas/equipos) dividiendo por días laborales
    y redondeando hacia arriba.
    """
    return hd_df.apply(lambda col: np.ceil(col / dias_mes).astype(int))


def calcular_total(dotacion_df: pd.DataFrame) -> pd.Series:
    """Suma total de recursos por mes."""
    return dotacion_df.sum(axis=1)


def resumen_dotacion(actividades: list[dict], qty_total: float, dias_mes: int) -> dict:
    """
    Ejecuta el pipeline completo y retorna dict con todos los DataFrames y métricas.
    """
    equiv = calcular_equivalentes(actividades, qty_total)
    hd = calcular_hd(equiv, actividades)
    dotacion = calcular_dotacion(hd, dias_mes)
    total = calcular_total(dotacion)

    return {
        "equivalentes": equiv,
        "hd": hd,
        "dotacion": dotacion,
        "total": total,
        "pico": int(total.max()),
        "mes_pico": int(total.idxmax()),
        "total_acumulado": int(total.sum()),
        "promedio_mensual": round(total.mean(), 1),
    }
