
"""Interfaz del agente con memoria persistente en SQLite."""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.types import Command

from src.grafo.grafo import crear_grafo

load_dotenv()


# Ruta donde guardaremos la memoria del agente.
RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_MEMORIA = RAIZ_PROYECTO / "data" / "memoria.sqlite3"

# Identificador de nuestra conversación.
THREAD_ID = "conversacion_principal"


def elegir_modelo() -> tuple[str, str]:
    """Permite seleccionar el modelo antes de conversar."""

    opciones = {
        "1": ("ollama", "qwen3:4b-instruct"),
        "2": ("ollama", "qwen2.5:3b"),
        "3": ("gemini", os.getenv("GEMINI_MODEL", "gemini-3.8-flash")),
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


async def resolver_confirmaciones(grafo, config, resultado):
    """Solicita autorización para continuar un grafo interrumpido."""

    # Repetimos si el grafo necesita alguna confirmación.
    while resultado.get("__interrupt__"):

        interrupciones = resultado["__interrupt__"]

        for interrupcion in interrupciones:
            datos = interrupcion.value

            print("\n=== CONFIRMACIÓN NECESARIA ===")
            print("El agente quiere ejecutar:")

            # Mostramos todas las operaciones pendientes.
            for operacion in datos["operaciones"]:
                print(f"\nHerramienta: {operacion['herramienta']}")
                print(f"Parámetros: {operacion['argumentos']}")

        # Pedimos una respuesta válida.
        while True:
            decision = input(
                "\n¿Autorizas estas operaciones? (s/N): "
            ).strip().lower()

            if decision in {"s", "si", "sí"}:
                aprobado = True
                break

            if decision in {"", "n", "no"}:
                aprobado = False
                break

            print("Responde 's' para confirmar o 'n' para cancelar.")

        # Reanudamos el grafo con la decisión del usuario.
        resultado = await grafo.ainvoke(
            Command(resume=aprobado),
            config=config,
        )

    return resultado


async def main():
    """Inicia el agente y recupera la conversación guardada."""

    proveedor, modelo = elegir_modelo()

    # Nos aseguramos de que exista la carpeta de datos.
    RUTA_MEMORIA.parent.mkdir(parents=True, exist_ok=True)

    # Abrimos la conexión con SQLite.
    async with AsyncSqliteSaver.from_conn_string(
        str(RUTA_MEMORIA)
    ) as memoria:

        # Creamos el grafo con memoria persistente.
        grafo = await crear_grafo(
            proveedor,
            modelo,
            checkpointer=memoria,
        )

        # Identificamos la conversación que queremos recuperar.
        config = {
            "configurable": {
                "thread_id": THREAD_ID
            }
        }

        # Recuperamos el estado anterior, si existe.
        estado = await grafo.aget_state(config)
        mensajes_guardados = estado.values.get("messages", [])

        print(f"\nModelo seleccionado: {proveedor} / {modelo}")
        print(f"Conversación: {THREAD_ID}")
        print(f"Mensajes recuperados: {len(mensajes_guardados)}")
        print("Escribe 'salir' para terminar.\n")

        # Comprobamos si quedó una operación pendiente
        # de confirmar en una ejecución anterior.
        if estado.interrupts:
            print("\nHay una operación pendiente de confirmación.")

            resultado_pendiente = await resolver_confirmaciones(
                grafo,
                config,
                {"__interrupt__": estado.interrupts},
            )

            respuesta_pendiente = resultado_pendiente["messages"][-1]
            print(f"\nAgente> {respuesta_pendiente.text}\n")

        while True:
            texto = input("Tú> ").strip()

            if texto.lower() in {"salir", "exit", "quit"}:
                break

            if not texto:
                continue

            try:
                # Consultamos cuántos mensajes hay guardados.
                estado_anterior = await grafo.aget_state(config)
                cantidad_anterior = len(
                    estado_anterior.values.get("messages", [])
                )

                # Enviamos solamente el mensaje nuevo.
                resultado = await grafo.ainvoke(
                    {"messages": [HumanMessage(content=texto)]},
                    config=config,
                )

                # Si el grafo se ha pausado, pedimos confirmación.
                resultado = await resolver_confirmaciones(
                    grafo,
                    config,
                    resultado,
                )

                # Mostramos las herramientas utilizadas en esta petición.
                mensajes_nuevos = resultado["messages"][
                    cantidad_anterior + 1:
                ]

                for mensaje in mensajes_nuevos:
                    if isinstance(mensaje, AIMessage):
                        for llamada in mensaje.tool_calls:
                            print(f"[MCP solicitado] {llamada['name']}")
                            print(f"      Parámetros: {llamada['args']}")

                # Mostramos la respuesta final.
                respuesta = resultado["messages"][-1]
                print(f"\nAgente> {respuesta.text}\n")

            except Exception as error:
                print(f"\nError al ejecutar el agente: {error}\n")


if __name__ == "__main__":
    asyncio.run(main())
