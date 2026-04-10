/**
 * mixerCanvas.js — Canvas matriz de routing Mixer.
 * - Headers de entradas (columnas) y salidas (filas)
 * - Click izquierdo en celda vacía '+': crea conexión
 * - Click derecho en celda verde: elimina conexión
 * - Doble-click en nombre: renombra entrada o salida
 * Puerto JS de MixerMatrixWidget del Python.
 */
import { Events } from '../../core/events.js';
import { t } from '../../core/i18n.js';
import {
    getConfig, patchConfig, getInLabels, getOutLabels, getMixer, getMixerNameFromState
} from '../../core/state.js';
import { GLOBAL_HEX_COLORS, clamp } from '../../core/utils.js';

const CELL_W = 52;
const CELL_H = 36;
const HDR_W  = 90;
const HDR_H  = 54;
const FONT   = '11px Consolas,monospace';
const FONT_SM= '9px Consolas,monospace';

export class MixerCanvas {
    constructor(canvas, tooltipEl) {
        this.canvas  = canvas;
        this.ctx     = canvas.getContext('2d');
        this.tooltip = tooltipEl;

        Events.on('config:updated', () => this._rebuild());
        Events.on('lang:changed',   () => this._rebuild());

        canvas.addEventListener('click',       this._onClick.bind(this));
        canvas.addEventListener('contextmenu', this._onRightClick.bind(this));
        canvas.addEventListener('dblclick',    this._onDblClick.bind(this));
        canvas.addEventListener('mousemove',   this._onMouseMove.bind(this));
        canvas.addEventListener('mouseleave',  () => this._hideTooltip());

        this._rebuild();
    }

    _rebuild() {
        const mixer = getMixer();
        if (!mixer) { this._drawEmpty(); return; }

        this._nIn  = mixer.channels?.in  || 2;
        this._nOut = mixer.channels?.out || 2;
        this._mapping = mixer.mapping || [];

        const inLabels  = getInLabels();
        const outLabels = getOutLabels();
        this._inLabels  = inLabels;
        this._outLabels = outLabels;

        // Ajustar tamaño canvas
        const w = HDR_W + this._nIn  * CELL_W + 20;
        const h = HDR_H + this._nOut * CELL_H + 20;
        this.canvas.width  = w;
        this.canvas.height = h;

        this.draw();
    }

    draw() {
        const { ctx, canvas } = this;
        if (!this._nIn) { this._drawEmpty(); return; }

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#08080f';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        this._drawHeaders();
        this._drawCells();
    }

    _drawEmpty() {
        const { ctx, canvas } = this;
        canvas.width = 300; canvas.height = 100;
        ctx.clearRect(0, 0, 300, 100);
        ctx.fillStyle = '#333';
        ctx.font = FONT;
        ctx.textAlign = 'center';
        ctx.fillText('Sin mixer configurado', 150, 55);
    }

    _drawHeaders() {
        const { ctx } = this;

        // Esquina
        ctx.fillStyle = '#111';
        ctx.fillRect(0, 0, HDR_W, HDR_H);

        // Entradas (columnas)
        for (let i = 0; i < this._nIn; i++) {
            const x = HDR_W + i * CELL_W;
            const color = GLOBAL_HEX_COLORS[i % 32];
            ctx.fillStyle = '#161622';
            ctx.fillRect(x, 0, CELL_W - 1, HDR_H - 1);
            ctx.strokeStyle = '#2a2a3a';
            ctx.strokeRect(x, 0, CELL_W, HDR_H);

            ctx.save();
            ctx.translate(x + CELL_W / 2, HDR_H - 6);
            ctx.rotate(-Math.PI / 4);
            ctx.fillStyle = color;
            ctx.font = FONT_SM;
            ctx.textAlign = 'left';
            const lbl = this._inLabels[i] || `IN ${i}`;
            ctx.fillText(lbl.length > 10 ? lbl.substring(0, 9) + '…' : lbl, 0, 0);
            ctx.restore();
        }

        // Salidas (filas)
        for (let o = 0; o < this._nOut; o++) {
            const y = HDR_H + o * CELL_H;
            const color = GLOBAL_HEX_COLORS[(o + 16) % 32];
            ctx.fillStyle = '#161622';
            ctx.fillRect(0, y, HDR_W - 1, CELL_H - 1);
            ctx.strokeStyle = '#2a2a3a';
            ctx.strokeRect(0, y, HDR_W, CELL_H);

            ctx.fillStyle = color;
            ctx.font = FONT;
            ctx.textAlign = 'right';
            const lbl = this._outLabels[o] || `OUT ${o}`;
            ctx.fillText(lbl.length > 12 ? lbl.substring(0, 11) + '…' : lbl, HDR_W - 6, y + CELL_H / 2 + 4);
        }
    }

