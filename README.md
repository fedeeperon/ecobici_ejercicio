# Pipeline Ecobici — Bronze / Silver / Gold

Pipeline de datos con pandas sobre los viajes de Ecobici (2016, 2019 y 2024).
Ejercicio de Ciencia de Datos, UTN FRVM.

## Requisitos

- Python 3.11
- Librerías de `requirements.txt` (pandas 2.2.3, pyarrow)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

## Datos de origen

Descargar del dataset [Bicicletas Públicas](https://data.buenosaires.gob.ar/dataset/bicicletas-publicas)
los recorridos (ZIP) y los usuarios (CSV) de 2016, 2019 y 2024, y guardarlos **sin
descomprimir ni modificar** en `data/raw/` con estos nombres:

```
data/raw/
├── recorridos-realizados-2016.zip
├── recorridos-realizados-2019.zip
├── recorridos-realizados-2024.zip
├── usuarios-ecobici-2016.csv
├── usuarios_ecobici_2019.csv
└── usuarios_ecobici_2024.csv
```

## Ejecución

```bash
python main.py
```

Genera `data/bronze/`. Se puede ejecutar todas las veces que se quiera: cada corrida
sobrescribe el resultado anterior.

Las decisiones tomadas están en `DECISIONES.md`.
