# DECISIONES

Registro de las diferencias encontradas entre los archivos de origen y de toda decisión
tomada que no esté indicada en el enunciado.

## Mapeo de archivos de origen

Los nombres de archivo no siguen un patrón común, así que el año y el tipo de cada archivo
se definen con un mapeo explícito en el código (no se deducen del nombre).

| Archivo en `data/raw/`             | Año  | Tipo       |
|------------------------------------|------|------------|
| `recorridos-realizados-2016.zip`   | 2016 | recorridos |
| `recorridos-realizados-2019.zip`   | 2019 | recorridos |
| `recorridos-realizados-2024.zip`   | 2024 | recorridos |
| `usuarios-ecobici-2016.csv`        | 2016 | usuarios   |
| `usuarios_ecobici_2019.csv`        | 2019 | usuarios   |
| `usuarios_ecobici_2024.csv`        | 2024 | usuarios   |

Justificación: un mapeo explícito evita errores si un archivo cambia de nombre y deja
documentado qué se procesa.

## Tarea 1: diferencias entre años

Exploración hecha con `pd.read_csv(..., nrows=1000, dtype=str)`. El total de filas se contó
leyendo cada archivo completo por partes (`chunksize`). Como los formatos de las primeras 1000
filas podían no representar al resto, también se revisaron en el archivo completo.

### Recorridos

| Aspecto a revisar | 2016 | 2019 | 2024 |
|---|---|---|---|
| Nombre del archivo dentro del ZIP | `recorridos-realizados-2016.csv` (único archivo) | `trips_2019.csv` (único archivo) | `badata_ecobici_recorridos_realizados_2024.csv` (único archivo) |
| Separador de columnas | `,` | `,` (todos los campos entre comillas `"`) | `,` |
| Codificación | UTF-8 | UTF-8 | UTF-8 **con BOM** (se lee con `encoding="utf-8-sig"`) |
| Nombres de las columnas (15 / 18 / 17) | `periodo, genero_usuario, fecha_origen_recorrido, id_estacion_origen, nombre_estacion_origen, long_estacion_origen, lat_estacion_origen, domicilio_estacion_origen, duracion_recorrido, fecha_destino_recorrido, id_estacion_destino, nombre_estacion_destino, long_estacion_destino, lat_estacion_destino, domicilio_estacion_destino` | `""` (índice sin nombre, pandas lo lee como `Unnamed: 0`), `Id_recorrido, duracion_recorrido, fecha_origen_recorrido, id_estacion_origen, nombre_estacion_origen, direccion_estacion_origen, long_estacion_origen, lat_estacion_origen, fecha_destino_recorrido, id_estacion_destino, nombre_estacion_destino, direccion_estacion_destino, long_estacion_destino, lat_estacion_destino, id_usuario, modelo_bicicleta, género` | `id_recorrido, duracion_recorrido, fecha_origen_recorrido, id_estacion_origen, nombre_estacion_origen, direccion_estacion_origen, long_estacion_origen, lat_estacion_origen, fecha_destino_recorrido, id_estacion_destino, nombre_estacion_destino, direccion_estacion_destino, long_estacion_destino, lat_estacion_destino, id_usuario, modelo_bicicleta, genero` |
| Formato de fecha y hora | `AAAA-MM-DD HH:MM:SS` | `AAAA-MM-DD HH:MM:SS` | `AAAA-MM-DD HH:MM:SS` |
| ¿Trae la duración? ¿En qué unidad? | Sí, como texto de timedelta (`0 days 00:16:29.000000000`). **No coincide con fin − inicio** en el 99,9 % de los casos comparables | Sí, en segundos, con coma como separador de miles (`2,814` = 2814 s). Coincide con fin − inicio en el 100 % de los casos | Sí, en segundos enteros (`568`). Coincide con fin − inicio salvo en 8 filas |
| ¿Trae id de usuario? | **No** (solo `genero_usuario`) | Sí, con sufijo de texto: `6243BAEcobici` | Sí, como número con decimal: `992557.0` |
| ¿Trae id de viaje? | **No** | Sí, con sufijo: `9379BAEcobici` (`Id_recorrido`, con mayúscula) | Sí, numérico de 8 dígitos (`id_recorrido`) |
| Formato de id de estación | Numérico (`11`) | Con sufijo: `5BAEcobici` | Numérico (`513`) |
| Formato de nombre de estación | Sin número (`Tribunales`) | Con número adelante: `005 - Plaza Italia` | Con número adelante: `308 - SAN MARTIN II`; mezcla de mayúsculas y minúsculas |
| Rango de fechas de inicio | 2016-01-01 → 2016-12-31 | **2019-02-09** → 2019-12-31 (no hay viajes de enero ni de principios de febrero) | 2024-01-01 → 2024-12-31 |
| Nulos relevantes | `fecha_destino_recorrido`: 93.555 | Estación destino (id, nombre, etc.): 1.760; `género`: 93.571 | `fecha_destino_recorrido`: 3.379; `genero`: 11.946 |
| Ids de viaje repetidos dentro del año | No aplica (no hay id) | 0 | 1 |
| Cantidad total de filas | **596.807** | **6.217.004** | **3.559.284** |

