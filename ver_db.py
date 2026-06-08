import sqlite3

conexion = sqlite3.connect("asistencias.db")

cursor = conexion.cursor()

cursor.execute("SELECT * FROM asistencias")

datos = cursor.fetchall()

for fila in datos:
    print(fila)

conexion.close()