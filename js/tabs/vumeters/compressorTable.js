// compressorTable.js — Tabla de compresores con botón AUTO (5s sampling)
import { t } from '../../core/i18n.js';
import { getConfig, patchConfig, getCompressors } from '../../core/state.js';
import { Events } from '../../core/events.js';
import * as API from '../../core/api.js';
import { clamp } from '../../core/utils.js';

export function initCompressorTable(container) {
    Events.on('config:updated', () => render(container));
    render(container);
}

function render(container) {
    if (!container) return;
    container.innerHTML = '';

    const h4 = document.createElement('h4');
    h4.textContent = 'COMPRESORES';
    container.appendChild(h4);

    const comps = getCompressors();
    if (comps.length === 0) {
        const none = document.createElement('div');
        none.style.cssText = 'font-size:10px;color:var(--text-muted);padding:4px';
        none.textContent = 'Sin compresores activos. Doble-clic en barra VU para crear.';
        container.appendChild(none);
        return;
    }

    const table = document.createElement('table');
    table.className = 'comp-table';

    // Encabezado
    const thead = document.createElement('thead');
    const hrow  = document.createElement('tr');
    const cols  = ['comp_id','comp_ch','comp_thr','comp_ratio','comp_atk','comp_rel','comp_makeup','comp_clip','comp_auto','comp_del'];
    const colLabels = [...cols.map(k => t(k)), ''];
    colLabels.forEach(lbl => {
        const th = document.createElement('th');
        th.textContent = lbl;
        hrow.appendChild(th);
    });
    thead.appendChild(hrow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    const cfg = getConfig();
    const pipeline = cfg?.pipeline || [];

    comps.forEach((comp, ci) => {
        const row = document.createElement('tr');
        const p   = comp.parameters || {};

        // ID
        row.appendChild(makeCell(comp.name || `comp_${ci}`));
        // Channel
        row.appendChild(makeCell(comp.channel ?? comp.channels ?? '?'));
        // Campos editables
        const fields = [
            { key: 'threshold', label: 'comp_thr',    step: 0.1 },
            { key: 'ratio',     label: 'comp_ratio',  step: 0.1 },
            { key: 'attack',    label: 'comp_atk',    step: 0.001 },
            { key: 'release',   label: 'comp_rel',    step: 0.001 },
            { key: 'makeup_gain',label:'comp_makeup', step: 0.1 },
            { key: 'clip_limit', label:'comp_clip',   step: 0.1 },
        ];
        fields.forEach(f => {
            const td  = document.createElement('td');
            const inp = document.createElement('input');
            inp.type  = 'number';
            inp.step  = String(f.step);
            inp.value = p[f.key] ?? '';
            inp.style.width = '60px';
            inp.style.fontSize = '10px';
            inp.addEventListener('change', async () => {
                const val = parseFloat(inp.value);
                if (isNaN(val)) return;
                await _updateCompressor(ci, f.key, val, pipeline, cfg);
            });
            td.appendChild(inp);
            row.appendChild(td);
        });

        // Auto
        const autoTd  = document.createElement('td');
        autoTd.className = 'comp-auto-col';
        const autoBtn = document.createElement('button');
        autoBtn.className = 'comp-auto-btn';
        autoBtn.textContent = t('comp_auto');
        let _autoRunning = false;
        autoBtn.addEventListener('click', async () => {
            if (_autoRunning) return;
            _autoRunning = true;
            autoBtn.classList.add('sampling');
            autoBtn.textContent = t('auto_sampling');
            try {
                const samples = [];
                for (let i = 0; i < 50; i++) {
                    const st = await API.getStatus();
                    const ch = comp.channel ?? 0;
                    const lvls = st?.playback_levels || st?.capture_levels || [];
                    if (lvls[ch] !== undefined) samples.push(lvls[ch]);
                    await new Promise(r => setTimeout(r, 100));
                }
                if (samples.length) {
                    const maxDb = Math.max(...samples);
                    const thr   = clamp(maxDb - 6, -40, 0);
                    await _updateCompressor(ci, 'threshold', thr, pipeline, cfg);
                }
            } finally {
                _autoRunning = false;
                autoBtn.classList.remove('sampling');
                autoBtn.textContent = t('comp_auto');
            }
        });
        autoTd.appendChild(autoBtn);
        row.appendChild(autoTd);

        // Eliminar
        const delTd  = document.createElement('td');
        const delBtn = document.createElement('button');
        delBtn.className = 'comp-del-btn';
        delBtn.textContent = t('comp_del');
        delBtn.addEventListener('click', async () => {
            const newPipeline = (getConfig()?.pipeline || []).filter((_, i) => {
                const comps2 = (getConfig()?.pipeline || []).filter(s => s.type === 'Compressor');
                return !(s.type === 'Compressor' && comps2.indexOf(s) === ci);
            });
            await patchConfig({ pipeline: newPipeline });
        });
        delTd.appendChild(delBtn);
        row.appendChild(delTd);

        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    container.appendChild(table);
}

function makeCell(text) {
    const td = document.createElement('td');
    td.textContent = String(text);
    return td;
}

async function _updateCompressor(ci, key, val, pipeline, cfg) {
    const compSteps = pipeline.filter(s => s.type === 'Compressor');
    if (ci >= compSteps.length) return;
    const comp = compSteps[ci];
    const newPipeline = pipeline.map(s => {
        if (s !== comp) return s;
        return { ...s, parameters: { ...(s.parameters || {}), [key]: val } };
    });
    await patchConfig({ pipeline: newPipeline });
}

/**
 * Crea un compresor nuevo en el canal dado con threshold en el punto clickeado.
 */
export async function createCompressor(channel, thresholdDb) {
    const cfg = getConfig();
    const pipeline = cfg?.pipeline || [];

    const name = `Comp_ch${channel}_${Date.now()}`;
    const newComp = {
        type: 'Compressor',
        channel,
        name,
        parameters: {
            threshold:   thresholdDb,
            ratio:       4,
            attack:      0.01,
            release:     0.1,
            makeup_gain: 0,
            clip_limit:  1.0,
            enable_clip_limiting: false,
            monitor_channels: [channel],
            attack_damping:  0,
            release_damping: 0,
        }
    };
    await patchConfig({ pipeline: [...pipeline, newComp] });
}

/**
 * Elimina el compresor del canal dado.
 */
export async function deleteCompressor(channel) {
    const cfg = getConfig();
    const pipeline = cfg?.pipeline || [];
    const newPipeline = pipeline.filter(s =>
        !(s.type === 'Compressor' && (s.channel === channel || (Array.isArray(s.channels) && s.channels.includes(channel))))
    );
    await patchConfig({ pipeline: newPipeline });
}
