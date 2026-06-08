from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# Crear carpeta uploads si no existe
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

    ahora = datetime.now()

    fecha = ahora.strftime("%d/%m/%Y")
    hora = ahora.strftime("%H:%M:%S")

    asistencia = pd.read_excel("asistencias.xlsx")

    registros_persona = asistencia[
        asistencia["Nombre"] == nombre
    ]

    if len(registros_persona) > 0:

        ultimo = registros_persona.iloc[-1]

        try:

            fecha_hora_ultima = datetime.strptime(
                str(ultimo["Fecha"]) + " " + str(ultimo["Hora"]),
                "%d/%m/%Y %H:%M:%S"
            )

            diferencia = ahora - fecha_hora_ultima

            if diferencia < timedelta(minutes=30):

                minutos_restantes = (
                    30 - int(diferencia.total_seconds() / 60)
                )

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

    nueva_fila = pd.DataFrame([{
        "Fecha": fecha,
        "Hora": hora,
        "Comite": comite,
        "Nombre": nombre,
        "Evidencia": nombre_archivo
    }])

    asistencia = pd.concat(
        [asistencia, nueva_fila],
        ignore_index=True
    )

    asistencia.to_excel(
        "asistencias.xlsx",
        index=False
    )

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

    asistencia = pd.read_excel("asistencias.xlsx")

    return render_template(
        "consultar.html",
        registros=asistencia.to_dict("records")
    )
if __name__ == "__main__":
    app.run(debug=True)