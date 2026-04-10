#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# install.sh — Instalador CamillaDSP + camillagui-backend + frontend web
# Detecta: x86_64 / aarch64 (ARM64) / armv7l (Raspberry Pi 32-bit)
# Package managers: apt (Debian/Ubuntu/Raspbian), pacman (Arch), dnf (Fedora)
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Colores ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*" >&2; }
step()    { echo -e "\n${BOLD}${BLUE}══ $* ${NC}"; }

# ── Config por defecto ────────────────────────────────────────────────────────
INSTALL_DIR="/opt/camillagui"
BACKEND_DIR="$INSTALL_DIR/backend"
FRONTEND_DIR="$INSTALL_DIR/frontend"
CAMILLADSP_BIN="/usr/local/bin/camilladsp"
BACKEND_REPO="https://github.com/HEnquist/camillagui-backend.git"
CAMILLADSP_REPO="https://github.com/HEnquist/camilladsp"
SERVICE_USER="${SUDO_USER:-$(whoami)}"
PYTHON_MIN="3.8"

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║      CamillaDSP + GUI Web — Instalador v1.0       ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Verificar root ────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    error "Este script requiere privilegios de root. Ejecutar con: sudo $0"
    exit 1
fi

# ── Detectar arquitectura ─────────────────────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
    x86_64)  ARCH_NAME="x86_64";  ARCH_LABEL="Intel/AMD 64-bit" ;;
    aarch64) ARCH_NAME="aarch64"; ARCH_LABEL="ARM64 (Raspberry Pi 4/5, Apple M1...)" ;;
    armv7l)  ARCH_NAME="armv7";   ARCH_LABEL="ARMv7 32-bit (Raspberry Pi 3...)" ;;
    armv6l)  ARCH_NAME="armv6";   ARCH_LABEL="ARMv6 (Raspberry Pi 1/Zero)" ;;
    *)
        warn "Arquitectura '$ARCH' no reconocida. Se intentará compilar desde fuente."
        ARCH_NAME="unknown"
        ARCH_LABEL="Desconocida"
        ;;
esac
info "Arquitectura detectada: $ARCH_NAME ($ARCH_LABEL)"

# ── Detectar distribución y package manager ───────────────────────────────────
detect_pkg_manager() {
    if command -v apt-get &>/dev/null; then
        PKG_MGR="apt"
        PKG_UPDATE="apt-get update -qq"
        PKG_INSTALL="apt-get install -y -qq"
        PKG_DEPS="python3 python3-pip python3-venv git curl wget alsa-utils"
    elif command -v pacman &>/dev/null; then
        PKG_MGR="pacman"
        PKG_UPDATE="pacman -Sy --noconfirm"
        PKG_INSTALL="pacman -S --noconfirm --needed"
        PKG_DEPS="python python-pip git curl wget alsa-utils"
    elif command -v dnf &>/dev/null; then
        PKG_MGR="dnf"
        PKG_UPDATE="dnf check-update || true"
        PKG_INSTALL="dnf install -y -q"
        PKG_DEPS="python3 python3-pip git curl wget alsa-utils"
    elif command -v yum &>/dev/null; then
        PKG_MGR="yum"
        PKG_UPDATE="yum check-update || true"
        PKG_INSTALL="yum install -y -q"
        PKG_DEPS="python3 python3-pip git curl wget alsa-utils"
    else
        error "No se encontró gestor de paquetes compatible (apt/pacman/dnf/yum)."
        exit 1
    fi
    info "Gestor de paquetes: $PKG_MGR"
}
detect_pkg_manager

# ── Versiones CamillaDSP disponibles ─────────────────────────────────────────
# URLs de releases en GitHub — ajustar a la versión estable más reciente
CDSP_VERSION="2.1.0"
BASE_URL="https://github.com/HEnquist/camilladsp/releases/download/v${CDSP_VERSION}"

case "$ARCH_NAME" in
    x86_64)  CDSP_URL="${BASE_URL}/camilladsp-linux-x86_64.tar.gz" ;;
    aarch64) CDSP_URL="${BASE_URL}/camilladsp-linux-aarch64.tar.gz" ;;
    armv7)   CDSP_URL="${BASE_URL}/camilladsp-linux-armv7.tar.gz" ;;
    armv6)   CDSP_URL="${BASE_URL}/camilladsp-linux-armv6.tar.gz" ;;
    *)       CDSP_URL="" ;;
esac

