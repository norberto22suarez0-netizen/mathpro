import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import time  
from groq import Groq  
from PIL import Image

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
activar_camara = st.sidebar.checkbox("Activar Cámara", value=False)

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

# --- SIDEBAR: HISTORIAL DE CONSULTAS ---
with st.sidebar.expander("📚 Historial de Consultas"):
    if st.session_state.historial:
        for i, h in enumerate(reversed(st.session_state.historial)):
            st.write(f"**{i+1}.** {h['op']}: `{h['ex']}`")
        st.markdown("---")
        if st.button("🗑️ Borrar Historial", use_container_width=True):
            st.session_state.historial = []
            st.rerun()
    else:
        st.write("Sin consultas previas.")

# --- SIDEBAR: SECCIÓN DE FAVORITOS ---
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
    
    # --- MÓDULO DE CÁMARA REPARADO PARA STREAMLIT CLOUD ---
    if activar_camara:
        st.info("📸 Captura una foto nítida de tu ejercicio matemático.")
        foto_archivo = st.camera_input("Toma la foto aquí")
        
        if foto_archivo is not None:
            with st.spinner("Analizando imagen con el motor visual..."):
                try:
                    # Usamos el API de Groq con capacidades de visión para procesar la imagen sin depender de easyocr
                    client = Groq(api_key=api_key)
                    imagen_bytes = foto_archivo.read()
                    
                    import base64
                    base64_image = base64.b64encode(imagen_bytes).decode('utf-8')
                    
                    response_vision = client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": "Extrae únicamente la expresión matemática de esta imagen. Devuelve SOLO la ecuación en formato de texto plano compatible con Python/SymPy (usa * para multiplicar y ** para potencias). No añadas introducciones, explicaciones ni texto adicional. Ejemplo de salida esperada: x**2 + 3*x + 5"},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                                ]
                            }
                        ],
                        temperature=0.1
                    )
                    
                    texto_detectado = response_vision.choices[0].message.content.strip().lower().replace(" ", "")
                    # Limpieza básica de caracteres comunes de formato markdown que devuelven los LLMs
                    texto_detectado = texto_detectado.replace("`", "").replace("^", "**")
                    
                    if texto_detectado:
                        st.session_state.input_expr = texto_detectado
                        st.success(f"✨ Expresión detectada: `{texto_detectado}`")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al analizar la imagen: {str(e)}")
    
    col1, col2 = st.columns([2, 2])
    with col1:
        lista_ops = ["Simplificar", "Límite", "L'Hopital", "Derivada", "Integral", "Factorizar"]
        operation = st.selectbox("Selecciona operación", lista_ops, index=lista_ops.index(st.session_state.input_op))
    with col2:
        expr = st.text_input("Expresión matemática (Usa * y **):", value=st.session_state.input_expr)
    
    st.session_state.input_expr = expr
    st.session_state.input_op = operation

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
            
            # --- EXPLICACIÓN ORIGINAL DEL MAESTRO RESTAURADA ---
            with st.spinner("Generando explicación académica con Groq..."):
                try:
                    client = Groq(api_key=api_key)
                    prompt = f"Actúa como un profesor excelente de matemáticas de primer año de Ingeniería de Sistemas. Explica detalladamente y paso a paso cómo resolver la operación de {operation} para la expresión {expr}. El resultado matemático obtenido es {result}. Redacta la explicación de forma natural y pedagógica para tus alumnos de la universidad, usando formato LaTeX ($) para que todas las fórmulas se muestren perfectas y elegantes."
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.5
                    )
                    texto_explicacion = response.choices[0].message.content
                except Exception as e:
                    texto_explicacion = f"❌ Error de conexión con Groq: {str(e)}"

            st.session_state.ultimo_calculo = {
                "op": operation, "ex": expr, "result_raw": result, "expr_latex": sp.latex(f),
                "lim_target": lim_target, "explicacion": texto_explicacion, "f_expr": f, "corte_y": corte_y
            }
        except Exception as e:
            st.error(f"Error en la expresión: {str(e)}")

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
        
        st.markdown("#### 💾 Gestión de Material")
        col_sav1, col_sav2 = st.columns(2)
        with col_sav1:
            st.download_button(
                label="📥 Descargar Guía de Procedimiento (.txt)",
                data=f"REPORTE MATHPRO\nOperación: {calc['op']}\nEjercicio: {calc['ex']}\n\n{calc['explicacion']}",
                file_name=f"Procedimiento_{calc['op']}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_sav2:
            if st.button("⭐ Guardar en Mis Ejercicios Favoritos", use_container_width=True):
                nuevo_fav = {"op": calc["op"], "ex": calc["ex"]}
                if nuevo_fav not in st.session_state.favoritos:
                    st.session_state.favoritos.append(nuevo_fav)
                    st.toast("¡Ejercicio añadido a favoritos!", icon="⭐")
                    st.rerun()

        # --- GRÁFICA AL FINAL COMO ESTABA ANTES ---
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
            st.warning("Gráfica no disponible.")

# --- TAB 2: QUIZ INTERACTIVO ---
with tab2:
    st.subheader("📝 Quiz Interactivo con Analíticas y Timer de Presión")
    
    questions = [
        {"pregunta": "Resuelve la ecuación lineal: 3x + 8 = 23", "opciones": ["x = 3", "x = 5", "x = 15", "x = 7"], "correcta": "x = 5", "tema": "Álgebra/Ecuaciones"},
        {"pregunta": "Encuentra la derivada de: x³ + 4x² - 2x", "opciones": ["3x² + 8x", "x² + 8x - 2", "3x² + 8x - 2", "3x² + 4x - 2"], "correcta": "3x² + 8x - 2", "tema": "Derivadas"},
        {"pregunta": "Determina la integral indefinida de: 4x + 5", "opciones": ["2x² + 5x + C", "4x² + 5x + C", "2x² + C", "x² + 5x + C"], "correcta": "2x² + 5x + C", "tema": "Integrales"},
        {"pregunta": "Factoriza la siguiente expresión: x² - 5x + 6", "opciones": ["(x-1)(x-6)", "(x+2)(x+3)", "(x-2)(x-3)", "(x-5)(x+1)"], "correcta": "(x-2)(x-3)", "tema": "Factorización"},
        {"pregunta": "Simplifica desarrollando el producto: (x+2)(x-3)", "opciones": ["x² - x - 6", "x² + x - 6", "x² - 5x - 6", "x² - 6"], "correcta": "x² - x - 6", "tema": "Álgebra/Ecuaciones"}
    ]
    
    if 'q' not in st.session_state:
        st.session_state.q = 0
        st.session_state.score = 0
        st.session_state.lives = 3
        st.session_state.respondido = False
        st.session_state.start_time = time.time()

    st.markdown(f"### Vidas restantes: {'❤️ ' * st.session_state.lives}")
    
    mostrar_analisis = False
    tiempo_total = 0.0

    if st.session_state.lives <= 0:
        st.error("💀 ¡GAME OVER! Te has quedado sin vidas.")
        mostrar_analisis = True
        tiempo_total = time.time() - st.session_state.start_time
            
    elif st.session_state.q < len(questions):
        current_quiz = questions[st.session_state.q]
        st.write(f"**Pregunta {st.session_state.q + 1} de {len(questions)}:** {current_quiz['pregunta']}")
        
        user_ans = st.radio("Selecciona la opción correcta:", current_quiz['opciones'], index=None, key=f"radio_q{st.session_state.q}")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Enviar Respuesta", type="primary", disabled=st.session_state.respondido):
                if user_ans is None:
                    st.warning("⚠️ Por favor selecciona una opción.")
                else:
                    if user_ans == current_quiz['correcta']:
                        st.session_state.score += 1
                        st.success("✅ ¡Correcto!")
                    else:
                        st.session_state.lives -= 1
                        tema_afectado = current_quiz['tema']
                        st.session_state.errores_quiz[tema_afectado] += 1
                        st.error(f"❌ Incorrecto. Respuesta correcta: **{current_quiz['correcta']}**")
                    st.session_state.respondido = True
                    st.rerun()
                    
        with col_btn2:
            if st.session_state.respondido:
                if st.button("Siguiente Pregunta ➡️"):
                    st.session_state.q += 1
                    st.session_state.respondido = False
                    st.rerun()
    else:
        st.success(f"🎉 ¡Quiz terminado!")
        mostrar_analisis = True
        tiempo_total = time.time() - st.session_state.start_time

    if mostrar_analisis:
        st.markdown("---")
        st.markdown("### ⏱️ Métricas de Eficiencia Temporales")
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.metric("Tiempo Total de Resolución", f"{int(tiempo_total // 60)}m {int(tiempo_total % 60)}s")
        with col_t2:
            preguntas_respondidas = st.session_state.q if st.session_state.q > 0 else 1
            st.metric("Velocidad Promedio por Pregunta", f"{tiempo_total / preguntas_respondidas:.2f} segundos")
        
        st.markdown("### 📊 Reporte Analítico de Rendimiento")
        st.bar_chart(st.session_state.errores_quiz)
        
        tema_critico = max(st.session_state.errores_quiz, key=st.session_state.errores_quiz.get)
        max_errores = st.session_state.errores_quiz[tema_critico]
        
        if max_errores > 0:
            st.warning(f"🔍 Nuestro sistema detecta debilidades en la categoría: **{tema_critico}**")
            if st.button("Generar Ejercicio de Refuerzo"):
                with st.spinner("Generando un ejercicio a tu medida..."):
                    client = Groq(api_key=api_key)
                    prompt_practica = f"Genera un ejercicio de nivel primer año de ingeniería basado estrictamente en el tema: {tema_critico}. Muestra el enunciado y abajo una solución explicada detalladamente usando LaTeX ($)."
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt_practica}],
                        temperature=0.7
                    )
                    st.info(response.choices[0].message.content)
        else:
            st.success("😎 ¡Excelente balance! No tienes un tema crítico predominante en este intento.")

        if st.button("Reiniciar Cuestionario Completo"):
            st.session_state.q = 0
            st.session_state.score = 0
            st.session_state.lives = 3
            st.session_state.respondido = False
            st.session_state.errores_quiz = {"Álgebra/Ecuaciones": 0, "Derivadas": 0, "Integrales": 0, "Factorización": 0}
            st.session_state.start_time = time.time()
            st.rerun()

