import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import time  
from groq import Groq  
from PIL import Image

# Intentar cargar EasyOCR de forma segura para el escáner
try:
    import easyocr
    @st.cache_resource
    def load_ocr():
        return easyocr.Reader(['en'])
    reader = load_ocr()
except Exception:
    reader = None

st.set_page_config(page_title="MathPro Professional", layout="wide", page_icon="📐")

# --- 1. CONFIGURACIÓN DE TEMAS VISUALES ---
if 'theme' not in st.session_state:
    st.session_state.theme = "Clásico Universitario"

st.sidebar.header("⚙️ Configuración")
st.session_state.theme = st.sidebar.selectbox(
    "Paleta de Colores", 
    ["Clásico Universitario", "Hacker Mode 💻", "Orgullo UNI 🔵"]
)

rango_x = st.sidebar.slider("Rango de visualización (Eje X)", 1, 50, 10)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📷 Escáner de Ejercicios")
activar_camara = st.sidebar.checkbox("Activar Cámara / OCR", value=False)

# Inyección de CSS de los temas visuales
if st.session_state.theme == "Hacker Mode 💻":
    st.markdown("<style>.stApp { background-color: #0d1117; color: #39ff14; } h1, h2, h3, h4, label, p, span { color: #39ff14 !important; font-family: 'Courier New'; }</style>", unsafe_allow_html=True)
elif st.session_state.theme == "Orgullo UNI 🔵":
    st.markdown("<style>.stApp { background-color: #f8fafc; } h1, h2, h3 { color: #003366 !important; } .stButton>button { background-color: #003366; color: white !important; }</style>", unsafe_allow_html=True)

# --- API KEY DE GROQ INTEGRADA AUTOMÁTICAMENTE ---
api_key = "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"

# Inicialización de estados de la sesión
if 'historial' not in st.session_state: st.session_state.historial = []
if 'errores_quiz' not in st.session_state: st.session_state.errores_quiz = {"Álgebra/Ecuaciones": 0, "Derivadas": 0, "Integrales": 0, "Factorización": 0}
if 'favoritos' not in st.session_state: st.session_state.favoritos = []
if 'input_expr' not in st.session_state: st.session_state.input_expr = "x**2 + 3*x + 5"
if 'input_op' not in st.session_state: st.session_state.input_op = "Simplificar"
if 'ultimo_calculo' not in st.session_state: st.session_state.ultimo_calculo = None

# --- COMPONENTES DE LA BARRA LATERAL ---
with st.sidebar.expander("📚 Historial de Consultas"):
    if st.session_state.historial:
        for i, h in enumerate(reversed(st.session_state.historial)):
            st.write(f"**{i+1}.** {h['op']}: `{h['ex']}`")
        if st.button("🗑️ Borrar Historial"):
            st.session_state.historial = []
            st.rerun()
    else:
        st.write("Sin consultas previas.")

st.title("📐 MathPro - Calculadora")
st.markdown("### 1er Año Ingeniería de Sistemas")

tab1, tab2, tab3 = st.tabs(["🧮 Calculadora Avanzada", "📝 Quiz de Evaluación", "📋 Fórmulas Útiles"])

