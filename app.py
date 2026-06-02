import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. LÓGICA DE CÁLCULO (BASE 100) ---

def calcular_horas_extras_formato_fijo(entrada_dt, salida_dt):
    # Definición de jornada
    HORA_INICIO_NORMAL = datetime.strptime("08:00", "%H:%M").time()
    HORA_FIN_NORMAL = datetime.strptime("17:00", "%H:%M").time()
    JORNADA_NORMAL_MINUTOS = 9 * 60  # 9 horas = 540 min

    inicio_normal_dt = datetime.combine(entrada_dt.date(), HORA_INICIO_NORMAL)
    fin_normal_dt = datetime.combine(entrada_dt.date(), HORA_FIN_NORMAL)

    # Minutos por tramos
    minutos_antes = max(0, int((inicio_normal_dt - entrada_dt).total_seconds() / 60))
    minutos_despues = max(0, int((salida_dt - fin_normal_dt).total_seconds() / 60))
    
    inicio_contado = max(entrada_dt, inicio_normal_dt)
    fin_contado = min(salida_dt, fin_normal_dt)
    minutos_normal_efectivo = max(0, int((fin_contado - inicio_contado).total_seconds() / 60))

    minutos_trabajados_totales = minutos_antes + minutos_despues + minutos_normal_efectivo

    # Regla de Fin de Semana (Sábado=5, Domingo=6)
    es_fin_de_semana = entrada_dt.weekday() >= 5

    if es_fin_de_semana:
        minutos_extras = minutos_trabajados_totales
    else:
        minutos_extras = max(0, minutos_trabajados_totales - JORNADA_NORMAL_MINUTOS)

    # Conversión a Formato Horas.Minutos (Base 100)
    horas = minutos_extras // 60
    minutos = minutos_extras % 60
    return float(f"{horas}.{minutos:02d}")

def h_mm_a_minutos(h_mm_float):
    horas = int(h_mm_float)
    minutos = round((h_mm_float - horas) * 100)
    return (horas * 60) + minutos

def minutos_a_h_mm(total_minutos):
    horas = total_minutos // 60
    minutos = total_minutos % 60
    return float(f"{horas}.{minutos:02d}")

# --- 2. INTERFAZ WEB CON STREAMLIT ---

st.set_page_config(page_title="Calculadora Horas Extras", page_icon="⏱️")
st.title("⏱️ Calculadora de Horas Extras")
st.markdown("Cálculo basado en jornada de **9h** (8:00 - 17:00). Fines de semana al **100% extra**.")

# Inicializar historial en la sesión del navegador
if 'historial' not in st.session_state:
    st.session_state.historial = []

with st.form("registro_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Selecciona la Fecha")
        entrada = st.time_input("Hora de Entrada", value=datetime.strptime("08:00", "%H:%M").time())
    with col2:
        empleado = st.text_input("Nombre del Empleado", value="Francisco Lopez")
        salida = st.time_input("Hora de Salida", value=datetime.strptime("17:00", "%H:%M").time())
    
    boton_agregar = st.form_submit_button("Calcular y Agregar al Total")

if boton_agregar:
    # Convertir a datetime para procesar
    entrada_dt = datetime.combine(fecha, entrada)
    salida_dt = datetime.combine(fecha, salida)
    
    # Manejo de jornada nocturna
    if salida_dt < entrada_dt:
        salida_dt += timedelta(days=1)
        
    resultado = calcular_horas_extras_formato_fijo(entrada_dt, salida_dt)
    
    # Guardar en el historial
    st.session_state.historial.append({
        "Empleado": empleado,
        "Fecha": fecha.strftime("%d/%m/%Y"),
        "Día": "FDS" if fecha.weekday() >= 5 else "Semana",
        "Entrada": entrada.strftime("%H:%M"),
        "Salida": salida.strftime("%H:%M"),
        "Extra (H.MM)": resultado
    })

# --- 3. MOSTRAR RESULTADOS ---

if st.session_state.historial:
    df = pd.DataFrame(st.session_state.historial)
    #st.table(df)
    st.dataframe(df, use_container_width=True)

    # Calcular Total General (Pasando por base 60 para que sea exacto)
    total_minutos = sum(df["Extra (H.MM)"].apply(h_mm_a_minutos))
    total_final = minutos_a_h_mm(total_minutos)

    st.metric(label="TOTAL ACUMULADO (Horas.Minutos)", value=f"{total_final:.2f}")

    if st.button("Limpiar Historial"):
        st.session_state.historial = []
        st.rerun()