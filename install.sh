#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# install.sh — Instalador CamillaDSP + camillagui-backend + frontend web
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

git config --global advice.detachedHead false

# ── Colores ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()    { echo -e "${GREEN}✓${NC} $*"; }
info()   { echo -e "${BLUE}→${NC} $*"; }
warn()   { echo -e "${YELLOW}⚠${NC} $*"; }
error()  { echo -e "${RED}✗${NC}  $*" >&2; }
header() { echo -e "\n${BOLD}${CYAN}$*${NC}"; }

# ── Config por defecto ────────────────────────────────────────────────────────
INSTALL_DIR="/opt/camilladsp"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/camilladsp"
SYSTEMD_DIR="/etc/systemd/system"
CAMILLADSP_BIN="${BIN_DIR}/camilladsp"
BACKEND_REPO="https://github.com/HEnquist/camillagui-backend.git"
FRONTEND_REPO="https://github.com/aasayag-hash/new_camilla_gui_fontend.git"

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║      CamillaDSP + GUI Web — Instalador v2.1       ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Verificar root ────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    error "Este script requiere privilegios de root. Ejecutar con: sudo $0"
    exit 1
fi

# Determinar usuario real
SERVICE_USER="${SUDO_USER:-}"
if [[ -z "$SERVICE_USER" ]] || [[ "$SERVICE_USER" == "root" ]]; then
    error "Ejecuta como un usuario normal con sudo, no directamente como root."
    echo "  Ejemplo: sudo bash install.sh"
    exit 1
fi

log "Instalando para el usuario: ${SERVICE_USER}"

# ── Detectar arquitectura ─────────────────────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
    x86_64)  ARCH_NAME="amd64";  ARCH_LABEL="x86_64 (PC)" ;;
    aarch64) ARCH_NAME="aarch64"; ARCH_LABEL="ARM64" ;;
    armv7l)  ARCH_NAME="armv7";   ARCH_LABEL="ARMv7" ;;
    armv6l)  ARCH_NAME="armv6";   ARCH_LABEL="ARMv6" ;;
    *)       ARCH_NAME="unknown"; ARCH_LABEL="Desconocida" ;;
esac
log "Arquitectura: $ARCH_NAME"

# ── Detectar distribución ─────────────────────────────────────────────────────
if command -v apt-get &>/dev/null; then
    PKG_MGR="apt"
    PKG_UPDATE="apt-get update -qq"
    PKG_INSTALL="apt-get install -y -qq"
    PKG_DEPS="python3 python3-pip python3-venv git curl wget"
    
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        if [[ "$ID" == "ubuntu" ]] && [[ "${VERSION_ID:-0}" == "24"* ]]; then
            PKG_DEPS="$PKG_DEPS libasound2t64"
        else
            PKG_DEPS="$PKG_DEPS libasound2"
        fi
    fi
elif command -v pacman &>/dev/null; then
    PKG_MGR="pacman"
    PKG_UPDATE="pacman -Sy --noconfirm"
    PKG_INSTALL="pacman -S --noconfirm --needed"
    PKG_DEPS="python python-pip git curl wget alsa-lib"
else
    error "Gestor de paquetes no soportado"
    exit 1
fi
log "Gestor de paquetes: $PKG_MGR"

# ── Obtener versión de CamillaDSP ───────────────────────────────────────────
CDSP_API="https://api.github.com/repos/HEnquist/camilladsp/releases/latest"
CDSP_VERSION=""
CDSP_URL=""

info "Consultando última versión..."
JSON=$(curl -sfL "$CDSP_API" 2>/dev/null || true)
if [[ -n "$JSON" ]]; then
    CDSP_VERSION=$(echo "$JSON" | grep '"tag_name"' | sed 's/.*"tag_name".*:.*"v\([^"]*\)".*/\1/' | head -1)
    if [[ -n "$CDSP_VERSION" ]]; then
        CDSP_URL="https://github.com/HEnquist/camilladsp/releases/download/v${CDSP_VERSION}/camilladsp-linux-${ARCH_NAME}.tar.gz"
        log "Versión: v${CDSP_VERSION}"
    fi
