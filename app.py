from flask import Flask, request, jsonify, send_from_directory
import re, os, json, asyncio
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Mantiene el frontend en la raíz
app = Flask(__name__, static_folder="static", static_url_path="")

# -----------------------------
# Configuración por variables de entorno (Vercel)
# -----------------------------
# Para búsquedas con Hugging Face
HUGGINGFACE_TOKEN = os.environ.get("HUGGINGFACE_TOKEN", "")
HUGGINGFACE_MODEL = "meta-llama/Llama-2-7b-chat-hf"

# Para generación de texto con Groq
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")  # Modelo de producción actual

DISCLAIMER = "ℹ Nota: Esta información es ficticia y solo con fines académicos."

# -----------------------------
# Guardrails (filtros de seguridad)
# -----------------------------
def guardrails(state):
    question = state["question"].lower().strip()

    # Verificar que haya texto
    if not question:
        return {**state, "blocked": True, "answer": "No hay ninguna pregunta de entrada."}

    # Filtro de contenido dañino
    palabras_prohibidas = [
        "odio","odiar","violencia","insulto","insultar","matar","robar","pegar","agredir","golpear",
        "lastimar","amenazar","dañar","abusar","secuestrar","secuestro","torturar","herir","discriminar",
        "humillar","intimidar","vengar","sabotear","maltratar","violar","corromper","estafar","traicionar",
        "despreciar","destruir","oprimir","castigar","maldecir","provocar","burlar","manipular","saquear",
        "extorsionar","asesinar"
    ]
    if any(p in question for p in palabras_prohibidas):
        return {**state, "blocked": True, "answer": "Contenido inapropiado detectado."}

    # Datos personales
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", question):
        return {**state, "blocked": True, "answer": "No puedo procesar correos electrónicos."}
    if re.search(r"\+?\d{8,}", question):
        return {**state, "blocked": True, "answer": "No puedo mostrar datos de contacto."}

    # Preguntas muy cortas
    if len(question.split()) < 2:
        return {**state, "blocked": True, "answer": "Pregunta demasiado corta para recomendar algo."}

    # Plagio / acceso no autorizado
    if any(p in question for p in ["plagio","descargar libro gratis","bypass","paywall"]):
        return {**state, "blocked": True, "answer": "No puedo ayudar con tareas de plagio o acceso no autorizado."}

    # Salud / legal
    if any(p in question for p in ["medicina","tratamiento","receta","abogado","demanda"]):
        return {**state, "blocked": True, "answer": "Este sistema no está diseñado para dar consejos médicos o legales."}

    return {**state, "blocked": False}

# Post-procesamiento: verificar que la respuesta no viole filtros
def guardrails_respuesta(answer: str):
    txt = (answer or "").lower()
    palabras_prohibidas = [
        "odio","odiar","violencia","insulto","insultar","matar","robar","pegar","agredir","golpear",
        "lastimar","amenazar","dañar","abusar","secuestrar","secuestro","torturar","herir","discriminar",
        "humillar","intimidar","vengar","sabotear","maltratar","violar","corromper","estafar","traicionar",
        "despreciar","destruir","oprimir","castigar","maldecir","provocar","burlar","manipular","saquear",
        "extorsionar","asesinar"
    ]
    if any(p in txt for p in palabras_prohibidas):
        return False
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", txt):
        return False
    if re.search(r"\+?\d{8,}", txt):
        return False
    return True

# -----------------------------
# Integración con Hugging Face
# -----------------------------
async def generate_with_groq(system_prompt: str, user_prompt: str) -> str:
    """Genera texto usando la API de Groq"""
    if not GROQ_API_KEY:
        print("[AI] Error: No GROQ_API_KEY provided")
        return "Lo siento, no estoy configurado correctamente. Falta la clave de API de Groq."
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1024
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[AI Groq] Error: {str(e)}")
        if hasattr(response, 'json') and 'error' in response.json():
            print(f"[AI Groq] API Error: {response.json()['error']}")
        return "Lo siento, no pude generar una respuesta en este momento."

