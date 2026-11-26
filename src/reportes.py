"""Reportes en CSV a partir de las tablas gold (data/gold/reportes/).

Todos salen de gold, excepto calidad_por_anio.csv, que por enunciado usa los
conteos de bronze, silver y cuarentena.
"""

import os
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

RAIZ = Path(__file__).resolve().parent.parent
DIR_BRONZE = RAIZ / "data" / "bronze"
DIR_SILVER = RAIZ / "data" / "silver"
DIR_GOLD = RAIZ / "data" / "gold"
DIR_REPORTES = DIR_GOLD / "reportes"


def leer_gold(tabla: str, columnas: list[str] | None = None) -> pd.DataFrame:
    return pd.read_parquet(DIR_GOLD / tabla / "data.parquet", columns=columnas)


def guardar_csv(df: pd.DataFrame, nombre: str) -> None:
    """Escribe el CSV reemplazando el anterior (idempotente)."""
    DIR_REPORTES.mkdir(parents=True, exist_ok=True)
    temporal = DIR_REPORTES / f"{nombre}.tmp"
    df.to_csv(temporal, index=False, encoding="utf-8")
    os.replace(temporal, DIR_REPORTES / nombre)
    print(f"  reportes/{nombre}: {len(df)} filas")


def viajes_con_fecha() -> pd.DataFrame:
    """fact_viajes + año y mes de dim_fecha (fecha de inicio)."""
    fact = leer_gold("fact_viajes", ["fecha_key", "id_estacion_origen", "id_usuario",
                                     "duracion_min", "es_circular"])
    fechas = leer_gold("dim_fecha", ["fecha_key", "anio", "mes"])
    return fact.merge(fechas, on="fecha_key", how="left", validate="many_to_one")


# ---------------------------------------------------------------------------
# Reportes
# ---------------------------------------------------------------------------
def reporte_viajes_por_mes(viajes: pd.DataFrame) -> pd.DataFrame:
    return (viajes.groupby(["anio", "mes"]).size().reset_index(name="cantidad_viajes")
            .sort_values(["anio", "mes"]))


def reporte_top10_estaciones(viajes: pd.DataFrame) -> pd.DataFrame:
    estaciones = leer_gold("dim_estacion", ["id_estacion", "nombre_estacion"])
    conteo = (viajes.groupby(["anio", "id_estacion_origen"]).size()
              .reset_index(name="cantidad_viajes"))
    # Empates: gana el id de estación menor, para que el ranking sea determinístico
    conteo = conteo.sort_values(["anio", "cantidad_viajes", "id_estacion_origen"],
                                ascending=[True, False, True])
    conteo["ranking"] = conteo.groupby("anio").cumcount() + 1
    top = conteo[conteo["ranking"] <= 10].merge(
        estaciones, left_on="id_estacion_origen", right_on="id_estacion", how="left")
    return top[["anio", "ranking", "nombre_estacion", "cantidad_viajes"]]


def reporte_duracion_rango_genero(viajes: pd.DataFrame) -> pd.DataFrame:
    """Solo viajes cuyo usuario está en dim_usuario (inner join)."""
    usuarios = leer_gold("dim_usuario", ["id_usuario", "rango_etario", "genero"])
    con_usuario = viajes.merge(usuarios, on="id_usuario", how="inner", validate="many_to_one")
    rep = (con_usuario.groupby(["rango_etario", "genero"])
           .agg(cantidad_viajes=("duracion_min", "size"),
                duracion_promedio_min=("duracion_min", "mean"))
           .reset_index())
    rep["duracion_promedio_min"] = rep["duracion_promedio_min"].astype(float).round(1)
    return rep.sort_values(["rango_etario", "genero"])


def reporte_viajes_circulares(viajes: pd.DataFrame) -> pd.DataFrame:
    rep = (viajes.groupby("anio")
           .agg(total_viajes=("es_circular", "size"),
                viajes_circulares=("es_circular", "sum"))
           .reset_index())
    rep["porcentaje_circulares"] = (100 * rep["viajes_circulares"] / rep["total_viajes"]).round(1)
    return rep


