import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# ==============================
# 🎨 Configuración de la página
# ==============================
st.set_page_config(
    page_title="📊 Dashboard Oficinas",
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
# 🔐 Pantalla de login
# ==============================
if not st.session_state.logged_in:
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
# 📊 Pantalla principal (ya logueado)
# ==============================
else:
    st.sidebar.markdown(f"### 👤 Oficina: {st.session_state.username}")

    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.experimental_rerun()

    st.markdown("<h1 style='text-align: center;'>📊 Registro de Actividad por Oficina</h1>", unsafe_allow_html=True)

    # ==============================
    # 📝 Formulario (solo oficinas)
    # ==============================
    if not st.session_state.is_admin:
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
            # Si no se ingresó semana, se genera automáticamente
            if semana_input and semana_input.strip():
                semana_val = semana_input.strip()
            else:
                today = datetime.date.today()
                iso = today.isocalendar()
                year, week = iso[0], iso[1]
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

                # 🚀 Tarjetas con resumen del registro
                st.markdown("### 📌 Resumen del Registro")
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
    # 📑 Mostrar registros
    # ==============================
    st.markdown("## 📑 Registros")

    # ✅ 1. Cada oficina ve solo sus datos
    if not st.session_state.is_admin:
        response = supabase.table("registros").select("*").eq("oficina", st.session_state.username).execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.markdown(f"### 📂 Registros de la oficina **{st.session_state.username}**")
            st.dataframe(df, use_container_width=True)

            # 📈 Resumen por semana
            st.markdown("### 📈 Resumen por Semana (Oficina)")
            resumen = df.groupby("semana").agg({
                "consultas": "sum",
                "controles": "sum",
                "ingreso": "sum"
            }).reset_index()
            resumen["ganancia"] = resumen["ingreso"] / 2
            st.table(resumen)

            # 📊 Dashboard de oficina
            st.markdown("### 📊 Dashboard Oficina")
            total_consultas = int(resumen["consultas"].sum())
            total_controles = int(resumen["controles"].sum())
            total_ingreso = float(resumen["ingreso"].sum())
            total_ganancia = float(resumen["ganancia"].sum())

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("📋 Total Consultas", total_consultas)
            with c2:
                st.metric("✅ Total Controles", total_controles)
            with c3:
                st.metric("💰 Total Ingreso", f"${total_ingreso:,.0f}")
            with c4:
                st.metric("📈 Total Ganancia", f"${total_ganancia:,.0f}")
        else:
            st.info("No hay registros disponibles para esta oficina.")

    # ✅ 2. Admin ve todos los datos globales
    else:
        st.markdown("## 🌍 Dashboard Global (Administrador)")

        response = supabase.table("registros").select("*").execute()
        df = pd.DataFrame(response.data)

        if not df.empty:
            st.dataframe(df, use_container_width=True)

            # 📈 Resumen por semana global
            st.markdown("### 📈 Resumen por Semana (Global)")
            resumen = df.groupby("semana").agg({
                "consultas": "sum",
                "controles": "sum",
                "ingreso": "sum"
            }).reset_index()
            resumen["ganancia"] = resumen["ingreso"] / 2
            st.table(resumen)

            # 📊 Dashboard general
            st.markdown("### 📊 Dashboard General (Todas las Oficinas)")
            total_consultas = int(resumen["consultas"].sum())
            total_controles = int(resumen["controles"].sum())
            total_ingreso = float(resumen["ingreso"].sum())
            total_ganancia = float(resumen["ganancia"].sum())

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("📋 Total Consultas", total_consultas)
            with c2:
                st.metric("✅ Total Controles", total_controles)
            with c3:
                st.metric("💰 Total Ingreso", f"${total_ingreso:,.0f}")
            with c4:
                st.metric("📈 Total Ganancia", f"${total_ganancia:,.0f}")
        else:
            st.info("No hay registros disponibles.")
