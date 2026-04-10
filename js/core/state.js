// Estado global singleton — fuente de verdad única para la config CamillaDSP
import { deepMerge, getLabels, getMixerName, cleanName, range } from './utils.js';
import * as API from './api.js';
import { Events } from './events.js';

// ── Estado interno ────────────────────────────────────────────────────────────
let _config = null;          // config_raw completa del backend
let _inLabels  = [];         // etiquetas de canales de captura
let _outLabels = [];         // etiquetas de canales de reproducción
let _sampleRate = 48000;
let _visibleIn  = new Set(); // índices de canales IN visibles
let _visibleOut = new Set(); // índices de canales OUT visibles
let _bypassedIn  = new Set(); // canales IN con EQ bypass
let _bypassedOut = new Set(); // canales OUT con EQ bypass

// ── Getters ───────────────────────────────────────────────────────────────────
export function getConfig()     { return _config; }
export function getInLabels()   { return _inLabels; }
export function getOutLabels()  { return _outLabels; }
export function getSampleRate() { return _sampleRate; }
export function getVisibleIn()  { return _visibleIn; }
export function getVisibleOut() { return _visibleOut; }
export function getBypassedIn()  { return _bypassedIn; }
export function getBypassedOut() { return _bypassedOut; }

// ── Helpers internos ──────────────────────────────────────────────────────────

/** Reconstruye etiquetas y sampleRate desde config_raw */
function _parseConfig(cfg) {
    if (!cfg) return;
    _inLabels   = getLabels(cfg, 'capture');
    _outLabels  = getLabels(cfg, 'playback');
    _sampleRate = cfg?.devices?.samplerate || 48000;
    // Inicializar sets si están vacíos
    if (_visibleIn.size === 0)  _inLabels.forEach((_, i) => _visibleIn.add(i));
    if (_visibleOut.size === 0) _outLabels.forEach((_, i) => _visibleOut.add(i));
}

/**
 * Asegurar que existe un mixer global en la config.
 * Puerto JS de asegurar_mixer_global() del Python.
 */
function _ensureMixerGlobal(cfg) {
    if (!cfg) return cfg;
    const nIn  = cfg?.devices?.capture?.channels  || 2;
    const nOut = cfg?.devices?.playback?.channels || 2;

    // Buscar mixer existente en pipeline
    const pipeline = cfg.pipeline || [];
    let mixerStep = pipeline.find(s => s.type === 'Mixer');

    if (!mixerStep) {
        // Crear pipeline básico: Mixer → (existentes)
        const mixerName = 'GlobalMixer';
        mixerStep = { type: 'Mixer', name: mixerName };
        cfg = { ...cfg, pipeline: [mixerStep, ...pipeline.filter(s => s.type !== 'Mixer')] };
    }

    const mixerName = mixerStep.name;
    if (!cfg.mixers) cfg = { ...cfg, mixers: {} };
    if (!cfg.mixers[mixerName]) {
        // Crear mixer identidad nIn→nOut
        const mappings = range(Math.min(nIn, nOut)).map(i => ({
            sources: [{ channel: i, gain: 0, inverted: false }],
            dest: i
        }));
        cfg = {
            ...cfg,
            mixers: {
                ...cfg.mixers,
                [mixerName]: {
                    channels: { in: nIn, out: nOut },
                    mapping: mappings,
                    labels: range(nOut).map(i => `OUT ${i}`)
                }
            }
        };
    }
    return cfg;
}

// ── API pública ───────────────────────────────────────────────────────────────

/** Carga la config desde el backend y emite "config:updated" */
export async function reloadConfig() {
    try {
        let cfg = await API.getConfig();
        cfg = _ensureMixerGlobal(cfg);
        _config = cfg;
        _parseConfig(_config);
        Events.emit('config:updated', _config);
    } catch (e) {
        console.error('[state] reloadConfig error:', e);
        Events.emit('config:error', e);
    }
}

/**
 * Aplica un patch parcial al config_raw, lo envía al backend y emite "config:updated".
 * @param {object} patch - objeto parcial a deep-merge en config_raw
 */
export async function patchConfig(patch) {
    if (!_config) {
        console.warn('[state] patchConfig llamado sin config cargada');
        return;
    }
    const newCfg = deepMerge(_config, patch);
    try {
        await API.setConfig(newCfg);
        _config = newCfg;
        _parseConfig(_config);
        Events.emit('config:updated', _config);
    } catch (e) {
        console.error('[state] patchConfig error:', e);
        Events.emit('config:error', e);
        throw e;
    }
}

/**
 * Reemplaza config completa (sin merge), la envía y emite "config:updated".
 */
export async function setFullConfig(cfg) {
    try {
        await API.setConfig(cfg);
        _config = cfg;
        _parseConfig(_config);
        Events.emit('config:updated', _config);
    } catch (e) {
        console.error('[state] setFullConfig error:', e);
        Events.emit('config:error', e);
        throw e;
    }
}

/** Actualiza visibilidad de canales IN */
export function setVisibleIn(indexSet) {
    _visibleIn = new Set(indexSet);
    Events.emit('channels:visibility', { target: 'in', set: _visibleIn });
}

/** Actualiza visibilidad de canales OUT */
export function setVisibleOut(indexSet) {
    _visibleOut = new Set(indexSet);
    Events.emit('channels:visibility', { target: 'out', set: _visibleOut });
}

/** Toggle bypass EQ para un canal */
export function toggleBypass(target, index) {
    const set = target === 'in' ? _bypassedIn : _bypassedOut;
    if (set.has(index)) set.delete(index); else set.add(index);
    Events.emit('channels:bypass', { target, index, bypassed: set.has(index) });
}

/** Devuelve true si el canal tiene bypass */
export function isBypassed(target, index) {
    return (target === 'in' ? _bypassedIn : _bypassedOut).has(index);
}

// ── Helpers de config ─────────────────────────────────────────────────────────

/** Devuelve los filtros biquad del config como Map<filterId, filterObj> */
export function getFilters() {
    return _config?.filters || {};
}

/** Devuelve el pipeline como array */
export function getPipeline() {
    return _config?.pipeline || [];
}

/** Devuelve el mixer global o null */
export function getMixer() {
    const name = getMixerName(_config);
    if (!name) return null;
    return _config?.mixers?.[name] || null;
}

/** Devuelve el nombre del mixer global o null */
export function getMixerNameFromState() {
    return getMixerName(_config);
}

/**
 * Obtiene los pasos de pipeline de un canal (captura o reproducción).
 * target: 'capture' | 'playback', channel: number
 */
export function getPipelineStepsForChannel(target, channel) {
    const pipeline = getPipeline();
    return pipeline.filter(step => {
        if (step.type !== 'Filter') return false;
        if (target === 'capture' && step.channel !== undefined) return step.channel === channel;
        if (target === 'playback' && step.channel !== undefined) return step.channel === channel;
        if (Array.isArray(step.channels)) return step.channels.includes(channel);
        return false;
    });
}

/** Devuelve los compresores activos (pasos Compressor en pipeline) */
export function getCompressors() {
    return getPipeline().filter(s => s.type === 'Compressor');
}

/** Devuelve el volumen master actual (from setparam/volume) */
export function getMasterVolume() {
    return _config?.devices?.capture?.silence_threshold ?? 0;
}
