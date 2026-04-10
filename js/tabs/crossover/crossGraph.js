/**
 * crossGraph.js — Canvas Crossover interactivo.
 * - Grid 20Hz-20kHz, -24/+12 dB
 * - Doble-click: crea filtro crossover LP o HP según posición
 * - Drag: mueve frecuencia
 * - Rueda: cambia orden (2,4,6,8...)
 * - Click derecho: elimina
 * Puerto JS de CrossoverGraph del Python.
 */
import { calcularMagnitudCrossover, logFreqs } from '../../dsp/crossover.js';
import { GLOBAL_HEX_COLORS, clamp, cleanName } from '../../core/utils.js';
import { Events } from '../../core/events.js';
import {
    getConfig, patchConfig, getInLabels, getOutLabels,
    getVisibleIn, getVisibleOut, getSampleRate, getFilters, getPipeline
} from '../../core/state.js';

const F_MIN   = 20, F_MAX = 20000;
const DB_MIN  = -30, DB_MAX = 12;
const FREQS   = logFreqs(F_MIN, F_MAX, 512);
const HIT_R   = 14;

const XO_FAMILIES = ['Butterworth', 'LinkwitzRiley'];
const XO_ORDERS   = [2, 4, 6, 8, 10, 12];

export class CrossGraph {
    constructor(canvas, tooltipEl) {
        this.canvas  = canvas;
        this.ctx     = canvas.getContext('2d');
        this.tooltip = tooltipEl;

        this._selected  = null;
        this._dragging  = false;
        this._dragStartX = 0;
        this._dragStartFreq = 0;
        this._moved = false;

        this._ro = new ResizeObserver(() => this._onResize());
        this._ro.observe(canvas.parentElement || canvas);

        canvas.addEventListener('dblclick',    this._onDblClick.bind(this));
        canvas.addEventListener('mousedown',   this._onMouseDown.bind(this));
        canvas.addEventListener('mousemove',   this._onMouseMove.bind(this));
        canvas.addEventListener('mouseup',     this._onMouseUp.bind(this));
        canvas.addEventListener('mouseleave',  () => { this._hideTooltip(); });
        canvas.addEventListener('wheel',       this._onWheel.bind(this), { passive: false });
        canvas.addEventListener('contextmenu', this._onRightClick.bind(this));

        Events.on('config:updated', () => this.draw());
        Events.on('channels:visibility', () => this.draw());
        this._onResize();
    }

    _onResize() {
        const p = this.canvas.parentElement;
        if (!p) return;
        this.canvas.width  = p.clientWidth  || 600;
        this.canvas.height = p.clientHeight || 300;
        this.draw();
    }

    _fToX(f) {
        const w = this.canvas.width;
        return (Math.log10(f) - Math.log10(F_MIN)) / (Math.log10(F_MAX) - Math.log10(F_MIN)) * (w - 60) + 30;
    }
    _xToF(x) {
        const w = this.canvas.width;
        const ratio = (x - 30) / (w - 60);
        return Math.pow(10, Math.log10(F_MIN) + ratio * (Math.log10(F_MAX) - Math.log10(F_MIN)));
    }
    _dbToY(db) {
        const h = this.canvas.height;
        return (1 - (db - DB_MIN) / (DB_MAX - DB_MIN)) * (h - 40) + 20;
    }

    draw() {
        const { ctx, canvas } = this;
        const w = canvas.width, h = canvas.height;
        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = '#080812';
        ctx.fillRect(0, 0, w, h);
        this._drawGrid(w, h);
        this._drawCurves(w, h);
        this._drawHandles(w, h);
    }

    _drawGrid(w, h) {
        const { ctx } = this;
        ctx.font = '9px Consolas,monospace';
        ctx.fillStyle = '#444';
        ctx.textAlign = 'center';

        [31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000].forEach(f => {
            const x = this._fToX(f);
            ctx.strokeStyle = '#1a1a2e'; ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(x, 20); ctx.lineTo(x, h - 20); ctx.stroke();
            ctx.fillText(f >= 1000 ? `${f/1000}k` : String(f), x, h - 5);
        });

        ctx.textAlign = 'right';
        for (let db = DB_MIN; db <= DB_MAX; db += 6) {
            const y = this._dbToY(db);
            ctx.strokeStyle = db === 0 ? '#334466' : '#151528';
            ctx.lineWidth   = db === 0 ? 1.5 : 1;
            ctx.beginPath(); ctx.moveTo(30, y); ctx.lineTo(w - 30, y); ctx.stroke();
            ctx.fillStyle = '#444';
            ctx.fillText(`${db >= 0 ? '+' : ''}${db}`, 28, y + 3);
        }
    }

