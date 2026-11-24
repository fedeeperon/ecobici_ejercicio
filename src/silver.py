"""Capa Silver: esquema canónico único, tipos correctos y controles de calidad.

Lee solo de data/bronze/ y escribe en data/silver/:
- viajes/             un registro por viaje válido
- viajes_cuarentena/  viajes que fallan una regla de calidad, con su motivo
- usuarios/           un registro por usuario
- usuarios_cuarentena/ usuarios descartados (id nulo o duplicado), con su motivo
"""

import os
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
DIR_BRONZE = RAIZ / "data" / "bronze"
DIR_SILVER = RAIZ / "data" / "silver"

ANIOS = [2016, 2019, 2024]

# ---------------------------------------------------------------------------
# Esquemas canónicos (enunciado, Tarea 3 paso 1)
# ---------------------------------------------------------------------------
ESQUEMA_VIAJES = {
    "id_viaje": "string",
    "fecha_hora_inicio": "datetime64[ns]",
    "fecha_hora_fin": "datetime64[ns]",
    "duracion_seg": "Int64",
    "id_estacion_origen": "Int64",
    "nombre_estacion_origen": "string",
    "id_estacion_destino": "Int64",
    "nombre_estacion_destino": "string",
    "id_usuario": "string",
    "anio_fuente": "Int64",
}
ESQUEMA_VIAJES_CUARENTENA = {**ESQUEMA_VIAJES, "motivo": "string"}

ESQUEMA_USUARIOS = {
    "id_usuario": "string",
    "genero": "string",
    "edad": "Int64",
    "fecha_alta": "datetime64[ns]",
    "anio_fuente": "Int64",
}
ESQUEMA_USUARIOS_CUARENTENA = {**ESQUEMA_USUARIOS, "motivo": "string"}

# ---------------------------------------------------------------------------
# Mapeos de columnas por año (paso 2). Lo que cambia entre años está acá.
# Si un año no trae una columna canónica, no figura y se calcula después.
# ---------------------------------------------------------------------------
MAPEO_VIAJES = {
    2016: {
        # sin id de viaje: se genera (ver generar_id_viaje)
        "fecha_origen_recorrido": "fecha_hora_inicio",
        "fecha_destino_recorrido": "fecha_hora_fin",
        # duracion_recorrido no se usa: no coincide con fin - inicio (DECISIONES.md)
        "id_estacion_origen": "id_estacion_origen",
        "nombre_estacion_origen": "nombre_estacion_origen",
        "id_estacion_destino": "id_estacion_destino",
        "nombre_estacion_destino": "nombre_estacion_destino",
        # sin id de usuario: queda nulo
    },
    2019: {
        "Id_recorrido": "id_viaje",
        "fecha_origen_recorrido": "fecha_hora_inicio",
        "fecha_destino_recorrido": "fecha_hora_fin",
        "duracion_recorrido": "duracion_seg",
        "id_estacion_origen": "id_estacion_origen",
        "nombre_estacion_origen": "nombre_estacion_origen",
        "id_estacion_destino": "id_estacion_destino",
        "nombre_estacion_destino": "nombre_estacion_destino",
        "id_usuario": "id_usuario",
    },
    2024: {
        "id_recorrido": "id_viaje",
        "fecha_origen_recorrido": "fecha_hora_inicio",
        "fecha_destino_recorrido": "fecha_hora_fin",
        "duracion_recorrido": "duracion_seg",
        "id_estacion_origen": "id_estacion_origen",
        "nombre_estacion_origen": "nombre_estacion_origen",
        "id_estacion_destino": "id_estacion_destino",
        "nombre_estacion_destino": "nombre_estacion_destino",
        "id_usuario": "id_usuario",
    },
}

FORMATO_FECHA_VIAJES = {
    2016: "%Y-%m-%d %H:%M:%S",
    2019: "%Y-%m-%d %H:%M:%S",
    2024: "%Y-%m-%d %H:%M:%S",
}

