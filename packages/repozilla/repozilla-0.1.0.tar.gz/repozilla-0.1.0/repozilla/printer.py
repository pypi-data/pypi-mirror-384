from pathlib import Path
from rich.console import Console
from rich.tree import Tree
from rich.theme import Theme


console = Console(theme=Theme({"dir": "bold cyan", "file": "green"}))


def build_tree(base_path=".", root_name=None, exclude=None, color=True):
    """Constrói e retorna a árvore em formato de texto."""
    base = Path(base_path).resolve()
    root_name = root_name or base.name
    exclude = set(exclude or [])

    lines = [f"{root_name}/"]

    for path in sorted(base.rglob("*")):
        # Ignora pastas que estejam na lista de exclusão
        if any(ex in path.parts for ex in exclude):
            continue

        depth = len(path.parts) - len(base.parts)
        indent = "    " * depth + "├── "

        if path.is_dir():
            if color:
                lines.append(f"{indent}[bold cyan]{path.name}/[/bold cyan]")
            else:
                lines.append(f"{indent}{path.name}/")
        else:
            if color:
                lines.append(f"{indent}[green]{path.name}[/green]")
            else:
                lines.append(f"{indent}{path.name}")

    return "\n".join(lines)


def show_tree(base_path=".", root_name=None, exclude=None, save_path=None, color=True):
    """Mostra a estrutura na tela e, se desejado, salva em arquivo."""
    result = build_tree(base_path, root_name, exclude, color=color)

    # Exibe no terminal (colorido)
    if color:
        console.print(result)
    else:
        print(result)

    # Salva se solicitado
    if save_path:
        # Se salvar, sempre salva o texto puro (sem cor)
        clean_text = build_tree(base_path, root_name, exclude, color=False)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(clean_text)
        console.print(f"\n💾 Estrutura salva em: [green]{save_path}[/green]")