Otras observaciones de recorridos:

- **2019, coordenadas corridas:** en `long_estacion_destino` viene la latitud y en
  `lat_estacion_destino` viene el par `"lat,long"`. No afecta al esquema canónico, que no usa
  coordenadas.
- **2019, columna de género con tilde:** se llama `género` (en 2024 es `genero`, sin tilde).
- **Acentos:** los tres archivos son UTF-8 válido y los acentos están bien (`Sánchez de Loria`,
  `Peña`). *Corrección hecha en la Tarea 2:* una versión anterior de esta tabla decía que había
  caracteres `�` en los datos; era un problema de la consola de Windows al mostrarlos. Al
  revisar bronze no apareció ningún `�` en ninguna columna de los 6 archivos.
- **2016, columna `periodo`:** siempre vale `2016`.
- Ningún ZIP contiene más de un archivo, así que no hubo que elegir.
- En los tres archivos, la cantidad de filas de pandas es igual a la de líneas físicas menos el
  encabezado: no hay saltos de línea dentro de los campos.

### Usuarios

| Aspecto a revisar | 2016 | 2019 | 2024 |
|---|---|---|---|
| Archivo | `usuarios-ecobici-2016.csv` | `usuarios_ecobici_2019.csv` | `usuarios_ecobici_2024.csv` |
| Separador de columnas | `,` | `,` (campos de texto entre comillas) | `,` |
| Codificación | UTF-8 | UTF-8 | UTF-8 **con BOM** |
| Nombres de las columnas | `id_usuario, genero_usuario, edad_usuario, fecha_alta, hora_alta` | `ID_usuario` (mayúsculas), `genero_usuario, edad_usuario, fecha_alta, hora_alta` | `id_usuario, genero_usuario, edad_usuario, fecha_alta, hora_alta` |
| Formato de fecha | `DD-MM-AA` (`27-10-16`) | `AAAA-MM-DD` | `AAAA-MM-DD` |
| Formato de hora | 12 horas con AM/PM, sin cero adelante (`3:45:19 AM`) | 24 horas `HH:MM:SS` | 24 horas `HH:MM:SS` |
| Fecha y hora | En dos columnas separadas (`fecha_alta` + `hora_alta`) | Ídem | Ídem |
| Formato de id de usuario | Numérico (`223858`) | Numérico (`627966`), **sin** el sufijo `BAEcobici` de los recorridos | Numérico (`1094487`), **sin** el `.0` de los recorridos |
| Valores de género (`value_counts`) | `M`: 21.697, `F`: 17.784 | `MALE`: 41.107, `FEMALE`: 24.285, `OTHER`: 17.351, nulo: 857 | `MALE`: 88.655, `FEMALE`: 79.310, `OTHER`: 29.112 |
| Edad | 16 a 88, sin nulos | 0 a 935; 765 nulos; 31 menores de 16 y 15 mayores de 90 | 4 a 2021; sin nulos; 9 menores de 16 y 85 mayores de 90 |
| Ids nulos / duplicados | 0 / 0 | 0 / 0 | 0 / 0 |
| Cantidad total de filas | **39.481** | **83.600** | **197.077** |

## Tarea 2: capa Bronze

- **Entorno:** pandas fijado en `2.2.3` (no 3.x), porque pandas 3 cambia el tipo de texto
  por defecto y la resolución de las fechas, y el enunciado espera `string` y
  `datetime64[ns]`. Se usa un entorno virtual `.venv` para no tocar el Python del sistema
  (allí pyarrow 26 no funcionaba con NumPy 1.26).