MAPEO_USUARIOS = {
    2016: {"id_usuario": "id_usuario", "genero_usuario": "genero",
           "edad_usuario": "edad", "fecha_alta": "fecha_alta", "hora_alta": "hora_alta"},
    2019: {"ID_usuario": "id_usuario", "genero_usuario": "genero",
           "edad_usuario": "edad", "fecha_alta": "fecha_alta", "hora_alta": "hora_alta"},
    2024: {"id_usuario": "id_usuario", "genero_usuario": "genero",
           "edad_usuario": "edad", "fecha_alta": "fecha_alta", "hora_alta": "hora_alta"},
}

# fecha_alta y hora_alta vienen en columnas separadas y se unen con un espacio
FORMATO_FECHA_ALTA = {
    2016: "%d-%m-%y %I:%M:%S %p",   # 27-10-16 3:45:19 AM
    2019: "%Y-%m-%d %H:%M:%S",
    2024: "%Y-%m-%d %H:%M:%S",
}

# Valores de género vistos con value_counts() (DECISIONES.md). Se comparan en
# mayúsculas y sin espacios; cualquier otro valor o nulo -> DESCONOCIDO.
MAPEO_GENERO = {
    "F": "F", "FEMALE": "F", "FEMENINO": "F",
    "M": "M", "MALE": "M", "MASCULINO": "M",
    "OTHER": "OTRO", "OTRO": "OTRO", "X": "OTRO",
}

EDAD_MIN, EDAD_MAX = 16, 90
DURACION_MAX_SEG = 86_400


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def leer_bronze(tipo: str, anio: int, columnas: list[str]) -> pd.DataFrame:
    return pd.read_parquet(
        DIR_BRONZE / tipo / f"anio={anio}" / "data.parquet", columns=columnas
    )


def renombrar(df: pd.DataFrame, mapeo: dict) -> pd.DataFrame:
    df = df.rename(columns=mapeo)
    return df[list(mapeo.values())].copy()  # descarta lo que no está en el mapeo


def a_entero(serie: pd.Series) -> pd.Series:
    """Texto -> Int64. Lo que no es número entero queda nulo."""
    num = pd.to_numeric(serie, errors="coerce")
    entero = num.notna() & (num % 1 == 0)
    return num.where(entero).astype("Int64")


def quitar_sufijo(serie: pd.Series, patron: str) -> pd.Series:
    return serie.str.replace(patron, "", regex=True)


def normalizar_estacion(serie: pd.Series) -> pd.Series:
    """Quita el número inicial ('005 - '), espacios de las puntas y repetidos; mayúsculas."""
    return (
        serie.str.replace(r"^\s*\d+\s*-\s*", "", regex=True)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
        .astype("string")
    )


def normalizar_genero(serie: pd.Series) -> pd.Series:
    return (
        serie.str.strip().str.upper().map(MAPEO_GENERO)
        .fillna("DESCONOCIDO").astype("string")
    )


def generar_id_viaje(anio: int, n: int) -> pd.Series:
    """Id sintético por posición en bronze: '2016-000001', ... (DECISIONES.md)."""
    ancho = len(str(n))
    return pd.Series([f"{anio}-{i:0{ancho}d}" for i in range(1, n + 1)], dtype="string")


def validar_esquema(df: pd.DataFrame, esquema: dict) -> None:
    """Falla si las columnas (y su orden) o los tipos no son exactamente los del esquema."""
    if list(df.columns) != list(esquema):
        raise ValueError(f"Columnas distintas al esquema.\n  tiene: {list(df.columns)}"
                         f"\n  espera: {list(esquema)}")
    distintos = {c: str(df[c].dtype) for c, t in esquema.items() if str(df[c].dtype) != t}
    if distintos:
        raise TypeError(f"Tipos distintos al esquema: {distintos}")


def guardar(df: pd.DataFrame, nombre: str, esquema: dict) -> None:
    """Valida y escribe data/silver/<nombre>/data.parquet, reemplazando el anterior."""
    validar_esquema(df, esquema)
    carpeta = DIR_SILVER / nombre
    carpeta.mkdir(parents=True, exist_ok=True)
    temporal = carpeta / "data.parquet.tmp"
    df.to_parquet(temporal, index=False)
    os.replace(temporal, carpeta / "data.parquet")


