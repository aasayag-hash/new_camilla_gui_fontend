// crossTable.js — Tabla de filtros crossover
import { Events } from '../../core/events.js';
import { t } from '../../core/i18n.js';
import { getConfig, patchConfig, getInLabels, getOutLabels, getPipeline, getFilters } from '../../core/state.js';
import { GLOBAL_HEX_COLORS } from '../../core/utils.js';

const XO_TYPES   = ['Lowpass','Highpass'];
const XO_FAMILIES= ['Butterworth','LinkwitzRiley'];
const XO_ORDERS  = [2, 4, 6, 8, 10, 12];

export function initCrossTable(container) {
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

    const rows = [];
    pipeline.forEach((step, si) => {
        if (step.type !== 'Filter') return;
        const names = step.names || (step.name ? [step.name] : []);
        names.forEach(name => {
            const fSpec = filters[name];
            if (!fSpec) return;
            const p = fSpec.parameters || {};
            if (!['Lowpass','Highpass','LowPass','HighPass'].includes(p.type)) return;
            rows.push({ stepIndex: si, step, filterName: name, fSpec });
        });
    });

    if (rows.length === 0) {
        const empty = document.createElement('div');
        empty.style.cssText = 'padding:8px;font-size:11px;color:var(--text-muted)';
        empty.textContent = 'Sin crossovers. Doble-clic en el gráfico para crear.';
        container.appendChild(empty);
        return;
    }

    const table = document.createElement('table');
    table.className = 'cross-table';

    const thead = document.createElement('thead');
    const hrow  = document.createElement('tr');
    ['ID', 'Tipo', 'Familia', 'Freq (Hz)', t('cross_ord'), 'Canal', t('filter_del')].forEach(h => {
        const th = document.createElement('th'); th.textContent = h; hrow.appendChild(th);
    });
    thead.appendChild(hrow);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');

    rows.forEach(({ stepIndex, step, filterName, fSpec }) => {
        const p     = fSpec.parameters || {};
        const ch    = step.channel ?? (Array.isArray(step.channels) ? step.channels[0] : null);
        const isOut = step.channel_type === 'playback';
        const colorIdx = (ch ?? 0) + (isOut ? 16 : 0);
        const color = GLOBAL_HEX_COLORS[colorIdx % 32];

        const row = document.createElement('tr');

        // ID
        const idTd = document.createElement('td');
        const sw = document.createElement('span');
        sw.className = 'filter-color-swatch'; sw.style.backgroundColor = color;
        idTd.appendChild(sw);
        idTd.appendChild(document.createTextNode(filterName));
        row.appendChild(idTd);

        // Tipo LP/HP
        row.appendChild(makeSelectTd(XO_TYPES, p.type || 'Lowpass', async val => {
            await patchConfig({ filters: { [filterName]: { ...fSpec, parameters: { ...p, type: val } } } });
        }));

        // Familia
        const curFamily = p.parameters?.type || p.family || 'Butterworth';
        row.appendChild(makeSelectTd(XO_FAMILIES, curFamily, async val => {
            const innerParams = { ...(p.parameters || {}), type: val };
            await patchConfig({ filters: { [filterName]: { ...fSpec, parameters: { ...p, parameters: innerParams } } } });
        }));

        // Freq
        row.appendChild(makeNumTd(p.freq || 1000, 1, 24000, 1, async val => {
            await patchConfig({ filters: { [filterName]: { ...fSpec, parameters: { ...p, freq: val } } } });
        }));

        // Orden (con badge)
        const ordTd   = document.createElement('td');
        const ordBadge = document.createElement('span');
        ordBadge.className = 'cross-order-badge';
        ordBadge.textContent = String(p.order || 4);
        ordBadge.title = 'Rueda del mouse para cambiar orden';
        ordBadge.addEventListener('wheel', async e => {
            e.preventDefault();
            const orders = XO_ORDERS;
            const cur = orders.indexOf(p.order || 4);
            const ni  = Math.max(0, Math.min(orders.length - 1, cur + (e.deltaY > 0 ? -1 : 1)));
            const newOrder = orders[ni];
            ordBadge.textContent = String(newOrder);
            await patchConfig({ filters: { [filterName]: { ...fSpec, parameters: { ...p, order: newOrder } } } });
        }, { passive: false });
        ordTd.appendChild(ordBadge);
        row.appendChild(ordTd);

        // Canal
        const chTd  = document.createElement('td');
        const chSel = document.createElement('select');
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
        chSel.style.fontSize = '11px'; chSel.style.padding = '2px 4px';
        chSel.addEventListener('change', async () => {
            const [tgt, idx] = chSel.value.split('_');
            const pipeline2  = (getPipeline()).map((s, i) => {
                if (i !== stepIndex) return s;
                return { ...s, channel: parseInt(idx), channel_type: tgt === 'out' ? 'playback' : 'capture' };
            });
            await patchConfig({ pipeline: pipeline2 });
        });
        chTd.appendChild(chSel);
        row.appendChild(chTd);

        // Eliminar
        const delTd  = document.createElement('td');
        const delBtn = document.createElement('button');
        delBtn.className = 'cross-del-btn';
        delBtn.textContent = t('filter_del');
        delBtn.addEventListener('click', async () => {
            const pipeline2 = (getPipeline()).filter((_, i) => i !== stepIndex);
            const filters2  = { ...getConfig()?.filters };
            delete filters2[filterName];
            await patchConfig({ filters: filters2, pipeline: pipeline2 });
        });
        delTd.appendChild(delBtn);
        row.appendChild(delTd);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}

function makeSelectTd(opts, current, onChange) {
    const td  = document.createElement('td');
    const sel = document.createElement('select');
    sel.style.fontSize = '11px'; sel.style.padding = '2px 4px';
    opts.forEach(o => {
        const opt = document.createElement('option');
        opt.value = o; opt.textContent = o;
        if (o === current) opt.selected = true;
        sel.appendChild(opt);
    });
    sel.addEventListener('change', () => onChange(sel.value));
    td.appendChild(sel);
    return td;
}

function makeNumTd(val, min, max, step, onChange) {
    const td  = document.createElement('td');
    const inp = document.createElement('input');
    inp.type = 'number'; inp.value = val;
    inp.min = String(min); inp.max = String(max); inp.step = String(step);
    inp.style.width = '80px'; inp.style.fontSize = '11px';
    inp.addEventListener('change', () => { const v = parseFloat(inp.value); if (!isNaN(v)) onChange(v); });
    td.appendChild(inp);
    return td;
}
