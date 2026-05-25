import streamlit as st
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt
import time  # Para el cronómetro de optimización
from groq import Groq  # Librería oficial de Groq

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
        
        /* CUERPO PRINCIPAL: Forzar letras oscuras para que se lean sobre el fondo blanco */
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown, span { 
            color: #1e293b !important; 
        }
        
        /* Títulos principales en el azul de la UNI */
        h1, h2, h3 { color: #003366 !important; }
        
        /* Asegurar que el texto dentro de los inputs y dropdowns principales sea oscuro */
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

# API Key configurada por defecto
api_key = st.sidebar.text_input(
    "API Key de Groq", 
    type="password", 
    value="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"
)
st.sidebar.markdown("---")

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO (SESSION STATE) ---
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

# --- SIDEBAR: HISTORIAL ---
with st.sidebar.expander("📚 Historial de Consultas"):
    if st.session_state.historial:
        for i, h in enumerate(reversed(st.session_state.historial)):
            st.write(f"**{i+1}.** {h['op']}: `{h['ex']}`")
        
        st.markdown("---")
        if st.button("🗑️ Borrar Historial", use_container_width=True):
            st.session_state.historial = []
            st.toast("Historial de consultas eliminado.", icon="🗑️")
            st.rerun()
    else:
        st.write("Aún no has realizado cálculos.")

# --- SIDEBAR: FAVORITOS ---
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
            st.toast("Lista de favoritos eliminada con éxito.", icon="⭐")
            st.rerun()
    else:
        st.write("No tienes elementos guardados.")

st.sidebar.markdown("---")
st.sidebar.markdown("**App diseñada para jóvenes universitarios de la materia de Matemática I**")

st.title("📐 MathPro - Calculadora Universitaria")
st.markdown("### 1er Año Ingeniería de Sistemas - Con Asistente Avanzado")

tab1, tab2, tab3 = st.tabs(["🧮 Calculadora Avanzada", "📝 Quiz de Evaluación", "📋 Fórmulas Útiles"])

# --- TAB 1: CALCULADORA ---
with tab1:
    st.subheader("Calculadora Avanzada con Procedimientos")
    
    # --- MÓDULO DE VISIÓN (PROCESAMIENTO POR FOTO) ---
    with st.expander("📸 Cargar Ejercicio por Foto / Captura (Módulo Vision AI REAL)"):
        st.write("Sube una imagen nítida del ejercicio matemático:")
        uploaded_image = st.file_uploader("Elige una imagen...", type=["png", "jpg", "jpeg"])
        
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Imagen cargada", use_container_width=True)
            
            if st.button("Procesar Imagen con IA"):
                if not api_key:
                    st.error("❌ Por favor, ingresa tu API Key de Groq en la barra lateral.")
                else:
                    import base64
                    try:
                        bytes_data = uploaded_image.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')
                        
                        with st.spinner("La IA está leyendo tu imagen..."):
                            client = Groq(api_key=api_key)
                            # Modelo actualizado a producción para evitar Decommissioned / 404
                            response = client.chat.completions.create(
                                model="llama-3.2-11b-vision-instruct",
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": "Analiza la imagen y extrae ÚNICAMENTE la expresión matemática o ecuación que veas. Devuélvela formateada para Python/Sympy (por ejemplo, usa * para multiplicar y ** para potencias). No agregues saludos ni explicaciones, solo la expresión."},
                                            {
                                                "type": "image_url",
                                                "image_url": {
                                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                                }
                                            }
                                        ]
                                    }
                                ],
                                temperature=0.0
                            )
                            
                            resultado_ia = response.choices[0].message.content.strip()
                            st.session_state.input_expr = resultado_ia
                            st.success(f"🤖 IA detectó la expresión: `{resultado_ia}`")
                            st.toast("¡Expresión cargada en la barra de cálculo!", icon="✅")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Error al conectar con el módulo de visión: {str(e)}")
                        st.warning("⚠️ El servidor de visión de Groq se encuentra saturado o el modelo cambió de ID.")
                        st.info("💡 Tip: Podés escribir la ecuación directamente en el cuadro de texto de abajo mientras se restablece el nodo visual.")

    col1, col2 = st.columns([2, 2])
    with col1:
        lista_ops = ["Simplificar", "Límite", "Derivada", "Integral", "Resolver Ecuación", "Factorizar", "Expandir"]
        default_index = lista_ops.index(st.session_state.input_op) if st.session_state.input_op in lista_ops else 0
        operation = st.selectbox("Selecciona operación", lista_ops, index=default_index)
    with col2:
        expr = st.text_input("Expresión matemática (Usa * para multiplicar y ** para potencias):", value=st.session_state.input_expr)
    
    st.session_state.input_expr = expr
    st.session_state.input_op = operation

    orden_derivada = 1
    tipo_integral = "Indefinida"
    lim_a, lim_b = "-1", "1"
    lim_target = "0"

    if operation == "Límite":
        st.markdown("##### 🎯 Configuración del Límite")
        col_lim1, _ = st.columns(2)
        with col_lim1:
            lim_target = st.text_input("¿A qué valor tiende x? (Usa un número o 'oo' para infinito):", "0")
            
    elif operation == "Derivada":
        st.markdown("##### ⚡ Configuración de la Derivada")
        col_der1, _ = st.columns(2)
        with col_der1:
            orden_derivada = st.selectbox("Orden de la derivada:", [1, 2, 3], format_func=lambda x: f"{x}ª Derivada")

    elif operation == "Integral":
        st.markdown("##### 📐 Configuración de la Integral")
        col_int1, col_int2 = st.columns(2)
        with col_int1:
            tipo_integral = st.radio("Tipo de integral:", ["Indefinida", "Definida"], horizontal=True)
        with col_int2:
            if tipo_integral == "Definida":
                col_ab1, col_ab2 = st.columns(2)
                with col_ab1: lim_a = st.text_input("Límite inferior (a):", "-1")
                with col_ab2: lim_b = st.text_input("Límite superior (b):", "1")
    
    if st.button("Calcular Todo", type="primary", use_container_width=True):
        if not api_key:
            st.error("❌ Por favor, ingresa tu API Key de Groq en la barra lateral.")
        else:
            try:
                x = sp.symbols('x')
                f = sp.sympify(expr)
                
                if operation == "Derivada":
                    result = sp.diff(f, x, orden_derivada)
                elif operation == "Integral":
                    if tipo_integral == "Definida":
                        result = sp.integrate(f, (x, sp.sympify(lim_a), sp.sympify(lim_b)))
                    else:
                        result = sp.integrate(f, x)
                        if result != sp.Integral(f, x):
                            result = f"{result} + C"
                elif operation == "Factorizar":
                    result = sp.factor(f)
                elif operation == "Expandir":
                    result = sp.expand(f)
                elif operation == "Resolver Ecuación":
                    result = sp.solve(f, x)
                elif operation == "Límite":
                    target_sym = sp.sympify(lim_target)
                    result = sp.limit(f, x, target_sym)
                else:
                    result = sp.simplify(f)
                
                try:
                    corte_y = f.subs(x, 0)
                    corte_y_str = str(corte_y)
                except Exception:
                    corte_y_str = "No definido"

                st.session_state.historial.append({"op": operation, "ex": expr})
                if len(st.session_state.historial) > 5:
                    st.session_state.historial.pop(0)
                
                with st.spinner("Explicando el ejercicio con la IA..."):
                    client = Groq(api_key=api_key)
                    prompt_extra = f"El límite se evalúa cuando x tiende a {lim_target}." if operation == "Límite" else ""
                    if operation == "Derivada" and orden_derivada > 1:
                        prompt_extra += f" Se solicita calcular la derivada de orden {orden_derivada}."
                    if operation == "Integral" and tipo_integral == "Definida":
                        prompt_extra += f" Es una integral definida desde {lim_a} hasta {lim_b}."

                    prompt_profesor = f"""
                    Actúa como un profesor de matemáticas de primer año de Ingeniería de Sistemas. 
                    Explica de forma didáctica, clara y estrictamente VERTICAL cómo resolver el siguiente ejercicio.
                    Operación: {operation} | Expresión: {expr} | {prompt_extra} | Resultado: {result}
                    """
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": "Eres un tutor universitario ordenado."},
                            {"role": "user", "content": prompt_profesor}
                        ],
                        temperature=0.5
                    )
                    texto_explicacion = response.choices[0].message.content
                
                st.session_state.ultimo_calculo = {
                    "op": operation,
                    "ex": expr,
                    "result_str": sp.latex(result) if not isinstance(result, str) else result,
                    "expr_latex": sp.latex(f),
                    "lim_target": lim_target,
                    "explicacion": texto_explicacion,
                    "f_expr": f,
                    "corte_y": corte_y_str
                }
                    
            except Exception as e:
                st.error(f"Error en el procesamiento: {str(e)}")
                st.session_state.ultimo_calculo = None

    if st.session_state.ultimo_calculo is not None:
        calc = st.session_state.ultimo_calculo
        st.markdown("---")
        col_res1, col_res2, col_res3 = st.columns(3)
        with col_res1:
            if calc["op"] == "Límite":
                st.info(f"**Expresión Original:**\n$\\lim_{{x \\to {calc['lim_target']}}} ({calc['expr_latex']})$")
            else:
                st.info(f"**Expresión Original:**\n$f(x) = {calc['expr_latex']}$")
        with col_res2:
            st.success(f"**Resultado Matemático ({calc['op']}):**\n$ {calc['result_str']} $")
        with col_res3:
            st.metric(label="Corte con Eje Y f(0)", value=calc["corte_y"])
        
        st.subheader("🤖 Explicación Paso a Paso")
        st.markdown(calc["explicacion"])
        
        st.markdown("#### 💾 Gestión de Material de Aprendizaje")
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
                    st.toast("¡Ejercicio añadido a favoritos exitosamente!", icon="⭐")
                    st.rerun()
                else:
                    st.toast("Este ejercicio ya está en tus favoritos.", icon="ℹ️")

        # Gráfica adaptada al slider lateral
        st.subheader("📈 Gráfica de la función original")
        try:
            x = sp.symbols('x')
            f_num = sp.lambdify(x, calc["f_expr"], "numpy")
            x_vals = np.linspace(-rango_x, rango_x, 400)
            y_vals = f_num(x_vals)
            if isinstance(y_vals, (int, float)):
                y_vals = np.full_like(x_vals, y_vals)
                
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(x_vals, y_vals, label=f"f(x) = {calc['ex']}", color="#003366" if st.session_state.theme == "Orgullo UNI 🔵" else "#2ca02c", linewidth=2)
            ax.axhline(0, color='black', linewidth=0.5, ls='--')
            ax.axvline(0, color='black', linewidth=0.5, ls='--')
            ax.grid(True, linestyle=':', alpha=0.6)
            st.pyplot(fig)
        except Exception:
            st.warning("Nota: Gráfica analítica no disponible.")

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
            if st.button("🤖 Generar Ejercicio de Refuerzo con IA"):
                with st.spinner("Generando un ejercicio a tu medida..."):
                    client = Groq(api_key=api_key)
                    prompt_practica = f"Genera un ejercicio de nivel primer año de ingeniería basado estrictamente en el tema: {tema_critico}. Muestra el enunciado y abajo una pestaña oculta o espacio claro que contenga la solución explicada detalladamente para verificar."
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": "Eres un tutor de Inteligencia Artificial que ayuda a estudiantes a reforzar sus puntos bajos en matemática."},
                            {"role": "user", "content": prompt_practica}
                        ],
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
    st.subheader("📋 Formulario Interactivo de Referencia Rápida")
    st.markdown("Copia la sintaxis de la columna derecha directamente en la barra de cálculo superior:")
    
    col_sheet1, col_sheet2 = st.columns(2)
    with col_sheet1:
        st.markdown("#### ⚡ Derivadas Básicas")
        formulas_derivadas = {
            "Función": ["Polinómica: xⁿ", "Exponencial: eˣ", "Seno: sin(x)", "Coseno: cos(x)"],
            "Sintaxis Sympy Estándar": ["x**n", "exp(x)", "sin(x)", "cos(x)"]
        }
        st.table(formulas_derivadas)
        
    with col_sheet2:
        st.markdown("#### 📈 Integrales Comunes")
        formulas_integrales = {
            "Integral": ["Constante: ∫k dx", "Inversa: ∫(1/x) dx", "Logarítmica: ∫ln(x) dx"],
            "Sintaxis Sympy Estándar": ["k", "1/x", "log(x)"]
        }
        st.table(formulas_integrales)
