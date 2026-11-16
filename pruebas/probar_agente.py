
"""Prueba de integración entre Gemini, LangGraph y MCP."""

import asyncio
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.grafo.grafo import crear_grafo


load_dotenv()


async def main():
    # Creamos el grafo usando Gemini.
    grafo = await crear_grafo(
        proveedor="ollama",
        nombre_modelo="qwen3:4b-instruct",
    )

    # Preparamos la petición del usuario.
    pregunta = "¿Qué archivos tengo pendientes en recepción?"

    print(f"\nUsuario: {pregunta}")
    print("\nEjecutando el grafo...\n")

    # Ejecutamos el grafo con el mensaje del usuario.
    resultado = await grafo.ainvoke({
        "messages": [HumanMessage(content=pregunta)]
    })

    # Revisamos los mensajes generados durante la ejecución.
    for mensaje in resultado["messages"]:

        if isinstance(mensaje, AIMessage):
            if mensaje.tool_calls:
                for llamada in mensaje.tool_calls:
                    print(f"El agente solicita: {llamada['name']}")
                    print(f"Parámetros: {llamada['args']}")

            elif mensaje.text:
                print(f"\nAgente: {mensaje.text}")

        elif isinstance(mensaje, ToolMessage):
            print(f"Resultado de MCP: {mensaje.content}")


if __name__ == "__main__":
    asyncio.run(main())
