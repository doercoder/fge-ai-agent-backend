Documentación del Backend - Agente AI Multimodal Momostenango

💡 Idea General del Proyecto

El objetivo de este backend es servir como la base funcional para un agente de inteligencia artificial multimodal al servicio de la Municipalidad de Momostenango. Este agente debe ser capaz de interactuar con los ciudadanos mediante texto, imagen o PDF, responder en lenguaje natural y estructurado, acceder a información reglamentaria o contextual almacenada localmente, y mantener persistencia de consultas, sesiones y documentos en una base de datos PostgreSQL.

Se ha utilizado el stack BlackSheep (framework ASGI para Python) como servidor principal, y se deja preparado para integrar Agno o Pydantic AI como orquestador de agentes en etapas posteriores.

El diseño del backend prioriza:

✅ Modularidad clara por funciones: agent, api, services, db

✅ Procesamiento multimodal: texto, imagen (OCR), PDF

✅ Almacenamiento vectorial: PgVector con embeddings

✅ Persistencia estructurada: sesiones, consultas, documentos

✅ Capacidad de respuesta en streaming (token a token)

✅ Medición de latencia P95 por endpoint

✅ Compatibilidad con Structured Output (JSON estructurado + respuesta humana)

Este agente está pensado como un sistema extensible y flexible, listo para futuras integraciones con capacidades más avanzadas como memoria multiturno, function calling con APIs internas, y razonamiento jerárquico.

En las siguientes secciones se detallará cada módulo, sus responsabilidades, funciones clave y ejemplos de uso (request-response), dejando para el final un resumen de las decisiones tecnológicas y arquitectónicas tomadas.

# Documentación del Módulo `agent`

El módulo `agent` representa el **corazón del razonamiento del sistema**, encargado de generar las respuestas del agente a partir de los prompts de los usuarios, integrando contexto, memoria y herramientas según sea necesario. Está compuesto principalmente por dos archivos clave:

---

## `agent_core.py`

Este archivo define la clase principal del agente, `MomostenangoAgent`, que expone los métodos necesarios para interactuar con el LLM.

### Funciones principales:

* **`responder_completo(prompt)`**: genera una respuesta completa para un prompt dado.
* **`responder_en_stream(prompt)`**: genera la respuesta en forma de stream, token a token.
* **`responder_con_json(prompt)`**: devuelve una respuesta natural + un JSON estructurado, ideal para Structured Output.

### Características destacadas:

* Utiliza `OpenRouter` como proveedor de modelo, configurable mediante el archivo `.env`.
* Está preparado para usar un modelo etiquetado como `:free`, cumpliendo el requisito del enunciado.
* Integra control de latencia desde `metrics_service` para auditoría P95.
* Modular y reutilizable: cada método del agente puede ser invocado por distintos endpoints según el flujo deseado.

---

## `tool_engine.py`

Este archivo define herramientas que el agente puede utilizar en su razonamiento, a modo de funciones auxiliares que se podrían activar mediante prompts o comandos.

### Funciones implementadas:

* **`combinar_prompt(prompt: str)`**: permite enriquecer el prompt del usuario con información extra (contexto adicional, instrucciones, estructura), según el tipo de tarea.

> Esta función es el lugar ideal para integrar comportamientos jerárquicos o contextuales en futuras versiones.

---

## Valor estratégico del módulo

El módulo `agent` está pensado para permitir flexibilidad y extensión:

* Puede acoplarse con un MCP, herramientas externas o un orquestador como Agno.
* Permite futuros hooks para aplicar razonamiento simbólico, planificación, o selección de herramientas.
* Abstrae completamente el proveedor de LLM, por lo que podría migrarse a HuggingFace, OpenAI, etc.

Este componente es fundamental para los endpoints `/chat`, `/chat-stream` y `/structured-output`, siendo el "cerebro" del agente y la puerta de entrada para todo el flujo multimodal.

# Documentación del Módulo `api`

