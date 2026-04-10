// Utilidades globales compartidas

export const GLOBAL_HEX_COLORS = [
    "#00ff96", "#0096ff", "#ff6464", "#ffc800", "#c800ff", "#00ffff", "#ffa500", "#ffffff",
    "#ff00ff", "#00ff00", "#ffff00", "#ff0000", "#0000ff", "#008080", "#800000", "#808000",
    "#800080", "#008000", "#ff7f50", "#7cfc00", "#6495ed", "#00ced1", "#ff1493", "#b0e0e6",
    "#dda0dd", "#fa8072", "#ffb6c1", "#2e8b57", "#da70d6", "#f0e68c", "#87cefa", "#98fb98"
];

export function cleanName(n) {
    return String(n).replace(/[^a-zA-Z0-9]/g, '');
}

export function clamp(val, min, max) {
    return Math.max(min, Math.min(max, val));
}

export function getMixerName(config_raw) {
    const pipeline = config_raw?.pipeline || [];
    const step = pipeline.find(s => s.type === 'Mixer');
    return step?.name || null;
}

export function getLabels(config_raw, target) {
    let numChannels = 0, lbls = [];
    if (target === 'playback') {
        const mixerName = getMixerName(config_raw);
        if (mixerName && config_raw.mixers?.[mixerName]) {
            const m = config_raw.mixers[mixerName];
            numChannels = m.channels?.out || 0;
            lbls = m.labels || [];
        }
    }
    if (numChannels === 0) {
        const dev = config_raw?.devices?.[target] || {};
        numChannels = dev.channels || 2;
        lbls = dev.labels || [];
    }
    const pref = target === 'capture' ? 'IN' : 'OUT';
    return Array.from({ length: numChannels }, (_, i) =>
        (lbls[i] && lbls[i] !== null) ? lbls[i] : `${pref} ${i}`
    );
}

export function getCHsFromStep(step) {
    if (Array.isArray(step.channels)) return step.channels;
    if (step.channel !== undefined) return [step.channel];
    return [];
}

export function deepMerge(target, source) {
    if (source === null) return null;
    if (typeof source !== 'object' || Array.isArray(source)) return source;
    const out = Object.assign({}, target);
    for (const key of Object.keys(source)) {
        if (source[key] === null) {
            out[key] = null;
        } else if (typeof source[key] === 'object' && !Array.isArray(source[key]) &&
                   typeof out[key] === 'object' && !Array.isArray(out[key]) && out[key] !== null) {
            out[key] = deepMerge(out[key], source[key]);
        } else {
            out[key] = source[key];
        }
    }
    return out;
}

export function range(n) {
    return Array.from({ length: n }, (_, i) => i);
}

export function downloadBlob(content, filename, mime = 'text/plain') {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}