fi

# ── Verificar instalación previa ─────────────────────────────────────────────
if [[ -d "$INSTALL_DIR" ]]; then
    warn "Ya existe instalación en: $INSTALL_DIR"
    read -rp "¿Eliminar y hacer instalación limpia? [s/N]: " CLEAN_INSTALL
    if [[ "${CLEAN_INSTALL^^}" == "S" ]]; then
        info "Deteniendo servicios..."
        systemctl stop camilladsp-engine camillagui 2>/dev/null || true
        rm -rf "$INSTALL_DIR"
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
header "1/6 — Dependencias del sistema"
# ══════════════════════════════════════════════════════════════════════════════
info "Actualizando repositorios..."
$PKG_UPDATE 2>&1 | tail -3 || true

info "Instalando paquetes..."
$PKG_INSTALL $PKG_DEPS
log "Dependencias instaladas"

# Verificar Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
log "Python ${PYTHON_VERSION}"

# ══════════════════════════════════════════════════════════════════════════════
header "2/6 — CamillaDSP Engine"
# ══════════════════════════════════════════════════════════════════════════════
if [[ -n "$CDSP_URL" ]]; then
    info "Descargando CamillaDSP v${CDSP_VERSION}..."
    TMP_DIR=$(mktemp -d)
    if curl -fsSL --progress-bar -o "${TMP_DIR}/camilladsp.tar.gz" "$CDSP_URL"; then
        tar -xzf "${TMP_DIR}/camilladsp.tar.gz" -C "$TMP_DIR"
        CDSP_BIN=$(find "$TMP_DIR" -name "camilladsp" -type f 2>/dev/null | head -1)
        if [[ -n "$CDSP_BIN" ]]; then
            install -m 755 "$CDSP_BIN" "$CAMILLADSP_BIN"
            CDSP_VER=$("$CAMILLADSP_BIN" --version 2>&1 | head -1 || echo "desconocida")
            log "CamillaDSP instalado: $CDSP_VER"
        fi
    else
        warn "No se pudo descargar. Instala manualmente desde GitHub."
    fi
    rm -rf "$TMP_DIR"
fi

# ══════════════════════════════════════════════════════════════════════════════
header "3/6 — CamillaGUI Backend"
# ══════════════════════════════════════════════════════════════════════════════
mkdir -p "$INSTALL_DIR"

info "Clonando camillagui-backend..."
git clone --depth=1 "$BACKEND_REPO" "$INSTALL_DIR/backend" || {
    error "Error al clonar el backend"
    exit 1
}
log "Backend instalado"

# Entorno virtual
info "Creando entorno virtual..."
python3 -m venv "$INSTALL_DIR/backend/venv"

info "Instalando dependencias..."
"$INSTALL_DIR/backend/venv/bin/pip" install --quiet --upgrade pip
"$INSTALL_DIR/backend/venv/bin/pip" install --quiet aiohttp pyyaml
"$INSTALL_DIR/backend/venv/bin/pip" install --quiet "camilladsp @ git+https://github.com/HEnquist/pycamilladsp.git"
"$INSTALL_DIR/backend/venv/bin/pip" install --quiet "camilladsp-plot @ git+https://github.com/HEnquist/pycamilladsp-plot.git"
log "Dependencias Python instaladas"

# ══════════════════════════════════════════════════════════════════════════════
header "4/6 — Frontend Web"
# ══════════════════════════════════════════════════════════════════════════════
GUI_DEST="$INSTALL_DIR/backend/build"
mkdir -p "$GUI_DEST"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/index.html" ]]; then
    info "Copiando frontend local..."
    cp -r "$SCRIPT_DIR"/index.html "$GUI_DEST/"
    [[ -d "$SCRIPT_DIR/js" ]] && cp -r "$SCRIPT_DIR/js" "$GUI_DEST/"
    [[ -d "$SCRIPT_DIR/style" ]] && cp -r "$SCRIPT_DIR/style" "$GUI_DEST/"
    [[ -d "$SCRIPT_DIR/assets" ]] && cp -r "$SCRIPT_DIR/assets" "$GUI_DEST/"