# --- TAB 1: CALCULADORA ---
with tab1:
    st.subheader("Calculadora Avanzada con Procedimientos")
    
    if activar_camara:
        foto_archivo = st.camera_input("Toma la foto aquí")
        if foto_archivo is not None and reader is not None:
            with st.spinner("Escaneando imagen..."):
                try:
                    imagen_pil = Image.open(foto_archivo)
                    resultado_ocr = reader.readtext(np.array(imagen_pil), detail=0)
                    if resultado_ocr:
                        st.session_state.input_expr = "".join(resultado_ocr).replace(" ", "").lower().replace("^", "**")
                        st.success(f"✨ Detectado: `{st.session_state.input_expr}`")
                except Exception as e:
                    st.error(f"Error de escaneo: {e}")
    
    col1, col2 = st.columns([2, 2])
    with col1:
        lista_ops = ["Simplificar", "Límite", "L'Hopital", "Derivada", "Integral", "Factorizar"]
        operation = st.selectbox("Selecciona operación", lista_ops, index=lista_ops.index(st.session_state.input_op))
    with col2:
        expr = st.text_input("Expresión matemática (Usa * y **):", value=st.session_state.input_expr)
    
    st.session_state.input_expr = expr
    st.session_state.input_op = operation

    # Variables de control
    lim_target = "0"
    orden_derivada = 1
    tipo_integral = "Indefinida"
    lim_a, lim_b = "-1", "1"

    if operation in ["Límite", "L'Hopital"]:
        lim_target = st.text_input("¿A qué valor tiende x?", "0")
    elif operation == "Derivada":
        orden_derivada = st.selectbox("Orden:", [1, 2, 3], format_func=lambda x: f"{x}ª Derivada")
    elif operation == "Integral":
        tipo_integral = st.radio("Tipo:", ["Indefinida", "Definida"], horizontal=True)
        if tipo_integral == "Definida":
            c_a, c_b = st.columns(2)
            with c_a: lim_a = st.text_input("Límite inferior (a):", "-1")
            with c_b: lim_b = st.text_input("Límite superior (b):", "1")
    
    if st.button("Calcular Todo", type="primary", use_container_width=True):
        try:
            x = sp.symbols('x')
            f = sp.sympify(expr)
            
            # Procesamiento matemático de SymPy
            if operation == "Derivada": result = sp.diff(f, x, orden_derivada)
            elif operation == "Integral":
                if tipo_integral == "Definida": result = sp.integrate(f, (x, sp.sympify(lim_a), sp.sympify(lim_b)))
                else: result = f"{sp.integrate(f, x)} + C"
            elif operation == "Factorizar": result = sp.factor(f)
            elif operation in ["Límite", "L'Hopital"]: result = sp.limit(f, x, sp.sympify(lim_target))
            else: result = sp.simplify(f)
            
            try: corte_y = str(f.subs(x, 0))
            except Exception: corte_y = "No definido"

            st.session_state.historial.append({"op": operation, "ex": expr})
            
            # Llamada al motor LLM de Groq
            with st.spinner("Generando explicación académica con Groq..."):
                try:
                    client = Groq(api_key=api_key)
                    prompt = f"Actúa como profesor de matemáticas universitarias. Explica paso a paso de forma clara la operación {operation} para la función ${sp.latex(f)}$ cuyo resultado es ${sp.latex(result) if not isinstance(result, str) else result}$. Usa exclusivamente LaTeX ($) para todas las expresiones matemáticas. Al final agrega una sección llamada '### 🔢 Procedimiento Directo (Vertical)' estructurada en líneas $$ consecutivas."
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3
                    )
                    texto_explicacion = response.choices[0].message.content
                except Exception as e:
                    texto_explicacion = f"❌ Error de conexión con la IA de Groq: {str(e)}"

            st.session_state.ultimo_calculo = {
                "op": operation, "ex": expr, "result_raw": result, "expr_latex": sp.latex(f),
                "lim_target": lim_target, "explicacion": texto_explicacion, "f_expr": f, "corte_y": corte_y
            }
        except Exception as e:
            st.error(f"Error en el procesamiento matemático de la expresión: {str(e)}")

    # Despliegue visual de resultados corregido para LaTeX
    if st.session_state.ultimo_calculo is not None:
        calc = st.session_state.ultimo_calculo
        st.markdown("---")
        res_col1, res_col2, res_col3 = st.columns(3)
        
        with res_col1:
            st.info("**Expresión Registrada:**")
            if calc["op"] in ["Límite", "L'Hopital"]: st.latex(f"\\lim_{{x \\to {calc['lim_target']}}} ({calc['expr_latex']})")
            else: st.latex(f"f(x) = {calc['expr_latex']}")
            
        with res_col2:
            st.success(f"**Resultado ({calc['op']}):**")
            st.latex(sp.latex(calc["result_raw"]) if not isinstance(calc["result_raw"], str) else calc["result_raw"])
            
        with res_col3:
            st.metric(label="Corte Eje Y f(0)", value=calc["corte_y"])
        
        st.subheader("📝 Explicación del Catedrático")
        st.markdown(calc["explicacion"])
        
        # Renderizado de Gráfica
        st.subheader("📈 Gráfica de la Función")
        try:
            x = sp.symbols('x')
            f_num = sp.lambdify(x, calc["f_expr"], "numpy")
            x_vals = np.linspace(-rango_x, rango_x, 400)
            y_vals = f_num(x_vals)
            if isinstance(y_vals, (int, float)): y_vals = np.full_like(x_vals, y_vals)
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.plot(x_vals, y_vals, color="#003366" if st.session_state.theme == "Orgullo UNI 🔵" else "#2ca02c", linewidth=2)
            ax.axhline(0, color='black', linewidth=0.5, ls='--')
            ax.axvline(0, color='black', linewidth=0.5, ls='--')
            ax.grid(True, linestyle=':', alpha=0.6)
            st.pyplot(fig)
        except Exception:
            st.warning("Gráfica no disponible para esta función.")

