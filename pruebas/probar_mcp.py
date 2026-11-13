
"""Prueba de conexión real con el servidor MCP."""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]


async def probar_conexion():

    # Indicamos cómo arrancar nuestro servidor.
    servidor = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.mcp.servidor"],
        cwd=str(RAIZ_PROYECTO),
    )

    # Abrimos la comunicación con el servidor.
    async with stdio_client(servidor) as (lectura, escritura):

        # Creamos una sesión MCP.
        async with ClientSession(lectura, escritura) as sesion:

            # Establecemos la conexión.
            await sesion.initialize()

            print("Conexión MCP establecida correctamente.")

            # Pedimos al servidor sus herramientas.
            resultado = await sesion.list_tools()

            print("\nHerramientas disponibles:")

            for herramienta in resultado.tools:
                print(f"- {herramienta.name}")

            # Ejecutamos una herramienta mediante MCP.
            respuesta = await sesion.call_tool(
                "listar_archivos_recepcion",
                arguments={},
            )

            print("\nResultado de listar archivos en recepción:")

            for bloque in respuesta.content:
                if bloque.type == "text":
                    print(bloque.text)


if __name__ == "__main__":
    asyncio.run(probar_conexion())
