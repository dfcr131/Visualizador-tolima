# app.py
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import folium
from streamlit_folium import st_folium


# ================== CONFIG BÁSICA ==================
st.set_page_config(
    page_title="Información cualitativa Tolima",
    page_icon="data/ubicacion.png",
    layout="wide"
)

# ---- Estilos (CSS) ----
st.markdown("""
<style>
/* Sidebar fondo y tipografía */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #1e1e2f 0%, #2b2b40 100%);
  color: #fff;
  padding-top: 10px !important;
}

/* Logo en el sidebar */
section[data-testid="stSidebar"] img {
  display: block;
  margin: 0 auto;
  max-width: 290px;  /* controla tamaño máximo */
  margin-bottom: 8px; /* espacio pequeño debajo del logo */
}

/* Línea divisoria */
section[data-testid="stSidebar"] hr {
  margin: 4px 0 8px 0;
  border: 0;
  border-top: 1px solid #444;
}

/* Encabezado de filtros */
section[data-testid="stSidebar"] h2 {
  color: #e5e7eb !important;
  font-weight: 600;
  margin: 6px 0;
  font-size: 1.1rem;
}

/* Botón limpiar */
.stButton > button {
  background: linear-gradient(90deg, #9333ea, #3b82f6);
  color: white;
  border-radius: 8px;
  border: none;
  padding: 6px 12px;
  font-weight: 600;
  margin-top: 4px;
  margin-bottom: 8px;
}
.stButton > button:hover {
  background: linear-gradient(90deg, #a855f7, #60a5fa);
}

/* KPI Cards */
.kpi-card {
  border-radius: 18px;
  padding: 18px;
  background: linear-gradient(135deg, #9333ea 0%, #3b82f6 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.25);
  transition: transform 0.2s ease-in-out;
}
.kpi-card:hover { transform: translateY(-4px); }
.kpi-title { font-size: 14px; opacity: 0.9; }
.kpi-value { font-size: 32px; font-weight: bold; }

/* General Cards */
.card {
  border-radius: 14px; 
  padding: 16px; 
  border: none;
  background: #fff;
  box-shadow: 0 4px 10px rgba(0,0,0,0.08);
  transition: transform 0.2s ease-in-out;
}
.card:hover { transform: scale(1.02); }
.card h4 { margin: 0 0 8px 0; color: #111827; }

/* Badges */
.badge {
  display:inline-block; 
  padding:4px 10px; 
  border-radius:999px; 
  background: #eef2ff; 
  color:#4338ca; 
  border:1px solid #c7d2fe; 
  font-size:12px; 
  margin:2px;
  font-weight: 500;
}
</style>

""", unsafe_allow_html=True)

# ================== ENCABEZADO ==================
col_logo, col_title, col_extra = st.columns([2, 5, 2], vertical_alignment="center")

with col_logo:
    try:
        st.image("data/indus.png", width=120)  # Imagen izquierda
    except Exception:
        pass

