# app.py
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ================== CONFIG BÁSICA ==================
st.set_page_config(
    page_title="Información cualitativa Tolima",
    page_icon="data/ubicacion.png",
    layout="wide"
)

# ---- Estilos (CSS) ----
st.markdown("""
<style>
section[data-testid="stSidebar"] { width: 320px !important; }
.kpi-card {
  border-radius: 16px; padding: 16px 18px; border: 1px solid rgba(0,0,0,0.06);
  background: linear-gradient(180deg, rgba(250,250,250,1) 0%, rgba(245,245,245,1) 100%);
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.kpi-title { font-size: 12px; color: #666; margin: 0; }
.kpi-value { font-size: 28px; font-weight: 700; margin: 2px 0 0 0; }

.card {
  border-radius: 14px; padding: 14px 16px; border: 1px solid rgba(0,0,0,0.08);
  background: #fff; box-shadow: 0 1px 2px rgba(0,0,0,0.03); margin-bottom: 10px;
}
.card h4 { margin: 0 0 6px 0; }
.small { color:#64748b; font-size: 12px; }
.badge {
  display:inline-block; padding:3px 8px; border-radius:999px; background:#eef2ff; color:#3730a3;
  border:1px solid #e0e7ff; font-size:12px; margin-right:6px;
}
</style>
""", unsafe_allow_html=True)

# ================== ENCABEZADO ==================
col_logo, col_title = st.columns([1, 6], vertical_alignment="center")
with col_logo:
    try:
        st.image("data/ubicacion.png", width=64)
    except Exception:
        pass
with col_title:
    st.title("Datos cualitativos – Tolima")
    st.caption("Información cualitativa levantada con instrumentos de **Web Scraping** y **Análisis de Redes Sociales**")

st.divider()

# ================== CARGA DE DATOS ==================
DEFAULT_FILE = Path("data") / "Codificación WS Y ARS - Tolima.xlsx"

@st.cache_data(show_spinner=False)
def read_excel(file: Path, sheet_name=None):
    xls = pd.ExcelFile(file, engine="openpyxl")
    sheets = xls.sheet_names
    if sheet_name is None:
        sheet_name = sheets[0]
    df = xls.parse(sheet_name=sheet_name, dtype=str)
    return df, sheets

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Normaliza espacios/acentos y unifica nombres comunes
    df.columns = df.columns.str.strip()
    aliases = {
        "DEPARTAMENTO": "Departamento",
        "Departamento ": "Departamento",
        "MUNICIPIO": "Municipio",
        "ENFOQUE TURÍSTICO": "Enfoque Turístico",
        "ENFOQUE TURISTICO": "Enfoque Turístico",
        "DESCRIPCIÓN": "Descripción",
        "Descripcion": "Descripción",
        "TITULO": "Título",
        "ACTOR": "Actor",
        "SECTOR": "Sector",
        "ASPECTO": "Aspecto",
        "NOMBRE": "Nombre",
    }
    df.rename(columns={k: v for k, v in aliases.items() if k in df.columns}, inplace=True)
    # Limpieza de strings
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    return df

def available(col, df):
    return col in df.columns

def options_sorted(series):
    return sorted([x for x in series.dropna().astype(str).str.strip().unique() if x != ""])

def multiselect_if(col, df, label=None, key=None):
    if available(col, df):
        opts = options_sorted(df[col])
        return st.sidebar.multiselect(label or col, opts, key=key)
    return []

def filter_by_selection(df, col, selected):
    if available(col, df) and selected:
        return df[df[col].isin(selected)]
    return df

if not DEFAULT_FILE.exists():
    st.error(f"⚠️ No se encontró el archivo fijo en: {DEFAULT_FILE}\n\nInclúyelo en el repositorio (carpeta **data/**).")
    st.stop()

df, sheets = read_excel(DEFAULT_FILE)
selected_sheet = sheets[0]
if len(sheets) > 1:
    st.sidebar.subheader("Hojas del archivo")
    selected_sheet = st.sidebar.selectbox("Selecciona la hoja", sheets, index=0)
    df, _ = read_excel(DEFAULT_FILE, sheet_name=selected_sheet)

df = normalize_columns(df)

# ================== FILTROS ==================
st.sidebar.header("Filtros")
col_btn, _ = st.sidebar.columns([1,1])
do_reset = col_btn.button("🔄 Limpiar filtros")
df_f = df.copy()

