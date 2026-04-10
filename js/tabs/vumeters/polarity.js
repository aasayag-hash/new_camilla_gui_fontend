// polarity.js — Botón +/- para inversión de polaridad por canal
import { getConfig, patchConfig } from '../../core/state.js';
import { getMixerName } from '../../core/utils.js';

/**
 * Crea y devuelve un botón de polaridad para un canal de salida.
 * @param {number} outIndex - índice del canal de salida en el mixer
 */
export function makePolarityBtn(outIndex) {
    const btn = document.createElement('button');
    btn.className = 'polarity-btn';
    btn.title = 'Invertir polaridad';
    _updateBtn(btn, outIndex);

    btn.addEventListener('click', async () => {
        await _togglePolarity(outIndex);
        _updateBtn(btn, outIndex);
    });

    return btn;
}

function _isInverted(outIndex) {
    const cfg = getConfig();
    const mixerName = getMixerName(cfg);
    if (!mixerName) return false;
    const mapping = cfg?.mixers?.[mixerName]?.mapping || [];
    const dest = mapping.find(m => m.dest === outIndex);
    if (!dest || !dest.sources?.length) return false;
    return dest.sources[0].inverted === true;
}

function _updateBtn(btn, outIndex) {
    const inv = _isInverted(outIndex);
    btn.textContent = inv ? '−' : '+';
    btn.classList.toggle('inverted', inv);
    btn.title = inv ? 'Polaridad invertida (clic para restaurar)' : 'Polaridad normal (clic para invertir)';
}

async function _togglePolarity(outIndex) {
    const cfg = getConfig();
    const mixerName = getMixerName(cfg);
    if (!mixerName || !cfg?.mixers?.[mixerName]) return;

    const mixer = cfg.mixers[mixerName];
    const mapping = (mixer.mapping || []).map(m => {
        if (m.dest !== outIndex) return m;
        const sources = (m.sources || []).map((s, si) =>
            si === 0 ? { ...s, inverted: !s.inverted } : s
        );
        return { ...m, sources };
    });

    await patchConfig({
        mixers: {
            [mixerName]: { ...mixer, mapping }
        }
    });
}
