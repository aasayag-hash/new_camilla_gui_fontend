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
INSTALL_DIR="/opt/camilladsp"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/camilladsp"
SYSTEMD_DIR="/etc/systemd/system"
CAMILLADSP_BIN="${BIN_DIR}/camilladsp"
BACKEND_REPO="https://github.com/HEnquist/camillagui-backend.git"
FRONTEND_REPO="https://github.com/aasayag-hash/new_camilla_gui_fontend.git"
CAMILLADSP_REPO="https://github.com/HEnquist/camilladsp"

# Determinar el usuario real que invocó sudo
SERVICE_USER="${SUDO_USER:-}"
if [[ -z "$SERVICE_USER" ]]; then
    SERVICE_USER=$(logname 2>/dev/null || echo "root")
fi

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔═══════════════════════════════════════════════════╗"
echo "║      CamillaDSP + GUI Web — Instalador v2.0        ║"
echo "╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Verificar root ────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    error "Este script requiere privilegios de root. Ejecutar con: sudo $0"
    exit 1
fi

# Verificar que se ejecute con sudo desde usuario normal
if [[ -z "${SUDO_USER:-}" ]] || [[ "${SUDO_USER}" == "root" ]]; then
    error "Ejecuta como un usuario normal con sudo, no directamente como root."
    echo "  Ejemplo: sudo bash install.sh"
    exit 1
fi

info "Instalando para el usuario: ${SERVICE_USER}"

# ── Detectar arquitectura ─────────────────────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
    x86_64)  ARCH_NAME="amd64";  ARCH_LABEL="x86_64 (PC)" ;;
    aarch64) ARCH_NAME="aarch64"; ARCH_LABEL="ARM64 (Raspberry Pi 4/5)" ;;
    armv7l)  ARCH_NAME="armv7";   ARCH_LABEL="ARMv7 (Raspberry Pi 3)" ;;
    armv6l)  ARCH_NAME="armv6";   ARCH_LABEL="ARMv6 (Raspberry Pi Zero)" ;;
    *)
        warn "Arquitectura '$ARCH' no reconocida."
        ARCH_NAME="unknown"
        ARCH_LABEL="Desconocida"
        ;;
esac
info "Arquitectura detectada: $ARCH_NAME ($ARCH_LABEL)"

# ── Detectar distribución y package manager ─────────────────────────────────
detect_pkg_manager() {
    if command -v apt-get &>/dev/null; then
        PKG_MGR="apt"
        PKG_UPDATE="apt-get update -qq"
        PKG_INSTALL="apt-get install -y -qq"
        PKG_DEPS="python3 python3-pip python3-venv git curl wget"
        
        UBUNTU_MAJOR=0
        if [[ -f /etc/os-release ]]; then
            source /etc/os-release
            if [[ "$ID" == "ubuntu" ]]; then
                UBUNTU_MAJOR=$(echo "$VERSION_ID" | cut -d. -f1)
            fi
        fi
        
        if [[ "$UBUNTU_MAJOR" -ge 24 ]]; then
            PKG_DEPS="$PKG_DEPS libasound2t64"
        else
            PKG_DEPS="$PKG_DEPS libasound2"
        fi
    elif command -v pacman &>/dev/null; then
        PKG_MGR="pacman"
        PKG_UPDATE="pacman -Sy --noconfirm"
        PKG_INSTALL="pacman -S --noconfirm --needed"
        PKG_DEPS="python python-pip git curl wget alsa-lib"
    elif command -v dnf &>/dev/null; then
        PKG_MGR="dnf"
        PKG_UPDATE="dnf check-update || true"
        PKG_INSTALL="dnf install -y -q"
        PKG_DEPS="python3 python3-pip git curl wget alsa-lib"
    else
        error "No se encontró gestor de paquetes compatible."
        exit 1
    fi
    info "Gestor de paquetes: $PKG_MGR"
}
detect_pkg_manager

