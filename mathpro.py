import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import time  # Para el cronómetro de optimización
from groq import Groq  
from PIL import Image

# NOTA: Para que el OCR funcione, necesitas instalar: pip install pytesseract easyocr
# Usaremos una lógica de simulación de OCR nativa o puedes implementar 'easyocr' fácilmente.
try:
    import easyocr
    reader = easyocr.Reader(['en']) # Inicializa el lector OCR
except ImportError:
    reader = None

st.set_page_config(page_title="MathPro Professional", layout="wide", page_icon="📐")

# --- 1. CONFIGURACIÓN DE TEMAS VISUALES ---
if 'theme' not in st.session_state:
    st.session_state.theme = "Clásico Universitario"

# Sidebar - Configuración
st.sidebar.header("⚙️ Configuración")

# Selector de Tema Visual
st.session_state.theme = st.sidebar.selectbox(
    "Paleta de Colores", 
    ["Clásico Universitario", "Hacker Mode 💻", "Orgullo UNI 🔵"]
)

# Control de rango interactivo para la gráfica en la barra lateral
st.sidebar.markdown("### 📈 Control de Gráfica")
rango_x = st.sidebar.slider("Rango de visualización (Eje X)", 1, 50, 10, help="Define los límites -N a N para la gráfica")

# --- NUEVA FUNCIÓN: ACTIVAR MÓDULO DE CÁMARA ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📷 Escáner de Ejercicios")
activar_camara = st.sidebar.checkbox("Activar Cámara / OCR", value=False, help="Permite tomar una foto a un ejercicio escrito")

# Inyección de CSS según el tema seleccionado
if st.session_state.theme == "Hacker Mode 💻":
    st.markdown("""
        <style>
        .stApp { background-color: #0d1117; color: #39ff14; }
        [data-testid="stSidebar"] { background-color: #161b22 !important; }
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { 
            color: #39ff14 !important; 
            font-family: 'Courier New', Courier, monospace; 
        }
        [data-testid="stSidebar"] div[data-baseweb="select"] > div, 
        [data-testid="stSidebar"] input {
            background-color: #21262d !important;
            color: #39ff14 !important;
            border: 1px solid #39ff14 !important;
        }
        div[data-baseweb="popover"] li {
            background-color: #21262d !important;
            color: #39ff14 !important;
        }
        h1, h2, h3, h4, h5, h6, label, p, .stMarkdown, span { 
            color: #39ff14 !important; 
            font-family: 'Courier New', Courier, monospace; 
        }
        .stButton>button { 
            background-color: #21262d; 
            color: #39ff14; 
            border: 1px solid #39ff14; 
        }
        .stButton>button:hover { 
            background-color: #39ff14; 
            color: #0d1117; 
        }
        </style>
    """, unsafe_allow_html=True)

elif st.session_state.theme == "Orgullo UNI 🔵":
    st.markdown("""
        <style>
        /* Fondo de la aplicación */
        .stApp { background-color: #f8fafc; }
        
        /* Barra lateral (Sidebar) - Fondo azul con letras blancas */
        [data-testid="stSidebar"] { background-color: #003366 !important; }
        [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { 
            color: #ffffff !important; 
        }
        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {
            background-color: #ffffff !important;
            color: #333333 !important;
        }
        
        /* CUERPO PRINCIPAL */
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, span { 
            color: #1e293b !important; 
        }
        
        /* Títulos principales en el azul de la UNI */
        h1, h2, h3 { color: #003366 !important; }
        
        /* Asegurar que el texto dentro de los inputs sea oscuro */
        div[data-baseweb="select"] > div, input {
            color: #1e293b !important;
            background-color: #ffffff !important;
        }
        
        /* Estilo de los botones */
        .stButton>button { 
            background-color: #003366; 
            color: white !important; 
            border: none;
            border-radius: 8px;
        }
        .stButton>button:hover { 
            background-color: #002244; 
            color: #ffffff !important; 
        }
        </style>
    """, unsafe_allow_html=True)

# API Key
api_key = st.sidebar.text_input(
    "API", 
    type="password", 
    value="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"
)
st.sidebar.markdown("---")

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
if 'historial' not in st.session_state:
    st.session_state.historial = []
if 'errores_quiz' not in st.session_state:
    st.session_state.errores_quiz = {"Álgebra/Ecuaciones": 0, "Derivadas": 0, "Integrales": 0, "Factorización": 0}
if 'favoritos' not in st.session_state:
    st.session_state.favoritos = []

if 'input_expr' not in st.session_state:
    st.session_state.input_expr = "x**2 + 3*x + 5"
if 'input_op' not in st.session_state:
    st.session_state.input_op = "Simplificar"

if 'ultimo_calculo' not in st.session_state:
    st.session_state.ultimo_calculo = None

