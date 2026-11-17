
# Agente clasificador con LangGraph y MCP

Proyecto académico desarrollado en Python que permite gestionar y clasificar archivos de texto mediante un agente de IA conectado a un servidor MCP.

El usuario interactúa con el agente desde la terminal, utilizando modelos de Ollama o Gemini.

## Funcionalidades

- Importar archivos `.txt` desde la carpeta `origen`.
- Crear documentos nuevos a partir de texto.
- Clasificar archivos por su contenido en cinco categorías: tecnología, salud, economía, educación y otros.
- Buscar, leer y listar documentos sin necesidad de conocer su ubicación.
- Editar documentos y devolverlos a recepción para clasificarlos de nuevo.
- Enviar archivos a la papelera y restaurarlos.
- Mantener el historial de conversación entre ejecuciones mediante SQLite.
- Solicitar confirmación antes de eliminar documentos.

## Arquitectura

- **LangGraph:** gestiona el flujo del agente, las llamadas a herramientas y la memoria.
- **MCP (Model Context Protocol):** proporciona las herramientas que permiten manipular los archivos.
- **Ollama / Gemini:** modelos de lenguaje que interpretan las peticiones y seleccionan las herramientas necesarias.
- **SQLite:** almacena el historial de conversación de forma persistente.

Las carpetas principales son:

- `src/config/`: configuración y selección de modelos.
- `src/grafo/`: grafo del agente con LangGraph.
- `src/mcp/`: servidor y herramientas MCP.
- `data/origen/`: documentos disponibles para importar.
- `data/recepcion/`: archivos pendientes de clasificación.
- `data/clasificados/`: documentos organizados por categorías.
- `data/papelera/`: archivos eliminados que pueden recuperarse.
- `pruebas/`: scripts para comprobar el funcionamiento.
- `docs/capturas/`: evidencias para la entrega.

## Instalación y ejecución

Desde Linux o WSL, con Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Para utilizar **Ollama**, instalarlo y descargar el modelo:

```bash
ollama pull qwen3:4b-instruct
```

Para utilizar **Gemini**, copiar `.env.example` a `.env` y configurar la clave de Google AI Studio.

Iniciar el agente:

```bash
python -m src.main
```

Al comenzar, se selecciona el modelo y se puede interactuar con el agente mediante lenguaje natural.

## Funcionamiento

El agente recibe la petición del usuario y utiliza LangGraph para decidir qué herramientas MCP necesita ejecutar.

Por ejemplo, al pedir que clasifique un documento, primero consulta su contenido y después lo mueve a la categoría correspondiente.

Los archivos modificados o restaurados vuelven a `recepcion/` para poder clasificarlos nuevamente.

La memoria se guarda en SQLite mediante un checkpointer de LangGraph. Las eliminaciones realizadas desde el agente requieren confirmación del usuario.

## Consideraciones

- El servidor MCP trabaja únicamente con las carpetas permitidas del proyecto.
- Si existen archivos con el mismo nombre en diferentes carpetas, se solicita especificar su ubicación.
- No se sobrescriben documentos cuando existe un conflicto de nombres.
- El archivo `.env` y las claves de API no deben subirse a GitHub.
- Las herramientas MCP tienen docstrings independientes del prompt del sistema.
