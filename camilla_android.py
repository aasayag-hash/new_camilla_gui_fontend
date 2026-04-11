import sys
import json
import math
import time
import re
import traceback
import subprocess
import webbrowser

# --- Auto-instalacion de dependencias (camilladsp y websocket) ---
try:
    import camilladsp
    import websocket
except ImportError:
    print("Descargando componentes de audio e instalando de forma automatica... Por favor espere.")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
            "https://github.com/HEnquist/pycamilladsp/archive/refs/heads/master.zip", "websocket-client"])
        print("Libreria CamillaDSP instalada correctamente!")
    except Exception as e:
        print(f"Error critico instalando librerias: {e}")

from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QLineEdit, QPushButton, 
                             QStackedWidget, QTextEdit, QFrame, QRadioButton, QGroupBox,
                             QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QAbstractItemView, QCheckBox, QButtonGroup, QDialog,
                             QScrollArea, QScroller, QTabWidget, QMessageBox, QFileDialog, QInputDialog)
from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QBrush, QLinearGradient, QFont

# Importacion CamillaDSP Segura
try:
    from camilladsp import CamillaClient as CamillaDSP
except:
    try:
        from camilladsp import CamillaConnection as CamillaDSP
    except:
        class CamillaDSP:
            def __init__(self, ip, port): pass
            def connect(self): pass
            def query(self, *args, **kwargs): raise Exception("CamillaDSP library not installed")

# Intentamos importar yaml para leer los config.yml
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# --- DICCIONARIO DE IDIOMAS ---
LANG = {
    "es": {
        "title": "CAMILLADSP MASTER CONSOLE",
        "ip_label": "IP Servidor:",
        "port_label": "Puerto:",
        "btn_scan": "CONECTAR A HARDWARE",
        "btn_help": "AYUDA / MANUAL",
        "btn_lang": "EN / ES",
        "btn_launch": "INICIAR ESTUDIO",
        "help_title": "Manual de Usuario - CamillaDSP",
        "warn_title": "Atención",
        "warn_msg": "Para crear filtros, selecciona al menos un canal en las solapas.",
        "cross_warn_msg": "Para crear un crossover, selecciona AL MENOS UNA SALIDA (OUT) en las solapas.",
        "help_text": """
=== CONTROLES TÁCTILES ANDROID ===
- MANTENER PRESIONADO (Long Press): Reemplaza el "Clic Derecho" del PC. Mantener el dedo 0.5s activa borrar o resetear.
- DESLIZAR (Swipe): Arrastra el dedo por la pantalla para mover gráficas, atenuadores y listas.
- DOBLE TOQUE: Tocar rápido dos veces para crear filtros.

=== PANTALLA DE INICIO ===
- IP / Puerto: Ingrese la dirección IP y el puerto del servidor CamillaDSP.
- CONECTAR A HARDWARE: Se conecta al servidor y abre la consola principal.
- Camilla WEB: Abre la interfaz web de CamillaDSP (puerto 5005) en el navegador usando la IP ingresada.
- RESET: Envía una configuración limpia por defecto a CamillaDSP. Solicita la cantidad de canales de entrada y salida del hardware antes de enviar.
- EN / ES: Cambia el idioma de la interfaz.
- AYUDA / MANUAL: Muestra esta ventana.

=== BARRA SUPERIOR Y CANALES ===
- Solapas IN / OUT: Seleccionan qué canales visualizar y sobre cuáles aplicar los nuevos filtros.
- MANTENER PRESIONADO (Solapa): Activa/Desactiva el BYPASS de Ecualización (Icono 🔴).
- Botón ALL: Selecciona/Deselecciona todos los canales rápidamente.

=== BOTONES DE GESTIÓN (Esquina Superior Derecha) ===
- WEB: Abre la interfaz web de CamillaDSP (puerto 5005) en el navegador.
- Imp Cfg: Importa una configuración completa desde un archivo YAML o JSON.
- Exp Cfg: Exporta la configuración actual completa a un archivo YAML o JSON.
- Imp EQ: Importa filtros de ecualización desde un archivo de texto.
- Exp EQ: Exporta los filtros de ecualización visibles a un archivo de texto.
- Reset: Restaura CamillaDSP a la configuración por defecto.
- Log: Abre la ventana de consola con el registro de comandos.

=== GRÁFICAS EQ Y CROSSOVER ===
- Doble Toque (Fondo libre): CREA un filtro nuevo para los canales activos.
- Tocar y Arrastrar (Punto): Mueve Frecuencia y Ganancia.
- MANTENER PRESIONADO (Punto): ELIMINA el filtro permanentemente.

=== TABLAS DE FILTROS Y CROSSOVERS ===
- Editar celdas: Modifique frecuencia, ganancia, Q u orden directamente en la tabla.
- ComboBox Tipo: Cambia el tipo de filtro (Peaking, Highshelf, Lowshelf, etc.).
- ComboBox Canal: Reasigna el filtro a otro canal.
- Botón X: Borra permanentemente ese filtro.

=== MATRIZ MIXER (RUTEO) ===
- Doble Toque (Nombres): Renombra entradas y salidas.
- Toque Normal (Celda '+'): CREA conexión In -> Out.
- MANTENER PRESIONADO (Celda Verde): BORRA la conexión.

=== VÚMETROS, FADERS Y COMPRESORES ===
- Botones de VISTA: Filtra para ver SÓLO Entradas, SÓLO Salidas, o TODO.
- Fader MASTER: Controla el volumen global del sistema.
- Botón MUTE ALL: Silencia o restaura globalmente todas las salidas.
- MANTENER PRESIONADO (Nombre de Canal): Renombra el canal.
- Toque Normal (Nombre Salida): Mutea (Rojo) o Activa (Verde) el canal.
- Tocar y Arrastrar (Fader): Ajusta el volumen de -30dB a +10dB.
- MANTENER PRESIONADO (Fader): Resetea instantáneamente a 0.0.
- Botón +/-: Invierte la polaridad (fase) del canal.
- DLY(ms): Campo de texto para ajustar el delay por canal en milisegundos.

=== COMPRESORES ===
- Doble Toque (Barra Vúmetro): CREA un compresor ajustando el Threshold donde tocaste.
- MANTENER PRESIONADO (Barra Vúmetro): BORRA permanentemente el compresor.
- Tabla de Compresores: Edite Attack, Release, Threshold, Ratio, Makeup Gain y Clip Limit.
- Botón AUTO: Muestrea el audio por 5s y calcula automáticamente Attack, Release, Ratio y Makeup Gain.
- Botón X: Borra permanentemente ese compresor.
"""
    },
    "en": {
        "title": "CAMILLADSP MASTER CONSOLE",
        "ip_label": "Server IP:",
        "port_label": "Port:",
        "btn_scan": "CONNECT HARDWARE",
        "btn_help": "HELP / MANUAL",
        "btn_lang": "ES / EN",
        "btn_launch": "LAUNCH STUDIO",
        "help_title": "User Manual - CamillaDSP",
        "warn_title": "Warning",
        "warn_msg": "To create filters, select at least one channel from the tabs.",
        "cross_warn_msg": "To create a crossover, select AT LEAST ONE OUTPUT (OUT) from the tabs.",
        "help_text": """
=== ANDROID TOUCH CONTROLS ===
- LONG PRESS: Replaces "Right Click" from PC. Hold finger 0.5s to delete or reset.
- SWIPE: Drag finger across the screen to move graphs, faders, and lists.
- DOUBLE TAP: Tap quickly twice to create filters.

=== START SCREEN ===
- IP / Port: Enter the CamillaDSP server IP address and port.
- CONNECT HARDWARE: Connects to the server and opens the main console.
- Camilla WEB: Opens the CamillaDSP web interface (port 5005) in your browser using the entered IP.
- RESET: Sends a clean default configuration to CamillaDSP. Asks for the number of hardware input and output channels before sending.
- ES / EN: Switches the interface language.
- HELP / MANUAL: Shows this window.

=== TOP BAR & CHANNELS ===
- IN / OUT Tabs: Select channels to view and apply new filters to.
- LONG PRESS (Tab): Toggles EQ BYPASS for that specific channel (🔴 Icon).
- ALL Button: Selects/Deselects all channels instantly.

=== MANAGEMENT BUTTONS (Top Right Corner) ===
- WEB: Opens the CamillaDSP web interface (port 5005) in the default browser.
- Imp Cfg: Imports a full configuration from a YAML or JSON file.
- Exp Cfg: Exports the current full configuration to a YAML or JSON file.
- Imp EQ: Imports EQ filters from a text file.
- Exp EQ: Exports visible EQ filters to a text file.
- Reset: Restores CamillaDSP to default configuration.
- Log: Opens the console window showing command logs.

=== EQ & CROSSOVER GRAPHS ===
- Double Tap (empty background): CREATES a new filter on selected channels.
- Touch & Drag (Point): Moves Frequency and Gain.
- LONG PRESS (Point): Permanently DELETES the filter.

=== FILTER & CROSSOVER TABLES ===
- Edit cells: Modify frequency, gain, Q, or order directly in the table.
- Type ComboBox: Changes the filter type (Peaking, Highshelf, Lowshelf, etc.).
- Channel ComboBox: Reassigns the filter to a different channel.
- X Button: Permanently deletes that filter.

=== MIXER MATRIX (ROUTING) ===
- Double Tap (Names): Renames inputs and outputs.
- Normal Tap ('+' cell): CREATES a routing connection (In -> Out).
- LONG PRESS (Green cell): DELETES the routing connection.

=== VU METERS, FADERS & COMPRESSORS ===
- VIEW Buttons: Filter to see ONLY Inputs, ONLY Outputs, or ALL.
- MASTER Fader: Controls the overall system volume.
- MUTE ALL Button: Globally mutes or restores all outputs.
- LONG PRESS (Channel Name): Renames the channel.
- Normal Tap (Output Name): Mutes (Red) or Unmutes (Green) the channel.
- Touch & Drag (Fader): Adjusts output volume from -30dB to +10dB.
- LONG PRESS (Fader): Instantly resets value to 0.0.
- +/- Button: Inverts channel polarity (phase).
- DLY(ms): Text field to adjust per-channel delay in milliseconds.

=== COMPRESSORS ===
- Double Tap (VU Meter Bar): CREATES a compressor setting the Threshold where tapped.
- LONG PRESS (VU Meter Bar): Permanently DELETES the compressor.
- Compressor Table: Edit Attack, Release, Threshold, Ratio, Makeup Gain, and Clip Limit.
- AUTO Button: Samples audio for 5s and automatically calculates Attack, Release, Ratio, and Makeup Gain.
- X Button: Permanently deletes that compressor.
"""
    }
}

class HelpDialog(QDialog):
    def __init__(self, current_lang, parent=None):
        super().__init__(parent)
        self.setWindowTitle(LANG[current_lang]["help_title"])
        self.setMinimumSize(600, 500)
        self.setStyleSheet("QDialog { background: #050505; }")
        
        layout = QVBoxLayout(self)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(LANG[current_lang]["help_text"])
        text_edit.setStyleSheet("font-size: 14px; background: #1a1a1a; color: #ffffff; border: 1px solid #444; padding: 10px;")
        QScroller.grabGesture(text_edit.viewport(), QScroller.LeftMouseButtonGesture)
        layout.addWidget(text_edit)
        
        btn_close = QPushButton("Cerrar" if current_lang == "es" else "Close")
        btn_close.setFixedHeight(40)
        btn_close.setStyleSheet("QPushButton { background: #007bff; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; } QPushButton:hover { background: #0056b3; }")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

# PALETA EXTENDIDA PARA HASTA 32 CANALES
GLOBAL_HEX_COLORS = [
    "#00ff96", "#0096ff", "#ff6464", "#ffc800", "#c800ff", "#00ffff", "#ffa500", "#ffffff",
    "#ff00ff", "#00ff00", "#ffff00", "#ff0000", "#0000ff", "#008080", "#800000", "#808000",
    "#800080", "#008000", "#ff7f50", "#7cfc00", "#6495ed", "#00ced1", "#ff1493", "#b0e0e6",
    "#dda0dd", "#fa8072", "#ffb6c1", "#2e8b57", "#da70d6", "#f0e68c", "#87cefa", "#98fb98"
]


# --- MIXIN DE TOQUE PROLONGADO (ANDROID RMOUSE EMULATOR) ---
class TouchLongPressMixin:
    def init_touch(self):
        if not hasattr(self, '_t_timer'):
            from PySide6.QtCore import QTimer
            self._t_timer = QTimer(self)
            self._t_timer.setSingleShot(True)
            self._t_timer.timeout.connect(self._on_long_press)
            self._t_fired = False

    def check_press(self, event):
        self.init_touch()
        if event.button() == Qt.LeftButton:
            from PySide6.QtGui import QMouseEvent
            self._t_event = QMouseEvent(event.type(), event.position(), event.globalPosition(), Qt.RightButton, Qt.RightButton, event.modifiers())
            self._t_start = event.position()
            self._t_fired = False
            self._t_timer.start(450)

    def check_move(self, event):
        if getattr(self, '_t_start', None):
            import math
            if math.hypot(event.position().x() - self._t_start.x(), event.position().y() - self._t_start.y()) > 15:
                self._t_timer.stop()

    def check_release(self, event):
        if hasattr(self, '_t_timer'): self._t_timer.stop()
        if getattr(self, '_t_fired', False):
            self._t_fired = False
            return True
        return False

    def _on_long_press(self):
        self._t_fired = True
        if hasattr(self, 'setDown'): self.setDown(False)
        self.mousePressEvent(self._t_event)

# --- CLASE BOTON DE SOLAPA (Detecta Clic Derecho) ---
    def mouseMoveEvent(self, event):
        self.check_move(event)
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if self.check_release(event): return
        super().mouseReleaseEvent(event)

class ChannelTabButton(QPushButton, TouchLongPressMixin):
    rightClicked = Signal()
    def mousePressEvent(self, event):
        self.check_press(event)
        if event.button() == Qt.RightButton:
            self.rightClicked.emit()
            return
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        self.check_move(event)
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if self.check_release(event): return
        super().mouseReleaseEvent(event)