- **Codificación `utf-8-sig` para todos los archivos:** quita el BOM de los de 2024 (si no,
  la primera columna se llamaría `﻿id_recorrido`) y no cambia nada en los que no lo tienen.
  El BOM es un detalle de la codificación, no parte del nombre de la columna.
- **Solo el campo vacío se lee como nulo** (`keep_default_na=False, na_values=[""]`): por
  defecto pandas también convierte en nulo textos como `NA` o `null`, y eso ya sería
  limpieza. Hay dos columnas con la palabra `NA` escrita, que bronze conserva como texto:
  `edad_usuario` de usuarios 2019 (765 filas) y `long_estacion_destino` de recorridos 2019
  (1.760, las mismas filas sin estación destino). Silver las va a pasar a nulo.
- **Columna `Unnamed: 0` en recorridos 2019:** el encabezado original de esa columna está
  vacío (`""`) y pandas le pone ese nombre al leerla. Se deja así en bronze.
- **Lectura y escritura por partes** (`chunksize=500_000` + `pyarrow.ParquetWriter`): evita
  cargar los 6,2 millones de filas de 2019 en memoria de una vez. Todas las columnas se
  guardan con tipo `string` de Arrow.
- **Idempotencia:** cada año se escribe en un `data.parquet.tmp` que al terminar reemplaza
  al `data.parquet` (`os.replace`). Cada corrida sobrescribe todo y nunca queda un archivo a
  medio escribir.
- **`_fecha_ingesta`:** una sola marca de tiempo por corrida (ISO, en segundos), la misma
  para los 6 archivos, para que identifique una ingesta completa.
- **ZIP con más de un archivo:** `elegir_csv_del_zip` exige que haya un único CSV y, si no,
  corta con un error que muestra el contenido. Hoy los tres ZIP tienen un solo archivo.

## Tarea 3: capa Silver

### Mapeo de columnas de viajes (`MAPEO_VIAJES` en `src/silver.py`)

| Columna canónica | 2016 | 2019 | 2024 |
|---|---|---|---|
| `id_viaje` | *(no viene: se genera)* | `Id_recorrido` (sin `BAEcobici`) | `id_recorrido` |
| `fecha_hora_inicio` | `fecha_origen_recorrido` | `fecha_origen_recorrido` | `fecha_origen_recorrido` |
| `fecha_hora_fin` | `fecha_destino_recorrido` | `fecha_destino_recorrido` | `fecha_destino_recorrido` |
| `duracion_seg` | *(se calcula: fin − inicio)* | `duracion_recorrido` (sin la coma de miles) | `duracion_recorrido` |
| `id_estacion_origen` | `id_estacion_origen` | `id_estacion_origen` (sin `BAEcobici`) | `id_estacion_origen` |
| `nombre_estacion_origen` | `nombre_estacion_origen` | `nombre_estacion_origen` | `nombre_estacion_origen` |
| `id_estacion_destino` | `id_estacion_destino` | `id_estacion_destino` (sin `BAEcobici`) | `id_estacion_destino` |
| `nombre_estacion_destino` | `nombre_estacion_destino` | `nombre_estacion_destino` | `nombre_estacion_destino` |
| `id_usuario` | *(no viene: nulo)* | `id_usuario` (sin `BAEcobici`) | `id_usuario` (sin `.0`) |
| `anio_fuente` | 2016 | 2019 | 2024 |

Formato de fecha de los tres años: `%Y-%m-%d %H:%M:%S`.

### Mapeo de columnas de usuarios (`MAPEO_USUARIOS`)

| Columna canónica | 2016 | 2019 | 2024 |
|---|---|---|---|
| `id_usuario` | `id_usuario` | `ID_usuario` | `id_usuario` |
| `genero` | `genero_usuario` | `genero_usuario` | `genero_usuario` |
| `edad` | `edad_usuario` | `edad_usuario` | `edad_usuario` |
| `fecha_alta` | `fecha_alta` + `hora_alta`, formato `%d-%m-%y %I:%M:%S %p` | `fecha_alta` + `hora_alta`, `%Y-%m-%d %H:%M:%S` | ídem 2019 |

### Mapeo de género (`MAPEO_GENERO`)

Los valores se comparan en mayúsculas y sin espacios en las puntas.

| Valor original | Silver | Visto en |
|---|---|---|
| `F`, `FEMALE` (y `FEMENINO`, por las dudas) | `F` | 2016 (`F`), 2019 y 2024 (`FEMALE`) |
| `M`, `MALE` (y `MASCULINO`) | `M` | 2016 (`M`), 2019 y 2024 (`MALE`) |
| `OTHER` (y `OTRO`, `X`) | `OTRO` | 2019, 2024 |
| nulo o cualquier otro valor | `DESCONOCIDO` | 2019 (857 nulos) |

