import streamlit as st
import math
import io
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ==============================
# CONTROL RESET
# ==============================
if "reset_flag" not in st.session_state:
    st.session_state.reset_flag = False

# ==============================
# CONFIG
# ==============================
PALLET_LARGO = 120
PALLET_ANCHO = 100
PALLET_ALTURA_MAX = 180
ALTURA_PALLET = 15
PESO_MAX_PALLET = 1000

CBM_20 = 33
CBM_40 = 67

PALLETS_20 = 11
PALLETS_40 = 22
ALTURA_CONTENEDOR = 260

# ==============================
# LOGICA
# ==============================
def rotaciones(l, a, h):
    return [
        (l, a, h), (a, l, h), (l, h, a),
        (h, l, a), (a, h, l), (h, a, l)
    ]

def mejor_config(p):
    opciones = []

    for (l, a, h) in rotaciones(p['largo'], p['ancho'], p['alto']):
        por_fila = int(PALLET_LARGO / l)
        por_col = int(PALLET_ANCHO / a)

        if por_fila == 0 or por_col == 0:
            continue

        base = por_fila * por_col
        altura_disp = PALLET_ALTURA_MAX - ALTURA_PALLET
        capas = int(altura_disp / h)

        if capas == 0:
            continue

        cajas_pallet = base * capas

        if cajas_pallet * p['peso'] > PESO_MAX_PALLET:
            cajas_pallet = int(PESO_MAX_PALLET / p['peso'])

        if cajas_pallet <= 0:
            continue

        opciones.append({
            'orientacion': (l, a, h),
            'cajas_pallet': cajas_pallet
        })

    mejor = max(opciones, key=lambda x: x['cajas_pallet'])
    return mejor, opciones

def calcular_producto(p):
    mejor, opciones = mejor_config(p)

    cajas_pallet = mejor['cajas_pallet']
    pallets = math.ceil(p['cantidad'] / cajas_pallet)

    vol_caja = (p['largo'] * p['ancho'] * p['alto']) / 1_000_000
    vol_pallet = cajas_pallet * vol_caja
    peso_pallet = cajas_pallet * p['peso']

    return {
        'pallets': pallets,
        'cajas_pallet': cajas_pallet,
        'vol_pallet': vol_pallet,
        'peso_pallet': peso_pallet,
        'opciones': opciones
    }

def calcular_contenedores(total_pallets, vol):
    doble = (PALLET_ALTURA_MAX * 2) <= ALTURA_CONTENEDOR

    cap_20 = PALLETS_20 * (2 if doble else 1)
    cap_40 = PALLETS_40 * (2 if doble else 1)

    c20 = math.ceil(total_pallets / cap_20)
    c40 = math.ceil(total_pallets / cap_40)

    occ20 = vol / (c20 * CBM_20) if c20 else 0
    occ40 = vol / (c40 * CBM_40) if c40 else 0

    return c20, c40, occ20, occ40, doble

# ==============================
# UI
# ==============================
st.set_page_config(layout="wide")
st.title("📦 CALCULADORA LOGÍSTICA RUUFE")

try:
    st.image("logo.png", width=200)
except:
    pass

# ==============================
# CLIENTE
# ==============================
st.subheader("🧾 Información cliente (opcional)")

cliente = st.text_input("Nombre del cliente", key="cliente")
destino = st.text_input("País destino", key="destino")

num_productos = st.number_input("Número de tipos de cajas", min_value=1, step=1, key="num_productos")

productos = []

for i in range(int(num_productos)):
    st.subheader(f"Tipo de caja {i+1}")

    col1, col2, col3 = st.columns(3)

    largo = col1.number_input(f"Largo cm {i}", key=f"l{i}")
    ancho = col2.number_input(f"Ancho cm {i}", key=f"a{i}")
    alto = col3.number_input(f"Alto cm {i}", key=f"h{i}")

    peso = st.number_input(f"Peso kg {i}", key=f"p{i}")
    cantidad = st.number_input(f"Cantidad {i}", key=f"c{i}")

    productos.append({
        'largo': largo,
        'ancho': ancho,
        'alto': alto,
        'peso': peso,
        'cantidad': cantidad
    })

