// login.js — Pantalla de login: IP/port, conexión, reset desde login
import { t, getLang, toggleLang, Events } from '../core/i18n.js';
import * as API from '../core/api.js';
import { reloadConfig, setFullConfig } from '../core/state.js';
import { showSnack } from './snack.js';

const LS_IP   = 'camilla_ip';
const LS_PORT = 'camilla_port';

function getSavedIP()   { return localStorage.getItem(LS_IP)   || ''; }
function getSavedPort() { return localStorage.getItem(LS_PORT) || '5005'; }

export function initLogin(onConnected) {
    const screen = document.getElementById('screen-login');
    const titleEl  = document.getElementById('login-title');
    const ipLbl    = document.getElementById('login-ip-label');
    const portLbl  = document.getElementById('login-port-label');
    const ipInput  = document.getElementById('login-ip');
    const portInput= document.getElementById('login-port');
    const btnConn  = document.getElementById('btn-connect');
    const btnHelp  = document.getElementById('btn-login-help');
    const btnLang  = document.getElementById('btn-login-lang');
    const btnReset = document.getElementById('btn-login-reset');
    const statusEl = document.getElementById('login-status');

    // Cargar guardados
    ipInput.value   = getSavedIP();
    portInput.value = getSavedPort();

    function applyI18n() {
        titleEl.textContent  = t('title');
        ipLbl.textContent    = t('ip_label');
        portLbl.textContent  = t('port_label');
        btnConn.textContent  = t('btn_scan');
        btnHelp.textContent  = t('btn_help');
        btnLang.textContent  = t('btn_lang');
        btnReset.textContent = t('btn_reset');
    }
    applyI18n();
    Events.on('lang:changed', applyI18n);

    function setStatus(msg, cls = '') {
        statusEl.textContent = msg;
        statusEl.className = cls;
    }

    async function connect() {
        const ip   = ipInput.value.trim();
        const port = portInput.value.trim();
        if (!port || isNaN(port)) {
            setStatus(t('error_port'), 'error');
            return;
        }
        const base = `http://${ip}:${port}`;
        window.CAMILLA_BASE = base;
        setStatus(t('connecting'));
        try {
            await API.getStatus();
            localStorage.setItem(LS_IP, ip);
            localStorage.setItem(LS_PORT, port);
            setStatus(`${t('connected')} ${base}`, 'ok');
            await reloadConfig();
            onConnected(ip, port);
        } catch (e) {
            setStatus(`${t('error_connect')} ${base}`, 'error');
            console.error('[login] connect error:', e);
        }
    }

    btnConn.addEventListener('click', connect);
    portInput.addEventListener('keydown', e => { if (e.key === 'Enter') connect(); });
    ipInput.addEventListener('keydown', e => { if (e.key === 'Enter') connect(); });

    btnLang.addEventListener('click', toggleLang);

    btnHelp.addEventListener('click', () => {
        document.getElementById('modal-help').classList.remove('hidden');
        document.getElementById('help-text').textContent = t('help_text');
        document.getElementById('modal-help-title').textContent = t('help_title');
    });

    btnReset.addEventListener('click', () => showResetFromLogin());

    // ── Reset desde login ────────────────────────────────────────────────
    async function showResetFromLogin() {
        const modal = document.getElementById('modal-reset');
        document.getElementById('modal-reset-title').textContent = t('reset_warn_title');
        document.getElementById('modal-reset-body').textContent  = t('reset_warn_body');
        document.getElementById('reset-in-label').textContent    = t('reset_in_label');
        document.getElementById('reset-out-label').textContent   = t('reset_out_label');
        document.getElementById('reset-in-val').value  = 2;
        document.getElementById('reset-out-val').value = 2;
        modal.classList.remove('hidden');

        const btnYes = document.getElementById('btn-reset-yes');
        const btnNo  = document.getElementById('btn-reset-no');
        document.getElementById('btn-reset-yes-label').textContent = t('yes');
        document.getElementById('btn-reset-no-label').textContent  = t('no');

        const onYes = async () => {
            const nIn  = parseInt(document.getElementById('reset-in-val').value)  || 2;
            const nOut = parseInt(document.getElementById('reset-out-val').value) || 2;
            modal.classList.add('hidden');
            cleanup();
            const ip   = ipInput.value.trim();
            const port = portInput.value.trim();
            window.CAMILLA_BASE = `http://${ip}:${port}`;
            try {
                const cfg = buildDefaultConfig(nIn, nOut);
                await API.setConfig(cfg);
                setStatus(`${t('reset_success')} ${nIn} ${t('reset_inputs')}, ${nOut} ${t('reset_outputs')}`, 'ok');
            } catch (err) {
                setStatus(`${t('error_connect')} ${window.CAMILLA_BASE}`, 'error');
            }
        };
        const onNo = () => { modal.classList.add('hidden'); cleanup(); };
        const cleanup = () => {
            btnYes.removeEventListener('click', onYes);
            btnNo.removeEventListener('click', onNo);
        };
        btnYes.addEventListener('click', onYes);
        btnNo.addEventListener('click', onNo);
    }
}

/** Construye una config CamillaDSP mínima con nIn entradas y nOut salidas */
function buildDefaultConfig(nIn, nOut) {
    const mappings = Array.from({ length: Math.min(nIn, nOut) }, (_, i) => ({
        sources: [{ channel: i, gain: 0, inverted: false }],
        dest: i
    }));
    return {
        devices: {
            samplerate: 48000,
            chunksize: 1024,
            queuelimit: 4,
            capture: {
                type: 'Alsa', channels: nIn, format: 'S32LE', device: 'hw:0'
            },
            playback: {
                type: 'Alsa', channels: nOut, format: 'S32LE', device: 'hw:0'
            }
        },
        mixers: {
            GlobalMixer: {
                channels: { in: nIn, out: nOut },
                mapping: mappings
            }
        },
        filters: {},
        pipeline: [{ type: 'Mixer', name: 'GlobalMixer' }]
    };
}
