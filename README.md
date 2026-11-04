# Agente clasificador con LangGraph y MCP

Proyecto académico. **Estado: fase 1**, selección del modelo y conversación básica por terminal; todavía **no** hay grafo, conexión MCP ni memoria persistente. Se añaden en las siguientes fases.

## Arquitectura prevista

- `src/config/`: fábrica de LLMs y categorías permitidas.
- `src/agentes/`: nodos/agentes para gestionar peticiones y clasificar textos.
- `src/grafo/`: grafo explícito con LangGraph y memoria persistente.
- `src/mcp/`: servidor MCP independiente; será el único que manipule archivos.
- `data/origen/`: archivos disponibles para importar.
- `data/recepcion/`: cola de archivos pendientes de clasificar.
- `data/clasificados/<tema>/`: destino según categorías predefinidas.
- `docs/capturas/`: imágenes para el PDF de entrega.

## Preparación (Linux / WSL, desde la raíz del proyecto)

1. Usa preferentemente Python 3.12: `python3.12 -m venv .venv` (si no está instalado, revisa la versión disponible antes de continuar).
2. `source .venv/bin/activate`
3. `python -m pip install -r requirements.txt`
4. `cp .env.example .env` y añade tu clave en `.env` solo si usarás Gemini.
5. Para Ollama, instala e inicia Ollama, y descarga el modelo: `ollama pull qwen3:4b-instruct`.
6. `python -m src.main`

## Importante

- La fase 1 solo mantiene historial mientras el proceso sigue abierto. La memoria real se implementará con un checkpointer SQLite de LangGraph.
- Nunca versionar `.env` ni claves de API.
- Las tools de MCP tendrán docstrings propios, separados del prompt del sistema.
- No se procesarán rutas arbitrarias facilitadas por el LLM: las tools trabajarán en directorios limitados.