# ── Preguntar opciones ────────────────────────────────────────────────────────
echo ""
read -rp "Directorio de instalación [${INSTALL_DIR}]: " INPUT_DIR
[[ -n "$INPUT_DIR" ]] && INSTALL_DIR="$INPUT_DIR" && BACKEND_DIR="$INSTALL_DIR/backend" && FRONTEND_DIR="$INSTALL_DIR/frontend"

read -rp "¿Instalar CamillaDSP binary? [S/n]: " INSTALL_CDSP
INSTALL_CDSP="${INSTALL_CDSP:-S}"

read -rp "¿Crear servicio systemd? [S/n]: " CREATE_SERVICE
CREATE_SERVICE="${CREATE_SERVICE:-S}"

read -rp "¿Puerto del backend GUI? [5005]: " GUI_PORT
GUI_PORT="${GUI_PORT:-5005}"

echo ""
info "Configuración:"
info "  Directorio:    $INSTALL_DIR"
info "  CamillaDSP:    $(echo $INSTALL_CDSP | tr '[:lower:]' '[:upper:]')"
info "  Servicio:      $(echo $CREATE_SERVICE | tr '[:lower:]' '[:upper:]')"
info "  Puerto GUI:    $GUI_PORT"
echo ""
read -rp "¿Continuar? [S/n]: " CONFIRM
[[ "${CONFIRM:-S}" =~ ^[Nn] ]] && echo "Cancelado." && exit 0

# ══════════════════════════════════════════════════════════════════════════════
step "1/6 — Instalando dependencias del sistema"
# ══════════════════════════════════════════════════════════════════════════════
info "Actualizando repositorios..."
eval "$PKG_UPDATE" 2>&1 | tail -5 || true

info "Instalando paquetes: $PKG_DEPS"
eval "$PKG_INSTALL $PKG_DEPS"
success "Dependencias instaladas"

# ══════════════════════════════════════════════════════════════════════════════
step "2/6 — Instalando CamillaDSP"
# ══════════════════════════════════════════════════════════════════════════════
if [[ "${INSTALL_CDSP^^}" != "N" ]]; then
    if [[ -n "$CDSP_URL" ]]; then
        info "Descargando CamillaDSP v${CDSP_VERSION} para ${ARCH_NAME}..."
        TMP_DIR=$(mktemp -d)
        cd "$TMP_DIR"
        if wget -q --show-progress "$CDSP_URL" -O camilladsp.tar.gz 2>&1; then
            tar xzf camilladsp.tar.gz
            CDSP_BIN=$(find . -name "camilladsp" -type f | head -1)
            if [[ -n "$CDSP_BIN" ]]; then
                install -m 755 "$CDSP_BIN" "$CAMILLADSP_BIN"
                success "CamillaDSP instalado en $CAMILLADSP_BIN"
            else
                warn "No se encontró binario en el archivo. Verificar manualmente."
            fi
        else
            warn "No se pudo descargar el binario precompilado."
            warn "Descarga manual desde: $CDSP_REPO/releases"
        fi
        rm -rf "$TMP_DIR"
    else
        warn "No hay binario precompilado para $ARCH_NAME."
        warn "Compilar manualmente: $CDSP_REPO"
    fi

    # Verificar
    if command -v camilladsp &>/dev/null; then
        CDSP_VER=$(camilladsp --version 2>&1 | head -1 || echo "desconocida")
        success "CamillaDSP: $CDSP_VER"
    fi
else
    info "Instalación de CamillaDSP omitida."
fi

# ══════════════════════════════════════════════════════════════════════════════
step "3/6 — Instalando camillagui-backend"
# ══════════════════════════════════════════════════════════════════════════════
mkdir -p "$INSTALL_DIR"

if [[ -d "$BACKEND_DIR/.git" ]]; then
    info "Backend ya existe, actualizando..."
    cd "$BACKEND_DIR"
    git pull --ff-only 2>&1 | tail -3 || true
else
    info "Clonando camillagui-backend..."
    git clone --depth=1 "$BACKEND_REPO" "$BACKEND_DIR"
fi
success "Backend en $BACKEND_DIR"

# Entorno virtual Python
info "Creando entorno virtual Python..."
cd "$BACKEND_DIR"
python3 -m venv venv
source venv/bin/activate

info "Instalando dependencias Python..."
pip install --quiet --upgrade pip
if [[ -f requirements.txt ]]; then
    pip install --quiet -r requirements.txt
else
    pip install --quiet aiohttp coloredlogs pycamilladsp pyyaml
