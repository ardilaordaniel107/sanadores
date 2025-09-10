import streamlit as st
import pandas as pd
import os

# Nombre del archivo CSV donde se guardarán los datos
FILE = "registros.csv"

# Si el archivo no existe, lo creamos con los encabezados
if not os.path.exists(FILE):
    df = pd.DataFrame(columns=["Trabajador", "Consultas", "Controles", "Ingreso", "Semana"])
    df.to_csv(FILE, index=False)

# Título principal
st.title("📊 Registro Semanal de Trabajadores")

st.markdown("Complete la información semanal de cada trabajador y guárdela en el sistema.")

# Formulario de ingreso de datos
with st.form("formulario"):
    trabajador = st.text_input("👤 Nombre del trabajador")
    consultas = st.number_input("📋 Número de consultas", min_value=0, step=1)
    controles = st.number_input("✅ Número de controles", min_value=0, step=1)
    ingreso = st.number_input("💰 Ingreso semanal ($)", min_value=0, step=1000)
    semana = st.text_input("📅 Semana (ej: 2025-W36)")

    submit = st.form_submit_button("Guardar")

# Guardar datos al presionar el botón
if submit:
    if trabajador and semana:
        nuevo = pd.DataFrame([[trabajador, consultas, controles, ingreso, semana]],
                             columns=["Trabajador", "Consultas", "Controles", "Ingreso", "Semana"])
        df = pd.read_csv(FILE)
        df = pd.concat([df, nuevo], ignore_index=True)
        df.to_csv(FILE, index=False)
        st.success(f"✅ Registro guardado para {trabajador} en la semana {semana}")
    else:
        st.error("⚠️ Debe ingresar al menos el nombre del trabajador y la semana.")

# Mostrar registros guardados
st.subheader("📑 Registros guardados")
df = pd.read_csv(FILE)
st.dataframe(df)

# Resumen por semana
st.subheader("📈 Resumen por semana")
if not df.empty:
    resumen = df.groupby("Semana").agg({
        "Consultas": "sum",
        "Controles": "sum",
        "Ingreso": "sum"
    }).reset_index()
    st.table(resumen)
else:
    st.info("Aún no hay registros para mostrar.")