# ---------------------------------------------------------------------------
# Viajes
# ---------------------------------------------------------------------------
def transformar_viajes(anio: int) -> pd.DataFrame:
    """Bronze de un año -> esquema canónico (pasos 2 a 4), sin filtrar nada."""
    mapeo = MAPEO_VIAJES[anio]
    df = renombrar(leer_bronze("recorridos", anio, list(mapeo)), mapeo)

    # id_viaje
    if "id_viaje" in df:
        df["id_viaje"] = quitar_sufijo(df["id_viaje"], r"BAEcobici$").str.strip()
    else:
        df["id_viaje"] = generar_id_viaje(anio, len(df)).values

    # fechas
    for col in ("fecha_hora_inicio", "fecha_hora_fin"):
        df[col] = pd.to_datetime(df[col], format=FORMATO_FECHA_VIAJES[anio], errors="coerce")

    # duración: en segundos si viene (2019 trae coma de miles: "2,814"); si no, fin - inicio
    if "duracion_seg" in df:
        df["duracion_seg"] = a_entero(df["duracion_seg"].str.replace(",", "", regex=False))
    else:
        seg = (df["fecha_hora_fin"] - df["fecha_hora_inicio"]).dt.total_seconds()
        df["duracion_seg"] = seg.round().astype("Int64")

    # estaciones
    for extremo in ("origen", "destino"):
        df[f"id_estacion_{extremo}"] = a_entero(
            quitar_sufijo(df[f"id_estacion_{extremo}"], r"BAEcobici$")
        )
        df[f"nombre_estacion_{extremo}"] = normalizar_estacion(df[f"nombre_estacion_{extremo}"])

    # usuario: 2019 trae "6243BAEcobici", 2024 trae "992557.0"
    if "id_usuario" in df:
        df["id_usuario"] = quitar_sufijo(df["id_usuario"], r"(BAEcobici|\.0)$").str.strip()
    else:
        df["id_usuario"] = pd.NA

    df["anio_fuente"] = anio
    df = df[list(ESQUEMA_VIAJES)]
    return df.astype({"id_viaje": "string", "id_usuario": "string", "anio_fuente": "Int64"})


def aplicar_calidad(df: pd.DataFrame):
    """Devuelve (validos, cuarentena). Cada fila guarda solo el primer motivo que falla."""
    motivo = pd.Series(pd.NA, index=df.index, dtype="string")
    reglas = [
        ("FECHA_INVALIDA",
         df["fecha_hora_inicio"].isna() | df["fecha_hora_fin"].isna()),
        ("ESTACION_NULA",
         df["id_estacion_origen"].isna() | df["id_estacion_destino"].isna()),
        ("FIN_ANTERIOR_A_INICIO",
         df["fecha_hora_fin"] < df["fecha_hora_inicio"]),
        ("DURACION_MAYOR_24H",
         (df["duracion_seg"] > DURACION_MAX_SEG).fillna(False)),
        ("DUPLICADO",
         df["id_viaje"].duplicated(keep="first")),
    ]
    for nombre, condicion in reglas:
        motivo = motivo.mask(motivo.isna() & condicion, nombre)

    validos = df[motivo.isna()].reset_index(drop=True)
    cuarentena = (df[motivo.notna()].assign(motivo=motivo[motivo.notna()])
                  .reset_index(drop=True))
    return validos, cuarentena


# ---------------------------------------------------------------------------
# Usuarios
# ---------------------------------------------------------------------------
def transformar_usuarios(anio: int) -> pd.DataFrame:
    mapeo = MAPEO_USUARIOS[anio]
    df = renombrar(leer_bronze("usuarios", anio, list(mapeo)), mapeo)

    df["id_usuario"] = df["id_usuario"].str.strip().astype("string")
    df["genero"] = normalizar_genero(df["genero"])

    # edad fuera de [16, 90] -> nulo (no se rechaza la fila)
    edad = a_entero(df["edad"])
    df["edad"] = edad.mask((edad < EDAD_MIN) | (edad > EDAD_MAX))

    texto = df["fecha_alta"].str.strip() + " " + df["hora_alta"].str.strip()
    df["fecha_alta"] = pd.to_datetime(texto, format=FORMATO_FECHA_ALTA[anio], errors="coerce")

    df["anio_fuente"] = anio
    df = df[list(ESQUEMA_USUARIOS)]
    return df.astype({"anio_fuente": "Int64"})