if not do_reset:
    sel_depto   = multiselect_if("Departamento", df, "Departamento", "depto")
    sel_mpio    = multiselect_if("Municipio", df, "Municipio", "mpio")
    sel_enfoque = multiselect_if("Enfoque Turístico", df, "Enfoque Turístico", "enfoque")
    sel_aspecto = multiselect_if("Aspecto", df, "Aspecto", "aspecto")
    sel_sector  = multiselect_if("Sector", df, "Sector", "sector")
else:
    sel_depto = sel_mpio = sel_enfoque = sel_aspecto = sel_sector = []

df_f = filter_by_selection(df_f, "Departamento", sel_depto)
df_f = filter_by_selection(df_f, "Municipio", sel_mpio)
df_f = filter_by_selection(df_f, "Enfoque Turístico", sel_enfoque)
df_f = filter_by_selection(df_f, "Aspecto", sel_aspecto)
df_f = filter_by_selection(df_f, "Sector", sel_sector)

with st.sidebar.expander("🔎 Búsqueda por texto", expanded=False):
    search_cols = [c for c in ["Nombre", "Actor", "Título", "Descripción"] if available(c, df_f)]
    query = st.text_input("Contiene (min. 2 caracteres)")
    if query and len(query) >= 2 and search_cols:
        mask = False
        for c in search_cols:
            mask = (mask | df_f[c].fillna("").astype(str).str.contains(query, case=False, na=False))
        df_f = df_f[mask]

# ================== KPIs ==================
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f'<div class="kpi-card"><p class="kpi-title">Filas filtradas</p><p class="kpi-value">{len(df_f):,}</p></div>', unsafe_allow_html=True)
with c2:
    if available("Departamento", df_f):
        st.markdown(f'<div class="kpi-card"><p class="kpi-title">Departamentos</p><p class="kpi-value">{df_f["Departamento"].nunique():,}</p></div>', unsafe_allow_html=True)
with c3:
    if available("Municipio", df_f):
        st.markdown(f'<div class="kpi-card"><p class="kpi-title">Municipios</p><p class="kpi-value">{df_f["Municipio"].nunique():,}</p></div>', unsafe_allow_html=True)
with c4:
    if available("Sector", df_f):
        st.markdown(f'<div class="kpi-card"><p class="kpi-title">Sectores</p><p class="kpi-value">{df_f["Sector"].nunique():,}</p></div>', unsafe_allow_html=True)

st.caption(f"Fuente: **{DEFAULT_FILE.name}** · Hoja: **{selected_sheet}**")
st.divider()

# ================== TABS PRINCIPALES ==================
tab_resumen, tab_tabla, tab_explorar, tab_barras = st.tabs([
    "📌 Resumen",
    "📋 Tabla interactiva",
    "🗺️ Explorador (Treemap/Sunburst)",
    "📊 Barras"
])

# --------- RESUMEN ----------
with tab_resumen:
    # Pequeños rankings
    cols = st.columns(3)
    if available("Aspecto", df_f) and not df_f["Aspecto"].dropna().empty:
        top_aspecto = df_f["Aspecto"].value_counts().head(5).reset_index()
        top_aspecto.columns = ["Aspecto", "Conteo"]
        with cols[0]:
            st.subheader("Top 5 Aspectos")
            st.dataframe(top_aspecto, use_container_width=True, hide_index=True)

    if available("Enfoque Turístico", df_f) and not df_f["Enfoque Turístico"].dropna().empty:
        top_enfoque = df_f["Enfoque Turístico"].value_counts().head(5).reset_index()
        top_enfoque.columns = ["Enfoque Turístico", "Conteo"]
        with cols[1]:
            st.subheader("Top 5 Enfoques")
            st.dataframe(top_enfoque, use_container_width=True, hide_index=True)

    if available("Municipio", df_f) and not df_f["Municipio"].dropna().empty:
        top_mpio = df_f["Municipio"].value_counts().head(5).reset_index()
        top_mpio.columns = ["Municipio", "Conteo"]
        with cols[2]:
            st.subheader("Top 5 Municipios")
            st.dataframe(top_mpio, use_container_width=True, hide_index=True)