El módulo `api` contiene todos los **endpoints HTTP** expuestos por el backend. Está organizado en archivos separados por dominio funcional, facilitando la extensión modular y el mantenimiento del código. Cada archivo se registra en la aplicación principal mediante `setup_routes(app)`.

---

## Endpoints implementados

### `chat_routes.py`

* `POST /chat` → respuesta completa
* `POST /chat-stream` → respuesta token por token (stream)
* `POST /structured-output` → respuesta + JSON estructurado

> Todos estos endpoints invocan directamente al agente `MomostenangoAgent`, y cada uno registra su latencia para análisis P95.

---

### `session_routes.py`

* `GET /sessions/{user_id}` → listar sesiones por usuario
* `GET /sessions/{user_id}/{session_id}` → ver detalle de una sesión específica

> Estos endpoints consultan la base de datos PostgreSQL mediante SQLModel. Son clave para trazabilidad.

---

### `document_routes.py`

* `POST /documents` → guardar documento (texto plano)
* `GET /documents` → listar todos los documentos con embedding

> Permite almacenar contenidos (como reglamentos, FAQs) ya vectorizados con embeddings.

---

### `file_processor_routes.py`

* `POST /process-document` → subir archivo base64 (imagen o PDF) y extraer texto

> Esta ruta aplica OCR o extracción según el tipo de archivo, luego lo guarda con su embedding asociado.

---

### `mcp_routes.py`

* `GET /mcp/list-docs` → listar archivos locales disponibles en el "sistema de archivos contextual"

> Endpoint preparatorio para exploración via MCP. Se usa en prompts que involucran contexto de carpetas.

---

### `metrics_routes.py`

* `GET /metrics/latencia?endpoint=/chat` → devuelve latencia promedio y P95 para un endpoint

> Fundamental para asegurar el cumplimiento del requerimiento de latencia máxima de 800ms.

---

## Valor estratégico del módulo

El módulo `api` representa la interfaz principal entre el frontend y la lógica del agente. Define claramente las capacidades del sistema y permite trazabilidad de consultas, latencia y documentos. Está diseñado de forma RESTful y asíncrona, optimizado para aplicaciones en tiempo real como chats y procesamiento multimodal.


# Documentación del Módulo `services`

El módulo `services` concentra la **lógica de negocio** del backend. Cada archivo encapsula una responsabilidad específica, desde el procesamiento de embeddings y OCR hasta la medición de métricas o la gestión de sesiones. Su separación modular permite mantener el código limpio, testeable y fácilmente escalable.

---

## `embedding_service.py`

Este archivo se encarga de generar embeddings desde texto utilizando OpenAI o proveedor compatible (vía OpenRouter).

### Funciones:

* `generate_embedding(text: str)`: Devuelve un vector de embedding.
* `cosine_similarity(vec1, vec2)`: Calcula la similitud entre dos vectores.

### Valor técnico:

* Se optó por almacenar vectores como listas flotantes normalizadas, optimizando la eficiencia de comparación semántica.
* El uso de PgVector permite indexación por proximidad (ANN), garantizando rendimiento alto en consultas.
* Las llamadas a embedding están desacopladas del ORM, permitiendo migrar fácilmente a otro proveedor (HuggingFace, Cohere, etc.)

> Esto apunta a una arquitectura **desacoplada y extensible**, clave para proyectos que podrían migrar modelos según disponibilidad o costos.

---

## `ocr_service.py`

Este servicio gestiona la extracción de texto desde archivos PDF e imágenes, combinando `PyMuPDF` (fitz) para PDFs y `pytesseract` para OCR.

### Funciones:

* `extract_text_from_pdf(base64_pdf)`
* `extract_text_from_image(base64_image)`
* `process_base64_file(filename, base64_data)`

### Consideraciones:

* Se detecta el tipo de archivo a partir de la extensión y se aplica el procesamiento adecuado.
* El contenido extraído se guarda junto al archivo para trazabilidad.

> Esta estrategia es **multimodal y eficiente**, pero **podría mejorarse en seguridad**: actualmente no se validan cabeceras MIME ni se controlan archivos potencialmente peligrosos. Esta validación sería ideal colocarla a nivel de middleware o capa de API.

