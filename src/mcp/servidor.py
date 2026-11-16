
"""Servidor MCP con herramientas para gestionar archivos."""

from pathlib import Path
from mcp.server.fastmcp import FastMCP
from typing import Literal
import shutil
import os
import tempfile


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

CARPETA_ORIGEN = RAIZ_PROYECTO / "data" / "origen"

CARPETA_RECEPCION = RAIZ_PROYECTO / "data" / "recepcion"

CARPETA_CLASIFICADOS = RAIZ_PROYECTO / "data" / "clasificados"

CATEGORIAS = ["tecnologia", "salud", "economia", "educacion", "otros"]

CARPETA_PAPELERA = RAIZ_PROYECTO / "data" / "papelera"

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
def leer_archivo(
    nombre_archivo: str,
    ubicacion: Literal[
        "auto",
        "recepcion",
        "tecnologia",
        "salud",
        "economia",
        "educacion",
        "otros"
    ] = "auto"
) -> str:
    """
    Lee el contenido de un archivo .txt.

    Busca automáticamente el archivo en recepción y en
    las categorías si no se indica una ubicación.

    Args:
        nombre_archivo: Nombre del archivo que se desea leer.
        ubicacion: 'auto' para buscar en todas las carpetas,
            o una ubicación concreta si existen duplicados.

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
        return "Error: nombre de archivo no válido."

    ubicacion = ubicacion.strip().lower()

    # Si no sabemos dónde está, lo buscamos.
    if ubicacion == "auto":

        ubicaciones = buscar_archivo(nombre_archivo)

        if not ubicaciones:
            return f"Error: no se encontró '{nombre_archivo}'."

        if len(ubicaciones) > 1:
            return (
                f"Error: '{nombre_archivo}' existe en varias "
                f"ubicaciones: {ubicaciones}. "
                "Indica cuál quieres consultar."
            )

        ubicacion = ubicaciones[0]

    # Determinamos la carpeta donde está el archivo.
    if ubicacion == "recepcion":
        carpeta = CARPETA_RECEPCION

    elif ubicacion in CATEGORIAS:
        carpeta = CARPETA_CLASIFICADOS / ubicacion

    else:
        return "Error: ubicación no permitida."

    # Comprobamos que no haya enlaces simbólicos
    # en las carpetas utilizadas.
    if carpeta.is_symlink() or CARPETA_CLASIFICADOS.is_symlink():
        return "Error: carpeta no permitida."

    ruta_archivo = carpeta / nombre_archivo

    if not ruta_archivo.is_file() or ruta_archivo.is_symlink():
        return f"Error: '{nombre_archivo}' no existe en '{ubicacion}'."

    # Leemos el contenido.
    try:
        return ruta_archivo.read_text(encoding="utf-8")

    except UnicodeDecodeError:
        return "Error: el archivo no tiene formato UTF-8."

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



@mcp.tool()
def editar_archivo(
    nombre_archivo: str,
    nuevo_contenido: str,
    ubicacion: Literal[
        "auto",
        "recepcion",
        "tecnologia",
        "salud",
        "economia",
        "educacion",
        "otros"
    ] = "auto"
) -> str:
    """
    Sustituye todo el contenido de un archivo .txt.

    Si el archivo está clasificado, lo devuelve a recepción
    para que pueda volver a clasificarse.

    Args:
        nombre_archivo: Nombre del archivo que se quiere editar.
        nuevo_contenido: Texto completo que sustituirá al anterior.
        ubicacion: Carpeta actual del archivo. Puede ser
            'recepcion' o una de las categorías permitidas.

    Returns:
        Mensaje indicando el resultado de la edición.
    """

    # 1. Validamos el nombre.
    if (
        not nombre_archivo.endswith(".txt")
        or nombre_archivo != Path(nombre_archivo).name
        or "/" in nombre_archivo
        or "\\" in nombre_archivo
    ):
        return "Error: nombre de archivo no válido."

    # 2. Comprobamos el contenido.
    if not nuevo_contenido.strip():
        return "Error: el contenido no puede estar vacío."

    # 3. Comprobamos la ubicación.
    ubicacion = ubicacion.strip().lower()


    # Si no se indica carpeta, buscamos el archivo.
    if ubicacion == "auto":
        ubicaciones = buscar_archivo(nombre_archivo)

        if not ubicaciones:
            return f"Error: no se encontró '{nombre_archivo}'."

        if len(ubicaciones) > 1:
            return (
                f"Error: '{nombre_archivo}' aparece en varias "
                f"ubicaciones: {ubicaciones}. "
                "Indica cuál quieres editar."
            )

        # Utilizamos la única ubicación encontrada.
        ubicacion = ubicaciones[0]

    if ubicacion == "recepcion":
        carpeta_origen = CARPETA_RECEPCION
    elif ubicacion in CATEGORIAS:
        carpeta_origen = CARPETA_CLASIFICADOS / ubicacion
    else:
        return "Error: ubicación no permitida."

    ruta_origen = carpeta_origen / nombre_archivo
    ruta_destino = CARPETA_RECEPCION / nombre_archivo

    # 4. Comprobamos que el archivo exista.
    if (
        carpeta_origen.is_symlink()
        or CARPETA_RECEPCION.is_symlink()
        or not ruta_origen.is_file()
        or ruta_origen.is_symlink()
    ):
        return "Error: archivo inexistente o ruta no permitida."

    try:
        CARPETA_RECEPCION.mkdir(parents=True, exist_ok=True)

        # 5. Si estaba clasificado, creamos la nueva versión
        # en recepción sin sobrescribir otros archivos.
        if ubicacion != "recepcion":

            try:
                with ruta_destino.open("x", encoding="utf-8") as archivo:
                    archivo.write(nuevo_contenido)
            except FileExistsError:
                return "Error: ya existe un archivo con ese nombre en recepción."

            # Eliminamos el original una vez guardada la nueva versión.
            try:
                ruta_origen.unlink()
            except OSError:
                ruta_destino.unlink(missing_ok=True)
                raise

        else:
            # 6. Si estaba en recepción, escribimos primero
            # en un archivo temporal para evitar perder el original.
            ruta_temporal = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=CARPETA_RECEPCION,
                    prefix=".edicion_",
                    suffix=".tmp",
                    delete=False
                ) as archivo:
                    ruta_temporal = Path(archivo.name)
                    archivo.write(nuevo_contenido)

                os.replace(ruta_temporal, ruta_origen)

            finally:
                if ruta_temporal is not None:
                    ruta_temporal.unlink(missing_ok=True)

        return (
            f"Archivo '{nombre_archivo}' editado correctamente. "
            "Está en recepción, pendiente de clasificar."
        )

    except OSError as error:
        return f"Error al editar el archivo: {error}"



@mcp.tool()
def buscar_archivo(nombre_archivo: str) -> list[str]:
    """
    Busca un archivo .txt por su nombre en recepción
    y en todas las categorías de archivos clasificados.

    Args:
        nombre_archivo: Nombre del archivo que se desea localizar.

    Returns:
        Lista de ubicaciones donde se ha encontrado.
        Si no existe, devuelve una lista vacía.
    """

    # Validamos el nombre del archivo.
    if (
        not nombre_archivo.endswith(".txt")
        or nombre_archivo != Path(nombre_archivo).name
        or "/" in nombre_archivo
        or "\\" in nombre_archivo
    ):
        return ["Error: nombre de archivo no válido."]

    ubicaciones = []

    # Buscamos primero en recepción.
    carpetas = [("recepcion", CARPETA_RECEPCION)]

    # Añadimos las categorías permitidas.
    for categoria in CATEGORIAS:
        carpetas.append((
            categoria,
            CARPETA_CLASIFICADOS / categoria
        ))

    # Recorremos las carpetas buscando el archivo.
    for nombre_carpeta, ruta_carpeta in carpetas:

        if ruta_carpeta.is_symlink():
            continue

        ruta_archivo = ruta_carpeta / nombre_archivo

        if ruta_archivo.is_file() and not ruta_archivo.is_symlink():
            ubicaciones.append(nombre_carpeta)

    return ubicaciones


@mcp.tool()
def eliminar_archivo(
    nombre_archivo: str,
    ubicacion: Literal[
        "auto",
        "recepcion",
        "tecnologia",
        "salud",
        "economia",
        "educacion",
        "otros"
    ] = "auto"
) -> str:
    """
    Envía un archivo de texto a la papelera.

    Busca automáticamente el archivo si no se indica ubicación.
    No elimina definitivamente el documento.

    Args:
        nombre_archivo: Nombre del archivo .txt que se desea eliminar.
        ubicacion: 'auto' para buscarlo o su carpeta concreta.

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

    ubicacion = ubicacion.strip().lower()

    # Localizamos el documento.
    if ubicacion == "auto":
        ubicaciones = buscar_archivo(nombre_archivo)

        if not ubicaciones:
            return f"Error: no se encontró '{nombre_archivo}'."

        if len(ubicaciones) > 1:
            return (
                f"Error: '{nombre_archivo}' existe en varias "
                f"ubicaciones: {ubicaciones}. "
                "Indica cuál quieres eliminar."
            )

        ubicacion = ubicaciones[0]

    # Determinamos su carpeta actual.
    if ubicacion == "recepcion":
        carpeta_origen = CARPETA_RECEPCION

    elif ubicacion in CATEGORIAS:
        carpeta_origen = CARPETA_CLASIFICADOS / ubicacion

    else:
        return "Error: ubicación no permitida."

    ruta_origen = carpeta_origen / nombre_archivo
    ruta_destino = CARPETA_PAPELERA / nombre_archivo

    # Comprobamos que la ruta sea segura.
    if (
        carpeta_origen.is_symlink()
        or CARPETA_CLASIFICADOS.is_symlink()
        or CARPETA_PAPELERA.is_symlink()
        or not ruta_origen.is_file()
        or ruta_origen.is_symlink()
    ):
        return "Error: archivo inexistente o ruta no permitida."

    # Creamos la papelera.
    CARPETA_PAPELERA.mkdir(parents=True, exist_ok=True)

    # Evitamos sobrescribir archivos eliminados anteriormente.
    if ruta_destino.exists() or ruta_destino.is_symlink():
        return (
            f"Error: ya existe '{nombre_archivo}' en la papelera. "
            "No se ha eliminado el archivo original."
        )

    try:
        shutil.move(str(ruta_origen), str(ruta_destino))

        return (
            f"Archivo '{nombre_archivo}' enviado a la papelera "
            "correctamente."
        )

    except OSError as error:
        return f"Error al eliminar el archivo: {error}"



