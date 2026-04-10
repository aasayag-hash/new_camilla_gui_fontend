// Sistema de internacionalización ES/EN
import { Events } from './events.js';

const LANG = {
    es: {
        title: "CAMILLADSP MASTER CONSOLE",
        ip_label: "IP Servidor:",
        port_label: "Puerto:",
        btn_scan: "CONECTAR A HARDWARE",
        btn_help: "AYUDA / MANUAL",
        btn_lang: "EN / ES",
        btn_reset: "RESET",
        warn_no_channels: "Para crear filtros, selecciona al menos un canal en las solapas.",
        warn_cross_no_out: "Para crear un crossover, selecciona AL MENOS UNA SALIDA (OUT) en las solapas.",
        tab_vu: "VÚMETROS Y DINÁMICA",
        tab_eq: "FILTROS Y EQ",
        tab_cross: "CROSSOVERS",
        tab_mixer: "MIXER",
        view_label: "VISTA:",
        view_all: "TODO",
        view_in: "ENTRADAS",
        view_out: "SALIDAS",
        mute_all: "MUTE ALL",
        help_title: "Manual de Usuario",
        btn_close: "Cerrar",
        btn_imp_cfg: "Imp Cfg",
        btn_exp_cfg: "Exp Cfg",
        btn_imp_eq: "Imp EQ",
        btn_exp_eq: "Exp EQ",
        btn_reset_top: "Reset",
        btn_log: "Log",
        btn_help2: "Ayuda",
        btn_web: "WEB",
        rename_title: "Renombrar Canal",
        rename_label: "Nuevo nombre:",
        reset_confirm: "¿Está seguro? Esto enviará la configuración por defecto a CamillaDSP.",
        reset_in_label: "Cantidad de canales de ENTRADA del hardware:",
        reset_out_label: "Cantidad de canales de SALIDA del hardware:",
        reset_in_title: "RESET - Entradas",
        reset_out_title: "RESET - Salidas",
        reset_success: "Config enviada:",
        reset_inputs: "entradas",
        reset_outputs: "salidas",
        connecting: "Conectando...",
        connected: "✓ Conectado a",
        error_port: "Error: El puerto debe ser un número.",
        error_connect: "Error al conectar con",
        reset_warn_title: "RESET",
        reset_warn_body: "¿Está seguro? Esto borrará toda la configuración actual.",
        yes: "Sí",
        no: "No",
        ok: "OK",
        cancel: "Cancelar",
        dly_ms: "DLY(ms)",
        all_in: "ALL IN",
        all_out: "ALL OUT",
        comp_id: "Comp ID",
        comp_atk: "Attack (s)",
        comp_rel: "Release (s)",
        comp_thr: "Threshold (dB)",
        comp_ratio: "Ratio",
        comp_makeup: "Makeup (dB)",
        comp_clip: "ClipLim",
        comp_auto: "Auto",
        comp_del: "Del",
        filter_id: "Filter ID",
        filter_type: "Tipo",
        filter_freq: "Freq (Hz)",
        filter_gain: "Gain (dB)",
        filter_q: "Q",
        filter_ch: "Canal",
        filter_del: "Del",
        cross_ord: "Orden",
        auto_sampling: "Muestreando por 5s...",
        help_text: `=== PANTALLA DE INICIO ===
• IP / Puerto: Ingrese la IP y puerto del servidor CamillaDSP.
• CONECTAR A HARDWARE: Conecta al servidor y abre la consola.
• Camilla WEB: Abre la interfaz web (puerto 5005).
• RESET: Envía una configuración vacía. Pide cantidad de canales IN/OUT.
• EN/ES: Cambia idioma.

=== PANEL DE CANALES ===
• Solapas IN/OUT: Seleccionan qué canales son visibles.
• Clic Derecho (Solapa): Activa/Desactiva BYPASS de EQ para ese canal.
• Botón ALL: Selecciona/Deselecciona todos los canales.

=== BOTONES SUPERIORES ===
• WEB: Abre interfaz web del backend.
• Imp Cfg / Exp Cfg: Importa/Exporta configuración completa YAML/JSON.
• Imp EQ / Exp EQ: Importa/Exporta filtros de EQ.
• Reset: Restaura config por defecto (solicita confirmación).
• Log: Abre consola de comandos.

=== GRÁFICOS EQ Y CROSSOVERS ===
• Doble Clic Izquierdo: CREA un filtro en los canales seleccionados.
• Clic Izquierdo Sostenido: Arrastra para ajustar Frecuencia/Ganancia.
• Rueda del Mouse: Ajusta el Factor Q (EQ) u Orden (Crossover).
• Clic Derecho: BORRA el filtro seleccionado.

=== TABLAS DE FILTROS ===
• Editar celdas directamente para cambiar valores.
• ComboBox Tipo: Cambia el tipo de filtro.
• ComboBox Canal: Reasigna el filtro a otro canal.
• Botón X: Borra el filtro.

=== MATRIZ MIXER ===
• Clic Izquierdo (celda vacía '+'):  CREA conexión (In → Out).
• Clic Derecho (celda verde): ELIMINA la conexión.
• Doble Clic (nombre): Renombra Entrada o Salida.

=== VÚMETROS Y DINÁMICAS ===
• Botones VISTA: Filtra para ver Entradas, Salidas, o Todo.
• Fader MASTER: Controla el volumen global.
• MUTE ALL: Silencia/restaura todas las salidas.
• Clic (Nombre Salida): Mutea o activa el canal.
• Arrastrar Fader: Ajusta volumen -30dB a +10dB.
• Clic Derecho (Fader/Delay): Resetea a 0.
• Botón +/-: Invierte la polaridad del canal.
• DLY(ms): Ajusta el delay por canal.

=== COMPRESORES ===
• Doble Clic (Barra VÚmetro): CREA compresor con threshold en ese punto.
• Clic Derecho (Barra VÚmetro): BORRA el compresor.
• Botón AUTO: Muestrea 5s y calcula parámetros automáticamente.`
    },
    en: {
        title: "CAMILLADSP MASTER CONSOLE",
        ip_label: "Server IP:",
        port_label: "Port:",
        btn_scan: "CONNECT HARDWARE",
        btn_help: "HELP / MANUAL",
        btn_lang: "ES / EN",
        btn_reset: "RESET",
        warn_no_channels: "To create filters, select at least one channel from the tabs.",
        warn_cross_no_out: "To create a crossover, select AT LEAST ONE OUTPUT (OUT) from the tabs.",
        tab_vu: "VUMETERS & DYNAMICS",
        tab_eq: "EQ & FILTERS",
        tab_cross: "CROSSOVERS",
        tab_mixer: "MIXER",
        view_label: "VIEW:",
        view_all: "ALL",
        view_in: "INPUTS",
        view_out: "OUTPUTS",
        mute_all: "MUTE ALL",
        help_title: "User Manual",
        btn_close: "Close",
        btn_imp_cfg: "Imp Cfg",
        btn_exp_cfg: "Exp Cfg",
        btn_imp_eq: "Imp EQ",
        btn_exp_eq: "Exp EQ",
        btn_reset_top: "Reset",
        btn_log: "Log",
        btn_help2: "Help",
        btn_web: "WEB",
        rename_title: "Rename Channel",
        rename_label: "New name:",
        reset_confirm: "Are you sure? This will send the default config to CamillaDSP.",
        reset_in_label: "Number of hardware INPUT channels:",
        reset_out_label: "Number of hardware OUTPUT channels:",
        reset_in_title: "RESET - Inputs",
        reset_out_title: "RESET - Outputs",
        reset_success: "Config sent:",
        reset_inputs: "inputs",
        reset_outputs: "outputs",
        connecting: "Connecting...",
        connected: "✓ Connected to",
        error_port: "Error: Port must be a number.",
        error_connect: "Error connecting to",
        reset_warn_title: "RESET",
        reset_warn_body: "Are you sure? This will wipe all current CamillaDSP configuration.",
        yes: "Yes",
        no: "No",
        ok: "OK",
        cancel: "Cancel",
        dly_ms: "DLY(ms)",
        all_in: "ALL IN",
        all_out: "ALL OUT",
        comp_id: "Comp ID",
        comp_atk: "Attack (s)",
        comp_rel: "Release (s)",
        comp_thr: "Threshold (dB)",
        comp_ratio: "Ratio",
        comp_makeup: "Makeup (dB)",
        comp_clip: "ClipLim",
        comp_auto: "Auto",
        comp_del: "Del",
        filter_id: "Filter ID",
        filter_type: "Type",
        filter_freq: "Freq (Hz)",
        filter_gain: "Gain (dB)",
        filter_q: "Q",
        filter_ch: "Channel",
        filter_del: "Del",
        cross_ord: "Order",
        auto_sampling: "Sampling for 5s...",
        help_text: `=== START SCREEN ===
• IP / Port: Enter the CamillaDSP server IP and port.
• CONNECT HARDWARE: Connects to server and opens the console.
• Camilla WEB: Opens web interface (port 5005).
• RESET: Sends a clean default config. Asks for IN/OUT channel count.
• ES/EN: Switch language.

=== CHANNEL PANEL ===
• IN/OUT Tabs: Select which channels are visible.
• Right Click (Tab): Toggles EQ BYPASS for that channel.
• ALL Button: Select/Deselect all channels.

=== TOP BUTTONS ===
• WEB: Opens backend web interface.
• Imp Cfg / Exp Cfg: Import/Export full config YAML/JSON.
• Imp EQ / Exp EQ: Import/Export EQ filters.
• Reset: Restore default config (asks for confirmation).
• Log: Opens command console.

=== EQ & CROSSOVER GRAPHS ===
• Double Left Click: CREATES a filter on selected channels.
• Left Click Hold: Drag to adjust Frequency/Gain.
• Mouse Wheel: Adjust Q Factor (EQ) or Order (Crossover).
• Right Click: DELETES the selected filter.

=== FILTER TABLES ===
• Edit cells directly to change values.
• Type ComboBox: Changes the filter type.
• Channel ComboBox: Reassigns filter to another channel.
• X Button: Deletes the filter.

=== MIXER MATRIX ===
• Left Click (empty '+' cell): CREATES routing connection (In → Out).
• Right Click (green cell): REMOVES the routing connection.
• Double Click (name): Renames Input or Output.

=== VUMETERS & DYNAMICS ===
• VIEW Buttons: Filter to see Inputs, Outputs, or All.
• MASTER Fader: Controls global volume.
• MUTE ALL: Mutes/restores all outputs.
• Click (Output Name): Mutes or activates the channel.
• Drag Fader: Adjusts volume from -30dB to +10dB.
• Right Click (Fader/Delay): Resets to 0.
• +/- Button: Inverts channel polarity.
• DLY(ms): Adjusts per-channel delay.

=== COMPRESSORS ===
• Double Click (VU Bar): CREATES compressor with threshold at clicked point.
• Right Click (VU Bar): DELETES the compressor.
• AUTO Button: Samples 5s and automatically calculates parameters.`
    }
};

let _currentLang = 'es';

export function t(key) {
    return LANG[_currentLang][key] ?? LANG['es'][key] ?? key;
}

export function getLang() {
    return _currentLang;
}

export function setLang(lang) {
    if (lang !== 'es' && lang !== 'en') return;
    _currentLang = lang;
    Events.emit('lang:changed', lang);
}

export function toggleLang() {
    setLang(_currentLang === 'es' ? 'en' : 'es');
}
