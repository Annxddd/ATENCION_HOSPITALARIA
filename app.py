from flask import Flask, render_template, jsonify
from PIL import Image
import numpy as np
import io, base64, os

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")


def remove_black_bg(path: str, threshold: int = 30) -> Image.Image:
    img = Image.open(path).convert("RGB")
    arr = np.array(img).astype(np.uint16)
    rgba = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
    rgba[:, :, :3] = arr.astype(np.uint8)
    is_black = (arr[:,:,0] < threshold) & (arr[:,:,1] < threshold) & (arr[:,:,2] < threshold)
    rgba[:, :, 3] = (~is_black * 255).astype(np.uint8)
    return Image.fromarray(rgba, "RGBA")


def to_b64(img: Image.Image, fmt: str = "PNG") -> str:
    buf = io.BytesIO()
    img.save(buf, format=fmt, optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def load_map() -> str:
    path = os.path.join(STATIC, "hospital.png")
    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return base64.b64encode(buf.getvalue()).decode()


def load_person(filename: str) -> str:
    path = os.path.join(STATIC, filename)
    img = remove_black_bg(path).resize((110, 110), Image.LANCZOS)
    return to_b64(img, "PNG")


def get_config() -> dict:
    S = 0.625
    def sc(x, y):
        return [round(x * S), round(y * S)]
    
    # Datos reales del documento - 305 pacientes semana
    hourly_weekly = [10, 27, 42, 35, 33, 32, 20, 14, 17, 15, 22, 23, 8, 5, 2]
    hour_labels = ["6AM","7AM","8AM","9AM","10AM","11AM",
                   "12PM","1PM","2PM","3PM","4PM","5PM","6PM","7PM","8PM"]
    
    total_weekly = sum(hourly_weekly)  # 305
    
    # Día pico: Jueves (66 pacientes)
    hourly_pct = [h / total_weekly for h in hourly_weekly]
    hourly_peak_day = []

    # Método manual para asegurar que sume 66
    remaining = 66
    for i, pct in enumerate(hourly_pct):
        val = round(pct * 66)
        if val < 1:
            val = 1
        if i == len(hourly_pct) - 1:
            val = remaining
        else:
            remaining -= val
        hourly_peak_day.append(val)

    print(f"✓ Total día pico: {sum(hourly_peak_day)} pacientes")
    print(f"✓ Distribución: {hourly_peak_day}")

    # =========================================================
    # ESCENARIOS - CON TIEMPOS DRÁSTICAMENTE DIFERENTES
    # =========================================================
    escenarios = {
        "actual": {
            "name": "Actual",
            "distribucion": [0.15, 0.60, 0.25],
            "tiempos_atencion": {
                "qr": [1.5, 2.5],
                "presencial": [5.0, 8.0],
                "asistido": [3.0, 5.0]
            },
            "wait_min": [8, 15],           # ← ESPERA LARGA
            "descripcion": "15% QR, 60% Presencial"
        },
        "mes3": {
            "name": "Mes 3",
            "distribucion": [0.27, 0.41, 0.32],
            "tiempos_atencion": {
                "qr": [1.3, 2.2],
                "presencial": [4.5, 7.0],
                "asistido": [2.8, 4.5]
            },
            "wait_min": [5, 10],
            "descripcion": "27% QR, 41% Presencial"
        },
        "mes6": {
            "name": "Mes 6",
            "distribucion": [0.38, 0.31, 0.31],
            "tiempos_atencion": {
                "qr": [1.0, 1.8],
                "presencial": [4.0, 6.5],
                "asistido": [2.5, 4.0]
            },
            "wait_min": [3, 6],
            "descripcion": "38% QR, 31% Presencial"
        },
        "mes12": {
            "name": "Mes 12",
            "distribucion": [0.52, 0.22, 0.26],
            "tiempos_atencion": {
                "qr": [0.4, 0.7],           # 24-42 segundos
                "presencial": [2.5, 3.5],
                "asistido": [1.2, 1.8]
            },
            "wait_min": [1, 3],         # ← ESPERA MUY CORTA (30-90 segundos)
            "descripcion": "52% QR 🚀"
        }
    }
    
    # Coordenadas
    sillas_originales = [
        [178, 662], [245, 662], [319, 662],
        [119, 730], [119, 807], [119, 884], [119, 956],
        [197, 956], [273, 956], [345, 956],
        [439, 777], [510, 777], [576, 777], [642, 777],
        [436, 868], [504, 868], [571, 868], [645, 868],
    ]
    
    seats = [sc(x, y) for x, y in sillas_originales]
    door = sc(107, 500)
    
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
    
    zones = {
        "door":      {"x": sc(107,500)[0], "y": sc(107,500)[1], "r": 20, "color": "#fbbf24", "label": "Entrada"},
        "qr":        {"x": sc(185,392)[0], "y": sc(185,392)[1], "r": 20, "color": "#ec4899", "label": "QR Digital"},
        "reception": {"x": sc(370,392)[0], "y": sc(370,392)[1], "r": 20, "color": "#3b82f6", "label": "Registro Fisico"},
        "kiosk":     {"x": sc(543,590)[0], "y": sc(543,590)[1], "r": 20, "color": "#10b981", "label": "Asistente Digital"},
        "xray":      {"x": sc(1553,351)[0], "y": sc(1553,351)[1], "r": 20, "color": "#8b5cf6", "label": "Rayos X"},
        "lab":       {"x": sc(1594,852)[0], "y": sc(1594,852)[1], "r": 20, "color": "#f97316", "label": "Laboratorio"},
    }
    
    return {
        "escenarios": escenarios,
        "total_weekly": total_weekly,
        "total_daily": sum(hourly_peak_day),
        "avg_age": 55.7,
        "peak_hour": "8 AM",
        "peak_hour_count": 42,
        "peak_day": "Jueves",
        "peak_day_count": 66,
        "hourly_weekly": hourly_weekly,
        "hourly_daily": hourly_peak_day,
        "hour_labels": hour_labels,
        "sim_duration": 14 * 60,
        "person_size": 55,
        "door": door,
        "paths": paths,
        "zones": zones,
        "seats": seats,
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/assets")
def assets():
    return jsonify({
        "images": {
            "hospital": load_map(),
            "hospital_type": "png",
            "pink": load_person("person_pink.png"),
            "blue": load_person("person_blue.png"),
            "green": load_person("person_green.png"),
        },
        "config": get_config(),
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  Simulación Pre-Admisión Hospitalaria")
    print("  Universidad Interamericana de Panamá")
    print("=" * 50)
    print("\n  → http://localhost:5000\n")
    app.run(debug=True, port=5000)
