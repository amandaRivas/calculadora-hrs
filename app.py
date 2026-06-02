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

# setar el mes anterior al que estamos
mes_defecto = st.text_input("📅 Mes y Año a calcular (MM/AAAA)", value="05/2026", help="Cambia esto si vas a calcular otro mes")

with st.form("registro_form", clear_on_submit=False): # Cambiado a False para que no te borre el día de golpe si no quieres
    col1, col2 = st.columns(2)
    with col1:
        # Ahora solo te pide el número del día (ej: 04)
        dia_str = st.text_input("Día (DD)", value="", placeholder="ej: 04", help="Solo escribe los 2 dígitos del día")
        entrada_str = st.text_input("Hora de Entrada", value="06:00")
    with col2:
        empleado = st.text_input("Nombre del Empleado", value="Francisco Lopez")
        salida_str = st.text_input("Hora de Salida", value="", placeholder="ej: 19:33")
    
    boton_agregar = st.form_submit_button("Calcular y Agregar al Total")

if boton_agregar:
    try:
        # Armamos la fecha completa juntando el día con el mes de arriba
        fecha_completa_str = f"{dia_str.strip()}/{mes_defecto.strip()}"
        
        # Validaciones de formatos
        fecha_dt = datetime.strptime(fecha_completa_str, "%d/%m/%Y")
        entrada_t = datetime.strptime(entrada_str.strip(), "%H:%M").time()
        salida_t = datetime.strptime(salida_str.strip(), "%H:%M").time()
        
        entrada_dt = datetime.combine(fecha_dt, entrada_t)
        salida_dt = datetime.combine(fecha_dt, salida_t)
        
        if salida_dt < entrada_dt:
            salida_dt += timedelta(days=1)
            
        resultado = calcular_horas_extras_formato_fijo(entrada_dt, salida_dt)
        
        st.session_state.historial.append({
            "Empleado": empleado,
            "Fecha": fecha_dt.strftime("%d/%m/%Y"),
            "Día": "FDS" if fecha_dt.weekday() >= 5 else "",
            "Entrada": entrada_t.strftime("%H:%M"),
            "Salida": salida_t.strftime("%H:%M"),
            "Extra (H.MM)": resultado
        })
    except ValueError:
        st.error("❌ Error: Revisa los datos. El día debe ser DD (ej: 04) y las horas HH:MM (ej: 19:33)")

# --- 3. MOSTRAR RESULTADOS (EDICIÓN, TOTAL ABAJO Y DESCARGA) ---
if st.session_state.historial:
    st.markdown("💡 *Tip: Puedes hacer doble clic en cualquier celda para corregirla, o seleccionar una fila y presionar 'Supr' (Delete) para borrarla.*")
    
    # Convertimos el historial a DataFrame y ajustamos el índice para que empiece en 1
    df = pd.DataFrame(st.session_state.historial)
    df.index = df.index + 1
    
    # Editor de datos interactivo
    df_editado = st.data_editor(
        df, 
        use_container_width=True,
        num_rows="dynamic",
        disabled=["Día", "Extra (H.MM)"]
    )
    
    # Si el usuario modificó algo en la tabla, actualizamos los cálculos
    if not df_editado.equals(df):
        df_editado["Extra (H.MM)"] = df_editado.apply(recalcular_fila_editada, axis=1)
        df_interno = df_editado.copy()
        df_interno.index = df_interno.index - 1
        st.session_state.historial = df_interno.to_dict(orient="records")
        st.rerun()

    # toal acumulado
    total_minutos = sum(df_editado["Extra (H.MM)"].apply(h_mm_a_minutos))
    total_final = minutos_a_h_mm(total_minutos)

    st.metric(label="TOTAL ACUMULADO (Horas.Minutos)", value=f"{total_final:.2f}")
    st.markdown("---") # Línea divisoria

    # preparar excel con el acumulado total
    import io
    buffer = io.BytesIO()
    
    # Creamos una copia de la tabla para el Excel sin alterar la que ves en pantalla
    df_excel = df_editado.copy()
    
    # Creamos la fila del total con la misma estructura
    fila_total = {
        "Empleado": "TOTAL GENERAL",
        "Fecha": "",
        "Día": "",
        "Entrada": "",
        "Salida": "",
        "Extra (H.MM)": total_final
    }
    
    # Añadimos la fila del total al final de la tabla de Excel
    df_excel = pd.concat([df_excel, pd.DataFrame([fila_total])], ignore_index=True)
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # index=False para que no guarde la columna de números de fila en el Excel
        df_excel.to_excel(writer, sheet_name='Horas Extras', index=False)
    
    # --- 🟢 UN SOLO BOTÓN DE DESCARGA (EXCEL) ---
    st.download_button(
        label="📥 Descargar Reporte en Excel",
        data=buffer.getvalue(),
        file_name=f"Reporte_Horas_{df_editado['Empleado'].iloc[0].replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
    
    st.markdown(" ") # Espacio estético
    
    # Botón para limpiar todo
    if st.button("Limpiar Todo el Historial", use_container_width=True):
        st.session_state.historial = []
        st.rerun()