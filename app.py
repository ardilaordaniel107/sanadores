import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client

# 🔑 Configuración de Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------------
# ⚙ Inicializar session_state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.is_admin = False

# -------------------------------
# 📌 Función para guardar registros
def guardar_registro(oficina, consultas, controles, ingreso, semana=None):
    """
    Guarda un registro en la tabla 'registros' para la oficina indicada.
    """
    if not semana:
        today = datetime.date.today()
        iso = today.isocalendar()
        semana = f"{iso[0]}-W{iso[1]:02d}"

    data = {
        "oficina": oficina,
        "consultas": int(consultas),
        "controles": int(controles),
        "ingreso": float(ingreso),
        "semana": semana,
    }

    try:
        supabase.table("registros").insert(data).execute()
        st.success(f"✅ Registro guardado para {oficina} (semana {semana})")

        # 🚀 Tarjetas con resumen
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

# -------------------------------
# 🔐 Pantalla de login
if not st.session_state.logged_in:
    st.title("🔑 Iniciar Sesión")

    nombre_login = st.text_input("🏢 Oficina (ejemplo: pachuca o san martin)")
    password = st.text_input("🔒 Contraseña (solo admin)", type="password")

    if st.button("Ingresar"):
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
            st.session_state.username = nombre_login.lower()
            st.session_state.is_admin = False
            st.success(f"✅ Bienvenido {nombre_login}")
        else:
            st.error("⚠ Debes ingresar el nombre de la oficina")

# -------------------------------
# 📊 Pantalla principal (ya logueado)
else:
    st.sidebar.write(f"🏢 Oficina: {st.session_state.username}")
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.experimental_rerun()

    st.title("📊 Registro de Actividad por Oficina")

    # -------------------------------
    # 📝 Formulario (solo oficinas, no admin)
    if not st.session_state.is_admin:
        with st.form("formulario"):
            consultas = st.number_input("📋 Número de consultas", min_value=0, step=1)
            controles = st.number_input("✅ Número de controles", min_value=0, step=1)
            ingreso = st.number_input("💰 Ingreso ($)", min_value=0, step=100)
            semana_input = st.text_input("📅 Semana (ej: 2025-W36, opcional)")

            submit = st.form_submit_button("Guardar")

        if submit:
            guardar_registro(
                oficina=st.session_state.username,
                consultas=consultas,
                controles=controles,
                ingreso=ingreso,
                semana=semana_input if semana_input.strip() else None,
            )

    # -------------------------------
    # 📑 Mostrar registros
    st.subheader("📑 Registros")

    if st.session_state.is_admin:
        # 🔐 Admin ve todo
        response = supabase.table("registros").select("*").execute()
    else:
        # 🏢 Oficina solo ve sus registros
        response = supabase.table("registros").select("*").eq("oficina", st.session_state.username).execute()

    df = pd.DataFrame(response.data)

    if not df.empty:
        # Asegurar formato de fecha si existe
        if "fecha_registro" in df.columns:
            df["fecha_registro"] = pd.to_datetime(df["fecha_registro"])

        st.dataframe(df)

        # 📈 Resumen por semana (solo de esa oficina o global si admin)
        st.subheader("📈 Resumen por semana")
        resumen = df.groupby("semana").agg({
            "consultas": "sum",
            "controles": "sum",
            "ingreso": "sum"
        }).reset_index()
        resumen["ganancia"] = resumen["ingreso"] / 2
        st.table(resumen)

        # 📊 Dashboard general (solo admin)
        if st.session_state.is_admin:
            st.subheader("📊 Dashboard Global")
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