# --- SIDEBAR: HISTORIAL Y FAVORITOS ---
with st.sidebar.expander("📚 Historial de Consultas"):
    if st.session_state.historial:
        for i, h in enumerate(reversed(st.session_state.historial)):
            st.write(f"**{i+1}.** {h['op']}: `{h['ex']}`")
        st.markdown("---")
        if st.button("🗑️ Borrar Historial", use_container_width=True):
            st.session_state.historial = []
            st.rerun()
    else:
        st.write("Aún no has realizado cálculos.")

with st.sidebar.expander("⭐ Ejercicios Favoritos"):
    if st.session_state.favoritos:
        for idx, fav in enumerate(st.session_state.favoritos):
            col_fav1, col_fav2 = st.columns([3, 1])
            with col_fav1:
                st.write(f"**{fav['op']}**: `{fav['ex']}`")
            with col_fav2:
                if st.button("🔄", key=f"load_fav_{idx}"):
                    st.session_state.input_expr = fav['ex']
                    st.session_state.input_op = fav['op']
                    st.rerun()
        st.markdown("---")
        if st.button("🗑️ Vaciar Favoritos", use_container_width=True):
            st.session_state.favoritos = []
            st.rerun()
    else:
        st.write("No tienes elementos guardados.")

st.sidebar.markdown("---")
st.sidebar.markdown("**App diseñada para jóvenes universitarios de la materia de Matemática I**")

st.title("📐 MathPro - Calculadora")
st.markdown("### 1er Año Ingeniería de Sistemas")

tab1, tab2, tab3 = st.tabs(["🧮 Calculadora Avanzada", "📝 Quiz de Evaluación", "📋 Fórmulas Útiles"])

