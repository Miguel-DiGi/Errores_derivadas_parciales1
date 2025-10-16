import streamlit as st
from sympy import symbols, sympify, sqrt, diff, re, im

# --- Título y Descripción de la App ---
st.title("Calculadora de Error Propagado (Derivadas Parciales)")
st.markdown("""
Esta app calcula el error propagado de una función de varias variables usando la fórmula de la suma en cuadratura de las derivadas parciales.
Puedes usar notación científica como `3.14e-15` o `6.022*10**23`.
""")

# --- Entradas del Usuario ---
st.markdown("---")
st.subheader("1. Función y Variables")

# Entrada para la expresión de la función
str_funcion = st.text_input("Introduce la función (ej. `G*m1*m2/r**2` o `V/I`):", value="I*R")

# Entrada para las variables en la función
str_variables = st.text_input("Introduce las variables separadas por comas (ej. `I, R`):", value="I, R")

# --- Sección de Constantes ---
st.markdown("---")
st.subheader("2. Constantes (opcional)")
st.markdown("Define aquí las constantes que aparecen en tu función, separadas por comas (ej. `c = 3e8, G = 6.67e-11`).")
str_constantes = st.text_input("Constantes y sus valores:", value="")

# --- Entradas de Valores Medidos e Incertidumbres ---
st.markdown("---")
st.subheader("3. Valores Medidos e Incertidumbres")

# Validar y crear símbolos para las variables
try:
    # symbols() crea variables simbólicas a partir de un string
    variables_list = [s.strip() for s in str_variables.split(',') if s.strip()]
    if not variables_list:
        st.warning("Por favor, introduce al menos una variable.")
        st.stop()
    variables = symbols(str_variables)
    # Asegurar que 'variables' sea siempre una tupla/lista para poder iterar
    if not isinstance(variables, (list, tuple)):
        variables = [variables]
except Exception as e:
    st.error(f"Error al interpretar las variables: {e}")
    st.stop()

# Diccionarios para guardar los valores y errores introducidos como texto
valores_medidos_str = {}
incertidumbres_str = {}

# Crear campos de entrada para el valor medido y la incertidumbre de cada variable
for var in variables:
    col1, col2 = st.columns(2)
    with col1:
        # Usamos st.text_input para permitir notación científica
        valor_str = st.text_input(f"Valor medido de `{var}`", "0", key=f"valor_{var}")
    with col2:
        error_str = st.text_input(f"Error (incertidumbre) de `{var}`", "0", key=f"error_{var}")
    
    valores_medidos_str[var] = valor_str
    incertidumbres_str[var] = error_str

# --- Botón de Cálculo y Lógica Principal ---
if st.button("Calcular Error Propagado"):

    # 1. Parsear (interpretar) las constantes
    constantes_dict = {}
    if str_constantes:
        try:
            constantes_list = [c.strip() for c in str_constantes.split(',')]
            for const_assignment in constantes_list:
                nombre, valor = const_assignment.split('=')
                # sympify convierte el string del valor en un objeto numérico de SymPy
                constantes_dict[symbols(nombre.strip())] = sympify(valor.strip())
        except Exception as e:
            st.error(f"Error al interpretar las constantes. Asegúrate de que el formato es correcto (ej. c = 3e8, g = 9.8). Detalle: {e}")
            st.stop()

    # 2. Parsear los valores y errores introducidos
    valores_medidos_num = {}
    incertidumbres_num = {}
    try:
        for var in variables:
            # sympify convierte strings como "1.23e-5" en números
            valores_medidos_num[var] = sympify(valores_medidos_str[var])
            incertidumbres_num[var] = sympify(incertidumbres_str[var])
    except Exception as e:
        st.error(f"Error al interpretar los valores o incertidumbres. Revisa las entradas. Detalle: {e}")
        st.stop()
        
    # 3. Crear la función simbólica
    try:
        # El diccionario 'locals' permite a sympify reconocer tanto las variables como las constantes
        all_symbols = {str(v): v for v in variables}
        all_symbols.update({str(k): k for k in constantes_dict.keys()})
        funcion = sympify(str_funcion, locals=all_symbols)
    except Exception as e:
        st.error(f"Error: La función introducida no es válida. Detalle: {e}")
        st.stop()

    # 4. Calcular la suma en cuadratura de los errores
    suma_errores_cuadrado_expr = 0
    for var in variables:
        try:
            # diff() calcula la derivada parcial
            derivada_parcial = diff(funcion, var)
            error_termino = (derivada_parcial * incertidumbres_num[var])**2
            suma_errores_cuadrado_expr += error_termino
        except Exception as e:
            st.error(f"Error al calcular la derivada parcial respecto a {var}: {e}")
            st.stop()
            
    # 5. Sustituir los valores numéricos en la expresión del error
    try:
        # Creamos un diccionario único con constantes y valores medidos para la sustitución
        subs_dict = {**constantes_dict, **valores_medidos_num}
        suma_errores_cuadrado_val = suma_errores_cuadrado_expr.subs(subs_dict)
    except Exception as e:
        st.error(f"Error al evaluar la suma de errores al sustituir valores: {e}")
        st.stop()

    # 6. Comprobar si el resultado es válido (no complejo o negativo)
    try:
        # im() y re() extraen las partes imaginaria y real de un número
        if im(suma_errores_cuadrado_val) != 0 or re(suma_errores_cuadrado_val) < 0:
            st.error("El cálculo del error ha producido un número complejo o negativo.\n"
                     "Causa probable: Uno de los valores medidos está fuera del dominio de la función.\n"
                     f"Valor dentro de la raíz cuadrada: {suma_errores_cuadrado_val}")
            st.stop()
    except Exception as e:
        st.error(f"Error al comprobar la validez del resultado: {e}")
        st.stop()

    # --- Mostrar Resultados ---
    st.markdown("---")
    st.header("Resultados")

    try:
        # La expresión final del error es la raíz cuadrada de la suma
        error_final_expr = sqrt(suma_errores_cuadrado_expr)
        # Sustituimos los valores para obtener el resultado numérico
        error_numerico = error_final_expr.subs(subs_dict)
        valor_funcion = funcion.subs(subs_dict)

        st.success("Cálculo realizado correctamente.")
        
        # Mostrar la fórmula simbólica del error
        st.subheader("Fórmulas Simbólicas")
        st.latex(f"f({', '.join(map(str, variables_list))}) = {funcion}")
        st.latex(f"\\Delta f = {error_final_expr}")
        
        # Mostrar los resultados numéricos
        st.subheader("Resultados Numéricos")
        # .evalf() convierte el objeto de SymPy a un número de punto flotante
        st.write(f"**Valor de la función:** `{valor_funcion.evalf():.6g}`")
        st.write(f"**Error propagado (incertidumbre):** `±{error_numerico.evalf():.6g}`")

    except Exception as e:
        st.error(f"Error al calcular el resultado final: {e}")
        st.stop()



