import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arc
from pvlib.location import Location

st.set_page_config(page_title="Diseño Paramétrico de Parasoles", layout="wide")
st.title("🌞 Diseño Paramétrico de Parasoles Verticales")

# === Entradas del usuario ===
col1, col2 = st.columns(2)

with col1:
    lat = st.number_input("Latitud", value=19.3809)
    lon = st.number_input("Longitud", value=-99.1931)
    orientacion_dict = {"Norte": 0, "Este": 90, "Sur": 180, "Oeste": 270}
    orientacion_str = st.selectbox("Orientación de la fachada", list(orientacion_dict.keys()), index=3)
    orientacion_fachada = orientacion_dict[orientacion_str]
    altura_ventana = st.slider("Altura de la ventana (m)", 0.5, 5.0, 1.5, step=0.1)
    ancho_ventana = st.slider("Ancho de la ventana (m)", 0.5, 20.0, 1.5, step=0.1)
    espesor_parasol = st.slider("Espesor del parasol (m)", 0.02, 0.1, 0.06, step=0.01)
    prof_usuario = st.slider("Profundidad sugerida del parasol (m)", 0.1, 1.5, 0.4, step=0.05)

with col2:
    altura_edificio = st.slider("Altura del edificio enfrente (m)", 1.0, 30.0, 6.0, step=0.5)
    ancho_calle = st.slider("Ancho de la calle (m)", 1.0, 30.0, 6.0, step=0.5)

altitud_minima_visible = np.degrees(np.arctan(altura_edificio / ancho_calle))


fechas_clave = ['2025-03-21', '2025-06-21', '2025-09-21', '2025-12-21']
horas = pd.date_range('06:00', '18:00', freq='15min').time

loc = Location(latitude=lat, longitude=lon, tz='Etc/GMT+6')
resultados = []

for fecha_base in fechas_clave:
    fecha_hora = [pd.Timestamp(f"{fecha_base} {h}", tz='Etc/GMT+6') for h in horas]
    solpos = loc.get_solarposition(fecha_hora)

    for i, row in solpos.iterrows():
        altitud = row['apparent_elevation']
        azimut = row['azimuth']

        if altitud > altitud_minima_visible:
            hsa_rad = np.arcsin(np.sin(np.radians(azimut - orientacion_fachada)) *
                                np.cos(np.radians(altitud)))
            hsa_deg = np.degrees(hsa_rad)

            resultados.append({
                "Fecha": i.date(),
                "Hora": i.time(),
                "Altitud solar (°)": altitud,
                "HSA (°)": hsa_deg
            })

df = pd.DataFrame(resultados)
hsa_prom = np.percentile(df["HSA (°)"].abs(), 75)
st.markdown(f"### HSA: **{hsa_prom:.1f}°**")

separacion = prof_usuario * np.tan(np.radians(hsa_prom))
num_parasoles = int((ancho_ventana + separacion) // (espesor_parasol + separacion))

st.markdown(f"### 📏 Separación calculada entre parasoles: **{separacion:.2f} m**")
st.markdown(f"### 🔢 Número de parasoles: **{num_parasoles}**")

fig, ax = plt.subplots(figsize=(8, 6))
room_size = 4
espesor_muro = 0.2

# Muros hacia el interior
ax.add_patch(Rectangle((0, 0), room_size, room_size, fill=False, edgecolor='black', linewidth=2))
ax.add_patch(Rectangle((espesor_muro, espesor_muro), room_size - 2*espesor_muro, room_size - 2*espesor_muro,
                       fill=False, edgecolor='gray', hatch='///', linewidth=1))

ax.annotate('N', xy=(room_size + 0.5, room_size), ha='center', fontsize=12, fontweight='bold', arrowprops=dict(facecolor='gray', arrowstyle='->'))

# Ventana centrada verticalmente con 1/3 arriba y 1/3 abajo
y0 = (room_size - ancho_ventana) / 2 if orientacion_fachada in [90, 270] else 0
x0 = (room_size - ancho_ventana) / 2 if orientacion_fachada in [0, 180] else 0

if orientacion_fachada in [90, 270]:
    cx = room_size if orientacion_fachada == 90 else 0
    cy = (room_size - ancho_ventana) / 2 + ancho_ventana / 2
    ax.add_patch(Rectangle((cx, cy - ancho_ventana / 3), 0.1 if orientacion_fachada == 90 else -0.1, ancho_ventana * 2 / 3, color='red'))

    for i in range(num_parasoles):
        py = cy - ancho_ventana / 3 + i * (espesor_parasol + separacion)
        if py + espesor_parasol <= cy + ancho_ventana / 3:
            px = cx if orientacion_fachada == 90 else cx - prof_usuario
            ax.add_patch(Rectangle((px, py), prof_usuario, espesor_parasol, color='steelblue'))

    dx = prof_usuario
    dy = dx * np.tan(np.radians(hsa_prom))
    x_end = cx + dx if orientacion_fachada == 90 else cx - dx
    ax.plot([cx, x_end], [cy, cy + dy], color='orange', linestyle='--')
    arc_radius = 0.5
    arc = Arc((cx, cy), arc_radius*2, arc_radius*2, angle=0,
              theta1=0 if orientacion_fachada == 90 else 180 - hsa_prom,
              theta2=hsa_prom if orientacion_fachada == 90 else 180,
              color='orange', linestyle='--')
    ax.add_patch(arc)
    ax.text(cx + arc_radius + 0.1 if orientacion_fachada == 90 else cx - arc_radius - 0.5, cy + 0.1,
            f"HSA ≈ {hsa_prom:.1f}°", color='orange', fontsize=12)

elif orientacion_fachada in [0, 180]:
    cy = room_size if orientacion_fachada == 0 else 0
    cx = (room_size - ancho_ventana) / 2 + ancho_ventana / 2
    ax.add_patch(Rectangle((cx - ancho_ventana / 3, cy), ancho_ventana * 2 / 3, 0.1 if orientacion_fachada == 0 else -0.1, color='red'))

    for i in range(num_parasoles):
        px = cx - ancho_ventana / 3 + i * (espesor_parasol + separacion)
        if px + espesor_parasol <= cx + ancho_ventana / 3:
            py = cy if orientacion_fachada == 0 else cy - prof_usuario
            ax.add_patch(Rectangle((px, py), espesor_parasol, prof_usuario, color='steelblue'))

    dy = prof_usuario
    dx = dy * np.tan(np.radians(hsa_prom))
    y_end = cy + dy if orientacion_fachada == 0 else cy - dy
    ax.plot([cx, cx + dx], [cy, y_end], color='orange', linestyle='--')
    arc_radius = 0.5
    arc = Arc((cx, cy), arc_radius*2, arc_radius*2, angle=90 if orientacion_fachada == 0 else 270,
              theta1=0, theta2=hsa_prom, color='orange', linestyle='--')
    ax.add_patch(arc)
    ax.text(cx + 0.1, cy + arc_radius + 0.1 if orientacion_fachada == 0 else cy - arc_radius - 0.5,
            f"HSA ≈ {hsa_prom:.1f}°", color='orange', fontsize=12)

ax.set_xlim(-1, room_size + 1.5)
ax.set_ylim(-1, room_size + 1.5)
ax.set_aspect('equal')
ax.axis('off')
plt.title("Planta esquemática con parasoles")
st.pyplot(fig)

st.subheader("Tabla solar (equinoccios y solsticios)")
st.dataframe(df)
