import sqlite3

conexion = sqlite3.connect("asistencias.db")
cursor = conexion.cursor()

try:
    cursor.execute("""
        ALTER TABLE asistencias
        ADD COLUMN dni TEXT
    """)

    print("Columna DNI agregada correctamente.")

except sqlite3.OperationalError:
    print("La columna DNI ya existe.")

conexion.commit()
conexion.close()