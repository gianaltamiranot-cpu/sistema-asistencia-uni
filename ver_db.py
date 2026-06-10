import sqlite3

conexion = sqlite3.connect("asistencias.db")
cursor = conexion.cursor()

cursor.execute("PRAGMA table_info(asistencias)")

for columna in cursor.fetchall():
    print(columna)

conexion.close()