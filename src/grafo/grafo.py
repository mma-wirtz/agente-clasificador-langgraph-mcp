
"""Grafo LangGraph para nuestro agente clasificador."""

import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command, interrupt

from src.config.modelos import crear_llm


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

SYSTEM_PROMPT = """
Eres un asistente para organizar archivos de texto.
Responde siempre en español.

Utiliza las herramientas disponibles cuando necesites
consultar, importar, crear, buscar, editar, clasificar,
eliminar o restaurar archivos.

Si el usuario cancela una operación, respeta su decisión.

Para clasificar un archivo, lee primero su contenido
y elige una de las categorías predefinidas.

No inventes resultados de herramientas.
"""


async def crear_grafo(
    proveedor: str,
    nombre_modelo: str,
    checkpointer=None
):
    """Construye el grafo y conecta las herramientas MCP."""

    # 1. Creamos el modelo seleccionado.
    llm = crear_llm(proveedor, nombre_modelo)

    # 2. Configuramos la conexión con nuestro servidor MCP.
    cliente_mcp = MultiServerMCPClient(
        {
            "archivos": {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["-m", "src.mcp.servidor"],
                "cwd": str(RAIZ_PROYECTO),
            }
        }
    )

    # 3. Obtenemos las herramientas del servidor.
    herramientas = await cliente_mcp.get_tools()

    # 4. Damos acceso al modelo a esas herramientas.
    llm_con_tools = llm.bind_tools(herramientas)

    # 5. Creamos el nodo principal del agente.
    async def agente(estado: MessagesState):
        mensajes = [
            SystemMessage(content=SYSTEM_PROMPT),
            *estado["messages"],
        ]

        respuesta = await llm_con_tools.ainvoke(mensajes)

        return {"messages": [respuesta]}

    
    # Nodo que comprueba si una herramienta necesita confirmación.
    def confirmar_eliminacion(estado: MessagesState):

        # Obtenemos las herramientas solicitadas por el modelo.
        mensaje = estado["messages"][-1]
        llamadas = mensaje.tool_calls

        # Comprobamos si alguna quiere eliminar un archivo.
        eliminaciones = [
            llamada
            for llamada in llamadas
            if llamada["name"] == "eliminar_archivo"
        ]

        # Si no hay eliminaciones, ejecutamos normalmente.
        if not eliminaciones:
            return Command(goto="tools")

        # Pausamos ANTES de ejecutar cualquier herramienta.
        aprobado = interrupt({
            "tipo": "confirmacion_eliminacion",
            "operaciones": [
                {
                    "herramienta": llamada["name"],
                    "argumentos": llamada["args"]
                }
                for llamada in llamadas
            ]
        })

        # Si el usuario confirma, permitimos la ejecución.
        if aprobado is True:
            return Command(goto="tools")

        # Si rechaza, cancelamos TODAS las herramientas
        # solicitadas en esta tanda.
        respuestas_canceladas = [
            ToolMessage(
                content="Operación cancelada por el usuario. No ejecutada.",
                tool_call_id=llamada["id"],
                name=llamada["name"],
            )
            for llamada in llamadas
        ]

        return Command(
            update={
                "messages": [
                    *respuestas_canceladas,
                    AIMessage(
                        content=(
                            "Operación cancelada. No he ejecutado "
                            "ninguna herramienta de esta solicitud."
                        )
                    )
                ]
            },
            goto=END,
        )

    # 6. Construimos el grafo.
    constructor = StateGraph(MessagesState)

    
    constructor.add_node("agente", agente)

    constructor.add_node(
        "confirmar_eliminacion",
        confirmar_eliminacion,
        destinations=("tools", END),
    )

    constructor.add_node("tools", ToolNode(herramientas))

    # 7. Definimos las conexiones entre nodos.
    constructor.add_edge(START, "agente")

    constructor.add_conditional_edges(
        "agente",
        tools_condition,
        {
            "tools": "confirmar_eliminacion",
            END: END,
        },
    )

    constructor.add_edge("tools", "agente")

    # 8. Compilamos el grafo.
    grafo = constructor.compile(checkpointer=checkpointer)

    return grafo
