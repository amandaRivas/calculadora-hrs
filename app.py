import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. LÓGICA DE CÁLCULO (BASE 100) ---

def calcular_horas_extras_formato_fijo(entrada_dt, salida_dt):
    HORA_INICIO_NORMAL = datetime.strptime("08:00", "%H:%M").time()
    HORA_FIN_NORMAL = datetime.strptime("17:00", "%H:%M").time()
    JORNADA_NORMAL_MINUTOS = 9 * 60 

    inicio_normal_dt = datetime.combine(entrada_dt.date(), HORA_INICIO_NORMAL)
    fin_normal_dt = datetime.combine(entrada_dt.date(), HORA_FIN_NORMAL)

    minutos_antes = max(0, int((inicio_normal_dt - entrada_dt).total_seconds() / 60))
    minutos_despues = max(0, int((salida_dt - fin_normal_dt).total_seconds() / 60))
    
    inicio_contado = max(entrada_dt, inicio_normal_dt)
    fin_contado = min(salida_dt, fin_normal_dt)
    minutos_normal_efectivo = max(0, int((fin_contado - inicio_contado).total_seconds() / 60))

    minutos_trabajados_totales = minutos_antes + minutos_despues + minutes_normal_efectivo if 'minutes_normal_efectivo' in locals() else minutos_antes + minutos_despues + minutos_normal_efectivo

    es_fin_de_semana = entrada_dt.weekday() >= 5

    if es_fin_de_semana:
        minutos_extras = minutos_trabajados_totales
    else:
        minutos_extras = max(0, minutos_trabajados_totales - JORNADA_NORMAL_MINUTOS)

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

# Recalcula las horas extras de una fila si el usuario edita la Entrada o Salida manualmente
def recalcular_fila_editada(row):
    try:
        fecha_dt = datetime.strptime(row["Fecha"], "%d/%m/%Y").date()
        entrada_t = datetime.strptime(row["Entrada"], "%H:%M").time()
        salida_t = datetime.strptime(row["Salida"], "%H:%M").time()
        
        entrada_dt = datetime.combine(fecha_dt, entrada_t)
        salida_dt = datetime.combine(fecha_dt, salida_t)
        
        if salida_dt < entrada_dt:
            salida_dt += timedelta(days=1)
            
        return calcular_horas_extras_formato_fijo(entrada_dt, salida_dt)
    except:
        return row["Extra (H.MM)"] # Si hay error de formato al escribir, deja el valor que estaba

# --- 2. INTERFAZ WEB CON STREAMLIT ---

st.set_page_config(page_title="Calculadora Horas Extras", page_icon="⏱️")
st.title("⏱️ Calculadora de Horas Extras")
st.markdown("Cálculo basado en jornada de **9h** (8:00 - 17:00). Fines de semana al **100% extra**.")

if 'historial' not in st.session_state:
    st.session_state.historial = []

with st.form("registro_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Selecciona la Fecha")
        entrada = st.time_input("Hora de Entrada", value=datetime.strptime("06:00", "%H:%M").time())
    with col2:
        empleado = st.text_input("Nombre del Empleado", value="")
        salida = st.time_input("Hora de Salida", value=datetime.strptime("17:00", "%H:%M").time())
    
    boton_agregar = st.form_submit_button("Calcular y Agregar al Total")

if boton_agregar:
    entrada_dt = datetime.combine(fecha, entrada)
    salida_dt = datetime.combine(fecha, salida)
    
    if salida_dt < entrada_dt:
        salida_dt += timedelta(days=1)
        
    resultado = calcular_horas_extras_formato_fijo(entrada_dt, salida_dt)
    
    st.session_state.historial.append({
        "Empleado": empleado,
        "Fecha": fecha.strftime("%d/%m/%Y"),
        "Día": "FDS" if fecha.weekday() >= 5 else "Semana",
        "Entrada": entrada.strftime("%H:%M"),
        "Salida": salida.strftime("%H:%M"),
        "Extra (H.MM)": resultado
    })

# --- 3. MOSTRAR RESULTADOS (EDICIÓN ACTIVA) ---

if st.session_state.historial:
    st.markdown("💡 *Tip: Puedes hacer doble clic en cualquier celda para corregirla, o seleccionar una fila y presionar 'Supr' (Delete) para borrarla.*")
    
    # Convertimos el historial a DataFrame
    df = pd.DataFrame(st.session_state.historial)
    
    # SOLUCIÓN 1: Hacer que el índice empiece en 1 en lugar de 0
    df.index = df.index + 1
    
    # SOLUCIÓN 2: Usar el editor de datos interactivo de Streamlit
    # Bloqueamos la edición de columnas calculadas automáticamente para evitar errores
    df_editado = st.data_editor(
        df, 
        use_container_width=True,
        num_rows="dynamic", # Permite borrar filas
        disabled=["Día", "Extra (H.MM)"] # No dejamos editar estos porque dependen de la entrada/salida
    )
    
    # Si el usuario modificó algo en la tabla, actualizamos los cálculos automáticamente
    if not df_editado.equals(df):
        # Volver a calcular las horas extras basándose en lo que el usuario editó en Entrada o Salida
        df_editado["Extra (H.MM)"] = df_editado.apply(recalcular_fila_editada, axis=1)
        # Sincronizar con el historial de la sesión (restando 1 al índice para guardarlo bien internamente)
        df_interno = df_editado.copy()
        df_interno.index = df_interno.index - 1
        st.session_state.historial = df_interno.to_dict(orient="records")
        st.rerun()

    # Calcular Total General
    total_minutos = sum(df_editado["Extra (H.MM)"].apply(h_mm_a_minutos))
    total_final = minutos_a_h_mm(total_minutos)

    st.metric(label="TOTAL ACUMULADO (Horas.Minutos)", value=f"{total_final:.2f}")

    if st.button("Limpiar Todo el Historial"):
        st.session_state.historial = []
        st.rerun()