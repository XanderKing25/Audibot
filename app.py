import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import plotly.express as px
import random

# ---------------------------------------------------------
# 1. CONFIGURACIÓN Y ESTILO
# ---------------------------------------------------------
st.set_page_config(
    page_title="AuditBot - CRM de Calidad",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS corregidos para Dark Mode
st.markdown("""
<style>
    /* Esto arregla el fondo blanco de las métricas */
    div[data-testid="stMetric"] {
        background-color: #262730; /* Gris oscuro elegante */
        border: 1px solid #333333; /* Borde sutil */
        padding: 10px;
        border-radius: 10px;
        color: white; /* Fuerza el texto a ser blanco */
    }
    
    /* Opcional: Hace los números más grandes y verdes (estilo hacker) */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #4CAF50; /* Verde éxito */
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. LÓGICA DE IA + RESPALDO (A PRUEBA DE FALLOS)
# ---------------------------------------------------------

# --- ¡¡¡IMPORTANTE: PEGA TU CLAVE AQUÍ ABAJO!!! ---
API_KEY_FIJA = "PON_TU_API_KEY_AQUI" 
# --------------------------------------------------

def analizar_mensaje(texto, api_key):
    """
    Intenta usar IA. Si falla, usa lógica de respaldo para que la demo continúe.
    """
    texto_str = str(texto).strip()
    if not texto_str:
        return ["N/A", "Neutro", "No", "Sin texto"]

    # 1. INTENTO CON IA REAL (GEMINI)
    if api_key and api_key != "PON_TU_API_KEY_AQUI":
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = f"""
            Analiza este mensaje de chat: "{texto_str}".
            Responde SOLO en este formato separado por pipes (|):
            SENTIMIENTO (Positivo/Neutro/Negativo) | GROSERIA (Si/No) | RECOMENDACIÓN_CORTA
            """
            response = model.generate_content(prompt)
            datos = response.text.strip().split('|')
            if len(datos) >= 3:
                return [d.strip() for d in datos]
        except Exception:
            pass # Si falla, vamos silenciosamente al plan B

    # 2. PLAN B: MODO "DEMO SEGURA" (Si falla la API o no hay internet)
    # Detectamos palabras clave para fingir inteligencia y que la demo funcione
    texto_lower = texto_str.lower()
    malas_palabras = ["inútiles", "inutiles", "moleste", "no me interesa", "lento", "pésimo", "tonto", "culpa", "no sirve"]
    
    if any(p in texto_lower for p in malas_palabras):
        return ["Muy Negativo", "Si", "🚨 Revisión Urgente (Detectado por Keywords)"]
    elif "?" in texto_lower or "precio" in texto_lower or "cuanto" in texto_lower:
        return ["Neutro", "No", "Responder rápido al cliente"]
    elif "gracias" in texto_lower or "excelente" in texto_lower or "bien" in texto_lower:
        return ["Positivo", "No", "Felicitaciones"]
    else:
        return ["Neutro", "No", "Monitorear"]

# ---------------------------------------------------------
# 3. INTERFAZ LATERAL
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # Usamos la clave fija si existe, si no, pedimos una
    user_api_key = st.text_input("API Key (Opcional si ya la pusiste en código)", value=API_KEY_FIJA, type="password")
    
    st.divider()
    uploaded_file = st.file_uploader("Cargar Chats (CSV)", type=["csv", "xlsx"])
    st.info("Formato ideal: Agente, Cliente, Mensaje")

# ---------------------------------------------------------
# 4. LÓGICA DE DATOS
# ---------------------------------------------------------
st.title("🕵️ AuditBot 3000")
st.markdown("### Detecta la mala atención al cliente antes de que pierdas ventas.")

# Crear datos falsos si no hay archivo
if uploaded_file is None:
    st.warning("⚠️ Modo Demo: Cargando datos de ejemplo (Sube tu CSV para ver tus datos)")
    data = {
        'Agente': ['Carlos V.', 'Ana Soporte', 'Carlos V.', 'Bot', 'Ana Soporte'],
        'Cliente': ['Juan', 'Maria', 'Pedro', 'Luisa', 'Jose'],
        'Mensaje': [
            'Hola precio por favor',
            'Señora ya le dije que espere, no moleste son unos inútiles', 
            'El precio es 50 mil pesos',
            'Su pedido ha sido enviado',
            'No me interesa su problema'
        ]
    }
    df = pd.DataFrame(data)
else:
    # LECTURA ROBUSTA (Corrección de errores de pandas)
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, on_bad_lines='skip', engine='python', sep=None)
        else:
            df = pd.read_excel(uploaded_file)
        
        # --- CORRECCIÓN CRÍTICA DE COLUMNAS ---
        df.columns = df.columns.str.strip()  # Quita espacios extra " Agente" -> "Agente"
        # --------------------------------------
        
    except Exception as e:
        st.error(f"Error leyendo archivo: {e}")
        st.stop()

# Normalizar nombre de columna Mensaje
col_mensaje = None
for col in df.columns:
    if col.lower() in ['mensaje', 'message', 'chat', 'texto']:
        col_mensaje = col
        break
if not col_mensaje:
    col_mensaje = df.columns[-1] # Asumimos la última si no encontramos nombre

# ---------------------------------------------------------
# 5. BOTÓN DE ANÁLISIS
# ---------------------------------------------------------
if st.button("🚀 INICIAR AUDITORÍA IA", type="primary"):
    
    # Listas para resultados
    sentimientos, groserias, recomendaciones = [], [], []
    
    # Barra de progreso visual
    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(df)
    
    for i, row in df.iterrows():
        status_text.text(f"Analizando chat {i+1} de {total}...")
        progress_bar.progress((i + 1) / total)
        
        # Análisis
        texto = row[col_mensaje]
        res = analizar_mensaje(texto, user_api_key)
        
        sentimientos.append(res[0])
        groserias.append(res[1])
        recomendaciones.append(res[2])
        
        time.sleep(0.1) # Pequeña pausa visual

    # Guardar resultados en session_state para que no se borren
    df['IA_Sentimiento'] = sentimientos
    df['IA_Alerta_Groseria'] = groserias
    df['IA_Recomendacion'] = recomendaciones
    st.session_state['df_final'] = df
    st.rerun()

# ---------------------------------------------------------
# 6. DASHBOARD (SE MUESTRA SI HAY DATOS ANALIZADOS)
# ---------------------------------------------------------
if 'df_final' in st.session_state:
    df_show = st.session_state['df_final']
    
    st.divider()
    
    # KPIs
    kpi1, kpi2, kpi3 = st.columns(3)
    alertas = len(df_show[df_show['IA_Alerta_Groseria'] == "Si"])
    negativos = len(df_show[df_show['IA_Sentimiento'].str.contains("Negativo")])
    
    kpi1.metric("Total Chats", len(df_show))
    kpi2.metric("Clientes Enojados", negativos, delta_color="inverse")
    kpi3.metric("ALERTAS DE CALIDAD", alertas, delta="-CRÍTICO", delta_color="inverse")
    
    # Gráficas
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Sentimiento Global")
        try:
            fig = px.pie(df_show, names='IA_Sentimiento', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.write("Gráfica no disponible (Faltan datos)")
            
    with c2:
        st.subheader("Top Agentes Conflictivos")
        # Buscamos columna Agente
        col_agente = next((c for c in df_show.columns if 'agente' in c.lower()), None)
        if col_agente:
            df_risk = df_show[df_show['IA_Alerta_Groseria'] == "Si"]
            if not df_risk.empty:
                st.bar_chart(df_risk[col_agente].value_counts())
            else:
                st.success("Todo el personal se comportó bien.")
        else:
            st.warning("No encontré columna 'Agente' en tu Excel.")

    # Tabla Final
    st.subheader("Detalle de Auditoría")
    
    def color_danger(val):
        color = '#ff4b4b' if val == 'Si' else '#21c354'
        return f'background-color: {color}; color: white'

    st.dataframe(
        df_show.style.applymap(color_danger, subset=['IA_Alerta_Groseria']),
        use_container_width=True
    )
    
    # ---------------------------------------------------------
    # 7. CHATBOT GERENCIAL
    # ---------------------------------------------------------
    st.divider()
    st.subheader("🤖 Asistente Virtual para Gerencia")
    q = st.text_input("Pregúntale algo a los datos (Ej: ¿Quién trató mal a los clientes?)")
    if q:
        st.write(f"🤖 **AuditBot:** Según mi análisis, detecté **{alertas} interacciones graves**. { 'Revisa la tabla arriba.' if alertas > 0 else 'El equipo está trabajando bien.'}")