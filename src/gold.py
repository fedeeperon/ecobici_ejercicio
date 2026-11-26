"""Capa Gold: modelo estrella a partir de silver.

Lee solo de data/silver/ y escribe en data/gold/<tabla>/data.parquet:
dim_fecha, dim_estacion, dim_usuario y fact_viajes.
Se usan los ids naturales como claves (sin claves sustitutas).
"""

import os
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_SILVER = RAIZ / "data" / "silver"
DIR_GOLD = RAIZ / "data" / "gold"

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# Rangos etarios: (desde, hasta inclusive, etiqueta). Silver ya dejó edades en 16-90.
RANGOS_ETARIOS = [(16, 25, "16-25"), (26, 35, "26-35"), (36, 50, "36-50"), (51, 200, "51+")]


def leer_silver(tabla: str) -> pd.DataFrame:
    return pd.read_parquet(DIR_SILVER / tabla / "data.parquet")


def guardar(df: pd.DataFrame, tabla: str) -> None:
    """Escribe data/gold/<tabla>/data.parquet reemplazando el anterior."""
    carpeta = DIR_GOLD / tabla
    carpeta.mkdir(parents=True, exist_ok=True)
    temporal = carpeta / "data.parquet.tmp"
    df.to_parquet(temporal, index=False)
    os.replace(temporal, carpeta / "data.parquet")


def a_fecha_key(fechas: pd.Series) -> pd.Series:
    """datetime -> entero AAAAMMDD."""
    return (fechas.dt.year * 10_000 + fechas.dt.month * 100 + fechas.dt.day).astype("Int64")


# ---------------------------------------------------------------------------
# Dimensiones
# ---------------------------------------------------------------------------
def construir_dim_fecha(viajes: pd.DataFrame) -> pd.DataFrame:
    """Un día por fila, continuo desde el primer hasta el último día con viajes."""
    inicio = viajes["fecha_hora_inicio"].min().normalize()
    fin = viajes["fecha_hora_inicio"].max().normalize()
    fechas = pd.Series(pd.date_range(inicio, fin, freq="D"))
    return pd.DataFrame({
        "fecha_key": a_fecha_key(fechas),
        "fecha": fechas,
        "anio": fechas.dt.year.astype("Int64"),
        "mes": fechas.dt.month.astype("Int64"),
        "dia": fechas.dt.day.astype("Int64"),
        "dia_semana": fechas.dt.dayofweek.map(dict(enumerate(DIAS_SEMANA))).astype("string"),
        "es_fin_de_semana": fechas.dt.dayofweek >= 5,
    })


def construir_dim_estacion(viajes: pd.DataFrame) -> pd.DataFrame:
    """Una fila por estación (origen y destino). Nombre: el del año más reciente."""
    apariciones = pd.concat([
        viajes[["id_estacion_origen", "nombre_estacion_origen", "anio_fuente"]]
        .set_axis(["id_estacion", "nombre_estacion", "anio"], axis=1),
        viajes[["id_estacion_destino", "nombre_estacion_destino", "anio_fuente"]]
        .set_axis(["id_estacion", "nombre_estacion", "anio"], axis=1),
    ])
    conteo = (apariciones.value_counts(["id_estacion", "anio", "nombre_estacion"])
              .reset_index(name="n"))

    # Año más reciente; si en ese año hay más de un nombre, el más usado (empate: alfabético)
    nombres = (conteo.sort_values(["id_estacion", "anio", "n", "nombre_estacion"],
                                  ascending=[True, False, False, True])
               .drop_duplicates("id_estacion")[["id_estacion", "nombre_estacion"]])
    anios = (conteo.groupby("id_estacion")["anio"].agg(primer_anio="min", ultimo_anio="max")
             .reset_index())

    dim = nombres.merge(anios, on="id_estacion").sort_values("id_estacion")
    return dim.reset_index(drop=True).astype({
        "id_estacion": "Int64", "nombre_estacion": "string",
        "primer_anio": "Int64", "ultimo_anio": "Int64",
    })


