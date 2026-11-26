"""Ejecuta el pipeline Ecobici completo: bronze -> silver -> gold -> reportes."""

from src.bronze import ejecutar_bronze
from src.gold import ejecutar_gold
from src.silver import ejecutar_silver


def main() -> None:
    print("== Bronze ==")
    ejecutar_bronze()
    print("== Silver ==")
    ejecutar_silver()
    print("== Gold ==")
    ejecutar_gold()


if __name__ == "__main__":
    main()
