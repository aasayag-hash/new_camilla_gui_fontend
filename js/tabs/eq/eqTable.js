// eqTable.js — Tabla editable de filtros EQ con combos tipo/canal
import { Events } from '../../core/events.js';
import { t } from '../../core/i18n.js';
import { getConfig, patchConfig, getInLabels, getOutLabels, getPipeline, getFilters } from '../../core/state.js';
import { GLOBAL_HEX_COLORS } from '../../core/utils.js';

const FILTER_TYPES = [
    'Peaking','Lowpass','Highpass','Notch','Allpass',
    'LowShelf','HighShelf','BandPass','Gain','Free'
];

export function initEqTable(container) {
    Events.on('config:updated', () => render(container));
    Events.on('lang:changed', () => render(container));
    render(container);
}

function render(container) {
    if (!container) return;
    container.innerHTML = '';

    const pipeline = getPipeline();
    const filters  = getFilters();
    const inLabels  = getInLabels();
    const outLabels = getOutLabels();

    // Recopilar filas: cada step Filter en el pipeline
    const rows = [];
    pipeline.forEach((step, si) => {
        if (step.type !== 'Filter') return;
        const names = step.names || (step.name ? [step.name] : []);
        names.forEach(name => {
            const fSpec = filters[name];
            if (!fSpec) return;
            rows.push({ stepIndex: si, step, filterName: name, fSpec });
        });
    });

    if (rows.length === 0) {
        const empty = document.createElement('div');
        empty.style.cssText = 'padding:8px;font-size:11px;color:var(--text-muted)';
        empty.textContent = 'Sin filtros. Doble-clic en el gráfico para crear.';
        container.appendChild(empty);
        return;
    }

    const table = document.createElement('table');
    table.className = 'filter-table';

    // Encabezado
    const thead = document.createElement('thead');
    const hrow  = document.createElement('tr');
    [t('filter_id'), t('filter_type'), t('filter_freq'), t('filter_gain'), t('filter_q'), t('filter_ch'), t('filter_del')].forEach(h => {
        const th = document.createElement('th');
        th.textContent = h;
        hrow.appendChild(th);
    });
    thead.appendChild(hrow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    rows.forEach(({ stepIndex, step, filterName, fSpec }) => {
        const p     = fSpec.parameters || {};
        const ch    = step.channel ?? (Array.isArray(step.channels) ? step.channels[0] : null);
        const isOut = step.channel_type === 'playback';
        const labels = isOut ? outLabels : inLabels;
        const colorIdx = (ch ?? 0) + (isOut ? 16 : 0);
        const color = GLOBAL_HEX_COLORS[colorIdx % 32];

        const row = document.createElement('tr');

        // ID con color
        const idTd = document.createElement('td');
        const swatch = document.createElement('span');
        swatch.className = 'filter-color-swatch';
        swatch.style.backgroundColor = color;
        idTd.appendChild(swatch);
        idTd.appendChild(document.createTextNode(filterName));
        row.appendChild(idTd);

        // Tipo
        const typeTd = document.createElement('td');
        const typeSel = document.createElement('select');
        FILTER_TYPES.forEach(ft => {
            const opt = document.createElement('option');
            opt.value = ft; opt.textContent = ft;
            if (ft === p.type) opt.selected = true;
            typeSel.appendChild(opt);
        });
        typeSel.addEventListener('change', async () => {
            await _updateFilter(filterName, fSpec, { type: typeSel.value });
        });
        typeTd.appendChild(typeSel);
        row.appendChild(typeTd);

        // Freq
        row.appendChild(makeNumInput(p.freq || 1000, 1, 24000, 1, async val => {
            await _updateFilter(filterName, fSpec, { freq: val });
        }));

        // Gain
        row.appendChild(makeNumInput(p.gain || 0, -30, 30, 0.1, async val => {
            await _updateFilter(filterName, fSpec, { gain: val });
        }));

        // Q
        row.appendChild(makeNumInput(p.q || 0.707, 0.1, 20, 0.01, async val => {
            await _updateFilter(filterName, fSpec, { q: val });
        }));

        // Canal
        const chTd  = document.createElement('td');
        const chSel = document.createElement('select');
        // Opciones: entradas + salidas
        inLabels.forEach((lbl, i) => {
            const opt = document.createElement('option');
            opt.value = `in_${i}`; opt.textContent = `IN ${i}: ${lbl}`;
            if (!isOut && ch === i) opt.selected = true;
            chSel.appendChild(opt);
        });
        outLabels.forEach((lbl, i) => {
            const opt = document.createElement('option');
            opt.value = `out_${i}`; opt.textContent = `OUT ${i}: ${lbl}`;
            if (isOut && ch === i) opt.selected = true;
            chSel.appendChild(opt);
        });
        chSel.addEventListener('change', async () => {
            const [tgt, idx] = chSel.value.split('_');
            await _moveFilterChannel(stepIndex, parseInt(idx), tgt === 'out');
        });
        chTd.appendChild(chSel);
        row.appendChild(chTd);

        // Borrar
        const delTd  = document.createElement('td');
        const delBtn = document.createElement('button');
        delBtn.className = 'filter-del-btn';
        delBtn.textContent = t('filter_del');
        delBtn.addEventListener('click', async () => {
            await _deleteFilter(filterName, stepIndex);
        });
        delTd.appendChild(delBtn);
        row.appendChild(delTd);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}

function makeNumInput(val, min, max, step, onChange) {
    const td  = document.createElement('td');
    const inp = document.createElement('input');
    inp.type  = 'number';
    inp.value = val;
    inp.min   = String(min);
    inp.max   = String(max);
    inp.step  = String(step);
    inp.addEventListener('change', () => {
        const v = parseFloat(inp.value);
        if (!isNaN(v)) onChange(v);
    });
    inp.addEventListener('keydown', e => { if (e.key === 'Enter') inp.blur(); });
    td.appendChild(inp);
    return td;
}

async function _updateFilter(filterName, fSpec, paramPatch) {
    await patchConfig({
        filters: {
            [filterName]: {
                ...fSpec,
                parameters: { ...(fSpec.parameters || {}), ...paramPatch }
            }
        }
    });
}

async function _deleteFilter(filterName, stepIndex) {
    const cfg = getConfig();
    const pipeline = (cfg.pipeline || []).filter((_, i) => i !== stepIndex);
    const filters  = { ...(cfg.filters || {}) };
    delete filters[filterName];
    await patchConfig({ filters, pipeline });
}

async function _moveFilterChannel(stepIndex, newChannel, isOut) {
    const cfg      = getConfig();
    const pipeline = (cfg.pipeline || []).map((s, i) => {
        if (i !== stepIndex) return s;
        return {
            ...s,
            channel: newChannel,
            channel_type: isOut ? 'playback' : 'capture'
        };
    });
    await patchConfig({ pipeline });
}
