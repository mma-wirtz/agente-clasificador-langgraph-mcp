
"""Comprueba que el grafo se construye correctamente."""

import asyncio

from src.grafo.grafo import crear_grafo


async def main():
    grafo = await crear_grafo(
        proveedor="gemini",
        nombre_modelo="gemini-3.8-flash",
    )

    print("Grafo construido correctamente.")
    print("\nNodos del grafo:")

    for nodo in grafo.get_graph().nodes:
        print(f"- {nodo}")


if __name__ == "__main__":
    asyncio.run(main())