# ── Auto-detectar última versión de CamillaDSP desde GitHub API ──────────────
CDSP_API="https://api.github.com/repos/HEnquist/camilladsp/releases/latest"
CDSP_VERSION=""
CDSP_URL=""

_fetch() {
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
        warn "No se pudo consultar la API de GitHub."
        return 1
    fi

    CDSP_VERSION=$(echo "$json" | grep '"tag_name"' \
        | sed 's/.*"tag_name"[[:space:]]*:[[:space:]]*"v\([^"]*\)".*/\1/' \
        | head -1)

    if [[ -z "$CDSP_VERSION" ]]; then
        return 1
    fi

    info "Última versión disponible: v${CDSP_VERSION}"

    CDSP_URL=$(echo "$json" \
        | grep '"browser_download_url"' \
        | grep "$ARCH_NAME" \
        | grep '\.tar\.gz' \
        | sed 's/.*"browser_download_url"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/' \
        | head -1)

    if [[ -z "$CDSP_URL" ]]; then
        warn "No se encontró asset para $ARCH_NAME"
        return 1
    fi

    info "URL del binario: $CDSP_URL"
    return 0
}

_detect_cdsp_release || true

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

# ── Preguntar opciones ────────────────────────────────────────────────────────
echo ""
read -rp "Directorio de instalación [${INSTALL_DIR}]: " INPUT_DIR
[[ -n "$INPUT_DIR" ]] && INSTALL_DIR="$INPUT_DIR"

read -rp "¿Instalar CamillaDSP binary? [S/n]: " INSTALL_CDSP
INSTALL_CDSP="${INSTALL_CDSP:-S}"

read -rp "¿Crear servicio systemd? [S/n]: " CREATE_SERVICE
CREATE_SERVICE="${CREATE_SERVICE:-S}"

read -rp "¿Puerto del backend GUI? [5005]: " GUI_PORT
GUI_PORT="${GUI_PORT:-5005}"

echo ""
info "Configuración:"
info "  Directorio:    $INSTALL_DIR"
info "  CamillaDSP:   $(echo $INSTALL_CDSP | tr '[:lower:]' '[:upper:]')${CDSP_VERSION:+ (v${CDSP_VERSION})}"
info "  Servicios:    $(echo $CREATE_SERVICE | tr '[:lower:]' '[:upper:]')"
info "  Puerto GUI:   $GUI_PORT"
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

# Verificar Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [[ "$PYTHON_MAJOR" -lt 3 || ( "$PYTHON_MAJOR" -eq 3 && "$PYTHON_MINOR" -lt 9 ) ]]; then
    error "Python 3.9+ requerido. Encontrado: $PYTHON_VERSION"
    exit 1
fi
success "Python ${PYTHON_VERSION} ✓"

# Verificar git
if ! command -v git &>/dev/null; then
    error "git no encontrado."
    exit 1
fi
success "git $(git --version | awk '{print $3}') ✓"

# ══════════════════════════════════════════════════════════════════════════════
step "2/6 — Instalando CamillaDSP"
# ══════════════════════════════════════════════════════════════════════════════
if [[ "${INSTALL_CDSP^^}" != "N" ]]; then
    if [[ -n "$CDSP_URL" ]]; then
        info "Descargando CamillaDSP v${CDSP_VERSION} para ${ARCH_NAME}..."
        TMP_DIR=$(mktemp -d)
        cd "$TMP_DIR"
        if _fetch "$CDSP_URL" -o camilladsp.tar.gz; then
            tar xzf camilladsp.tar.gz
            CDSP_BIN=$(find . -name "camilladsp" -type f | head -1)
            if [[ -n "$CDSP_BIN" ]]; then
                install -m 755 "$CDSP_BIN" "$CAMILLADSP_BIN"
                CDSP_VER=$("$CAMILLADSP_BIN" --version 2>&1 | head -1 || echo "desconocida")
                success "CamillaDSP instalado: $CDSP_VER"
            else
                warn "No se encontró binario en el archivo."
            fi
        else
            warn "No se pudo descargar el binario precompilado."
        fi
        rm -rf "$TMP_DIR"
    else
        warn "No hay binario precompilado para $ARCH_NAME."
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
step "3/6 — Instalando camillagui-backend"
# ══════════════════════════════════════════════════════════════════════════════
mkdir -p "$INSTALL_DIR"