@mcp.tool()
def listar_papelera() -> list[str]:
    """
    Lista los archivos de texto que están en la papelera.

    Returns:
        Lista con los nombres de los archivos eliminados.
    """

    # Si la carpeta no existe o es un enlace, no la consultamos.
    if not CARPETA_PAPELERA.is_dir() or CARPETA_PAPELERA.is_symlink():
        return []

    archivos = sorted(CARPETA_PAPELERA.glob("*.txt"))

    return [
        archivo.name
        for archivo in archivos
        if archivo.is_file() and not archivo.is_symlink()
    ]



@mcp.tool()
def restaurar_archivo(nombre_archivo: str) -> str:
    """
    Restaura un archivo .txt desde la papelera a recepción.

    Args:
        nombre_archivo: Nombre del documento que se quiere recuperar.

    Returns:
        Mensaje indicando el resultado de la restauración.
    """

    # Validamos el nombre del archivo.
    if (
        not nombre_archivo.endswith(".txt")
        or nombre_archivo != Path(nombre_archivo).name
        or "/" in nombre_archivo
        or "\\" in nombre_archivo
    ):
        return "Error: nombre de archivo no válido."

    ruta_origen = CARPETA_PAPELERA / nombre_archivo
    ruta_destino = CARPETA_RECEPCION / nombre_archivo

    # Evitamos acceder a enlaces simbólicos.
    if (
        CARPETA_PAPELERA.is_symlink()
        or CARPETA_RECEPCION.is_symlink()
        or not ruta_origen.is_file()
        or ruta_origen.is_symlink()
    ):
        return f"Error: '{nombre_archivo}' no existe en la papelera."

    # Creamos recepción si todavía no existe.
    CARPETA_RECEPCION.mkdir(parents=True, exist_ok=True)

    # No sobrescribimos archivos existentes.
    if ruta_destino.exists() or ruta_destino.is_symlink():
        return (
            f"Error: '{nombre_archivo}' ya existe en recepción. "
            "No se ha restaurado."
        )

    try:
        shutil.move(str(ruta_origen), str(ruta_destino))

        return (
            f"Archivo '{nombre_archivo}' restaurado correctamente "
            "en recepción, pendiente de clasificar."
        )

    except OSError as error:
        return f"Error al restaurar el archivo: {error}"


if __name__ == "__main__":
    mcp.run()
