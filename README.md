# CamillaDSP Master Console — Web Frontend

> Interfaz web completa para [CamillaDSP](https://github.com/HEnquist/camilladsp) y [camillagui-backend](https://github.com/HEnquist/camillagui-backend).  
> Reemplaza la aplicación de escritorio Python por una SPA que funciona desde cualquier navegador moderno.

---

## Capturas de pantalla

| Login | VU Meters | EQ Graph |
|-------|-----------|----------|
| Pantalla de conexión con IP/Puerto | VU meters en tiempo real con faders por canal | Gráfico EQ interactivo con arrastre |

| Crossover | Mixer Matrix |
|-----------|--------------|
| Filtros LP/HP con orden ajustable | Matriz de routing entrada → salida |

---

## Características

### Panel de Control en Tiempo Real
- **VU Meters** con polling a 50ms (igual que la app Python original)
- **Peak hold**: 40 frames de retención + decaimiento 0.5 dB/frame
- **GR bar** (gain reduction) por canal de salida
- **Faders por canal** arrastrables (-30 dB a +10 dB), con rueda de mouse y reset con click derecho
- **Master fader** de volumen global
- **Mute por canal** con click en el nombre
- **MUTE ALL** global
- **Inversión de polaridad** (+/-) por canal
- **Delay por canal** en ms con reset con click derecho

### Ecualizador (Tab EQ)
- Gráfico Canvas interactivo con grid logarítmico 20 Hz–20 kHz, ±18 dB
- **Doble-click**: crea filtro Peaking en los canales seleccionados
- **Arrastre**: mueve frecuencia y ganancia
- **Rueda del mouse**: ajusta el factor Q
- **Click derecho**: elimina el filtro
- Tabla editable con combos de tipo de filtro y reasignación de canal
- Tipos: Peaking, Lowpass, Highpass, Notch, Allpass, LowShelf, HighShelf, BandPass, Gain, Free

### Crossover (Tab Crossovers)
- Gráfico Canvas con respuesta Butterworth y Linkwitz-Riley
- **Doble-click**: crea LP/HP según posición (izquierda = LP, derecha = HP)
- **Rueda del mouse**: cambia el orden del filtro (2, 4, 6, 8, 10, 12)
- **Arrastre**: mueve la frecuencia de corte
- Tabla con selector de familia (Butterworth / LinkwitzRiley) y orden

### Mixer Matrix (Tab Mixer)
- Canvas de routing entrada → salida en tiempo real
- **Click en celda '+' vacía**: crea conexión
- **Click derecho en celda verde**: elimina conexión
- **Doble-click en nombre de canal**: renombra entrada o salida

### Compresores
- **Doble-click** en barra VU: crea compresor con threshold en ese punto
- **Click derecho** en barra VU: elimina compresor
- Tabla editable: threshold, ratio, attack, release, makeup gain, clip limit
- **Botón AUTO**: muestrea 5 segundos y calcula parámetros automáticamente

### Gestión de Configuración
- Importar/Exportar configuración completa en **YAML** o **JSON**
- Importar filtros EQ en formato **REW / APO**
- Exportar filtros EQ como texto
- **Reset** con selección de número de canales IN/OUT
- **Consola de Log** con salida del motor CamillaDSP

### Internacionalización
- Idioma **Español / Inglés** con toggle en tiempo real
- Manual de usuario completo integrado en ambos idiomas

### Panel de Canales
- Botones IN/OUT para seleccionar canales visibles
- **Click derecho** en canal: activa/desactiva bypass de EQ
- Indicador visual de color por canal (32 colores únicos)

---

## Arquitectura

```
new_camilla_gui_fontend/
├── index.html                    # SPA única — login + app (toggle display)
├── install.sh                    # Instalador bash multi-arquitectura
├── style/
│   ├── base.css                  # Variables CSS, dark theme, resets globales
│   ├── layout.css                # Shell, login, tabs, channel panel
│   ├── vu.css                    # VU meters, faders, compresores
│   ├── eq.css                    # Gráfico EQ, tabla de filtros
│   ├── crossover.css             # Gráfico crossover, tabla
│   ├── mixer.css                 # Matriz mixer
│   └── modal.css                 # Modales, consola, snackbar
└── js/
    ├── core/
    │   ├── api.js                # Wrappers fetch() para todos los endpoints REST
    │   ├── events.js             # EventBus pub/sub global
    │   ├── i18n.js               # Traducciones ES/EN completas
    │   ├── state.js              # Estado global (config_raw, patchConfig, etc.)
    │   └── utils.js              # Utilidades compartidas, GLOBAL_HEX_COLORS
    ├── dsp/
    │   ├── biquad.js             # Matemáticas biquad (puerto exacto del Python)
    │   └── crossover.js          # Matemáticas Butterworth/LinkwitzRiley
    ├── ui/
    │   ├── login.js              # Pantalla de login con localStorage
    │   ├── snack.js              # Snackbar/toast global
    │   ├── channelPanel.js       # Panel lateral de canales
    │   ├── tabManager.js         # Gestión de tabs
    │   └── cornerButtons.js      # Imp/Exp Config/EQ, Reset, Log, Ayuda
    ├── tabs/
    │   ├── vumeters/
    │   │   ├── vuCanvas.js       # Canvas VU: gradiente, peak hold, GR bar
    │   │   ├── fader.js          # Canvas fader -30/+10 dB
    │   │   ├── polarity.js       # Botón +/- polaridad
    │   │   ├── delayInput.js     # Input delay ms
    │   │   ├── compressorTable.js# Tabla compresores con AUTO sampling
    │   │   └── vuTab.js          # Orchestrator VU + polling
    │   ├── eq/
    │   │   ├── eqGraph.js        # Canvas EQ interactivo
    │   │   ├── eqTable.js        # Tabla de filtros editable
    │   │   └── eqTab.js          # Orchestrator EQ
    │   ├── crossover/
    │   │   ├── crossGraph.js     # Canvas crossover interactivo
    │   │   ├── crossTable.js     # Tabla crossover
    │   │   └── crossTab.js       # Orchestrator crossover
    │   └── mixer/
    │       ├── mixerCanvas.js    # Canvas matriz de routing
    │       └── mixerTab.js       # Orchestrator mixer
    └── init.js                   # Entry point, bootstrap de la app
```

### Decisiones de diseño

| Decisión | Motivo |
|----------|--------|
| **SPA sin bundler** | Funciona servido directamente por el backend aiohttp, sin pasos de build |
| **ES Modules nativos** | `<script type="module">` — compatible con todos los navegadores modernos |
| **Canvas API** | Equivalente web a QPainter/QWidget del Python original |
| **EventBus pub/sub** | Desacopla estado, UI y lógica de negocio |
| **setTimeout recursivo** | Evita acumulación de requests en el polling de VU meters |
| **deep-merge + setConfig** | Una sola fuente de verdad, cada cambio envía la config completa |

---

## Requisitos

### Para usar el frontend

- **Backend**: [camillagui-backend](https://github.com/HEnquist/camillagui-backend) corriendo en puerto 5005
- **Motor**: [CamillaDSP](https://github.com/HEnquist/camilladsp) corriendo en puerto 1234
- **Navegador**: Chrome 90+, Firefox 88+, Edge 90+, Safari 14+

### Para el script de instalación

- Linux (Debian/Ubuntu/Raspbian, Arch, Fedora/RHEL)
- `sudo` / privilegios de root
- Conexión a internet (para descargar binarios y clonar repositorios)

---

## Instalación rápida (Linux)

```bash
git clone https://github.com/TU_USUARIO/camilladsp-web-gui.git
cd camilladsp-web-gui
sudo bash install.sh
```

El script detecta automáticamente la arquitectura y el gestor de paquetes, luego:

1. Instala dependencias del sistema (Python 3, pip, git, alsa-utils)
2. Descarga el binario de CamillaDSP para tu arquitectura
3. Clona e instala `camillagui-backend` con entorno virtual Python
4. Copia el frontend a `{backend}/gui/`
5. Crea configuración por defecto en `/etc/camilladsp/`
6. Opcionalmente crea servicios **systemd** para auto-inicio

### Arquitecturas soportadas por el instalador

| Arquitectura | Hardware típico |
|---|---|
| `x86_64` | PC / laptop Intel o AMD |
| `aarch64` | Raspberry Pi 4/5, Raspberry Pi CM4, Apple M1 (Linux) |
| `armv7l` | Raspberry Pi 2/3 (32-bit), otras placas ARM |
| `armv6l` | Raspberry Pi 1, Raspberry Pi Zero |

### Gestores de paquetes soportados

| Gestor | Distribuciones |
|---|---|
| `apt` | Debian, Ubuntu, Raspbian/Raspberry Pi OS |
| `pacman` | Arch Linux, Manjaro |
| `dnf` | Fedora, RHEL 8+, Rocky Linux |
| `yum` | CentOS 7, RHEL 7 |

---

## Instalación manual

### 1. Instalar CamillaDSP

Descarga el binario para tu arquitectura desde [releases de CamillaDSP](https://github.com/HEnquist/camilladsp/releases):

```bash
# Ejemplo para x86_64
wget https://github.com/HEnquist/camilladsp/releases/download/v2.1.0/camilladsp-linux-x86_64.tar.gz
tar xzf camilladsp-linux-x86_64.tar.gz
sudo install -m 755 camilladsp /usr/local/bin/
```

### 2. Instalar el backend

```bash
git clone https://github.com/HEnquist/camillagui-backend.git
cd camillagui-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Copiar el frontend

```bash
# Dentro del directorio del backend:
git clone https://github.com/TU_USUARIO/camilladsp-web-gui.git gui
```

O copiar manualmente los archivos al subdirectorio `gui/` del backend.

### 4. Iniciar los servicios

```bash
# Terminal 1 — CamillaDSP
camilladsp -p 1234 -a 0.0.0.0 /etc/camilladsp/configs/default.yml

# Terminal 2 — Backend + frontend web
cd camillagui-backend
source venv/bin/activate
python main.py
```

### 5. Acceder

Abrir en el navegador: `http://IP_DEL_SERVIDOR:5005`

---

## Configuración con systemd (opcional)

Después de la instalación manual, crear los servicios:

```bash
# /etc/systemd/system/camilladsp.service
sudo tee /etc/systemd/system/camilladsp.service << 'EOF'
[Unit]
Description=CamillaDSP Audio Processor
After=sound.target

[Service]
Type=simple
User=pi
ExecStart=/usr/local/bin/camilladsp -p 1234 -a 0.0.0.0 /etc/camilladsp/configs/default.yml
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# /etc/systemd/system/camillagui.service
sudo tee /etc/systemd/system/camillagui.service << 'EOF'
[Unit]
Description=CamillaGUI Web Backend
After=network.target camilladsp.service

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/camillagui/backend
ExecStart=/opt/camillagui/backend/venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now camilladsp camillagui
```

### Comandos de gestión

```bash
sudo systemctl start   camilladsp camillagui
sudo systemctl stop    camilladsp camillagui
sudo systemctl restart camillagui
sudo systemctl status  camillagui
sudo journalctl -u camillagui -f      # Ver logs en tiempo real
sudo journalctl -u camilladsp -f
```

---

## Guía de uso rápido

### Pantalla de Login
1. Ingresar la **IP** del servidor donde corre CamillaDSP
2. Ingresar el **puerto** del backend GUI (por defecto: `5005`)
3. Click en **CONECTAR A HARDWARE**

> La IP y puerto se guardan en `localStorage` para la próxima vez.

### Panel de canales (izquierda)
- **Click** en un canal: activa/desactiva su visibilidad en los gráficos
- **Click derecho** en un canal: activa/desactiva bypass de EQ para ese canal
- **ALL IN / ALL OUT**: selecciona o deselecciona todos los canales del grupo

### Tab VU Meters
| Acción | Resultado |
|--------|-----------|
| Click en nombre de salida | Mute / unmute del canal |
| Arrastrar fader | Ajusta ganancia -30 a +10 dB |
| Rueda en fader | Ajuste fino ±0.5 dB |
| Click derecho en fader | Reset a 0 dB |
| Doble-click en barra VU | Crea compresor con threshold en ese punto |
| Click derecho en barra VU | Elimina compresor |
| MUTE ALL | Silencia/restaura todas las salidas |

### Tab EQ
| Acción | Resultado |
|--------|-----------|
| Doble-click en área vacía | Crea filtro Peaking en canales seleccionados |
| Arrastrar punto de filtro | Mueve frecuencia (horizontal) y ganancia (vertical) |
| Rueda del mouse sobre filtro | Ajusta el factor Q |
| Click derecho sobre filtro | Elimina el filtro |
| Editar celda en tabla | Cambia el parámetro directamente |

### Tab Crossovers
| Acción | Resultado |
|--------|-----------|
| Doble-click lado izquierdo | Crea filtro Lowpass |
| Doble-click lado derecho | Crea filtro Highpass |
| Arrastrar punto | Mueve la frecuencia de corte |
| Rueda del mouse | Cambia el orden (2, 4, 6, 8, 10, 12) |
| Click derecho | Elimina el filtro |

### Tab Mixer
| Acción | Resultado |
|--------|-----------|
| Click en celda `+` | Crea conexión entrada → salida |
| Click derecho en celda verde | Elimina la conexión |
| Doble-click en nombre | Renombra la entrada o salida |

---

## API del Backend

El frontend se comunica exclusivamente con el backend REST de camillagui:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/status` | GET | Niveles RMS/peak en tiempo real |
| `/api/getconfig` | GET | Configuración completa JSON |
| `/api/setconfig` | POST | Aplica nueva configuración |
| `/api/validateconfig` | POST | Valida sin aplicar |
| `/api/getparam/{name}` | GET | Obtiene parámetro (volume, mute) |
| `/api/setparam/{name}` | POST | Establece parámetro |
| `/api/setparamindex/{name}/{index}` | POST | Parámetro por índice de canal |
| `/api/storedconfigs` | GET | Lista de configs guardadas |
| `/api/uploadconfigs` | POST | Sube archivos de config |
| `/api/deleteconfigs` | POST | Elimina configs |
| `/api/storedcoeffs` | GET | Lista de coeficientes FIR |
| `/api/uploadcoeffs` | POST | Sube archivos de coeficientes |
| `/api/configtoyml` | POST | Convierte JSON → YAML |
| `/api/ymlconfigtojsonconfig` | POST | Convierte YAML → JSON |
| `/api/eqapotojson` | POST | Importa filtros REW/APO |
| `/api/evalfilter` | POST | Evalúa respuesta frecuencial |
| `/api/logfile` | GET | Log del motor CamillaDSP |
| `/api/backends` | GET | Backends de audio disponibles |
| `/api/capturedevices/{backend}` | GET | Dispositivos de captura |
| `/api/playbackdevices/{backend}` | GET | Dispositivos de reproducción |

---

## Configuración mínima de CamillaDSP

Ejemplo de `default.yml` para 2 entradas / 2 salidas:

```yaml
devices:
  samplerate: 48000
  chunksize: 1024
  capture:
    type: Alsa
    channels: 2
    format: S32LE
    device: hw:0
  playback:
    type: Alsa
    channels: 2
    format: S32LE
    device: hw:0

mixers:
  GlobalMixer:
    channels:
      in: 2
      out: 2
    mapping:
      - dest: 0
        sources:
          - channel: 0
            gain: 0
            inverted: false
      - dest: 1
        sources:
          - channel: 1
            gain: 0
            inverted: false

filters: {}
pipeline:
  - type: Mixer
    name: GlobalMixer
```

---

## Solución de problemas

### Error al conectar
- Verificar que el backend esté corriendo: `curl http://IP:5005/api/status`
- Verificar que CamillaDSP esté activo: `systemctl status camilladsp`
- Revisar el firewall: el puerto 5005 debe estar abierto
- En Raspberry Pi, verificar que el usuario tenga acceso a ALSA: `sudo usermod -aG audio $USER`

### Los VU meters no se mueven
- Verificar que CamillaDSP esté procesando audio (puerto 1234)
- En la consola de Log revisar si hay errores de dispositivo de audio
- Comprobar la configuración de dispositivos ALSA con `aplay -l` y `arecord -l`

### No aparecen canales en el panel lateral
- La configuración debe tener al menos un dispositivo `capture` y `playback` con `channels > 0`
- Usar el botón **Reset** para generar una configuración base

### Error CORS en el navegador
Añadir en la configuración del backend (`camillagui.yml`):
```yaml
allow_cors: true
```

### El frontend no carga (404)
Verificar que los archivos estén en el subdirectorio `gui/` del backend:
```bash
ls /opt/camillagui/backend/gui/index.html
```

---

## Desarrollo

El proyecto usa **ES Modules nativos** sin transpilación ni bundler. Para desarrollar:

```bash
# Desde el directorio del backend de camillagui
python main.py

# Editar archivos JS/CSS y recargar el navegador
# No hay paso de build
```

Para pruebas locales sin el backend real, se puede usar cualquier servidor HTTP estático:

```bash
# Python
cd new_camilla_gui_fontend
python3 -m http.server 8080

# Node.js (npx)
npx serve .
```

> Al servir desde un servidor diferente al backend, habrá errores CORS en las llamadas API. Esto es esperado; en producción siempre se sirve desde el puerto 5005 del backend.

---

## Compatibilidad

| Componente | Versión |
|------------|---------|
| CamillaDSP | 2.x |
| camillagui-backend | 0.x / 1.x |
| Python (backend) | 3.8+ |
| Chrome / Edge | 90+ |
| Firefox | 88+ |
| Safari | 14+ |

---

## Diferencias con la app Python original

| Característica | App Python (PySide6) | Este frontend web |
|---|---|---|
| Instalación | Requiere Qt6 + Python en escritorio | Solo navegador web |
| Acceso remoto | No (local) | Sí — desde cualquier dispositivo en la red |
| VU meters | 50ms (QTimer) | 50ms (setTimeout recursivo) |
| Peak hold | 40 frames | 40 frames (idéntico) |
| GR smoothing | attack=0.4, release=0.05 | Idéntico |
| Matemáticas biquad | `calcular_magnitud_biquad()` | Puerto JS exacto |
| Interfaz de audio | Qt audio / ALSA directo | Via REST API al backend |
| Multi-usuario | No | Sí (múltiples navegadores) |

---

## Licencia

MIT License — libre para uso, modificación y distribución.

---

## Créditos

- **CamillaDSP**: [Henrik Enquist](https://github.com/HEnquist/camilladsp) — motor DSP de audio
- **camillagui-backend**: [Henrik Enquist](https://github.com/HEnquist/camillagui-backend) — API REST
- Este frontend web fue creado como reemplazo multiplataforma de la GUI de escritorio
