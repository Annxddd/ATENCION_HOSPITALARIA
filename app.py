from flask import Flask, render_template, jsonify
from PIL import Image
import numpy as np
import io, base64, os

app    = Flask(__name__)
BASE   = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")


# ── Procesamiento de imágenes ────────────────────────────

def remove_black_bg(path: str, threshold: int = 30) -> Image.Image:
    """Elimina fondo negro convirtiéndolo en transparente (alpha = 0)."""
    img  = Image.open(path).convert("RGB")
    arr  = np.array(img).astype(np.uint16)
    rgba = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
    rgba[:, :, :3] = arr.astype(np.uint8)
    is_black       = (arr[:,:,0] < threshold) & (arr[:,:,1] < threshold) & (arr[:,:,2] < threshold)
    rgba[:, :, 3]  = (~is_black * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def to_b64(img: Image.Image, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def load_map() -> str:
    """Carga el mapa en su tamaño original"""
    path = os.path.join(STATIC, "hospital.png")
    img = Image.open(path).convert("RGB")  # Sin resize
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return base64.b64encode(buf.getvalue()).decode()


def load_person(filename: str) -> str:
    """Carga ícono de persona, elimina fondo negro y retorna PNG base64 a 110×110."""
    path = os.path.join(STATIC, filename)
    img  = remove_black_bg(path).resize((110, 110), Image.LANCZOS)
    return to_b64(img, "PNG")


def get_config() -> dict:
    S = 0.625
    def sc(x, y):
        return [round(x * S), round(y * S)]
    
    # =========================================================
    # DATOS DEL DASHBOARD - 02 AL 08 DE MARZO 2026
    # =========================================================
    
    # Distribución horaria de la SEMANA (total 305 pacientes)
    hourly_weekly = [10, 27, 42, 35, 33, 32, 20, 14, 17, 15, 22, 23, 8, 5, 2]
    hour_labels = ["6AM","7AM","8AM","9AM","10AM","11AM",
                   "12PM","1PM","2PM","3PM","4PM","5PM","6PM","7PM","8PM"]
    
    total_weekly = sum(hourly_weekly)  # 305
    
    # Día pico: Jueves (66 pacientes)
    # Calcular distribución horaria para el día pico basada en porcentajes
    hourly_pct = [h / total_weekly for h in hourly_weekly]
    hourly_peak_day = [max(1, round(p * 66)) for p in hourly_pct]
    
    # Ajustar para que sume exactamente 66
    diff = 66 - sum(hourly_peak_day)
    if diff != 0:
        # Encontrar la hora con más pacientes y ajustar
        max_idx = hourly_peak_day.index(max(hourly_peak_day))
        hourly_peak_day[max_idx] += diff
    
    # Datos diarios (aproximados según el dashboard)
    daily_patients = {
        "Lunes": 42,
        "Martes": 44,
        "Miércoles": 45,
        "Jueves": 66,   # Día pico
        "Viernes": 48,
        "Sábado": 35,
        "Domingo": 25,
    }
    
    print(f"✓ Total semana: {total_weekly} pacientes")
    print(f"✓ Día pico (Jueves): {sum(hourly_peak_day)} pacientes")
    print(f"✓ Distribución horaria día pico: {hourly_peak_day}")
    
    # =========================================================
    # TUS COORDENADAS DE SILLAS
    # =========================================================
    sillas_originales = [
        [178, 662], [245, 662], [319, 662],
        [119, 730], [119, 807], [119, 884], [119, 956],
        [197, 956], [273, 956], [345, 956],
        [439, 777], [510, 777], [576, 777], [642, 777],
        [436, 868], [504, 868], [571, 868], [645, 868],
    ]
    
    seats = [sc(x, y) for x, y in sillas_originales]
    door = sc(107, 500)
    
    # Paths
    paths = {
        "pink_to_desk": [door, sc(199,506), sc(185,392)],
        "pink_to_wait": [sc(185,392), sc(400,700), sc(257,821)],
        "blue_to_desk": [door, sc(370,420), sc(370,392)],
        "blue_to_wait": [sc(370,392), sc(400,700), sc(257,821)],
        "green_to_desk": [door, sc(370,504), sc(370,612), sc(543,590)],
        "green_to_wait": [sc(543,590), sc(400,700), sc(257,821)],
        "to_xray": [sc(400,700), sc(1143,545), sc(1143,654), sc(1596,654), sc(1553,351)],
        "to_lab": [sc(400,700), sc(1143,545), sc(1143,654), sc(1596,654), sc(1594,852)],
        "exit": [sc(1598,654), sc(1782,654)],
    }
    
    # Zonas
    zones = {
        "door":      {"x": sc(107,500)[0], "y": sc(107,500)[1], "r": 20, "color": "#fbbf24", "label": "Entrada"},
        "qr":        {"x": sc(185,392)[0], "y": sc(185,392)[1], "r": 20, "color": "#ec4899", "label": "QR Digital"},
        "reception": {"x": sc(370,392)[0], "y": sc(370,392)[1], "r": 20, "color": "#3b82f6", "label": "Registro Fisico"},
        "kiosk":     {"x": sc(543,590)[0], "y": sc(543,590)[1], "r": 20, "color": "#10b981", "label": "Asistente Digital"},
        "xray":      {"x": sc(1553,351)[0], "y": sc(1553,351)[1], "r": 20, "color": "#8b5cf6", "label": "Rayos X"},
        "lab":       {"x": sc(1594,852)[0], "y": sc(1594,852)[1], "r": 20, "color": "#f97316", "label": "Laboratorio"},
    }
    
    return {
        # Datos para mostrar en el dashboard
        "total_weekly": total_weekly,
        "total_daily": sum(hourly_peak_day),
        "avg_age": 55.7,
        "peak_hour": "8 AM",
        "peak_hour_count": 42,
        "peak_day": "Jueves",
        "peak_day_count": 66,
        
        # Datos horarios
        "hourly_weekly": hourly_weekly,      # Para la gráfica de barras
        "hourly_daily": hourly_peak_day,     # Para spawnear pacientes (día pico)
        "hour_labels": hour_labels,
        
        # Configuración de simulación
        "sim_duration": 15 * 60,  # 15 horas (6AM a 9PM)
        "person_size": 55,
        "door": door,
        "paths": paths,
        "zones": zones,
        "seats": seats,
    }

# ── Rutas ────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/assets")
def assets():
    """
    Devuelve imágenes procesadas (base64) + config de simulación.
    El frontend llama esto una sola vez al iniciar.
    """
    return jsonify({
        "images": {
            "hospital":      load_map(),
            "hospital_type": "png",
            "pink":          load_person("person_pink.png"),
            "blue":          load_person("person_blue.png"),
            "green":         load_person("person_green.png"),
        },
        "config": get_config(),
    })


# ── Entry point ──────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  Simulación Pre-Admisión Hospitalaria")
    print("  Universidad Interamericana de Panamá")
    print("=" * 50)

    required = ["hospital.png", "person_pink.png", "person_blue.png", "person_green.png"]
    missing  = [f for f in required if not os.path.exists(os.path.join(STATIC, f))]

    if missing:
        print("\n⚠  Faltan imágenes en la carpeta static/:")
        for f in missing:
            print(f"     static/{f}")
        print("\n  Ponlas ahí y vuelve a correr.\n")
    else:
        print("\n✓  Imágenes OK")

    print("  → http://localhost:5000\n")
    app.run(debug=True, port=5000)