    _drawCurves(w, h) {
        const { ctx } = this;
        const cfg = getConfig();
        if (!cfg) return;

        const pipeline = getPipeline();
        const filters  = getFilters();
        const sr       = getSampleRate();
        const visIn    = getVisibleIn();
        const visOut   = getVisibleOut();
        const inLabels = getInLabels();
        const outLabels= getOutLabels();

        // Filtrar solo pasos crossover por canal
        const chXO = new Map();
        pipeline.forEach(step => {
            if (step.type !== 'Filter') return;
            const fSpec = filters[step.name];
            if (!fSpec || fSpec.type !== 'Conv') {
                // Crossover se almacena como BiquadCombo o similares
            }
            if (!fSpec) return;
            if (!['BiquadCombo', 'DiffEq'].includes(fSpec.type)) {
                // Para crossover "tradicional" en CamillaDSP 2.x se usan BiquadCombo
                // Detectamos por la presencia de parameters.type = Lowpass/Highpass
                const p = fSpec.parameters || {};
                if (!['Lowpass','Highpass','LowPass','HighPass'].includes(p.type)) return;
            }
            const chs = Array.isArray(step.channels) ? step.channels
                      : step.channel !== undefined    ? [step.channel]
                      : [];
            const isOut = step.channel_type === 'playback';
            chs.forEach(ch => {
                const key = `${isOut ? 'out' : 'in'}_${ch}`;
                if (!chXO.has(key)) chXO.set(key, []);
                chXO.get(key).push({ step, fSpec });
            });
        });

        const draw = (labels, vis, prefix, colorOff) => {
            labels.forEach((_, i) => {
                if (!vis.has(i)) return;
                const key = `${prefix}_${i}`;
                const entries = chXO.get(key) || [];
                if (!entries.length) return;
                const mags = new Array(FREQS.length).fill(0);
                entries.forEach(({ fSpec }) => {
                    const p = fSpec.parameters || {};
                    const m = calcularMagnitudCrossover(
                        p.type, p.parameters?.type || 'Butterworth',
                        p.freq || p.parameters?.freq || 1000,
                        p.order || p.parameters?.order || 4,
                        sr, FREQS
                    );
                    m.forEach((v, idx) => { mags[idx] += v; });
                });
                const color = GLOBAL_HEX_COLORS[(i + colorOff) % 32];
                ctx.strokeStyle = color + 'cc';
                ctx.lineWidth = 2;
                ctx.beginPath();
                FREQS.forEach((f, idx) => {
                    const x = this._fToX(f);
                    const y = this._dbToY(clamp(mags[idx], DB_MIN, DB_MAX));
                    idx === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
                });
                ctx.stroke();
            });
        };

        draw(inLabels, visIn, 'in', 0);
        draw(outLabels, visOut, 'out', 16);
    }

    _drawHandles(w, h) {
        const { ctx } = this;
        const pipeline = getPipeline();
        const filters  = getFilters();

        pipeline.forEach((step, si) => {
            if (step.type !== 'Filter') return;
            const fSpec = filters[step.name];
            if (!fSpec) return;
            const p = fSpec.parameters || {};
            if (!['Lowpass','Highpass','LowPass','HighPass'].includes(p.type)) return;

            const f    = p.freq || 1000;
            const x    = this._fToX(f);
            const y    = this._dbToY(-3);  // -3dB point
            const isSel= this._selected?.pipelineIndex === si;
            const color= p.type.toLowerCase().includes('low') ? '#0096ff' : '#ff6464';

            ctx.beginPath();
            ctx.arc(x, y, isSel ? 9 : 7, 0, Math.PI * 2);
            ctx.fillStyle   = isSel ? '#fff' : color + 'aa';
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.fill(); ctx.stroke();

            // Etiqueta orden
            const ord = p.order || p.parameters?.order || 4;
            ctx.fillStyle = '#ccc';
            ctx.font = '9px Consolas,monospace';
            ctx.textAlign = 'center';
            ctx.fillText(`${p.type?.substring(0,2).toUpperCase()} ${f}Hz O${ord}`, x, y - 14);
        });
    }

    _hitTest(x, y) {
        const pipeline = getPipeline();
        const filters  = getFilters();
        let best = null, bestDist = HIT_R;
        pipeline.forEach((step, si) => {
            if (step.type !== 'Filter') return;
            const fSpec = filters[step.name];
            if (!fSpec) return;
            const p = fSpec.parameters || {};
            if (!['Lowpass','Highpass','LowPass','HighPass'].includes(p.type)) return;
            const fx = this._fToX(p.freq || 1000);
            const fy = this._dbToY(-3);
            const d  = Math.hypot(x - fx, y - fy);
            if (d < bestDist) { bestDist = d; best = { pipelineIndex: si, step, fSpec }; }
        });
        return best;
    }

    async _onDblClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        if (this._hitTest(x, y)) return;