    _drawCells() {
        const { ctx } = this;

        for (let o = 0; o < this._nOut; o++) {
            for (let i = 0; i < this._nIn; i++) {
                const x = HDR_W + i * CELL_W;
                const y = HDR_H + o * CELL_H;
                const conn = this._getConnection(i, o);

                if (conn) {
                    // Celda conectada
                    const gain = conn.gain ?? 0;
                    const alpha = clamp((gain + 60) / 60, 0.2, 1);
                    ctx.fillStyle = `rgba(0,200,100,${alpha * 0.6})`;
                    ctx.fillRect(x, y, CELL_W - 1, CELL_H - 1);
                    ctx.fillStyle = '#0f0';
                    ctx.font = FONT_SM;
                    ctx.textAlign = 'center';
                    ctx.fillText(gain === 0 ? '0dB' : `${gain > 0 ? '+' : ''}${gain.toFixed(1)}`, x + CELL_W / 2, y + CELL_H / 2 + 3);
                    ctx.strokeStyle = '#00cc6622';
                    ctx.strokeRect(x, y, CELL_W - 1, CELL_H - 1);
                } else {
                    // Celda vacía
                    ctx.fillStyle = '#0a0a14';
                    ctx.fillRect(x, y, CELL_W - 1, CELL_H - 1);
                    ctx.fillStyle = '#334';
                    ctx.font = '14px Consolas,monospace';
                    ctx.textAlign = 'center';
                    ctx.fillText('+', x + CELL_W / 2, y + CELL_H / 2 + 5);
                    ctx.strokeStyle = '#1a1a2a';
                    ctx.strokeRect(x, y, CELL_W - 1, CELL_H - 1);
                }
            }
        }
    }

    _getConnection(inCh, outCh) {
        const dest = this._mapping?.find(m => m.dest === outCh);
        if (!dest) return null;
        return (dest.sources || []).find(s => s.channel === inCh) || null;
    }

    _cellAt(x, y) {
        if (x < HDR_W || y < HDR_H) return null;
        const ci = Math.floor((x - HDR_W) / CELL_W);
        const ri = Math.floor((y - HDR_H) / CELL_H);
        if (ci < 0 || ci >= this._nIn  || ri < 0 || ri >= this._nOut) return null;
        return { inCh: ci, outCh: ri };
    }

    _headerAt(x, y) {
        if (y < HDR_H && x >= HDR_W) {
            const ci = Math.floor((x - HDR_W) / CELL_W);
            return ci < this._nIn ? { type: 'in', index: ci } : null;
        }
        if (x < HDR_W && y >= HDR_H) {
            const ri = Math.floor((y - HDR_H) / CELL_H);
            return ri < this._nOut ? { type: 'out', index: ri } : null;
        }
        return null;
    }

    async _onClick(e) {
        if (e.button !== 0) return;
        const rect = this.canvas.getBoundingClientRect();
        const cell = this._cellAt(e.clientX - rect.left, e.clientY - rect.top);
        if (!cell) return;

        const conn = this._getConnection(cell.inCh, cell.outCh);
        if (!conn) {
            await this._addConnection(cell.inCh, cell.outCh, 0);
        }
        // Click en celda conectada → no hacer nada (se borra con derecho)
    }

    async _onRightClick(e) {
        e.preventDefault();
        const rect = this.canvas.getBoundingClientRect();
        const cell = this._cellAt(e.clientX - rect.left, e.clientY - rect.top);
        if (!cell) return;
        await this._removeConnection(cell.inCh, cell.outCh);
    }

