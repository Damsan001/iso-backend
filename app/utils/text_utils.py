def clear_name(name: str) -> str:
    """
    Limpia el nombre del documento eliminando caracteres especiales y espacios.
    """
    return "".join(e for e in name if e.isalnum() or e in (" ", "-", "_")).strip()
