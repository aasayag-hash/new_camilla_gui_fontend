/**
 * eqGraph.js — Canvas EQ interactivo.
 * - Grid logarítmico 20Hz-20kHz, ±12dB
 * - Curvas de respuesta por canal (colores GLOBAL_HEX_COLORS)
 * - Doble-click: crea filtro Peaking
 * - Drag (click sostenido): mueve filtro (freq/gain)
 * - Rueda: ajusta Q
 * - Click derecho: elimina filtro
 * Puerto JS de EQGraph del Python.
 */
import { calcularMagnitudBiquad, logFreqs } from '../../dsp/biquad.js';
import { GLOBAL_HEX_COLORS, clamp, cleanName, range } from '../../core/utils.js';
import { Events } from '../../core/events.js';
import {
    getConfig, patchConfig, getInLabels, getOutLabels,
    getVisibleIn, getVisibleOut, getSampleRate, getFilters, getPipeline, isBypassed
} from '../../core/state.js';

const F_MIN = 20, F_MAX = 20000;
const DB_MIN = -18, DB_MAX = 18;
const FREQS = logFreqs(F_MIN, F_MAX, 512);
const HIT_RADIUS = 14;  // px para detección de click en filtro

export class EQGraph {
    constructor(canvas, tooltipEl) {
        this.canvas  = canvas;
        this.ctx     = canvas.getContext('2d');
        this.tooltip = tooltipEl;

        this._selectedFilter = null;  // { filterName, pipelineIndex }
        this._dragging = false;
        this._dragStartX = 0;
        this._dragStartY = 0;
        this._dragStartFreq = 0;
        this._dragStartGain = 0;
        this._moved = false;

        this._ro = new ResizeObserver(() => this._onResize());
        this._ro.observe(canvas.parentElement || canvas);

        canvas.addEventListener('dblclick',    this._onDblClick.bind(this));
        canvas.addEventListener('mousedown',   this._onMouseDown.bind(this));
        canvas.addEventListener('mousemove',   this._onMouseMove.bind(this));
        canvas.addEventListener('mouseup',     this._onMouseUp.bind(this));
        canvas.addEventListener('mouseleave',  this._onMouseLeave.bind(this));
        canvas.addEventListener('wheel',       this._onWheel.bind(this), { passive: false });
        canvas.addEventListener('contextmenu', this._onRightClick.bind(this));

        Events.on('config:updated', () => this.draw());
        Events.on('channels:visibility', () => this.draw());
        this._onResize();
    }

    _onResize() {
        const parent = this.canvas.parentElement;
        if (!parent) return;
        this.canvas.width  = parent.clientWidth  || 600;
        this.canvas.height = parent.clientHeight || 300;
        this.draw();
    }

    // ── Coordenadas ──────────────────────────────────────────────────────
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
    _yToDb(y) {
        const h = this.canvas.height;
        return DB_MIN + (1 - (y - 20) / (h - 40)) * (DB_MAX - DB_MIN);
    }

    // ── Draw ─────────────────────────────────────────────────────────────
    draw() {
        const { ctx, canvas } = this;
        const w = canvas.width, h = canvas.height;
        ctx.clearRect(0, 0, w, h);

        // Fondo
        ctx.fillStyle = '#080810';
        ctx.fillRect(0, 0, w, h);

        this._drawGrid(w, h);
        this._drawCurves(w, h);
        this._drawFilterHandles(w, h);
    }

