"""Capa Bronze: copia fiel de los archivos de data/raw/ en Parquet.

Todo se lee como texto, sin renombrar columnas ni limpiar nada. Solo se agregan
tres columnas de metadatos de ingesta: _archivo_origen, _fecha_ingesta y _anio.
"""

import os
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parent.parent
DIR_RAW = RAIZ / "data" / "raw"
DIR_BRONZE = RAIZ / "data" / "bronze"

# Mapeo explícito archivo -> (año, tipo). Los nombres no siguen un patrón común,
# así que el año NO se deduce del nombre (ver DECISIONES.md).
ARCHIVOS_ORIGEN = {
    "recorridos-realizados-2016.zip": (2016, "recorridos"),
    "recorridos-realizados-2019.zip": (2019, "recorridos"),
    "recorridos-realizados-2024.zip": (2024, "recorridos"),
    "usuarios-ecobici-2016.csv": (2016, "usuarios"),
    "usuarios_ecobici_2019.csv": (2019, "usuarios"),
    "usuarios_ecobici_2024.csv": (2024, "usuarios"),
}

COLUMNAS_METADATOS = ["_archivo_origen", "_fecha_ingesta", "_anio"]

# Opciones de lectura comunes a todos los archivos (ver DECISIONES.md):
# - dtype=str: todo como texto, sin conversiones.
# - utf-8-sig: quita el BOM de los archivos 2024 sin afectar a los que no lo tienen.
# - keep_default_na=False + na_values=[""]: solo el campo vacío es nulo; textos
#   como "NA" o "null" se conservan tal cual vinieron.
OPCIONES_LECTURA = dict(
    dtype=str,
    encoding="utf-8-sig",
    keep_default_na=False,
    na_values=[""],
)

TAMANIO_CHUNK = 500_000


def elegir_csv_del_zip(ruta_zip: Path) -> str:
    """Devuelve el nombre del CSV dentro del ZIP. Falla si no hay exactamente uno."""
    with zipfile.ZipFile(ruta_zip) as zf:
        csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    if len(csvs) != 1:
        raise ValueError(
            f"{ruta_zip.name}: se esperaba un único CSV dentro del ZIP y hay {csvs}"
        )
    return csvs[0]


def leer_por_partes(ruta: Path):
    """Itera el archivo de origen en chunks de texto, leyendo ZIPs sin descomprimir."""
    if ruta.suffix.lower() == ".zip":
        miembro = elegir_csv_del_zip(ruta)
        with zipfile.ZipFile(ruta) as zf:
            if len(zf.namelist()) == 1:
                # Caso normal: un solo archivo, pandas lo lee directo del ZIP.
                yield from pd.read_csv(
                    ruta, compression="zip", chunksize=TAMANIO_CHUNK, **OPCIONES_LECTURA
                )
            else:
                with zf.open(miembro) as f:
                    yield from pd.read_csv(f, chunksize=TAMANIO_CHUNK, **OPCIONES_LECTURA)
    else:
        yield from pd.read_csv(ruta, chunksize=TAMANIO_CHUNK, **OPCIONES_LECTURA)


def ingestar_archivo(ruta: Path, anio: int, destino: Path, fecha_ingesta: str) -> int:
    """Copia un archivo de origen a destino/anio=AAAA/data.parquet. Devuelve las filas.

    Se escribe por partes con un ParquetWriter sobre un archivo temporal que al final
    reemplaza al anterior: así cada ejecución sobrescribe el resultado (idempotencia)
    y nunca queda un data.parquet a medio escribir.
    """
    carpeta = destino / f"anio={anio}"
    carpeta.mkdir(parents=True, exist_ok=True)
    final = carpeta / "data.parquet"
    temporal = carpeta / "data.parquet.tmp"

    writer = None
    filas = 0
    try:
        for chunk in leer_por_partes(ruta):
            chunk["_archivo_origen"] = ruta.name
            chunk["_fecha_ingesta"] = fecha_ingesta
            chunk["_anio"] = str(anio)
            if writer is None:
                esquema = pa.schema([(c, pa.string()) for c in chunk.columns])
                writer = pq.ParquetWriter(temporal, esquema)
            writer.write_table(
                pa.Table.from_pandas(chunk, schema=esquema, preserve_index=False)
            )
            filas += len(chunk)
    finally:
        if writer is not None:
            writer.close()

    os.replace(temporal, final)
    return filas


def ejecutar_bronze() -> dict:
    """Ingesta todos los archivos de origen. Devuelve {(tipo, anio): filas}."""
    fecha_ingesta = datetime.now().isoformat(timespec="seconds")
    conteos = {}
    for nombre, (anio, tipo) in ARCHIVOS_ORIGEN.items():
        ruta = DIR_RAW / nombre
        if not ruta.exists():
            raise FileNotFoundError(f"Falta el archivo de origen: {ruta}")
        filas = ingestar_archivo(ruta, anio, DIR_BRONZE / tipo, fecha_ingesta)
        conteos[(tipo, anio)] = filas
        print(f"  bronze/{tipo}/anio={anio}: {filas:,} filas  <- {nombre}")
    return conteos
