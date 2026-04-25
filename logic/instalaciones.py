import math
import pandas as pd


def calcular_consumo_mensual(
    equiv_df: pd.DataFrame,
    actividades_filtro: list[str],
    indicador: float,
) -> pd.Series:
    """
    Calcula el consumo mensual de un material/insumo sumando
    las actividades seleccionadas multiplicadas por el indicador.
    """
    cols = [c for c in equiv_df.columns if c in actividades_filtro]
    if not cols:
        return pd.Series(0.0, index=equiv_df.index)
    return equiv_df[cols].sum(axis=1) * indicador


def calcular_stock_bodega(
    consumo: pd.Series,
    dias_stock: int,
    dias_mes: int,
) -> pd.Series:
    """
    Calcula el stock requerido en bodega para cubrir N días de consumo.
    stock = consumo_mensual * (dias_stock / dias_mes)
    """
    return (consumo * (dias_stock / dias_mes)).apply(math.ceil)


def calcular_tamano_bodega(
    stock: pd.Series,
    unidades_por_m2: float,
) -> int:
    """
    Determina el tamaño de bodega en m² a partir del stock máximo.
    """
    return math.ceil(stock.max() / unidades_por_m2)


def resumen_instalacion(
    equiv_df: pd.DataFrame,
    actividades_filtro: list[str],
    indicador: float,
    dias_stock: int,
    dias_mes: int,
    unidades_por_m2: float,
    nombre_item: str = "material",
) -> dict:
    """Pipeline completo para dimensionamiento de instalaciones."""
    consumo = calcular_consumo_mensual(equiv_df, actividades_filtro, indicador)
    stock = calcular_stock_bodega(consumo, dias_stock, dias_mes)
    tamano = calcular_tamano_bodega(stock, unidades_por_m2)

    tabla = pd.DataFrame({
        "Consumo mensual": consumo.round(1),
        "Stock en bodega": stock,
    })
    tabla.index.name = "mes"

    return {
        "tabla": tabla,
        "consumo": consumo,
        "stock": stock,
        "tamano_bodega_m2": tamano,
        "stock_maximo": int(stock.max()),
        "mes_pico": int(stock.idxmax()),
        "consumo_total": round(consumo.sum(), 1),
        "nombre_item": nombre_item,
    }
