# 📈 Curvas de Avance — Gestión de Proyectos

Aplicación web para planificación y control de proyectos usando curvas de avance.  
Desarrollada con **Python + Streamlit**. Sin instalación: corre en Streamlit Cloud.

---

## Funcionalidades

### 📋 Actividades
- Define las actividades del proyecto, sus pesos presupuestarios, indicadores de recurso y distribución mensual
- Edición directa en tabla interactiva
- Carga desde archivo **Excel o CSV**
- Descarga de plantilla lista para completar

### 👷 Dotación de recursos
- Calcula la cantidad de recursos (personas, HH, equipos) necesarios por mes
- Curva de contratación con visualización por actividad y total

### 🏗️ Instalaciones
- Dimensiona el espacio de almacenamiento para materiales o insumos
- Configurable: indicador, días de stock, densidad de bodega
- Gráfico de consumo vs stock

### 📊 Curvas de control
- **CAPCP** — Avance Planificado a Costo Planificado (se genera automáticamente)
- **CARCP** — Avance Real a Costo Planificado (ingresa avances reales)
- **CARCR** — Avance Real a Costo Real (ingresa variaciones de costo)
- Cálculo automático de eficiencia física y económica

---

## Estructura del repositorio

```
curvas_avance/
├── app.py                  # App principal Streamlit
├── requirements.txt        # Dependencias
├── README.md
└── logic/
    ├── __init__.py
    ├── dotacion.py         # Cálculo de dotación de recursos
    ├── instalaciones.py    # Dimensionamiento de instalaciones
    ├── control.py          # Curvas CAPCP / CARCP / CARCR
    └── carga.py            # Lectura de Excel/CSV y plantillas
```

---

## Despliegue en Streamlit Cloud (gratuito)

1. **Sube este repositorio a GitHub** (puede ser público o privado)

2. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con tu cuenta de GitHub

3. Haz clic en **"New app"**

4. Selecciona:
   - Repositorio: el que acabas de subir
   - Branch: `main`
   - Main file path: `app.py`

5. Haz clic en **"Deploy"** — listo, en ~2 minutos tendrás la URL

---

## Correr localmente (opcional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Formato del archivo Excel/CSV de entrada

| actividad | peso | indicador_recurso | mes_0 | mes_1 | ... | mes_N |
|-----------|------|-------------------|-------|-------|-----|-------|
| A         | 30   | 1.0               | 0     | 4.17  | ... | 0     |
| B         | 25   | 0.8               | 0     | 0     | ... | 0     |

- `actividad`: nombre de la actividad
- `peso`: peso presupuestario en % (recomendado que sume 100)
- `indicador_recurso`: recurso por unidad (HH/m², kg/m², etc.)
- `mes_0` ... `mes_N`: distribución porcentual del avance (recomendado que cada fila sume 100)

> Usa el botón **"Descargar plantilla Excel"** en la app para obtener el formato correcto.

---

## Adaptación a otros sectores

La app es completamente genérica. Solo cambia:
- **Unidad de medida** (m², toneladas, unidades, km...)
- **Nombre del recurso** (HH, operadores, kg, equipos...)
- **Indicadores por actividad** según las estadísticas de tu empresa

Funciona para construcción, manufactura, software, energía, logística, salud, y cualquier proyecto con actividades paralelas.