        const freq = clamp(this._xToF(x), F_MIN, F_MAX);
        const visIn  = getVisibleIn();
        const visOut = getVisibleOut();
        // Izquierda → LP, derecha → HP relativo al centro
        const xoType = x < this.canvas.width / 2 ? 'Lowpass' : 'Highpass';
        await _createCrossover(freq, xoType, 4, visIn, visOut);
    }

    _onMouseDown(e) {
        if (e.button !== 0) return;
        const rect = this.canvas.getBoundingClientRect();
        const hit  = this._hitTest(e.clientX - rect.left, e.clientY - rect.top);
        if (hit) {
            e.preventDefault();
            this._selected = hit;
            this._dragging = true;
            this._moved    = false;
            this._dragStartX    = e.clientX - rect.left;
            this._dragStartFreq = hit.fSpec.parameters?.freq || 1000;
            this.canvas.classList.add('dragging');
        } else {
            this._selected = null;
        }
        this.draw();
    }

    _onMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x    = e.clientX - rect.left;

        if (this._dragging && this._selected) {
            const dx   = x - this._dragStartX;
            const freqRange = Math.log10(F_MAX) - Math.log10(F_MIN);
            const wUsable   = this.canvas.width - 60;
            const logDelta  = (dx / wUsable) * freqRange;
            const newFreq   = clamp(Math.pow(10, Math.log10(this._dragStartFreq) + logDelta), F_MIN, F_MAX);
            this._pendingFreq = Math.round(newFreq);
            if (Math.abs(dx) > 2) this._moved = true;
            this.draw();
            this._showTooltip(e.clientX, e.clientY, this._selected.step.name, this._pendingFreq);
            return;
        }

        const hit = this._hitTest(x, e.clientY - rect.top);
        if (hit) {
            const p = hit.fSpec.parameters || {};
            this._showTooltip(e.clientX, e.clientY, hit.step.name, p.freq, p.order);
        } else {
            this._hideTooltip();
        }
    }

    async _onMouseUp() {
        if (this._dragging && this._selected && this._moved && this._pendingFreq) {
            const f = this._selected.fSpec;
            await patchConfig({
                filters: {
                    [this._selected.step.name]: {
                        ...f,
                        parameters: { ...(f.parameters || {}), freq: this._pendingFreq }
                    }
                }
            });
        }
        this._dragging = false;
        this._moved    = false;
        this.canvas.classList.remove('dragging');
        this.draw();
    }

    async _onWheel(e) {
        e.preventDefault();
        const rect = this.canvas.getBoundingClientRect();
        const hit  = this._hitTest(e.clientX - rect.left, e.clientY - rect.top) || this._selected;
        if (!hit) return;
        const p        = hit.fSpec.parameters || {};
        const curOrder = p.order || 4;
        const orders   = XO_ORDERS;
        const ci       = orders.indexOf(curOrder);
        const ni       = clamp(ci + (e.deltaY > 0 ? -1 : 1), 0, orders.length - 1);
        const newOrder = orders[ni];
        await patchConfig({
            filters: {
                [hit.step.name]: {
                    ...hit.fSpec,
                    parameters: { ...(hit.fSpec.parameters || {}), order: newOrder }
                }
            }
        });
    }

    async _onRightClick(e) {
        e.preventDefault();
        const rect = this.canvas.getBoundingClientRect();
        const hit  = this._hitTest(e.clientX - rect.left, e.clientY - rect.top);
        if (!hit) return;
        await _deleteCrossover(hit.step.name, hit.pipelineIndex);
        this._selected = null;
        this.draw();
    }

    _showTooltip(cx, cy, name, freq, order) {
        if (!this.tooltip) return;
        this.tooltip.style.display = 'block';
        this.tooltip.style.left = `${cx + 10}px`;
        this.tooltip.style.top  = `${cy - 30}px`;
        this.tooltip.textContent = order
            ? `${name}  ${freq}Hz  Orden ${order}`
            : `${name}  ${freq}Hz`;
    }
    _hideTooltip() { if (this.tooltip) this.tooltip.style.display = 'none'; }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
async function _createCrossover(freq, xoType, order, visIn, visOut) {
    const cfg = getConfig();
    if (!cfg) return;

    const ts = Date.now();
    const newFilters = {};
    const newSteps   = [];

    visIn.forEach(ch => {
        const name = cleanName(`XO_in${ch}_${xoType.substring(0,2)}_${ts}`);
        newFilters[name] = {
            type: 'Biquad',
            parameters: { type: xoType, freq, order }
        };
        newSteps.push({ type: 'Filter', channel: ch, names: [name] });
    });

    visOut.forEach(ch => {
        const name = cleanName(`XO_out${ch}_${xoType.substring(0,2)}_${ts}`);
        newFilters[name] = {
            type: 'Biquad',
            parameters: { type: xoType, freq, order }
        };
        newSteps.push({ type: 'Filter', channel: ch, channel_type: 'playback', names: [name] });
    });

    await patchConfig({
        filters:  { ...(cfg.filters || {}), ...newFilters },
        pipeline: [...(cfg.pipeline || []), ...newSteps]
    });
}

async function _deleteCrossover(filterName, stepIndex) {
    const cfg = getConfig();
    if (!cfg) return;
    const pipeline = (cfg.pipeline || []).filter((_, i) => i !== stepIndex);
    const filters  = { ...(cfg.filters || {}) };
    delete filters[filterName];
    await patchConfig({ filters, pipeline });
}
