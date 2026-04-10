#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# install.sh — Instalador CamillaDSP + camillagui-backend + frontend web
# Detecta: x86_64 / aarch64 (ARM64) / armv7l (Raspberry Pi 32-bit)
# Package managers: apt (Debian/Ubuntu/Raspbian), pacman (Arch), dnf (Fedora)
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

git config --global advice.detachedHead false

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
FRONTEND_REPO="https://github.com/aasayag-hash/new_camilla_gui_fontend.git"
CAMILLADSP_REPO="https://github.com/HEnquist/camilladsp"
SERVICE_USER="${SUDO_USER:-$(whoami)}"
PYTHON_MIN="3.8"

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║      CamillaDSP + GUI Web — Instalador v1.0       ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Verificar si existe instalación previa ─────────────────────────────────────
if [[ -d "$INSTALL_DIR" ]]; then
    warn "Ya existe una instalación en: $INSTALL_DIR"
    echo ""
    echo "Para desinstalar manualmente, ejecuta:"
    echo "  sudo systemctl stop camilladsp-engine camillagui 2>/dev/null || true"
    echo "  sudo systemctl disable camilladsp-engine camillagui 2>/dev/null || true"
    echo "  sudo rm -f /etc/systemd/system/camilladsp-engine.service /etc/systemd/system/camillagui.service"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo rm -rf $INSTALL_DIR"
    echo ""
    read -rp "¿Desea eliminar la instalación existente y hacer una instalación limpia? [s/N]: " CLEAN_INSTALL
    if [[ "${CLEAN_INSTALL^^}" == "S" ]]; then
        info "Deteniendo servicios..."
        systemctl stop camilladsp-engine camillagui 2>/dev/null || true
        info "Eliminando instalación anterior..."
        rm -rf "$INSTALL_DIR"
    else
        info "Actualizando instalación existente..."
    fi
    echo ""
fi

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

# ── Auto-detectar última versión de CamillaDSP desde GitHub API ──────────────
CDSP_API="https://api.github.com/repos/HEnquist/camilladsp/releases/latest"
CDSP_VERSION=""
CDSP_URL=""

# ── Auto-detectar última versión de camillagui-backend desde GitHub API ───────
BACKEND_API="https://api.github.com/repos/HEnquist/camillagui-backend/releases/latest"
BACKEND_VERSION=""
BACKEND_TAG=""

_fetch() {
    # Intenta con curl primero, luego wget
    if command -v curl &>/dev/null; then
        curl -sfL "$1"
    elif command -v wget &>/dev/null; then
        wget -qO- "$1"
    fi
}

_detect_cdsp_release() {
    info "Consultando última versión en GitHub..."
    local json
    json=$(_fetch "$CDSP_API") || true

    if [[ -z "$json" ]]; then
        warn "No se pudo consultar la API de GitHub. Verificar conexión a internet."
        return 1
    fi

    # Extraer tag_name (ej: "v2.0.3")
    CDSP_VERSION=$(echo "$json" | grep '"tag_name"' \
        | sed 's/.*"tag_name"[[:space:]]*:[[:space:]]*"v\([^"]*\)".*/\1/' \
        | head -1)

    if [[ -z "$CDSP_VERSION" ]]; then
        warn "No se pudo determinar la versión. Respuesta de la API inesperada."
        return 1
    fi

    info "Última versión disponible: v${CDSP_VERSION}"

    # Buscar la URL del asset según arquitectura
    # Los assets de CamillaDSP siguen el patrón: camilladsp-vX.Y.Z-ARCH-TARGET.tar.gz
    local arch_pattern
    case "$ARCH_NAME" in
        x86_64)  arch_pattern="x86_64" ;;
        aarch64) arch_pattern="aarch64" ;;
        armv7)   arch_pattern="armv7" ;;
        armv6)   arch_pattern="armv6" ;;
        *)       arch_pattern="" ;;
    esac

    if [[ -z "$arch_pattern" ]]; then
        warn "No hay binario precompilado para $ARCH_NAME."
        return 1
    fi

    CDSP_URL=$(echo "$json" \
        | grep '"browser_download_url"' \
        | grep "$arch_pattern" \
        | grep '\.tar\.gz' \
        | sed 's/.*"browser_download_url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' \
        | head -1)

    if [[ -z "$CDSP_URL" ]]; then
        warn "No se encontró asset para arquitectura '$arch_pattern' en v${CDSP_VERSION}."
        # Listar assets disponibles para ayudar al diagnóstico
        info "Assets disponibles en esta release:"
        echo "$json" | grep '"browser_download_url"' \
            | sed 's/.*"browser_download_url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/  \1/' \
            | head -20
        return 1
    fi

    info "URL del binario: $CDSP_URL"
    return 0
}

