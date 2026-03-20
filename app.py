import streamlit as st
import math
from datetime import datetime

# ==============================
# CONFIG
# ==============================
st.set_page_config(layout="wide")

st.title("📦 CALCULADORA LOGÍSTICA RUUFE")

# LOGO
try:
    st.image("logo.png", width=200)
except:
    pass

# ==============================
# INPUT CLIENTE
# ==============================
st.subheader("🧾 Información del cliente (opcional)")
cliente = st.text_input("Nombre del cliente")
destino = st.text_input("País destino")

st.divider()

# ==============================
# INPUT GENERAL
# ==============================
num_tipos = st.number_input("¿Cuántos tipos de caja?", min_value=1, step=1)

productos = []

for i in range(num_tipos):
    st.subheader(f"Tipo de caja {i+1}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    largo = col1.number_input(f"Largo (cm) - Caja {i+1}", key=f"l{i}")
    ancho = col2.number_input(f"Ancho (cm) - Caja {i+1}", key=f"a{i}")
    alto = col3.number_input(f"Alto (cm) - Caja {i+1}", key=f"h{i}")
    peso = col4.number_input(f"Peso (kg) - Caja {i+1}", key=f"p{i}")
    
    cantidad = st.number_input(f"Cantidad de cajas - Tipo {i+1}", key=f"c{i}")
    
    productos.append({
        "l": largo/100,
        "a": ancho/100,
        "h": alto/100,
        "peso": peso,
        "cantidad": cantidad
    })

# ==============================
# PARÁMETROS PALLET
# ==============================
st.subheader("📦 Parámetros pallet")

colp1, colp2, colp3 = st.columns(3)
pallet_l = colp1.number_input("Largo pallet (m)", value=1.2)
pallet_a = colp2.number_input("Ancho pallet (m)", value=1.0)
pallet_h_max = colp3.number_input("Altura máxima (m)", value=2.2)

peso_max_pallet = st.number_input("Peso máximo por pallet (kg)", value=1000)

# ==============================
# BOTÓN CALCULAR
# ==============================
if st.button("Calcular"):

    resultados = []
    total_pallets = 0
    total_vol = 0
    total_peso = 0

    for p in productos:

        # ROTACIONES
        rotaciones = [
            (p["l"], p["a"], p["h"]),
            (p["a"], p["l"], p["h"]),
            (p["h"], p["a"], p["l"])
        ]

        mejor = None
        max_cajas = 0

        for r in rotaciones:
            cajas_base = math.floor(pallet_l / r[0]) * math.floor(pallet_a / r[1])
            alturas = math.floor(pallet_h_max / r[2])
            total = cajas_base * alturas

            if total > max_cajas:
                max_cajas = total
                mejor = r

        cajas_pallet = max_cajas if max_cajas > 0 else 1

        pallets = math.ceil(p["cantidad"] / cajas_pallet)

        peso_pallet = cajas_pallet * p["peso"]

        if peso_pallet > peso_max_pallet:
            cajas_pallet = math.floor(peso_max_pallet / p["peso"])
            pallets = math.ceil(p["cantidad"] / cajas_pallet)

        vol_pallet = pallet_l * pallet_a * pallet_h_max

        total_pallets += pallets
        total_vol += vol_pallet * pallets
        total_peso += p["peso"] * p["cantidad"]

        resultados.append({
            "cajas_pallet": cajas_pallet,
            "pallets": pallets,
            "vol_pallet": vol_pallet,
            "peso_pallet": peso_pallet
        })

    # ==============================
    # CONTENEDORES
    # ==============================
    pallets_20 = 10
    pallets_40 = 21

    c20 = math.ceil(total_pallets / pallets_20)
    c40 = math.ceil(total_pallets / pallets_40)

    occ20 = total_pallets / (c20 * pallets_20) if c20 else 0
    occ40 = total_pallets / (c40 * pallets_40) if c40 else 0

    doble = pallet_h_max < 1.2

    # ==============================
    # RESULTADOS
    # ==============================
    st.subheader("📊 Resultados")

    st.write(f"Total pallets: {total_pallets}")
    st.write(f"Volumen total: {round(total_vol,2)} m3")
    st.write(f"Peso total: {round(total_peso,2)} kg")

    st.write(f"Contenedor 20ft: {c20}")
    st.write(f"Contenedor 40ft: {c40}")

    if doble:
        st.success("📦 Apilación de pallets: Permitida")
    else:
        st.error("📦 Apilación de pallets: No permitida por límite de altura")

    # ==============================
    # RECOMENDACIÓN
    # ==============================
    if total_pallets <= 5:
        recomendacion = "Consolidar carga (LCL)"
    elif occ40 < 0.6:
        recomendacion = "Baja ocupación, considerar consolidación"
    else:
        recomendacion = "Envío FCL óptimo"

    st.subheader("🧠 Recomendación")
    st.write(recomendacion)

    # ==============================
    # PDF
    # ==============================
    import io
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    contenido = []

    try:
        contenido.append(Image("logo.png", width=140, height=60))
    except:
        pass

    contenido.append(Spacer(1, 10))
    contenido.append(Paragraph("<b>COTIZACIÓN DE EMBARQUE LOGÍSTICO</b>", styles['Title']))
    contenido.append(Spacer(1, 10))

    fecha = datetime.now().strftime("%d/%m/%Y")

    contenido.append(Paragraph(f"Fecha: {fecha}", styles['Normal']))
    contenido.append(Paragraph(f"Cliente: {cliente if cliente else '________________'}", styles['Normal']))
    contenido.append(Paragraph(f"Destino: {destino if destino else '________________'}", styles['Normal']))

    contenido.append(Spacer(1, 15))

    estilo = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.orange),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black)
    ])

    ancho = [260, 140]

    # TABLA RESUMEN
    contenido.append(Paragraph("<b>Resumen logístico</b>", styles['Heading2']))
    contenido.append(Spacer(1, 8))

    data = [
        ["Concepto", "Valor"],
        ["Total pallets", total_pallets],
        ["Volumen total", round(total_vol,2)],
        ["Peso total", round(total_peso,2)],
        ["Contenedor 20ft", c20],
        ["Contenedor 40ft", c40],
        ["Ocupación 40ft (%)", f"{round(occ40*100,1)}%"],
        ["Apilación", "Permitida" if doble else "No permitida"]
    ]

    tabla = Table(data, colWidths=ancho)
    tabla.setStyle(estilo)

    contenido.append(tabla)

    contenido.append(Spacer(1, 15))

    contenido.append(Paragraph(f"<b>Recomendación:</b> {recomendacion}", styles['Normal']))

    doc.build(contenido)

    pdf = buffer.getvalue()
    buffer.close()

    st.download_button(
        label="📄 Exportar reporte en PDF",
        data=pdf,
        file_name="cotizacion_logistica_ruufe.pdf",
        mime="application/pdf"
    )

# ==============================
# LIMPIAR
# ==============================
if st.button("🔄 Limpiar y nueva simulación"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()