### Decisiones

- **`id_viaje` de 2016 sintético:** `2016-000001`, `2016-000002`, …, según la posición de la
  fila en bronze. 2016 no trae id. Es determinístico (idempotente) y no puede chocar con los
  ids numéricos de 2019 (10 a 6.875.895) ni de 2024 (20.180.969 a 24.503.283), que tampoco se
  pisan entre sí. 2016 no tiene filas idénticas repetidas, así que no se pierde ningún
  duplicado real.
- **`id_usuario` de 2016 nulo:** el archivo no lo trae, y el esquema lo permite.
- **`duracion_seg` de 2016 calculada como fin − inicio:** la duración informada siempre es
  menor que la diferencia de fechas, por una cantidad variable (mediana 1.557 s contra
  1.876 s), y no está documentado qué mide. En 2019 coincide con fin − inicio en el 100 % de
  los casos y en 2024 en todos salvo 8 filas, así que ahí se usa la informada.
- **Sufijos de los ids:** se quita `BAEcobici` (2019) y `.0` (ids de usuario de 2024) para
  que los ids sean numéricos y crucen con la tabla de usuarios, que no tiene esos sufijos.
- **Prefijo numérico en nombres de estación:** además de la normalización de la consigna, se
  quita el número inicial (`005 - Plaza Italia` → `PLAZA ITALIA`). 2016 no lo tiene y no
  coincide con el id de estación (solo en el 38 % de los casos en 2019 y el 31 % en 2024).
  Algunas estaciones de 2019 se llaman solo con un número en el origen (`175`, `234`,
  `359 PB`): no tienen guion y quedan así.
- **Acentos:** se conservan (`ZOOLÓGICO`). La consigna no pide quitarlos.
- **Textos `NA` de bronze:** pasan a nulo al convertir a número (`errors="coerce"`).
- **Edades fuera de 16–90 → nulo** (lo pide la consigna): 46 en 2019 y 94 en 2024. Con las
  765 `NA` de 2019, quedan 811 edades nulas en 2019 y 94 en 2024.
- **Regla DUPLICADO:** se aplica a todo el conjunto, en el orden 2016 → 2019 → 2024 y en el
  orden de las filas en bronze. La primera aparición queda en silver y las siguientes van a
  cuarentena. El único caso (2024, id `22425357`) son dos filas idénticas en todas las
  columnas.
- **Usuarios descartados a `silver/usuarios_cuarentena`** (con `motivo` `ID_NULO` o
  `DUPLICADO`): la consigna pide quedarse con uno solo, pero así el registro descartado no se
  pierde y los usuarios también concilian con bronze. Si hay empate de `fecha_alta`, queda
  el del año más reciente.
- **Los 5.231 usuarios repetidos entre 2016 y 2019 son personas distintas:** el género
  coincide solo en el 39 % y las edades no son coherentes, así que la fuente reutilizó ids.
  Se aplica igual la regla de la consigna y queda el de 2019, que es el más reciente. Es el
  que corresponde para los cruces, porque los viajes de 2016 no traen id de usuario.
- **Los archivos de usuarios solo traen las altas de ese año** (`fecha_alta` siempre está
  dentro del año del archivo). Por eso solo el 24 % de los viajes de 2019 y el 32 % de los de
  2024 cruzan con un usuario del mismo año. Se va a medir en la Tarea 4.
- **Salida:** `data/silver/<tabla>/data.parquet` para `viajes`, `viajes_cuarentena`,
  `usuarios` y `usuarios_cuarentena`. Se escribe a un archivo temporal y después se reemplaza,
  como en bronze. Se llama a `validar_esquema()` antes de cada escritura.

### Observaciones de los datos (no son decisiones)

- 2016: las 93.555 filas sin `fecha_destino_recorrido` son las últimas del archivo
  (desde la fila 503.253) y van todas a cuarentena por `FECHA_INVALIDA` (15,7 % del año).
- 2016: las duraciones válidas van de 600 s a 10.797 s. Parece que la fuente solo publicó
  viajes de entre 10 minutos y 3 horas.
- 2019: el primer viaje (09/02) duró 10 días y va a cuarentena, así que los viajes válidos
  empiezan el 17/02.