_detect_cdsp_release || true

# ── Auto-detectar última versión de camillagui-backend ───────────────────────
_detect_backend_release() {
    info "Consultando última versión de camillagui-backend en GitHub..."
    local json
    json=$(_fetch "$BACKEND_API") || true

    if [[ -z "$json" ]]; then
        warn "No se pudo consultar la API de GitHub para el backend."
        return 1
    fi

    BACKEND_TAG=$(echo "$json" \
        | grep '"tag_name"' \
        | sed 's/.*"tag_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' \
        | head -1)

    if [[ -z "$BACKEND_TAG" ]]; then
        warn "No se pudo determinar la versión del backend. Se usará la rama principal."
        return 1
    fi

    BACKEND_VERSION="$BACKEND_TAG"
    info "Última versión de camillagui-backend: $BACKEND_TAG"
    return 0
}

_detect_backend_release || true

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
info "  CamillaDSP:    $(echo $INSTALL_CDSP | tr '[:lower:]' '[:upper:]')${CDSP_VERSION:+ (v${CDSP_VERSION})}"
info "  Backend GUI:   ${BACKEND_TAG:-rama principal (sin releases detectados)}"
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
            warn "Descarga manual desde: $CAMILLADSP_REPO/releases"
        fi
        rm -rf "$TMP_DIR"
    else
        warn "No hay binario precompilado para $ARCH_NAME."
        warn "Compilar manualmente: $CAMILLADSP_REPO"
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
    warn "El directorio del backend ya existe: $BACKEND_DIR"
    read -rp "¿Desea eliminarlo y hacer una instalación limpia? [s/N]: " CLEAN_INSTALL
    if [[ "${CLEAN_INSTALL^^}" == "S" ]]; then
        info "Eliminando instalación anterior..."
        rm -rf "$BACKEND_DIR"
    else
        info "Actualizando instalación existente..."
        cd "$BACKEND_DIR"
        git fetch --tags 2>&1 | tail -3 || true
        if [[ -n "$BACKEND_TAG" ]]; then
            info "Cambiando a versión $BACKEND_TAG..."
            git checkout "$BACKEND_TAG" 2>&1 | tail -3 \
                || git pull --ff-only 2>&1 | tail -3 || true
        else
            git pull --ff-only 2>&1 | tail -3 || true
        fi
    fi
fi

if [[ ! -d "$BACKEND_DIR/.git" ]]; then
    if [[ -n "$BACKEND_TAG" ]]; then
        info "Clonando camillagui-backend $BACKEND_TAG..."
        git clone --depth=1 --branch "$BACKEND_TAG" "$BACKEND_REPO" "$BACKEND_DIR"
    else
        info "Clonando camillagui-backend (rama principal)..."
        git clone --depth=1 "$BACKEND_REPO" "$BACKEND_DIR"
    fi
fi
success "Backend en $BACKEND_DIR${BACKEND_TAG:+ — versión $BACKEND_TAG}"

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
    pip install --quiet aiohttp coloredlogs pyyaml websocket-client git+https://github.com/HEnquist/pycamilladsp.git
fi
deactivate
success "Dependencias Python instaladas"

