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

    nombre = request.form["nombre"]
    comite = request.form["comite"]

    archivo = request.files["evidencia"]

    nombre_archivo = (
        datetime.now(ZoneInfo("America/Lima")).strftime("%Y%m%d_%H%M%S_")
        + secure_filename(archivo.filename)
    )

    ruta = os.path.join("uploads", nombre_archivo)
    archivo.save(ruta)

    ahora = datetime.now(ZoneInfo("America/Lima"))

    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M:%S")

    conexion = sqlite3.connect("asistencias.db")
    cursor = conexion.cursor()

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
    <a href="/">Volver</a>
    """
    
@app.route("/consultar", methods=["GET", "POST"])
def consultar():

    if request.method == "GET":
        return render_template("consultar.html")

    accion = request.form.get("accion", "")

    # Administrador
    if accion == "admin":

        password = request.form["password"]

        if password != ADMIN_PASSWORD:
            return """
            <h2>❌ Contraseña incorrecta</h2>
            <a href="/consultar">Volver</a>
            """

        return admin()

    # Voluntario
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

    # Ranking de asistencia
    cursor.execute("""
        SELECT nombre,
               comite,
               COUNT(*) AS total
        FROM asistencias
        GROUP BY nombre, comite
        ORDER BY total DESC
    """)

    ranking_datos = cursor.fetchall()

    ranking = []

    for fila in ranking_datos:

        ranking.append({
            "Nombre": fila[0],
            "Comite": fila[1],
            "Total": fila[2]
        })

    # Voluntarios que asistieron
    cursor.execute("""
        SELECT DISTINCT nombre
        FROM asistencias
    """)

    asistieron = [fila[0] for fila in cursor.fetchall()]

    # Todos los voluntarios del Excel
    todos = df["Nombre"].dropna().tolist()

    # Faltantes
    faltaron = []

    for nombre in todos:

        if nombre not in asistieron:

            faltaron.append(nombre)

    total_voluntarios = len(todos)
    total_asistieron = len(asistieron)
    total_faltaron = len(faltaron)

    porcentaje = round(
        total_asistieron * 100 / total_voluntarios,
        2
    )

    # Registros completos
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

        dni = fila[4]

        if dni is None:
            dni = ""
        else:
            dni = str(dni).replace(".0", "")

        registros.append({
            "Fecha": fila[0],
            "Hora": fila[1],
            "Comite": fila[2],
            "Nombre": fila[3],
            "DNI": dni,
            "Evidencia": fila[5]
        })

    return render_template(
        "admin.html",
        registros=registros,
        ranking=ranking,
        faltaron=faltaron,
        total_voluntarios=total_voluntarios,
        total_asistieron=total_asistieron,
        total_faltaron=total_faltaron,
        porcentaje=porcentaje
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