# ==============================
# CALCULAR
# ==============================
calcular = st.button("Calcular")

if calcular:

    total_vol = 0
    total_peso = 0
    total_pallets = 0
    resultados = []

    st.header("📊 Resultados por tipo de caja")

    for i, p in enumerate(productos):
        r = calcular_producto(p)
        resultados.append((p, r))

        total_pallets += r['pallets']
        total_vol += (p['largo'] * p['ancho'] * p['alto'] / 1_000_000) * p['cantidad']
        total_peso += p['peso'] * p['cantidad']

        st.subheader(f"Tipo de caja {i+1}")

        for op in r['opciones']:
            st.write(f"{op['orientacion']} → {op['cajas_pallet']} cajas/pallet")

        st.write(f"Cajas por pallet: {r['cajas_pallet']}")
        st.write(f"Pallets: {r['pallets']}")
        st.write(f"Volumen pallet: {round(r['vol_pallet'],2)} m3")
        st.write(f"Peso pallet: {round(r['peso_pallet'],2)} kg")

    c20, c40, occ20, occ40, doble = calcular_contenedores(total_pallets, total_vol)

    st.header("🚢 REPORTE LOGÍSTICO FINAL")

    st.write(f"📦 Total cajas: {sum([p['cantidad'] for p in productos])}")
    st.write(f"🧱 Total pallets: {total_pallets}")
    st.write(f"⚖️ Peso total: {round(total_peso,2)} kg")
    st.write(f"📐 Volumen total: {round(total_vol,2)} m3")

    st.write(f"20ft: {c20} | Ocupación: {round(occ20*100,1)}%")
    st.write(f"40ft: {c40} | Ocupación: {round(occ40*100,1)}%")

    if doble:
        st.success("📦 Apilación de pallets: Permitida")
    else:
        st.error("📦 Apilación de pallets: No permitida por límite de altura")

    # ==============================
    # RECOMENDACIÓN INTELIGENTE
    # ==============================

    st.header("🧠 RECOMENDACIÓN LOGÍSTICA")

    ocupacion_20 = occ20 * 100
    ocupacion_40 = occ40 * 100

    if total_pallets <= 4:
     recomendacion = "📦 Envío muy pequeño: se recomienda consolidación (LCL) para optimizar costos logísticos."

    elif ocupacion_20 >= 80 and c20 == 1:
     recomendacion = "🚢 Alta eficiencia: se recomienda contenedor de 20 pies (FCL), con excelente nivel de ocupación."

    elif ocupacion_40 >= 80 and c40 == 1:
     recomendacion = "🚢 Alta eficiencia: se recomienda contenedor de 40 pies (FCL), maximizando capacidad."

    elif ocupacion_40 > ocupacion_20:
     recomendacion = "⚖️ Mejor desempeño en contenedor de 40 pies: mayor eficiencia volumétrica."

    elif ocupacion_20 > ocupacion_40:
     recomendacion = "⚖️ Mejor desempeño en contenedor de 20 pies: opción más eficiente para este embarque."

    elif ocupacion_40 < 50:
     recomendacion = "📉 Baja ocupación: se recomienda consolidar carga o evaluar envío parcial."

    else:
     recomendacion = "📦 Envío viable, se recomienda evaluar costos entre 20ft y 40ft según tarifa naviera."

    st.success(recomendacion)

    # ==============================
    # PDF PROFESIONAL
    # ==============================
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    contenido = []

    # ==============================
    # LOGO
    # ==============================
    try:
     contenido.append(Image("logo.png", width=160, height=70))
    except:
     pass

     contenido.append(Spacer(1, 10))

    # ==============================
    # TITULO
    # ==============================
     contenido.append(Paragraph("<b>COTIZACIÓN DE EMBARQUE LOGÍSTICO</b>", styles['Title']))
     contenido.append(Spacer(1, 10))

    # ==============================
    # INFO GENERAL
    # ==============================
    fecha = datetime.now().strftime("%d/%m/%Y")

    contenido.append(Paragraph(f"<b>Fecha:</b> {fecha}", styles['Normal']))
    contenido.append(Paragraph(f"<b>Cliente:</b> {cliente if cliente else '________________________'}", styles['Normal']))
    contenido.append(Paragraph(f"<b>Destino:</b> {destino if destino else '________________________'}", styles['Normal']))

    contenido.append(Spacer(1, 15))

    # ==============================
    # ESTILO TABLAS
    # ==============================
    estilo = TableStyle([
     ('BACKGROUND', (0,0), (-1,0), colors.orange),
     ('TEXTCOLOR', (0,0), (-1,0), colors.white),
     ('GRID', (0,0), (-1,-1), 0.5, colors.black),
     ('ALIGN', (0,0), (-1,-1), 'CENTER')
 ])

    ancho_tabla = [300, 200]

    # ==============================
    # KPI PRINCIPALES
    # ==============================
    contenido.append(Paragraph("<b>Resumen logístico</b>", styles['Heading2']))

    data_kpi = [
     ["Concepto", "Valor"],
     ["Total cajas", sum([p['cantidad'] for p in productos])],
     ["Total pallets", total_pallets],
     ["Peso total (kg)", round(total_peso,2)],
     ["Volumen total (m³)", round(total_vol,2)],
 ]

    tabla_kpi = Table(data_kpi, colWidths=ancho_tabla)
    tabla_kpi.setStyle(estilo)

    contenido.append(tabla_kpi)
    contenido.append(Spacer(1, 15))

    # ==============================
    # CONTENEDORES
    # ==============================
    contenido.append(Paragraph("<b>Capacidad de contenedores</b>", styles['Heading2']))
 
     data_cont = [
      ["Concepto", "Valor"],
      ["Contenedores 20ft", c20],
      ["Ocupación 20ft", f"{round(occ20*100,1)}%"],
      ["Contenedores 40ft", c40],
      ["Ocupación 40ft", f"{round(occ40*100,1)}%"],
      ["Apilación de pallets", "Permitida" if doble else "No permitida por altura"],
   ]

      tabla_cont = Table(data_cont, colWidths=ancho_tabla)
      tabla_cont.setStyle(estilo)

    contenido.append(tabla_cont)
    contenido.append(Spacer(1, 15))

    # ==============================
    # DETALLE POR CAJA
    # ==============================
     contenido.append(Paragraph("<b>Detalle por tipo de caja</b>", styles['Heading2']))

     for i, (p, r) in enumerate(resultados):

    contenido.append(Spacer(1, 10))
    contenido.append(Paragraph(f"<b>Tipo de caja {i+1}</b>", styles['Normal']))

     data_det = [
        ["Concepto", "Valor"],
        ["Cajas por pallet", r['cajas_pallet']],
        ["Cantidad total cajas", p['cantidad']],
        ["Pallets requeridos", r['pallets']],
        ["Peso por pallet (kg)", round(r['peso_pallet'],2)],
        ["Volumen por pallet (m³)", round(r['vol_pallet'],2)],
    ]

    tabla_det = Table(data_det, colWidths=ancho_tabla)
    tabla_det.setStyle(estilo)

    contenido.append(tabla_det)

    contenido.append(Spacer(1, 15))

    # ==============================
    # RECOMENDACIÓN
    # ==============================
      contenido.append(Paragraph("<b>Recomendación logística</b>", styles['Heading2']))
      contenido.append(Spacer(1, 5))

      contenido.append(Paragraph(recomendacion, styles['Normal']))

    # ==============================
    # GENERAR PDF
    # ==============================
     doc.build(contenido)

      pdf = buffer.getvalue()
      buffer.close()

      st.download_button(
        "📄 Exportar PDF",
       pdf,
      "cotizacion_logistica_ruufe.pdf",
       mime="application/pdf"
    )

    # ==============================
    # BOTON LIMPIAR (CORRECTO)
    # ==============================
    if st.button("🔄 Limpiar y nueva simulación"):
        for key in st.session_state.keys():
            st.session_state[key] = 0 if isinstance(st.session_state[key], (int, float)) else ""
        st.rerun()