# Clonar backend
if [[ -d "$INSTALL_DIR/backend/.git" ]]; then
    warn "El directorio del backend ya existe"
    read -rp "¿Desea eliminarlo y hacer una instalación limpia? [s/N]: " CLEAN_BACKEND
    if [[ "${CLEAN_BACKEND^^}" == "S" ]]; then
        rm -rf "$INSTALL_DIR/backend"
    else
        cd "$INSTALL_DIR/backend"
        git fetch --tags 2>&1 | tail -3 || true
        git pull --ff-only 2>&1 | tail -3 || true
    fi
fi

if [[ ! -d "$INSTALL_DIR/backend/.git" ]]; then
    info "Clonando camillagui-backend..."
    git clone --depth=1 "$BACKEND_REPO" "$INSTALL_DIR/backend"
fi
success "Backend instalado en $INSTALL_DIR/backend"

# Crear entorno virtual
info "Creando entorno virtual Python..."
python3 -m venv "$INSTALL_DIR/backend/venv"
"$INSTALL_DIR/backend/venv/bin/pip" install --quiet --upgrade pip

# Instalar dependencias
info "Instalando dependencias Python..."
"$INSTALL_DIR/backend/venv/bin/pip" install --quiet aiohttp pyyaml
"$INSTALL_DIR/backend/venv/bin/pip" install --quiet "camilladsp @ git+https://github.com/HEnquist/pycamilladsp.git"
"$INSTALL_DIR/backend/venv/bin/pip" install --quiet "camilladsp-plot @ git+https://github.com/HEnquist/pycamilladsp-plot.git"
success "Dependencias Python instaladas"

# ══════════════════════════════════════════════════════════════════════════════
step "4/6 — Instalando frontend web"
# ══════════════════════════════════════════════════════════════════════════════
GUI_DEST="$INSTALL_DIR/backend/build"
mkdir -p "$GUI_DEST"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/index.html" ]]; then
    info "Copiando frontend local..."
    if command -v rsync &>/dev/null; then
        rsync -a --exclude='.git' --exclude='.claude' --exclude='install.sh' \
            "$SCRIPT_DIR/" "$GUI_DEST/"
    else
        cp -r "$SCRIPT_DIR"/index.html "$GUI_DEST/"
        cp -r "$SCRIPT_DIR"/js         "$GUI_DEST/" 2>/dev/null || true
        cp -r "$SCRIPT_DIR"/style      "$GUI_DEST/" 2>/dev/null || true
        cp -r "$SCRIPT_DIR"/assets     "$GUI_DEST/" 2>/dev/null || true
    fi
    success "Frontend copiado a $GUI_DEST"
else
    info "Clonando frontend desde GitHub..."
    if [[ -d "$GUI_DEST/.git" ]]; then
        cd "$GUI_DEST"
        git pull --ff-only 2>&1 | tail -3 || true
    else
        git clone --depth=1 "$FRONTEND_REPO" "$GUI_DEST"
    fi
    success "Frontend instalado en $GUI_DEST"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "5/6 — Configurando"
# ══════════════════════════════════════════════════════════════════════════════
mkdir -p "$CONFIG_DIR/configs" "$CONFIG_DIR/coeffs"

