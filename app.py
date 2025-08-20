import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Cálculo de Prestaciones - Honduras", layout="centered")

st.title("📊 Cálculo de Prestaciones Laborales - Honduras")

# -------------------------
# Función de cálculo
# -------------------------
def calcular_prestaciones_hn(fecha_ingreso, fecha_salida, salario_mensual):
    ingreso = datetime.strptime(fecha_ingreso, "%d/%m/%Y")
    salida = datetime.strptime(fecha_salida, "%d/%m/%Y")

    dias_trabajados_total = (salida - ingreso).days
    anios = dias_trabajados_total / 365

    # --- CESANTÍA ---
    if anios < 0.25:
        cesantia = 0
    elif anios < 0.5:
        cesantia = (salario_mensual / 30) * 10
    elif anios < 1:
        cesantia = (salario_mensual / 30) * 20
    elif anios < 2:
        cesantia = salario_mensual * 1
    elif anios < 3:
        cesantia = salario_mensual * 2
    elif anios < 4:
        cesantia = salario_mensual * 3
    elif anios < 5:
        cesantia = salario_mensual * 4
    elif anios < 6:
        cesantia = salario_mensual * 5
    elif anios < 7:
        cesantia = salario_mensual * 6
    elif anios < 8:
        cesantia = salario_mensual * 7
    else:
        cesantia = salario_mensual * 8

    # --- PREAVISO ---
    if anios < 0.25:
        preaviso = 0
    elif anios < 0.5:
        preaviso = (salario_mensual / 30) * 7
    elif anios < 1:
        preaviso = (salario_mensual / 30) * 14
    elif anios < 2:
        preaviso = salario_mensual * 1
    elif anios < 5:
        preaviso = salario_mensual * 2
    elif anios < 10:
        preaviso = salario_mensual * 3
    else:
        preaviso = salario_mensual * 4

    # --- VACACIONES ---
    if anios < 1:
        dias_vac = 0
    elif anios < 4:
        dias_vac = 10
    elif anios < 7:
        dias_vac = 12
    elif anios < 10:
        dias_vac = 15
    else:
        dias_vac = 20

    # proporción en el último año trabajado
    try:
        inicio_ultimo_anio = datetime(salida.year, ingreso.month, ingreso.day)
    except:
        inicio_ultimo_anio = datetime(salida.year, 1, 1)
    dias_en_anio = (salida - inicio_ultimo_anio).days
    if dias_en_anio < 0:
        inicio_ultimo_anio = datetime(salida.year - 1, ingreso.month, ingreso.day)
        dias_en_anio = (salida - inicio_ultimo_anio).days
    proporcion_vac = dias_en_anio / 365
    vacaciones = (salario_mensual / 30) * dias_vac * proporcion_vac

    # --- DÉCIMO TERCERO ---
    inicio_dec13 = datetime(salida.year, 1, 1)
    dias_dec13 = (salida - inicio_dec13).days
    decimo_tercero = (dias_dec13 / 365) * salario_mensual

    # --- DÉCIMO CUARTO ---
    if salida.month >= 6:
        inicio_dec14 = datetime(salida.year, 6, 1)
    else:
        inicio_dec14 = datetime(salida.year - 1, 6, 1)
    dias_dec14 = (salida - inicio_dec14).days
    decimo_cuarto = (dias_dec14 / 365) * salario_mensual

    total = cesantia + preaviso + vacaciones + decimo_tercero + decimo_cuarto

    return {
        "Cesantía": round(cesantia, 2),
        "Preaviso": round(preaviso, 2),
        "Vacaciones proporcionales": round(vacaciones, 2),
        "Décimo Tercero (proporcional)": round(decimo_tercero, 2),
        "Décimo Cuarto (proporcional)": round(decimo_cuarto, 2),
        "Total Prestaciones": round(total, 2)
    }

# -------------------------
# Función exportar Excel
# -------------------------
def export_excel(data_dict):
    df = pd.DataFrame(list(data_dict.items()), columns=["Concepto", "Monto (Lps)"])
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Prestaciones")
    return output.getvalue()

# -------------------------
# Función exportar PDF
# -------------------------
def export_pdf(data_dict):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Cálculo de Prestaciones - Honduras", styles["Title"]))
    elements.append(Spacer(1, 12))

    data = [["Concepto", "Monto (Lps)"]]
    for k, v in data_dict.items():
        data.append([k, f"L. {v:,.2f}"])

    table = Table(data, colWidths=[200, 200])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0,0), (-1,0), 10),
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# -------------------------
# Inputs de usuario
# -------------------------
fecha_ingreso = st.text_input("📅 Fecha de Ingreso (dd/mm/aaaa)", "01/01/2020")
fecha_salida = st.text_input("📅 Fecha de Salida (dd/mm/aaaa)", "01/08/2025")
salario_mensual = st.number_input("💵 Salario Mensual (Lps)", min_value=0.0, value=15000.0, step=500.0)

if st.button("Calcular Prestaciones"):
    try:
        prestaciones = calcular_prestaciones_hn(fecha_ingreso, fecha_salida, salario_mensual)

        st.subheader("📋 Resultados")
        for k, v in prestaciones.items():
            st.write(f"**{k}:** L. {v:,.2f}")

        # Botones de descarga
        st.download_button(
            label="⬇️ Descargar en Excel",
            data=export_excel(prestaciones),
            file_name="prestaciones_hn.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.download_button(
            label="⬇️ Descargar en PDF",
            data=export_pdf(prestaciones),
            file_name="prestaciones_hn.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Error en el cálculo: {e}")
