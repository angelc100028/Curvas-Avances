import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io

from logic.carga import (
    leer_archivo, df_a_actividades, generar_template_excel, actividades_a_df
)
from logic.dotacion import resumen_dotacion
from logic.instalaciones import resumen_instalacion
from logic.control import (
    calcular_capcp, calcular_carcp, calcular_carcr,
    calcular_eficiencias, tabla_control
)

# ─────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Curvas de Avance",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .metric-label { font-size: 0.8rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 6px 20px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# ESTADO DE SESIÓN
# ─────────────────────────────────────────
def init_state():
    defaults = {
        "actividades": [
            {"nombre": "A", "peso": 30.0, "indicador": 1.0,
             "distribucion": [0,4.17,12.50,20.83,25.00,20.83,12.50,4.17,0,0,0,0,0]},
            {"nombre": "B", "peso": 25.0, "indicador": 0.8,
             "distribucion": [0,0,3.13,9.38,15.63,21.88,21.88,15.63,9.38,3.13,0,0,0]},
            {"nombre": "C", "peso": 20.0, "indicador": 1.2,
             "distribucion": [0,0,0,0,4.17,12.50,20.83,25.00,20.83,12.50,4.17,0,0]},
            {"nombre": "D", "peso": 15.0, "indicador": 1.5,
             "distribucion": [0,0,0,0,0,0,4.17,12.50,20.83,25.00,20.83,12.50,4.17]},
            {"nombre": "E", "peso": 10.0, "indicador": 1.0,
             "distribucion": [0,0,0,0,0,0,4.35,13.04,21.74,21.74,26.09,21.74,13.04]},
        ],
        "qty_total": 400.0,
        "dias_mes": 20,
        "unidad": "m²",
        "nombre_recurso": "HH",
        "proyecto": "Mi Proyecto",
        "avances_reales": {},
        "variaciones_costo": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────
# SIDEBAR — CONFIGURACIÓN GLOBAL
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Proyecto")
    st.session_state["proyecto"] = st.text_input("Nombre del proyecto", st.session_state["proyecto"])
    st.session_state["unidad"] = st.text_input("Unidad de medida", st.session_state["unidad"])
    st.session_state["qty_total"] = st.number_input("Cantidad total de unidades", min_value=1.0, value=st.session_state["qty_total"], step=10.0)
    st.session_state["dias_mes"] = st.number_input("Días laborales por mes", min_value=1, max_value=31, value=st.session_state["dias_mes"])
    st.session_state["nombre_recurso"] = st.text_input("Nombre del recurso (HH, kg, etc.)", st.session_state["nombre_recurso"])

    st.divider()
    st.markdown("## 📥 Cargar datos")
    template_bytes = generar_template_excel(
        num_meses=len(st.session_state["actividades"][0]["distribucion"]) - 1,
        num_actividades=len(st.session_state["actividades"])
    )
    st.download_button(
        "⬇ Descargar plantilla Excel",
        data=template_bytes,
        file_name="plantilla_curvas_avance.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    uploaded = st.file_uploader("Subir Excel / CSV", type=["xlsx", "xls", "csv"])
    if uploaded:
        df_cargado, error = leer_archivo(uploaded)
        if error:
            st.error(error)
        else:
            st.session_state["actividades"] = df_a_actividades(df_cargado)
            st.success(f"✅ {len(st.session_state['actividades'])} actividades cargadas")

    st.divider()
    st.markdown("## 💾 Exportar actividades")
    df_export = actividades_a_df(st.session_state["actividades"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        df_export.to_excel(w, index=False)
    st.download_button(
        "⬇ Exportar actividades actuales",
        data=buf.getvalue(),
        file_name="actividades_proyecto.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


# ─────────────────────────────────────────
# TÍTULO
# ─────────────────────────────────────────
st.title(f"📈 {st.session_state['proyecto']}")
st.caption("Curvas de avance · Planificación y control de proyectos")

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Actividades",
    "👷 Dotación de recursos",
    "🏗️ Instalaciones",
    "📊 Curvas de control",
])


# ─────────────────────────────────────────
# TAB 1 — ACTIVIDADES
# ─────────────────────────────────────────
with tab1:
    st.subheader("Configuración de actividades")
    actividades = st.session_state["actividades"]
    num_meses = len(actividades[0]["distribucion"]) - 1

    col_add, col_rem, col_meses = st.columns([1, 1, 2])
    with col_add:
        if st.button("➕ Agregar actividad"):
            nombre_nuevo = chr(65 + len(actividades))
            actividades.append({
                "nombre": nombre_nuevo,
                "peso": 0.0,
                "indicador": 1.0,
                "distribucion": [0.0] * (num_meses + 1),
            })
    with col_rem:
        if st.button("➖ Eliminar última") and len(actividades) > 1:
            actividades.pop()
    with col_meses:
        nuevo_dur = st.number_input("Duración del proyecto (meses)", min_value=2, max_value=60, value=num_meses)
        if nuevo_dur != num_meses:
            for act in actividades:
                dist = act["distribucion"]
                if nuevo_dur + 1 > len(dist):
                    act["distribucion"] = dist + [0.0] * (nuevo_dur + 1 - len(dist))
                else:
                    act["distribucion"] = dist[:nuevo_dur + 1]

    st.markdown("**Edita directamente en la tabla:**")
    meses_header = [f"Mes {m}" for m in range(nuevo_dur + 1)]
    df_edit = pd.DataFrame([
        {
            "Actividad": act["nombre"],
            "Peso %": act["peso"],
            f"Indicador ({st.session_state['nombre_recurso']}/{st.session_state['unidad']})": act["indicador"],
            **{meses_header[m]: act["distribucion"][m] for m in range(nuevo_dur + 1)},
        }
        for act in actividades
    ])

    edited = st.data_editor(
        df_edit,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_actividades",
    )

    # Sincronizar cambios del editor
    actividades_sync = []
    for _, row in edited.iterrows():
        nombre = str(row.get("Actividad", "?"))
        peso = float(row.get("Peso %", 0) or 0)
        ind_col = f"Indicador ({st.session_state['nombre_recurso']}/{st.session_state['unidad']})"
        indicador = float(row.get(ind_col, 1) or 1)
        dist = [float(row.get(f"Mes {m}", 0) or 0) for m in range(nuevo_dur + 1)]
        actividades_sync.append({"nombre": nombre, "peso": peso, "indicador": indicador, "distribucion": dist})
    st.session_state["actividades"] = actividades_sync

    # Validaciones
    peso_total = sum(a["peso"] for a in actividades_sync)
    if abs(peso_total - 100) > 0.5:
        st.warning(f"⚠️ La suma de pesos es {peso_total:.1f}%. Se recomienda que sume 100%.")
    else:
        st.success(f"✅ Suma de pesos: {peso_total:.1f}%")

    for act in actividades_sync:
        suma_dist = sum(act["distribucion"])
        if abs(suma_dist - 100) > 1:
            st.warning(f"⚠️ Actividad **{act['nombre']}**: distribución suma {suma_dist:.1f}% (se esperan ~100%)")


# ─────────────────────────────────────────
# TAB 2 — DOTACIÓN
# ─────────────────────────────────────────
with tab2:
    st.subheader("Dotación de recursos por mes")
    actividades = st.session_state["actividades"]

    try:
        res = resumen_dotacion(
            actividades,
            st.session_state["qty_total"],
            st.session_state["dias_mes"],
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Pico de dotación", f"{res['pico']} {st.session_state['nombre_recurso']}", f"Mes {res['mes_pico']}")
        col2.metric("Total acumulado", f"{res['total_acumulado']:,}")
        col3.metric("Promedio mensual", f"{res['promedio_mensual']:.1f}")
        col4.metric("Actividades", len(actividades))

        st.markdown("#### Tabla de dotación mensual")
        dot_df = res["dotacion"].copy()
        dot_df["Total"] = res["total"]
        dot_df.index.name = "Mes"
        st.dataframe(dot_df.style.highlight_max(axis=0, color="#d4f4e8"), use_container_width=True)

        st.markdown("#### Curva de contratación")
        fig = go.Figure()
        colores = ["#1D9E75", "#378ADD", "#D85A30", "#BA7517", "#9333EA", "#E91E8C", "#00BCD4", "#FF5722"]
        for i, act in enumerate(actividades):
            fig.add_trace(go.Scatter(
                x=list(res["dotacion"].index),
                y=res["dotacion"][act["nombre"]].tolist(),
                name=act["nombre"],
                mode="lines+markers",
                line=dict(color=colores[i % len(colores)], width=1.5),
                marker=dict(size=5),
            ))
        fig.add_trace(go.Scatter(
            x=list(res["total"].index),
            y=res["total"].tolist(),
            name="Total",
            mode="lines+markers",
            line=dict(color="#1a1a1a", width=3),
            marker=dict(size=7),
        ))
        fig.update_layout(
            xaxis_title="Mes",
            yaxis_title=st.session_state["nombre_recurso"],
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            height=400,
            margin=dict(t=60, b=40),
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error al calcular dotación: {e}")


# ─────────────────────────────────────────
# TAB 3 — INSTALACIONES
# ─────────────────────────────────────────
with tab3:
    st.subheader("Dimensionamiento de instalaciones")
    actividades = st.session_state["actividades"]
    nombres_acts = [a["nombre"] for a in actividades]

    with st.expander("⚙️ Configuración del material / insumo", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            nombre_item = st.text_input("Nombre del ítem (ej: sacos de cemento, toneladas de acero)", "Material principal")
            indicador_inst = st.number_input(
                f"Indicador ({nombre_item}/{st.session_state['unidad']})",
                min_value=0.001, value=5.0, step=0.1, format="%.3f"
            )
            acts_selec = st.multiselect(
                "Actividades que consumen este material",
                options=nombres_acts,
                default=nombres_acts[:3],
            )
        with col2:
            dias_stock = st.number_input("Días de stock (pedido cada N días)", min_value=1, max_value=90, value=15)
            dens = st.number_input(f"Unidades de {nombre_item} por m² de bodega", min_value=0.01, value=60.0, step=1.0)

    if acts_selec:
        try:
            from logic.dotacion import calcular_equivalentes
            equiv_df = calcular_equivalentes(actividades, st.session_state["qty_total"])

            res_inst = resumen_instalacion(
                equiv_df=equiv_df,
                actividades_filtro=acts_selec,
                indicador=indicador_inst,
                dias_stock=dias_stock,
                dias_mes=st.session_state["dias_mes"],
                unidades_por_m2=dens,
                nombre_item=nombre_item,
            )

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Tamaño de bodega", f"{res_inst['tamano_bodega_m2']} m²")
            col2.metric("Stock máximo", f"{res_inst['stock_maximo']:,} {nombre_item}")
            col3.metric("Mes pico", f"Mes {res_inst['mes_pico']}")
            col4.metric("Consumo total", f"{res_inst['consumo_total']:,.0f} {nombre_item}")

            st.markdown("#### Consumo y stock mensual")
            st.dataframe(res_inst["tabla"].style.highlight_max(color="#d4f4e8"), use_container_width=True)

            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=list(res_inst["consumo"].index),
                y=res_inst["consumo"].round(1).tolist(),
                name="Consumo mensual",
                marker_color="#1D9E7566",
                marker_line_color="#1D9E75",
                marker_line_width=1.5,
            ))
            fig2.add_trace(go.Scatter(
                x=list(res_inst["stock"].index),
                y=res_inst["stock"].tolist(),
                name="Stock en bodega",
                mode="lines+markers",
                line=dict(color="#D85A30", width=2.5),
                marker=dict(size=6),
            ))
            fig2.update_layout(
                xaxis_title="Mes",
                yaxis_title=nombre_item,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                height=380,
                margin=dict(t=60, b=40),
            )
            st.plotly_chart(fig2, use_container_width=True)

        except Exception as e:
            st.error(f"Error al calcular instalaciones: {e}")
    else:
        st.info("Selecciona al menos una actividad para calcular.")


# ─────────────────────────────────────────
# TAB 4 — CURVAS DE CONTROL
# ─────────────────────────────────────────
with tab4:
    st.subheader("Curvas de control — CAPCP / CARCP / CARCR")
    actividades = st.session_state["actividades"]
    num_meses = len(actividades[0]["distribucion"])

    capcp = calcular_capcp(actividades, num_meses)

    st.markdown("#### Avances reales por actividad (%)")
    st.caption("Ingresa el avance real **parcial** de cada actividad en cada mes (0–100%)")

    meses_visibles = list(range(1, num_meses))
    ar_data = {
        act["nombre"]: [
            st.session_state["avances_reales"].get(f"{act['nombre']}_{m}", 0.0)
            for m in meses_visibles
        ]
        for act in actividades
    }
    df_ar = pd.DataFrame(ar_data, index=meses_visibles)
    df_ar.index.name = "Mes"

    df_ar_edited = st.data_editor(
        df_ar,
        use_container_width=True,
        key="editor_avances_reales",
    )

    # Guardar en session state
    for act in actividades:
        for m in meses_visibles:
            val = df_ar_edited.loc[m, act["nombre"]] if m in df_ar_edited.index else 0.0
            st.session_state["avances_reales"][f"{act['nombre']}_{m}"] = float(val or 0)

    # Reconstruir df avances reales con mes 0
    ar_full = pd.DataFrame(
        {act["nombre"]: [0.0] + [
            st.session_state["avances_reales"].get(f"{act['nombre']}_{m}", 0.0)
            for m in meses_visibles
        ] for act in actividades},
        index=range(num_meses),
    )

    st.markdown("#### Variaciones de costo real (opcional)")
    with st.expander("Ingresar variaciones de costo por actividad (%)"):
        st.caption("Ingresa la variación % del costo real respecto al planificado. Ej: 10 = 10% más caro")
        var_cols = st.columns(len(actividades))
        for i, act in enumerate(actividades):
            with var_cols[i]:
                v = st.number_input(
                    act["nombre"],
                    value=float(st.session_state["variaciones_costo"].get(act["nombre"], 0.0)),
                    step=1.0,
                    key=f"var_{act['nombre']}",
                )
                st.session_state["variaciones_costo"][act["nombre"]] = v

    try:
        carcp = calcular_carcp(ar_full, actividades)
        carcr = calcular_carcr(ar_full, actividades, st.session_state["variaciones_costo"])

        # Métricas al mes más avanzado con datos reales
        mes_actual = max([m for m in range(num_meses) if carcp.get(m, 0) > 0], default=0)
        efic = calcular_eficiencias(capcp, carcp, carcr, mes_actual)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Mes actual", f"Mes {mes_actual}")
        col2.metric("CAPCP", f"{efic['capcp']:.1f}%")
        col3.metric("CARCP", f"{efic['carcp']:.1f}%")
        delta_fisica = f"{efic['eficiencia_fisica']:.1f}%" if efic['eficiencia_fisica'] else "—"
        delta_econ = f"{efic['eficiencia_economica']:.1f}%" if efic['eficiencia_economica'] else "—"
        col4.metric("Efic. física", delta_fisica,
                    delta=f"{efic['adelanto_atraso']:+.1f}% vs plan" if efic['eficiencia_fisica'] else None)
        col5.metric("Efic. económica", delta_econ)

        # Gráfico de las 3 curvas
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=list(capcp.index), y=capcp.tolist(),
            name="CAPCP — Planificado/Planificado",
            mode="lines+markers",
            line=dict(color="#378ADD", width=2.5),
            marker=dict(size=6),
        ))
        fig3.add_trace(go.Scatter(
            x=list(carcp.index), y=carcp.tolist(),
            name="CARCP — Real/Planificado",
            mode="lines+markers",
            line=dict(color="#1D9E75", width=2.5, dash="dash"),
            marker=dict(size=6),
        ))
        fig3.add_trace(go.Scatter(
            x=list(carcr.index), y=carcr.tolist(),
            name="CARCR — Real/Real",
            mode="lines+markers",
            line=dict(color="#D85A30", width=2.5, dash="dot"),
            marker=dict(size=6),
        ))
        if mes_actual > 0:
            fig3.add_vline(
                x=mes_actual,
                line_dash="dot",
                line_color="gray",
                annotation_text=f"Hoy: Mes {mes_actual}",
                annotation_position="top right",
            )
        fig3.update_layout(
            xaxis_title="Mes",
            yaxis_title="Avance acumulado (%)",
            yaxis=dict(range=[0, 105], ticksuffix="%"),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=420,
            margin=dict(t=80, b=40),
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("#### Tabla comparativa")
        ctrl_df = tabla_control(capcp, carcp, carcr)
        st.dataframe(
            ctrl_df.style
                .format("{:.2f}", subset=["CAPCP (%)", "CARCP (%)", "CARCR (%)"])
                .format("{:.1f}", subset=["Efic. física (%)", "Efic. económica (%)"])
                .applymap(lambda v: "color: #1D9E75" if isinstance(v, float) and v >= 100
                          else ("color: #D85A30" if isinstance(v, float) and v < 90 else ""),
                          subset=["Efic. física (%)", "Efic. económica (%)"]),
            use_container_width=True,
        )

        st.markdown("#### Interpretación")
        if mes_actual > 0 and efic["eficiencia_fisica"] is not None:
            ef = efic["eficiencia_fisica"]
            ee = efic["eficiencia_economica"]
            if ef >= 100 and ee >= 100:
                st.success("✅ El proyecto va **adelantado** en plazo y **dentro del presupuesto**.")
            elif ef >= 100 and ee < 100:
                st.warning("⚠️ El proyecto va adelantado en plazo pero con **sobrecosto**.")
            elif ef < 100 and ee >= 100:
                st.warning("⚠️ El proyecto está **atrasado** en plazo pero dentro del presupuesto.")
            else:
                st.error("❌ El proyecto está **atrasado** y con **sobrecosto**.")
        else:
            st.info("Ingresa avances reales para ver el análisis.")

    except Exception as e:
        st.error(f"Error al calcular curvas de control: {e}")