    async _onDblClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const hdr  = this._headerAt(e.clientX - rect.left, e.clientY - rect.top);
        if (!hdr) return;

        const current = hdr.type === 'in'
            ? (this._inLabels[hdr.index] || `IN ${hdr.index}`)
            : (this._outLabels[hdr.index] || `OUT ${hdr.index}`);

        const newName = prompt(t('rename_label'), current);
        if (!newName || newName === current) return;
        await this._renameChannel(hdr.type, hdr.index, newName);
    }

    _onMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const cell = this._cellAt(x, y);
        if (cell) {
            const conn = this._getConnection(cell.inCh, cell.outCh);
            const inLbl  = this._inLabels[cell.inCh]  || `IN ${cell.inCh}`;
            const outLbl = this._outLabels[cell.outCh] || `OUT ${cell.outCh}`;
            const msg = conn
                ? `${inLbl} → ${outLbl}  ${conn.gain ?? 0}dB  (Derecho: eliminar)`
                : `${inLbl} → ${outLbl}  (Clic: crear)`;
            this._showTooltip(e.clientX, e.clientY, msg);
        } else {
            this._hideTooltip();
        }
    }

    async _addConnection(inCh, outCh, gain = 0) {
        const cfg = getConfig();
        const mixerName = getMixerNameFromState();
        if (!mixerName || !cfg?.mixers?.[mixerName]) return;

        const mixer = cfg.mixers[mixerName];
        const mapping = (mixer.mapping || []).map(m => {
            if (m.dest !== outCh) return m;
            const already = (m.sources || []).find(s => s.channel === inCh);
            if (already) return m;
            return { ...m, sources: [...(m.sources || []), { channel: inCh, gain, inverted: false }] };
        });

        // Si no hay entrada para este destino, crearla
        const hasDest = mapping.find(m => m.dest === outCh);
        const finalMapping = hasDest ? mapping : [
            ...mapping,
            { dest: outCh, sources: [{ channel: inCh, gain, inverted: false }] }
        ];

        await patchConfig({ mixers: { [mixerName]: { ...mixer, mapping: finalMapping } } });
    }

    async _removeConnection(inCh, outCh) {
        const cfg = getConfig();
        const mixerName = getMixerNameFromState();
        if (!mixerName || !cfg?.mixers?.[mixerName]) return;

        const mixer = cfg.mixers[mixerName];
        const mapping = (mixer.mapping || []).map(m => {
            if (m.dest !== outCh) return m;
            return { ...m, sources: (m.sources || []).filter(s => s.channel !== inCh) };
        });
        await patchConfig({ mixers: { [mixerName]: { ...mixer, mapping } } });
    }

    async _renameChannel(type, index, newName) {
        const cfg = getConfig();
        const mixerName = getMixerNameFromState();
        if (!mixerName || !cfg?.mixers?.[mixerName]) return;

        const mixer = cfg.mixers[mixerName];
        if (type === 'out') {
            const labels = [...(mixer.labels || Array.from({ length: this._nOut }, (_, i) => `OUT ${i}`))];
            labels[index] = newName;
            await patchConfig({ mixers: { [mixerName]: { ...mixer, labels } } });
        } else {
            // Para entradas: etiquetas en devices.capture.labels
            const devCap = cfg?.devices?.capture || {};
            const labels = [...(devCap.labels || Array.from({ length: this._nIn }, (_, i) => `IN ${i}`))];
            labels[index] = newName;
            await patchConfig({ devices: { ...cfg.devices, capture: { ...devCap, labels } } });
        }
    }

    _showTooltip(cx, cy, msg) {
        if (!this.tooltip) return;
        this.tooltip.style.display = 'block';
        this.tooltip.style.left = `${cx + 12}px`;
        this.tooltip.style.top  = `${cy - 32}px`;
        this.tooltip.textContent = msg;
    }
    _hideTooltip() { if (this.tooltip) this.tooltip.style.display = 'none'; }
}
