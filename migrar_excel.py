import pandas as pd
import sqlite3

# Leer Excel
df = pd.read_excel("asistencias.xlsx")

# Conectar a SQLite
conexion = sqlite3.connect("asistencias.db")

# Guardar datos en la tabla
df.to_sql(
    "asistencias",
    conexion,
    if_exists="append",
    index=False
)

conexion.close()

print("Datos migrados correctamente")