else
    info "Clonando frontend..."
    git clone --depth=1 "$FRONTEND_REPO" "$GUI_DEST" 2>/dev/null || {
        warn "No se encontró frontend. Copia los archivos manualmente."
    }
fi
log "Frontend instalado"

# ══════════════════════════════════════════════════════════════════════════════
header "5/6 — Configuración"
# ══════════════════════════════════════════════════════════════════════════════
mkdir -p "$CONFIG_DIR/configs" "$CONFIG_DIR/coeffs"

# camillagui.yml
cat > "$CONFIG_DIR/camillagui.yml" << 'EOF'
---
camilla_host: "localhost"
camilla_port: 1234
bind_address: "0.0.0.0"
port: 5005
ssl_certificate: null
ssl_private_key: null
gui_config_file: null
config_dir: "/etc/camilladsp/configs"
coeff_dir: "/etc/camilladsp/coeffs"
default_config: "/etc/camilladsp/configs/default.yml"
statefile_path: "/etc/camilladsp/statefile.yml"
log_file: null
on_set_active_config: null
on_get_active_config: null
supported_capture_types: null
supported_playback_types: null
EOF

touch "$CONFIG_DIR/statefile.yml"

# default.yml
if [[ ! -f "$CONFIG_DIR/configs/default.yml" ]]; then
    cat > "$CONFIG_DIR/configs/default.yml" << 'EOF'
---
devices:
  samplerate: 48000
  chunksize: 1024
  queuelimit: 4
  capture:
    type: Alsa
    channels: 2
    format: null
    device: 'null'
  playback:
    type: Alsa
    channels: 2
    format: null
    device: 'null'
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
    log "Configuración inicial creada"
fi
log "Configuración lista"

# ══════════════════════════════════════════════════════════════════════════════
header "6/6 — Servicios systemd"
# ══════════════════════════════════════════════════════════════════════════════
if command -v systemctl &>/dev/null; then
    # Grupos
    if ! getent group realtime &>/dev/null; then
        groupadd --system realtime 2>/dev/null || true
    fi
    usermod -aG audio "$SERVICE_USER" 2>/dev/null || true
    usermod -aG realtime "$SERVICE_USER" 2>/dev/null || true

    # Servicio engine
    cat > "${SYSTEMD_DIR}/camilladsp-engine.service" << EOF
[Unit]
Description=CamillaDSP Audio Processing Engine
After=sound.target
Wants=sound.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=audio
SupplementaryGroups=realtime

ExecStart=${CAMILLADSP_BIN} -p 1234 -a 0.0.0.0 -w ${CONFIG_DIR}/configs/default.yml
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Servicio GUI
    cat > "${SYSTEMD_DIR}/camillagui.service" << EOF
[Unit]
Description=CamillaDSP GUI Backend
After=network.target camilladsp-engine.service
Wants=camilladsp-engine.service

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}/backend
Environment=PYTHONUNBUFFERED=1
ExecStart=${INSTALL_DIR}/backend/venv/bin/python main.py -c ${CONFIG_DIR}/camillagui.yml
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable camilladsp-engine.service camillagui.service 2>/dev/null || true
    log "Servicios configurados"

    # Permisos
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "$CONFIG_DIR"
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "$INSTALL_DIR/backend/build" 2>/dev/null || true
    chmod 600 "$CONFIG_DIR/statefile.yml"
fi

# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════"
echo "  Instalación completada"
echo -e "════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Accede a la GUI:${NC}"
echo -e "  ${CYAN}http://localhost:5005${NC}"
echo ""
echo -e "  ${BOLD}Comandos:${NC}"
echo "  sudo systemctl start camilladsp-engine camillagui"
echo "  sudo systemctl status camilladsp-engine camillagui"
echo "  journalctl -u camilladsp-engine -f"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC} Edita /etc/camilladsp/configs/default.yml con tus dispositivos de audio"
echo "  Usa 'aplay -l' y 'arecord -l' para listar dispositivos"
echo ""