# --- TAB 2: QUIZ INTERACTIVO ---
with tab2:
    st.subheader("📝 Quiz de Autoevaluación")
    questions = [
        {"pregunta": "Resuelve: 3x + 8 = 23", "opciones": ["x = 3", "x = 5", "x = 15"], "correcta": "x = 5", "tema": "Álgebra/Ecuaciones"},
        {"pregunta": "Derivada de: x³ + 4x²", "opciones": ["3x² + 8x", "x² + 8x", "3x² + 4"], "correcta": "3x² + 8x", "tema": "Derivadas"}
    ]
    
    if 'q' not in st.session_state:
        st.session_state.q, st.session_state.score, st.session_state.lives = 0, 0, 3
        st.session_state.respondido, st.session_state.start_time = False, time.time()

    if st.session_state.lives <= 0:
        st.error("💀 ¡Game Over! Inténtalo de nuevo.")
        if st.button("Reiniciar Quiz"): 
            st.session_state.q = 0; st.session_state.lives = 3; st.rerun()
    elif st.session_state.q < len(questions):
        st.markdown(f"**Vidas:** {'❤️ ' * st.session_state.lives}")
        current = questions[st.session_state.q]
        st.write(f"**Pregunta:** {current['pregunta']}")
        ans = st.radio("Selecciona una opción:", current['opciones'], index=None, key=f"q_{st.session_state.q}")
        
        if st.button("Validar", disabled=st.session_state.respondido):
            if ans == current['correcta']: st.success("¡Excelente!")
            else:
                st.session_state.lives -= 1
                st.error(f"Incorrecto. Era {current['correcta']}")
            st.session_state.respondido = True
            st.rerun()
            
        if st.session_state.respondido and st.button("Continuar"):
            st.session_state.q += 1
            st.session_state.respondido = False
            st.rerun()
    else:
        st.success("🎉 ¡Felicidades! Completaste el cuestionario.")

# --- TAB 3: FORMULARIO INTERACTIVO ---
with tab3:
    st.subheader("📋 Formulario de Referencia Rápida")
    c_form1, c_form2 = st.columns(2)
    with c_form1:
        st.markdown("#### 📐 Álgebra y Límites")
        st.latex(r"x^2 - y^2 = (x - y)(x + y)")
        st.latex(r"\lim_{x \to 0} \frac{\sin(x)}{x} = 1")
    with c_form2:
        st.markdown("#### ⚡ Derivadas e Integrales")
        st.latex(r"\frac{d}{dx}[x^n] = n \cdot x^{n-1}")
        st.latex(r"\int x^n \, dx = \frac{x^{n+1}}{n+1} + C")