# camillagui.yml
info "Creando configuración del backend..."
cat > "$CONFIG_DIR/camillagui.yml" << EOF
---
camilla_host: "localhost"
camilla_port: 1234
bind_address: "0.0.0.0"
port: ${GUI_PORT}
ssl_certificate: null
ssl_private_key: null
gui_config_file: null
config_dir: "${CONFIG_DIR}/configs"
coeff_dir: "${CONFIG_DIR}/coeffs"
default_config: "${CONFIG_DIR}/configs/default.yml"
statefile_path: "${CONFIG_DIR}/statefile.yml"
log_file: null
on_set_active_config: null
on_get_active_config: null
supported_capture_types: null
supported_playback_types: null
EOF
success "camillagui.yml creado"

# Statefile
touch "$CONFIG_DIR/statefile.yml"

# default.yml
DEFAULT_CFG="$CONFIG_DIR/configs/default.yml"
if [[ ! -f "$DEFAULT_CFG" ]]; then
    info "Creando configuración inicial de audio..."
    cat > "$DEFAULT_CFG" << 'EOF'
---
devices:
  samplerate: 48000
  chunksize: 1024
  enable_rate_adjust: true
  capture:
    type: Alsa
    channels: 2
    device: "hw:0,0"
    format: S32_LE
  playback:
    type: Alsa
    channels: 2
    device: "hw:0,0"
    format: S32_LE

filters:
  pass_through:
    type: Gain
    parameters:
      gain: 0
      inverted: false

mixers: {}

pipeline:
  - type: Filter
    channels: [0, 1]
    names:
      - pass_through
EOF
    success "Configuración inicial creada: $DEFAULT_CFG"
    info "IMPORTANTE: Edita $DEFAULT_CFG con tus dispositivos de audio"
    info "  Usa 'aplay -l' y 'arecord -l' para listar dispositivos"
else
    info "Configuración existente mantenida"
fi

# ══════════════════════════════════════════════════════════════════════════════
step "6/6 — Servicios systemd"
# ══════════════════════════════════════════════════════════════════════════════
if [[ "${CREATE_SERVICE^^}" != "N" ]] && command -v systemctl &>/dev/null; then
    # Grupo realtime
    if ! getent group realtime &>/dev/null; then
        groupadd --system realtime 2>/dev/null || true
    fi

    # Agregar usuario a grupos
    usermod -aG audio "$SERVICE_USER" 2>/dev/null || true
    usermod -aG realtime "$SERVICE_USER" 2>/dev/null || true

    # Servicio camilladsp-engine
    cat > "${SYSTEMD_DIR}/camilladsp-engine.service" << EOF
[Unit]
Description=CamillaDSP Audio Processing Engine v4.x
After=sound.target
Wants=sound.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=audio
SupplementaryGroups=realtime
Nice=-10
IOSchedulingClass=realtime
IOSchedulingPriority=0

ExecStart=${CAMILLADSP_BIN} -p 1234 -a 0.0.0.0 -w ${DEFAULT_CFG}
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    # Servicio camillagui
    cat > "${SYSTEMD_DIR}/camillagui.service" << EOF
[Unit]
Description=CamillaDSP GUI Backend (Python/aiohttp)
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
    systemctl enable camilladsp-engine.service camillagui.service || true
    success "Servicios systemd creados y habilitados"

    # Corregir permisos
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "$CONFIG_DIR"
    chown -R "${SERVICE_USER}:${SERVICE_USER}" "$INSTALL_DIR/backend/build"
    chmod 600 "$CONFIG_DIR/statefile.yml"
fi

# ═══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${BOLD}${GREEN}════════════════════════════════════════"
echo "  Instalación completada correctamente"
echo -e "════════════════════════════════════════${NC}"
echo ""
info "Acceder a la interfaz web:"
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "localhost")
echo -e "  ${BOLD}http://${LOCAL_IP}:${GUI_PORT}${NC}"
echo ""
info "Comandos útiles:"
echo "  sudo systemctl start camilladsp-engine camillagui"
echo "  sudo systemctl status camilladsp-engine camillagui"
echo "  sudo journalctl -u camilladsp-engine -f"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC} Cierra sesión y vuelve a entrar para que los cambios"
echo "de grupo (audio, realtime) tomen efecto."
echo ""