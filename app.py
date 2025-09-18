import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Información cualitativa Tolima",
    page_icon="data/ubicacion.png",  # ruta a tu imagen .png/.ico/.jpg
    layout="wide"
)
st.title("Datos cualitativos Tolima")
st.caption("Información cualitativa levantada con instrumentos de web Scraping y Análisis de redes Sociales")

# === Archivo fijo (ajusta nombre/ruta si lo necesitas) ===
DEFAULT_FILE = Path("data") / "Codificación WS Y ARS - Tolima.xlsx"

@st.cache_data
def read_excel(file, sheet_name=None):
    xls = pd.ExcelFile(file, engine="openpyxl")
    sheets = xls.sheet_names
    if sheet_name is None:
        sheet_name = sheets[0]
    df = xls.parse(sheet_name=sheet_name, dtype=str)
    return df, sheets

def available(col, df):
    return col in df.columns

def multiselect_if(col, df, label=None, key=None):
    if available(col, df):
        opts = sorted([x for x in df[col].dropna().unique() if str(x).strip() != ""])
        return st.sidebar.multiselect(label or col, opts, key=key)
    return []

def filter_by_selection(df, col, selected):
    if available(col, df) and selected:
        return df[df[col].isin(selected)]
    return df

# Cargar archivo fijo
if not DEFAULT_FILE.exists():
    st.error(f"No se encontró el archivo fijo en: {DEFAULT_FILE}. Inclúyelo en el repositorio.")
    st.stop()

df, sheets = read_excel(DEFAULT_FILE)
if len(sheets) > 1:
    st.sidebar.subheader("Hojas del archivo")
    selected_sheet = st.sidebar.selectbox("Selecciona la hoja", sheets, index=0)
    df, _ = read_excel(DEFAULT_FILE, sheet_name=selected_sheet)

# Limpiar espacios y unificar dtypes
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

#st.info(f"Fuente: {DEFAULT_FILE}")

st.sidebar.header("Filtros")
sel_depto = multiselect_if("Departamento", df, "Departamento", "depto")
sel_mpio = multiselect_if("Municipio", df, "Municipio", "mpio")
sel_enfoque = multiselect_if("Enfoque Turístico", df, "Enfoque Turístico", "enfoque")
sel_aspecto = multiselect_if("Aspecto", df, "Aspecto", "aspecto")
sel_sector = multiselect_if("Sector", df, "Sector", "sector")

df_f = df.copy()
df_f = filter_by_selection(df_f, "Departamento", sel_depto)
df_f = filter_by_selection(df_f, "Municipio", sel_mpio)
df_f = filter_by_selection(df_f, "Enfoque Turístico", sel_enfoque)
df_f = filter_by_selection(df_f, "Aspecto", sel_aspecto)
df_f = filter_by_selection(df_f, "Sector", sel_sector)

with st.sidebar.expander("Búsqueda por texto"):
    search_cols = [c for c in ["Nombre", "Actor", "Título", "Descripcion", "Descripción"] if available(c, df_f)]
    query = st.text_input("Contiene (min. 2 caracteres)")
    if query and len(query) >= 2 and search_cols:
        mask = False
        for c in search_cols:
            mask = (mask | df_f[c].fillna("").str.contains(query, case=False, na=False))
        df_f = df_f[mask]

kpi_cols = st.columns(4)
kpi_cols[0].metric("Filas filtradas", len(df_f))
if available("Departamento", df_f):
    kpi_cols[1].metric("Departamentos", df_f["Departamento"].nunique())
if available("Municipio", df_f):
    kpi_cols[2].metric("Municipios", df_f["Municipio"].nunique())
if available("Sector", df_f):
    kpi_cols[3].metric("Sectores", df_f["Sector"].nunique())

st.subheader("Tabla de resultados")
st.dataframe(df_f, use_container_width=True)

if available("Departamento", df_f):
    st.subheader("Distribución por Departamento")
    counts = df_f["Departamento"].value_counts().reset_index()
    counts.columns = ["Departamento", "Conteo"]
    st.bar_chart(counts.set_index("Departamento"))

csv_bytes = df_f.to_csv(index=False).encode("utf-8")
st.download_button("Descargar CSV filtrado", csv_bytes, file_name="datos_filtrados.csv", mime="text/csv")
