/**
 * vuTab.js — Orchestrator del tab VU meters.
 * Gestiona polling de /api/status, canales dinámicos, master fader, MUTE ALL.
 */
import { Events } from '../../core/events.js';
import { t }      from '../../core/i18n.js';
import * as API   from '../../core/api.js';
import {
    getConfig, patchConfig, getInLabels, getOutLabels,
    getVisibleIn, getVisibleOut, getMixer, getMixerNameFromState
} from '../../core/state.js';
import { GLOBAL_HEX_COLORS, getMixerName, clamp } from '../../core/utils.js';
import { VUCanvas }      from './vuCanvas.js';
import { Fader }         from './fader.js';
import { makePolarityBtn } from './polarity.js';
import { makeDelayWidget } from './delayInput.js';
import { initCompressorTable, createCompressor, deleteCompressor } from './compressorTable.js';

// ── Estado del tab ────────────────────────────────────────────────────────────
let _polling    = false;
let _pollTimer  = null;
let _vuMap      = new Map();  // 'in_0', 'out_0' → VUCanvas
let _faderMap   = new Map();  // 'out_0' → Fader
let _masterFader = null;
let _viewMode   = 'all';   // 'all' | 'in' | 'out'
let _allMuted   = false;

const POLL_MS = 50;

export function initVuTab() {
    _buildToolbar();
    _buildMasterSection();
    Events.on('config:updated', _rebuild);
    Events.on('channels:visibility', _rebuild);
    Events.on('lang:changed', _onLangChanged);
    _rebuild();
    startPolling();
}

export function startPolling() {
    if (_polling) return;
    _polling = true;
    _schedulePoll();
}

export function stopPolling() {
    _polling = false;
    if (_pollTimer) { clearTimeout(_pollTimer); _pollTimer = null; }
}

// ── Toolbar ───────────────────────────────────────────────────────────────────
function _buildToolbar() {
    const tb = document.getElementById('vu-toolbar');
    if (!tb) return;
    tb.innerHTML = '';

    const lbl = document.createElement('label');
    lbl.textContent = t('view_label');
    tb.appendChild(lbl);

    ['all', 'in', 'out'].forEach(mode => {
        const btn = document.createElement('button');
        btn.className = 'view-btn' + (mode === _viewMode ? ' active' : '');
        btn.id = `view-btn-${mode}`;
        btn.textContent = { all: t('view_all'), in: t('view_in'), out: t('view_out') }[mode];
        btn.addEventListener('click', () => {
            _viewMode = mode;
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            _rebuild();
        });
        tb.appendChild(btn);
    });

    const muteBtn = document.createElement('button');
    muteBtn.id = 'btn-mute-all';
    muteBtn.textContent = t('mute_all');
    muteBtn.addEventListener('click', _toggleMuteAll);
    tb.appendChild(muteBtn);
}

function _onLangChanged() { _buildToolbar(); _buildMasterSection(); }

// ── Master fader ──────────────────────────────────────────────────────────────
function _buildMasterSection() {
    const sec = document.getElementById('vu-master-section');
    if (!sec) return;
    sec.innerHTML = '';

    const lbl = document.createElement('div');
    lbl.id = 'vu-master-label';
    lbl.textContent = 'MASTER';
    sec.appendChild(lbl);

    const canvas = document.createElement('canvas');
    canvas.id = 'master-fader-canvas';
    sec.appendChild(canvas);

    const disp = document.createElement('div');
    disp.id = 'master-volume-display';
    disp.textContent = '0.0 dB';
    sec.appendChild(disp);

    _masterFader = new Fader(canvas, {
        width: 22, height: 100,
        initialDb: 0,
        onChange: async db => {
            disp.textContent = `${db >= 0 ? '+' : ''}${db.toFixed(1)} dB`;
            try { await API.setParam('volume', db); } catch {}
        },
        onReset: () => { disp.textContent = '0.0 dB'; }
    });
}

