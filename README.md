# CamillaDSP Master Console — Web Frontend

> Interfaz web completa para [CamillaDSP](https://github.com/HEnquist/camilladsp) y [camillagui-backend](https://github.com/HEnquist/camillagui-backend).  
> Reemplaza la aplicación de escritorio Python por una SPA que funciona desde cualquier navegador moderno, sin instalación en el cliente.

---

## Índice

1. [Características](#características)
2. [Cómo funciona el sistema](#cómo-funciona-el-sistema)
3. [Requisitos previos](#requisitos-previos)
4. [Instalación rápida con script automático](#instalación-rápida-con-script-automático)
5. [Instalación manual paso a paso](#instalación-manual-paso-a-paso)
   - [Paso 1 — Instalar dependencias del sistema](#paso-1--instalar-dependencias-del-sistema)
   - [Paso 2 — Instalar CamillaDSP](#paso-2--instalar-camilladsp)
   - [Paso 3 — Instalar camillagui-backend](#paso-3--instalar-camillagui-backend)
   - [Paso 4 — Instalar el frontend web](#paso-4--instalar-el-frontend-web)
   - [Paso 5 — Configurar CamillaDSP](#paso-5--configurar-camilladsp)
   - [Paso 6 — Iniciar los servicios](#paso-6--iniciar-los-servicios)
6. [Auto-inicio con systemd](#auto-inicio-con-systemd)
7. [Forma de conexión](#forma-de-conexión)
8. [Guía de uso](#guía-de-uso)
9. [Configuración del backend](#configuración-del-backend)
10. [Solución de problemas](#solución-de-problemas)
11. [Arquitectura del código](#arquitectura-del-código)
12. [Compatibilidad](#compatibilidad)

---

## Características

### VU Meters y Dinámica
- VU meters en tiempo real (polling cada 50 ms)
- Peak hold: 40 frames de retención + decaimiento 0.5 dB/frame
- Barra GR (Gain Reduction) por canal de salida
- Faders por canal arrastrables de −30 dB a +10 dB
- Master fader de volumen global
- Mute individual por canal (click en el nombre)
- MUTE ALL global
- Inversión de polaridad (+/−) por canal de salida
- Delay por canal en milisegundos

### Ecualizador
- Gráfico Canvas interactivo 20 Hz – 20 kHz, ±18 dB, escala logarítmica
- Doble-click: crea filtro Peaking en los canales seleccionados
- Arrastre: mueve frecuencia y ganancia
- Rueda del mouse: ajusta el factor Q
- Click derecho: elimina el filtro
- Tabla editable con selector de tipo y reasignación de canal
- Tipos soportados: Peaking, Lowpass, Highpass, Notch, Allpass, LowShelf, HighShelf, BandPass, Gain, Free

### Crossovers
- Gráfico Canvas con curvas Butterworth y Linkwitz-Riley
- Doble-click: crea LP (lado izquierdo) o HP (lado derecho)
- Rueda del mouse: cambia el orden (2, 4, 6, 8, 10, 12)
- Arrastre: mueve la frecuencia de corte
- Tabla con selector de familia y orden

### Mixer Matrix
- Matriz de routing entrada → salida con canvas interactivo
- Click en celda vacía (+): crea conexión
- Click derecho en celda verde: elimina conexión
- Doble-click en nombre de canal: renombra

### Compresores
- Doble-click en barra VU: crea compresor con threshold automático
- Click derecho en barra VU: elimina compresor
- Tabla editable: threshold, ratio, attack, release, makeup gain, clip limit
- Botón AUTO: muestrea 5 segundos y calcula parámetros automáticamente

### Gestión de configuración
- Importar / Exportar configuración completa YAML o JSON
- Importar filtros EQ en formato REW / APO
- Exportar filtros EQ como texto plano
- Reset con selección de número de canales IN/OUT
- Consola de log con salida en tiempo real de CamillaDSP

### Otros
- Idioma Español / Inglés con toggle instantáneo
- Panel lateral de canales con selección individual y bypass por canal
- Sin instalación en el cliente — solo un navegador web moderno

---

## Cómo funciona el sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                      Servidor Linux / RPi                        │
│                                                                  │
│  ┌─────────────────┐    WebSocket     ┌──────────────────────┐  │
│  │                 │◄────puerto 1234──►│                      │  │
│  │  CamillaDSP     │                  │  camillagui-backend  │  │
│  │  (motor DSP)    │                  │  (API REST Python)   │  │
│  │                 │                  │  puerto 5005         │  │
│  └────────┬────────┘                  └──────────┬───────────┘  │
│           │                                      │              │
│     Hardware ALSA                         Sirve index.html      │
│     (tarjeta de audio)                    + archivos estáticos  │
└───────────────────────────────────────────────────┬─────────────┘
                                                    │ HTTP puerto 5005
                                                    │
                        ┌───────────────────────────▼────────────────────┐
                        │         Navegador Web (cualquier dispositivo)   │
                        │                                                  │
                        │   http://IP_SERVIDOR:5005                        │
                        │                                                  │
                        │   • VU Meters en tiempo real                     │
                        │   • EQ / Crossover interactivos                  │
                        │   • Mixer Matrix                                 │
                        └──────────────────────────────────────────────────┘
```

**Flujo de datos:**
1. El navegador abre `http://IP_SERVIDOR:5005` — el backend sirve `index.html` y los archivos JS/CSS
2. El frontend hace `GET /api/status` cada 50 ms para actualizar los VU meters
3. Cualquier cambio de configuración hace `POST /api/setconfig` con la config JSON completa
4. El backend retransmite los cambios a CamillaDSP vía WebSocket en el puerto 1234

---

## Requisitos previos

### Hardware mínimo para el servidor

| Hardware | Mínimo | Recomendado |
|----------|--------|-------------|
| CPU | ARMv7 1 GHz | x86_64 o ARM64 |
| RAM | 256 MB | 512 MB o más |
| Almacenamiento | 1 GB libre | 2 GB libre |
| Audio | Tarjeta ALSA compatible | Tarjeta dedicada (USB DAC, HAT) |
| Red | 100 Mbps | — |

**Placas probadas:**
- Raspberry Pi 2B / 3B / 3B+ / 4B / 5
- Raspberry Pi Zero 2W
- PC con Ubuntu / Debian
- Odroid C4

### Software necesario (se instala automáticamente)

- **Python 3.8 o superior**
- **pip** y **venv**
- **git**
- **wget** o **curl**
- **ALSA utils** (`alsa-utils`)
- Bibliotecas Python: `aiohttp`, `pycamilladsp`, `pyyaml`, `coloredlogs`

### Red

- El servidor debe ser accesible desde los dispositivos cliente en la red
- Puerto **5005** abierto (frontend + API)
- Puerto **1234** abierto solo si se accede al WebSocket de CamillaDSP desde fuera (normalmente no es necesario)

---

## Instalación rápida con script automático

> El script `install.sh` detecta automáticamente la arquitectura, el gestor de paquetes y la disponibilidad de systemd.

### En Raspberry Pi OS / Debian / Ubuntu

#### Opción A — Desde GitHub

```bash
git clone https://github.com/aasayag-hash/new_camilla_gui_fontend.git
cd new_camilla_gui_fontend
sudo bash install.sh
```

> **Nota:** GitHub no acepta contraseñas por HTTPS desde agosto 2021.  
> Usar **SSH** (`git@github.com:aasayag-hash/new_camilla_gui_fontend.git`) o un **Personal Access Token** como contraseña.  
> Ver [Cómo subir el proyecto a GitHub](#cómo-subir-el-proyecto-a-github) más abajo.

#### Opción B — Copiar los archivos directamente (sin GitHub)

Si tienes los archivos en un PC con Windows y el servidor es una Raspberry Pi u otro Linux en tu red:

```bash
# Desde Windows (PowerShell o cmd), copiar via SCP:
scp -r "C:\Users\lenovo\Downloads\fir python\new_camilla_gui_fontend" pi@192.168.1.45:/home/pi/new_camilla_gui_fontend

# Luego en el servidor Linux:
cd /home/pi/new_camilla_gui_fontend
sudo bash install.sh
```

O copiar con un pendrive USB:

```bash
# En Linux, montar el pendrive y copiar:
cp -r /media/usb/new_camilla_gui_fontend /home/pi/
cd /home/pi/new_camilla_gui_fontend
sudo bash install.sh
```

### Qué hace el script paso a paso

```
[1/6] Detecta arquitectura (x86_64 / aarch64 / armv7l / armv6l)
[2/6] Detecta gestor de paquetes (apt / pacman / dnf / yum)
[3/6] Instala dependencias del sistema
[4/6] Descarga binario CamillaDSP para tu arquitectura desde GitHub Releases
[5/6] Clona camillagui-backend + crea entorno virtual Python + instala dependencias
[6/6] Copia el frontend a {backend}/gui/
      Crea /etc/camilladsp/configs/default.yml
      (Opcional) Crea y habilita servicios systemd
```

### Preguntas del instalador

| Pregunta | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| Directorio de instalación | `/opt/camillagui` | Dónde se instalan todos los archivos |
| ¿Instalar CamillaDSP binary? | S | Descarga el binario precompilado |
| ¿Crear servicio systemd? | S | Configura inicio automático |
| Puerto del backend GUI | `5005` | Puerto HTTP del frontend/API |

### Verificar la instalación

```bash
# Verificar que CamillaDSP está instalado
camilladsp --version

# Verificar que el backend corre
sudo systemctl status camillagui

# Verificar que el puerto 5005 está activo
ss -tlnp | grep 5005

# Probar la API desde el mismo servidor
curl http://localhost:5005/api/status
```

---

## Instalación manual paso a paso

### Paso 1 — Instalar dependencias del sistema

#### Debian / Ubuntu / Raspberry Pi OS

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git curl wget alsa-utils
```

#### Arch Linux / Manjaro

```bash
sudo pacman -Sy --noconfirm python python-pip git curl wget alsa-utils
```

#### Fedora / RHEL / Rocky Linux

```bash
sudo dnf install -y python3 python3-pip git curl wget alsa-utils
```

#### Verificar Python

```bash
python3 --version
# Debe mostrar Python 3.8.x o superior

pip3 --version
# Debe mostrar pip 21.x o superior
```

---

### Paso 2 — Instalar CamillaDSP

#### Opción A — Binario precompilado (recomendado)

Ir a [github.com/HEnquist/camilladsp/releases](https://github.com/HEnquist/camilladsp/releases) y descargar el binario para tu arquitectura:

```bash
# Detectar arquitectura
uname -m
# x86_64  →  camilladsp-linux-x86_64.tar.gz
# aarch64 →  camilladsp-linux-aarch64.tar.gz
# armv7l  →  camilladsp-linux-armv7.tar.gz
# armv6l  →  camilladsp-linux-armv6.tar.gz
```

```bash
# Ejemplo para Raspberry Pi 4 (aarch64 / 64-bit OS)
VERSION="2.1.0"
wget https://github.com/HEnquist/camilladsp/releases/download/v${VERSION}/camilladsp-linux-aarch64.tar.gz
tar xzf camilladsp-linux-aarch64.tar.gz
sudo install -m 755 camilladsp /usr/local/bin/camilladsp

# Verificar
camilladsp --version
```

```bash
# Ejemplo para Raspberry Pi 3 (armv7l / 32-bit OS)
VERSION="2.1.0"
wget https://github.com/HEnquist/camilladsp/releases/download/v${VERSION}/camilladsp-linux-armv7.tar.gz
tar xzf camilladsp-linux-armv7.tar.gz
sudo install -m 755 camilladsp /usr/local/bin/camilladsp
```

```bash
# Ejemplo para PC con Ubuntu (x86_64)
VERSION="2.1.0"
wget https://github.com/HEnquist/camilladsp/releases/download/v${VERSION}/camilladsp-linux-x86_64.tar.gz
tar xzf camilladsp-linux-x86_64.tar.gz
sudo install -m 755 camilladsp /usr/local/bin/camilladsp
```

#### Opción B — Compilar desde código fuente

Requiere Rust instalado:

```bash
# Instalar Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Compilar CamillaDSP con soporte ALSA
git clone https://github.com/HEnquist/camilladsp.git
cd camilladsp
cargo build --release --features alsa-backend

# Instalar
sudo install -m 755 target/release/camilladsp /usr/local/bin/camilladsp
```

> **Nota:** La compilación puede tardar 10–30 minutos en una Raspberry Pi.

---

### Paso 3 — Instalar camillagui-backend

```bash
# Crear directorio de instalación
sudo mkdir -p /opt/camillagui
sudo chown $USER:$USER /opt/camillagui

# Clonar el backend
git clone https://github.com/HEnquist/camillagui-backend.git /opt/camillagui/backend
cd /opt/camillagui/backend

# Crear entorno virtual Python
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate

# Instalar dependencias Python
pip install --upgrade pip
pip install -r requirements.txt

# Desactivar entorno virtual
deactivate
```

#### Verificar el backend

```bash
cd /opt/camillagui/backend
source venv/bin/activate
python main.py &
sleep 2
curl http://localhost:5005/api/status
# Debe responder con JSON (o error de conexión a CamillaDSP, que es normal si no está corriendo)
kill %1
deactivate
```

---

### Paso 4 — Instalar el frontend web

```bash
# El frontend debe copiarse al subdirectorio gui/ del backend
# El backend lo sirve automáticamente como archivos estáticos

# Opción A: clonar directamente en gui/
git clone https://github.com/aasayag-hash/new_camilla_gui_fontend.git /opt/camillagui/backend/gui

# Opción B: copiar manualmente desde un directorio local
cp -r /ruta/al/frontend /opt/camillagui/backend/gui

# Verificar
ls /opt/camillagui/backend/gui/index.html
ls /opt/camillagui/backend/gui/js/
ls /opt/camillagui/backend/gui/style/
```

---

### Paso 5 — Configurar CamillaDSP

#### Crear directorios de configuración

```bash
sudo mkdir -p /etc/camilladsp/configs
sudo mkdir -p /etc/camilladsp/coeffs
sudo chown -R $USER:$USER /etc/camilladsp
```

#### Crear configuración por defecto

Ajustar `device` según el resultado de `aplay -l` y `arecord -l`:

```bash
# Ver dispositivos de reproducción disponibles
aplay -l

# Ver dispositivos de captura disponibles
arecord -l
```

Crear `/etc/camilladsp/configs/default.yml`:

```yaml
---
devices:
  samplerate: 48000
  chunksize: 1024
  queuelimit: 4
  capture:
    type: Alsa
    channels: 2
    format: S32LE
    device: "hw:0,0"        # Cambiar según tu hardware (ver arecord -l)
  playback:
    type: Alsa
    channels: 2
    format: S32LE
    device: "hw:0,0"        # Cambiar según tu hardware (ver aplay -l)

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

#### Identificar el dispositivo de audio correcto

```bash
# Listar todos los dispositivos de reproducción
aplay -l
# Ejemplo de salida:
# card 0: PCH [HDA Intel PCH], device 0: ALC887 Analog
#   → usar device: "hw:0,0"
# card 1: USB [USB Audio Device], device 0:
#   → usar device: "hw:1,0"

# Probar reproducción (tono de prueba)
aplay -D hw:0,0 /usr/share/sounds/alsa/Front_Left.wav

# Para DAC USB:
aplay -D hw:1,0 /usr/share/sounds/alsa/Front_Left.wav
```

#### Configuración para DAC USB (muy común en RPi)

```yaml
devices:
  samplerate: 44100        # o 48000, según tu DAC
  chunksize: 1024
  capture:
    type: Alsa
    channels: 2
    format: S16LE           # DACs USB suelen usar S16LE o S24LE
    device: "hw:1,0"        # Ajustar según arecord -l
  playback:
    type: Alsa
    channels: 2
    format: S16LE
    device: "hw:1,0"        # Ajustar según aplay -l
```

---

### Paso 6 — Iniciar los servicios

#### Arranque manual (para pruebas)

Abrir **dos terminales** en el servidor:

**Terminal 1 — CamillaDSP:**
```bash
camilladsp -a 0.0.0.0 -p 1234 -w /etc/camilladsp/configs/default.yml
```

**Terminal 2 — Backend + Frontend:**
```bash
cd /opt/camillagui/backend
source venv/bin/activate
python main.py
```

Si todo está bien, verás en Terminal 2:
```
INFO  CamillaGUI backend starting
INFO  Connecting to CamillaDSP at localhost:1234
INFO  Serving GUI on http://0.0.0.0:5005
```

Abrir en el navegador: `http://IP_DEL_SERVIDOR:5005`

---

## Auto-inicio con systemd

Una vez verificado que todo funciona en modo manual, configurar el inicio automático:

### Crear servicio para CamillaDSP

```bash
sudo tee /etc/systemd/system/camilladsp-engine.service << 'EOF'
[Unit]
Description=CamillaDSP Audio Processor
After=sound.target
Wants=sound.target

[Service]
Type=simple
User=pi
Group=audio
ExecStart=/usr/local/bin/camilladsp -a 0.0.0.0 -p 1234 -w /etc/camilladsp/configs/default.yml
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

> Reemplazar `User=pi` por tu usuario real (usar `whoami` para verlo).  
> El flag `-w` hace que CamillaDSP espere la conexión WebSocket del backend antes de procesar audio.

### Crear servicio para el backend

```bash
# Determinar el usuario actual
CURRENT_USER=$(whoami)

sudo tee /etc/systemd/system/camillagui.service << EOF
[Unit]
Description=CamillaGUI Web Backend
After=network-online.target camilladsp-engine.service
Wants=network-online.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=/opt/camillagui/backend
ExecStart=/opt/camillagui/backend/venv/bin/python main.py
Restart=on-failure
RestartSec=5
Environment="PYTHONUNBUFFERED=1"
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### Activar y gestionar los servicios

```bash
# Recargar configuración de systemd
sudo systemctl daemon-reload

# Habilitar inicio automático al arrancar
sudo systemctl enable camilladsp-engine.service
sudo systemctl enable camillagui.service

# Iniciar ahora
sudo systemctl start camilladsp-engine-engine.service
sudo systemctl start camillagui.service

# Verificar estado
sudo systemctl status camilladsp-engine-engine
sudo systemctl status camillagui
```

### Comandos de gestión diaria

```bash
# Iniciar ambos servicios
sudo systemctl start camilladsp-engine-engine camillagui

# Detener ambos servicios
sudo systemctl stop camillagui camilladsp-engine

# Reiniciar solo el backend (después de cambiar configuración)
sudo systemctl restart camillagui

# Reiniciar el motor DSP (después de cambiar hardware de audio)
sudo systemctl restart camilladsp-engine

# Ver logs en tiempo real
sudo journalctl -u camilladsp-engine -f
sudo journalctl -u camillagui -f

# Ver los últimos 50 mensajes de log
sudo journalctl -u camilladsp-engine -n 50
sudo journalctl -u camillagui -n 50

# Deshabilitar inicio automático
sudo systemctl disable camilladsp-engine camillagui
```

---

## Forma de conexión

### Escenario 1 — Acceso desde la misma máquina

Si el servidor y el navegador están en el mismo equipo:

```
URL: http://localhost:5005
IP en el campo login: localhost  (o 127.0.0.1)
Puerto: 5005
```

### Escenario 2 — Acceso desde la red local (LAN)

El caso más habitual: el servidor es una Raspberry Pi o PC dedicado, y accedes desde un teléfono, tablet o laptop en la misma red Wi-Fi.

**1. Encontrar la IP del servidor:**

```bash
# En el servidor, ejecutar:
hostname -I
# Ejemplo de salida: 192.168.1.45 (la primera IP es la que necesitas)

# Alternativa más detallada:
ip addr show | grep "inet " | grep -v "127.0.0.1"
```

**2. Abrir en el navegador:**
```
http://192.168.1.45:5005
```

**3. En la pantalla de login:**
```
IP Servidor:  192.168.1.45
Puerto:       5005
```

> La IP y puerto se guardan automáticamente en el navegador para la próxima visita.

### Escenario 3 — IP fija (recomendado para uso permanente)

Para que la IP del servidor no cambie entre reinicios, configurar IP estática:

**En Raspberry Pi OS (con NetworkManager):**
```bash
# Ver el nombre de la interfaz de red
nmcli device status

# Configurar IP estática (ajustar valores según tu red)
sudo nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.1.100/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "8.8.8.8,8.8.4.4" \
  ipv4.method manual

sudo nmcli connection up "Wired connection 1"
```

**En Raspberry Pi OS (dhcpcd — versiones antiguas):**

Editar `/etc/dhcpcd.conf` y añadir al final:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
```

**En Ubuntu (Netplan):**

Editar `/etc/netplan/01-netcfg.yaml`:
```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
      addresses: [192.168.1.100/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
```
```bash
sudo netplan apply
```

### Escenario 4 — Acceso por nombre de host (mDNS)

En lugar de recordar la IP, usa el nombre del host:

```bash
# En el servidor, ver el hostname
hostname
# Ejemplo: raspberrypi

# Instalar avahi para mDNS (normalmente ya está en RPi OS)
sudo apt-get install -y avahi-daemon
sudo systemctl enable --now avahi-daemon
```

Desde el navegador en la misma red:
```
http://raspberrypi.local:5005
```

En el campo IP del login:
```
IP Servidor:  raspberrypi.local
Puerto:       5005
```

### Escenario 5 — Abrir el puerto en el firewall

Si el servidor tiene firewall activo (UFW en Ubuntu/Debian):

```bash
# Ver estado del firewall
sudo ufw status

# Abrir puerto 5005
sudo ufw allow 5005/tcp

# Si también necesitas acceso al puerto de CamillaDSP desde fuera:
sudo ufw allow 1234/tcp

# Aplicar cambios
sudo ufw reload
sudo ufw status verbose
```

Con `firewalld` (Fedora / RHEL):
```bash
sudo firewall-cmd --permanent --add-port=5005/tcp
sudo firewall-cmd --reload
```

### Escenario 6 — Acceso remoto por Internet (avanzado)

Para acceder desde fuera de tu red local se recomienda usar un **túnel SSH** en lugar de abrir puertos directamente en el router:

```bash
# Desde el cliente externo, crear túnel SSH
ssh -L 5005:localhost:5005 usuario@IP_PUBLICA_DEL_SERVIDOR

# Luego en el navegador del cliente:
# http://localhost:5005
```

---

## Guía de uso

### Pantalla de Login

```
┌─────────────────────────────────────────┐
│  CAMILLADSP MASTER CONSOLE              │
│                                         │
│  IP Servidor: [192.168.1.45         ]   │
│  Puerto:      [5005                 ]   │
│                                         │
│  [  CONECTAR A HARDWARE  ]              │
│                                         │
│  [EN/ES]  [AYUDA]  [RESET]              │
│                                         │
│  ✓ Conectado a http://192.168.1.45:5005 │
└─────────────────────────────────────────┘
```

1. Ingresar la IP del servidor (o `localhost` si es la misma máquina)
2. Ingresar el puerto del backend (por defecto `5005`)
3. Click en **CONECTAR A HARDWARE**
4. Si la conexión es exitosa, se abre la consola principal

> La IP y puerto se recuerdan automáticamente para la próxima vez.

### Botones superiores (app)

| Botón | Función |
|-------|---------|
| **WEB** | Abre la interfaz web original del backend en nueva pestaña |
| **Imp Cfg** | Importa configuración completa desde archivo YAML o JSON |
| **Exp Cfg** | Exporta la configuración actual como archivo YAML |
| **Imp EQ** | Importa filtros en formato REW / APO |
| **Exp EQ** | Exporta los filtros EQ actuales como texto |
| **Reset** | Envía configuración vacía (pide número de canales) |
| **Log** | Abre consola con el log de CamillaDSP |
| **Ayuda** | Abre el manual de usuario integrado |
| **EN/ES** | Cambia el idioma de la interfaz |

### Panel de canales (izquierda)

El panel izquierdo muestra todos los canales IN y OUT de la configuración actual.

| Acción | Resultado |
|--------|-----------|
| Click en un canal | Activa / desactiva su visibilidad en los gráficos |
| Click derecho en un canal | Activa / desactiva bypass de EQ para ese canal |
| Click en ALL IN | Selecciona o deselecciona todos los canales de entrada |
| Click en ALL OUT | Selecciona o deselecciona todos los canales de salida |

> El canal con bypass aparece tachado. Los gráficos EQ no muestran su curva.

### Tab VU Meters

| Acción | Resultado |
|--------|-----------|
| Click en nombre de salida | Mute / unmute de ese canal |
| Arrastrar fader verticalmente | Ajusta ganancia −30 a +10 dB |
| Rueda del mouse sobre fader | Ajuste fino ±0.5 dB |
| Click derecho sobre fader | Reset a 0 dB |
| Click derecho sobre input delay | Reset delay a 0 ms |
| Doble-click en barra VU (salida) | Crea compresor con threshold en ese nivel |
| Click derecho en barra VU (salida) | Elimina el compresor de ese canal |
| Botón +/− junto al canal | Invierte la polaridad |
| MUTE ALL | Silencia / restaura todas las salidas |

### Tab EQ

| Acción | Resultado |
|--------|-----------|
| Doble-click en área vacía del gráfico | Crea filtro Peaking en canales seleccionados |
| Click y arrastrar punto de filtro | Mueve frecuencia (horizontal) y ganancia (vertical) |
| Rueda del mouse sobre punto | Ajusta el factor Q (ancho de banda) |
| Click derecho sobre punto | Elimina el filtro |
| Editar campo en la tabla | Cambia el valor del parámetro |
| Selector Tipo en tabla | Cambia el tipo de filtro (Peaking, LP, HP, etc.) |
| Selector Canal en tabla | Reasigna el filtro a otro canal |
| Botón X en tabla | Elimina el filtro |

### Tab Crossovers

| Acción | Resultado |
|--------|-----------|
| Doble-click zona izquierda (< 1 kHz) | Crea filtro Lowpass |
| Doble-click zona derecha (> 1 kHz) | Crea filtro Highpass |
| Click y arrastrar punto | Mueve la frecuencia de corte |
| Rueda del mouse sobre punto | Cambia el orden: 2→4→6→8→10→12 |
| Click derecho sobre punto | Elimina el filtro |
| Rueda sobre badge de orden en tabla | Ajusta el orden sin usar el gráfico |

### Tab Mixer

| Acción | Resultado |
|--------|-----------|
| Click en celda vacía (+) | Crea conexión In → Out (ganancia 0 dB) |
| Click derecho en celda verde | Elimina la conexión |
| Doble-click en nombre de entrada | Renombra la entrada |
| Doble-click en nombre de salida | Renombra la salida |

> El color de la celda verde indica la ganancia: más intenso = más cercano a 0 dB.

---

## Configuración del backend

El archivo de configuración del backend es `/opt/camillagui/backend/config/camillagui.yml` (o el que indique tu instalación):

```yaml
---
# IP donde escucha el backend (0.0.0.0 = todas las interfaces)
camilla_host: 0.0.0.0

# Puerto donde CamillaDSP escucha WebSocket
camilla_port: 1234

# Puerto HTTP del frontend y la API
port: 5005

# Directorios de configuración y coeficientes FIR
config_dir: /etc/camilladsp/configs
coeff_dir:  /etc/camilladsp/coeffs

# Configuración activa al inicio
default_config: default.yml
active_config:  active.yml

# Permitir modificar la configuración activa desde la GUI
can_update_active_config: true

# SSL (opcional — para HTTPS)
ssl_certificate: null
ssl_private_key: null

# CORS (habilitar solo si accedes desde otro dominio/puerto)
# allow_cors: true
```

---

## Solución de problemas

### Problema: "Error al conectar" en la pantalla de login

**Síntomas:** Aparece mensaje rojo "Error al conectar con http://IP:5005"

**Diagnóstico paso a paso:**

```bash
# 1. Verificar que el backend está corriendo
sudo systemctl status camillagui
# Debe mostrar "active (running)"

# 2. Probar desde el mismo servidor
curl -s http://localhost:5005/api/status
# Respuesta esperada: JSON con niveles de audio o {}

# 3. Probar desde otro equipo en la misma red
curl -s http://192.168.1.45:5005/api/status

# 4. Verificar que el puerto 5005 está escuchando
ss -tlnp | grep 5005
# Debe aparecer: *:5005 o 0.0.0.0:5005

# 5. Verificar el firewall
sudo ufw status
# Si está activo y no hay regla para 5005:
sudo ufw allow 5005/tcp
```

**Causas comunes y soluciones:**

| Causa | Solución |
|-------|---------|
| Backend no está corriendo | `sudo systemctl start camillagui` |
| Puerto bloqueado por firewall | `sudo ufw allow 5005/tcp` |
| IP incorrecta en el login | Usar `hostname -I` en el servidor para obtener la IP real |
| Backend corriendo en otra IP | Revisar `camillagui.yml`, asegurar `camilla_host: 0.0.0.0` |
| Error en el arranque del backend | `sudo journalctl -u camillagui -n 50` para ver el error |

---

### Problema: Los VU meters no se mueven

**Síntomas:** La interfaz carga, pero los VU meters están quietos en −∞ o −60 dB.

```bash
# 1. Verificar que CamillaDSP está corriendo
sudo systemctl status camilladsp-engine
# Si no está corriendo:
sudo systemctl start camilladsp-engine
sudo journalctl -u camilladsp -n 30

# 2. Verificar conexión backend ↔ CamillaDSP
curl http://localhost:5005/api/status
# Si responde {} o con error de conexión, CamillaDSP no está accesible

# 3. Verificar que CamillaDSP puede abrir el dispositivo de audio
sudo journalctl -u camilladsp-engine -f
# Buscar errores como:
# "Failed to open device hw:0,0"
# "Device busy"
# "No such device"

# 4. Verificar dispositivos ALSA disponibles
aplay -l    # Dispositivos de reproducción
arecord -l  # Dispositivos de captura

# 5. Probar el dispositivo directamente
aplay -D hw:0,0 /usr/share/sounds/alsa/Front_Left.wav
```

**Causas comunes:**

| Causa | Solución |
|-------|---------|
| CamillaDSP no está corriendo | `sudo systemctl start camilladsp-engine` |

| Dispositivo ALSA incorrecto en default.yml | Corregir `device:` con el resultado de `aplay -l` |
| Dispositivo en uso por otro proceso | `fuser /dev/snd/*` para ver qué proceso lo usa |
| Usuario sin permisos de audio | `sudo usermod -aG audio $USER` y reiniciar sesión |
| Formato de audio no soportado | Cambiar `format: S32LE` a `S16LE` o `S24LE` |

---

### Problema: "device busy" — Dispositivo de audio ocupado

```bash
# Ver qué proceso está usando el dispositivo de audio
fuser /dev/snd/*
# Ejemplo de salida: /dev/snd/pcmC0D0p: 1234  ← PID del proceso

# Ver el nombre del proceso
ps -p 1234 -o comm=

# Si es pulseaudio o pipewire, pueden competir con ALSA directo
# Opción 1: Detener pulseaudio temporalmente
systemctl --user stop pulseaudio.socket pulseaudio.service

# Opción 2: Usar dispositivo "dmix" que permite compartir
# En default.yml cambiar:
#   device: "dmix:0,0"   # para reproducción
#   device: "dsnoop:0,0" # para captura
```

---

### Problema: No aparecen canales en el panel lateral

**Síntoma:** El panel izquierdo está vacío o no muestra ningún botón IN/OUT.

```bash
# Verificar la configuración activa
curl http://localhost:5005/api/getconfig | python3 -m json.tool | head -40

# La configuración debe tener devices con channels > 0
# Si la config está vacía o incompleta, usar Reset en la interfaz:
# Botón Reset → Ingresar número de entradas y salidas → Confirmar
```

**También puede ocurrir si:**
- La configuración YAML tiene errores de sintaxis — verificar con `camilladsp --verify /etc/camilladsp/configs/default.yml`
- El campo `channels` está en 0 — cambiarlo a 2 o más
- El mixer no tiene `channels.out` definido

---

### Problema: Error CORS en la consola del navegador

**Síntoma:** En la consola del navegador (F12) aparece:
```
Access to fetch at 'http://...' from origin 'http://...' has been blocked by CORS policy
```

Esto ocurre cuando el frontend no está siendo servido desde el mismo servidor/puerto que la API.

**Solución A (recomendada):** Siempre acceder a través del backend en puerto 5005, no abrir `index.html` como archivo local.

**Solución B:** Habilitar CORS en el backend:
```yaml
# En camillagui.yml
allow_cors: true
```
Luego reiniciar: `sudo systemctl restart camillagui`

---

### Problema: El frontend no carga o muestra página en blanco

```bash
# Verificar que index.html existe en el lugar correcto
ls -la /opt/camillagui/backend/gui/index.html

# Ver qué carpeta sirve el backend
grep -r "gui" /opt/camillagui/backend/*.py 2>/dev/null | head -5
grep -r "static" /opt/camillagui/backend/*.py 2>/dev/null | head -5

# Verificar permisos de los archivos
ls -la /opt/camillagui/backend/gui/

# Los archivos deben ser legibles (rw-r--r--)
# Si no lo son:
chmod -R 644 /opt/camillagui/backend/gui/
chmod 755 /opt/camillagui/backend/gui/
find /opt/camillagui/backend/gui/ -type d -exec chmod 755 {} \;
```

---

### Problema: Error en Python al iniciar el backend

```bash
# Ver el error completo
sudo journalctl -u camillagui -n 100

# Error común: módulo no encontrado
# "ModuleNotFoundError: No module named 'aiohttp'"
cd /opt/camillagui/backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart camillagui

# Error de versión de Python
python3 --version  # Debe ser 3.8+
which python3      # Verificar que el venv usa el Python correcto
```

---

### Problema: Raspberry Pi — El audio suena distorsionado o con crackles

```bash
# Aumentar el tamaño de buffer (chunksize) en default.yml
# Cambiar: chunksize: 1024 → chunksize: 2048 o 4096

# También verificar la carga del sistema
top
# Si la CPU está al 100%, aumentar chunksize o bajar samplerate

# Para DAC USB en RPi, a veces ayuda:
echo "options snd_usb_audio nrpacks=1" | sudo tee /etc/modprobe.d/snd-usb-audio.conf
sudo reboot
```

---

### Problema: La Raspberry Pi no arranca después de instalar

```bash
# Acceder por SSH desde otro equipo
ssh pi@192.168.1.45

# Ver errores de arranque
sudo journalctl -b -p err

# Si no hay SSH disponible, conectar teclado/monitor y ver mensajes de boot
# O acceder a la tarjeta SD desde otro equipo y revisar los logs en:
# /var/log/syslog
```

---

### Referencia rápida de comandos de diagnóstico

```bash
# Estado general del sistema
sudo systemctl status camilladsp-engine
sudo systemctl status camillagui

# Logs en tiempo real (ambos servicios)
sudo journalctl -u camilladsp -u camillagui -f

# Probar API
curl -s http://localhost:5005/api/status | python3 -m json.tool
curl -s http://localhost:5005/api/getconfig | python3 -m json.tool

# Dispositivos de audio
aplay -l && arecord -l
cat /proc/asound/cards

# Red y puertos
hostname -I
ss -tlnp | grep -E "5005|1234"
sudo ufw status

# Uso de recursos
top -b -n1 | head -20
df -h
free -h
```

---

## Cómo subir el proyecto a GitHub

El repositorio oficial es: **https://github.com/aasayag-hash/new_camilla_gui_fontend**

### Actualizar el repositorio existente (push de cambios)

```bash
cd "C:\Users\lenovo\Downloads\fir python\new_camilla_gui_fontend"

# Si es la primera vez, configurar el remote
git remote add origin https://github.com/aasayag-hash/new_camilla_gui_fontend.git
# Si ya existe el remote, omitir el comando anterior

git add .
git commit -m "Update: descripción del cambio"
git push origin main
# Username: aasayag-hash
# Password: PEGAR_TOKEN_PERSONAL (no la contraseña de GitHub)
```

### Cómo obtener el Personal Access Token (PAT)

GitHub no acepta contraseñas por HTTPS desde agosto 2021. Necesitas un token:

1. Ir a **github.com** → click en tu avatar → **Settings**
2. En el menú izquierdo, ir al final: **Developer settings**
3. **Personal access tokens** → **Tokens (classic)**
4. Click en **Generate new token (classic)**
5. Escribir un nombre (ej: "mi-pc"), marcar el scope **repo**, click **Generate token**
6. **Copiar el token inmediatamente** — solo se muestra una vez

### Alternativa: usar SSH (sin token)

```bash
# Generar clave SSH (si no tienes una)
ssh-keygen -t ed25519 -C "tu@email.com"

# Copiar la clave pública y agregarla en GitHub:
# github.com → Settings → SSH and GPG keys → New SSH key
cat ~/.ssh/id_ed25519.pub

# Verificar conexión
ssh -T git@github.com
# Respuesta: "Hi aasayag-hash! You've successfully authenticated..."

# Configurar remote SSH
git remote set-url origin git@github.com:aasayag-hash/new_camilla_gui_fontend.git
git push origin main
```

### Clonar en el servidor Linux

```bash
# Con HTTPS (pedirá usuario y token como contraseña)
git clone https://github.com/aasayag-hash/new_camilla_gui_fontend.git

# Con HTTPS embebiendo el token (sin preguntar)
git clone https://aasayag-hash:TOKEN@github.com/aasayag-hash/new_camilla_gui_fontend.git

# Con SSH (sin contraseña, si configuraste la clave)
git clone git@github.com:aasayag-hash/new_camilla_gui_fontend.git

# Instalar
cd new_camilla_gui_fontend
sudo bash install.sh
```

---

## Arquitectura del código

```
new_camilla_gui_fontend/
├── index.html                    # SPA — pantalla login + app (toggle display:none)
├── install.sh                    # Instalador bash multi-arquitectura
├── README.md                     # Esta documentación
├── style/
│   ├── base.css                  # Variables CSS dark theme, resets globales
│   ├── layout.css                # Login, app shell, tabs, channel panel
│   ├── vu.css                    # VU meters, faders, tabla compresores
│   ├── eq.css                    # Gráfico EQ, tabla de filtros
│   ├── crossover.css             # Gráfico crossover, tabla
│   ├── mixer.css                 # Matriz mixer
│   └── modal.css                 # Modales, consola, snackbar
└── js/
    ├── core/
    │   ├── api.js                # Todos los fetch() hacia el backend REST
    │   ├── events.js             # EventBus pub/sub global (on/off/emit)
    │   ├── i18n.js               # Traducciones ES/EN completas + help text
    │   ├── state.js              # Estado global: config_raw, patchConfig(), reloadConfig()
    │   └── utils.js              # GLOBAL_HEX_COLORS, cleanName, deepMerge, etc.
    ├── dsp/
    │   ├── biquad.js             # calcularMagnitudBiquad() — puerto exacto del Python
    │   └── crossover.js          # calcularMagnitudCrossover() — Butterworth / LR
    ├── ui/
    │   ├── login.js              # Pantalla login, localStorage IP/port, reset login
    │   ├── snack.js              # Toast/snackbar de notificaciones
    │   ├── channelPanel.js       # Panel lateral IN/OUT con bypass click-derecho
    │   ├── tabManager.js         # Cambio de tabs + visibilidad del channel panel
    │   └── cornerButtons.js      # WEB, Imp/Exp Config/EQ, Reset, Log, Ayuda
    ├── tabs/
    │   ├── vumeters/
    │   │   ├── vuCanvas.js       # Canvas VU: gradiente, peak hold, GR bar, threshold
    │   │   ├── fader.js          # Canvas fader -30/+10 dB con drag y rueda
    │   │   ├── polarity.js       # Botón +/- inversión de polaridad
    │   │   ├── delayInput.js     # Input delay ms con right-click reset
    │   │   ├── compressorTable.js# Tabla compresores + botón AUTO 5s sampling
    │   │   └── vuTab.js          # Orchestrator: polling, rebuild canales, mute
    │   ├── eq/
    │   │   ├── eqGraph.js        # Canvas EQ: grid, curvas, drag, wheel Q, create/delete
    │   │   ├── eqTable.js        # Tabla filtros editable con combos tipo/canal
    │   │   └── eqTab.js          # Orchestrator EQ
    │   ├── crossover/
    │   │   ├── crossGraph.js     # Canvas crossover: LP/HP, drag freq, wheel order
    │   │   ├── crossTable.js     # Tabla crossover con badge de orden
    │   │   └── crossTab.js       # Orchestrator crossover
    │   └── mixer/
    │       ├── mixerCanvas.js    # Canvas matriz routing: headers, celdas, click/right/dblclick
    │       └── mixerTab.js       # Orchestrator mixer
    └── init.js                   # Entry point: bootstrap, inicializa todos los módulos
```

---

## Compatibilidad

| Componente | Versión mínima | Notas |
|------------|---------------|-------|
| CamillaDSP | 2.0 | Para v1.x pueden requerirse ajustes en la API |
| camillagui-backend | 0.6+ | Requiere endpoint `/api/status` con niveles |
| Python | 3.8 | Para el backend |
| Chrome / Edge | 90+ | ES Modules + Canvas + ResizeObserver |
| Firefox | 88+ | |
| Safari | 14+ | |
| Opera | 76+ | |
| Navegadores móviles | Sí | Chrome/Firefox en Android, Safari en iOS 14+ |

---

## Diferencias con la app Python original

| Característica | App Python (PySide6) | Este frontend web |
|---|---|---|
| Instalación en cliente | Qt6 + Python en escritorio | Solo un navegador |
| Acceso remoto | No — solo local | Sí — cualquier dispositivo en la red |
| Multi-ventana | No | Sí — múltiples pestañas/navegadores |
| VU meters | 50 ms (QTimer) | 50 ms (setTimeout async) |
| Peak hold | 40 frames + 0.5 dB/frame | Idéntico |
| GR smoothing | attack=0.4, release=0.05 | Idéntico |
| Matemáticas biquad | `calcular_magnitud_biquad()` | Puerto JS exacto |
| Interfaz de audio | Qt/ALSA directo | Vía REST API del backend |
| Uso en dispositivos móviles | No | Sí |

---

## Licencia

MIT License — libre para uso personal y comercial, con o sin modificaciones.

---

## Créditos

- **CamillaDSP** — [Henrik Enquist](https://github.com/HEnquist/camilladsp): motor DSP de audio de alto rendimiento
- **camillagui-backend** — [Henrik Enquist](https://github.com/HEnquist/camillagui-backend): backend Python con API REST y WebSocket
- Este frontend web fue desarrollado como reemplazo multiplataforma accesible desde cualquier navegador
