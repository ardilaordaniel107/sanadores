import streamlit as st
import pandas as pd
from supabase import create_client, Client
import datetime

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
# 🔐 Pantalla de login
if not st.session_state.logged_in:
    st.title("🔑 Iniciar Sesión")

    nombre_login = st.text_input("👤 Usuario")
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
            st.session_state.username = nombre_login
            st.session_state.is_admin = False
            st.success(f"✅ Bienvenido {nombre_login}")
        else:
            st.error("⚠ Debes ingresar un nombre de usuario")

# -------------------------------
# 📊 Pantalla principal (ya logueado)
else:
    st.sidebar.write(f"👤 Usuario: {st.session_state.username}")
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.is_admin = False
        st.experimental_rerun()

    st.title("📊 Registro de Actividad de Trabajadores")

    # -------------------------------
    # 📝 Formulario (solo trabajadores)
    if not st.session_state.is_admin:
        with st.form("formulario"):
            consultas = st.number_input("📋 Número de consultas", min_value=0, step=1)
            controles = st.number_input("✅ Número de controles", min_value=0, step=1)
            ingreso = st.number_input("💰 Ingreso ($)", min_value=0, step=100)
            semana_input = st.text_input(
                "📅 Semana (ej: 2025-W36) — opcional (si lo dejas vacío se usará la semana actual)"
            )

            submit = st.form_submit_button("Guardar")

        if submit:
            # si no proporcionaron semana, generamos la semana ISO actual
            if semana_input and semana_input.strip():
                semana_val = semana_input.strip()
            else:
                today = datetime.date.today()
                iso = today.isocalendar()  # (year, week, weekday)
                year = iso[0]
                week = iso[1]
                semana_val = f"{year}-W{week:02d}"

            # preparar datos (no enviamos 'ganancia' para que el trigger DB la calcule)
            data = {
                "trabajador": st.session_state.username,
                "consultas": int(consultas),
                "controles": int(controles),
                "ingreso": float(ingreso),
                "semana": semana_val
            }

            st.write("📤 Datos a insertar:", data)

            try:
                result = supabase.table("registros").insert(data).execute()
                st.success(f"✅ Registro guardado para {st.session_state.username} (semana {semana_val})")
                st.write("📥 Respuesta Supabase:", result)
            except Exception as e:
                st.error("❌ Error al guardar en Supabase")
                st.exception(e)

    # -------------------------------
    # 📑 Mostrar registros
    st.subheader("📑 Registros")

    if st.session_state.is_admin:
        # 🔐 Admin ve todo (puedes agregar filtros)
        response = supabase.table("registros").select("*").execute()
    else:
        # 👤 Trabajador solo ve sus registros
        response = (
            supabase.table("registros")
            .select("*")
            .eq("trabajador", st.session_state.username)
            .execute()
        )

    df = pd.DataFrame(response.data)

    if not df.empty:
        # Asegurar formato de fecha si existe
        if "fecha_registro" in df.columns:
            df["fecha_registro"] = pd.to_datetime(df["fecha_registro"])

        # Si por algún motivo la columna ganancia no existe, calcularla localmente (backup)
        if "ganancia" not in df.columns:
            df["ganancia"] = df["ingreso"].astype(float) / 2

        st.dataframe(df)

        # 📈 Resumen por fecha y por semana
        st.subheader("📈 Resumen por fecha")
        if "fecha_registro" in df.columns:
            resumen_fecha = (
                df.groupby(df["fecha_registro"].dt.date)
                .agg({"consultas": "sum", "controles": "sum", "ingreso": "sum", "ganancia": "sum"})
                .reset_index()
                .rename(columns={"fecha_registro": "fecha"})
            )
            st.table(resumen_fecha)

        st.subheader("📈 Resumen por semana")
        resumen_semana = (
            df.groupby("semana")
            .agg({"consultas": "sum", "controles": "sum", "ingreso": "sum", "ganancia": "sum"})
            .reset_index()
        )
        st.table(resumen_semana)
    else:
        st.info("No hay registros disponibles.")