with col_title:
    st.markdown(
        """
        <div style="text-align: center;">
            <h1>Bienvenido a la Información Cualitativa Tolima</h1>
            <p>Explora los datos de forma interactiva</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_extra:
    c1, c2 = st.columns([1, 2])  # más espacio vacío a la izquierda
    with c2:
        try:
            st.image("data/fontur_logo.png", width=120)  # Imagen derecha desplazada
        except Exception:
            pass

st.divider()



# ================== CARGA DE DATOS ==================
DEFAULT_FILE = Path("data") / "consolidado_turismo_LOTE 1.xlsx"

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
# Logo arriba en la barra lateral
st.sidebar.image("data/betagroup_logo.jpg", width=290)

# Línea divisoria
st.sidebar.markdown("---")

# Encabezado de filtros
st.sidebar.header("Filtros")
# Columna para botón
col_btn, _ = st.sidebar.columns([1,1])
with col_btn:
    do_reset = st.button("🔄 Limpiar filtros")
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
# Línea divisoria
st.sidebar.markdown("---")

# Imagen al final de todos los filtros
st.sidebar.image("data/OIP.webp", width=290)

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

# ================== TABS ==================
tab_resumen, tab_tabla, tab_explorar, tab_barras = st.tabs([
    "📌 Resumen",
    "📋 Tarjetas de Información",
    "🗺️ Mapa Geografico",
    "📊 Barras"
])

# ================== CSS PARA AGRANDAR TABS ==================
st.markdown("""
    <style>
    button[data-baseweb="tab"] > div[data-testid="stMarkdownContainer"] p {
        font-size: 18px;   /* tamaño de la letra */
        font-weight: 600;  /* más negrita */
    }
    </style>
""", unsafe_allow_html=True)


# Función de estilo reutilizable (sin highlight_max)
def estilo_tabla(df):
    return (
        df.style
        .set_properties(**{
            "background-color": "#f9fafb",   # gris muy claro
            "color": "#111827",              # texto oscuro
            "border-color": "#e5e7eb",       # bordes suaves
            "border-radius": "8px",          # esquinas redondeadas
            "padding": "6px",                # espacio interno
        })
        .set_table_styles([
            {"selector": "thead th", "props": [("background-color", "#3b82f6"), 
                                               ("color", "white"),
                                               ("font-size", "14px"),
                                               ("padding", "8px"),
                                               ("text-align", "center")]},
            {"selector": "tbody td", "props": [("font-size", "13px"),
                                               ("text-align", "center")]}
        ])
    )

with tab_resumen:
    # Pequeños rankings
    cols = st.columns(3)
    if available("Aspecto", df_f) and not df_f["Aspecto"].dropna().empty:
        top_aspecto = df_f["Aspecto"].value_counts().head(5).reset_index()
        top_aspecto.columns = ["Aspecto", "Conteo"]
        with cols[0]:
            st.subheader("Top 5 Aspectos")
            st.dataframe(estilo_tabla(top_aspecto), use_container_width=True, hide_index=True)

    if available("Enfoque Turístico", df_f) and not df_f["Enfoque Turístico"].dropna().empty:
        top_enfoque = df_f["Enfoque Turístico"].value_counts().head(5).reset_index()
        top_enfoque.columns = ["Enfoque Turístico", "Conteo"]
        with cols[1]:
            st.subheader("Top 5 Enfoques")
            st.dataframe(estilo_tabla(top_enfoque), use_container_width=True, hide_index=True)

    if available("Municipio", df_f) and not df_f["Municipio"].dropna().empty:
        top_mpio = df_f["Municipio"].value_counts().head(5).reset_index()
        top_mpio.columns = ["Municipio", "Conteo"]
        with cols[2]:
            st.subheader("Top 5 Municipios")
            st.dataframe(estilo_tabla(top_mpio), use_container_width=True, hide_index=True)



# --------- TABLA (AgGrid) ----------
with tab_tabla:
    st.subheader("Explora los registros en formato tarjetas")
    
    if len(df_f) == 0:
        st.info("No hay filas con los filtros actuales. Ajusta filtros o limpia la búsqueda.")
    else:
        for i, row in df_f.head(50).iterrows():  # límite para no cargar demasiadas
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                
                # Título dinámico
                title = row.get("Título") or row.get("Titulo") or row.get("Nombre") or f"Registro {i}"
                st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)

                # Badges dinámicos
                badges = []
                for b in ["Departamento", "Municipio", "Enfoque Turístico", "Aspecto", "Sector", "Actor"]:
                    v = row.get(b)
                    if v and str(v).strip():
                        badges.append(f'<span class="badge">{b}: {v}</span>')
                if badges:
                    st.markdown(" ".join(badges), unsafe_allow_html=True)

                # Descripción
                desc = row.get("Descripción") or ""
                if desc:
                    st.markdown(f"<p>{desc}</p>", unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)


# --------- EXPLORADOR (Treemap / Sunburst) ----------
# Coordenadas aproximadas de los departamentos
coords_departamentos = {
    "Tolima": [4.3333, -75.0000],
    "Huila": [2.9167, -75.3333],
    "Caquetá": [1.6000, -75.6000],
    "Putumayo": [0.3000, -76.5000],
}

with tab_explorar:
    st.subheader("🗺️ Explorador geográfico con filtros")
    st.caption("Filtra por Departamento, Municipio, Aspecto, Enfoque o Sector y visualiza los resultados en el mapa.")

    # --- Columnas disponibles ---
    dims = [d for d in ["Departamento", "Municipio", "Aspecto", "Enfoque Turístico", "Sector"] if available(d, df_f)]

    if len(dims) == 0:
        st.info("⚠️ No se encuentran columnas categóricas para filtrar.")
    else:
        # Crear filtros dinámicos
        filtros = {}
        for dim in dims:
            valores = sorted(df_f[dim].dropna().unique())
            seleccion = st.multiselect(f"📍 Filtrar por {dim}:", valores, default=valores)
            filtros[dim] = seleccion

        # Aplicar filtros
        df_filtrado = df_f.copy()
        for dim, seleccion in filtros.items():
            if seleccion:  # Solo aplicar si hay selección
                df_filtrado = df_filtrado[df_filtrado[dim].isin(seleccion)]

        # Layout en dos columnas
        col1, col2 = st.columns([2, 2])

        # --- Resumen en tabla ---
        with col1:
            st.markdown("### 📊 Resumen filtrado")
            if len(df_filtrado) == 0:
                st.info("No hay registros con los filtros seleccionados.")
            else:
                resumen = df_filtrado.groupby(dims).size().reset_index(name="Conteo")
                st.dataframe(resumen, use_container_width=True)

        # --- Mapa geográfico ---
        with col2:
            st.markdown("### 🗺️ Mapa interactivo")
            if len(df_filtrado) == 0:
                st.caption("No hay datos para mostrar en el mapa.")
            else:
                # Agrupar por departamento
                departamentos = df_filtrado.groupby("Departamento").size().reset_index(name="Conteo")

                # Crear mapa
                m = folium.Map(location=[2.5, -75.0], zoom_start=6, tiles="cartodbpositron")

                for _, row in departamentos.iterrows():
                    depto = row["Departamento"]
                    conteo = row["Conteo"]
                    coords = coords_departamentos.get(depto)

                    if coords:
                        folium.CircleMarker(
                            location=coords,
                            radius=8 + conteo * 0.3,
                            popup=f"<b>{depto}</b><br>Registros: {conteo}",
                            color="darkblue",
                            fill=True,
                            fill_color="purple",
                            fill_opacity=0.6,
                        ).add_to(m)

                # Mostrar mapa
                st_folium(m, width=800, height=500)

# --------- BARRAS DINÁMICAS ----------
with tab_barras:
    st.subheader("📊 Comparación por categorías")

    cols = [c for c in ["Aspecto", "Enfoque Turístico", "Municipio", "Departamento", "Sector"] if available(c, df_f)]
    
    if not cols:
        st.info("No hay columnas categóricas disponibles para graficar.")
    else:
        col_sel = st.selectbox("📍 Selecciona categoría", cols, index=0)
        top_n = st.slider("🔝 Top N", 5, 50, 20, step=5)

        s = df_f[col_sel].dropna().astype(str).str.strip()
        s = s[s != ""]
        
        if s.empty:
            st.info("⚠️ No hay datos válidos para la categoría seleccionada.")
        else:
            vc = s.value_counts().head(top_n).reset_index()
            vc.columns = [col_sel, "Conteo"]

            fig = px.bar(
                vc,
                x="Conteo",
                y=col_sel,
                orientation="h",
                text="Conteo",
                color="Conteo",
                color_continuous_scale="plasma"  # gradiente bonito
            )

            fig.update_traces(
                texttemplate="%{text}",
                textposition="outside",
                marker=dict(line=dict(width=0.5, color="white"))
            )

            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                height=600,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title="Número de registros",
                yaxis_title="",
                plot_bgcolor="rgba(0,0,0,0)",  # fondo transparente
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(size=13)
            )

            st.plotly_chart(fig, use_container_width=True)