def calidad_usuarios(df: pd.DataFrame):
    """id no nulo y sin duplicados: ante repetidos queda el de fecha_alta más reciente."""
    motivo = pd.Series(pd.NA, index=df.index, dtype="string")
    motivo = motivo.mask(df["id_usuario"].isna(), "ID_NULO")

    # Orden: fecha_alta más reciente primero (NaT al final); empate -> año más reciente
    orden = df.sort_values(["fecha_alta", "anio_fuente"], ascending=False,
                           na_position="last", kind="stable")
    repetido = orden["id_usuario"].duplicated(keep="first") & orden["id_usuario"].notna()
    motivo = motivo.mask(motivo.isna() & repetido.reindex(df.index), "DUPLICADO")

    validos = df[motivo.isna()].reset_index(drop=True)
    cuarentena = (df[motivo.notna()].assign(motivo=motivo[motivo.notna()])
                  .reset_index(drop=True))
    return validos, cuarentena


# ---------------------------------------------------------------------------
# Orquestación y verificación
# ---------------------------------------------------------------------------
def contar_bronze(tipo: str) -> dict:
    import pyarrow.parquet as pq
    return {a: pq.ParquetFile(DIR_BRONZE / tipo / f"anio={a}" / "data.parquet").metadata.num_rows
            for a in ANIOS}


def verificar_silver(viajes, cuarentena, usuarios, usuarios_cuar) -> None:
    """Paso 6: conciliación por año, id_viaje único y esquema. Falla si algo no cierra."""
    for tipo, ok, mal in (("recorridos", viajes, cuarentena),
                          ("usuarios", usuarios, usuarios_cuar)):
        bronze = contar_bronze(tipo)
        n_ok = ok["anio_fuente"].value_counts()
        n_mal = mal["anio_fuente"].value_counts()
        for a in ANIOS:
            s, c = int(n_ok.get(a, 0)), int(n_mal.get(a, 0))
            estado = "OK" if bronze[a] == s + c else "NO CIERRA"
            print(f"  {tipo} {a}: bronze {bronze[a]:>10,} = silver {s:>10,}"
                  f" + cuarentena {c:>8,}  {estado}")
            if estado != "OK":
                raise AssertionError(f"Conciliación de {tipo} {a} no cierra")
    if not viajes["id_viaje"].is_unique:
        raise AssertionError("id_viaje no es único en silver/viajes")
    if not usuarios["id_usuario"].is_unique:
        raise AssertionError("id_usuario no es único en silver/usuarios")
    validar_esquema(viajes, ESQUEMA_VIAJES)
    validar_esquema(cuarentena, ESQUEMA_VIAJES_CUARENTENA)
    validar_esquema(usuarios, ESQUEMA_USUARIOS)
    validar_esquema(usuarios_cuar, ESQUEMA_USUARIOS_CUARENTENA)
    print("  id_viaje único, id_usuario único y esquemas: OK")


def ejecutar_silver() -> None:
    viajes = pd.concat([transformar_viajes(a) for a in ANIOS], ignore_index=True)
    viajes_ok, viajes_cuar = aplicar_calidad(viajes)
    del viajes

    usuarios = pd.concat([transformar_usuarios(a) for a in ANIOS], ignore_index=True)
    usuarios_ok, usuarios_cuar = calidad_usuarios(usuarios)

    guardar(viajes_ok, "viajes", ESQUEMA_VIAJES)
    guardar(viajes_cuar, "viajes_cuarentena", ESQUEMA_VIAJES_CUARENTENA)
    guardar(usuarios_ok, "usuarios", ESQUEMA_USUARIOS)
    guardar(usuarios_cuar, "usuarios_cuarentena", ESQUEMA_USUARIOS_CUARENTENA)

    print("  Cuarentena de viajes por motivo:")
    tabla = viajes_cuar.groupby(["anio_fuente", "motivo"]).size()
    for (a, m), n in tabla.items():
        print(f"    {a} {m:<24}{n:>8,}")
    print("  Cuarentena de usuarios por motivo:",
          usuarios_cuar.groupby(["anio_fuente", "motivo"]).size().to_dict())

    verificar_silver(viajes_ok, viajes_cuar, usuarios_ok, usuarios_cuar)