---

## `metrics_service.py`

Implementa un sistema simple pero funcional para registrar y consultar latencias por endpoint.

### Funciones:

* `log_latency(endpoint: str, start_time, end_time)`
* `obtener_metricas_latencia(endpoint: str)`

### Valor de diseño:

* Permite cumplir el requisito de latencia P95.
* No requiere herramientas externas como Prometheus: se implementa con SQLModel, ideal para entornos con recursos limitados.

> Esta solución es **ligera, funcional y razonablemente precisa** para un entorno de prototipado, aunque en producción se recomendaría una solución como OpenTelemetry.

---

## `session_service.py`

Permite guardar interacciones en la base de datos, incluyendo `user_id`, `session_id`, `prompt`, `reply`, `timestamp`.

### Funciones:

* `save_session(...)`: Guarda una sesión en la tabla `session`.

> Es clave para trazabilidad y **auditoría**, además de permitir reconstrucción del contexto conversacional.

### Comentario sobre seguridad:

* Se debería sanitizar la entrada para evitar logs maliciosos, aunque el riesgo es bajo dado que no se ejecuta código desde estas entradas. No obstante, es buena práctica aplicar `strip()` y límites de longitud.

---

## Valor estratégico general

Este módulo centraliza la lógica compleja, permitiendo que los endpoints del `módulo api` sean delgados y expresivos. Esto **mejora la mantenibilidad, permite tests unitarios y facilita escalado horizontal**.

* Seguridad: algunos puntos pueden reforzarse (validación de archivos, sanitización de input), pero la base es segura y clara.
* Rendimiento: uso eficiente de PgVector, OCR por tipo de archivo, y latencia auditada.
* Creatividad: uso de base64 + OCR + embedding en cadena permite flujos multimodales sin depender de herramientas externas pesadas.

Este diseño es propicio para evolucionar hacia flujos más avanzados sin incurrir en deuda técnica innecesaria.


# Documentación del Módulo `db`

El módulo `db` contiene la definición del modelo de datos y la configuración de acceso a la base de datos PostgreSQL mediante **SQLModel**, una biblioteca ORM asincrónica compatible con FastAPI y BlackSheep.

Está compuesto por dos archivos clave:

---

## `database.py`

Define la sesión asincrónica de conexión a la base de datos.

### Contenido:

* `async_engine`: motor de conexión SQLModel con soporte async.
* `async_session`: función `async_session()` que genera una sesión de base de datos.
* `create_db_and_tables()`: función utilitaria para crear tablas si no existen.

> Este diseño permite integrar fácilmente migraciones automatizadas y pruebas de integración sin dependencia de entornos externos.

---

## `models.py`

Define las tablas principales del sistema como clases SQLModel. Incluye:

### Modelos definidos:

* `Session`: representa una interacción del usuario con el agente.

  * Campos: `user_id`, `session_id`, `prompt`, `reply`, `created_at`

* `McpDocument`: representa un archivo procesado (imagen o PDF).

  * Campos: `filename`, `base64_data`, `content`, `file_type`, `created_at`

* `Document`: texto indexado con embeddings.

  * Campos: `title`, `content`, `embedding`, `created_at`

### Consideraciones de diseño:

* Todos los modelos tienen campo `created_at` para trazabilidad temporal.
* Se almacena `embedding` como lista flotante (PgVector), compatible con búsquedas semánticas.
* `base64_data` está presente para permitir persistencia sin almacenamiento externo.

> Esta estructura favorece un diseño **self-contained y portable**, útil para entornos sin S3 o file servers.

---

## Seguridad y rendimiento

* **Rendimiento**: se ha habilitado `pgvector` y creado el índice necesario para operaciones ANN, garantizando eficiencia en búsquedas.
* **Seguridad**: si bien el backend no ejecuta código sobre los campos, sería recomendable limitar la longitud de `base64_data` o mover a almacenamiento de archivos en disco/objeto para evitar saturar la base de datos.
* **Escalabilidad**: esta estructura es funcional para prototipos y pilotos. En producción, se sugiere separar embeddings en tabla independiente y utilizar almacenamiento de archivos fuera de base de datos.

