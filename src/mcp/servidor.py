
"""Servidor MCP con herramientas para gestionar archivos."""

from pathlib import Path
from mcp.server.fastmcp import FastMCP
from typing import Literal
import shutil


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

CARPETA_ORIGEN = RAIZ_PROYECTO / "data" / "origen"

CARPETA_RECEPCION = RAIZ_PROYECTO / "data" / "recepcion"

CARPETA_CLASIFICADOS = RAIZ_PROYECTO / "data" / "clasificados"

CATEGORIAS = ["tecnologia", "salud", "economia", "educacion", "otros"]

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


@mcp.tool()
def crear_archivo(nombre_archivo: str, contenido: str) -> str:
    """
    Crea un archivo de texto en la carpeta de recepción.

    Args:
        nombre_archivo: Nombre del archivo .txt que se quiere crear.
        contenido: Texto que se guardará dentro del archivo.

    Returns:
        Mensaje indicando si el archivo se ha creado correctamente.
    """

    # Comprobamos que el nombre del archivo sea válido.
    if (
        not nombre_archivo.endswith(".txt")
        or nombre_archivo != Path(nombre_archivo).name
        or "/" in nombre_archivo
        or "\\" in nombre_archivo
    ):
        return "Error: debes indicar un nombre de archivo .txt válido."

    # Comprobamos que el contenido no esté vacío.
    if not contenido.strip():
        return "Error: el contenido del archivo no puede estar vacío."

    # Creamos la carpeta de recepción si no existe.
    CARPETA_RECEPCION.mkdir(parents=True, exist_ok=True)

    # Construimos la ruta del nuevo archivo.
    ruta_archivo = CARPETA_RECEPCION / nombre_archivo

    try:
        # El modo "x" crea el archivo solo si no existe.
        with ruta_archivo.open("x", encoding="utf-8") as archivo:
            archivo.write(contenido)

    except FileExistsError:
        return f"Error: '{nombre_archivo}' ya existe en recepción."

    return f"Archivo '{nombre_archivo}' creado correctamente en recepción."


@mcp.tool()
def leer_archivo(nombre_archivo: str) -> str:
    """
    Lee el contenido de un archivo de texto de recepción.

    Args:
        nombre_archivo: Nombre del archivo .txt que se quiere leer.

    Returns:
        Contenido del archivo o mensaje de error.
    """

    # Comprobamos que el nombre sea válido.
    if (
        not nombre_archivo.endswith(".txt")
        or nombre_archivo != Path(nombre_archivo).name
        or "/" in nombre_archivo
        or "\\" in nombre_archivo
    ):
        return "Error: debes indicar un nombre de archivo .txt válido."

    # Construimos la ruta del archivo.
    ruta_archivo = CARPETA_RECEPCION / nombre_archivo

    # Comprobamos que el archivo exista.
    if not ruta_archivo.is_file() or ruta_archivo.is_symlink():
        return f"Error: '{nombre_archivo}' no existe en recepción."

    # Leemos el contenido.
    try:
        contenido = ruta_archivo.read_text(encoding="utf-8")
        return contenido

    except UnicodeDecodeError:
        return f"Error: no se puede leer '{nombre_archivo}' como UTF-8."

    except OSError as error:
        return f"Error al leer el archivo: {error}"


    
@mcp.tool()
def listar_archivos_recepcion() -> list[str]:
    """
    Lista los archivos de texto pendientes de clasificación.

    Returns:
        Lista con los nombres de los archivos .txt
        que se encuentran en la carpeta de recepción.
    """

    # Buscamos todos los archivos .txt de recepción.
    archivos = sorted(CARPETA_RECEPCION.glob("*.txt"))

    # Devolvemos solamente sus nombres.
    return [
        archivo.name
        for archivo in archivos
        if archivo.is_file() and not archivo.is_symlink()
    ]


@mcp.tool()
def mover_archivo(
    nombre_archivo: str,
    categoria: Literal[
        "tecnologia",
        "salud",
        "economia",
        "educacion",
        "otros"
    ]
) -> str:
    """
    Mueve un archivo de recepción a una categoría existente
    o crea la carpeta de la categoría si no existe.

    Args:
        nombre_archivo: Nombre del archivo .txt que se quiere mover.
        categoria: Categoría de destino elegida por el agente.

    Returns:
        Mensaje indicando el resultado de la operación.
    """

    # Validamos el nombre del archivo.
    if (
        not nombre_archivo.endswith(".txt")
        or nombre_archivo != Path(nombre_archivo).name
        or "/" in nombre_archivo
        or "\\" in nombre_archivo
    ):
        return "Error: nombre de archivo no válido."

    # Normalizamos la categoría.
    categoria = categoria.strip().lower()

    # Solo permitimos categorías predefinidas.
    if categoria not in CATEGORIAS:
        return f"Error: categoría no válida. Usa una de estas: {CATEGORIAS}"

    # Preparamos las rutas.
    ruta_origen = CARPETA_RECEPCION / nombre_archivo
    carpeta_destino = CARPETA_CLASIFICADOS / categoria
    ruta_destino = carpeta_destino / nombre_archivo

    # Comprobamos que el archivo exista.
    if not ruta_origen.is_file() or ruta_origen.is_symlink():
        return f"Error: '{nombre_archivo}' no existe en recepción."

    # Evitamos sobrescribir archivos.
    if ruta_destino.exists() or ruta_destino.is_symlink():
        return f"Error: '{nombre_archivo}' ya existe en '{categoria}'."

    # Creamos la carpeta de categoría si no existe.
    carpeta_destino.mkdir(parents=True, exist_ok=True)

    # Movemos el archivo.
    shutil.move(str(ruta_origen), str(ruta_destino))

    return f"Archivo '{nombre_archivo}' clasificado en '{categoria}'."


@mcp.tool()
def listar_archivos_por_tema(tema: str) -> list[str]:
    """
    Lista los archivos clasificados en una categoría concreta.

    Args:
        tema: Categoría que se quiere consultar.

    Returns:
        Lista con los nombres de los archivos encontrados.
    """

    # Normalizamos el tema introducido.
    tema = tema.strip().lower()

    # Comprobamos que sea una categoría permitida.
    if tema not in CATEGORIAS:
        return [f"Error: categoría no válida. Usa una de estas: {CATEGORIAS}"]

    # Construimos la ruta de la carpeta correspondiente.
    carpeta_tema = CARPETA_CLASIFICADOS / tema

    # Si la carpeta todavía no existe, no hay archivos.
    if not carpeta_tema.is_dir():
        return []

    # Buscamos los archivos .txt de esa categoría.
    archivos = sorted(carpeta_tema.glob("*.txt"))

    # Devolvemos únicamente los nombres.
    return [
        archivo.name
        for archivo in archivos
        if archivo.is_file() and not archivo.is_symlink()
    ]


if __name__ == "__main__":
    mcp.run()