# --- TAB 3: FORMULARIO INTERACTIVO ---
with tab3:
    st.subheader("📋 Formulario de Referencia Rápida Matemática")
    
    col_sheet1, col_sheet2 = st.columns(2)
    with col_sheet1:
        st.markdown("#### 📐 Álgebra, Simplificación y Factorización")
        st.latex(r"x^2 - y^2 = (x - y)(x + y)")
        st.latex(r"(x \pm y)^2 = x^2 \pm 2xy + y^2")
        st.latex(r"x^3 \pm y^3 = (x \pm y)(x^2 \mp xy + y^2)")
        
        st.markdown("---")
        st.markdown("#### 🎯 Límites Matemáticos y Regla de L'Hôpital")
        st.latex(r"\lim_{x \to 0} \frac{\sin(x)}{x} = 1")
        st.latex(r"\lim_{x \to \infty} \left(1 + \frac{1}{x}\right)^x = e")
        st.markdown("Si se genera una indeterminación del tipo $\\frac{0}{0}$ o $\\frac{\\infty}{\\infty}$:")
        st.latex(r"\lim_{x \to c} \frac{f(x)}{g(x)} = \lim_{x \to c} \frac{f'(x)}{g'(x)}")
        
    with col_sheet2:
        st.markdown("#### ⚡ Derivadas de Funciones Elementales")
        st.latex(r"\frac{d}{dx}\left[x^n\right] = n \cdot x^{n-1}")
        st.latex(r"\frac{d}{dx}\left[e^x\right] = e^x")
        st.latex(r"\frac{d}{dx}\left[\ln(x)\right] = \frac{1}{x}")
        st.latex(r"\frac{d}{dx}\left[\sin(x)\right] = \cos(x)")
        st.latex(r"\frac{d}{dx}\left[\cos(x)\right] = -\sin(x)")
        
        st.markdown("---")
        st.markdown("#### 📈 Integrales Inmediatas")
        st.latex(r"\int k \, dx = kx + C")
        st.latex(r"\int x^n \, dx = \frac{x^{n+1}}{n+1} + C \quad (n \neq -1)")
        st.latex(r"\int \frac{1}{x} \, dx = \ln|x| + C")
        st.latex(r"\int e^x \, dx = e^x + C")
        st.latex(r"\int \sin(x) \, dx = -\cos(x) + C")
        st.latex(r"\int \cos(x) \, dx = \sin(x) + C")
