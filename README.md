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

Tarda unos 4 minutos y genera:

| Carpeta | Contenido |
|---|---|
| `data/bronze/` | Copia fiel de los archivos en Parquet, todo como texto (`recorridos/` y `usuarios/`, una carpeta por año) |
| `data/silver/` | `viajes`, `viajes_cuarentena`, `usuarios` y `usuarios_cuarentena` con el esquema canónico |
| `data/gold/` | Modelo estrella: `fact_viajes`, `dim_fecha`, `dim_estacion` y `dim_usuario` |
| `data/gold/reportes/` | Los 5 reportes en CSV |

Cada capa se genera solo desde la anterior y se verifica al terminar (conciliación de
filas, esquema, integridad referencial y controles entre reportes): si algo no cierra, el
pipeline se detiene con un error. Se puede ejecutar todas las veces que se quiera, porque
cada corrida sobrescribe el resultado anterior.

## Estructura

```
src/bronze.py     ingesta de data/raw a bronze
src/silver.py     esquema canónico, normalización y cuarentena
src/gold.py       modelo estrella
src/reportes.py   reportes en CSV
main.py           corre todo en orden
```

Las decisiones tomadas están en `DECISIONES.md`.
