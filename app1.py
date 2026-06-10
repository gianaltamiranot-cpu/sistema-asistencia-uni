from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, send_from_directory, send_file
from werkzeug.utils import secure_filename
import os
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

ADMIN_PASSWORD = "UNI2026"

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

    nombre = request.form["nombre"].strip()
    comite = request.form["comite"]

    # Buscar DNI automáticamente en el Excel
    fila_miembro = df[df["Nombre"] == nombre]

    if len(fila_miembro) == 0:
        return """
        <h2>❌ Error</h2>
        <p>No se encontró el DNI del voluntario.</p>
        <a href="/">Volver</a>
        """

    dni = str(int(fila_miembro.iloc[0]["DNI"])).strip()

    archivo = request.files["evidencia"]

    nombre_archivo = (
        datetime.now().strftime("%Y%m%d_%H%M%S_")
        + secure_filename(archivo.filename)
    )

    ruta = os.path.join("uploads", nombre_archivo)

    archivo.save(ruta)

    ahora = datetime.now(ZoneInfo("America/Lima"))

    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M:%S")

    conexion = sqlite3.connect("asistencias.db")
    cursor = conexion.cursor()

    # Buscar el último registro del voluntario
    cursor.execute("""
        SELECT fecha, hora
        FROM asistencias
        WHERE nombre = ?
        ORDER BY id DESC
        LIMIT 1
    """, (nombre,))

    ultimo = cursor.fetchone()

    # Verificar si ya registró hace menos de 30 minutos
    if ultimo:

        fecha_hora_ultima = datetime.strptime(
            ultimo[0] + " " + ultimo[1],
            "%d/%m/%Y %H:%M:%S"
        )

        fecha_hora_ultima = fecha_hora_ultima.replace(
            tzinfo=ZoneInfo("America/Lima")
        )

        diferencia = ahora - fecha_hora_ultima

        if diferencia.total_seconds() < 1800:

            minutos_restantes = (
                30 - int(diferencia.total_seconds() // 60)
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

    # Registrar asistencia
    cursor.execute("""
        INSERT INTO asistencias
        (fecha, hora, comite, nombre, evidencia, dni)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        fecha,
        hora,
        comite,
        nombre,
        nombre_archivo,
        dni
    ))

    conexion.commit()
    conexion.close()

    return f"""
    <h2>✅ Asistencia registrada</h2>

    <p><b>Nombre:</b> {nombre}</p>
    <p><b>Comité:</b> {comite}</p>
    <p><b>DNI:</b> {dni}</p>
    <p><b>Fecha:</b> {fecha}</p>
    <p><b>Hora:</b> {hora}</p>
    <p><b>Evidencia:</b> {nombre_archivo}</p>

    <a href="/">Volver</a>
    """


@app.route("/uploads/<archivo>")
def ver_evidencia(archivo):
    return send_from_directory("uploads", archivo)


@app.route("/consultar", methods=["GET", "POST"])
def consultar():

    if request.method == "GET":
        return render_template("consultar.html")

    dni = request.form["dni"].strip()

    conexion = sqlite3.connect("asistencias.db")
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT fecha, hora, comite, nombre
        FROM asistencias
        WHERE dni = ?
        ORDER BY id DESC
    """, (dni,))

    datos = cursor.fetchall()

    conexion.close()

    if len(datos) == 0:
        return f"""
        <h2>❌ No se encontraron registros</h2>

        <p>No existen asistencias registradas para el DNI {dni}.</p>

        <a href="/consultar">Volver</a>
        """

    nombre = datos[0][3]

    total = len(datos)

    html = f"""
    <h1>Mis Asistencias</h1>

    <p><b>Nombre:</b> {nombre}</p>

    <p><b>DNI:</b> {dni}</p>

    <p><b>Total de registros:</b> {total}</p>

    <table border="1" cellpadding="10" style="border-collapse:collapse;">
        <tr>
            <th>Fecha</th>
            <th>Hora</th>
            <th>Comité</th>
        </tr>
    """

    for fila in datos:
        html += f"""
        <tr>
            <td>{fila[0]}</td>
            <td>{fila[1]}</td>
            <td>{fila[2]}</td>
        </tr>
        """

    html += """
    </table>

    <br><br>

    <a href="/consultar">Nueva consulta</a>
    """

    return html

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "GET":

        return """
        <h1>Panel Administrador</h1>

        <form method="POST">

            <p>Ingrese la contraseña:</p>

            <input type="password"
                   name="password"
                   required>

            <br><br>

            <button type="submit">
                Ingresar
            </button>

        </form>
        """

    password = request.form["password"]

    if password != ADMIN_PASSWORD:

        return """
        <h2>❌ Contraseña incorrecta</h2>

        <a href="/admin">Volver</a>
        """

    conexion = sqlite3.connect("asistencias.db")

    cursor = conexion.cursor()

    cursor.execute("""
        SELECT fecha,
               hora,
               comite,
               nombre,
               dni,
               evidencia
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
            "DNI": fila[4],
            "Evidencia": fila[5]
        })

    return render_template(
        "admin.html",
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