def reporte_calidad_por_anio() -> pd.DataFrame:
    """Excepción del enunciado: conteos de bronze, silver y cuarentena por año."""
    filas_bronze = {
        int(carpeta.name.split("=")[1]): pq.ParquetFile(carpeta / "data.parquet").metadata.num_rows
        for carpeta in sorted((DIR_BRONZE / "recorridos").glob("anio=*"))
    }
    silver = pd.read_parquet(DIR_SILVER / "viajes" / "data.parquet", columns=["anio_fuente"])
    cuar = pd.read_parquet(DIR_SILVER / "viajes_cuarentena" / "data.parquet",
                           columns=["anio_fuente"])
    rep = pd.DataFrame({"anio": sorted(filas_bronze)})
    rep["filas_bronze"] = rep["anio"].map(filas_bronze)
    rep["filas_silver"] = rep["anio"].map(silver["anio_fuente"].value_counts()).fillna(0).astype(int)
    rep["filas_cuarentena"] = rep["anio"].map(cuar["anio_fuente"].value_counts()).fillna(0).astype(int)
    rep["porcentaje_cuarentena"] = (100 * rep["filas_cuarentena"] / rep["filas_bronze"]).round(2)
    return rep


# ---------------------------------------------------------------------------
# Orquestación y verificación
# ---------------------------------------------------------------------------
def verificar_reportes(viajes, r1, r2, r3, r4, r5) -> None:
    """Controles cruzados entre reportes. Falla si algo no cierra."""
    total = len(viajes)
    por_anio = {int(a): int(n) for a, n in viajes.groupby("anio").size().items()}
    por_anio_r1 = {int(a): int(n) for a, n in r1.groupby("anio")["cantidad_viajes"].sum().items()}
    con_usuario = int(viajes["id_usuario"].isin(
        leer_gold("dim_usuario", ["id_usuario"])["id_usuario"]).sum())
    controles = {
        "R1: suma de viajes = filas de fact_viajes": r1["cantidad_viajes"].sum() == total,
        "R2: 10 estaciones por año, sin nombres nulos":
            (r2.groupby("anio").size() == 10).all() and r2["nombre_estacion"].notna().all(),
        "R3: suma de viajes = viajes con usuario en dim_usuario":
            r3["cantidad_viajes"].sum() == con_usuario,
        "R4: total por año = R1 por año":
            dict(zip(r4["anio"].astype(int), r4["total_viajes"].astype(int))) == por_anio_r1,
        "R5: bronze = silver + cuarentena":
            (r5["filas_bronze"] == r5["filas_silver"] + r5["filas_cuarentena"]).all(),
        "R5: silver por año = fact_viajes por año":
            dict(zip(r5["anio"].astype(int), r5["filas_silver"].astype(int))) == por_anio,
    }
    for nombre, ok in controles.items():
        print(f"  {nombre}: {'OK' if ok else 'FALLA'}")
    if not all(controles.values()):
        raise AssertionError("Hay controles de reportes que no cierran")
    print(f"  (R3 excluye {total - con_usuario:,} viajes sin usuario en dim_usuario)")


def ejecutar_reportes() -> None:
    viajes = viajes_con_fecha()
    r1 = reporte_viajes_por_mes(viajes)
    r2 = reporte_top10_estaciones(viajes)
    r3 = reporte_duracion_rango_genero(viajes)
    r4 = reporte_viajes_circulares(viajes)
    r5 = reporte_calidad_por_anio()

    guardar_csv(r1, "viajes_por_mes.csv")
    guardar_csv(r2, "top10_estaciones_por_anio.csv")
    guardar_csv(r3, "duracion_por_rango_y_genero.csv")
    guardar_csv(r4, "viajes_circulares.csv")
    guardar_csv(r5, "calidad_por_anio.csv")

    verificar_reportes(viajes, r1, r2, r3, r4, r5)