# --- MOTOR MATEMATICO EXACTO ---
def calcular_magnitud_biquad(params, freq_hz, sample_rate=44100):
    tipo = params.get("type", "")
    f0 = params.get("freq", 1000.0)
    gain = params.get("gain", 0.0)
    q = params.get("q", 1.0)
    if sample_rate <= 0: sample_rate = 44100
    if f0 <= 0: f0 = 10.0
    if q <= 0: q = 0.1
    w0 = 2.0 * math.pi * f0 / sample_rate
    cos_w0 = math.cos(w0); sin_w0 = math.sin(w0); alpha = sin_w0 / (2.0 * q)
    A = math.pow(10.0, gain / 40.0)
    b0=b1=b2=a0=a1=a2=0.0
    if tipo == "Peaking":
        b0 = 1.0 + alpha * A; b1 = -2.0 * cos_w0; b2 = 1.0 - alpha * A
        a0 = 1.0 + alpha / A; a1 = -2.0 * cos_w0; a2 = 1.0 - alpha / A
    elif tipo == "Lowpass":
        b0 = (1.0 - cos_w0) / 2.0; b1 = 1.0 - cos_w0; b2 = (1.0 - cos_w0) / 2.0
        a0 = 1.0 + alpha; a1 = -2.0 * cos_w0; a2 = 1.0 - alpha
    elif tipo == "Highpass":
        b0 = (1.0 + cos_w0) / 2.0; b1 = -(1.0 + cos_w0); b2 = (1.0 + cos_w0) / 2.0
        a0 = 1.0 + alpha; a1 = -2.0 * cos_w0; a2 = 1.0 - alpha
    elif tipo == "Highshelf":
        sqA = math.sqrt(A)
        b0 = A * ((A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * sqA * alpha)
        b1 = -2.0 * A * ((A - 1.0) + (A + 1.0) * cos_w0)
        b2 = A * ((A + 1.0) + (A - 1.0) * cos_w0 - 2.0 * sqA * alpha)
        a0 = (A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * sqA * alpha
        a1 = 2.0 * ((A - 1.0) - (A + 1.0) * cos_w0)
        a2 = (A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * sqA * alpha
    elif tipo == "Lowshelf":
        sqA = math.sqrt(A)
        b0 = A * ((A + 1.0) - (A - 1.0) * cos_w0 + 2.0 * sqA * alpha)
        b1 = 2.0 * A * ((A - 1.0) - (A + 1.0) * cos_w0)
        b2 = A * ((A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * sqA * alpha)
        a0 = (A + 1.0) + (A - 1.0) * cos_w0 + 2.0 * sqA * alpha
        a1 = -2.0 * ((A - 1.0) + (A + 1.0) * cos_w0)
        a2 = (A + 1.0) - (A - 1.0) * cos_w0 - 2.0 * sqA * alpha
    else: return 0.0

    w = 2.0 * math.pi * freq_hz / sample_rate
    z1_r, z1_i = math.cos(-w), math.sin(-w); z2_r, z2_i = math.cos(-2.0*w), math.sin(-2.0*w)
    n_r = b0 + b1 * z1_r + b2 * z2_r; n_i = b1 * z1_i + b2 * z2_i
    d_r = a0 + a1 * z1_r + a2 * z2_r; d_i = a1 * z1_i + a2 * z2_i
    mag_num = math.hypot(n_r, n_i); mag_den = math.hypot(d_r, d_i)
    if mag_den == 0.0 or mag_num == 0.0: return -100.0
    return 20.0 * math.log10(mag_num / mag_den)

def calcular_magnitud_crossover(params, freq_hz):
    tipo = params.get("type", "")
    f0 = float(params.get("freq", 1000.0))
    order = int(params.get("order", 2))
    if f0 <= 0: f0 = 10.0
    
    ratio = freq_hz / f0
    try:
        if tipo == "ButterworthLowpass":
            mag_sq = 1.0 / (1.0 + ratio**(2 * order))
        elif tipo == "ButterworthHighpass":
            mag_sq = ratio**(2 * order) / (1.0 + ratio**(2 * order))
        elif tipo == "LinkwitzRileyLowpass":
            n = order / 2.0
            mag_sq = (1.0 / (1.0 + ratio**(2 * n)))**2
        elif tipo == "LinkwitzRileyHighpass":
            n = order / 2.0
            mag_sq = (ratio**(2 * n) / (1.0 + ratio**(2 * n)))**2
        else:
            return 0.0
    except OverflowError:
        mag_sq = 0.0 if "Lowpass" in tipo else 1.0
        
    if mag_sq <= 1e-10: return -100.0
    return 10.0 * math.log10(mag_sq)

# --- CLASE PERSONALIZADA PARA BLOQUEAR SCROLL EN COMBOBOX ---
class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

# --- VENTANA DE CONSOLA INDEPENDIENTE ---
class ConsoleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Terminal / Consola - CamillaDSP")
        self.resize(700, 400)
        self.setStyleSheet("background: #121212; color: white;")
        layout = QVBoxLayout(self)
        self.log_v = QTextEdit()
        self.log_v.setReadOnly(True)
        self.log_v.setStyleSheet("background:#000; color:#0f0; border:1px solid #333; font-family:Consolas; font-size: 12px;")
        layout.addWidget(self.log_v)
        
        btn_clear = QPushButton("Limpiar Consola")
        btn_clear.setStyleSheet("background: #444; color: white; font-weight: bold; padding: 8px; border-radius: 4px;")
        btn_clear.clicked.connect(self.log_v.clear)
        layout.addWidget(btn_clear)

# --- MATRIZ MIXER GRAFICA ---
class MixerMatrixWidget(QWidget, TouchLongPressMixin):
    def __init__(self, app_ref):
        super().__init__()
        self.app = app_ref
        self.setMouseTracking(True)
        self.cell_w = 40
        self.cell_h = 35
        self.left_margin = 150
        self.top_margin = 120
        self.actualizar_tamanio()

    def actualizar_tamanio(self):
        w = self.left_margin + len(self.app.in_labels) * self.cell_w + 50
        h = self.top_margin + len(self.app.out_labels) * self.cell_h + 50
        self.setMinimumSize(w, h)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(10, 10, 10))

        in_lbls = self.app.in_labels
        out_lbls = self.app.out_labels

        if not in_lbls or not out_lbls:
            p.setPen(Qt.white)
            p.drawText(self.rect(), Qt.AlignCenter, "No Mixer configured or active.")
            return

        mixer_name = next((s.get("name") for s in self.app.config_raw.get("pipeline", []) if s.get("type") == "Mixer"), None)
        mixer_cfg = {}
        if mixer_name and "mixers" in self.app.config_raw and mixer_name in self.app.config_raw["mixers"]:
            mixer_cfg = self.app.config_raw["mixers"][mixer_name]

        mappings = mixer_cfg.get("mapping", [])
        
        active_cells = {} 
        for m in mappings:
            dest = m.get("dest")
            for s in m.get("sources", []):
                src_ch = s.get("channel")
                active_cells[(dest, src_ch)] = s.get("gain", 0.0)

        # Entradas (Top Header)
        p.setPen(Qt.white)
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.drawText(self.left_margin, 20, len(in_lbls)*self.cell_w, 20, Qt.AlignCenter, "Input")
        
        p.setFont(QFont("Arial", 9))
        for col, lbl in enumerate(in_lbls):
            x = self.left_margin + col * self.cell_w
            p.save()
            p.translate(x + self.cell_w/2 + 4, self.top_margin - 25)
            p.rotate(-90)
            p.drawText(0, 0, lbl)
            p.restore()
            p.setPen(QColor(180, 180, 180))
            p.drawText(x, self.top_margin - 15, self.cell_w, 15, Qt.AlignCenter, str(col))
            p.setPen(Qt.white)

        # Salidas (Left Header)
        p.save()
        p.setFont(QFont("Arial", 10, QFont.Bold))
        p.translate(20, self.top_margin + self.cell_h + (len(out_lbls)*self.cell_h)/2)
        p.rotate(-90)
        p.drawText(0, 0, "Output")
        p.restore()

        p.setFont(QFont("Arial", 9))
        for row, lbl in enumerate(out_lbls):
            y = self.top_margin + row * self.cell_h
            p.drawText(40, y, self.left_margin - 65, self.cell_h, Qt.AlignRight | Qt.AlignVCenter, lbl)
            p.setPen(QColor(180, 180, 180))
            p.drawText(self.left_margin - 30, y, 25, self.cell_h, Qt.AlignCenter, str(row))
            p.setPen(Qt.white)

        # Rejilla (Grid)
        for row in range(len(out_lbls)):
            for col in range(len(in_lbls)):
                x = self.left_margin + col * self.cell_w
                y = self.top_margin + row * self.cell_h
                rect = QRectF(x, y, self.cell_w, self.cell_h)
                
                if (row, col) in active_cells:
                    p.fillRect(rect, QColor(80, 255, 80)) 
                    p.setPen(Qt.black)
                    p.setFont(QFont("Arial", 10, QFont.Bold))
                    p.drawText(rect, Qt.AlignCenter, f"{active_cells[(row, col)]:.0f}")
                else:
                    p.fillRect(rect, QColor(25, 25, 25))
                    p.setPen(QColor(100, 100, 100))
                    p.setFont(QFont("Arial", 12))
                    p.drawText(rect, Qt.AlignCenter, "+")

        # Lineas de la matriz
        p.setPen(QPen(QColor(60, 60, 60), 1))
        for r in range(len(out_lbls) + 1):
            y = self.top_margin + r * self.cell_h
            p.drawLine(self.left_margin - 35, y, self.left_margin + len(in_lbls) * self.cell_w, y)
        for c in range(len(in_lbls) + 1):
            x = self.left_margin + c * self.cell_w
            p.drawLine(x, self.top_margin - 20, x, self.top_margin + len(out_lbls) * self.cell_h)

    def mouseMoveEvent(self, event):
        self.check_move(event)
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if self.check_release(event): return
        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        self.check_press(event)
        x, y = event.position().x(), event.position().y()
        in_lbls = self.app.in_labels
        out_lbls = self.app.out_labels

        col = int((x - self.left_margin) // self.cell_w)
        row = int((y - self.top_margin) // self.cell_h)

        if 0 <= col < len(in_lbls) and 0 <= row < len(out_lbls):
            mixer_name = next((s.get("name") for s in self.app.config_raw.get("pipeline", []) if s.get("type") == "Mixer"), None)
            if not mixer_name or "mixers" not in self.app.config_raw or mixer_name not in self.app.config_raw["mixers"]:
                return

            m_conf = self.app.config_raw["mixers"][mixer_name]
            mappings = m_conf.setdefault("mapping", [])
            
            dest_mapping = next((m for m in mappings if m.get("dest") == row), None)
            
            if event.button() == Qt.LeftButton:
                if not dest_mapping:
                    dest_mapping = {"dest": row, "mute": False, "sources": []}
                    mappings.append(dest_mapping)
                
                src_exists = any(s.get("channel") == col for s in dest_mapping.setdefault("sources", []))
                if not src_exists:
                    dest_mapping["sources"].append({"channel": col, "gain": 0.0, "inverted": False, "mute": False, "scale": "dB"})
                    self.app.aplicar_y_guardar(patch_dict={"mixers": {mixer_name: m_conf}})
                    self.update()

            elif event.button() == Qt.RightButton:
                if dest_mapping:
                    dest_mapping["sources"] = [s for s in dest_mapping.get("sources", []) if s.get("channel") != col]
                    self.app.aplicar_y_guardar(patch_dict={"mixers": {mixer_name: m_conf}})
                    self.update()

    def mouseDoubleClickEvent(self, event):
        if hasattr(self, "_t_timer"): self._t_timer.stop()
        if event.button() != Qt.LeftButton: return

        x, y = event.position().x(), event.position().y()
        in_lbls = self.app.in_labels
        out_lbls = self.app.out_labels

        if 40 <= x <= self.left_margin - 35:
            row = int((y - self.top_margin) // self.cell_h)
            if 0 <= row < len(out_lbls):
                self._prompt_rename(True, row, out_lbls[row])
                return

        if 30 <= y <= self.top_margin:
            col = int((x - self.left_margin) // self.cell_w)
            if 0 <= col < len(in_lbls):
                self._prompt_rename(False, col, in_lbls[col])
                return

    def _prompt_rename(self, is_output, ch_index, old_name):
        dialog = QInputDialog(self)
        title = "Renombrar Canal" if self.app.current_lang == "es" else "Rename Channel"
        label = "Nuevo nombre:" if self.app.current_lang == "es" else "New name:"
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setTextValue(old_name)
        
        dialog.setStyleSheet("""
            QDialog { background-color: #222222; }
            QLabel { color: white; font-weight: bold; font-size: 13px; }
            QLineEdit { background-color: #000000; color: #00ffff; border: 1px solid #555555; padding: 5px; font-size: 14px; }
            QPushButton { background-color: #007bff; color: white; font-weight: bold; padding: 6px 15px; border-radius: 4px; min-width: 80px; }
            QPushButton:hover { background-color: #0056b3; }
        """)
        
        ok = dialog.exec()
        if ok:
            new_name = dialog.textValue().strip()
            if new_name:
                self.app.renombrar_canal(is_output, ch_index, new_name)
                self.update()
                self.actualizar_tamanio()

# --- COMPONENTES VISUALES SECUNDARIOS ---
class ProVUMeter(QWidget, TouchLongPressMixin):
    def __init__(self, name="CH"):
        super().__init__(); self.setMinimumWidth(60); self.level = -80.0; self.peak = -80.0; self.peak_timer = 0; self.name = name
        self.comp_threshold = None; self.is_muted = False
    def set_level(self, db):
        self.level = db if db is not None else -80.0
        if self.level > self.peak: self.peak = self.level; self.peak_timer = 40
        elif self.peak_timer > 0: self.peak_timer -= 1
        else: self.peak -= 0.5
        
        target_gr = 0.0
        if getattr(self, 'is_output', False) and getattr(self, 'comp_threshold', None) is not None:
            ratio = getattr(self, 'comp_ratio', 1.0)
            makeup = getattr(self, 'comp_makeup', 0.0)
            t = self.comp_threshold
            
            # CamillaDSP sólo nos dice el nivel de SALIDA (Lout), es decir, ya comprimido.
            Lout = self.level - makeup
            
            if Lout > t and ratio > 1.0:
                # 1) Calculamos cuánto sobresale este nivel *reducido* por encima del threshold:
                E_out = Lout - t
                
                # 2) Reconstruimos virtualmente el exceso de entrada (E), ya que sabemos que
                # E_out fue el resultado de dividir el exceso original por el Ratio.
                E = E_out * ratio
                
                # 3) Ahora aplicamos tu cálculo EXCEPTO que usamos el 'E' real reconstruido
                # GR = E_in * (1 - 1/R)
                target_gr = E * (1.0 - 1.0 / ratio)
                
        current_gr = getattr(self, 'gr_level', 0.0)
        
        # Suavizado Ataque y Release realista
        attack_coef = 0.4
        release_coef = 0.05
        
        if target_gr > current_gr:
            self.gr_level = current_gr + (target_gr - current_gr) * attack_coef
        else:
            self.gr_level = current_gr + (target_gr - current_gr) * release_coef
            
        if self.gr_level < 0.1 and target_gr == 0.0: 
            self.gr_level = 0.0
        
        self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(10, 10, 10)); fh = 45; bh = h - fh; bx = 18; bw = 22
        p.fillRect(bx, 0, bw, bh, QColor(35, 35, 35))
        p.setPen(Qt.white); p.setFont(QFont("Arial", 10))
        for db in [0, -6, -12, -24, -40, -60, -80]:
            y = bh - ((db + 80) / 80 * bh)
            p.drawLine(bx + bw, int(y), bx + bw + 5, int(y)); p.drawText(bx + bw + 8, int(y) + 3, str(db))
        lh = (max(-80, self.level) + 80) / 80 * bh
        grad = QLinearGradient(0, bh, 0, 0); grad.setColorAt(0, Qt.green); grad.setColorAt(0.7, Qt.yellow); grad.setColorAt(0.9, Qt.red)
        p.fillRect(QRectF(bx, bh - lh, bw, lh), grad)
        
        if getattr(self, 'is_output', False) and getattr(self, 'comp_threshold', None) is not None:
            gr_x = 14; gr_w = 3
            p.fillRect(gr_x, 0, gr_w, bh, QColor(30, 30, 30))
            gr_val = getattr(self, 'gr_level', 0.0)
            
            def get_gr_y(db_val):
                if db_val <= 0: return 0.0
                if db_val >= 30: return 1.0
                return db_val / 30.0
                
            if gr_val > 0.1:
                gr_h = min(bh, get_gr_y(gr_val) * bh)
                p.fillRect(QRectF(gr_x, 0, gr_w, gr_h), QColor(255, 130, 0))
            
            p.setPen(QColor(160, 160, 160))
            p.setFont(QFont("Arial", 6))
            for g_db in [3, 6, 12, 18, 24, 30]:
                gy = get_gr_y(g_db) * bh
                p.drawLine(gr_x-2, int(gy), gr_x, int(gy))
                p.drawText(QRectF(0, int(gy)-5, gr_x-3, 10), Qt.AlignRight | Qt.AlignVCenter, f"-{g_db}")
        
        if getattr(self, 'is_output', False) and self.comp_threshold is not None and self.comp_threshold != 0.0:
            th_y = bh - ((self.comp_threshold + 80) / 80 * bh)
            p.fillRect(QRectF(bx, 0, bw, th_y), QColor(255, 0, 0, 90))
            p.setPen(QPen(Qt.red, 2)); p.drawLine(bx, int(th_y), bx+bw, int(th_y))

        py = bh - ((max(-80, self.peak) + 80) / 80 * bh); p.setPen(QPen(Qt.white, 2.5)); p.drawLine(bx-3, int(py), bx+bw+3, int(py))
        py_txt = int(py) - 12
        if py_txt < 0: py_txt = int(py) + 4
        p.setFont(QFont("Arial", 9, QFont.Bold)); p.setPen(Qt.yellow)
        p.drawText(QRectF(bx - 10, py_txt, bw + 20, 12), Qt.AlignCenter, f"{self.peak:.1f}")
        
        p.setFont(QFont("Arial", 11, QFont.Bold))
        text_rect = QRectF(0, bh + 5, w, 40)
        if getattr(self, 'is_output', False):
            if self.is_muted: p.setPen(Qt.red); p.drawText(text_rect, Qt.AlignCenter, f"{self.name}\n[MUTE]")
            else: p.setPen(Qt.green); p.drawText(text_rect, Qt.AlignCenter, f"{self.name}\n(active)")
        else:
            p.setPen(Qt.white); p.drawText(text_rect, Qt.AlignCenter, self.name)

    def mouseDoubleClickEvent(self, event):
        if hasattr(self, "_t_timer"): self._t_timer.stop()
        if event.button() != Qt.LeftButton: return 
        if getattr(self, 'is_output', False) and hasattr(self, 'app_ref'):
            bh = self.height() - 45; y = event.position().y()
            if y <= bh:
                db = max(-80.0, min(0.0, -80 * (y / bh)))
                self.app_ref.crear_compresor(self.name, self.ch_index, db, self)

    def mousePressEvent(self, event):
        self.check_press(event)
        if not hasattr(self, 'app_ref'): return
        bh = self.height() - 45
        is_text_area = event.position().y() > bh
        
        if event.button() == Qt.RightButton:
            if is_text_area:
                dialog = QInputDialog(self)
                title = "Renombrar Canal" if self.app_ref.current_lang == "es" else "Rename Channel"
                label = "Nuevo nombre:" if self.app_ref.current_lang == "es" else "New name:"
                dialog.setWindowTitle(title)
                dialog.setLabelText(label)
                dialog.setTextValue(self.name)
                
                dialog.setStyleSheet("""
                    QDialog { background-color: #222222; }
                    QLabel { color: white; font-weight: bold; font-size: 13px; }
                    QLineEdit { background-color: #000000; color: #00ffff; border: 1px solid #555555; padding: 5px; font-size: 14px; }
                    QPushButton { background-color: #007bff; color: white; font-weight: bold; padding: 6px 15px; border-radius: 4px; min-width: 80px; }
                    QPushButton:hover { background-color: #0056b3; }
                """)
                
                ok = dialog.exec()
                new_name = dialog.textValue()
                
                if ok and new_name.strip():
                    is_out = getattr(self, 'is_output', False)
                    self.app_ref.renombrar_canal(is_out, self.ch_index, new_name.strip())
            else:
                if getattr(self, 'is_output', False):
                    self.app_ref.borrar_compresor_por_ch(self.ch_index)
                    
        elif event.button() == Qt.LeftButton and is_text_area:
            if getattr(self, 'is_output', False):
                self.is_muted = not self.is_muted
                self.app_ref.toggle_mute(self.ch_index, self.is_muted, self)
                self.update()

    def mouseMoveEvent(self, event):
        self.check_move(event)
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if self.check_release(event): return
        super().mouseReleaseEvent(event)

class ProFader(QWidget, TouchLongPressMixin):
    def __init__(self, name="VOL", ch_index=0, init_db=0.0, mode="mixer"):
        super().__init__(); self.setMinimumWidth(50); self.name = name; self.ch_index = ch_index
        self.db = init_db; self.app_ref = None; self.is_dragging = False; self.mode = mode

    def db_to_y(self, db, h):
        db = max(-30.0, min(10.0, db))
        if db >= 0: return (10.0 - db) / 10.0 * (0.2 * h)
        else: return 0.2 * h + (-db / 30.0) * (0.8 * h)

    def y_to_db(self, y, h):
        if y <= 0.2 * h: db = 10.0 - (y / (0.2 * h)) * 10.0
        else: db = - ((y - 0.2 * h) / (0.8 * h)) * 30.0
        return max(-30.0, min(10.0, db))

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(10, 10, 10)); fh = 45; bh = h - fh; tx = w // 2 - 2
        p.fillRect(tx, 0, 4, bh, QColor(20, 20, 20))
        p.setPen(QColor(100, 100, 100))
        
        p.setFont(QFont("Arial", 6))
        for db in [10, 0, -10, -20, -30]:
            y = self.db_to_y(db, bh); p.drawLine(tx - 6, int(y), tx + 10, int(y))
            
            is_master = getattr(self, "mode", "mixer") == "master"
            if db == 0: 
                p.setPen(Qt.red if is_master else Qt.green)
                p.drawLine(tx - 8, int(y), tx + 12, int(y))
                p.drawText(QRectF(0, int(y)-6, tx - 10, 12), Qt.AlignRight | Qt.AlignVCenter, "0")
                p.setPen(QColor(100, 100, 100))
            else:
                p.drawText(QRectF(0, int(y)-6, tx - 8, 12), Qt.AlignRight | Qt.AlignVCenter, str(db))
            
        fy = self.db_to_y(self.db, bh)
        p.setBrush(QColor(0, 150, 255) if self.is_dragging else QColor(150, 150, 150)); p.setPen(Qt.NoPen)
        p.drawRoundedRect(tx - 12, int(fy) - 6, 28, 12, 3, 3)
        p.setPen(Qt.white); p.drawLine(tx - 10, int(fy), tx + 10, int(fy))
        p.setFont(QFont("Arial", 9)); p.drawText(QRectF(0, bh + 5, w, 15), Qt.AlignCenter, f"{self.db:.1f}")
        p.setFont(QFont("Arial", 11, QFont.Bold)); p.drawText(QRectF(0, bh + 20, w, 20), Qt.AlignCenter, getattr(self, "name", "VOL"))

    def mousePressEvent(self, event):
        self.check_press(event)
        if event.button() == Qt.LeftButton:
            self.is_dragging = True; self.update_db_from_mouse(event.position().y())
        elif event.button() == Qt.RightButton:
            self.db = 0.0; self.enviar_gain(); self.update()

    def mouseMoveEvent(self, event):
        self.check_move(event)
        if self.is_dragging: self.update_db_from_mouse(event.position().y())

    def mouseReleaseEvent(self, event):
        if self.check_release(event): return
        if event.button() == Qt.LeftButton:
            self.is_dragging = False; self.enviar_gain(); self.update()

    def update_db_from_mouse(self, y):
        bh = self.height() - 45; self.db = self.y_to_db(y, bh); self.update()

    def enviar_gain(self):
        if not self.app_ref: return
        if getattr(self, 'mode', 'mixer') == 'master':
            try:
                self.app_ref.ejecutar_comando("SetVolume", float(f"{self.db:.1f}"))
            except Exception as e:
                self.app_ref.log_v.append(f"❌ Error al enviar Master Volume: {e}")
            return
            
        mixer_name = next((s.get("name") for s in self.app_ref.config_raw.get("pipeline", []) if s.get("type") == "Mixer"), None)
        if mixer_name and "mixers" in self.app_ref.config_raw and mixer_name in self.app_ref.config_raw["mixers"]:
            m_conf = self.app_ref.config_raw["mixers"][mixer_name]
            for mapping in m_conf.get("mapping", []):
                if mapping.get("dest") == self.ch_index:
                    for src in mapping.get("sources", []): src["gain"] = float(f"{self.db:.1f}")
            self.app_ref.aplicar_y_guardar(patch_dict={"mixers": {mixer_name: m_conf}})

class DelayLineEdit(QLineEdit, TouchLongPressMixin):
    def __init__(self, text, ch_index, fname, app_ref):
        super().__init__(text)
        self.ch_index = ch_index; self.fname = fname; self.app_ref = app_ref
        self.setContextMenuPolicy(Qt.NoContextMenu)
    def mousePressEvent(self, event):
        self.check_press(event)
        if event.button() == Qt.RightButton:
            self.setText("0.0"); self.app_ref.cambiar_delay(self.ch_index, self.fname, "0.0", self); self.clearFocus(); event.accept()
        else: super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        self.check_move(event)
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if self.check_release(event): return
        super().mouseReleaseEvent(event)

class BaseGraph(QFrame, TouchLongPressMixin):
    def mousePressEvent(self, event):
        self.check_press(event)
        super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        self.check_move(event)
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self, event):
        if self.check_release(event): return
        super().mouseReleaseEvent(event)

    def __init__(self, parent_app):
        super().__init__()
        self.app = parent_app; self.setMinimumHeight(250); self.setMouseTracking(True); self.setFocusPolicy(Qt.StrongFocus)
        self.filters = {}; self.active_drag = None; self.hovered_point = None; self.highlighted_point = None
        self.drag_group = [] 
        self.sample_rate = 44100
        self.colors = [QColor(c) for c in GLOBAL_HEX_COLORS]
        self.warn_box = QFrame(self)
        self.warn_box.setStyleSheet("background-color: rgba(220, 50, 50, 230); border-radius: 6px; border: 1px solid #ffaaaa;")
        self.warn_box.hide(); wl = QHBoxLayout(self.warn_box)
        self.warn_lbl = QLabel(""); self.warn_lbl.setStyleSheet("color: white; font-weight: bold; background: transparent; border: none; font-size: 13px;")
        self.warn_btn = QPushButton("OK"); self.warn_btn.setFixedSize(40, 25)
        self.warn_btn.setStyleSheet("background: white; color: black; border-radius: 3px; font-weight: bold;")
        self.warn_btn.clicked.connect(self.warn_box.hide)
        wl.addWidget(self.warn_lbl); wl.addWidget(self.warn_btn)

    def resizeEvent(self, event):
        super().resizeEvent(event); self.warn_box.resize(self.width() - 40, 45); self.warn_box.move(20, 10)

    def show_warning(self, msg):
        self.warn_lbl.setText(msg); self.warn_box.resize(self.width() - 40, 45); self.warn_box.move(20, 10)
        self.warn_box.show(); QTimer.singleShot(4000, self.warn_box.hide)

    def set_filters(self, d): self.filters = d; self.update()
    def x_to_f(self, x): return math.pow(10, math.log10(20) + (x / self.width()) * (math.log10(20000) - math.log10(20)))
    def f_to_x(self, f): return self.width() * (math.log10(max(20, min(20000, f))) - math.log10(20)) / (math.log10(20000) - math.log10(20))
    def db_to_y(self, db): return self.height() * (12 - max(-24, min(12, db))) / 36

    def draw_grid(self, p, w, h):
        p.fillRect(0, 0, w, h, Qt.black)
        for decade in [10, 100, 1000, 10000]:
            for i in range(1, 10):
                f = decade * i
                if f < 20 or f > 20000: continue
                x = self.f_to_x(f); alpha = 130 if i == 1 else 35
                p.setPen(QPen(QColor(255, 255, 255, alpha), 1)); p.drawLine(int(x), 0, int(x), h)
                if i in [1, 2, 5]:
                    p.setPen(Qt.white); p.setFont(QFont("Arial", 8)); p.drawText(int(x) + 3, h - 10, f"{int(f) if f < 1000 else str(int(f/1000)) + 'k'}")
        for db in range(-24, 13, 3):
            y = self.db_to_y(db); alpha = 180 if db == 0 else 70 if db % 6 == 0 else 25
            p.setPen(QPen(QColor(255, 255, 255, alpha), 1)); p.drawLine(0, int(y), w, int(y))
            if db % 6 == 0: p.setPen(Qt.white); p.drawText(8, int(y) - 5, f"{db}dB")

class EQGraph(BaseGraph):
    def db_to_y(self, db): return self.height() * (12 - max(-12, min(12, db))) / 24
    def y_to_db(self, y): return 12 - (y / self.height()) * 24

    def paintEvent(self, event):
        bypassed_fids = set()
        for step in self.app.config_raw.get("pipeline", []):
            if step.get("type") == "Filter" and step.get("bypassed", False):
                bypassed_fids.update(step.get("names", []))

        self.btn_minus_q_rect = None
        self.btn_plus_q_rect = None
        self.selected_q_fid = None

        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, Qt.black)
        for decade in [10, 100, 1000, 10000]:
            for i in range(1, 10):
                f = decade * i
                if f < 20 or f > 20000: continue
                x = self.f_to_x(f); alpha = 130 if i == 1 else 35
                p.setPen(QPen(QColor(255, 255, 255, alpha), 1)); p.drawLine(int(x), 0, int(x), h)
                if i in [1, 2, 5]:
                    p.setPen(Qt.white); p.setFont(QFont("Arial", 8)); p.drawText(int(x) + 3, h - 10, f"{int(f) if f < 1000 else str(int(f/1000)) + 'k'}")
        for db in range(-12, 13):
            y = self.db_to_y(db); alpha = 180 if db == 0 else 70 if db % 3 == 0 else 25
            p.setPen(QPen(QColor(255, 255, 255, alpha), 1)); p.drawLine(0, int(y), w, int(y))
            if db % 3 == 0: p.setPen(Qt.white); p.drawText(8, int(y) - 5, f"{db}dB")

        target = self.active_drag or self.hovered_point or self.highlighted_point
        by_channel = {}
        for fid, info in self.filters.items():
            dom = info["domain"]
            for ch in info["channels"]:
                if dom == "in" and ch not in self.app.visible_in_channels: continue
                if dom == "out" and ch not in self.app.visible_out_channels: continue
                key = f"{dom}_{ch}"
                if key not in by_channel: by_channel[key] = []
                by_channel[key].append((fid, info["data"]["parameters"]))
            
        for key, params_list in by_channel.items():
            dom, ch = key.split("_"); ch = int(ch)
            path = QPainterPath()
            col = self.colors[ch % len(self.colors)] if ch >= 0 else Qt.white
            if dom == "in": col = col.darker(130) 
            
            for i in range(w + 1):
                f = self.x_to_f(i)
                total_db = sum(calcular_magnitud_biquad(pr, f, self.sample_rate) for fid, pr in params_list if fid not in bypassed_fids)
                y = self.db_to_y(total_db)
                if i == 0: path.moveTo(i, y)
                else: path.lineTo(i, y)
            p.setPen(QPen(col, 2.5)); p.drawPath(path)
            
        for i, (fid, info) in enumerate(self.filters.items()):
            pr = info["data"]["parameters"]; dom = info["domain"]
            is_bypassed = fid in bypassed_fids
            
            visible_chs = [ch for ch in info["channels"] if (dom == "in" and ch in self.app.visible_in_channels) or (dom == "out" and ch in self.app.visible_out_channels)]
            if not visible_chs: continue
            
            ch_names = []
            for ch in visible_chs:
                ch_names.append(self.app.in_labels[ch] if dom == "in" and ch < len(self.app.in_labels) else self.app.out_labels[ch] if dom == "out" and ch < len(self.app.out_labels) else f"CH{ch}")
            
            display_name = f"{i+1} | {dom.upper()}: {','.join(ch_names)}"
            
            ch = visible_chs[0]
            col = self.colors[ch % len(self.colors)] if ch >= 0 else Qt.white
            if dom == "in": col = col.darker(130)
            
            x, y = self.f_to_x(pr["freq"]), self.db_to_y(pr.get("gain", 0))
            sel = (fid == target)
            
            p.setBrush(QBrush(Qt.gray if is_bypassed else (Qt.white if sel else col)))
            p.setPen(Qt.darkGray if is_bypassed else Qt.black)
            p.drawEllipse(QPointF(x, y), 12, 12) 
            
            if is_bypassed:
                p.setPen(Qt.gray)
                display_name += " [BYPASS]"
            else:
                p.setPen(col)
                
            p.setFont(QFont("Arial", 10, QFont.Bold))
            p.drawText(QRectF(x - 60, y - 25, 120, 22), Qt.AlignCenter, display_name)
            
            if sel:
                self.selected_q_fid = fid
                txt = f"#{i+1} | F:{pr['freq']:.0f}Hz | G:{pr.get('gain',0):.1f}dB | Q:{pr.get('q',1.0):.2f}"
                p.setBrush(QBrush(QColor(0,0,0,235))); p.setPen(QPen(col, 1.5))
                bw, bh = 150, 35; bx = int(x) - (bw // 2); by = int(y) - bh - 10 
                if by < 0: by = int(y) + 10 
                if by + bh > h: by = h - bh
                if bx < 0: bx = 0
                if bx + bw > w: bx = w - bw
                
                p.drawRoundedRect(bx, by, bw, bh, 5, 5)
                p.setPen(Qt.white); p.setFont(QFont("Arial", 10, QFont.Bold)) 
                p.drawText(QRectF(bx, by, bw, bh/2), Qt.AlignCenter, txt)
                p.setPen(QColor(180, 180, 180)); p.setFont(QFont("Arial", 10))
                p.drawText(QRectF(bx, by + bh/2 - 5, bw, bh/2), Qt.AlignCenter, str(pr.get('type', '')))
                
                qw, qh = 60, 45
                btn_my = int(y) - qh // 2
                self.btn_minus_q_rect = QRectF(x - 50 - qw, btn_my, qw, qh)
                self.btn_plus_q_rect = QRectF(x + 50, btn_my, qw, qh)
                
                p.setBrush(QBrush(QColor(20, 20, 20, 220)))
                p.setPen(QPen(Qt.white, 2))
                p.drawRoundedRect(self.btn_minus_q_rect, 5, 5)
                p.drawRoundedRect(self.btn_plus_q_rect, 5, 5)
                
                p.setPen(Qt.white); p.setFont(QFont("Arial", 14, QFont.Bold))
                p.drawText(self.btn_minus_q_rect, Qt.AlignCenter, "-Q")
                p.drawText(self.btn_plus_q_rect, Qt.AlignCenter, "+Q")

    def mouseDoubleClickEvent(self, event):
        if hasattr(self, "_t_timer"): self._t_timer.stop() 
        if event.button() != Qt.LeftButton: return 
        
        pos = event.position()
        if hasattr(self, 'btn_plus_q_rect') and self.btn_plus_q_rect and self.btn_plus_q_rect.contains(pos):
            self.modify_q_step(0.1)
            event.accept()
            return
        if hasattr(self, 'btn_minus_q_rect') and self.btn_minus_q_rect and self.btn_minus_q_rect.contains(pos):
            self.modify_q_step(-0.1)
            event.accept()
            return
            
        if not self.app.visible_in_channels and not self.app.visible_out_channels:
            self.show_warning(LANG[self.app.current_lang]["warn_msg"])
            return
        self.app.crear_filtros_eq(self.x_to_f(event.position().x()), self.y_to_db(event.position().y()))

    def mousePressEvent(self, event):
        self.check_press(event)
        pos = event.position()
        
        if not hasattr(self, '_last_q_click'): self._last_q_click = 0
        now = time.time()
        
        if hasattr(self, 'btn_plus_q_rect') and self.btn_plus_q_rect and self.btn_plus_q_rect.contains(pos):
            if hasattr(self, "_t_timer"): self._t_timer.stop()
            if event.button() == Qt.LeftButton and now - self._last_q_click > 0.2:
                self.modify_q_step(0.1)
                self._last_q_click = now
            event.accept()
            return
        if hasattr(self, 'btn_minus_q_rect') and self.btn_minus_q_rect and self.btn_minus_q_rect.contains(pos):
            if hasattr(self, "_t_timer"): self._t_timer.stop()
            if event.button() == Qt.LeftButton and now - self._last_q_click > 0.2:
                self.modify_q_step(-0.1)
                self._last_q_click = now
            event.accept()
            return
            
        self.setFocus(); drag_candidates = []
        for fid, info in self.filters.items():
            dom = info["domain"]
            visible_chs = [ch for ch in info["channels"] if (dom == "in" and ch in self.app.visible_in_channels) or (dom == "out" and ch in self.app.visible_out_channels)]
            if not visible_chs: continue
            p = info["data"]["parameters"]; fx, fy = self.f_to_x(p["freq"]), self.db_to_y(p.get("gain", 0))
            if math.hypot(event.position().x()-fx, event.position().y()-fy) < 35: 
                drag_candidates.append((fid, p))
                
        if drag_candidates:
            if event.button() == Qt.RightButton:
                self.app.borrar_eq(drag_candidates[0][0])
                self.hovered_point = None; self.active_drag = None; self.highlighted_point = None
            elif event.button() == Qt.LeftButton:
                primary_fid, primary_p = drag_candidates[0]
                self.active_drag = primary_fid; self.app.marcar_fila_activa_eq(primary_fid)
                self.drag_group = []
                for f_id, f_info in self.filters.items():
                    d2 = f_info["domain"]
                    v2 = [ch for ch in f_info["channels"] if (d2 == "in" and ch in self.app.visible_in_channels) or (d2 == "out" and ch in self.app.visible_out_channels)]
                    if not v2: continue
                    p2 = f_info["data"]["parameters"]
                    if abs(p2.get("freq",0) - primary_p.get("freq",0)) < 1.0 and abs(p2.get("gain", 0) - primary_p.get("gain", 0)) < 0.1 and abs(p2.get("q", 1) - primary_p.get("q", 1)) < 0.01:
                        self.drag_group.append(f_id)
            return
                
    def mouseMoveEvent(self, event):
        self.check_move(event)
        if self.active_drag and (event.buttons() & Qt.LeftButton):
            new_f = float(self.x_to_f(event.position().x()))
            new_g = float(self.y_to_db(event.position().y()))
            for fid in getattr(self, "drag_group", [self.active_drag]):
                if fid in self.filters:
                    p = self.filters[fid]["data"]["parameters"]
                    p["freq"] = new_f
                    if "gain" in p: p["gain"] = new_g
                    self.app.actualizar_celda_eq(fid, 2, f"{new_f:.0f}")
                    if "gain" in p: self.app.actualizar_celda_eq(fid, 3, f"{new_g:.1f}")
            self.update()
        else:
            old = self.hovered_point; self.hovered_point = None
            for fid, info in self.filters.items():
                dom = info["domain"]
                visible_chs = [ch for ch in info["channels"] if (dom == "in" and ch in self.app.visible_in_channels) or (dom == "out" and ch in self.app.visible_out_channels)]
                if not visible_chs: continue
                p = info["data"]["parameters"]; fx, fy = self.f_to_x(p["freq"]), self.db_to_y(p.get("gain", 0))
                if math.hypot(event.position().x()-fx, event.position().y()-fy) < 35: 
                    self.hovered_point = fid; break
            if old != self.hovered_point: self.update()
            
    def wheelEvent(self, event):
        self.setFocus()
        target = self.active_drag or self.hovered_point or self.highlighted_point
        if not target:
            for fid, info in self.filters.items():
                dom = info["domain"]
                visible_chs = [ch for ch in info["channels"] if (dom == "in" and ch in self.app.visible_in_channels) or (dom == "out" and ch in self.app.visible_out_channels)]
                if not visible_chs: continue
                p = info["data"]["parameters"]; fx, fy = self.f_to_x(p["freq"]), self.db_to_y(p.get("gain", 0))
                if math.hypot(event.position().x()-fx, event.position().y()-fy) < 35: 
                    target = fid; break
        if target and target in self.filters:
            primary_p = self.filters[target]["data"]["parameters"]
            step = 0.1 if event.angleDelta().y() > 0 else -0.1
            new_q = max(0.1, min(20, primary_p.get("q", 1.0) + step))
            
            group = []
            for f_id, f_info in self.filters.items():
                d2 = f_info["domain"]
                v2 = [ch for ch in f_info["channels"] if (d2 == "in" and ch in self.app.visible_in_channels) or (d2 == "out" and ch in self.app.visible_out_channels)]
                if not v2: continue
                p2 = f_info["data"]["parameters"]
                if abs(p2.get("freq",0) - primary_p.get("freq",0)) < 1.0 and abs(p2.get("gain", 0) - primary_p.get("gain", 0)) < 0.1 and abs(p2.get("q", 1) - primary_p.get("q", 1)) < 0.01:
                    group.append(f_id)

            patch_filters = {}
            for fid in group:
                p = self.filters[fid]["data"]["parameters"]
                p["q"] = new_q
                patch_filters[fid] = {"parameters": {"q": new_q}}
                self.app.actualizar_celda_eq(fid, 4, f"{new_q:.2f}")
                
            self.app.aplicar_y_guardar(patch_dict={"filters": patch_filters})
            self.update(); event.accept()
            
    def mouseReleaseEvent(self, event): 
        if self.check_release(event): return
        if event.button() == Qt.LeftButton and self.active_drag:
            patch_filters = {}
            for fid in getattr(self, "drag_group", [self.active_drag]):
                if fid in self.filters:
                    p = self.filters[fid]["data"]["parameters"]
                    patch_filters[fid] = {"parameters": {"freq": p["freq"], "gain": p.get("gain", 0.0)}}
            self.app.aplicar_y_guardar(patch_dict={"filters": patch_filters})
            self.active_drag = None

    def modify_q_step(self, step):
        target = getattr(self, 'selected_q_fid', None)
        if not target or target not in self.filters: return
        primary_p = self.filters[target]["data"]["parameters"]
        new_q = max(0.1, min(20, primary_p.get("q", 1.0) + step))
        
        group = []
        for f_id, f_info in self.filters.items():
            d2 = f_info["domain"]
            v2 = [ch for ch in f_info["channels"] if (d2 == "in" and self.app.visible_in_channels and ch in self.app.visible_in_channels) or (d2 == "out" and self.app.visible_out_channels and ch in self.app.visible_out_channels)]
            if not v2: continue
            p2 = f_info["data"]["parameters"]
            if abs(p2.get("freq",0) - primary_p.get("freq",0)) < 1.0 and abs(p2.get("gain", 0) - primary_p.get("gain", 0)) < 0.1 and abs(p2.get("q", 1) - primary_p.get("q", 1)) < 0.01:
                group.append(f_id)

        patch_filters = {}
        for fid in group:
            p = self.filters[fid]["data"]["parameters"]
            p["q"] = new_q
            patch_filters[fid] = {"parameters": {"q": new_q}}
            self.app.actualizar_celda_eq(fid, 4, f"{new_q:.2f}")
            
        self.app.aplicar_y_guardar(patch_dict={"filters": patch_filters})
        self.update()

class CrossoverGraph(BaseGraph):
    def paintEvent(self, event):
        bypassed_fids = set()
        for step in self.app.config_raw.get("pipeline", []):
            if step.get("type") == "Filter" and step.get("bypassed", False):
                bypassed_fids.update(step.get("names", []))

        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); w, h = self.width(), self.height()
        self.draw_grid(p, w, h)
        target = self.active_drag or self.hovered_point or self.highlighted_point

        by_channel = {}
        for fid, info in self.filters.items():
            dom = info["domain"]
            for ch in info["channels"]:
                if dom == "in" or ch not in self.app.visible_out_channels: continue 
                key = f"{dom}_{ch}"
                if key not in by_channel: by_channel[key] = []
                by_channel[key].append((fid, info["data"]["parameters"]))
            
        for key, params_list in by_channel.items():
            dom, ch = key.split("_"); ch = int(ch)
            path = QPainterPath()
            col = self.colors[ch % len(self.colors)] if ch >= 0 else Qt.white
            
            for i in range(w + 1):
                f = self.x_to_f(i)
                total_db = sum(calcular_magnitud_crossover(pr, f) for fid, pr in params_list if fid not in bypassed_fids)
                y = self.db_to_y(total_db)
                if i == 0: path.moveTo(i, y)
                else: path.lineTo(i, y)
            p.setPen(QPen(col, 2.5)); p.drawPath(path)
            
        for i, (fid, info) in enumerate(self.filters.items()):
            pr = info["data"]["parameters"]; dom = info["domain"]
            is_bypassed = fid in bypassed_fids
            
            visible_chs = [ch for ch in info["channels"] if dom == "out" and ch in self.app.visible_out_channels]
            if not visible_chs: continue
            
            ch_names = [self.app.out_labels[c] if c < len(self.app.out_labels) else f"CH{c}" for c in visible_chs]
            display_name = f"{i+1} | {','.join(ch_names)}"
            
            ch = visible_chs[0]
            col = self.colors[ch % len(self.colors)] if ch >= 0 else Qt.white
            f_val = float(pr.get("freq", 1000))
            db_val = calcular_magnitud_crossover(pr, f_val)
            x, y = self.f_to_x(f_val), self.db_to_y(db_val)
            
            sel = (fid == target)
            p.setBrush(QBrush(Qt.gray if is_bypassed else (Qt.white if sel else col)))
            p.setPen(Qt.darkGray if is_bypassed else Qt.black)
            p.drawEllipse(QPointF(x, y), 12, 12) 
            
            if is_bypassed:
                p.setPen(Qt.gray)
                display_name += " [BYPASS]"
            else:
                p.setPen(col)
                
            p.setFont(QFont("Arial", 10, QFont.Bold)) 
            p.drawText(QRectF(x - 50, y - 25, 100, 22), Qt.AlignCenter, display_name)
            
            if sel:
                txt = f"#{i+1} | F:{pr.get('freq', 1000):.0f}Hz | Ord:{pr.get('order', 2)} | {ch_names[0]}"
                p.setBrush(QBrush(QColor(0,0,0,235))); p.setPen(QPen(col, 1.5))
                bw, bh = 150, 35; bx = int(x) - (bw // 2); by = int(y) - bh - 10 
                if by < 0: by = int(y) + 10 
                if by + bh > h: by = h - bh
                if bx < 0: bx = 0
                if bx + bw > w: bx = w - bw
                
                p.drawRoundedRect(bx, by, bw, bh, 5, 5)
                p.setPen(Qt.white); p.setFont(QFont("Arial", 10, QFont.Bold)) 
                p.drawText(QRectF(bx, by, bw, bh/2), Qt.AlignCenter, txt)
                p.setPen(QColor(180, 180, 180)); p.setFont(QFont("Arial", 10))
                p.drawText(QRectF(bx, by + bh/2 - 5, bw, bh/2), Qt.AlignCenter, str(pr.get('type', '')))

    def mouseDoubleClickEvent(self, event):
        if hasattr(self, "_t_timer"): self._t_timer.stop() 
        if event.button() != Qt.LeftButton: return 
        if len(self.app.visible_out_channels) > 0:
            self.app.crear_filtros_crossover(self.x_to_f(event.position().x()))
        else:
            self.show_warning(LANG[self.app.current_lang]["cross_warn_msg"])
        
    def mousePressEvent(self, event):
        self.check_press(event)
        self.setFocus(); drag_candidates = []
        for fid, info in self.filters.items():
            dom = info["domain"]
            visible_chs = [ch for ch in info["channels"] if dom == "out" and ch in self.app.visible_out_channels]
            if not visible_chs: continue
            p = info["data"]["parameters"]; f_val = float(p.get("freq", 1000))
            fx, fy = self.f_to_x(f_val), self.db_to_y(calcular_magnitud_crossover(p, f_val))
            if math.hypot(event.position().x()-fx, event.position().y()-fy) < 35: 
                drag_candidates.append((fid, p))
                
        if drag_candidates:
            if event.button() == Qt.RightButton:
                self.app.borrar_crossover(drag_candidates[0][0])
                self.hovered_point = None; self.active_drag = None; self.highlighted_point = None
            elif event.button() == Qt.LeftButton:
                primary_fid, primary_p = drag_candidates[0]
                self.active_drag = primary_fid; self.app.marcar_fila_activa_cross(primary_fid)
                self.drag_group = []
                for f_id, f_info in self.filters.items():
                    d2 = f_info["domain"]
                    v2 = [ch for ch in f_info["channels"] if d2 == "out" and ch in self.app.visible_out_channels]
                    if not v2: continue
                    p2 = f_info["data"]["parameters"]
                    if abs(p2.get("freq",0) - primary_p.get("freq",0)) < 1.0 and p2.get("order") == primary_p.get("order") and p2.get("type") == primary_p.get("type"):
                        self.drag_group.append(f_id)
            return
                
    def mouseMoveEvent(self, event):
        if self.active_drag and (event.buttons() & Qt.LeftButton):
            new_f = float(self.x_to_f(event.position().x()))
            for fid in getattr(self, "drag_group", [self.active_drag]):
                if fid in self.filters:
                    p = self.filters[fid]["data"]["parameters"]
                    p["freq"] = new_f
                    self.app.actualizar_celda_cross(fid, 2, f"{new_f:.0f}")
            self.update()
        else:
            old = self.hovered_point; self.hovered_point = None
            for fid, info in self.filters.items():
                dom = info["domain"]
                visible_chs = [ch for ch in info["channels"] if dom == "out" and ch in self.app.visible_out_channels]
                if not visible_chs: continue
                p = info["data"]["parameters"]; f_val = float(p.get("freq", 1000))
                fx, fy = self.f_to_x(f_val), self.db_to_y(calcular_magnitud_crossover(p, f_val))
                if math.hypot(event.position().x()-fx, event.position().y()-fy) < 35: 
                    self.hovered_point = fid; break
            if old != self.hovered_point: self.update()
            
    def wheelEvent(self, event):
        self.setFocus()
        target = self.active_drag or self.hovered_point or self.highlighted_point
        if not target:
            for fid, info in self.filters.items():
                dom = info["domain"]
                visible_chs = [ch for ch in info["channels"] if dom == "out" and ch in self.app.visible_out_channels]
                if not visible_chs: continue
                p = info["data"]["parameters"]; f_val = float(p.get("freq", 1000))
                fx, fy = self.f_to_x(f_val), self.db_to_y(calcular_magnitud_crossover(p, f_val))
                if math.hypot(event.position().x()-fx, event.position().y()-fy) < 35: 
                    target = fid; break
                    
        if target and target in self.filters:
            primary_p = self.filters[target]["data"]["parameters"]
            tipo = primary_p.get("type", "")
            
            step = 1 if event.angleDelta().y() > 0 else -1
            new_order = int(primary_p.get("order", 2)) + step
            new_order = max(1, min(4, new_order))
                
            group = []
            for f_id, f_info in self.filters.items():
                d2 = f_info["domain"]
                v2 = [ch for ch in f_info["channels"] if d2 == "out" and ch in self.app.visible_out_channels]
                if not v2: continue
                p2 = f_info["data"]["parameters"]
                if abs(p2.get("freq",0) - primary_p.get("freq",0)) < 1.0 and p2.get("order") == primary_p.get("order") and p2.get("type") == primary_p.get("type"):
                    group.append(f_id)

            patch_filters = {}
            for fid in group:
                p = self.filters[fid]["data"]["parameters"]
                p["order"] = new_order
                patch_filters[fid] = {"parameters": {"order": new_order}}
                
            self.app.aplicar_y_guardar(patch_dict={"filters": patch_filters})
            self.app.actualizar_tabla_crossover_ui()
            self.update(); event.accept()
            
    def mouseReleaseEvent(self, event): 
        if event.button() == Qt.LeftButton and self.active_drag:
            patch_filters = {}
            for fid in getattr(self, "drag_group", [self.active_drag]):
                if fid in self.filters:
                    p = self.filters[fid]["data"]["parameters"]
                    patch_filters[fid] = {"parameters": {"freq": p["freq"]}}
            self.app.aplicar_y_guardar(patch_dict={"filters": patch_filters})
            self.active_drag = None

# --- APP ---
class PEQApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CamillaDSP Pro Master - Android")
        self.setMinimumSize(1024, 600)
        self.resize(1250, 680)
        self.setStyleSheet("QMainWindow { background: #050505; } QLabel { color: #fff; }")
        
        c = QWidget()
        self.layout = QVBoxLayout(c)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(c)
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        self.console_window = ConsoleWindow()
        self.log_v = self.console_window.log_v
        
        self.filtros_biquad = {}
        self.filtros_crossover = {}
        self.config_raw = {}
        self.v_in = []; self.v_out = []
        self.vu_in_widgets = []
        self.vu_out_widgets = []
        self.in_labels = []
        self.out_labels = [] 
        
        self.visible_in_channels = set()
        self.visible_out_channels = set()
        self.ch_in_buttons = {}
        self.ch_out_buttons = {}
        
        self.sample_rate = 44100
        self.auto_samplers = {}
        self.current_lang = "es"
        self.all_outputs_muted = False 
        
        self.init_login()

    def clean_name(self, n): return re.sub(r'[^a-zA-Z0-9]', '', str(n))

    def _log_if_error(self, res, prefix):
        if res is None: return
        msg = str(res)
        if "error" in msg.lower() or "invalid" in msg.lower() or "unknown field" in msg.lower():
            self.log_v.append(f"❌ {prefix}: {msg}")

    # ================= NUEVO SISTEMA DE ESCÁNER ================= 
    def ejecutar_comando(self, comando, payload=None):
        try:
            if payload is not None:
                if isinstance(payload, str):
                    try:
                        p_str = json.dumps(json.loads(payload), indent=2)
                    except:
                        p_str = payload
                else:
                    p_str = json.dumps(payload, indent=2)
                
                self.log_v.append(f"\n--- SENT -> {comando} ---\n{p_str}\n-----------------")
                res = self.cdsp.query(comando, payload)
            else:
                if comando not in ["GetPlaybackLevels", "GetCaptureLevels"]:
                    self.log_v.append(f"\n--- SENT -> {comando} ---")
                res = self.cdsp.query(comando)
            
            if comando not in ["GetPlaybackLevels", "GetCaptureLevels"]:
                res_str = json.dumps(res, indent=2) if isinstance(res, (dict, list)) else str(res)
                self.log_v.append(f"--- RCVD <- {comando} ---\n{res_str}\n-----------------")
            
            return res
        except Exception as e:
            if comando not in ["GetPlaybackLevels", "GetCaptureLevels"]:
                self.log_v.append(f"\n❌ ERROR EN '{comando}': {str(e)}\n-----------------")
            raise e
    # ==========================================================

    def aplicar_y_guardar(self, patch_dict=None, reload=False):
        try:
            if patch_dict and not reload:
                res = self.ejecutar_comando("PatchConfig", patch_dict)
                self._log_if_error(res, "Error PatchConfig")
            else:
                res1 = self.ejecutar_comando("SetConfigJson", json.dumps(self.config_raw))
                self._log_if_error(res1, "Error SetConfig")
        except Exception as global_e:
            self.log_v.append(f"❌ Error Critico Comunicacion: {global_e}")

    def init_login(self):
        self.p_login = QWidget(); l_main = QVBoxLayout(self.p_login); card = QFrame(); card.setFixedWidth(500); card.setObjectName("MainCard")
        
        card.setStyleSheet("""
            #MainCard { background: #121212; border-radius: 15px; border: 2px solid #00ffff; } 
            QLineEdit { height: 35px; background: #1a1a1a; color: white; border: 1px solid #444; padding: 5px; font-size: 16px;} 
            QPushButton { height: 45px; background: #007bff; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; } 
        """)
        
        l_card = QVBoxLayout(card); l_card.setContentsMargins(30, 30, 30, 30); l_card.setSpacing(20)
        
        h_top = QHBoxLayout()
        self.btn_lang = QPushButton(LANG[self.current_lang]["btn_lang"]); self.btn_lang.setFixedSize(80, 30); self.btn_lang.setStyleSheet("background: #555;")
        self.btn_lang.clicked.connect(self.toggle_lang)
        self.btn_reset_login = QPushButton("RESET"); self.btn_reset_login.setFixedSize(80, 30)
        self.btn_reset_login.setStyleSheet("QPushButton { background: #8b0000; color: white; font-weight: bold; font-size: 12px; border-radius: 4px; } QPushButton:hover { background: #d32f2f; }")
        self.btn_reset_login.clicked.connect(self.reset_from_login)
        self.btn_help = QPushButton(LANG[self.current_lang]["btn_help"]); self.btn_help.setFixedSize(120, 30); self.btn_help.setStyleSheet("background: #28a745;")
        self.btn_help.clicked.connect(self.show_help)
        
        h_top.addWidget(self.btn_lang); h_top.addStretch(); h_top.addWidget(self.btn_reset_login); h_top.addWidget(self.btn_help); l_card.addLayout(h_top)

        self.lbl_title = QLabel(LANG[self.current_lang]["title"])
        self.lbl_title.setAlignment(Qt.AlignCenter); self.lbl_title.setStyleSheet("font-size: 24px; color:#00ffff; border:none; font-weight: bold;")
        l_card.addWidget(self.lbl_title)
        
        saved_ip, saved_port = "127.0.0.1", "1234"
        try:
            with open("app_settings.json", "r") as f:
                settings = json.load(f)
                saved_ip, saved_port = settings.get("ip", "127.0.0.1"), str(settings.get("port", "1234"))
        except: pass 

        h_ip_port = QHBoxLayout()
        v_ip = QVBoxLayout()
        self.lbl_ip = QLabel(LANG[self.current_lang]["ip_label"]); v_ip.addWidget(self.lbl_ip)
        self.ip_i = QLineEdit(saved_ip); v_ip.addWidget(self.ip_i)
        v_port = QVBoxLayout()
        self.lbl_port = QLabel(LANG[self.current_lang]["port_label"]); v_port.addWidget(self.lbl_port)
        self.port_i = QLineEdit(saved_port); self.port_i.setFixedWidth(120); v_port.addWidget(self.port_i)
        h_ip_port.addLayout(v_ip); h_ip_port.addLayout(v_port); l_card.addLayout(h_ip_port)
        
        self.btn_s = QPushButton(LANG[self.current_lang]["btn_scan"]); self.btn_s.clicked.connect(self.scan_and_start); l_card.addWidget(self.btn_s)
        
        self.btn_web_login = QPushButton("Camilla WEB")
        self.btn_web_login.setFixedHeight(30)
        self.btn_web_login.setStyleSheet("QPushButton { background: #17a2b8; color: white; font-weight: bold; font-size: 11px; border: 1px solid #117a8b; border-radius: 4px; padding: 2px 10px; } QPushButton:hover { background: #138496; }")
        self.btn_web_login.clicked.connect(lambda: webbrowser.open(f"http://{self.ip_i.text().strip()}:5005"))
        l_card.addWidget(self.btn_web_login)
        
        l_main.addStretch(); hc = QHBoxLayout(); hc.addStretch(); hc.addWidget(card); hc.addStretch(); l_main.addLayout(hc); l_main.addStretch()
        self.stack.addWidget(self.p_login)

    def toggle_lang(self):
        self.current_lang = "en" if self.current_lang == "es" else "es"
        d = LANG[self.current_lang]
        
        if getattr(self, 'btn_lang', None): self.btn_lang.setText(d["btn_lang"])
        if getattr(self, 'btn_help', None): self.btn_help.setText(d["btn_help"])
        if getattr(self, 'btn_help2', None): self.btn_help2.setText("Ayuda" if self.current_lang == "es" else "Help")
        if getattr(self, 'lbl_title', None): self.lbl_title.setText(d["title"])
        if getattr(self, 'lbl_ip', None): self.lbl_ip.setText(d["ip_label"])
        if getattr(self, 'lbl_port', None): self.lbl_port.setText(d["port_label"])
        if getattr(self, 'btn_s', None): self.btn_s.setText(d["btn_scan"])
            
        if getattr(self, 'tabs', None) is not None:
            try:
                self.tabs.setTabText(0, "VÚMETROS Y DINÁMICA" if self.current_lang == "es" else "VUMETERS & DYNAMICS")
                self.tabs.setTabText(1, "FILTROS Y EQ" if self.current_lang == "es" else "EQ & FILTERS")
                self.tabs.setTabText(2, "CROSSOVERS")
                self.tabs.setTabText(3, "MIXER")
            except: pass

        if getattr(self, 'btn_lang_studio', None):
            self.btn_lang_studio.setText(d["btn_lang"])
        if getattr(self, 'btn_show_console', None):
            self.btn_show_console.setText("Log")
        if getattr(self, 'btn_importar_cfg', None):
            self.btn_importar_cfg.setText("Imp Cfg")
        if getattr(self, 'btn_exportar_cfg', None):
            self.btn_exportar_cfg.setText("Exp Cfg")
        if getattr(self, 'btn_default_cfg', None):
            self.btn_default_cfg.setText("Reset")
        if getattr(self, 'btn_importar', None):
            self.btn_importar.setText("Imp EQ")
        if getattr(self, 'btn_exportar', None):
            self.btn_exportar.setText("Exp EQ")
        
        if getattr(self, 'lbl_view', None):
            self.lbl_view.setText("VISTA:" if self.current_lang == "es" else "VIEW:")
        if getattr(self, 'btn_view_all', None):
            self.btn_view_all.setText("TODO" if self.current_lang == "es" else "ALL")
            self.btn_view_in.setText("ENTRADAS" if self.current_lang == "es" else "INPUTS")
            self.btn_view_out.setText("SALIDAS" if self.current_lang == "es" else "OUTPUTS")

    def show_help(self): diag = HelpDialog(self.current_lang, self); diag.exec()

    def get_labels(self, target):
        num_channels, lbls = 0, []
        if target == "playback":
            mixer_name = next((s.get("name") for s in self.config_raw.get("pipeline", []) if s.get("type") == "Mixer"), None)
            if mixer_name and "mixers" in self.config_raw and mixer_name in self.config_raw["mixers"]:
                m_conf = self.config_raw["mixers"][mixer_name]
                num_channels = m_conf.get("channels", {}).get("out", 0)
                lbls = m_conf.get("labels", [])
        if num_channels == 0:
            dev = self.config_raw.get("devices", {}).get(target, {})
            num_channels = dev.get("channels", 2)
            lbls = dev.get("labels", [])
            
        if not lbls: 
            lbls = []
            
        pref = "IN" if target == "capture" else "OUT"
        return [lbls[i] if i < len(lbls) and lbls[i] else f"{pref} {i}" for i in range(num_channels)]

    def _get_chs_from_step(self, step):
        if "channels" in step and isinstance(step["channels"], list):
            return step["channels"]
        if "channel" in step:
            return [step["channel"]]
        return []

    def renombrar_canal(self, is_output, ch_index, new_name):
        if is_output:
            mixer_name = next((s.get("name") for s in self.config_raw.get("pipeline", []) if s.get("type") == "Mixer"), None)
            if mixer_name and "mixers" in self.config_raw and mixer_name in self.config_raw["mixers"]:
                m_conf = self.config_raw["mixers"][mixer_name]
                labels = m_conf.get("labels") or []
                while len(labels) <= ch_index: labels.append(f"OUT {len(labels)}")
                labels[ch_index] = new_name
                m_conf["labels"] = labels
            else:
                dev = self.config_raw.setdefault("devices", {}).setdefault("playback", {})
                labels = dev.get("labels") or []
                while len(labels) <= ch_index: labels.append(f"OUT {len(labels)}")
                labels[ch_index] = new_name
                dev["labels"] = labels
                
            self.out_labels[ch_index] = new_name
            if ch_index < len(self.v_out): self.v_out[ch_index].name = new_name
            if ch_index in self.ch_out_buttons: 
                btn = self.ch_out_buttons[ch_index]
                btn.setText(f"{'🔴' if '🔴' in btn.text() else '🔊'} {new_name}")
        else:
            dev = self.config_raw.setdefault("devices", {}).setdefault("capture", {})
            labels = dev.get("labels") or []
            while len(labels) <= ch_index: labels.append(f"IN {len(labels)}")
            labels[ch_index] = new_name
            dev["labels"] = labels
            
            self.in_labels[ch_index] = new_name
            if ch_index < len(self.v_in): self.v_in[ch_index].name = new_name
            if ch_index in self.ch_in_buttons:
                btn = self.ch_in_buttons[ch_index]
                btn.setText(f"{'🔴' if '🔴' in btn.text() else '🔊'} {new_name}")

        self.aplicar_y_guardar(reload=True)
        self.log_v.append(f"✅ Canal renombrado a '{new_name}'")

        self.combo_ch_list = [f"in {i}: {lbl}" for i, lbl in enumerate(self.in_labels)] + [f"out {i}: {lbl}" for i, lbl in enumerate(self.out_labels)]
        self.combo_out_ch_list = [f"out {i}: {lbl}" for i, lbl in enumerate(self.out_labels)]
        
        self.actualizar_tabla_ui()
        self.actualizar_tabla_crossover_ui()
        self.actualizar_iconos_bypass()
        
        if hasattr(self, 'graph'): self.graph.update()
        if hasattr(self, 'cross_graph'): self.cross_graph.update()
        if hasattr(self, 'mixer_graph'): 
            self.mixer_graph.actualizar_tamanio()
            self.mixer_graph.update()
        for vu in self.v_in + self.v_out: vu.update()

    def borrar_compresor_por_ch(self, ch_index):
        for pid, pdata in self.config_raw.get("processors", {}).items():
            if pdata.get("type") == "Compressor" and pdata.get("parameters", {}).get("process_channels", [-1])[0] == ch_index:
                self.borrar_compresor_por_id(pid)
                return

    def limpiar_memoria(self):
        if hasattr(self, 't') and self.t.isActive():
            self.t.stop()
        if hasattr(self, 'tabs') and self.tabs is not None:
            try: self.tabs.currentChanged.disconnect()
            except: pass
        
        self.tabs = None
        self.channel_selection_panel = None
        self.v_in.clear()
        self.v_out.clear()
        self.vu_in_widgets.clear()
        self.vu_out_widgets.clear()
        self.ch_in_buttons.clear()
        self.ch_out_buttons.clear()
        self.auto_samplers.clear()
        
        while self.stack.count() > 1:
            w = self.stack.widget(1)
            self.stack.removeWidget(w)
            w.deleteLater()

    def parse_and_build_ui(self):
        self.limpiar_memoria()
        
        self.sample_rate = self.config_raw.get("devices", {}).get("samplerate", 44100)
        self.in_labels = self.get_labels("capture")
        self.out_labels = self.get_labels("playback")
        
        self.visible_in_channels = set(range(len(self.in_labels)))
        self.visible_out_channels = set(range(len(self.out_labels)))
        
        self.asegurar_mixer_global()

        pipeline = self.config_raw.get("pipeline", [])
        mixer_idx = next((i for i, s in enumerate(pipeline) if s.get("type") == "Mixer"), -1)
        
        all_f = self.config_raw.get("filters", {})
        self.filtros_biquad, self.filtros_crossover = {}, {}
        biquad_types = ["Peaking", "Highshelf", "Lowshelf", "Highpass", "Lowpass"]
        cross_types = ["ButterworthHighpass", "ButterworthLowpass", "LinkwitzRileyHighpass", "LinkwitzRileyLowpass"]
        
        for fid, d in all_f.items():
            t = d.get("type")
            if t in ["Biquad", "BiquadCombo"]:
                domain, chs = "out", []
                for idx, step in enumerate(pipeline):
                    if step.get("type") == "Filter" and fid in step.get("names", []):
                        domain = "in" if mixer_idx != -1 and idx < mixer_idx else "out"
                        chs = self._get_chs_from_step(step)
                        break
                
                if not chs: continue
                
                p_type = d.get("parameters", {}).get("type", "")
                
                if t == "Biquad" and p_type in biquad_types:
                    self.filtros_biquad[fid] = {"data": d, "domain": domain, "channels": chs}
                elif t == "BiquadCombo" and p_type in cross_types:
                    self.filtros_crossover[fid] = {"data": d, "domain": domain, "channels": chs}
        
        self.init_studio()
        self.stack.setCurrentIndex(1)
        
        if not hasattr(self, 't'):
            self.t = QTimer()
            self.t.timeout.connect(self.up_v)
        self.t.start(50)

    def asegurar_mixer_global(self):
        changed = False
        pipeline = self.config_raw.setdefault("pipeline", [])
        
        mixer_idx = next((i for i, s in enumerate(pipeline) if s.get("type") == "Mixer"), -1)
        mixer_name = "Mixer" if mixer_idx == -1 else pipeline[mixer_idx].get("name", "Mixer")

        # Always read actual hardware channel count from devices section
        hw_in = self.config_raw.get("devices", {}).get("capture", {}).get("channels", 2)
        hw_out = self.config_raw.get("devices", {}).get("playback", {}).get("channels", 2)
        in_chs = hw_in
        out_chs = hw_out

        # Remove any stale mixers that don't match the current active mixer name
        current_mixers = self.config_raw.get("mixers", {})
        stale = [k for k in list(current_mixers.keys()) if k != mixer_name]
        for k in stale:
            del current_mixers[k]
            changed = True
        self.config_raw["mixers"] = current_mixers

        if mixer_name not in self.config_raw["mixers"]:
            self.config_raw["mixers"][mixer_name] = {
                "channels": {"in": in_chs, "out": out_chs},
                "description": None,
                "labels": None,
                "mapping": []
            }
            changed = True
        else:
            # Update channel counts if hardware config changed
            existing = self.config_raw["mixers"][mixer_name]
            if existing.get("channels", {}).get("in") != in_chs or existing.get("channels", {}).get("out") != out_chs:
                existing["channels"] = {"in": in_chs, "out": out_chs}
                changed = True
            
        if mixer_idx == -1:
            pipeline.insert(0, {"type": "Mixer", "name": mixer_name, "description": None})
            changed = True

        if changed:
            self.aplicar_y_guardar(reload=True)

    def reset_from_login(self):
        ip = self.ip_i.text().strip()
        port_str = self.port_i.text().strip()
        try: port = int(port_str)
        except ValueError: self.log_v.append("❌ Error: El puerto debe ser un número."); return

        dark_dlg_style = "QDialog { background-color: #1e1e1e; } QLabel { color: white; font-weight: bold; font-size: 13px; } QLineEdit { background-color: #000; color: #00ffff; border: 1px solid #555; padding: 5px; font-size: 14px; } QPushButton { background-color: #007bff; color: white; font-weight: bold; padding: 6px 15px; border-radius: 4px; min-width: 80px; } QPushButton:hover { background-color: #0056b3; }"
        dark_msg_style = "QMessageBox { background-color: #1e1e1e; color: white; } QLabel { color: white; font-size: 13px; } QPushButton { background: #333; color: white; border: 1px solid #555; padding: 6px 16px; border-radius: 4px; } QPushButton:hover { background: #007bff; }"

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("RESET")
        msg_box.setText("¿Está seguro? Esto enviará la configuración por defecto a CamillaDSP." if self.current_lang == "es" else "Are you sure? This will send the default config to CamillaDSP.")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet(dark_msg_style)
        if msg_box.exec() != QMessageBox.StandardButton.Yes:
            return

        dlg_in = QInputDialog(self)
        dlg_in.setWindowTitle("RESET - Entradas" if self.current_lang == "es" else "RESET - Inputs")
        dlg_in.setLabelText("Cantidad de canales de ENTRADA del hardware:" if self.current_lang == "es" else "Number of hardware INPUT channels:")
        dlg_in.setIntValue(2); dlg_in.setIntMinimum(1); dlg_in.setIntMaximum(64)
        dlg_in.setStyleSheet(dark_dlg_style)
        if not dlg_in.exec(): return
        in_ch = dlg_in.intValue()

        dlg_out = QInputDialog(self)
        dlg_out.setWindowTitle("RESET - Salidas" if self.current_lang == "es" else "RESET - Outputs")
        dlg_out.setLabelText("Cantidad de canales de SALIDA del hardware:" if self.current_lang == "es" else "Number of hardware OUTPUT channels:")
        dlg_out.setIntValue(2); dlg_out.setIntMinimum(1); dlg_out.setIntMaximum(64)
        dlg_out.setStyleSheet(dark_dlg_style)
        if not dlg_out.exec(): return
        out_ch = dlg_out.intValue()

        default_config = {
            "description": "default",
            "devices": {
                "adjust_period": None,
                "capture": {
                    "channels": in_ch, "device": "null", "format": None, "labels": None,
                    "link_mute_control": None, "link_volume_control": None,
                    "stop_on_inactive": None, "type": "Alsa"
                },
                "capture_samplerate": 48000, "chunksize": 1024, "enable_rate_adjust": None,
                "multithreaded": None,
                "playback": {
                    "channels": out_ch, "device": "null", "format": None, "type": "Alsa"
                },
                "queuelimit": None, "rate_measure_interval": None, "resampler": None,
                "samplerate": 48000, "silence_threshold": None, "silence_timeout": None,
                "stop_on_rate_change": None, "target_level": None, "volume_limit": None,
                "volume_ramp_time": None, "worker_threads": None
            },
            "filters": {},
            "mixers": {
                "Mixer": {
                    "channels": {"in": in_ch, "out": out_ch},
                    "description": None, "labels": None, "mapping": []
                }
            },
            "pipeline": [],
            "processors": {},
            "title": "default"
        }

        try:
            cdsp = CamillaDSP(ip, port)
            cdsp.connect()
            cdsp.query("SetConfigJson", json.dumps(default_config))
            self.log_v.append(f"✅ RESET: Config por defecto enviada ({in_ch} IN / {out_ch} OUT).")
            mb = QMessageBox(self); mb.setWindowTitle("RESET"); mb.setText(f"✅ Config enviada: {in_ch} entradas, {out_ch} salidas." if self.current_lang == "es" else f"✅ Config sent: {in_ch} inputs, {out_ch} outputs.")
            mb.setStyleSheet(dark_msg_style); mb.exec()
        except Exception as e:
            self.log_v.append(f"❌ Error al enviar RESET: {e}")
            mb = QMessageBox(self); mb.setWindowTitle("Error"); mb.setText(f"❌ Error: {e}")
            mb.setStyleSheet(dark_msg_style); mb.exec()

    def scan_and_start(self):
        ip, port_str = self.ip_i.text().strip(), self.port_i.text().strip()
        try: port = int(port_str)
        except ValueError: self.log_v.append("❌ Error: El puerto debe ser un número."); return

        try:
            with open("app_settings.json", "w") as f: json.dump({"ip": ip, "port": port}, f)
        except: pass

        self.cdsp = CamillaDSP(ip, port)
        try:
            self.cdsp.connect()
            c = self.ejecutar_comando("GetConfigJson")
            if not c:
                self.log_v.append("❌ Error CRÍTICO: CamillaDSP conectó pero no devolvió configuración.")
                return
            self.config_raw = json.loads(c) if isinstance(c, str) else c
            self.log_v.append(f"✅ Conectado a {ip}:{port}.")
            
            self.parse_and_build_ui()
            
        except Exception as e: 
            self.log_v.append(f"❌ Error al conectar con {ip}:{port} -> {e}")
            return

    def toggle_all_in(self, checked):
        self.btn_all_in.blockSignals(True)
        if checked:
            for i, btn in self.ch_in_buttons.items():
                btn.blockSignals(True); btn.setChecked(True); btn.blockSignals(False); self.visible_in_channels.add(i)
        else:
            for i, btn in self.ch_in_buttons.items():
                btn.blockSignals(True); btn.setChecked(False); btn.blockSignals(False)
            self.visible_in_channels.clear()
        self.btn_all_in.blockSignals(False)
        if hasattr(self, 'graph'): self.graph.update()
        if hasattr(self, 'cross_graph'): self.cross_graph.update()

    def toggle_in_ch(self, ch, checked):
        if checked: self.visible_in_channels.add(ch)
        else: self.visible_in_channels.discard(ch)
        self.btn_all_in.blockSignals(True)
        self.btn_all_in.setChecked(len(self.visible_in_channels) == len(self.ch_in_buttons))
        self.btn_all_in.blockSignals(False)
        if hasattr(self, 'graph'): self.graph.update()
        if hasattr(self, 'cross_graph'): self.cross_graph.update()

    def toggle_all_out(self, checked):
        self.btn_all_out.blockSignals(True)
        if checked:
            for i, btn in self.ch_out_buttons.items():
                btn.blockSignals(True); btn.setChecked(True); btn.blockSignals(False); self.visible_out_channels.add(i)
        else:
            for i, btn in self.ch_out_buttons.items():
                btn.blockSignals(True); btn.setChecked(False); btn.blockSignals(False)
            self.visible_out_channels.clear()
        self.btn_all_out.blockSignals(False)
        if hasattr(self, 'graph'): self.graph.update()
        if hasattr(self, 'cross_graph'): self.cross_graph.update()

    def toggle_out_ch(self, ch, checked):
        if checked: self.visible_out_channels.add(ch)
        else: self.visible_out_channels.discard(ch)
        self.btn_all_out.blockSignals(True)
        self.btn_all_out.setChecked(len(self.visible_out_channels) == len(self.ch_out_buttons))
        self.btn_all_out.blockSignals(False)
        if hasattr(self, 'graph'): self.graph.update()
        if hasattr(self, 'cross_graph'): self.cross_graph.update()

    def on_tab_changed(self, index):
        try:
            if getattr(self, 'channel_selection_panel', None) is None: return
            if index == 0:
                self.channel_selection_panel.hide()
            elif index == 1:
                self.lay_eq.insertWidget(0, self.channel_selection_panel)
                self.channel_selection_panel.show()
                if hasattr(self, 'in_scroll_area'): self.in_scroll_area.show()
            elif index == 2:
                self.lay_cross.insertWidget(0, self.channel_selection_panel)
                self.channel_selection_panel.show()
                if hasattr(self, 'in_scroll_area'): self.in_scroll_area.hide()
            elif index == 3:
                self.channel_selection_panel.hide()
        except RuntimeError:
            pass

    def filtrar_vumetros(self, button=None):
        idx = self.vu_view_group.checkedId()
        for w in self.vu_in_widgets:
            w.setVisible(idx in [0, 1])
        if hasattr(self, 'vu_separator') and self.vu_separator:
            self.vu_separator.setVisible(idx == 0)
        for w in self.vu_out_widgets:
            w.setVisible(idx in [0, 2])
            
    def toggle_channel_bypass(self, ch_index, is_out):
        pipeline = self.config_raw.get("pipeline", [])
        mixer_idx = next((i for i, s in enumerate(pipeline) if s.get("type") == "Mixer"), -1)
        
        changed = False
        patch_pipe = list(pipeline)
        
        is_bypassed = False
        for idx, step in enumerate(patch_pipe):
            if step.get("type") == "Filter":
                domain = "in" if mixer_idx != -1 and idx < mixer_idx else "out"
                if (domain == "out") == is_out:
                    chs = self._get_chs_from_step(step)
                    if ch_index in chs:
                        is_eq = False
                        desc = step.get("description") or ""
                        if desc.startswith("EQ-"): is_eq = True
                        elif step.get("names") and len(step["names"]) > 0 and step["names"][0].startswith("EQ_"): is_eq = True
                        
                        if is_eq:
                            is_bypassed = step.get("bypassed", False)
                            break
        
        new_state = not is_bypassed
        
        for idx, step in enumerate(patch_pipe):
            if step.get("type") == "Filter":
                domain = "in" if mixer_idx != -1 and idx < mixer_idx else "out"
                if (domain == "out") == is_out:
                    chs = self._get_chs_from_step(step)
                    if ch_index in chs:
                        is_eq = False
                        desc = step.get("description") or ""
                        if desc.startswith("EQ-"): is_eq = True
                        elif step.get("names") and len(step["names"]) > 0 and step["names"][0].startswith("EQ_"): is_eq = True
                        
                        if is_eq:
                            step["bypassed"] = new_state
                            changed = True
                            
        if changed:
            self.aplicar_y_guardar(patch_dict={"pipeline": patch_pipe})
            msg = f"✅ Bypass {'ACTIVADO' if new_state else 'DESACTIVADO'} en canal {'OUT' if is_out else 'IN'} {ch_index}."
            self.log_v.append(msg)
            self.actualizar_iconos_bypass()
            if hasattr(self, 'graph'): self.graph.update()

    def actualizar_iconos_bypass(self):
        pipeline = self.config_raw.get("pipeline", [])
        mixer_idx = next((i for i, s in enumerate(pipeline) if s.get("type") == "Mixer"), -1)
        
        in_bypassed = {i: False for i in range(len(self.in_labels))}
        out_bypassed = {i: False for i in range(len(self.out_labels))}
        
        for idx, step in enumerate(pipeline):
            if step.get("type") == "Filter":
                domain = "in" if mixer_idx != -1 and idx < mixer_idx else "out"
                is_eq = False
                desc = step.get("description") or ""
                if desc.startswith("EQ-"): is_eq = True
                elif step.get("names") and len(step["names"]) > 0 and step["names"][0].startswith("EQ_"): is_eq = True
                
                if is_eq and step.get("bypassed", False):
                    for c in self._get_chs_from_step(step):
                        if domain == "in" and c in in_bypassed: in_bypassed[c] = True
                        elif domain == "out" and c in out_bypassed: out_bypassed[c] = True
                        
        for i, btn in self.ch_in_buttons.items():
            name = self.in_labels[i]
            icon = "🔴" if in_bypassed.get(i, False) else "🔊"
            btn.setText(f"{icon} {name}")
            
        for i, btn in self.ch_out_buttons.items():
            name = self.out_labels[i]
            icon = "🔴" if out_bypassed.get(i, False) else "🔊"
            btn.setText(f"{icon} {name}")

    def toggle_mute_all(self):
        mixer_name = next((s.get("name") for s in self.config_raw.get("pipeline", []) if s.get("type") == "Mixer"), None)
        if not (mixer_name and "mixers" in self.config_raw and mixer_name in self.config_raw["mixers"]):
            self.log_v.append("❌ Error: No se encontró la configuración del Mixer para silenciar todo.")
            return

        m_conf = self.config_raw["mixers"][mixer_name]
        mappings = m_conf.setdefault("mapping", [])
        
        self.all_outputs_muted = not self.all_outputs_muted
        
        for ch_idx in range(len(self.out_labels)):
            mapping = next((m for m in mappings if m.get("dest") == ch_idx), None)
            if not mapping:
                mapping = {"dest": ch_idx, "mute": False, "sources": []}
                mappings.append(mapping)
                
            mapping["mute"] = self.all_outputs_muted
            
            if ch_idx < len(self.v_out):
                self.v_out[ch_idx].is_muted = self.all_outputs_muted
                self.v_out[ch_idx].update()
                
        self.aplicar_y_guardar(patch_dict={"mixers": {mixer_name: m_conf}})
        self.check_mute_all_state()

    def check_mute_all_state(self):
        if not hasattr(self, 'v_out') or not self.v_out: return
        
        all_muted = all(v.is_muted for v in self.v_out)
        self.all_outputs_muted = all_muted
        
        if hasattr(self, 'btn_mute_all'):
            if self.all_outputs_muted:
                self.btn_mute_all.setStyleSheet("background: #d9534f; color: white; font-weight: bold; font-size: 11px; border-radius: 4px; padding: 0 10px;")
            else:
                self.btn_mute_all.setStyleSheet("background: #666; color: white; font-weight: bold; font-size: 11px; border-radius: 4px; padding: 0 10px;")

    def toggle_mute(self, ch_index, is_muted, vu_ref):
        mixer_name = next((s.get("name") for s in self.config_raw.get("pipeline", []) if s.get("type") == "Mixer"), None)
        if mixer_name and "mixers" in self.config_raw and mixer_name in self.config_raw["mixers"]:
            m_conf = self.config_raw["mixers"][mixer_name]
            for mapping in m_conf.get("mapping", []):
                if mapping.get("dest") == ch_index: mapping["mute"] = is_muted
            self.aplicar_y_guardar(patch_dict={"mixers": {mixer_name: m_conf}})
            self.check_mute_all_state()

    def toggle_polarity(self, ch_index, is_inverted):
        mixer_name = next((s.get("name") for s in self.config_raw.get("pipeline", []) if s.get("type") == "Mixer"), None)
        if mixer_name and "mixers" in self.config_raw and mixer_name in self.config_raw["mixers"]:
            m_conf = self.config_raw["mixers"][mixer_name]
            for mapping in m_conf.get("mapping", []):
                if mapping.get("dest") == ch_index:
                    for src in mapping.get("sources", []): src["inverted"] = is_inverted
            self.aplicar_y_guardar(patch_dict={"mixers": {mixer_name: m_conf}})

    def init_studio(self):
        p = QWidget()
        main_lay = QVBoxLayout(p); main_lay.setContentsMargins(0, 0, 0, 0); main_lay.setSpacing(0)

        # --- PANEL DE SELECCION DE CANALES (Estilo Ultra Compacto) ---
        self.channel_selection_panel = QWidget()
        self.channel_selection_panel.setStyleSheet("background-color: #050505;")
        csp_lay = QVBoxLayout(self.channel_selection_panel)
        csp_lay.setContentsMargins(0, 0, 0, 0)
        csp_lay.setSpacing(1) 

        # --- Solapas Entradas ---
        self.in_scroll_area = QScrollArea()
        QScroller.grabGesture(self.in_scroll_area.viewport(), QScroller.LeftMouseButtonGesture)
        self.in_scroll_area.setWidgetResizable(True)
        self.in_scroll_area.setFrameShape(QFrame.NoFrame)
        self.in_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.in_scroll_area.setFixedHeight(24) 
        self.in_scroll_area.setStyleSheet("QScrollArea { background: transparent; } QScrollBar:horizontal { height: 6px; background: #111; } QScrollBar::handle:horizontal { background: #444; border-radius: 3px; }")

        in_widget = QWidget()
        in_widget.setStyleSheet("background: transparent;")
        h_in = QHBoxLayout(in_widget)
        h_in.setContentsMargins(0, 0, 0, 0) 
        h_in.setSpacing(2) 
        
        self.btn_all_in = QPushButton("ALL IN")
        self.btn_all_in.setCheckable(True)
        self.btn_all_in.setChecked(True)
        self.btn_all_in.setFixedHeight(20) 
        self.btn_all_in.setStyleSheet("QPushButton { background: #2a2a2a; color: #999; border: 1px solid #444; border-radius: 2px; font-weight: bold; font-size: 10px; padding: 0 10px;} QPushButton:hover { background: #333; color: white; } QPushButton:checked { background: #007bff; color: white; border: 1px solid #0ff; }")
        self.btn_all_in.clicked.connect(self.toggle_all_in)
        h_in.addWidget(self.btn_all_in)
        
        for i, name in enumerate(self.in_labels):
            btn = ChannelTabButton(f"🔊 {name}")
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedHeight(20) 
            btn.setToolTip(name)
            btn.setStyleSheet("QPushButton { background: #2a2a2a; color: #999; border: 1px solid #444; border-radius: 2px; padding: 0 6px; font-weight: bold; font-size: 11px; } QPushButton:hover { background: #333; color: white; } QPushButton:checked { background: #00aaaa; color: black; border: 1px solid white; }")
            btn.clicked.connect(lambda checked, ch=i: self.toggle_in_ch(ch, checked))
            btn.rightClicked.connect(lambda ch=i: self.toggle_channel_bypass(ch, False))
            self.ch_in_buttons[i] = btn
            h_in.addWidget(btn)
        h_in.addStretch()
        
        self.in_scroll_area.setWidget(in_widget)
        csp_lay.addWidget(self.in_scroll_area)

        # --- Solapas Salidas ---
        self.out_scroll_area = QScrollArea()
        QScroller.grabGesture(self.out_scroll_area.viewport(), QScroller.LeftMouseButtonGesture)
        self.out_scroll_area.setWidgetResizable(True)
        self.out_scroll_area.setFrameShape(QFrame.NoFrame)
        self.out_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.out_scroll_area.setFixedHeight(24) 
        self.out_scroll_area.setStyleSheet("QScrollArea { background: transparent; } QScrollBar:horizontal { height: 6px; background: #111; } QScrollBar::handle:horizontal { background: #444; border-radius: 3px; }")

        out_widget = QWidget()
        out_widget.setStyleSheet("background: transparent;")
        h_out = QHBoxLayout(out_widget)
        h_out.setContentsMargins(0, 0, 0, 0) 
        h_out.setSpacing(2) 
        
        self.btn_all_out = QPushButton("ALL OUT")
        self.btn_all_out.setCheckable(True)
        self.btn_all_out.setChecked(True)
        self.btn_all_out.setFixedHeight(20) 
        self.btn_all_out.setStyleSheet("QPushButton { background: #2a2a2a; color: #999; border: 1px solid #444; border-radius: 2px; font-weight: bold; font-size: 10px; padding: 0 10px;} QPushButton:hover { background: #333; color: white; } QPushButton:checked { background: #007bff; color: white; border: 1px solid #0ff; }")
        self.btn_all_out.clicked.connect(self.toggle_all_out)
        h_out.addWidget(self.btn_all_out)
        
        for i, name in enumerate(self.out_labels): 
            btn = ChannelTabButton(f"🔊 {name}")
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedHeight(20) 
            btn.setToolTip(name)
            col_hex = GLOBAL_HEX_COLORS[i % len(GLOBAL_HEX_COLORS)]
            btn.setStyleSheet(f"QPushButton {{ background: #2a2a2a; color: #999; border: 1px solid #444; border-radius: 2px; padding: 0 6px; font-weight: bold; font-size: 11px; }} QPushButton:hover {{ background: #333; color: white; }} QPushButton:checked {{ background: {col_hex}; color: black; border: 1px solid white; }}")
            btn.clicked.connect(lambda checked, ch=i: self.toggle_out_ch(ch, checked))
            btn.rightClicked.connect(lambda ch=i: self.toggle_channel_bypass(ch, True))
            self.ch_out_buttons[i] = btn
            h_out.addWidget(btn)
        h_out.addStretch()
        
        self.out_scroll_area.setWidget(out_widget)
        csp_lay.addWidget(self.out_scroll_area)

        # --- PESTAÑAS PRINCIPALES ---
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #333; background: #050505; }
            QTabBar::tab { background: #222; color: #ccc; padding: 10px 20px; border: 1px solid #333; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; font-weight: bold; }
            QTabBar::tab:selected { background: #007bff; color: white; border-top: 2px solid #00ffff; }
        """)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # --- BOTONES DE GESTION (Esquina Superior Derecha de las Pestañas) ---
        self.corner_widget = QWidget()
        cw_lay = QHBoxLayout(self.corner_widget)
        cw_lay.setContentsMargins(0, 0, 0, 0)
        cw_lay.setSpacing(2)
        
        btn_style = "QPushButton { background: #333; color: white; border: 1px solid #555; border-radius: 2px; font-size: 10px; font-weight: bold; padding: 2px 6px; } QPushButton:hover { background: #007bff; }"
        
        self.btn_importar_cfg = QPushButton("Imp Cfg")
        self.btn_importar_cfg.setFixedHeight(22); self.btn_importar_cfg.setStyleSheet(btn_style)
        self.btn_importar_cfg.clicked.connect(self.importar_config)
        
        self.btn_exportar_cfg = QPushButton("Exp Cfg")
        self.btn_exportar_cfg.setFixedHeight(22); self.btn_exportar_cfg.setStyleSheet(btn_style)
        self.btn_exportar_cfg.clicked.connect(self.exportar_config)
        
        self.btn_default_cfg = QPushButton("Reset")
        self.btn_default_cfg.setFixedHeight(22); self.btn_default_cfg.setStyleSheet("QPushButton { background: #400; color: white; border: 1px solid #600; border-radius: 2px; font-size: 10px; font-weight: bold; padding: 2px 6px; } QPushButton:hover { background: #d32f2f; }")
        self.btn_default_cfg.clicked.connect(self.cargar_config_default)
        
        self.btn_importar = QPushButton("Imp EQ")
        self.btn_importar.setFixedHeight(22); self.btn_importar.setStyleSheet(btn_style)
        self.btn_importar.clicked.connect(self.importar_filtros)
        
        self.btn_exportar = QPushButton("Exp EQ")
        self.btn_exportar.setFixedHeight(22); self.btn_exportar.setStyleSheet(btn_style)
        self.btn_exportar.clicked.connect(self.exportar_filtros)
        
        self.btn_web = QPushButton("WEB")
        self.btn_web.setFixedHeight(22); self.btn_web.setStyleSheet("QPushButton { background: #17a2b8; color: white; border: 1px solid #117a8b; border-radius: 2px; font-size: 10px; font-weight: bold; padding: 2px 6px; } QPushButton:hover { background: #138496; }")
        self.btn_web.clicked.connect(lambda: webbrowser.open(f"http://{self.ip_i.text().strip()}:5005"))
        
        self.btn_show_console = QPushButton("Log")
        self.btn_show_console.setFixedHeight(22); self.btn_show_console.setStyleSheet("QPushButton { background: #007bff; color: white; border: 1px solid #0056b3; border-radius: 2px; font-size: 10px; font-weight: bold; padding: 2px 6px; } QPushButton:hover { background: #0056b3; }")
        self.btn_show_console.clicked.connect(self.console_window.show)
        
        cw_lay.addWidget(self.btn_web)
        cw_lay.addWidget(self.btn_importar_cfg)
        cw_lay.addWidget(self.btn_exportar_cfg)
        cw_lay.addWidget(self.btn_importar)
        cw_lay.addWidget(self.btn_exportar)
        cw_lay.addWidget(self.btn_default_cfg)
        self.btn_lang_studio = QPushButton("ES / EN")
        self.btn_lang_studio.setFixedHeight(22)
        self.btn_lang_studio.setStyleSheet("QPushButton { background: #444; color: white; border: 1px solid #666; border-radius: 2px; font-size: 10px; font-weight: bold; padding: 2px 6px; }")
        self.btn_lang_studio.clicked.connect(self.toggle_lang)
        
        self.btn_help2 = QPushButton("Ayuda" if self.current_lang == "es" else "Help")
        self.btn_help2.setFixedHeight(22)
        self.btn_help2.setStyleSheet("QPushButton { background: #28a745; color: white; border: 1px solid #1e7e34; border-radius: 2px; font-size: 10px; font-weight: bold; padding: 2px 6px; }")
        self.btn_help2.clicked.connect(self.show_help)
        
        cw_lay.addWidget(self.btn_show_console)
        cw_lay.addWidget(self.btn_help2)
        cw_lay.addWidget(self.btn_lang_studio)

        self.tabs.setCornerWidget(self.corner_widget, Qt.TopRightCorner)

        # PESTAÑA 1: VUMETROS
        tab_vu = QWidget(); tab_vu.setStyleSheet("background-color: #050505;")
        lay_vu = QVBoxLayout(tab_vu)
        
        # Filtros de Vistas (Vumetros) y MUTE ALL
        h_vu_top = QHBoxLayout()
        self.lbl_view = QLabel("VISTA:" if self.current_lang == "es" else "VIEW:")
        self.lbl_view.setStyleSheet("color: #888; font-weight: bold; font-size: 11px;")
        h_vu_top.addWidget(self.lbl_view)
        
        self.btn_view_all = QPushButton("TODO" if self.current_lang == "es" else "ALL")
        self.btn_view_in = QPushButton("ENTRADAS" if self.current_lang == "es" else "INPUTS")
        self.btn_view_out = QPushButton("SALIDAS" if self.current_lang == "es" else "OUTPUTS")
        
        self.vu_view_group = QButtonGroup(self)
        for i, btn in enumerate([self.btn_view_all, self.btn_view_in, self.btn_view_out]):
            btn.setCheckable(True)
            btn.setFixedSize(100, 25)
            btn.setStyleSheet("QPushButton { background: #222; color: #ccc; border: 1px solid #444; border-radius: 4px; font-weight: bold; } QPushButton:checked { background: #007bff; color: white; border: 1px solid #0ff; }")
            h_vu_top.addWidget(btn)
            self.vu_view_group.addButton(btn, i)
            
        self.btn_view_all.setChecked(True)
        self.vu_view_group.buttonClicked.connect(self.filtrar_vumetros)
        
        # Boton MUTE ALL
        self.btn_mute_all = QPushButton("MUTE ALL")
        self.btn_mute_all.setFixedSize(80, 25)
        self.btn_mute_all.setStyleSheet("background: #666; color: white; font-weight: bold; font-size: 11px; border-radius: 4px; padding: 0 10px;")
        self.btn_mute_all.clicked.connect(self.toggle_mute_all)
        h_vu_top.addWidget(self.btn_mute_all)
        
        h_vu_top.addStretch()
        lay_vu.addLayout(h_vu_top)

        scroll_vu = QScrollArea()
        QScroller.grabGesture(scroll_vu.viewport(), QScroller.LeftMouseButtonGesture)
        scroll_vu.setWidgetResizable(True)
        scroll_vu.setStyleSheet("QScrollArea { border: none; background-color: #050505; } QScrollBar:horizontal { background: #111; height: 14px; } QScrollBar::handle:horizontal { background: #444; border-radius: 7px; min-width: 20px; }")
        
        vu_container = QWidget(); vu_container.setStyleSheet("background-color: #050505;")
        vu_layout = QHBoxLayout(vu_container); vu_layout.setAlignment(Qt.AlignLeft) 
        
        init_master_vol = 0.0
        try:
            if hasattr(self, 'cdsp') and hasattr(self.cdsp, 'volume'):
                init_master_vol = self.cdsp.volume.main()
        except: pass
        
        self.master_fader = ProFader("MASTER", -1, init_master_vol, mode="master")
        self.master_fader.app_ref = self
        vu_layout.addWidget(self.master_fader)
        
        sep_master = QFrame(); sep_master.setFrameShape(QFrame.VLine); sep_master.setStyleSheet("color: #444;"); vu_layout.addWidget(sep_master)

        
        for i, n in enumerate(self.in_labels): 
            vu = ProVUMeter(n)
            vu.is_output = False
            vu.ch_index = i
            vu.app_ref = self
            vu_layout.addWidget(vu)
            self.v_in.append(vu)
            self.vu_in_widgets.append(vu)
            
        self.vu_separator = None
        if self.in_labels and self.out_labels:
            self.vu_separator = QFrame(); self.vu_separator.setFrameShape(QFrame.VLine); self.vu_separator.setStyleSheet("color: #444;"); vu_layout.addWidget(self.vu_separator)
            
        mixer_name = next((s.get("name") for s in self.config_raw.get("pipeline", []) if s.get("type") == "Mixer"), None)

        for i, n in enumerate(self.out_labels): 
            strip = QWidget(); slay = QHBoxLayout(strip); slay.setContentsMargins(0,0,0,0)
            
            vu = ProVUMeter(n)
            vu.is_output = True; vu.ch_index = i; vu.app_ref = self
            
            comp_threshold = None
            comp_ratio = 1.0
            comp_makeup = 0.0
            for pid, pdata in self.config_raw.get("processors", {}).items():
                if pdata.get("type") == "Compressor" and pdata.get("parameters", {}).get("process_channels", [-1])[0] == i:
                    t_val = pdata.get("parameters", {}).get("threshold")
                    if t_val != 0.0:
                        comp_threshold = t_val
                        comp_ratio = pdata.get("parameters", {}).get("factor", 1.0)
                        comp_makeup = pdata.get("parameters", {}).get("makeup_gain", 0.0)
                    break
                    
            vu.comp_threshold = comp_threshold
            vu.comp_ratio = comp_ratio
            vu.comp_makeup = comp_makeup
            self.v_out.append(vu)
            
            init_db, init_inv, init_mute = 0.0, False, False
            if mixer_name and "mixers" in self.config_raw and mixer_name in self.config_raw["mixers"]:
                m_conf = self.config_raw["mixers"][mixer_name]
                for mapping in m_conf.get("mapping", []):
                    if mapping.get("dest") == i:
                        init_mute = mapping.get("mute", False)
                        srcs = mapping.get("sources", [])
                        if srcs: 
                            init_db = srcs[0].get("gain", 0.0)
                            init_inv = srcs[0].get("inverted", False)
                        break

            init_delay = 0.0
            delay_fname = f"Delay_{self.clean_name(n)}"
            mixer_idx = next((ix for ix, st in enumerate(self.config_raw.get("pipeline", [])) if st.get("type") == "Mixer"), -1)
            start_idx = mixer_idx + 1 if mixer_idx != -1 else 0
            
            for step in self.config_raw.get("pipeline", [])[start_idx:]:
                if step.get("type") == "Filter" and i in self._get_chs_from_step(step):
                    for fn in step.get("names", []):
                        f_cfg = self.config_raw.get("filters", {}).get(fn, {})
                        if f_cfg.get("type") == "Delay" and fn == delay_fname:
                            init_delay = float(f_cfg.get("parameters", {}).get("delay", 0.0))
                            break
                if init_delay > 0: break

            vu.is_muted = init_mute
            fader_col = QWidget(); flay = QVBoxLayout(fader_col); flay.setContentsMargins(0,0,0,0); flay.setSpacing(2)
            fader = ProFader(n, i, init_db); fader.app_ref = self
            flay.addWidget(fader, 1)
            
            btn_pol = QPushButton("+/-")
            btn_pol.setCheckable(True); btn_pol.setChecked(init_inv); btn_pol.setFixedSize(40, 22)
            btn_pol.setStyleSheet("QPushButton { background: #333; color: white; border-radius: 3px; font-weight: bold; } QPushButton:checked { background: #d9534f; color: white; }")
            btn_pol.clicked.connect(lambda checked, ch=i: self.toggle_polarity(ch, checked))
            flay.addWidget(btn_pol, 0, Qt.AlignHCenter)

            lbl_del = QLabel("DLY(ms)"); lbl_del.setFont(QFont("Arial", 7)); lbl_del.setStyleSheet("color: #888;")
            flay.addWidget(lbl_del, 0, Qt.AlignHCenter)

            inp_del = DelayLineEdit(f"{init_delay:.1f}", i, delay_fname, self)
            inp_del.setFixedSize(40, 20); inp_del.setAlignment(Qt.AlignCenter)
            inp_del.setStyleSheet("background: #111; color: #0ff; border: 1px solid #444; font-size: 10px; border-radius: 2px;")
            inp_del.editingFinished.connect(lambda ch=i, nm=delay_fname, inp=inp_del: self.cambiar_delay(ch, nm, inp.text(), inp))
            flay.addWidget(inp_del, 0, Qt.AlignHCenter)

            slay.addWidget(vu); slay.addWidget(fader_col); vu_layout.addWidget(strip)
            self.vu_out_widgets.append(strip)
            
        scroll_vu.setWidget(vu_container)
        lay_vu.addWidget(scroll_vu, 1) 
        
        self.comp_table = QTableWidget(0, 9); 
        self.comp_table.setHorizontalHeaderLabels(["Comp ID", "Attack (s)", "Release (s)", "threshold (db)", "Ratio", "Output Gain (db)", "ClipLim", "Auto", "Del"])
        self.comp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.comp_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.comp_table.verticalHeader().setDefaultSectionSize(35)
        lay_vu.addWidget(self.comp_table, 0) 

        t_style = """
            QTableWidget { background: #111; color: white; border: none; gridline-color: #333; selection-background-color: #0055ff; selection-color: white; font-family: Consolas; font-size: 13px; }
            QHeaderView::section { background: #1a1a1a; color: #00ffff; font-weight: bold; border: 1px solid #333; height: 35px; }
            QComboBox { background: #333; color: white; border: 1px solid #555; border-radius: 3px; padding: 2px; }
            QComboBox QAbstractItemView { background-color: #222; color: white; selection-background-color: #007bff; }
            QTableWidget QLineEdit { color: #0ff; background-color: #000; }
            QPushButton { background: #400; color: #f55; border: 1px solid #600; border-radius: 3px; font-weight: bold; }
        """
        self.comp_table.setStyleSheet(t_style)
        self.comp_table.itemChanged.connect(self.modificar_compresor_desde_tabla)

        self.combo_ch_list = [f"in {i}: {lbl}" for i, lbl in enumerate(self.in_labels)] + [f"out {i}: {lbl}" for i, lbl in enumerate(self.out_labels)]
        self.combo_out_ch_list = [f"out {i}: {lbl}" for i, lbl in enumerate(self.out_labels)]

        # PESTAÑA 2: EQ
        tab_eq = QWidget(); tab_eq.setStyleSheet("background-color: #050505;")
        self.lay_eq = QVBoxLayout(tab_eq)
        self.lay_eq.setContentsMargins(5, 5, 5, 5)
        self.lay_eq.setSpacing(5)
        
        self.graph = EQGraph(self); self.graph.sample_rate = self.sample_rate; self.graph.set_filters(self.filtros_biquad)
        self.lay_eq.addWidget(self.graph, 1) 
        
        self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels(["Filter ID", "Type", "Freq", "Gain", "Q", "Channel", "Del"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.setStyleSheet(t_style)
        self.table.itemSelectionChanged.connect(self.on_eq_table_selection)
        self.table.itemChanged.connect(self.modificar_filtro_desde_tabla)
        self.lay_eq.addWidget(self.table, 1) 
        
        # PESTAÑA 3: CROSSOVERS
        tab_cross = QWidget(); tab_cross.setStyleSheet("background-color: #050505;")
        self.lay_cross = QVBoxLayout(tab_cross)
        self.lay_cross.setContentsMargins(5, 5, 5, 5)
        self.lay_cross.setSpacing(5)
        
        self.cross_graph = CrossoverGraph(self); self.cross_graph.set_filters(self.filtros_crossover)
        self.lay_cross.addWidget(self.cross_graph, 1)
        self.cross_table = QTableWidget(0, 6)
        self.cross_table.setHorizontalHeaderLabels(["Filter ID", "Type", "Freq (Hz)", "Order", "Channel", "Del"])
        self.cross_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.cross_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cross_table.verticalHeader().setDefaultSectionSize(35)
        self.cross_table.setStyleSheet(t_style)
        self.cross_table.itemSelectionChanged.connect(self.on_cross_table_selection)
        self.cross_table.itemChanged.connect(self.modificar_crossover_desde_tabla)
        self.lay_cross.addWidget(self.cross_table, 0)

        # PESTAÑA 4: MATRIZ MIXER
        tab_mixer = QWidget(); tab_mixer.setStyleSheet("background-color: #050505;")
        lay_mixer = QVBoxLayout(tab_mixer)
        
        scroll_mixer = QScrollArea()
        scroll_mixer.setWidgetResizable(True)
        scroll_mixer.setStyleSheet("QScrollArea { border: none; background-color: #050505; } QScrollBar:horizontal { background: #111; height: 14px; } QScrollBar::handle:horizontal { background: #444; border-radius: 7px; min-width: 20px; } QScrollBar:vertical { background: #111; width: 14px; } QScrollBar::handle:vertical { background: #444; border-radius: 7px; min-height: 20px; }")
        
        self.mixer_graph = MixerMatrixWidget(self)
        scroll_mixer.setWidget(self.mixer_graph)
        lay_mixer.addWidget(scroll_mixer)

        self.tabs.addTab(tab_vu, "")
        self.tabs.addTab(tab_eq, "")
        self.tabs.addTab(tab_cross, "")
        self.tabs.addTab(tab_mixer, "")
        
        main_lay.addWidget(self.tabs)
        self.actualizar_tabla_ui()
        self.actualizar_tabla_comp_ui()
        self.actualizar_tabla_crossover_ui()
        self.actualizar_iconos_bypass()
        self.check_mute_all_state()
        
        # Aplicamos la traducción inicial de las pestañas
        if getattr(self, 'tabs', None) is not None:
            self.tabs.setTabText(0, "VÚMETROS Y DINÁMICA" if self.current_lang == "es" else "VUMETERS & DYNAMICS")
            self.tabs.setTabText(1, "FILTROS Y EQ" if self.current_lang == "es" else "EQ & FILTERS")
            self.tabs.setTabText(2, "CROSSOVERS")
            self.tabs.setTabText(3, "MIXER")
            
        self.stack.addWidget(p)
        self.on_tab_changed(0) 

    def cargar_config_default(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Atención" if self.current_lang == "es" else "Warning")
        msg_box.setText("¿Está seguro? Esto borrará toda la configuración actual de CamillaDSP y cargará los valores por defecto." if self.current_lang == "es" else "Are you sure? This will wipe CamillaDSP and load defaults.")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        msg_box.setStyleSheet("QMessageBox { background-color: #1e1e1e; color: white; } QLabel { color: white; font-size: 13px; } QPushButton { background: #333; color: white; border: 1px solid #555; padding: 6px 16px; border-radius: 4px; } QPushButton:hover { background: #007bff; }")
        respuesta = msg_box.exec()
        
        if respuesta == QMessageBox.StandardButton.Yes:
            default_config = {
              "description": "default",
              "devices": {
                "adjust_period": None,
                "capture": {
                  "channels": 6,
                  "device": "null",
                  "format": None,
                  "labels": None,
                  "link_mute_control": None,
                  "link_volume_control": None,
                  "stop_on_inactive": None,
                  "type": "Alsa"
                },
                "capture_samplerate": 48000,
                "chunksize": 512,
                "enable_rate_adjust": None,
                "multithreaded": None,
                "playback": {
                  "channels": 6,
                  "device": "null",
                  "format": None,
                  "type": "Alsa"
                },
                "queuelimit": None,
                "rate_measure_interval": None,
                "resampler": None,
                "samplerate": 48000,
                "silence_threshold": None,
                "silence_timeout": None,
                "stop_on_rate_change": None,
                "target_level": None,
                "volume_limit": None,
                "volume_ramp_time": None,
                "worker_threads": None
              },
              "filters": {},
              "mixers": {
                "Unnamed Mixer 1": {
                  "channels": {"in": 2, "out": 2},
                  "description": None,
                  "labels": None,
                  "mapping": []
                }
              },
              "pipeline": [],
              "processors": {},
              "title": "default"
            }
            try:
                self.config_raw = default_config
                self.aplicar_y_guardar(reload=True)
                import subprocess
                subprocess.Popen([sys.executable] + sys.argv)
                QApplication.instance().quit()
                return
                # msg = "✅ Configuración por defecto cargada con éxito." if self.current_lang == "es" else "✅ Default config loaded."
                self.log_v.append(msg)
            except Exception as e:
                self.log_v.append(f"❌ Error al cargar config por defecto: {e}")

    def importar_config(self):
        title = "Importar Configuración Completa" if self.current_lang == "es" else "Import Configuration"
        path, _ = QFileDialog.getOpenFileName(self, title, "", "YAML/JSON Files (*.yml *.yaml *.json);;All Files (*)")
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if path.endswith('.json'):
                new_conf = json.loads(content)
            else:
                try:
                    if HAS_YAML:
                        new_conf = yaml.safe_load(content)
                    else:
                        self.log_v.append("❌ Falta la librería 'pyyaml'. Ejecute: pip install pyyaml en su terminal para leer archivos .yml")
                        return
                except Exception as ye:
                    self.log_v.append(f"❌ Error leyendo YAML: {ye}")
                    return
                
            self.config_raw = new_conf
            self.aplicar_y_guardar(reload=True)
            self.parse_and_build_ui()
            msg = f"✅ Configuración importada con éxito desde {path}" if self.current_lang == "es" else f"✅ Config imported from {path}"
            self.log_v.append(msg)
        except Exception as e:
            self.log_v.append(f"❌ Error al importar config: {e}")

    def exportar_config(self):
        title = "Exportar Configuración Completa" if self.current_lang == "es" else "Export Configuration"
        path, _ = QFileDialog.getSaveFileName(self, title, "camilladsp_config.yml", "YAML Files (*.yml *.yaml);;JSON Files (*.json)")
        if not path: return
        try:
            if path.endswith('.json'):
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.config_raw, f, indent=4)
            else:
                if HAS_YAML:
                    with open(path, 'w', encoding='utf-8') as f:
                        yaml.dump(self.config_raw, f, default_flow_style=False, sort_keys=False)
                else:
                    self.log_v.append("❌ Falta la librería 'pyyaml'. Guardando como JSON de respaldo...")
                    with open(path + '.json', 'w', encoding='utf-8') as f:
                        json.dump(self.config_raw, f, indent=4)
                        
            msg = f"✅ Configuración exportada a {path}" if self.current_lang == "es" else f"✅ Config exported to {path}"            
            self.log_v.append(msg)
        except Exception as e:
            self.log_v.append(f"❌ Error al exportar config: {e}")

    def importar_filtros(self):
        ins = list(self.visible_in_channels)
        outs = list(self.visible_out_channels)
        if not ins and not outs:
            self.graph.show_warning(LANG[self.current_lang]["warn_msg"])
            return
            
        title = "Importar Filtros" if self.current_lang == "es" else "Import Filters"
        path, _ = QFileDialog.getOpenFileName(self, title, "", "Filtros (*.txt *.yml *.yaml);;All Files (*)")
        if not path: return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                f.seek(0)
                lines = f.readlines()
                
            count = 0
            patch_filters = {}
            
            # --- DETECCIÓN FORMATO CAMILLADSP (YAML/TXT) ---
            if "filters:" in content and "parameters:" in content:
                import re
                # Extraemos la sección 'filters'
                f_sec = re.search(r'filters:(.*?)(?:pipeline:|\Z)', content, re.DOTALL)
                if f_sec:
                    filters_text = f_sec.group(1)
                    # Buscamos bloques que empiecen con indentación de 2 espacios seguidos de un nombre y luego 'parameters'
                    item_blocks = re.findall(r'^\s{2}(\w+):.*?parameters:(.*?)(?=\n\s{2}\w+:|\Z)', filters_text, re.DOTALL | re.MULTILINE)
                    for name, block in item_blocks:
                        f_m = re.search(r'freq:\s*([-\d.]+)', block)
                        g_m = re.search(r'gain:\s*([-\d.]+)', block)
                        q_m = re.search(r'q:\s*([-\d.]+)', block)
                        t_m = re.search(r'type:\s*(\w+)', block)
                        
                        if f_m and g_m and q_m:
                            freq = float(f_m.group(1))
                            gain = float(g_m.group(1))
                            q = float(q_m.group(1))
                            tipo = t_m.group(1) if t_m else "Peaking"
                            
                            if tipo.lower() == "peak": tipo = "Peaking"
                            
                            for ch in ins:
                                fid, p = self._crear_filtro_eq_dict(freq, gain, q, tipo, "in", ch)
                                patch_filters[fid] = p
                            for ch in outs:
                                fid, p = self._crear_filtro_eq_dict(freq, gain, q, tipo, "out", ch)
                                patch_filters[fid] = p
                            count += 1
            
            if count == 0:
                # --- FORMATO TRADICIONAL (REW / TXT / TAB) ---
                for line in lines: 
                    line = line.strip()
                    if not line: continue
                    if line.lower().startswith("freq"): continue
                    
                    freq, gain, q, tipo = None, None, None, None
                    
                    if line.lower().startswith("filter"):
                        if "ON" not in line: continue
                        parts = line.split()
                        try:
                            if "None" in parts: continue
                            freq = float(parts[parts.index("Fc") + 1])
                            gain = float(parts[parts.index("Gain") + 1])
                            
                            q = 1.0
                            if "Q" in parts:
                                q = float(parts[parts.index("Q") + 1])
                                
                            t_raw = parts[3].upper()
                            if t_raw in ["PK", "PEQ"]: tipo = "Peaking"
                            elif "LS" in t_raw or "LSC" in t_raw: tipo = "Lowshelf"
                            elif "HS" in t_raw or "HSC" in t_raw: tipo = "Highshelf"
                            elif "LP" in t_raw or "LPQ" in t_raw: tipo = "Lowpass"
                            elif "HP" in t_raw or "HPQ" in t_raw: tipo = "Highpass"
                            else: tipo = "Peaking"
                        except:
                            continue
                    else:
                        parts = line.split('\t')
                        if len(parts) < 4:
                            parts = line.split()
                        if len(parts) >= 4:
                            try:
                                freq = float(parts[0])
                                gain = float(parts[1])
                                q = float(parts[2])
                                tipo = parts[3].strip()
                                if tipo.lower() == "peak": tipo = "Peaking"
                            except:
                                continue
                                
                    if freq is not None and gain is not None and q is not None and tipo is not None:
                        for ch in ins:
                            fid, p = self._crear_filtro_eq_dict(freq, gain, q, tipo, "in", ch)
                            patch_filters[fid] = p
                        for ch in outs:
                            fid, p = self._crear_filtro_eq_dict(freq, gain, q, tipo, "out", ch)
                            patch_filters[fid] = p
                        count += 1
            
            if count > 0:
                self.aplicar_y_guardar(patch_dict={"filters": patch_filters, "pipeline": self.config_raw.get("pipeline", [])})
                self.actualizar_tabla_ui()
                self.graph.update()
                msg = f"✅ Se importaron {count} filtros desde {path}." if self.current_lang == "es" else f"✅ {count} filters imported from {path}."
                self.log_v.append(msg)
            
        except Exception as e:
            self.log_v.append(f"❌ Error al importar filtros: {e}")

    def exportar_filtros(self):
        title = "Exportar Filtros" if self.current_lang == "es" else "Export Filters"
        path, _ = QFileDialog.getSaveFileName(self, title, "", "Text Files (*.txt)")
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write("Freq(Hz)\tGain(dB)\tQ\tTipo\n")
                exported = set()
                for fid, info in self.filtros_biquad.items():
                    dom = info["domain"]
                    visible_chs = [ch for ch in info["channels"] if (dom == "in" and ch in self.visible_in_channels) or (dom == "out" and ch in self.visible_out_channels)]
                    if not visible_chs: continue
                    
                    p = info["data"]["parameters"]
                    freq = p.get('freq', 1000.0)
                    gain = p.get('gain', 0.0)
                    q = p.get('q', 1.0)
                    tipo = p.get('type', 'Peaking')
                    if tipo == "Peaking": tipo = "Peak"
                    
                    param_tuple = (freq, gain, q, tipo)
                    if param_tuple not in exported:
                        exported.add(param_tuple)
                        f.write(f"{freq}\t{gain}\t{q}\t{tipo}\n")
            msg = f"✅ Filtros exportados a {path}" if self.current_lang == "es" else f"✅ Filters exported to {path}"
            self.log_v.append(msg)
        except Exception as e:
            self.log_v.append(f"❌ Error al exportar filtros: {e}")

    def on_cross_table_selection(self):
        selected = self.cross_table.selectedItems()
        self.cross_graph.highlighted_point = self.cross_table.item(selected[0].row(), 0).text() if selected else None
        self.cross_graph.update()

    def marcar_fila_activa_cross(self, fid):
        self.cross_table.blockSignals(True)
        for r in range(self.cross_table.rowCount()):
            it = self.cross_table.item(r, 0)
            if it and it.text() == fid: 
                self.cross_table.selectRow(r); self.cross_graph.highlighted_point = fid; break
        self.cross_table.blockSignals(False)

    def on_eq_table_selection(self):
        selected = self.table.selectedItems()
        self.graph.highlighted_point = self.table.item(selected[0].row(), 0).text() if selected else None
        self.graph.update()

    def marcar_fila_activa_eq(self, fid):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 0)
            if it and it.text() == fid: 
                self.table.selectRow(r); self.graph.highlighted_point = fid; break
        self.table.blockSignals(False)

    def _add_filter_to_pipeline(self, fid, domain, ch):
        pipeline = self.config_raw.setdefault("pipeline", [])
        mixer_idx = next((i for i, s in enumerate(pipeline) if s.get("type") == "Mixer"), -1)
        
        if domain == "in":
            search_space = pipeline[:mixer_idx if mixer_idx != -1 else len(pipeline)]
            insert_idx = mixer_idx if mixer_idx != -1 else len(pipeline)
        else:
            start_idx = mixer_idx + 1 if mixer_idx != -1 else 0
            search_space = pipeline[start_idx:]
            insert_idx = len(pipeline)
            
        group = "MISC"
        if fid.startswith("EQ_"): group = "EQ"
        elif fid.startswith("Cross_"): group = "CROSS"
        elif fid.startswith("Delay_"): group = "DELAY"
        
        ch_name = self.in_labels[ch] if domain == "in" else self.out_labels[ch] if ch < len(self.out_labels) else f"CH{ch}"
        expected_desc = f"{group}-{ch_name}"
            
        for step in search_space:
            if step.get("type") == "Filter" and self._get_chs_from_step(step) == [ch]:
                desc = step.get("description") or ""
                if desc == expected_desc:
                    if fid not in step.setdefault("names", []): step["names"].append(fid)
                    return

        pipeline.insert(insert_idx, {"type": "Filter", "channels": [ch], "names": [fid], "description": expected_desc, "bypassed": False})

    def _remove_filter_from_pipeline(self, fid):
        new_pipeline = []
        for step in self.config_raw.get("pipeline", []):
            if step.get("type") == "Filter" and "names" in step and fid in step["names"]:
                step["names"].remove(fid)
                if len(step["names"]) > 0:
                    new_pipeline.append(step)
            else:
                new_pipeline.append(step)
        self.config_raw["pipeline"] = new_pipeline

    def cambiar_delay(self, ch_index, filter_name, txt_val, ui_element=None):
        try: val = float(txt_val.replace(',', '.'))
        except ValueError: return
        val = max(0.0, val)
        
        if val == 0.0:
            changed = False
            if filter_name in self.config_raw.get("filters", {}):
                del self.config_raw["filters"][filter_name]
                changed = True
            
            self._remove_filter_from_pipeline(filter_name)
            patch_pipe = self.config_raw.get("pipeline", [])
                        
            if changed:
                self.aplicar_y_guardar(patch_dict={"filters": {filter_name: None}, "pipeline": patch_pipe})
                self.log_v.append(f"Delay CH {ch_index} borrado.")
            if ui_element: ui_element.setText("0.0")
            return
            
        filters = self.config_raw.setdefault("filters", {})
        if filter_name in filters:
            filters[filter_name]["parameters"]["delay"] = val
            try:
                self.aplicar_y_guardar(patch_dict={"filters": {filter_name: {"parameters": {"delay": val}}}})
                self.log_v.append(f"Delay CH {ch_index} actualizado: {val} ms")
            except Exception as e: self.log_v.append(f"Error Delay: {e}")
        else:
            if val == 0.0:
                if ui_element: ui_element.setText("0.0")
                return
                
            filters[filter_name] = {"type": "Delay", "description": None, "parameters": {"delay": val, "unit": "ms", "subsample": False}}
            self._add_filter_to_pipeline(filter_name, "out", ch_index)
            self.aplicar_y_guardar(patch_dict={"filters": {filter_name: filters[filter_name]}, "pipeline": self.config_raw["pipeline"]})
            self.log_v.append(f"Delay CH {ch_index} inyectado: {val} ms")

        if ui_element: ui_element.setText(str(val))

    def actualizar_celda_eq(self, fid, col, val_str):
        self.table.blockSignals(True)
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 0)
            if it and it.text() == fid:
                self.table.setItem(r, col, QTableWidgetItem(val_str)); break
        self.table.blockSignals(False)

    def actualizar_celda_cross(self, fid, col, val_str):
        self.cross_table.blockSignals(True)
        for r in range(self.cross_table.rowCount()):
            it = self.cross_table.item(r, 0)
            if it and it.text() == fid:
                self.cross_table.setItem(r, col, QTableWidgetItem(val_str)); break
        self.cross_table.blockSignals(False)

    def _crear_filtro_eq_dict(self, f, g, q, tipo, domain, ch):
        clean_ch = self.clean_name(self.in_labels[ch] if domain == "in" else self.out_labels[ch])
        fid = f"EQ_{domain.upper()}_{clean_ch}_{int(time.time()*1000)}_{ch}"
        while fid in self.config_raw.get("filters", {}):
            fid += "_1"
            
        p = {"type": tipo, "freq": float(f), "gain": float(g), "q": float(q)}
        filter_dict = {"type": "Biquad", "description": None, "parameters": p}
        
        self.config_raw.setdefault("filters", {})[fid] = filter_dict
        self.filtros_biquad[fid] = {"data": filter_dict, "domain": domain, "channels": [ch]}
        self._add_filter_to_pipeline(fid, domain, ch)
        return fid, filter_dict

    def crear_filtros_eq(self, f, g):
        ins = list(self.visible_in_channels); outs = list(self.visible_out_channels)
        if not ins and not outs:
            self.graph.show_warning(LANG[self.current_lang]["warn_msg"]); return
            
        patch_filters = {}
        for ch in ins: 
            fid, p = self._crear_filtro_eq_dict(f, g, 1.0, "Peaking", "in", ch)
            patch_filters[fid] = p
        for ch in outs: 
            fid, p = self._crear_filtro_eq_dict(f, g, 1.0, "Peaking", "out", ch)
            patch_filters[fid] = p
            
        self.aplicar_y_guardar(patch_dict={"filters": patch_filters, "pipeline": self.config_raw["pipeline"]})
        self.actualizar_tabla_ui(); self.graph.update()

    def _crear_filtro_crossover_dict(self, f, ch):
        clean_ch = self.clean_name(self.out_labels[ch])
        fid = f"Cross_OUT_{clean_ch}_{int(time.time()*1000)}_{ch}" 
        while fid in self.config_raw.get("filters", {}):
            fid += "_1"
        
        existing_types = [info["data"]["parameters"].get("type", "") for k, info in self.filtros_crossover.items() if ch in info["channels"] and info["domain"] == "out"]
        new_type = "LinkwitzRileyHighpass"
        for t in existing_types:
            if "Highpass" in t: new_type = "LinkwitzRileyLowpass"; break
            elif "Lowpass" in t: new_type = "LinkwitzRileyHighpass"; break
        
        f_d = {"type": "BiquadCombo", "description": None, "parameters": {"type": new_type, "freq": float(f), "order": 2}}
        self.config_raw.setdefault("filters", {})[fid] = f_d
        self.filtros_crossover[fid] = {"data": f_d, "domain": "out", "channels": [ch]}
        self._add_filter_to_pipeline(fid, "out", ch)
        return fid, f_d

    def crear_filtros_crossover(self, f):
        outs = list(self.visible_out_channels)
        if not outs: 
            self.cross_graph.show_warning(LANG[self.current_lang]["cross_warn_msg"]); return
            
        patch_filters = {}
        for ch in outs: 
            fid, p = self._crear_filtro_crossover_dict(f, ch)
            patch_filters[fid] = p
            
        self.aplicar_y_guardar(patch_dict={"filters": patch_filters, "pipeline": self.config_raw["pipeline"]})
        self.actualizar_tabla_crossover_ui(); self.cross_graph.update()

    def cambiar_canal_global(self, fid, nuevo_texto, dict_ref, prefix, ftype):
        if fid not in dict_ref: return
        if "Multi" in nuevo_texto: return 
        
        parts = nuevo_texto.split(" ", 1); n_dom = parts[0].lower()
        try: n_ch = int(parts[1].split(":")[0])
        except: return
        if prefix == "Cross" and n_dom == "in": self.actualizar_tabla_crossover_ui(); return
        
        old_dom, old_chs = dict_ref[fid]["domain"], dict_ref[fid]["channels"]
        if old_dom == n_dom and len(old_chs) == 1 and old_chs[0] == n_ch: return
        
        clean_ch = self.clean_name(self.in_labels[n_ch] if n_dom == "in" else self.out_labels[n_ch])
        p_fid = fid.split("_")
        timestamp = p_fid[-1] if p_fid[-1].isdigit() else str(int(time.time()*1000))
        nuevo_fid = f"{prefix}_{n_dom.upper()}_{clean_ch}_{timestamp}"
        while nuevo_fid in self.config_raw.get("filters", {}): nuevo_fid += "1"
        
        self._remove_filter_from_pipeline(fid)
        self._add_filter_to_pipeline(nuevo_fid, n_dom, n_ch)
            
        self.config_raw["filters"][nuevo_fid] = self.config_raw["filters"].pop(fid)
        dict_ref[nuevo_fid] = dict_ref.pop(fid)
        dict_ref[nuevo_fid]["domain"] = n_dom
        dict_ref[nuevo_fid]["channels"] = [n_ch]
        
        patch = {
            "filters": {fid: None, nuevo_fid: dict_ref[nuevo_fid]["data"]},
            "pipeline": self.config_raw["pipeline"]
        }
        self.aplicar_y_guardar(patch_dict=patch)

    def cambiar_canal_eq(self, fid, txt): self.cambiar_canal_global(fid, txt, self.filtros_biquad, "EQ", "Biquad"); self.actualizar_tabla_ui(); self.graph.update()
    def cambiar_canal_crossover(self, fid, txt): self.cambiar_canal_global(fid, txt, self.filtros_crossover, "Cross", "BiquadCombo"); self.actualizar_tabla_crossover_ui(); self.cross_graph.update()

    def actualizar_tabla_ui(self):
        self.table.blockSignals(True); self.table.setRowCount(0); tipos = ["Peaking", "Highshelf", "Lowshelf", "Highpass", "Lowpass"]
        for fid, info in self.filtros_biquad.items():
            r = self.table.rowCount(); self.table.insertRow(r); p = info["data"]["parameters"]; dom = info["domain"]; chs = info["channels"]
            it = QTableWidgetItem(fid); it.setFlags(it.flags() & ~Qt.ItemIsEditable); self.table.setItem(r, 0, it)
            cb = NoScrollComboBox(); cb.addItems(tipos); cb.blockSignals(True); cb.setCurrentText(p["type"]); cb.blockSignals(False); cb.currentTextChanged.connect(lambda t, f=fid: self.cambiar_tipo_eq(f, t)); self.table.setCellWidget(r, 1, cb)
            self.table.setItem(r, 2, QTableWidgetItem(f"{p['freq']:.0f}"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{p.get('gain',0):.1f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"{p.get('q',1.0):.2f}"))
            cb_ch = NoScrollComboBox(); cb_ch.addItems(self.combo_ch_list); cb_ch.blockSignals(True)
            
            if len(chs) == 1:
                ch = chs[0]
                ch_name = self.in_labels[ch] if dom == "in" and ch < len(self.in_labels) else self.out_labels[ch] if dom == "out" and ch < len(self.out_labels) else str(ch)
                txt = f"{dom} {ch}: {ch_name}"
            else:
                txt = f"{dom} Multi: {chs}"
                cb_ch.addItem(txt)
                
            cb_ch.setCurrentText(txt); cb_ch.blockSignals(False)
            cb_ch.currentTextChanged.connect(lambda t, f=fid: self.cambiar_canal_eq(f, t)); self.table.setCellWidget(r, 5, cb_ch)
            btn = QPushButton("X"); btn.clicked.connect(lambda _, f=fid: self.borrar_eq(f)); self.table.setCellWidget(r, 6, btn)
        self.table.blockSignals(False)

    def actualizar_tabla_crossover_ui(self):
        self.cross_table.blockSignals(True); self.cross_table.setRowCount(0)
        tipos = ["ButterworthHighpass", "ButterworthLowpass", "LinkwitzRileyHighpass", "LinkwitzRileyLowpass"]
        for fid, info in self.filtros_crossover.items():
            r = self.cross_table.rowCount(); self.cross_table.insertRow(r); p = info["data"]["parameters"]; chs = info["channels"]; dom = info["domain"]
            it = QTableWidgetItem(fid); it.setFlags(it.flags() & ~Qt.ItemIsEditable); self.cross_table.setItem(r, 0, it)
            cb = NoScrollComboBox(); cb.addItems(tipos); cb.blockSignals(True); cb.setCurrentText(p.get("type", "ButterworthHighpass")); cb.blockSignals(False); cb.currentTextChanged.connect(lambda t, f=fid: self.cambiar_tipo_crossover(f, t)); self.cross_table.setCellWidget(r, 1, cb)
            self.cross_table.setItem(r, 2, QTableWidgetItem(f"{p.get('freq', 1000):.0f}"))
            
            cb_order = NoScrollComboBox()
            ord_opts = ["1 (6 dB/octava)", "2 (12 dB/octava)", "3 (18 dB/octava)", "4 (24 dB/octava)"]
            cb_order.addItems(ord_opts)
            cb_order.blockSignals(True)
            current_order = int(p.get('order', 2))
            opt_idx = max(0, min(3, current_order - 1))
            cb_order.setCurrentIndex(opt_idx)
            cb_order.blockSignals(False)
            cb_order.currentIndexChanged.connect(lambda idx, f=fid: self.cambiar_orden_crossover(f, idx + 1))
            self.cross_table.setCellWidget(r, 3, cb_order)
            
            cb_ch = NoScrollComboBox(); cb_ch.addItems(self.combo_out_ch_list); cb_ch.blockSignals(True)
            
            if len(chs) == 1:
                ch = chs[0]
                ch_name = self.out_labels[ch] if ch < len(self.out_labels) else str(ch)
                txt = f"out {ch}: {ch_name}"
            else:
                txt = f"out Multi: {chs}"
                cb_ch.addItem(txt)
                
            cb_ch.setCurrentText(txt); cb_ch.blockSignals(False)
            cb_ch.currentTextChanged.connect(lambda t, f=fid: self.cambiar_canal_crossover(f, t)); self.cross_table.setCellWidget(r, 4, cb_ch)
            btn = QPushButton("X"); btn.clicked.connect(lambda _, f=fid: self.borrar_crossover(f)); self.cross_table.setCellWidget(r, 5, btn)
        self.cross_table.blockSignals(False)

    def modificar_filtro_desde_tabla(self, item):
        r = item.row(); c = item.column(); fid = self.table.item(r, 0).text()
        if c not in [2, 3, 4] or fid not in self.filtros_biquad: return
        try: val = float(item.text())
        except ValueError: return
        param = {2: "freq", 3: "gain", 4: "q"}[c]
        self.filtros_biquad[fid]["data"]["parameters"][param] = val
        self.config_raw["filters"][fid]["parameters"][param] = val
        patch = {"filters": {fid: {"parameters": {param: val}}}}
        self.aplicar_y_guardar(patch_dict=patch)
        self.graph.update()

    def modificar_crossover_desde_tabla(self, item):
        r = item.row(); c = item.column(); fid = self.cross_table.item(r, 0).text()
        if c != 2 or fid not in self.filtros_crossover: return
        try: val = float(item.text())
        except ValueError: return
        p = self.filtros_crossover[fid]["data"]["parameters"]
        p["freq"] = val
        self.config_raw["filters"][fid]["parameters"]["freq"] = val
        patch = {"filters": {fid: {"parameters": {"freq": val}}}}
        self.aplicar_y_guardar(patch_dict=patch)
        self.cross_graph.update()

    def cambiar_orden_crossover(self, fid, new_order):
        if fid not in self.filtros_crossover: return
        p = self.filtros_crossover[fid]["data"]["parameters"]
        
        p["order"] = new_order
        self.config_raw["filters"][fid]["parameters"]["order"] = new_order
        patch = {"filters": {fid: {"parameters": {"order": new_order}}}}
        self.aplicar_y_guardar(patch_dict=patch)
        self.cross_graph.update()

    def cambiar_tipo_eq(self, fid, nt):
        if fid in self.filtros_biquad:
            self.filtros_biquad[fid]["data"]["parameters"]["type"] = nt
            self.config_raw["filters"][fid]["parameters"]["type"] = nt
            patch = {"filters": {fid: {"parameters": {"type": nt}}}}
            self.aplicar_y_guardar(patch_dict=patch)
            self.graph.update()

    def cambiar_tipo_crossover(self, fid, nt):
        if fid in self.filtros_crossover:
            p = self.filtros_crossover[fid]["data"]["parameters"]; p["type"] = nt
            self.config_raw["filters"][fid]["parameters"]["type"] = nt
            patch_dict = {"filters": {fid: {"parameters": {"type": nt}}}}
            self.aplicar_y_guardar(patch_dict=patch_dict)
            self.cross_graph.update()

    def borrar_eq(self, fid):
        if fid in self.filtros_biquad:
            del self.filtros_biquad[fid]
            if fid in self.config_raw.get("filters", {}):
                del self.config_raw["filters"][fid]
            self._remove_filter_from_pipeline(fid)
            
            patch = {
                "filters": {fid: None},
                "pipeline": self.config_raw.get("pipeline", [])
            }
            self.aplicar_y_guardar(patch_dict=patch)
            self.actualizar_tabla_ui(); self.graph.update()

    def borrar_crossover(self, fid):
        if fid in self.filtros_crossover:
            del self.filtros_crossover[fid]
            if fid in self.config_raw.get("filters", {}):
                del self.config_raw["filters"][fid]
            self._remove_filter_from_pipeline(fid)
            
            patch = {
                "filters": {fid: None},
                "pipeline": self.config_raw.get("pipeline", [])
            }
            self.aplicar_y_guardar(patch_dict=patch)
            self.actualizar_tabla_crossover_ui(); self.cross_graph.update()

    def crear_compresor(self, name, ch_index, threshold_db, vu_ref):
        try:
            comp_name = f"Comp_{self.clean_name(name)}"
            total_out_ch = self.config_raw.get("devices", {}).get("playback", {}).get("channels", len(self.v_out))
            
            atk = 0.2
            rel = 1.0
            factor = 5.0
            makeup = 0.0
            soft_clip = False
            clip_limit = None
            
            existing_pid = None
            for pid, pdata in self.config_raw.get("processors", {}).items():
                if pdata.get("type") == "Compressor" and pdata.get("parameters", {}).get("process_channels", [-1])[0] == ch_index:
                    existing_pid = pid
                    break
            
            if existing_pid:
                comp_name = existing_pid
                old_p = self.config_raw["processors"][comp_name].get("parameters", {})
                atk = old_p.get("attack", atk)
                rel = old_p.get("release", rel)
                factor = old_p.get("factor", factor)
                makeup = old_p.get("makeup_gain", makeup)
                soft_clip = old_p.get("soft_clip", soft_clip)
                clip_limit = old_p.get("clip_limit", clip_limit)

            comp_data = {
                "type": "Compressor",
                "description": None,
                "parameters": {
                    "channels": total_out_ch,
                    "monitor_channels": [ch_index],
                    "process_channels": [ch_index],
                    "attack": atk,
                    "release": rel,
                    "threshold": float(f"{threshold_db:.1f}"),
                    "factor": factor,
                    "makeup_gain": makeup,
                    "soft_clip": soft_clip,
                    "clip_limit": clip_limit
                }
            }
            self.config_raw.setdefault("processors", {})[comp_name] = comp_data
            
            patch_dict = {"processors": {comp_name: comp_data}}
            
            if "pipeline" not in self.config_raw: self.config_raw["pipeline"] = []
            target = next((s for s in self.config_raw["pipeline"] if s.get("type") == "Processor" and s.get("name") == comp_name), None)
            
            if not target:
                target = {"type": "Processor", "name": comp_name, "description": None}
                self.config_raw["pipeline"].append(target)
                patch_dict["pipeline"] = self.config_raw["pipeline"]
                
            self.aplicar_y_guardar(patch_dict=patch_dict)
            vu_ref.comp_threshold = threshold_db
            vu_ref.comp_ratio = factor
            vu_ref.comp_makeup = makeup
            vu_ref.update(); self.actualizar_tabla_comp_ui()
            self.log_v.append(f"✅ Compresor '{comp_name}' actualizado/creado a {threshold_db:.1f}dB.")
        except Exception as e:
            self.log_v.append(f"❌ Error interno creando compresor: {e}\n{traceback.format_exc()}")

    def borrar_compresor_por_id(self, comp_name):
        try:
            changed = False
            patch = {"processors": {comp_name: None}}
            if "processors" in self.config_raw and comp_name in self.config_raw["processors"]:
                ch_idx = self.config_raw["processors"][comp_name]["parameters"]["process_channels"][0]
                del self.config_raw["processors"][comp_name]
                changed = True
                
                if ch_idx < len(self.v_out):
                    self.v_out[ch_idx].comp_threshold = None
                    self.v_out[ch_idx].comp_ratio = 1.0
                    self.v_out[ch_idx].comp_makeup = 0.0
                    self.v_out[ch_idx].update()
                
            if "pipeline" in self.config_raw:
                new_pipe = []
                for s in self.config_raw["pipeline"]:
                    if s.get("type") == "Processor" and s.get("name") == comp_name:
                        continue
                    new_pipe.append(s)
                if len(new_pipe) != len(self.config_raw["pipeline"]):
                    self.config_raw["pipeline"] = new_pipe
                    patch["pipeline"] = new_pipe
                    changed = True
            
            if changed:
                self.aplicar_y_guardar(patch_dict=patch)
                self.actualizar_tabla_comp_ui()
                self.log_v.append(f"✅ Compresor '{comp_name}' eliminado permanentemente de la memoria.")
        except Exception as e:
            self.log_v.append(f"❌ Error borrando compresor: {e}")

    def actualizar_tabla_comp_ui(self):
        self.comp_table.blockSignals(True)
        self.comp_table.setRowCount(0)
        processors = self.config_raw.get("processors", {})
        for pid, pdata in processors.items():
            if pdata.get("type") == "Compressor":
                r = self.comp_table.rowCount(); self.comp_table.insertRow(r); params = pdata.get("parameters", {})
                it_id = QTableWidgetItem(pid); it_id.setFlags(it_id.flags() & ~Qt.ItemIsEditable); self.comp_table.setItem(r, 0, it_id)
                self.comp_table.setItem(r, 1, QTableWidgetItem(str(params.get("attack", 0.2))))
                self.comp_table.setItem(r, 2, QTableWidgetItem(str(params.get("release", 1.0))))
                self.comp_table.setItem(r, 3, QTableWidgetItem(str(params.get("threshold", -20.0))))
                self.comp_table.setItem(r, 4, QTableWidgetItem(str(params.get("factor", 5.0))))
                self.comp_table.setItem(r, 5, QTableWidgetItem(str(params.get("makeup_gain", 0.0))))
                c_lim = params.get("clip_limit", None)
                self.comp_table.setItem(r, 6, QTableWidgetItem(str(c_lim if c_lim is not None else "0.0")))
                btn_auto = QPushButton("AUTO")
                if pid in self.auto_samplers:
                    btn_auto.setText(f"{self.auto_samplers[pid]['ticks']//20}s")
                    btn_auto.setEnabled(False); btn_auto.setStyleSheet("background: #aa8800; color: white; border-radius: 3px; font-weight: bold;")
                else:
                    btn_auto.setStyleSheet("background: #007bff; color: white; border-radius: 3px; font-weight: bold;")
                    btn_auto.clicked.connect(lambda ch, f=pid, b=btn_auto: self.iniciar_auto_compresion(f, b))
                self.comp_table.setCellWidget(r, 7, btn_auto)
                btn_del = QPushButton("X"); btn_del.clicked.connect(lambda ch, f=pid: self.borrar_compresor_por_id(f))
                self.comp_table.setCellWidget(r, 8, btn_del)
        self.comp_table.blockSignals(False)

    def modificar_compresor_desde_tabla(self, item):
        r = item.row(); c = item.column()
        if c == 0 or c == 7 or c == 8: return
        pid = self.comp_table.item(r, 0).text()
        
        param_map = ["", "attack", "release", "threshold", "factor", "makeup_gain", "clip_limit"]
        param = param_map[c]

        try: 
            if param == "factor": 
                val = int(item.text())
                val = max(1, min(99, val))
                self.comp_table.blockSignals(True)
                item.setText(str(val))
                self.comp_table.blockSignals(False)
            else:
                val = float(item.text())
        except ValueError: 
            return
        
        if pid in self.config_raw.get("processors", {}):
            if param == "clip_limit" and val == 0.0: val = None 
            self.config_raw["processors"][pid]["parameters"][param] = val
            ch_idx = self.config_raw["processors"][pid]["parameters"]["process_channels"][0]
            if ch_idx < len(self.v_out):
                if param == "threshold":
                    self.v_out[ch_idx].comp_threshold = val
                    self.v_out[ch_idx].update()
                elif param == "factor":
                    self.v_out[ch_idx].comp_ratio = val
                    self.v_out[ch_idx].update()
                elif param == "makeup_gain":
                    self.v_out[ch_idx].comp_makeup = val
                    self.v_out[ch_idx].update()
            
            patch = {"processors": {pid: {"type": "Compressor", "description": None, "parameters": self.config_raw["processors"][pid]["parameters"]}}}
            self.aplicar_y_guardar(patch_dict=patch)
            self.log_v.append(f"Compresor {pid} actualizado: {param} = {val}")

    def iniciar_auto_compresion(self, pid, btn):
        ch_index = self.config_raw["processors"][pid]["parameters"]["process_channels"][0]
        self.auto_samplers[pid] = {"ticks": 100, "ch": ch_index, "history": [], "btn": btn}
        btn.setText("5s"); btn.setEnabled(False); btn.setStyleSheet("background: #aa8800; color: white; border-radius: 3px; font-weight: bold;")
        self.log_v.append(f"AUTO-MUESTREO {pid}: Leyendo dinámica por 5 segundos...")

    def finalizar_auto_compresion(self, pid):
        data = self.auto_samplers.pop(pid); btn = data["btn"]
        history = [x for x in data["history"] if x > -80.0]
        if not history: 
            self.log_v.append(f"AUTO-COMP {pid}: No se detectó audio en el canal. Abortado.")
        else:
            sum_energy = sum([10.0 ** (x / 10.0) for x in history])
            rms_db = 10.0 * math.log10(sum_energy / len(history))
            peak_db = max(history)
            crest_factor = peak_db - rms_db

            peaks = []
            peak_thresh = rms_db + (crest_factor * 0.4)
            for i in range(1, len(history)-1):
                if history[i] > peak_thresh and history[i] > history[i-1] and history[i] > history[i+1]:
                    peaks.append(i)
            
            bpm = 120.0
            if len(peaks) > 2:
                distances = [peaks[j] - peaks[j-1] for j in range(1, len(peaks))]
                avg_dist = sum(distances) / len(distances)
                if avg_dist > 0:
                    bpm = 60.0 / (avg_dist * 0.05)
                    while bpm < 60.0: bpm *= 2.0
                    while bpm > 200.0: bpm /= 2.0
            
            if crest_factor > 14.0:
                atk, factor = 0.005, 8.0
                rel = 15.0 / bpm
            elif crest_factor > 10.0:
                atk, factor = 0.012, 4.0
                rel = 30.0 / bpm
            elif crest_factor > 6.0:
                atk, factor = 0.025, 3.0
                rel = 60.0 / bpm
            else:
                atk, factor = 0.050, 2.0
                rel = 120.0 / bpm
                
            atk = round(atk, 3)
            rel = round(rel, 3)
            factor = round(factor, 1)
            
            threshold = self.config_raw["processors"][pid]["parameters"].get("threshold", -20.0)
            
            sum_energy_uncomp = 0.0
            sum_energy_comp = 0.0
            
            for x in history:
                sum_energy_uncomp += 10.0 ** (x / 10.0)
                if x > threshold:
                    comp_x = threshold + ((x - threshold) / max(1.0, factor))
                else:
                    comp_x = x
                sum_energy_comp += 10.0 ** (comp_x / 10.0)
                
            if sum_energy_comp > 0 and sum_energy_uncomp > 0:
                rms_uncomp = 10.0 * math.log10(sum_energy_uncomp / len(history))
                rms_comp = 10.0 * math.log10(sum_energy_comp / len(history))
                makeup = round((rms_uncomp - rms_comp) + 0.5, 1)
            else:
                makeup = 0.0
            
            self.config_raw["processors"][pid]["parameters"]["attack"] = atk
            self.config_raw["processors"][pid]["parameters"]["release"] = rel
            self.config_raw["processors"][pid]["parameters"]["factor"] = factor
            self.config_raw["processors"][pid]["parameters"]["makeup_gain"] = makeup
            
            ch_idx = self.config_raw["processors"][pid]["parameters"]["process_channels"][0]
            if ch_idx < len(self.v_out):
                self.v_out[ch_idx].comp_ratio = factor
                self.v_out[ch_idx].comp_makeup = makeup
                self.v_out[ch_idx].update()
            
            patch = {"processors": {pid: {"type": "Compressor", "description": None, "parameters": self.config_raw["processors"][pid]["parameters"]}}}
            self.aplicar_y_guardar(patch_dict=patch)
            self.actualizar_tabla_comp_ui()
            self.log_v.append(f"✅ AUTO {pid}: BPM={bpm:.0f} | CF={crest_factor:.1f}dB -> Ratio={factor:.1f}:1, Atk={atk}s, Rel={rel}s | MakeUp=+{makeup}dB")
                
        try: 
            btn.setText("AUTO")
            btn.setEnabled(True)
            btn.setStyleSheet("background: #007bff; color: white; border-radius: 3px; font-weight: bold;")
        except: pass

    def up_v(self):
        try:
            if not getattr(self, 'v_in', None) or not getattr(self, 'v_out', None): return
            if hasattr(self.cdsp, 'levels'):
                ir = self.cdsp.levels.capture_rms(); orr = self.cdsp.levels.playback_rms()
                for i, v in enumerate(self.v_in): v.set_level(ir[i] if i < len(ir) else -80)
                for i, v in enumerate(self.v_out): v.set_level(orr[i] if i < len(orr) else -80)
                to_finish = []
                for pid, data in self.auto_samplers.items():
                    ch = data["ch"]
                    if ch < len(orr): data["history"].append(orr[ch])
                    data["ticks"] -= 1
                    if data["ticks"] % 20 == 0:
                        try: data["btn"].setText(f"{data['ticks']//20}s")
                        except: pass
                    if data["ticks"] <= 0: to_finish.append(pid)
                for pid in to_finish: self.finalizar_auto_compresion(pid)
        except Exception: pass

if __name__ == "__main__":
    app = QApplication(sys.argv); window = PEQApp(); window.show(); sys.exit(app.exec())