async def search_with_hf(query: str) -> list:
    """Realiza búsquedas usando la API de Hugging Face"""
    if not HUGGINGFACE_TOKEN:
        print("[Search] Error: No HUGGINGFACE_TOKEN provided")
        return []
    
    API_URL = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_TOKEN}"}
    
    system_prompt = "Eres un asistente que resume información de búsquedas. Proporciona información concisa y útil."
    prompt = f"Busca información sobre: {query}"
    
    payload = {
        "inputs": f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{prompt} [/INST]",
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.3,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return [{"content": result[0]['generated_text'].strip()}]
    except Exception as e:
        print(f"[Search] Error: {str(e)}")
        return []

# -----------------------------
# Funciones auxiliares
# -----------------------------
def extraer_destino(question: str) -> str:
    """Extrae el destino de la pregunta del usuario"""
    # Patrones comunes para extraer el destino
    patrones = [
        r"(?:en|a|para|hacia|de)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:viajar|visitar|conocer|ir|ver)\s+(?:a|en)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"(?:qué\s+hay\s+en|qué\s+hacer\s+en|qué\s+ver\s+en)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
    ]
    
    for patron in patrones:
        match = re.search(patron, question, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    # Si no se encuentra con patrones, buscar palabras con mayúscula
    palabras = re.findall(r'\b[A-Z][a-z]+\b', question)
    if palabras:
        return ' '.join(palabras)
    
    return ""

def extraer_dias(question: str) -> int:
    """Extrae el número de días de la pregunta"""
    match = re.search(r'(\d+)\s+d[ií]as?', question, re.IGNORECASE)
    if match:
        return min(int(match.group(1)), 14)  # Máximo 14 días
    return 3  # Valor por defecto

def extraer_tema(question: str) -> str:
    """Extrae el tema de la pregunta (ej: familiar, aventura, etc.)"""
    temas = {
        'familiar': ['familiar', 'niños', 'niñas', 'niño', 'niña', 'hijos', 'hijas', 'pequeños'],
        'aventura': ['aventura', 'aventurero', 'extremo', 'deportes extremos'],
        'romántico': ['romántico', 'romantico', 'pareja', 'luna de miel', 'aniversario'],
        'cultural': ['cultural', 'cultura', 'museos', 'historia', 'histórico', 'tradiciones'],
        'gastronómico': ['gastronomía', 'gastronomia', 'comida', 'restaurantes', 'platos típicos'],
        'naturaleza': ['naturaleza', 'parques', 'montaña', 'playa', 'selva', 'bosque', 'cataratas'],
        'low-cost': ['económico', 'económica', 'barato', 'barata', 'low cost', 'bajo presupuesto']
    }
    
    question_lower = question.lower()
    for tema, palabras in temas.items():
        if any(palabra in question_lower for palabra in palabras):
            return tema
    
    return "general"

# -----------------------------
# Agentes de respuesta
# -----------------------------
async def agente_clima(state):
    """Agente para consultas sobre el clima"""
    destino = extraer_destino(state["question"])
    if not destino:
        return {**state, "answer": "¿Podrías decirme de qué lugar te gustaría saber el clima?"}
    
    system_prompt = """Eres un asistente turístico especializado en información climática. 
    Proporciona información útil sobre el clima del destino, incluyendo temporadas, 
    temperaturas promedio, y recomendaciones de ropa."""
    
    user_prompt = f"Proporciona información sobre el clima en {destino}. {DISCLAIMER}"
    
    respuesta = await generate_with_hf(system_prompt, user_prompt)
    return {**state, "answer": respuesta}

async def agente_costos(state):
    """Agente para consultas sobre costos"""
    destino = extraer_destino(state["question"])
    if not destino:
        return {**state, "answer": "¿Podrías decirme de qué lugar te gustaría saber los costos?"}
    
    system_prompt = """Eres un experto en viajes que proporciona estimaciones de costos. 
    Incluye rangos de precios para alojamiento, comida, transporte y actividades. 
    Sé claro que son estimaciones aproximadas."""
    
    user_prompt = f"Proporciona estimaciones de costos para viajar a {destino}. {DISCLAIMER}"
    
    respuesta = await generate_with_hf(system_prompt, user_prompt)
    return {**state, "answer": respuesta}

async def agente_lugares(state):
    """Agente para recomendaciones de lugares"""
    destino = extraer_destino(state["question"])
    if not destino:
        return {**state, "answer": "¿Podrías decirme de qué lugar te gustaría recomendaciones?"}
    
    tema = extraer_tema(state["question"])
    
    system_prompt = """Eres un guía turístico experto. Recomienda lugares interesantes para visitar, 
    incluyendo atracciones principales, lugares menos conocidos y consejos útiles. 
    Organiza la información de manera clara y atractiva."""
    
    user_prompt = f"Recomienda lugares para visitar en {destino} con temática {tema}. {DISCLAIMER}"
    
    respuesta = await generate_with_hf(system_prompt, user_prompt)
    return {**state, "answer": respuesta}

async def agente_itinerario(state):
    """Agente para generar itinerarios"""
    destino = extraer_destino(state["question"])
    if not destino:
        return {**state, "answer": "¿Podrías decirme para qué destino te gustaría un itinerario?"}
    
    dias = extraer_dias(state["question"])
    tema = extraer_tema(state["question"])
    
    system_prompt = """Eres un experto en planificación de viajes. Crea un itinerario detallado 
    que incluya actividades para cada día, recomendaciones de lugares para comer, 
    y consejos de transporte. Sé específico y realista con los tiempos."""
    
    user_prompt = f"Crea un itinerario de {dias} días en {destino} con temática {tema}. {DISCLAIMER}"
    
    respuesta = await generate_with_hf(system_prompt, user_prompt)
    return {**state, "answer": respuesta}

# -----------------------------
# Clasificador de intenciones
# -----------------------------
async def clasificador(state):
    """Clasifica la intención de la pregunta"""
    system_prompt = """Clasifica la intención de la pregunta del usuario en una de estas categorías:
    - "clima": Preguntas sobre el clima o condiciones meteorológicas
    - "costos": Consultas sobre precios, presupuestos o gastos
    - "lugares": Búsqueda de puntos de interés o recomendaciones
    - "itinerario": Solicitudes para crear planes de viaje o rutas
    - "otro": Cualquier otra consulta que no entre en las categorías anteriores

    Responde SOLO con la palabra clave de la categoría, sin comillas ni puntos.
    """
    respuesta = await generate_with_groq(system_prompt, state["question"])
    state["intencion"] = respuesta.lower().strip()
    return state
# -----------------------------
async def run_graph(question: str):
    """Ejecuta el flujo de procesamiento de la pregunta"""
    # Inicializar estado
    state = {
        "question": question,
        "answer": "",
        "blocked": False,
        "intencion": ""
    }
    
    # Aplicar guardrails
    state = guardrails(state)
    if state["blocked"]:
        return state["answer"]
    
    # Clasificar intención
    state = await clasificador(state)
    
    # Enrutar al agente correspondiente
    agentes = {
        "clima": agente_clima,
        "costos": agente_costos,
        "lugares": agente_lugares,
        "itinerario": agente_itinerario
    }
    
    if state["intencion"] in agentes:
        state = await agentes[state["intencion"]](state)
    else:
        # Respuesta genérica para intenciones no reconocidas
        system_prompt = """Eres un asistente turístico amable y servicial. Responde a la pregunta 
        del usuario de manera clara y concisa. Si no tienes suficiente información, 
        sé honesto y ofrece ayuda con lo que puedas."""
        state["answer"] = await generate_with_groq(system_prompt, question)
    
    # Verificar que la respuesta sea segura
    if not guardrails_respuesta(state["answer"]):
        state["answer"] = "Lo siento, no puedo proporcionar esa información."
    
    return state["answer"]

# -----------------------------
# Endpoints de la API
# -----------------------------
@app.route("/api/ask", methods=["POST"])
async def ask():
    """Endpoint para hacer preguntas al asistente"""
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Se requiere una pregunta"}), 400
    
    respuesta = await run_graph(data["question"])
    return jsonify({"answer": respuesta})

@app.route("/")
def serve_index():
    """Sirve el frontend"""
    return send_from_directory("static", "index.html")

# -----------------------------
# Punto de entrada
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