# ══════════════════════════════════════════════════════════════════════════════
step "4/6 — Instalando frontend web"
# ══════════════════════════════════════════════════════════════════════════════
GUI_DEST="$BACKEND_DIR/gui"
mkdir -p "$GUI_DEST"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Detectar si el script se ejecuta desde dentro del repositorio clonado
# (existe index.html en el mismo directorio del script)
if [[ -f "$SCRIPT_DIR/index.html" ]]; then
    info "Copiando frontend desde $SCRIPT_DIR a $GUI_DEST..."
    if command -v rsync &>/dev/null; then
        rsync -a --exclude='.git' --exclude='.claude' --exclude='install.sh' \
            "$SCRIPT_DIR/" "$GUI_DEST/"
    else
        cp -r "$SCRIPT_DIR"/index.html "$GUI_DEST/"
        cp -r "$SCRIPT_DIR"/js         "$GUI_DEST/"
        cp -r "$SCRIPT_DIR"/style      "$GUI_DEST/"
        [[ -d "$SCRIPT_DIR/assets" ]] && cp -r "$SCRIPT_DIR"/assets "$GUI_DEST/"
    fi
    success "Frontend copiado a $GUI_DEST"
else
    # El script se ejecutó desde un directorio diferente — clonar desde GitHub
    info "Clonando frontend desde $FRONTEND_REPO..."
    if [[ -d "$GUI_DEST/.git" ]]; then
        info "Frontend ya existe, actualizando..."
        cd "$GUI_DEST"
        git pull --ff-only 2>&1 | tail -3 || true
    else
        git clone --depth=1 "$FRONTEND_REPO" "$GUI_DEST"
    fi
    success "Frontend instalado en $GUI_DEST"
fi

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
description: default
devices:
  adjust_period: null
  capture:
    channels: 2
    device: 'null'
    format: null
    labels: null
    link_mute_control: null
    link_volume_control: null
    stop_on_inactive: null
    type: Alsa
  capture_samplerate: 48000
  chunksize: 1024
  enable_rate_adjust: null
  multithreaded: null
  playback:
    channels: 2
    device: 'null'
    format: null
    type: Alsa
  queuelimit: null
  rate_measure_interval: null
  resampler: null
  samplerate: 48000
  silence_threshold: null
  silence_timeout: null
  stop_on_rate_change: null
  target_level: null
  volume_limit: null
  volume_ramp_time: null
  worker_threads: null
filters: {}
mixers:
  Unnamed Mixer 1:
    channels:
      in: 2
      out: 2
    description: null
    labels: null
    mapping: []
pipeline: []
processors: {}
title: default
EOF
    success "Configuración por defecto creada: $DEFAULT_CFG"
fi

ACTIVE_CFG="/etc/camilladsp/configs/active.yml"
if [[ ! -f "$ACTIVE_CFG" ]]; then
    cp "$DEFAULT_CFG" "$ACTIVE_CFG"
    success "Configuración activa creada: $ACTIVE_CFG"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "6/6 — Servicio systemd"
# ══════════════════════════════════════════════════════════════════════════════
if [[ "${CREATE_SERVICE^^}" != "N" ]] && command -v systemctl &>/dev/null; then

    # Servicio camilladsp-engine
    cat > /etc/systemd/system/camilladsp-engine.service << EOF
[Unit]
Description=CamillaDSP Audio Processor
After=sound.target

[Service]
Type=simple
User=$SERVICE_USER
ExecStart=$CAMILLADSP_BIN -c $DEFAULT_CFG -p 1234 -a 0.0.0.0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    # Servicio camillagui-backend
    cat > /etc/systemd/system/camillagui.service << EOF
[Unit]
Description=CamillaGUI Web Backend
After=network.target camilladsp-engine.service

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
    systemctl enable camilladsp-engine.service || true
    success "Servicios systemd creados y habilitados"
    info "Para iniciar ahora: sudo systemctl start camilladsp-engine camillagui"
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
    echo "  sudo systemctl start   camilladsp-engine camillagui"
    echo "  sudo systemctl stop    camillagui camilladsp-engine"
    echo "  sudo systemctl status  camilladsp-engine camillagui"
    echo "  sudo journalctl -u camilladsp-engine -f"
    echo "  sudo journalctl -u camillagui -f"
fi
