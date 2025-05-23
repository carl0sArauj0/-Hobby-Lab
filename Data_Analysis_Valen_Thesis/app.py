import streamlit as st
import pandas as pd
import plotly.express as px
import statsmodels.formula.api as smf
import folium
from streamlit_folium import st_folium

# ------------------------------
# Cargar datos
@st.cache_data
def load_data():
    df_w1 = pd.read_csv("ColombiaMAPSwave1_Public.csv", encoding='ISO-8859-1', low_memory=False)
    df_avg = pd.read_csv("ColombiaMAPSwave1_Public_municipality_average.csv", encoding='ISO-8859-1')
    df_all = pd.read_csv("MAPS public dataset Wave 1+2.csv", encoding='ISO-8859-1', low_memory=False)
    return df_w1, df_avg, df_all

df_w1, df_avg, df_all = load_data()
st.write("Columnas disponibles en df_avg:", df_avg.columns.tolist())

# ------------------------------
# Título principal
st.title("📊 Análisis de Implementación de Paz en Zonas PDET")

st.markdown("""
Esta aplicación permite explorar:
- Cambios de percepción entre olas.
- Relación entre implementación de paz y desarrollo.
- Modelos de regresión y diferencias en diferencias.
""")

# ------------------------------
# Filtro por departamento
st.sidebar.header("🎛️ Filtros")
departamentos = df_avg["p4_departamento"].dropna().unique()
selected_depto = st.sidebar.selectbox("Filtrar por departamento:", ["Todos"] + sorted(departamentos.tolist()))

df_avg_filtered = df_avg if selected_depto == "Todos" else df_avg[df_avg["p4_departamento"] == selected_depto]

# ------------------------------
# Visualización de variable
st.header("1. Distribución de variable municipal")

var = st.selectbox("Selecciona la variable:", options=df_avg.columns[3:])
fig = px.histogram(df_avg_filtered, x=var, nbins=30, title=f"Distribución de {var}")
st.plotly_chart(fig)

# ------------------------------
# Regresión lineal
st.header("2. Regresión lineal")

y_var = st.selectbox("Variable dependiente (Y)", df_avg.columns[3:], key="y_var")
x_vars = st.multiselect("Variables independientes (X)", df_avg.columns[3:], default=[df_avg.columns[4]])

if x_vars:
    formula = f"{y_var} ~ {' + '.join(x_vars)}"
    st.code(f"Fórmula: {formula}")
    model = smf.ols(formula=formula, data=df_avg_filtered).fit()
    st.text(model.summary())

    st.markdown(f"""
    - **R²**: {model.rsquared:.3f} (proporción explicada)
    - **Coeficientes** positivos = relación directa; negativos = inversa
    - **p-valores < 0.05** indican efecto estadísticamente significativo
    """)

    st.markdown("### Gráficos:")
    for x in x_vars:
        fig = px.scatter(df_avg_filtered, x=x, y=y_var, trendline="ols", title=f"{y_var} vs. {x}")
        st.plotly_chart(fig)

# ------------------------------
# Regresiones por departamento
st.header("3. Regresión por departamento")

dep_var = st.selectbox("Y variable", df_avg.columns[3:], key="dep_var_dept")
indep_var = st.selectbox("X variable", df_avg.columns[3:], key="indep_var_dept")

dept_results = []
for depto in df_avg["p4_departamento"].dropna().unique():
    sub_df = df_avg[df_avg["p4_departamento"] == depto]
    try:
        model = smf.ols(f"{dep_var} ~ {indep_var}", data=sub_df).fit()
        dept_results.append({
            "Departamento": depto,
            "Coeficiente": model.params[indep_var],
            "p-valor": model.pvalues[indep_var]
        })
    except:
        continue

df_coef = pd.DataFrame(dept_results)
st.dataframe(df_coef.sort_values("Coeficiente", ascending=False), use_container_width=True)

fig = px.bar(df_coef, x="Departamento", y="Coeficiente", color="p-valor",
             color_continuous_scale="RdBu", title=f"Efecto de {indep_var} sobre {dep_var}")
st.plotly_chart(fig)

# ------------------------------
# Mapa interactivo
st.header("4. 🗺️ Mapa por municipio")

map_var = st.selectbox("Variable a mapear:", df_avg_filtered.columns[3:])

if "latitude" in df_avg_filtered.columns and "longitude" in df_avg_filtered.columns:
    m = folium.Map(location=[4.5, -74], zoom_start=6)
    for _, row in df_avg_filtered.iterrows():
        folium.CircleMarker(
            location=(row["latitude"], row["longitude"]),
            radius=6,
            fill=True,
            fill_color="blue",
            tooltip=f"{row['p5_municipio']}: {row[map_var]}"
        ).add_to(m)
    st_data = st_folium(m, width=700, height=500)
else:
    st.warning("No se encontraron columnas 'latitude' y 'longitude' para generar el mapa.")

# ------------------------------
# Diferencias en diferencias
st.header("5. 📉 Diferencias en Diferencias")

st.markdown("""
Este modelo estima el efecto del acuerdo de paz sobre una variable como el PIB o desempleo,
comparando zonas PDET y no PDET antes y después del acuerdo.
""")

diff_y = st.selectbox("Variable dependiente para DiD", df_avg.columns[3:], key="did_y")

if {'pdet', 'post'}.issubset(df_avg.columns):
    formula_did = f"{diff_y} ~ pdet * post"
    st.code(f"Modelo: {formula_did}")
    model_did = smf.ols(formula=formula_did, data=df_avg).fit()
    st.text(model_did.summary())

    st.markdown(f"""
    - El coeficiente de `pdet:post` representa el **efecto diferencial** del acuerdo de paz.
    - Si es positivo y significativo, indica mejora en zonas PDET **mayor que** en otras.
    """)
else:
    st.warning("Tu base debe contener columnas 'pdet' (zona priorizada) y 'post' (año posterior al acuerdo).")

# ------------------------------
# Comparación entre olas (individual)
st.header("6. Comparación entre Olas (individuales)")

if "wave" in df_all.columns:
    var_ind = st.selectbox("Variable individual", options=[
        col for col in df_all.columns if df_all[col].dtype in ["float64", "int64"]
    ])
    fig = px.box(df_all, x="wave", y=var_ind, points="all",
                 title=f"{var_ind} por ola", color="wave")
    st.plotly_chart(fig)
else:
    st.warning("La base de datos no tiene columna 'wave'.")

df_w1, df_avg, df_all = load_data()
st.write("Columnas disponibles en df_avg:", df_avg.columns.tolist())
