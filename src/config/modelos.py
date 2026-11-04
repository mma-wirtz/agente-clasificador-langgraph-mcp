"""Configuración centralizada para cambiar el LLM sin tocar la lógica de agentes."""
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

load_dotenv()


def crear_llm(proveedor: str, nombre_modelo: str):
    """Devuelve una instancia de chat compatible con LangChain/LangGraph."""
    proveedor = proveedor.strip().lower()
    nombre_modelo = nombre_modelo.strip()
    if not nombre_modelo:
        raise ValueError("Debes indicar el nombre del modelo.")

    if proveedor == "ollama":
        return ChatOllama(
            model=nombre_modelo,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )
    if proveedor == "gemini":
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("Falta GOOGLE_API_KEY en el archivo .env.")
        return ChatGoogleGenerativeAI(model=nombre_modelo, temperature=0)

    raise ValueError(f"Proveedor no compatible: {proveedor}. Usa ollama o gemini.")
