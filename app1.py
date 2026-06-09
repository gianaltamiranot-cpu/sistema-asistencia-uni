from flask import Flask, render_template, request, send_from_directory, send_file
from werkzeug.utils import secure_filename
import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# Crear carpeta uploads
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Leer miembros
df = pd.read_excel("miembros1.xlsx")

df["Comites"] = df["Comites"].fillna("")
df["Nombre"] = df["Nombre"].fillna("")

comites = sorted(df["Comites"].dropna().astype(str).unique())


@app.route("/")
def inicio():

    miembros_por_comite = {}

    for comite in comites:

        miembros = df[df["Comites"] == comite]["Nombre"].tolist()

        miembros_por_comite[comite] = miembros

    return render_template(
        "index.html",
        comites=comites,
        miembros_por_comite=miembros_por_comite
    )


@app.route("/registrar", methods=["POST"])
def registrar():

    nombre = request.form["nombre"]
    comite = request.form["comite"]

    archivo = request.files["evidencia"]

    nombre_archivo = (
        datetime.now().strftime("%Y%m%d_%H%M%S_")
        + secure_filename(archivo.filename)
    )

    ruta = os.path.join("uploads", nombre_archivo)

    archivo.save(ruta)

    ahora = datetime.utcnow() - timedelta(hours=5)

    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M:%S")

    conexion = sqlite3.connect("asistencias.db")
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT fecha, hora
        FROM asistencias
        WHERE nombre = ?
        ORDER BY id DESC
        LIMIT 1
    """, (nombre,))

    ultimo = cursor.fetchone()

    if ultimo:

        try:

            fecha_hora_ultima = datetime.strptime(
                ultimo[0] + " " + ultimo[1],
                "%d/%m/%Y %H:%M:%S"
            )

            diferencia = ahora - fecha_hora_ultima

            if diferencia < timedelta(minutes=30):

                minutos_restantes = (
                    30 - int(diferencia.total_seconds() / 60)
                )

                conexion.close()

                return f"""
                <h2>⚠️ Registro reciente</h2>

                <p>
                <b>{nombre}</b> ya registró asistencia hace poco.
                </p>

                <p>
                Debe esperar aproximadamente
                <b>{minutos_restantes} minutos</b>
                para volver a registrar.
                </p>

                <a href="/">Volver</a>
                """

        except:
            pass

    cursor.execute("""
        INSERT INTO asistencias
        (fecha, hora, comite, nombre, evidencia)
        VALUES (?, ?, ?, ?, ?)
    """, (
        fecha,
        hora,
        comite,
        nombre,
        nombre_archivo
    ))

    conexion.commit()
    conexion.close()

    return f"""
    <h2>✅ Asistencia registrada</h2>

    <p><b>Nombre:</b> {nombre}</p>
    <p><b>Comité:</b> {comite}</p>
    <p><b>Fecha:</b> {fecha}</p>
    <p><b>Hora:</b> {hora}</p>
    <p><b>Evidencia:</b> {nombre_archivo}</p>

    <a href="/">Volver</a>
    """


@app.route("/uploads/<archivo>")
def ver_evidencia(archivo):
    return send_from_directory("uploads", archivo)


@app.route("/consultar")
def consultar():

    conexion = sqlite3.connect("asistencias.db")

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT fecha, hora, comite, nombre, evidencia
        FROM asistencias
        ORDER BY id DESC
    """)

    datos = cursor.fetchall()

    conexion.close()

    registros = []

    for fila in datos:

        registros.append({
            "Fecha": fila[0],
            "Hora": fila[1],
            "Comite": fila[2],
            "Nombre": fila[3],
            "Evidencia": fila[4]
        })

    print("TOTAL:", len(registros))
    print(registros)

    return render_template(
        "consultar.html",
        registros=registros
    )

@app.route("/exportar_excel")
def exportar_excel():

    conexion = sqlite3.connect("asistencias.db")

    df = pd.read_sql_query(
        """
        SELECT
            fecha AS Fecha,
            hora AS Hora,
            comite AS Comite,
            nombre AS Nombre,
            evidencia AS Evidencia
        FROM asistencias
        ORDER BY id DESC
        """,
        conexion
    )

    conexion.close()

    nombre_archivo = "reporte_asistencias.xlsx"

    df.to_excel(
        nombre_archivo,
        index=False
    )

    return send_file(
        nombre_archivo,
        as_attachment=True
    )
if __name__ == "__main__":
    app.run(debug=True)