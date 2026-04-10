// cornerButtons.js — WEB, ImpCfg, ExpCfg, ImpEQ, ExpEQ, Reset, Log, Ayuda
import { t, Events } from '../core/i18n.js';
import * as API from '../core/api.js';
import { getConfig, setFullConfig, reloadConfig } from '../core/state.js';
import { downloadBlob } from '../core/utils.js';
import { showSnack } from './snack.js';

export function initCornerButtons() {
    _bindI18n();
    Events.on('lang:changed', _bindI18n);

    // ── WEB ────────────────────────────────────────────────────────────────
    document.getElementById('btn-web')?.addEventListener('click', () => {
        window.open(window.CAMILLA_BASE || 'http://localhost:5005', '_blank');
    });

    // ── Importar Config ────────────────────────────────────────────────────
    document.getElementById('btn-imp-cfg')?.addEventListener('click', () => {
        pickFile('.json,.yaml,.yml', async text => {
            try {
                let cfg;
                if (text.trimStart().startsWith('{')) {
                    cfg = JSON.parse(text);
                } else {
                    cfg = await API.ymlToJson(text);
                }
                await setFullConfig(cfg);
                showSnack(t('reset_success'), 'success');
            } catch (e) {
                showSnack(String(e), 'error');
            }
        });
    });

    // ── Exportar Config ────────────────────────────────────────────────────
    document.getElementById('btn-exp-cfg')?.addEventListener('click', async () => {
        try {
            const cfg = getConfig();
            if (!cfg) return;
            const yml = await API.configToYml(cfg);
            downloadBlob(yml, 'camilla_config.yaml', 'text/yaml');
        } catch (e) {
            showSnack(String(e), 'error');
        }
    });

    // ── Importar EQ (formato REW/APO) ─────────────────────────────────────
    document.getElementById('btn-imp-eq')?.addEventListener('click', () => {
        pickFile('.txt,.eq', async text => {
            try {
                // Pedir número de canales destino
                const chStr = prompt('Canales destino (ej: 0,1):') || '0';
                const result = await API.eqApoToJson(text, chStr);
                const patch = typeof result === 'string' ? JSON.parse(result) : result;
                const cfg = getConfig();
                if (!cfg) return;
                // Merge de filtros y pipeline
                const merged = {
                    ...cfg,
                    filters:  { ...(cfg.filters  || {}), ...(patch.filters  || {}) },
                    pipeline: [...(cfg.pipeline || []), ...(patch.pipeline || []).filter(
                        s => !cfg.pipeline?.find(p => p.name === s.name && p.type === s.type)
                    )]
                };
                await setFullConfig(merged);
                showSnack('EQ importado', 'success');
            } catch (e) {
                showSnack(String(e), 'error');
            }
        });
    });

    // ── Exportar EQ ────────────────────────────────────────────────────────
    document.getElementById('btn-exp-eq')?.addEventListener('click', () => {
        const cfg = getConfig();
        if (!cfg) return;
        const filters = cfg.filters || {};
        const lines = Object.entries(filters).map(([name, f]) => {
            const p = f.parameters || {};
            return `Filter: ON PK Fc ${p.freq ?? 1000} Hz Gain ${p.gain ?? 0} dB Q ${p.q ?? 0.707}`;
        });
        downloadBlob(lines.join('\n'), 'camilla_eq.txt', 'text/plain');
    });

    // ── Reset ──────────────────────────────────────────────────────────────
    document.getElementById('btn-reset-top')?.addEventListener('click', () => {
        showResetModal();
    });

    // ── Log ────────────────────────────────────────────────────────────────
    document.getElementById('btn-log')?.addEventListener('click', async () => {
        const modal = document.getElementById('modal-log');
        const output = document.getElementById('log-output');
        modal.classList.remove('hidden');
        try {
            output.value = await API.getLogFile();
            output.scrollTop = output.scrollHeight;
        } catch (e) {
            output.value = String(e);
        }
    });

    // ── Ayuda ──────────────────────────────────────────────────────────────
    document.getElementById('btn-help2')?.addEventListener('click', () => {
        const modal = document.getElementById('modal-help');
        document.getElementById('help-text').textContent = t('help_text');
        document.getElementById('modal-help-title').textContent = t('help_title');
        modal.classList.remove('hidden');
    });
}

function _bindI18n() {
    const map = {
        'btn-web':     'btn_web',
        'btn-imp-cfg': 'btn_imp_cfg',
        'btn-exp-cfg': 'btn_exp_cfg',
        'btn-imp-eq':  'btn_imp_eq',
        'btn-exp-eq':  'btn_exp_eq',
        'btn-reset-top':'btn_reset_top',
        'btn-log':     'btn_log',
        'btn-help2':   'btn_help2',
    };
    for (const [id, key] of Object.entries(map)) {
        const el = document.getElementById(id);
        if (el) el.textContent = t(key);
    }
}

function pickFile(accept, onText) {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = accept;
    input.addEventListener('change', async () => {
        const file = input.files?.[0];
        if (!file) return;
        const text = await file.text();
        onText(text);
    });
    input.click();
}

async function showResetModal() {
    const modal = document.getElementById('modal-reset');
    document.getElementById('modal-reset-title').textContent = t('reset_warn_title');
    document.getElementById('modal-reset-body').textContent  = t('reset_warn_body');
    document.getElementById('reset-in-label').textContent    = t('reset_in_label');
    document.getElementById('reset-out-label').textContent   = t('reset_out_label');
    document.getElementById('btn-reset-yes-label').textContent = t('yes');
    document.getElementById('btn-reset-no-label').textContent  = t('no');
    // Sugerir canales actuales de la config
    const cfg = getConfig();
    document.getElementById('reset-in-val').value  = cfg?.devices?.capture?.channels  || 2;
    document.getElementById('reset-out-val').value = cfg?.devices?.playback?.channels || 2;
    modal.classList.remove('hidden');

    const btnYes = document.getElementById('btn-reset-yes');
    const btnNo  = document.getElementById('btn-reset-no');

    const onYes = async () => {
        const nIn  = parseInt(document.getElementById('reset-in-val').value)  || 2;
        const nOut = parseInt(document.getElementById('reset-out-val').value) || 2;
        modal.classList.add('hidden');
        cleanup();
        try {
            const newCfg = buildDefaultConfig(nIn, nOut);
            await setFullConfig(newCfg);
            showSnack(`${t('reset_success')} ${nIn} ${t('reset_inputs')}, ${nOut} ${t('reset_outputs')}`, 'success');
        } catch (e) {
            showSnack(String(e), 'error');
        }
    };
    const onNo  = () => { modal.classList.add('hidden'); cleanup(); };
    const cleanup = () => {
        btnYes.removeEventListener('click', onYes);
        btnNo.removeEventListener('click', onNo);
    };
    btnYes.addEventListener('click', onYes);
    btnNo.addEventListener('click', onNo);
}

function buildDefaultConfig(nIn, nOut) {
    const mappings = Array.from({ length: Math.min(nIn, nOut) }, (_, i) => ({
        sources: [{ channel: i, gain: 0, inverted: false }],
        dest: i
    }));
    return {
        devices: {
            samplerate: 48000, chunksize: 1024, queuelimit: 4,
            capture:  { type: 'Alsa', channels: nIn,  format: 'S32LE', device: 'hw:0' },
            playback: { type: 'Alsa', channels: nOut, format: 'S32LE', device: 'hw:0' }
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
