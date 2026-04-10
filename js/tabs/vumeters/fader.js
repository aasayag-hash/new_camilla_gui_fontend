/**
 * fader.js — Canvas fader vertical -30dB a +10dB.
 * Puerto JS de ProFader del Python.
 * Soporta modo "channel" (patch config) y "master" (setparam/volume).
 */
import { clamp } from '../../core/utils.js';

const DB_MIN  = -30;
const DB_MAX  =  10;
const DB_ZERO =   0;

export class Fader {
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {object} opts
     * @param {number}   opts.width
     * @param {number}   opts.height
     * @param {number}   opts.initialDb
     * @param {function} opts.onChange    - callback(db) cuando cambia
     * @param {function} opts.onReset     - callback al click derecho (reset a 0)
     */
    constructor(canvas, opts = {}) {
        this.canvas = canvas;
        this.ctx    = canvas.getContext('2d');
        this.w = opts.width  || 22;
        this.h = opts.height || 120;
        canvas.width  = this.w;
        canvas.height = this.h;

        this.db       = opts.initialDb ?? 0;
        this.onChange = opts.onChange || (() => {});
        this.onReset  = opts.onReset  || (() => {});

        this._dragging = false;
        this._dragStartY = 0;
        this._dragStartDb = 0;

        canvas.addEventListener('mousedown',    this._onMouseDown.bind(this));
        canvas.addEventListener('contextmenu',  e => { e.preventDefault(); this._doReset(); });
        canvas.addEventListener('wheel',        this._onWheel.bind(this), { passive: false });
        window.addEventListener('mousemove',    this._onMouseMove.bind(this));
        window.addEventListener('mouseup',      this._onMouseUp.bind(this));

        this.draw();
    }

    setDb(db) {
        this.db = clamp(db, DB_MIN, DB_MAX);
        this.draw();
    }

    draw() {
        const { ctx, w, h } = this;
        ctx.clearRect(0, 0, w, h);

        // Fondo pista
        ctx.fillStyle = '#111120';
        ctx.roundRect(w/2 - 3, 0, 6, h, 3);
        ctx.fill();

        // Marca de cero
        const zeroY = this._dbToY(DB_ZERO);
        ctx.strokeStyle = '#ffffff44';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(2, zeroY);
        ctx.lineTo(w - 2, zeroY);
        ctx.stroke();

        // Thumb
        const thumbY = this._dbToY(this.db);
        const thumbH = 14;
        const thumbW = w - 4;
        const color  = this.db > 0 ? '#ff9800' : '#00ff96';
        ctx.fillStyle = color;
        ctx.strokeStyle = '#fff8';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.roundRect(2, thumbY - thumbH / 2, thumbW, thumbH, 3);
        ctx.fill();
        ctx.stroke();

        // Valor dB
        ctx.fillStyle = '#aaa';
        ctx.font = '8px Consolas,monospace';
        ctx.textAlign = 'center';
        ctx.fillText(`${this.db >= 0 ? '+' : ''}${this.db.toFixed(1)}`, w / 2, h - 2);
    }

    _dbToY(db) {
        const ratio = 1 - (db - DB_MIN) / (DB_MAX - DB_MIN);
        return Math.round(ratio * (this.h - 10) + 5);
    }

    _yToDb(y) {
        const ratio = 1 - (y - 5) / (this.h - 10);
        return clamp(ratio * (DB_MAX - DB_MIN) + DB_MIN, DB_MIN, DB_MAX);
    }

    _onMouseDown(e) {
        if (e.button !== 0) return;
        e.preventDefault();
        this._dragging = true;
        this._dragStartY  = e.clientY;
        this._dragStartDb = this.db;
        this.canvas.style.cursor = 'ns-resize';
    }

    _onMouseMove(e) {
        if (!this._dragging) return;
        const dy = this._dragStartY - e.clientY;
        const dbPerPx = (DB_MAX - DB_MIN) / (this.h - 10);
        const newDb = clamp(this._dragStartDb + dy * dbPerPx, DB_MIN, DB_MAX);
        this.db = Math.round(newDb * 10) / 10;
        this.draw();
        this.onChange(this.db);
    }

    _onMouseUp() {
        if (!this._dragging) return;
        this._dragging = false;
        this.canvas.style.cursor = 'ns-resize';
    }

    _onWheel(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.5 : 0.5;
        this.db = clamp(Math.round((this.db + delta) * 10) / 10, DB_MIN, DB_MAX);
        this.draw();
        this.onChange(this.db);
    }

    _doReset() {
        this.db = 0;
        this.draw();
        this.onChange(0);
        this.onReset();
    }
}
