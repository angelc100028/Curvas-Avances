import pandas as pd
import numpy as np


def calcular_capcp(
    actividades: list[dict],
    num_meses: int,
) -> pd.Series:
    """
    Curva de Avance Planificado a Costo Planificado (CAPCP).
    Avance planificado de cada actividad ponderado por su peso presupuestario.
    Retorna avance acumulado (%).
    """
    peso_total = sum(a["peso"] for a in actividades) or 1.0
    parcial = []
    for m in range(num_meses):
        aporte = sum(
            (a["distribucion"][m] if m < len(a["distribucion"]) else 0.0)
            * (a["peso"] / peso_total)
            for a in actividades
        )
        parcial.append(aporte)
    acumulado = pd.Series(parcial, name="CAPCP").cumsum().round(4)
    acumulado.index.name = "mes"
    return acumulado


def calcular_carcp(
    avances_reales: pd.DataFrame,
    actividades: list[dict],
) -> pd.Series:
    """
    Curva de Avance Real a Costo Planificado (CARCP).
    Avance real de cada actividad ponderado por su peso presupuestario planificado.
    avances_reales: DataFrame [mes x actividad] con avances parciales reales (%)
    Retorna avance acumulado (%).
    """
    peso_total = sum(a["peso"] for a in actividades) or 1.0
    parcial = []
    for m in avances_reales.index:
        aporte = 0.0
        for act in actividades:
            nombre = act["nombre"]
            if nombre in avances_reales.columns:
                rv = avances_reales.loc[m, nombre] if not pd.isna(avances_reales.loc[m, nombre]) else 0.0
                aporte += rv * (act["peso"] / peso_total)
        parcial.append(aporte)
    acumulado = pd.Series(parcial, index=avances_reales.index, name="CARCP").cumsum().clip(upper=100).round(4)
    acumulado.index.name = "mes"
    return acumulado


def calcular_carcr(
    avances_reales: pd.DataFrame,
    actividades: list[dict],
    variaciones_costo: dict | None = None,
) -> pd.Series:
    """
    Curva de Avance Real a Costo Real (CARCR).
    Avance real ponderado por el impacto del costo real sobre el presupuesto total.
    variaciones_costo: dict {nombre_actividad: variacion_%} (ej: {'A': 10} = 10% más caro)
    Si no se provee, CARCR = CARCP (sin variación de costos).
    """
    if variaciones_costo is None:
        variaciones_costo = {}

    peso_total_plan = sum(a["peso"] for a in actividades) or 1.0
    costo_real_total = sum(
        a["peso"] * (1 + variaciones_costo.get(a["nombre"], 0.0) / 100.0)
        for a in actividades
    ) or 1.0

    parcial = []
    for m in avances_reales.index:
        aporte = 0.0
        for act in actividades:
            nombre = act["nombre"]
            if nombre in avances_reales.columns:
                rv = avances_reales.loc[m, nombre] if not pd.isna(avances_reales.loc[m, nombre]) else 0.0
                costo_real_act = act["peso"] * (1 + variaciones_costo.get(nombre, 0.0) / 100.0)
                aporte += rv * (costo_real_act / costo_real_total)
        parcial.append(aporte)

    acumulado = pd.Series(parcial, index=avances_reales.index, name="CARCR").cumsum().clip(upper=100).round(4)
    acumulado.index.name = "mes"
    return acumulado


def calcular_eficiencias(
    capcp: pd.Series,
    carcp: pd.Series,
    carcr: pd.Series,
    mes_actual: int,
) -> dict:
    """
    Calcula eficiencia física y económica en el mes actual.
    Eficiencia física = CARCP / CAPCP
    Eficiencia económica = CARCR / CAPCP
    """
    cap = capcp.get(mes_actual, 0) or 0
    car = carcp.get(mes_actual, 0) or 0
    carcr_val = carcr.get(mes_actual, 0) or 0

    ef_fisica = round((car / cap) * 100, 2) if cap > 0 else None
    ef_econ = round((carcr_val / cap) * 100, 2) if cap > 0 else None

    return {
        "mes_actual": mes_actual,
        "capcp": round(cap, 2),
        "carcp": round(car, 2),
        "carcr": round(carcr_val, 2),
        "eficiencia_fisica": ef_fisica,
        "eficiencia_economica": ef_econ,
        "adelanto_atraso": round(car - cap, 2),
    }


def tabla_control(
    capcp: pd.Series,
    carcp: pd.Series,
    carcr: pd.Series,
) -> pd.DataFrame:
    """Combina las tres curvas en un DataFrame de comparación."""
    df = pd.DataFrame({
        "CAPCP (%)": capcp.round(2),
        "CARCP (%)": carcp.round(2),
        "CARCR (%)": carcr.round(2),
    })
    df["Efic. física (%)"] = (df["CARCP (%)"] / df["CAPCP (%)"] * 100).round(1).where(df["CAPCP (%)"] > 0)
    df["Efic. económica (%)"] = (df["CARCR (%)"] / df["CAPCP (%)"] * 100).round(1).where(df["CAPCP (%)"] > 0)
    df.index.name = "mes"
    return df
