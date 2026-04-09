## Simulación Pre-Admisión Hospitalaria
## Estructura del proyecto

```
sim_hospital/
├── app.py                  ← servidor Flask (backend + procesamiento de imágenes)
├── static/
│   ├── hospital.png        ← pon aquí el mapa del hospital
│   ├── person_pink.png     ← ícono paciente con QR (fondo negro OK, se elimina automático)
│   ├── person_blue.png     ← ícono paciente registro físico
│   └── person_green.png    ← ícono paciente kiosko
└── templates/
    └── index.html          ← simulación visual completa
```

## Instalar dependencias

```
pip install flask pillow numpy
```

## Flujo de la simulación

Llega → Camina → Se sienta (at_wait) 
                     ↓
              Espera su tiempo sentado
                     ↓
              ¿Servicio libre? 
                ↓ NO        ↓ SÍ
           (queued)     (to_service)
          Sigue sentado     ↓
              ↓         En servicio
           Espera turno      ↓
              ↓           Termina
           Es llamado     Sale
              ↓
        Se levanta y va al servicio

```
Llegadas: 66 pacientes en el día pico
           ↓
Registro rápido (QR: 0.5 min, Kiosko: 2 min, Recepción: 5 min)
           ↓
Espera en sala → 15-18 pacientes acumulados
           ↓
Servicios: SOLO 1 paciente por vez (Rayos X: 8-18 min, Lab: 10-16 min)
           ↓
Cuello de botella → Pacientes se acumulan

