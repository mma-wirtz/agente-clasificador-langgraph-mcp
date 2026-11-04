"""Fase 1: seleccionar un LLM antes de iniciar la conversación.

En próximas fases se reemplazará este bucle por el grafo LangGraph,
el servidor MCP y un checkpointer SQLite.
"""
import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from src.config.ajustes import SYSTEM_PROMPT
from src.config.modelos import crear_llm

load_dotenv()


def elegir_modelo() -> tuple[str, str]:
    opciones = {
        "1": ("ollama", "qwen3:4b-instruct"),
        "2": ("ollama", "qwen2.5:3b"),
        "3": ("gemini", os.getenv("GEMINI_MODEL", "gemini-2.5-flash")),
    }
    print("\n=== SELECCIÓN DEL MODELO ===")
    print("1. Ollama · Qwen3 4B Instruct")
    print("2. Ollama · Qwen2.5 3B")
    print("3. Gemini · modelo configurado en .env")
    while True:
        eleccion = input("Elige una opción (1, 2 o 3): ").strip()
        if eleccion in opciones:
            return opciones[eleccion]
        print("Opción no válida.")


def main() -> None:
    proveedor, modelo = elegir_modelo()
    llm = crear_llm(proveedor, modelo)
    print(f"\nModelo seleccionado: {proveedor} / {modelo}")
    print("Escribe 'salir' para terminar.\n")

    # Historial TEMPORAL de fase 1. Más adelante usaremos checkpointer de LangGraph.
    mensajes = [SystemMessage(content=SYSTEM_PROMPT)]
    while True:
        texto = input("Tú> ").strip()
        if texto.lower() in {"salir", "exit", "quit"}:
            break
        if not texto:
            continue
        mensaje = HumanMessage(content=texto)
        try:
            respuesta = llm.invoke([*mensajes, mensaje])
        except Exception as exc:
            print(f"Error al consultar el modelo: {exc}")
            continue
        mensajes.extend((mensaje, respuesta))
        print(f"Agente> {respuesta.content}\n")


if __name__ == "__main__":
    main()