def rango_etario(edad: pd.Series) -> pd.Series:
    rango = pd.Series("DESCONOCIDO", index=edad.index, dtype="string")
    for desde, hasta, etiqueta in RANGOS_ETARIOS:
        rango = rango.mask(edad.between(desde, hasta).fillna(False), etiqueta)
    return rango


def construir_dim_usuario(usuarios: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "id_usuario": usuarios["id_usuario"],
        "genero": usuarios["genero"],
        "edad": usuarios["edad"],
        "rango_etario": rango_etario(usuarios["edad"]),
        "anio_alta": usuarios["fecha_alta"].dt.year.astype("Int64"),
    })


# ---------------------------------------------------------------------------
# Hechos
# ---------------------------------------------------------------------------
def construir_fact_viajes(viajes: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "id_viaje": viajes["id_viaje"],
        "fecha_key": a_fecha_key(viajes["fecha_hora_inicio"]),
        "hora_inicio": viajes["fecha_hora_inicio"].dt.hour.astype("Int64"),
        "id_estacion_origen": viajes["id_estacion_origen"],
        "id_estacion_destino": viajes["id_estacion_destino"],
        "id_usuario": viajes["id_usuario"],
        "duracion_min": (viajes["duracion_seg"].astype("Float64") / 60).round(1),
        "es_circular": (viajes["id_estacion_origen"] == viajes["id_estacion_destino"])
                       .astype("bool"),
    })


# ---------------------------------------------------------------------------
# Orquestación y verificación
# ---------------------------------------------------------------------------
def verificar_gold(n_silver, fact, dim_fecha, dim_estacion, dim_usuario) -> dict:
    """Verificaciones de la Tarea 4. Falla si algo no cierra; devuelve los conteos."""
    print(f"  filas fact_viajes {len(fact):,} = silver/viajes {n_silver:,}: "
          f"{'OK' if len(fact) == n_silver else 'NO'}")
    if len(fact) != n_silver:
        raise AssertionError("fact_viajes no tiene las mismas filas que silver/viajes")

    for col, dim, clave in (("fecha_key", dim_fecha, "fecha_key"),
                            ("id_estacion_origen", dim_estacion, "id_estacion"),
                            ("id_estacion_destino", dim_estacion, "id_estacion")):
        huerfanos = int((~fact[col].isin(dim[clave])).sum())
        print(f"  {col} sin match en dimensión: {huerfanos}")
        if huerfanos:
            raise AssertionError(f"{col} tiene {huerfanos} valores sin match")

    for dim, clave in ((dim_fecha, "fecha_key"), (dim_estacion, "id_estacion"),
                       (dim_usuario, "id_usuario")):
        if not dim[clave].is_unique:
            raise AssertionError(f"clave {clave} repetida en su dimensión")

    # Viajes con id_usuario que no está en dim_usuario (no es error; se informa)
    anio = fact["fecha_key"] // 10_000
    con_id = fact["id_usuario"].notna()
    sin_match = con_id & ~fact["id_usuario"].isin(dim_usuario["id_usuario"])
    resumen = pd.DataFrame({
        "viajes": anio.value_counts(),
        "sin_id_usuario": (~con_id).groupby(anio).sum(),
        "id_sin_match": sin_match.groupby(anio).sum(),
    }).sort_index()
    resumen["pct_sin_match"] = (100 * resumen["id_sin_match"] / resumen["viajes"]).round(1)
    print("  Viajes cuyo id_usuario no está en dim_usuario:")
    print("    " + resumen.to_string().replace("\n", "\n    "))
    return resumen


def ejecutar_gold() -> None:
    viajes = leer_silver("viajes")
    usuarios = leer_silver("usuarios")

    dim_fecha = construir_dim_fecha(viajes)
    dim_estacion = construir_dim_estacion(viajes)
    dim_usuario = construir_dim_usuario(usuarios)
    fact = construir_fact_viajes(viajes)

    for nombre, df in (("dim_fecha", dim_fecha), ("dim_estacion", dim_estacion),
                       ("dim_usuario", dim_usuario), ("fact_viajes", fact)):
        guardar(df, nombre)
        print(f"  gold/{nombre}: {len(df):,} filas")

    verificar_gold(len(viajes), fact, dim_fecha, dim_estacion, dim_usuario)
