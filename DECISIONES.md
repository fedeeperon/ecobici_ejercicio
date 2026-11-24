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
| Nombres de las columnas (15 / 18 / 17) | `periodo, genero_usuario, fecha_origen_recorrido, id_estacion_origen, nombre_estacion_origen, long_estacion_origen, lat_estacion_origen, domicilio_estacion_origen, duracion_recorrido, fecha_destino_recorrido, id_estacion_destino, nombre_estacion_destino, long_estacion_destino, lat_estacion_destino, domicilio_estacion_destino` | `""` (índice sin nombre, pandas lo lee como `Unnamed: 0`), `Id_recorrido, duracion_recorrido, fecha_origen_recorrido, id_estacion_origen, nombre_estacion_origen, direccion_estacion_origen, long_estacion_origen, lat_estacion_origen, fecha_destino_recorrido, id_estacion_destino, nombre_estacion_destino, direccion_estacion_destino, long_estacion_destino, lat_estacion_destino, id_usuario, modelo_bicicleta, g�nero` | `id_recorrido, duracion_recorrido, fecha_origen_recorrido, id_estacion_origen, nombre_estacion_origen, direccion_estacion_origen, long_estacion_origen, lat_estacion_origen, fecha_destino_recorrido, id_estacion_destino, nombre_estacion_destino, direccion_estacion_destino, long_estacion_destino, lat_estacion_destino, id_usuario, modelo_bicicleta, genero` |
| Formato de fecha y hora | `AAAA-MM-DD HH:MM:SS` | `AAAA-MM-DD HH:MM:SS` | `AAAA-MM-DD HH:MM:SS` |
| ¿Trae la duración? ¿En qué unidad? | Sí, como texto de timedelta (`0 days 00:16:29.000000000`). **No coincide con fin − inicio** en el 99,9 % de los casos comparables | Sí, en segundos, con coma como separador de miles (`2,814` = 2814 s). Coincide con fin − inicio en el 100 % de los casos | Sí, en segundos enteros (`568`). Coincide con fin − inicio salvo en 8 filas |
| ¿Trae id de usuario? | **No** (solo `genero_usuario`) | Sí, con sufijo de texto: `6243BAEcobici` | Sí, como número con decimal: `992557.0` |
| ¿Trae id de viaje? | **No** | Sí, con sufijo: `9379BAEcobici` (`Id_recorrido`, con mayúscula) | Sí, numérico de 8 dígitos (`id_recorrido`) |
| Formato de id de estación | Numérico (`11`) | Con sufijo: `5BAEcobici` | Numérico (`513`) |
| Formato de nombre de estación | Sin número (`Tribunales`) | Con número adelante: `005 - Plaza Italia` | Con número adelante: `308 - SAN MARTIN II`; mezcla de mayúsculas y minúsculas |
| Rango de fechas de inicio | 2016-01-01 → 2016-12-31 | **2019-02-09** → 2019-12-31 (no hay viajes de enero ni de principios de febrero) | 2024-01-01 → 2024-12-31 |
| Nulos relevantes | `fecha_destino_recorrido`: 93.555 | Estación destino (id, nombre, etc.): 1.760; `g�nero`: 93.571 | `fecha_destino_recorrido`: 3.379; `genero`: 11.946 |
| Ids de viaje repetidos dentro del año | No aplica (no hay id) | 0 | 1 |
| Cantidad total de filas | **596.807** | **6.217.004** | **3.559.284** |

Otras observaciones de recorridos:

- **2019, coordenadas corridas:** en `long_estacion_destino` viene la latitud y en
  `lat_estacion_destino` viene el par `"lat,long"`. No afecta al esquema canónico, que no usa
  coordenadas.
- **2019, nombre de columna dañado:** la columna de género se llama `g�nero`. El carácter
  `�` (U+FFFD) ya viene así en el archivo, que es UTF-8 válido.
- **Caracteres dañados en el origen:** en los tres años hay nombres y direcciones con `�` en
  lugar de letras acentuadas (`S�nchez de Loria`, `Pe�a`). Es un error de la fuente, no de la
  lectura: todos los archivos se decodifican como UTF-8 sin errores. Bronze los conserva tal
  cual.
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

## Puntos a resolver antes de la Tarea 3 (pendientes de confirmación)

1. **2016 no trae id de viaje.** El esquema canónico pide `id_viaje` y la regla 5 detecta
   duplicados por ese id.
2. **2016 no trae id de usuario.** `id_usuario` puede ser nulo según el esquema, así que se
   cargaría como nulo.
3. **Duración de 2016:** como no coincide con fin − inicio, se calcularía desde las fechas
   (el enunciado lo prevé cuando la duración "viene en otra unidad").
4. **Sufijo `BAEcobici` en 2019 (ids de viaje, estación y usuario) y `.0` en ids de usuario de
   2024:** hay que quitarlos para que los ids sean numéricos y crucen con la tabla de usuarios.
5. **Prefijo numérico en nombres de estación de 2019 y 2024 (`005 - Plaza Italia`):** 2016 no
   lo tiene. Hay que decidir si se quita o no al normalizar.