    _drawGrid(w, h) {
        const { ctx } = this;
        ctx.strokeStyle = '#1a1a2e';
        ctx.lineWidth = 1;
        ctx.font = '9px Consolas,monospace';
        ctx.fillStyle = '#444';
        ctx.textAlign = 'center';

        // Frecuencias verticales
        [31, 63, 125, 250, 500, 1000, 2000, 4000, 8000, 16000].forEach(f => {
            const x = this._fToX(f);
            ctx.beginPath();
            ctx.moveTo(x, 20); ctx.lineTo(x, h - 20);
            ctx.stroke();
            ctx.fillText(f >= 1000 ? `${f/1000}k` : String(f), x, h - 5);
        });

        // dB horizontales
        ctx.textAlign = 'right';
        for (let db = DB_MIN; db <= DB_MAX; db += 6) {
            const y = this._dbToY(db);
            ctx.strokeStyle = db === 0 ? '#334466' : '#151528';
            ctx.lineWidth   = db === 0 ? 1.5 : 1;
            ctx.beginPath();
            ctx.moveTo(30, y); ctx.lineTo(w - 30, y);
            ctx.stroke();
            ctx.fillStyle = '#444';
            ctx.fillText(`${db >= 0 ? '+' : ''}${db}`, 28, y + 3);
        }
    }

