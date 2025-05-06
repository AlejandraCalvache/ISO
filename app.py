from flask import Flask, render_template, request, make_response, render_template_string
import ollama
from difflib import SequenceMatcher
from io import BytesIO
from xhtml2pdf import pisa

app = Flask(__name__)

# Generar caso de estudio con IA
def generar_caso_estudio():
    prompt = (
        "Genera un caso de estudio realista sobre el incumplimiento de la norma ISO/IEC 27001 por parte de una empresa ficticia. "
        "La historia debe incluir una descripción clara del incidente de seguridad ocurrido (por ejemplo, filtración de datos, accesos no autorizados, ataques por phishing, etc.), "
        "las consecuencias para la organización (como pérdida de clientes, sanciones legales o daño reputacional), y los fallos internos que contribuyeron al incidente "
        "(como mala gestión de accesos, falta de capacitación, ausencia de controles o políticas). "
        "No incluyas definiciones ni explicaciones teóricas de la norma. El tono debe ser objetivo y orientado a hechos."
    )
    respuesta = ollama.chat(model='tinyllama', messages=[{'role': 'user', 'content': prompt}])
    return respuesta['message']['content']

# Obtener solución de IA para el caso
def obtener_solucion_ia(caso):
    prompt = f"Dada esta situación relacionada con la norma ISO 27001, proporciona una solución detallada sobre cómo debería ser la solución a este incumplimiento dado:\n\n{caso}"
    respuesta = ollama.chat(model='tinyllama', messages=[{'role': 'user', 'content': prompt}])
    return respuesta['message']['content']

# Comparar soluciones
def comparar_soluciones(user_text, ia_text):
    ratio = SequenceMatcher(None, user_text.lower(), ia_text.lower()).ratio()
    return round(ratio * 100, 2)

# Generar PDF desde HTML
def generar_pdf(html):
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        return None
    result.seek(0)
    return result

# Almacenar caso generado
caso_actual = generar_caso_estudio()

@app.route("/", methods=["GET", "POST"])
def index():
    global caso_actual
    user_solution = ""
    ia_solution = ""
    resultado = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "nuevo_caso":
            caso_actual = generar_caso_estudio()

        elif action == "comparar":
            user_solution = request.form["user_solution"]
            ia_solution = obtener_solucion_ia(caso_actual)
            resultado = comparar_soluciones(user_solution, ia_solution)

        elif action == "descargar_pdf":
            user_solution = request.form["user_solution"]
            ia_solution = obtener_solucion_ia(caso_actual)
            resultado = comparar_soluciones(user_solution, ia_solution)

            html = render_template_string("""
                <h1>Informe - Caso ISO 27001</h1>
                <p><strong>Caso de estudio:</strong></p>
                <p>{{ caso }}</p>
                <hr>
                <p><strong>Solución del usuario:</strong></p>
                <p>{{ user }}</p>
                <hr>
                <p><strong>Solución IA:</strong></p>
                <p>{{ ia }}</p>
                <hr>
                <p><strong>Similitud:</strong> {{ resultado }}%</p>
            """, caso=caso_actual, user=user_solution, ia=ia_solution, resultado=resultado)

            pdf = generar_pdf(html)
            if pdf:
                response = make_response(pdf.read())
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = 'attachment; filename=caso_iso27001.pdf'
                return response

    return render_template("index.html",
                           caso=caso_actual,
                           user_solution=user_solution,
                           ia_solution=ia_solution,
                           resultado=resultado)

if __name__ == "__main__":
    app.run(debug=True)
