"""Ejecuta el pipeline Ecobici completo: bronze -> silver -> gold -> reportes."""

from src.bronze import ejecutar_bronze
from src.silver import ejecutar_silver


def main() -> None:
    print("== Bronze ==")
    ejecutar_bronze()
    print("== Silver ==")
    ejecutar_silver()


if __name__ == "__main__":
    main()
