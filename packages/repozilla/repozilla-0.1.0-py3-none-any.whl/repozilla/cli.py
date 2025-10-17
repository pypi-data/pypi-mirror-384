import argparse
from repozilla.printer import show_tree


def main():
    parser = argparse.ArgumentParser(description="🦖 Repozilla — explorador de diretórios com estilo!")
    parser.add_argument("path", nargs="*", default=["."], help="Caminho para listar (padrão: .)")
    parser.add_argument("--exclude", nargs="*", default=[], help="Pastas a excluir da listagem")
    parser.add_argument("--save", help="Salva a estrutura em um arquivo de texto (ex: estrutura.txt)")
    args = parser.parse_args()

    show_tree(
        base_path=args.path[0],
        exclude=args.exclude,
        save_path=args.save
    )


if __name__ == "__main__":
    main()
