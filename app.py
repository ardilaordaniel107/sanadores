import streamlit as st
from supabase import create_client, Client
import datetime

# ==============================
# Configuración de Supabase
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# Login básico (ejemplo)
# ==============================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Login")
    username = st.text_input("Usuario (oficina)")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        # 🔑 Aquí puedes validar usuario/clave contra tu propia lógica
        if username and password:  
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Bienvenido {username}")
            st.experimental_rerun()
else:
    st.sidebar.success(f"Oficina: {st.session_state.username}")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.experimental_rerun()

    # ==============================
    # Formulario para registrar datos
    # ==============================
    st.header("Nuevo registro")

    consultas = st.number_input("Consultas", min_value=0, step=1)
    controles = st.number_input("Controles", min_value=0, step=1)
    ingreso = st.number_input("Ingreso", min_value=0.0, step=0.01)
    semana = st.text_input("Semana")

    if st.button("Guardar registro"):
        data = {
            "consultas": consultas,
            "controles": controles,
            "ingreso": ingreso,
            "semana": semana,
            "oficina": st.session_state.username,
            # Si quieres guardar fecha de forma automática:
            # "fecha_registro": datetime.datetime.utcnow().isoformat()
        }

        response = supabase.table("registros").insert(data).execute()
        st.success("Registro guardado correctamente ✅")

    # ==============================
    # Recuperar registros
    # ==============================
    st.header("Mis registros")

    try:
        response = supabase.table("registros").select(
            "id, oficina, consultas, controles, ingreso, semana"
        ).eq("oficina", st.session_state.username).execute()

        registros = response.data

        if registros:
            st.write(registros)
        else:
            st.info("No hay registros aún.")
    except Exception as e:
        st.error(f"Error al recuperar registros: {e}")