---

## Valor estratégico del módulo

Este módulo proporciona la base para la trazabilidad, análisis de uso, reconstrucción de sesiones, almacenamiento de información indexada y métricas. Su diseño orientado a SQLModel + PgVector permite aprovechar lo mejor de la integración con LLMs sin comprometer el control sobre la estructura y queries.

> Su simplicidad y adaptabilidad hacen de este módulo una base sólida para evolución futura, integraciones con otras fuentes, o migración hacia arquitecturas más complejas como event sourcing o almacenamiento híbrido.


# Resumen de Decisiones Tecnológicas y Arquitectónicas

Este documento resume las decisiones clave tomadas en el desarrollo del backend del agente AI multimodal para la Municipalidad de Momostenango. Estas elecciones reflejan un balance entre creatividad, rendimiento y seguridad, considerando además las limitaciones de tiempo y recursos de la etapa de prototipado.

---

## 🧠 Stack Tecnológico

* **BlackSheep (ASGI)**: elegido por su rendimiento, compatibilidad con ASGI, y sintaxis clara. Permite streaming, uso de middlewares y tareas asincrónicas.
* **SQLModel + PostgreSQL**: proporciona ORM moderno y flexible con acceso directo a SQL. Se eligió PostgreSQL por su soporte a `pgvector`.
* **PgVector**: habilita búsquedas semánticas eficientes usando vectores, ideal para RAG y consultas a embeddings.
* **OpenRouter (LLM provider)**: se configuró para usar modelos gratuitos con la etiqueta `:free`, cumpliendo la consigna de minimizar costos.
* **OCR: PyMuPDF + Tesseract**: permite extracción multimodal de texto desde PDFs o imágenes, cubriendo el requisito de entradas complejas.

---

## 🧩 Arquitectura Modular

* Cada componente está claramente separado en módulos:

  * `agent`: razonamiento central
  * `api`: rutas REST
  * `services`: lógica de negocio
  * `db`: conexión y modelos de datos
* Esto favorece el testeo, la evolución por partes y una curva de aprendizaje rápida para nuevos desarrolladores.

---

## ⚙️ Decisiones de Rendimiento

* **Latencia auditada**: se implementó un sistema propio de logging de latencias para cada endpoint. Esto permite verificar el cumplimiento del P95 < 800ms.
* **Uso de stream en `/chat-stream`**: mejora la experiencia del usuario final y reduce la percepción de espera.
* **Embeddings preprocesados**: documentos son vectorizados al almacenarse, lo que evita reprocesamiento innecesario.

---

## 🔐 Decisiones de Seguridad

* Inputs validados manualmente en puntos clave (OCR, almacenamiento, sesiones).
* Se priorizó un diseño simple que evita ejecuciones dinámicas o llamadas arbitrarias.
* Aún así, se reconocen posibles mejoras:

  * Validación de tipo MIME más estricta al subir archivos
  * Límite de tamaño para campos como `base64_data`
  * Sanitización sistemática de inputs (aunque no se ejecuta código desde ellos)

> Se priorizó claridad y estabilidad antes que seguridad avanzada, dada la naturaleza de prototipo.

---

## 🧠 Escalabilidad y Futuro

El diseño del sistema facilita:

* Integración futura con orquestadores como **Agno** o sistemas como **Zep Memory**
* Almacenamiento de archivos externo si se desea aligerar la base de datos
* Incorporación de herramientas externas o APIs mediante MCP o function calling
* Soporte para modos multi-agente, razonamiento jerárquico o chain-of-thought

---

## 💡 Conclusión

El backend desarrollado equilibra simplicidad, potencia y claridad, siendo adecuado para un prototipo funcional con visión a largo plazo. Las decisiones tomadas aseguran compatibilidad con requisitos clave del enunciado sin comprometer mantenibilidad ni rendimiento.