    _drawCurves(w, h) {
        const { ctx } = this;
        const cfg = getConfig();
        if (!cfg) return;

        const pipeline   = getPipeline();
        const filters    = getFilters();
        const sampleRate = getSampleRate();
        const inLabels   = getInLabels();
        const outLabels  = getOutLabels();
        const visIn  = getVisibleIn();
        const visOut = getVisibleOut();

        // Agrupar steps de Filter por canal
        const channelFilters = new Map();  // 'in_0' → [filterSpec,...]

        pipeline.forEach(step => {
            if (step.type !== 'Filter') return;
            const channels = Array.isArray(step.channels) ? step.channels
                           : step.channel !== undefined    ? [step.channel]
                           : [];
            const target = step.channel_type || 'capture';
            channels.forEach(ch => {
                const key = `${target === 'playback' ? 'out' : 'in'}_${ch}`;
                if (!channelFilters.has(key)) channelFilters.set(key, []);
                const fName = step.name;
                const fSpec = filters[fName];
                if (fSpec) channelFilters.get(key).push({ stepName: fName, ...fSpec });
            });
        });

        // Dibujar curva por canal visible
        const drawForTarget = (labels, vis, prefix, colorOffset) => {
            labels.forEach((lbl, i) => {
                if (!vis.has(i)) return;
                if (isBypassed(prefix === 'in' ? 'in' : 'out', i)) return;
                const key = `${prefix}_${i}`;
                const chFilters = channelFilters.get(key) || [];
                if (chFilters.length === 0) return;

                // Suma de magnitudes
                const mags = new Array(FREQS.length).fill(0);
                chFilters.forEach(f => {
                    const p = f.parameters || {};
                    const m = calcularMagnitudBiquad(
                        p.type, p.freq || p.frequency || 1000,
                        p.gain || 0, p.q || p.bandwidth_or_slope || 0.707,
                        sampleRate, FREQS
                    );
                    m.forEach((v, idx) => { mags[idx] += v; });
                });

                const color = GLOBAL_HEX_COLORS[(i + colorOffset) % 32];
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

        drawForTarget(inLabels, visIn, 'in', 0);
        drawForTarget(outLabels, visOut, 'out', 16);
    }

    _drawFilterHandles(w, h) {
        const { ctx } = this;
        const cfg = getConfig();
        if (!cfg) return;

        const pipeline = getPipeline();
        const filters  = getFilters();

        pipeline.forEach((step, si) => {
            if (step.type !== 'Filter') return;
            const fSpec = filters[step.name];
            if (!fSpec) return;
            const p = fSpec.parameters || {};
            const f = p.freq || p.frequency || 1000;
            const g = p.gain || 0;

            const x = this._fToX(f);
            const y = this._dbToY(clamp(g, DB_MIN, DB_MAX));

            const isSelected = this._selectedFilter?.pipelineIndex === si;

            ctx.beginPath();
            ctx.arc(x, y, isSelected ? 8 : 6, 0, Math.PI * 2);
            ctx.fillStyle   = isSelected ? '#fff' : '#00ff96aa';
            ctx.strokeStyle = isSelected ? '#00ff96' : '#008855';
            ctx.lineWidth   = 2;
            ctx.fill();
            ctx.stroke();

            // Etiqueta
            ctx.fillStyle = '#ccc';
            ctx.font = '9px Consolas,monospace';
            ctx.textAlign = 'center';
            ctx.fillText(step.name || '', x, y - 12);
        });
    }

    // ── Detección de filtro bajo el cursor ───────────────────────────────
    _filterAtPos(x, y) {
        const pipeline = getPipeline();
        const filters  = getFilters();
        let bestDist = HIT_RADIUS, best = null;
        pipeline.forEach((step, si) => {
            if (step.type !== 'Filter') return;
            const fSpec = filters[step.name];
            if (!fSpec) return;
            const p = fSpec.parameters || {};
            const fx = this._fToX(p.freq || p.frequency || 1000);
            const fy = this._dbToY(clamp(p.gain || 0, DB_MIN, DB_MAX));
            const dist = Math.hypot(x - fx, y - fy);
            if (dist < bestDist) { bestDist = dist; best = { pipelineIndex: si, step }; }
        });
        return best;
    }

    // ── Eventos ──────────────────────────────────────────────────────────
    async _onDblClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Si hay un filtro cerca, no crear
        if (this._filterAtPos(x, y)) return;

        const freq = clamp(this._xToF(x), F_MIN, F_MAX);
        const gain = clamp(this._yToDb(y), DB_MIN, DB_MAX);

        const visIn  = getVisibleIn();
        const visOut = getVisibleOut();
        if (visIn.size === 0 && visOut.size === 0) return;

        await _createFilter(freq, Math.round(gain * 10) / 10, 0.707, visIn, visOut);
    }

    _onMouseDown(e) {
        if (e.button !== 0) return;
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const hit = this._filterAtPos(x, y);
        if (hit) {
            e.preventDefault();
            this._selectedFilter = hit;
            this._dragging = true;
            this._moved = false;
            this._dragStartX = x;
            this._dragStartY = y;
            const fSpec = getFilters()[hit.step.name];
            this._dragStartFreq = fSpec?.parameters?.freq || fSpec?.parameters?.frequency || 1000;
            this._dragStartGain = fSpec?.parameters?.gain || 0;
            this.canvas.classList.add('dragging');
        } else {
            this._selectedFilter = null;
        }
        this.draw();
    }

    _onMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (this._dragging && this._selectedFilter) {
            const dx = x - this._dragStartX;
            const dy = y - this._dragStartY;
            if (Math.abs(dx) > 2 || Math.abs(dy) > 2) this._moved = true;

            const freqRange = Math.log10(F_MAX) - Math.log10(F_MIN);
            const wUsable   = this.canvas.width - 60;
            const logDelta  = (dx / wUsable) * freqRange;
            const newFreq   = clamp(
                Math.pow(10, Math.log10(this._dragStartFreq) + logDelta),
                F_MIN, F_MAX
            );
            const dbRange   = DB_MAX - DB_MIN;
            const hUsable   = this.canvas.height - 40;
            const newGain   = clamp(
                this._dragStartGain - (dy / hUsable) * dbRange,
                DB_MIN, DB_MAX
            );
            this._pendingFreq = Math.round(newFreq);
            this._pendingGain = Math.round(newGain * 10) / 10;
            this.draw();
            this._showTooltip(e.clientX, e.clientY, this._selectedFilter.step.name,
                this._pendingFreq, this._pendingGain);
            return;
        }

        // Hover tooltip
        const hit = this._filterAtPos(x, y);
        if (hit) {
            const fSpec = getFilters()[hit.step.name];
            const p = fSpec?.parameters || {};
            this._showTooltip(e.clientX, e.clientY, hit.step.name,
                p.freq || 1000, p.gain || 0, p.q || 0.707);
        } else {
            this._hideTooltip();
        }
    }

    async _onMouseUp(e) {
        if (this._dragging && this._selectedFilter && this._moved) {
            const f = getFilters()[this._selectedFilter.step.name];
            if (f) {
                const newParams = {
                    ...f.parameters,
                    freq: this._pendingFreq ?? f.parameters.freq,
                    gain: this._pendingGain ?? f.parameters.gain
                };
                await patchConfig({ filters: { [this._selectedFilter.step.name]: { ...f, parameters: newParams } } });
            }
        }
        this._dragging = false;
        this._moved    = false;
        this.canvas.classList.remove('dragging');
        this.draw();
    }

    _onMouseLeave() {
        this._hideTooltip();
        if (this._dragging) { this._dragging = false; this.canvas.classList.remove('dragging'); }
    }

    async _onWheel(e) {
        e.preventDefault();
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const hit = this._filterAtPos(x, y) || this._selectedFilter;
        if (!hit) return;

        const fSpec = getFilters()[hit.step?.name || hit.step?.name];
        if (!fSpec) return;
        const p = fSpec.parameters || {};
        const delta = e.deltaY > 0 ? -0.05 : 0.05;
        const newQ = clamp((p.q || 0.707) + delta, 0.1, 20);
        await patchConfig({
            filters: {
                [hit.step.name]: { ...fSpec, parameters: { ...p, q: Math.round(newQ * 100) / 100 } }
            }
        });
    }

    async _onRightClick(e) {
        e.preventDefault();
        const rect = this.canvas.getBoundingClientRect();
        const hit = this._filterAtPos(e.clientX - rect.left, e.clientY - rect.top);
        if (!hit) return;
        await _deleteFilter(hit.step.name, hit.pipelineIndex);
        this._selectedFilter = null;
        this.draw();
    }

    _showTooltip(cx, cy, name, freq, gain, q) {
        if (!this.tooltip) return;
        this.tooltip.style.display = 'block';
        this.tooltip.style.left = `${cx + 10}px`;
        this.tooltip.style.top  = `${cy - 30}px`;
        this.tooltip.textContent = q != null
            ? `${name}  ${freq}Hz  ${gain >= 0 ? '+' : ''}${gain}dB  Q${q}`
            : `${name}  ${freq}Hz  ${gain >= 0 ? '+' : ''}${gain}dB`;
    }

    _hideTooltip() {
        if (this.tooltip) this.tooltip.style.display = 'none';
    }
}

// ── Helpers de creación/borrado ───────────────────────────────────────────────

async function _createFilter(freq, gain, q, visIn, visOut) {
    const cfg = getConfig();
    if (!cfg) return;

    const ts = Date.now();
    const newFilters = {};
    const newSteps   = [];

    visIn.forEach(ch => {
        const name = cleanName(`EQ_in${ch}_${ts}`);
        newFilters[name] = {
            type: 'Biquad',
            parameters: { type: 'Peaking', freq, gain, q }
        };
        newSteps.push({ type: 'Filter', channel: ch, names: [name] });
    });

    visOut.forEach(ch => {
        const name = cleanName(`EQ_out${ch}_${ts}`);
        newFilters[name] = {
            type: 'Biquad',
            parameters: { type: 'Peaking', freq, gain, q }
        };
        newSteps.push({ type: 'Filter', channel: ch, channel_type: 'playback', names: [name] });
    });

    const pipeline = [...(cfg.pipeline || []), ...newSteps];
    await patchConfig({ filters: { ...(cfg.filters || {}), ...newFilters }, pipeline });
}

async function _deleteFilter(filterName, pipelineIndex) {
    const cfg = getConfig();
    if (!cfg) return;

    const pipeline = (cfg.pipeline || []).filter((_, i) => i !== pipelineIndex);
    const filters  = { ...(cfg.filters || {}) };
    delete filters[filterName];
    await patchConfig({ filters, pipeline });
}
