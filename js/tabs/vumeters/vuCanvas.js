/**
 * vuCanvas.js — Canvas VU meter individual con:
 *   - Barra gradiente verde/amarillo/rojo
 *   - Peak hold: 40 frames hold + decaimiento 0.5 dB/frame
 *   - GR bar (gain reduction) para compresores
 *   - Threshold line
 * Puerto JS exacto de ProVUMeter del Python.
 */

const DB_MIN   = -60;
const DB_MAX   =  12;
const DB_RANGE = DB_MAX - DB_MIN;

// Peak hold
const PEAK_HOLD_FRAMES = 40;
const PEAK_DECAY_DB    = 0.5;

// GR smoothing — iguales al Python
const GR_ATK = 0.4;
const GR_REL = 0.05;

export class VUCanvas {
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {object} opts
     * @param {boolean} opts.isOutput   - true para canales de salida
     * @param {number}  opts.width
     * @param {number}  opts.height
     */
    constructor(canvas, opts = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.isOutput = opts.isOutput ?? false;
        this.resize(opts.width || 28, opts.height || 160);

        this._rms  = DB_MIN;
        this._peak = DB_MIN;
        this._peakHold  = DB_MIN;
        this._peakTimer = 0;
        this._grSmooth  = 0;       // dB de GR suavizado
        this._threshold = null;    // threshold del compresor (dB) o null
        this._muted = false;

        this._grad = null;
        this._buildGradient();
    }

    resize(w, h) {
        this.canvas.width  = w;
        this.canvas.height = h;
        this.w = w;
        this.h = h;
        this._grad = null;  // reconstruir gradient
    }

    setMuted(m) { this._muted = m; this.draw(); }

    setThreshold(dbOrNull) { this._threshold = dbOrNull; }

    /** Actualizar con nuevos datos del API /api/status */
    update(rmsDb, peakDb, grDb = 0) {
        if (this._muted) {
            this._rms = DB_MIN;
            this._peak = DB_MIN;
            grDb = 0;
        } else {
            this._rms  = Math.max(DB_MIN, Math.min(DB_MAX, rmsDb));
            this._peak = Math.max(DB_MIN, Math.min(DB_MAX, peakDb));
        }

        // Peak hold
        if (this._peak > this._peakHold) {
            this._peakHold  = this._peak;
            this._peakTimer = PEAK_HOLD_FRAMES;
        } else if (this._peakTimer > 0) {
            this._peakTimer--;
        } else {
            this._peakHold -= PEAK_DECAY_DB;
            if (this._peakHold < DB_MIN) this._peakHold = DB_MIN;
        }

        // GR smoothing
        if (grDb > this._grSmooth) {
            this._grSmooth += (grDb - this._grSmooth) * GR_ATK;
        } else {
            this._grSmooth += (grDb - this._grSmooth) * GR_REL;
        }

        this.draw();
    }

    draw() {
        const { ctx, w, h } = this;
        ctx.clearRect(0, 0, w, h);

        const grBarW = this.isOutput ? 5 : 0;
        const barW   = w - grBarW - 1;

        // ── Fondo ─────────────────────────────────────────────────────────
        ctx.fillStyle = '#0a0a12';
        ctx.fillRect(0, 0, barW, h);

        // ── Barra RMS ─────────────────────────────────────────────────────
        if (!this._grad) this._buildGradient(barW, h);
        const rmsY = this._dbToY(this._rms, h);
        ctx.fillStyle = this._muted ? '#333' : this._grad;
        ctx.fillRect(0, rmsY, barW, h - rmsY);

        // ── Peak hold line ────────────────────────────────────────────────
        if (this._peakHold > DB_MIN) {
            const py = this._dbToY(this._peakHold, h);
            ctx.fillStyle = this._peakColor(this._peakHold);
            ctx.fillRect(0, py, barW, 2);
        }

        // ── Threshold line ────────────────────────────────────────────────
        if (this._threshold !== null) {
            const ty = this._dbToY(this._threshold, h);
            ctx.strokeStyle = '#c800ff';
            ctx.lineWidth = 1;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(0, ty);
            ctx.lineTo(barW, ty);
            ctx.stroke();
            ctx.setLineDash([]);
        }

        // ── GR bar (salidas) ──────────────────────────────────────────────
        if (this.isOutput && grBarW > 0) {
            const grX = barW + 1;
            ctx.fillStyle = '#111';
            ctx.fillRect(grX, 0, grBarW, h);
            if (this._grSmooth > 0.1) {
                const grH = (this._grSmooth / DB_RANGE) * h;
                ctx.fillStyle = '#7c4dff';
                ctx.fillRect(grX, 0, grBarW, Math.min(grH, h));
            }
        }

        // ── Escala dB (marcas cada 6 dB) ─────────────────────────────────
        ctx.fillStyle = '#334';
        ctx.font = '7px Consolas, monospace';
        ctx.textAlign = 'right';
        for (let db = DB_MAX; db >= DB_MIN; db -= 6) {
            const y = this._dbToY(db, h);
            ctx.fillRect(barW - 3, y, 3, 1);
        }
    }

    _dbToY(db, h) {
        const ratio = (DB_MAX - db) / DB_RANGE;
        return Math.round(ratio * h);
    }

    _peakColor(db) {
        if (db >= 0)   return '#ff4444';
        if (db >= -6)  return '#ffc800';
        return '#00e676';
    }

    _buildGradient(w, h) {
        if (!w) { w = this.w; h = this.h; }
        const g = this.ctx.createLinearGradient(0, 0, 0, h);
        g.addColorStop(0,    '#ff4444');
        g.addColorStop(0.10, '#ff6d00');
        g.addColorStop(0.20, '#ffea00');
        g.addColorStop(0.45, '#00e676');
        g.addColorStop(1,    '#00604a');
        this._grad = g;
    }

    /** Devuelve el nivel de pico actual para mostrar en etiqueta */
    getPeakDb() { return this._peak; }
}