fi
deactivate
success "Dependencias Python instaladas"

# ══════════════════════════════════════════════════════════════════════════════
step "4/6 — Instalando frontend web"
# ══════════════════════════════════════════════════════════════════════════════
# Determinar directorio GUI del backend
GUI_DEST="$BACKEND_DIR/gui"
mkdir -p "$GUI_DEST"

# Copiar archivos del frontend (directorio del script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
info "Copiando frontend desde $SCRIPT_DIR a $GUI_DEST..."

rsync -a --exclude='.git' --exclude='.claude' --exclude='install.sh' \
    "$SCRIPT_DIR/" "$GUI_DEST/" 2>/dev/null \
    || cp -r "$SCRIPT_DIR"/* "$GUI_DEST/" 2>/dev/null \
    || true

success "Frontend copiado a $GUI_DEST"

# ══════════════════════════════════════════════════════════════════════════════
step "5/6 — Configurando backend"
# ══════════════════════════════════════════════════════════════════════════════
# Crear/actualizar config del backend si no existe
BACKEND_CFG="$BACKEND_DIR/config/camillagui.yml"
mkdir -p "$(dirname "$BACKEND_CFG")"

if [[ ! -f "$BACKEND_CFG" ]]; then
    info "Creando configuración básica del backend..."
    cat > "$BACKEND_CFG" << EOF
---
camilla_host: 0.0.0.0
camilla_port: 1234
port: ${GUI_PORT}
ssl_certificate: null
ssl_private_key: null
config_dir: /etc/camilladsp/configs
coeff_dir: /etc/camilladsp/coeffs
default_config: default.yml
active_config: active.yml
can_update_active_config: true
supported_capture_types: null
supported_playback_types: null
EOF
    success "Configuración backend creada: $BACKEND_CFG"
else
    info "Configuración del backend ya existe, no se sobreescribe."
fi

# Directorio de configs de CamillaDSP
mkdir -p /etc/camilladsp/configs /etc/camilladsp/coeffs

# Config por defecto si no existe
DEFAULT_CFG="/etc/camilladsp/configs/default.yml"
if [[ ! -f "$DEFAULT_CFG" ]]; then
    cat > "$DEFAULT_CFG" << 'EOF'
---
devices:
  samplerate: 48000
  chunksize: 1024
  queuelimit: 4
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
EOF
    success "Configuración por defecto creada: $DEFAULT_CFG"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "6/6 — Servicio systemd"
# ══════════════════════════════════════════════════════════════════════════════
if [[ "${CREATE_SERVICE^^}" != "N" ]] && command -v systemctl &>/dev/null; then

    # Servicio camilladsp
    cat > /etc/systemd/system/camilladsp.service << EOF
[Unit]
Description=CamillaDSP Audio Processor
After=sound.target

[Service]
Type=simple
User=$SERVICE_USER
ExecStart=$CAMILLADSP_BIN -p 1234 -a 0.0.0.0 $DEFAULT_CFG
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Servicio camillagui-backend
    cat > /etc/systemd/system/camillagui.service << EOF
[Unit]
Description=CamillaGUI Web Backend
After=network.target camilladsp.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$BACKEND_DIR
ExecStart=$BACKEND_DIR/venv/bin/python $BACKEND_DIR/main.py
Restart=on-failure
RestartSec=5
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable camillagui.service || true
    systemctl enable camilladsp.service || true
    success "Servicios systemd creados y habilitados"
    info "Para iniciar ahora: sudo systemctl start camilladsp camillagui"
else
    info "Servicio systemd omitido."
    info "Para iniciar manualmente:"
    info "  cd $BACKEND_DIR && source venv/bin/activate && python main.py"
fi

# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}${GREEN}════════════════════════════════════════"
echo "  Instalación completada correctamente"
echo -e "════════════════════════════════════════${NC}"
echo ""
info "Acceder a la interfaz web:"
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
echo -e "  ${BOLD}http://${LOCAL_IP}:${GUI_PORT}${NC}"
echo ""
info "Conectar con IP del servidor CamillaDSP y puerto 1234"
echo ""

# Resumen
if command -v systemctl &>/dev/null && systemctl is-enabled camillagui.service &>/dev/null; then
    echo -e "Comandos útiles:"
    echo "  sudo systemctl start   camilladsp camillagui"
    echo "  sudo systemctl stop    camilladsp camillagui"
    echo "  sudo systemctl status  camillagui"
    echo "  sudo journalctl -u camillagui -f"
fi
