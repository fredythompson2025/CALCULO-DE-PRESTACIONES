import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import base64

# Para PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

# ------------------------------
# Función para calcular tiempo trabajado
# ------------------------------
def calcular_tiempo(fecha_ingreso, fecha_salida):
    delta = fecha_salida - fecha_ingreso
    dias_totales = delta.days
    anios = dias_totales // 360
    meses = (dias_totales % 360) // 30
    dias = (dias_totales % 360) % 30
    return anios, meses, dias

# ------------------------------
# Función principal de prestaciones
# ------------------------------
def calcular_prestaciones(fecha_ingreso, fecha_salida, salario):
    anios, meses, dias = calcular_tiempo(fecha_ingreso, fecha_salida)
    salario_diario = salario / 30
    salario_promedio = salario  # Aquí podrías promediar si fuera necesario

    # Preaviso (2 meses por más de 15 años, simplificado)
    preaviso = 2 * salario
    # Cesantía (25 días por año trabajado, máx. 8 años pagados según ley)
    cesantia = min(anios, 8) * salario * 25 / 30
    # Vacaciones proporcionales (15 días x año)
    vacaciones = (salario_diario * 15) * (meses / 12)
    # Aguinaldo proporcional (1 salario / 12 * meses trabajados en el año)
    aguinaldo = (salario / 12) * (meses / 12 * 12)
    # Décimo cuarto proporcional
    decimo_cuarto = (salario / 12) * (meses / 12 * 12)

    data = [
        ["Preaviso", "60.00", f"{preaviso:,.2f}"],
        ["Cesantía", f"{anios*25:.2f}", f"{cesantia:,.2f}"],
        ["Vacaciones Proporcionales", f"{meses*2.5:.2f}", f"{vacaciones:,.2f}"],
        ["Aguinaldo Proporcional", f"{meses*20:.2f}", f"{aguinaldo:,.2f}"],
        ["Décimo Cuarto Proporcional", f"{meses*5:.2f}", f"{decimo_cuarto:,.2f}"],
    ]

    df = pd.DataFrame(data, columns=["Derecho", "Tiempo", "Valor Total"])
    total = df["Valor Total"].apply(lambda x: float(x.replace(",", ""))).sum()
    return df, total, (anios, meses, dias), salario_diario, salario_promedio

# ------------------------------
# Exportar a PDF
# ------------------------------
def export_pdf(df, total, trabajador, ingreso, salida, salario):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("CÁLCULO DE PRESTACIONES LABORALES - HONDURAS", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Trabajador: {trabajador}", styles['Normal']))
    story.append(Paragraph(f"Fecha de Ingreso: {ingreso.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Paragraph(f"Fecha de Salida: {salida.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Paragraph(f"Salario Mensual: Lps. {salario:,.2f}", styles['Normal']))
    story.append(Spacer(1, 12))

    data = [["Derecho", "Tiempo", "Valor Total"]] + df.values.tolist()
    table = Table(data, colWidths=[200, 100, 150])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"TOTAL A PAGAR: Lps. {total:,.2f}", styles['Heading2']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# ------------------------------
# Streamlit App
# ------------------------------
st.title("📊 Cálculo de Prestaciones Laborales - Honduras")

trabajador = st.text_input("Nombre del trabajador", "Carlos Aguilar")
fecha_ingreso = st.text_input("Fecha de Ingreso (dd/mm/aaaa)", "06/12/2006")
fecha_salida = st.text_input("Fecha de Salida (dd/mm/aaaa)", "30/08/2025")
salario = st.number_input("Salario Mensual (Lps)", min_value=0.0, value=27100.0)

if st.button("Calcular Prestaciones"):
    try:
        fi = datetime.strptime(fecha_ingreso, "%d/%m/%Y")
        fs = datetime.strptime(fecha_salida, "%d/%m/%Y")

        df, total, tiempo, sd, sp = calcular_prestaciones(fi, fs, salario)

        st.subheader("📋 Resultado")
        st.write(f"Años: {tiempo[0]}, Meses: {tiempo[1]}, Días: {tiempo[2]}")
        st.dataframe(df)
        st.success(f"💰 TOTAL A PAGAR: Lps. {total:,.2f}")

        # Exportar Excel
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        st.download_button("📥 Descargar Excel", data=excel_buffer, file_name="prestaciones.xlsx")

        # Exportar PDF
        pdf_buffer = export_pdf(df, total, trabajador, fi, fs, salario)
        st.download_button("📥 Descargar PDF", data=pdf_buffer, file_name="prestaciones.pdf", mime="application/pdf")

    except Exception as e:
        st.error(f"Error en el cálculo: {e}")
lo: {e}")
