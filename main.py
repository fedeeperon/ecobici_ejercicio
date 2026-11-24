"""Ejecuta el pipeline Ecobici completo: bronze -> silver -> gold -> reportes."""

from src.bronze import ejecutar_bronze


def main() -> None:
    print("== Bronze ==")
    ejecutar_bronze()


if __name__ == "__main__":
    main()