// ── Rebuild channels ──────────────────────────────────────────────────────────
function _rebuild() {
    const container = document.getElementById('vu-channels-container');
    if (!container) return;
    container.innerHTML = '';
    _vuMap.clear();
    _faderMap.clear();

    const cfg      = getConfig();
    const inLabels  = getInLabels();
    const outLabels = getOutLabels();
    const mixer     = getMixer();
    const visIn     = getVisibleIn();
    const visOut    = getVisibleOut();

    const showIn  = (_viewMode === 'all' || _viewMode === 'in');
    const showOut = (_viewMode === 'all' || _viewMode === 'out');

    // ── Canales de entrada ────────────────────────────────────────────────
    if (showIn) {
        inLabels.forEach((lbl, i) => {
            if (!visIn.has(i)) return;
            const col = _buildChannel(i, lbl, false, GLOBAL_HEX_COLORS[i % 32]);
            container.appendChild(col);
        });
    }

    // ── Canales de salida ─────────────────────────────────────────────────
    if (showOut) {
        outLabels.forEach((lbl, i) => {
            if (!visOut.has(i)) return;
            const isMuted = _isOutMuted(i, cfg);
            const col = _buildChannel(i, lbl, true, GLOBAL_HEX_COLORS[(i + 16) % 32], isMuted);
            container.appendChild(col);
        });
    }

    // Tabla de compresores
    const compSection = document.getElementById('comp-table-section');
    if (compSection) initCompressorTable(compSection);
}

function _buildChannel(index, label, isOutput, color, muted = false) {
    const col = document.createElement('div');
    col.className = 'vu-channel' + (muted ? ' muted' : '');
    col.dataset.target = isOutput ? 'out' : 'in';
    col.dataset.index  = index;

    // Nombre
    const nameEl = document.createElement('div');
    nameEl.className = 'vu-name' + (isOutput ? ' output' : '');
    nameEl.textContent = label;
    nameEl.style.color = color;
    col.appendChild(nameEl);

    // Mute al click en nombre (solo salidas)
    if (isOutput) {
        nameEl.addEventListener('click', e => { e.stopPropagation(); _toggleMuteChannel(index); });
    }

    // Canvas VU
    const vuCanvas = document.createElement('canvas');
    vuCanvas.className = 'vu-bar-canvas';
    col.appendChild(vuCanvas);
    const vu = new VUCanvas(vuCanvas, { isOutput, width: 28, height: 140 });
    vu.setMuted(muted);
    _vuMap.set(`${isOutput ? 'out' : 'in'}_${index}`, vu);

    // Peak label
    const peak = document.createElement('div');
    peak.className = 'vu-peak-label';
    peak.textContent = '-∞';
    col.dataset.peakEl = '';
    col.appendChild(peak);
    vu._peakLabelEl = peak;

    // Doble-click en canvas VU → crear compresor (solo salidas)
    if (isOutput) {
        vuCanvas.addEventListener('dblclick', async e => {
            const rect = vuCanvas.getBoundingClientRect();
            const y = e.clientY - rect.top;
            const h = rect.height;
            const db = -60 + (1 - y / h) * 72;
            await createCompressor(index, Math.round(db));
        });
        vuCanvas.addEventListener('contextmenu', async e => {
            e.preventDefault();
            await deleteCompressor(index);
        });
    }

    // Fader (solo salidas)
    if (isOutput) {
        const faderCanvas = document.createElement('canvas');
        faderCanvas.className = 'ch-fader-canvas';
        col.appendChild(faderCanvas);

        const gain = _getChannelGain(index);
        const fader = new Fader(faderCanvas, {
            width: 22, height: 100,
            initialDb: gain,
            onChange: async db => { await _setChannelGain(index, db); },
        });
        _faderMap.set(`out_${index}`, fader);

        // Polaridad
        col.appendChild(makePolarityBtn(index));
    }

    // Delay
    col.appendChild(makeDelayWidget(index, isOutput ? 'playback' : 'capture'));

    return col;
}

// ── Polling ───────────────────────────────────────────────────────────────────
function _schedulePoll() {
    if (!_polling) return;
    _pollTimer = setTimeout(async () => {
        try { await _poll(); } catch {}
        _schedulePoll();
    }, POLL_MS);
}