# --- TAB 1: CALCULADORA ---
with tab1:
    st.subheader("Calculadora Avanzada con Procedimientos")
    
    # LÓGICA DE PROCESAMIENTO DE CÁMARA (OCR)
    if activar_camara:
        st.info("📸 Captura un ejercicio claro escrito en papel o pizarra.")
        foto_archivo = st.camera_input("Toma la foto aquí")
        
        if foto_archivo is not None:
            with st.spinner("Analizando trazos de la imagen..."):
                try:
                    imagen_pil = Image.open(foto_archivo)
                    # Convertir a arreglo numpy para EasyOCR
                    img_np = np.array(imagen_pil)
                    
                    if reader is not None:
                        resultado_ocr = reader.readtext(img_np, detail=0)
                        if resultado_ocr:
                            # Unir los fragmentos detectados y limpiar espacios comunes
                            texto_detectado = "".join(resultado_ocr).replace(" ", "").lower()
                            # Reemplazos básicos para ajustar a sintaxis Python
                            texto_detectado = texto_detectado.replace("^", "**")
                            st.session_state.input_expr = texto_detectado
                            st.success(f"✨ Texto detectado con éxito: `{texto_detectado}`")
                        else:
                            st.warning("⚠️ No se pudo extraer texto claro. Intenta con mejor iluminación.")
                    else:
                        # Modo simulación por si no tienes instalado EasyOCR en local todavía
                        st.warning("Librería de visión EasyOCR no detectada en el entorno. Cargando demo analítico...")
                        st.session_state.input_expr = "x**2 / (x - 1)"
                        
                except Exception as e:
                    st.error(f"Error en el escaneo: {str(e)}")

    col1, col2 = st.columns([2, 2])
    with col1:
        lista_ops = ["Simplificar", "Límite", "L'Hopital", "Derivada", "Integral", "Factorizar"]
        default_index = lista_ops.index(st.session_state.input_op) if st.session_state.input_op in lista_ops else 0
        operation = st.selectbox("Selecciona operación", lista_ops, index=default_index)
    with col2:
        expr = st.text_input("Expresión matemática (Usa * para multiplicar y ** para potencias):", value=st.session_state.input_expr)
    
    st.session_state.input_expr = expr
    st.session_state.input_op = operation

    # [El resto de la lógica de tu Tab 1, Tab 2 y Tab 3 se mantiene exactamente igual]
    orden_derivada = 1
    tipo_integral = "Indefinida"
    lim_a, lim_b = "-1", "1"
    lim_target = "0"

    if operation in ["Límite", "L'Hopital"]:
        st.markdown("##### 🎯 Configuración del Límite")
        col_lim1, _ = st.columns(2)
        with col_lim1: lim_target = st.text_input("¿A qué valor tiende x?", "0")
            
    elif operation == "Derivada":
        st.markdown("##### ⚡ Configuración de la Derivada")
        col_der1, _ = st.columns(2)
        with col_der1: orden_derivada = st.selectbox("Orden de la derivada:", [1, 2, 3], format_func=lambda x: f"{x}ª Derivada")

    elif operation == "Integral":
        st.markdown("##### 📐 Configuración de la Integral")
        col_int1, col_int2 = st.columns(2)
        with col_int1: tipo_integral = st.radio("Tipo de integral:", ["Indefinida", "Definida"], horizontal=True)
        with col_int2:
            if tipo_integral == "Definida":
                col_ab1, col_ab2 = st.columns(2)
                with col_ab1: lim_a = st.text_input("Límite inferior (a):", "-1")
                with col_ab2: lim_b = st.text_input("Límite superior (b):", "1")
    
    if st.button("Calcular Todo", type="primary", use_container_width=True):
        if not api_key:
            st.error("❌ Por favor, ingresa tu API en la barra lateral.")
        else:
            try:
                x = sp.symbols('x')
                f = sp.sympify(expr)
                
                if operation == "Derivada": result = sp.diff(f, x, orden_derivada)
                elif operation == "Integral":
                    if tipo_integral == "Definida": result = sp.integrate(f, (x, sp.sympify(lim_a), sp.sympify(lim_b)))
                    else:
                        result = sp.integrate(f, x)
                        if result != sp.Integral(f, x): result = f"{result} + C"
                elif operation == "Factorizar": result = sp.factor(f)
                elif operation in ["Límite", "L'Hopital"]: result = sp.limit(f, x, sp.sympify(lim_target))
                else: result = sp.simplify(f)
                
                try: corte_y = f.subs(x, 0); corte_y_str = str(corte_y)
                except Exception: corte_y_str = "No definido"

                st.session_state.historial.append({"op": operation, "ex": expr})
                if len(st.session_state.historial) > 5: st.session_state.historial.pop(0)
                
                with st.spinner("Explicando el ejercicio..."):
                    client = Groq(api_key=api_key)
                    prompt_extra = f"El límite se evalúa cuando x tiende a {lim_target}." if operation in ["Límite", "L'Hopital"] else ""
                    instruccion_pizarra = """
                    REGLAS DE FORMATO MATEMÁTICO DE PIZARRA (OBLIGATORIO):
                    1. Prohibido formato de computadora (* o **). Usar LaTeX con $ o $$.
                    2. Al final agrega: '### 🔢 Procedimiento Directo (Vertical)' en bloques $$ independientes.
                    """
                    prompt_profesor = f"Actúa como catedrático de ingeniería. Operación: {operation} | Expresión: ${sp.latex(f)}$ | Resultado: ${sp.latex(result) if not isinstance(result, str) else result}$ {prompt_extra} {instruccion_pizarra}"
                        
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": "Eres un catedrático universitario que escribe en pizarra con LaTeX."},
                            {"role": "user", "content": prompt_profesor}
                        ], temperature=0.3
                    )
                    texto_explicacion = response.choices[0].message.content
                
                st.session_state.ultimo_calculo = {
                    "op": operation, "ex": expr, "result_str": sp.latex(result) if not isinstance(result, str) else result,
                    "expr_latex": sp.latex(f), "lim_target": lim_target, "explicacion": texto_explicacion, "f_expr": f, "corte_y": corte_y_str
                }
            except Exception as e:
                st.error(f"Error en el procesamiento: {str(e)}")

    if st.session_state.ultimo_calculo is not None:
        calc = st.session_state.ultimo_calculo
        st.markdown("---")
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            if calc["op"] in ["Límite", "L'Hopital"]: st.info(f"**Expresión Original:**\n$\\lim_{{x \\to {calc['lim_target']}}} ({calc['expr_latex']})$")
            else: st.info(f"**Expresión Original:**\n$f(x) = {calc['expr_latex']}$")
        with col_res2: st.success(f"**Resultado Matemático ({calc['op']}):** ${calc['result_str']}$")
        with col_res3: st.metric(label="Corte con Eje Y f(0)", value=calc["corte_y"])
        
        st.subheader(" Explicación Paso a Paso")
        st.markdown(calc["explicacion"])
        
        # Gráfica
        st.subheader("📈 Gráfica de la función original")
        try:
            x = sp.symbols('x')
            f_num = sp.lambdify(x, calc["f_expr"], "numpy")
            x_vals = np.linspace(-rango_x, rango_x, 400)
            y_vals = f_num(x_vals)
            if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(x_vals, y_vals, color="#003366" if st.session_state.theme == "Orgullo UNI 🔵" else "#2ca02c", linewidth=2)
            ax.axhline(0, color='black', linewidth=0.5, ls='--')
            ax.axvline(0, color='black', linewidth=0.5, ls='--')
            ax.grid(True, linestyle=':', alpha=0.6)
            st.pyplot(fig)
        except Exception: st.warning("Nota: Gráfica analítica no disponible.")

# [El código restante del Quiz y Formulario de tu script original continúa intacto abajo]
