from langchain.tools import tool

@tool
def greet(name: str) -> str:
    """Greet a person by name"""
    return f"Hello, {name}!"