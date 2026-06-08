import sqlite3

conexion = sqlite3.connect("asistencias.db")

cursor = conexion.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS asistencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT,
    hora TEXT,
    comite TEXT,
    nombre TEXT,
    evidencia TEXT
)
""")

conexion.commit()
conexion.close()

print("Base de datos creada correctamente")