async function _poll() {
    const status = await API.getStatus();
    if (!status) return;

    const capLvls  = status.capture_levels  || status.capturelevels  || [];
    const pbLvls   = status.playback_levels || status.playbacklevels || [];
    const pbPeaks  = status.playback_peaks  || [];
    const capPeaks = status.capture_peaks   || [];

    // Actualizar VU de entradas
    capLvls.forEach((rmsDb, i) => {
        const vu = _vuMap.get(`in_${i}`);
        if (!vu) return;
        const peak = capPeaks[i] ?? rmsDb;
        vu.update(rmsDb, peak);
        if (vu._peakLabelEl) {
            vu._peakLabelEl.textContent = peak <= -60 ? '-∞' : `${peak.toFixed(1)}`;
        }
    });

    // Actualizar VU de salidas
    pbLvls.forEach((rmsDb, i) => {
        const vu = _vuMap.get(`out_${i}`);
        if (!vu) return;
        const peak = pbPeaks[i] ?? rmsDb;
        vu.update(rmsDb, peak);
        if (vu._peakLabelEl) {
            vu._peakLabelEl.textContent = peak <= -60 ? '-∞' : `${peak.toFixed(1)}`;
        }
    });
}

// ── Mute ──────────────────────────────────────────────────────────────────────
function _isOutMuted(outIndex, cfg) {
    const mixerName = getMixerName(cfg);
    if (!mixerName) return false;
    const mapping = cfg?.mixers?.[mixerName]?.mapping || [];
    const dest = mapping.find(m => m.dest === outIndex);
    if (!dest) return false;
    return (dest.sources || []).every(s => s.gain === null || s.gain <= -100);
}

async function _toggleMuteChannel(outIndex) {
    const cfg       = getConfig();
    const mixerName = getMixerName(cfg);
    if (!mixerName || !cfg?.mixers?.[mixerName]) return;

    const mixer   = cfg.mixers[mixerName];
    const mapping = (mixer.mapping || []).map(m => {
        if (m.dest !== outIndex) return m;
        const muted = (m.sources || []).every(s => s.gain <= -100);
        const sources = (m.sources || []).map(s => ({
            ...s,
            gain: muted ? 0 : -200
        }));
        return { ...m, sources };
    });
    await patchConfig({ mixers: { [mixerName]: { ...mixer, mapping } } });
}

async function _toggleMuteAll() {
    _allMuted = !_allMuted;
    const btn = document.getElementById('btn-mute-all');
    if (btn) btn.classList.toggle('muted', _allMuted);
    try {
        await API.setParam('mute', _allMuted);
    } catch {
        // Fallback: mutar todos los canales vía mixer
        const cfg = getConfig();
        const mixerName = getMixerName(cfg);
        if (!mixerName || !cfg?.mixers?.[mixerName]) return;
        const mixer = cfg.mixers[mixerName];
        const mapping = (mixer.mapping || []).map(m => ({
            ...m,
            sources: (m.sources || []).map(s => ({ ...s, gain: _allMuted ? -200 : 0 }))
        }));
        await patchConfig({ mixers: { [mixerName]: { ...mixer, mapping } } });
    }
}

// ── Gain por canal ────────────────────────────────────────────────────────────
function _getChannelGain(outIndex) {
    const cfg = getConfig();
    const mixerName = getMixerName(cfg);
    if (!mixerName) return 0;
    const mapping = cfg?.mixers?.[mixerName]?.mapping || [];
    const dest = mapping.find(m => m.dest === outIndex);
    return dest?.sources?.[0]?.gain ?? 0;
}

async function _setChannelGain(outIndex, db) {
    const cfg = getConfig();
    const mixerName = getMixerName(cfg);
    if (!mixerName || !cfg?.mixers?.[mixerName]) return;
    const mixer = cfg.mixers[mixerName];
    const mapping = (mixer.mapping || []).map(m => {
        if (m.dest !== outIndex) return m;
        const sources = (m.sources || []).map((s, si) =>
            si === 0 ? { ...s, gain: db } : s
        );
        return { ...m, sources };
    });
    await patchConfig({ mixers: { [mixerName]: { ...mixer, mapping } } });
}
