from pathlib import Path

def scan(root=".", exclude=None):
    """
    Faz varredura completa de diretórios e arquivos.

    Args:
        root (str): Caminho base.
        exclude (list[str]): Pastas a ignorar.

    Returns:
        list[Path]: Lista com todos os caminhos encontrados.
    """
    root = Path(root).resolve()
    exclude = set(exclude or [])
    items = []

    for path in sorted(root.rglob("*")):
        if any(ex in path.parts for ex in exclude):
            continue
        items.append(path)
    return items
