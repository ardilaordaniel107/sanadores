import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
import plotly.express as px

# ==============================
# 🎨 Configuración de la página
# ==============================
st.set_page_config(
    page_title="📊 Registro de Oficinas",
    page_icon="🏢",
    layout="wide"
)

# ==============================
# 🔑 Configuración de Supabase
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# ⚙ Inicializar session_state
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False


# ==============================
# 🔐 Función de login
# ==============================
def login_screen():
    st.markdown("<h1 style='text-align: center;'>🔑 Iniciar Sesión</h1>", unsafe_allow_html=True)

    nombre_login = st.text_input("🏢 Nombre de la Oficina")
    password = st.text_input("🔒 Contraseña (solo admin)", type="password")

    if st.button("Ingresar", use_container_width=True):
        if nombre_login.lower() == "admin":
            if password == st.secrets["ADMIN_PASSWORD"]:
                st.session_state.logged_in = True
                st.session_state.username = "admin"
                st.session_state.is_admin = True
                st.success("✅ Bienvenido Administrador")
            else:
                st.error("❌ Contraseña incorrecta")
        elif nombre_login.strip() != "":
            st.session_state.logged_in = True
            st.session_state.username = nombre_login
            st.session_state.is_admin = False
            st.success(f"✅ Bienvenida oficina {nombre_login}")
        else:
            st.error("⚠ Debes ingresar un nombre de oficina")


# ==============================
# 📝 Formulario de registros
# ==============================
def formulario_registro():
    st.markdown("### 📝 Registrar Actividad")

    with st.form("formulario", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            consultas = st.number_input("📋 Número de consultas", min_value=0, step=1)
            ingreso = st.number_input("💰 Ingreso ($)", min_value=0, step=100)

        with col2:
            controles = st.number_input("✅ Número de controles", min_value=0, step=1)
            semana_input = st.text_input("📅 Semana (ej: 2025-W36, opcional)")

        submit = st.form_submit_button("Guardar Registro")

    if submit:
        # Generar semana automáticamente si no se ingresó
        if semana_input and semana_input.strip():
            semana_val = semana_input.strip()
        else:
            today = datetime.date.today()
            year, week, _ = today.isocalendar()
            semana_val = f"{year}-W{week:02d}"

        # Datos a insertar
        data = {
            "oficina": st.session_state.username,
            "consultas": int(consultas),
            "controles": int(controles),
            "ingreso": float(ingreso),
            "semana": semana_val,
        }

        try:
            supabase.table("registros").insert(data).execute()
            st.success(f"✅ Registro guardado para la oficina **{st.session_state.username}** (semana {semana_val})")

            # Resumen visual del registro recién guardado
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📋 Consultas", data["consultas"])
            with col2:
                st.metric("✅ Controles", data["controles"])
            with col3:
                st.metric("💰 Ingreso", f"${data['ingreso']:,.0f}")
            with col4:
                st.metric("📈 Ganancia", f"${data['ingreso']/2:,.0f}")

        except Exception as e:
            st.error("❌ Error al guardar en Supabase")
            st.exception(e)


# ==============================
# 📑 Mostrar registros + gráficas
# ==============================
def mostrar_registros():
    st.markdown("## 📑 Registros")

    if not st.session_state.is_admin:
        # Filtrar por oficina
        response = supabase.table("registros").select("*").eq("oficina", st.session_state.username).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.markdown(f"### 📂 Registros de la oficina **{st.session_state.username}**")
            st.dataframe(df, use_container_width=True)

            # Resumen por semana
            st.markdown("### 📈 Resumen por Semana (Oficina)")
            resumen = df.groupby("semana").agg({
                "consultas": "sum",
                "controles": "sum",
                "ingreso": "sum"
            }).reset_index()
            resumen["ganancia"] = resumen["ingreso"] / 2
            st.table(resumen)

            # Gráficas
            st.markdown("### 📊 Gráficas de Actividad (Oficina)")

            fig_line = px.line(
                resumen,
                x="semana",
                y=["consultas", "controles", "ingreso"],
                markers=True,
                title="📈 Evolución semanal"
            )
            st.plotly_chart(fig_line, use_container_width=True)

            fig_bar = px.bar(
                resumen,
                x="semana",
                y="ganancia",
                title="📊 Ganancia por semana",
                text_auto=True
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Totales
            st.markdown("### 📊 Dashboard Oficina")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📋 Total Consultas", int(resumen["consultas"].sum()))
            with col2:
                st.metric("✅ Total Controles", int(resumen["controles"].sum()))
            with col3:
                st.metric("💰 Total Ingreso", f"${float(resumen['ingreso'].sum()):,.0f}")
            with col4:
                st.metric("📈 Total Ganancia", f"${float(resumen['ganancia'].sum()):,.0f}")
        else:
            st.info("No hay registros disponibles para esta oficina.")

    else:
        # Admin ve todo
        st.markdown("## 🌍 Dashboard Global (Administrador)")
        response = supabase.table("registros").select("*").execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.dataframe(df, use_container_width=True)

            # Resumen por semana global
            st.markdown("### 📈 Resumen por Semana (Global)")
            resumen = df.groupby("semana").agg({
                "consultas": "sum",
                "controles": "sum",
                "ingreso": "sum"
            }).reset_index()
            resumen["ganancia"] = resumen["ingreso"] / 2
            st.table(resumen)

            # Gráficas
            st.markdown("### 📊 Gráficas Globales")

            fig_line = px.line(
                resumen,
                x="semana",
                y=["consultas", "controles", "ingreso"],
                markers=True,
                title="📈 Evolución semanal global"
            )
            st.plotly_chart(fig_line, use_container_width=True)

            fig_bar = px.bar(
                resumen,
                x="semana",
                y="ganancia",
                title="📊 Ganancia por semana (Global)",
                text_auto=True
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            # Totales globales
            st.markdown("### 📊 Dashboard General")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📋 Total Consultas", int(resumen["consultas"].sum()))
            with col2:
                st.metric("✅ Total Controles", int(resumen["controles"].sum()))
            with col3:
                st.metric("💰 Total Ingreso", f"${float(resumen['ingreso'].sum()):,.0f}")
            with col4:
                st.metric("📈 Total Ganancia", f"${float(resumen['ganancia'].sum()):,.0f}")
        else:
            st.info("No hay registros disponibles.")


# ==============================
# 🚀 Main App
# ==============================
if not st.session_state.logged_in:
    login_screen()
else:
    st.sidebar.markdown(f"### 👤 Oficina: {st.session_state.username}")
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.experimental_rerun()

    st.markdown("<h1 style='text-align: center;'>📊 Registro de Actividad por Oficina</h1>", unsafe_allow_html=True)

    if not st.session_state.is_admin:
        formulario_registro()

    mostrar_registros()
