
"""Servidor MCP con herramientas para gestionar archivos."""

from pathlib import Path
from mcp.server.fastmcp import FastMCP
import shutil


# Carpeta principal del proyecto.
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

# Carpeta desde la que importaremos archivos.
CARPETA_ORIGEN = RAIZ_PROYECTO / "data" / "origen"

# Carpeta en la que copiaremos los archivos.
CARPETA_RECEPCION = RAIZ_PROYECTO / "data" / "recepcion"

# Creamos nuestro servidor MCP.
mcp = FastMCP("Clasificador de archivos")


@mcp.tool()
def listar_archivos_origen() -> list[str]:
    """
    Lista los archivos de texto disponibles en la carpeta de origen.

    Returns:
        Lista con los nombres de los archivos .txt encontrados.
    """
    archivos = sorted(CARPETA_ORIGEN.glob("*.txt"))

    return [archivo.name for archivo in archivos]


@mcp.tool()
def importar_archivo(nombre_archivo: str) -> str:
    """
    Copia un archivo de texto desde origen hasta recepcion.

    Args:
        nombre_archivo: Nombre del archivo .txt que se quiere importar.

    Returns:
        Mensaje indicando si la operación se realizó correctamente.
    """

    # Comprobamos que el usuario introduce un nombre válido.
    if (
        nombre_archivo != Path(nombre_archivo).name
        or not nombre_archivo.endswith(".txt")
        or nombre_archivo in {".", ".."}
    ):
        return "Error: debes indicar un nombre de archivo .txt válido."

    # Construimos las rutas de origen y destino.
    ruta_origen = CARPETA_ORIGEN / nombre_archivo
    ruta_destino = CARPETA_RECEPCION / nombre_archivo

    # Comprobamos que el archivo existe y es un archivo normal.
    if not ruta_origen.is_file() or ruta_origen.is_symlink():
        return f"Error: el archivo '{nombre_archivo}' no existe en origen."

    # Evitamos sobrescribir archivos existentes.
    if ruta_destino.exists() or ruta_destino.is_symlink():
        return f"Error: '{nombre_archivo}' ya existe en recepcion."

    # Creamos la carpeta de recepción si no existe.
    CARPETA_RECEPCION.mkdir(parents=True, exist_ok=True)

    # Copiamos el archivo conservando el original.
    shutil.copy2(ruta_origen, ruta_destino)

    return f"Archivo '{nombre_archivo}' importado correctamente."


if __name__ == "__main__":
    mcp.run()
