import sqlite3

conexion = sqlite3.connect("asistencias.db")

cursor = conexion.cursor()

cursor.execute("DELETE FROM asistencias")

conexion.commit()
conexion.close()

print("Todos los registros fueron eliminados")