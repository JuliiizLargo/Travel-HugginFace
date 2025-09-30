🧳 Travel-HugginFace
Agente turístico conversacional (Flask + Groq + Hugging Face)

📖 Descripción
Travel-HugginFace es un asistente turístico educativo en español.

Responde preguntas sobre:
- 🌤 Clima de un destino.
- 💸 Costos estimados (alojamiento, comida, transporte, actividades).
- 🏝 Recomendación de lugares por temática: familiar, cultural, foodie, naturaleza, low-cost, etc.
- 🗓 Generación de itinerarios diarios con formatos claros (mañana / tarde / noche / tip).

⚠️ Aviso: la información generada es ficticia y con fines académicos (incluye un “ℹ Nota” en las respuestas).

📂 Arquitectura y archivos
Raíz del proyecto:
- static/ → Frontend (index.html servido por Flask), estilos y assets.
- app.py → Backend Flask (async), router /api/ask, orquestación y guardrails.
- requirements.txt → Dependencias de Python.
- runtime.txt → Versión de Python para despliegue.
- vercel.json → Configuración de build y rutas para Vercel.
- POLITICAS.md → Políticas de uso y disclaimer.
- README.md → Documentación.

Estructura esperada:
- static/
   └─ styles.css
- app.py
- requirements.txt
- runtime.txt
- vercel.json
- POLITICAS.md
- README.md

✅ Requisitos
- Python 3.11 (runtime.txt indica 3.11.9).
- Cuenta y API Key de Groq.
- Cuenta y Token de Hugging Face (opcional si no usarás la función de “búsqueda”).
- ⚠️**Nota importante:** si se acaban los créditos del token en Hugging Face o alguna de las APIs, el sistema puede devolver respuestas incorrectas o indicar que no puede responder a la consulta.
- Git (para clonar) y, si despliegas, una cuenta en Vercel.

⚙️ Instalación local (paso a paso)
1. Clonar el repositorio:
   git clone https://github.com/USUARIO/Travel-HugginFace.git
   cd Travel-HugginFace

2. Crear y activar entorno virtual:
   Linux / Mac:
   python -m venv venv
   source venv/bin/activate

   Windows:
   Python -m venv venv
   venv\Scripts\activate

3. Instalar dependencias:
   pip install -r requirements.txt

4. Crear archivo .env en la raíz con las variables:
   GROQ_API_KEY=tu_api_key_de_groq
   GROQ_MODEL=llama-3.3-70b-versatile
   HUGGINGFACE_TOKEN=tu_token_hf
   HUGGINGFACE_MODEL=meta-llama/Llama-2-7b-chat-hf
   PORT=5000

   Notas:
   - GROQ_API_KEY es obligatoria para generar respuestas.
   - HUGGINGFACE_TOKEN es opcional si no usarás la función de “search_with_hf”.

5. Ejecutar la app en local:
   python app.py

6. Abrir en el navegador:
   http://localhost:5000

🖥 Uso en la interfaz
1. Escribe tu consulta en la caja de texto, por ejemplo:
   - “¿Cómo es el clima en Madrid?”
   - “Hazme un itinerario de 3 días en París, familiar y low-cost y con presupuesto de 300 USD.”
   - “Dame costos aproximados para viajar a Cancún.”

2. El backend clasifica la intención (clima, costos, lugares, itinerario) y responde.
3. Las respuestas con formato de Itinerario de X días … - Día 1 / Mañana/Tarde/Noche/Tip se convierten en tarjetas visuales.

🔗 Endpoints Backend
POST /api/ask

Body JSON:
{ "question": "tu pregunta en texto" }

Respuesta JSON:
{ "answer": "texto de la respuesta" }

👉 El frontend ya usa este endpoint mediante fetch().

🛡 Guardrails (filtros de seguridad)
El sistema bloquea:
- Lenguaje violento/dañino/discriminatorio.
- Datos personales (emails, teléfonos).
- Peticiones ilegales (plagio, bypass de paywalls).
- Consultas de salud o legales.
- Preguntas demasiado cortas.

📌 Si algo se bloquea, responde con mensajes de advertencia adecuados.

🤖 Modelos y servicios
- Groq (obligatorio): generación de texto (chat completions).
   Variables: GROQ_API_KEY, GROQ_MODEL (por defecto: llama-3.3-70b-versatile).
- Hugging Face (opcional): “búsqueda” / resumen rápido.
   Variables: HUGGINGFACE_TOKEN, HUGGINGFACE_MODEL (por defecto: meta-llama/Llama-2-7b-chat-hf).

🚀 Despliegue en Vercel
1. Subir el repo a GitHub.
2. En Vercel → “New Project” → Importar desde GitHub.
3. Añadir variables de entorno en Project Settings → Environment Variables:
   - GROQ_API_KEY
   - GROQ_MODEL
   - HUGGINGFACE_TOKEN (opcional)
   - HUGGINGFACE_MODEL (opcional)
4. Deploy.

Ejemplo de vercel.json:
{
  "builds": [
    { "src": "app.py", "use": "@vercel/python" },
    { "src": "static/**", "use": "@vercel/static" }
  ],
  "routes": [
    { "src": "/api", "dest": "/app.py" },
    { "src": "/api/ask", "dest": "/app.py" },
    { "src": "/", "dest": "/static/index.html" }
  ]
}

🐞 Solución de problemas comunes
- Error: “Lo siento, no estoy configurado correctamente. Falta la clave de API de Groq.”
   → No configuraste GROQ_API_KEY en .env o en Vercel.

- /api/ask devuelve 500 en Vercel.
   → Revisa que las variables estén en “Production” y que el deploy las tomó.
   → Verifica que app.py esté en la raíz.

- La interfaz no carga.
   → Asegúrate de que static/index.html exista y que static/styles.css sea accesible.
   → Comprueba la ruta / en vercel.json.

- Respuestas vacías o muy cortas.
   → Puede ser rate limit o error transitorio → Reintentar.
   → Revisar logs en Vercel y disponibilidad de GROQ_MODEL.

🧩 Cómo extender el proyecto
- Añadir una nueva intención (ej. transporte):
   - Agregar la etiqueta al clasificador.
   - Crear un nuevo agente async y mapearlo en agentes.

- Cambiar estilos:
   - Editar static/styles.css y/o static/index.html.

- Ajustar guardrails:
   - Modificar listas/patrones en guardrails() y guardrails_respuesta().

🛠 Tecnologías
- Frontend: HTML5, CSS3, JavaScript (vanilla).
- Backend: Flask 3 (async), Python 3.11.
- IA: Groq API (chat completions), Hugging Face Inference (opcional).
- Despliegue: Vercel (serverless Python + estáticos).

📜 Licencia y uso
Proyecto educativo.
Sugerencia: licencia MIT.
Revisa/ajusta POLITICAS.md para tu caso.

👨‍💻 Créditos / Autoría
- Autoría del repositorio y personalización de frontend/backends: (agrega tu nombre/usuario).
- Agradecimientos a Groq y Hugging Face por sus APIs.

💬 Ejemplos de preguntas
- “¿Cómo es el clima en Medellín a lo largo del año?”
- “Quiero un itinerario de 3 días en Cusco con temática cultural.”
- “Presupuesto aproximado para 5 días en Buenos Aires.”
- “Itinerario de 3 días en Cartagena, familiar, con 250 USD de presupuesto.”