# --------- TABLA (AgGrid) ----------
with tab_tabla:
    st.subheader("Tabla de resultados (interactiva)")
    if len(df_f) == 0:
        st.info("No hay filas con los filtros actuales. Ajusta filtros o limpia la búsqueda.")
    else:
        # Columnas largas como wrap
        col_defs_wrap = ["Descripción", "Titulo", "Título", "Actor", "Nombre"]
        for c in col_defs_wrap:
            if available(c, df_f):
                df_f[c] = df_f[c].astype(str)

        gb = GridOptionsBuilder.from_dataframe(df_f)
        gb.configure_default_column(
            filter=True, sortable=True, resizable=True, wrapText=True, autoHeight=True
        )
        gb.configure_grid_options(domLayout="normal")
        gb.configure_selection("multiple", use_checkbox=True, header_checkbox=True)
        grid_options = gb.build()

        grid = AgGrid(
            df_f,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            enable_enterprise_modules=False,
            fit_columns_on_grid_load=True,
            allow_unsafe_jscode=False,
            height=520, theme="balham"
        )

        sel_rows = grid["selected_rows"]
        st.download_button(
            "⬇️ Descargar CSV filtrado",
            df_f.to_csv(index=False).encode("utf-8"),
            file_name="datos_filtrados.csv",
            mime="text/csv",
            type="primary"
        )

        st.markdown("—")
        st.subheader("Detalle de selección")
        if sel_rows:
            for i, r in enumerate(sel_rows[:15], start=1):
                with st.container():
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    title = r.get("Título") or r.get("Titulo") or r.get("Nombre") or f"Registro {i}"
                    st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
                    badges = []
                    for b in ["Departamento", "Municipio", "Enfoque Turístico", "Aspecto", "Sector", "Actor"]:
                        v = r.get(b)
                        if v and str(v).strip():
                            badges.append(f'<span class="badge">{b}: {v}</span>')
                    if badges:
                        st.markdown(" ".join(badges), unsafe_allow_html=True)
                    desc = r.get("Descripción") or ""
                    if desc:
                        st.markdown(f"<p>{desc}</p>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.caption("Selecciona filas en la tabla para ver el detalle aquí.")

# --------- EXPLORADOR (Treemap / Sunburst) ----------
with tab_explorar:
    st.subheader("Explorador jerárquico")
    st.caption("Usa combinaciones de Departamento / Municipio / Aspecto para navegar los volúmenes.")

    # Construir rutas disponibles según columnas presentes
    dims = [d for d in ["Departamento", "Municipio", "Aspecto", "Enfoque Turístico", "Sector"] if available(d, df_f)]
    if len(dims) < 2:
        st.info("Se requieren al menos 2 columnas categóricas (p. ej., Departamento y Municipio) para el explorador.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            path_treemap = st.multiselect("Jerarquía Treemap (orden)", dims, default=dims[:3], key="tree")
        with c2:
            path_sun = st.multiselect("Jerarquía Sunburst (orden)", dims, default=dims[:3], key="sun")

        def clean_for_plot(df_, cols):
            d = df_[cols].dropna(how="all").copy()
            for c in cols:
                d[c] = d[c].fillna("Sin dato").astype(str).str.strip()
                d.loc[d[c] == "", c] = "Sin dato"
            d["value"] = 1
            return d

        if path_treemap:
            data_tree = clean_for_plot(df_f, path_treemap)
            fig_tree = px.treemap(
                data_tree,
                path=[px.Constant("Total")] + path_treemap,
                values="value",
                hover_data=path_treemap
            )
            fig_tree.update_traces(root_color="lightgrey")
            st.plotly_chart(fig_tree, use_container_width=True)
        if path_sun:
            data_sun = clean_for_plot(df_f, path_sun)
            fig_sun = px.sunburst(
                data_sun,
                path=[px.Constant("Total")] + path_sun,
                values="value",
                hover_data=path_sun,
                branchvalues="total"
            )
            st.plotly_chart(fig_sun, use_container_width=True)

# --------- BARRAS DINÁMICAS ----------
with tab_barras:
    st.subheader("Barras por categoría")
    cols = [c for c in ["Aspecto", "Enfoque Turístico", "Municipio", "Departamento", "Sector"] if available(c, df_f)]
    if not cols:
        st.info("No hay columnas categóricas disponibles para graficar.")
    else:
        col_sel = st.selectbox("Categoría", cols, index=0)
        top_n = st.slider("Top N", 5, 50, 20, step=5)
        s = df_f[col_sel].dropna().astype(str).str.strip()
        s = s[s != ""]
        if s.empty:
            st.info("No hay datos válidos para la categoría seleccionada.")
        else:
            vc = s.value_counts().head(top_n).reset_index()
            vc.columns = [col_sel, "Conteo"]
            fig = px.bar(
                vc, x="Conteo", y=col_sel, orientation="h",
                text="Conteo"
            )
            fig.update_layout(yaxis={"categoryorder":"total ascending"}, height=520)
            st.plotly_chart(fig, use_container_width=True)
