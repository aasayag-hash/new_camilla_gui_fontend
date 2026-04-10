// delayInput.js — Input de delay (ms) por canal, click derecho resetea a 0
import { getConfig, patchConfig } from '../../core/state.js';
import { t } from '../../core/i18n.js';

/**
 * Crea y devuelve el widget de delay para un canal del pipeline.
 * El delay vive en un paso de pipeline de tipo "Delay" asociado al canal.
 * @param {number} channel  - índice del canal
 * @param {string} target   - 'capture' | 'playback'
 */
export function makeDelayWidget(channel, target) {
    const wrap  = document.createElement('div');
    wrap.className = 'delay-wrap';

    const lbl = document.createElement('div');
    lbl.className = 'delay-label';
    lbl.textContent = t('dly_ms');
    wrap.appendChild(lbl);

    const input = document.createElement('input');
    input.type = 'number';
    input.className = 'delay-input';
    input.min   = '0';
    input.max   = '1000';
    input.step  = '0.1';
    input.value = _getDelay(channel, target);
    wrap.appendChild(input);

    input.addEventListener('change', async () => {
        const ms = parseFloat(input.value) || 0;
        await _setDelay(channel, target, ms);
    });

    input.addEventListener('contextmenu', async e => {
        e.preventDefault();
        input.value = '0';
        await _setDelay(channel, target, 0);
    });

    input.addEventListener('keydown', e => {
        if (e.key === 'Enter') input.blur();
    });

    return wrap;
}

function _getDelayStep(channel, target) {
    const cfg = getConfig();
    const pipeline = cfg?.pipeline || [];
    return pipeline.find(s =>
        s.type === 'Delay' &&
        (s.channel === channel || (Array.isArray(s.channels) && s.channels.includes(channel)))
    ) || null;
}

function _getDelay(channel, target) {
    const step = _getDelayStep(channel, target);
    if (!step) return '0';
    const ms = step.parameters?.delay_ms ?? step.parameters?.delay ?? 0;
    return String(ms);
}

async function _setDelay(channel, target, ms) {
    const cfg = getConfig();
    if (!cfg) return;
    const pipeline = cfg.pipeline || [];

    // Buscar paso Delay existente para este canal
    const idx = pipeline.findIndex(s =>
        s.type === 'Delay' &&
        (s.channel === channel || (Array.isArray(s.channels) && s.channels.includes(channel)))
    );

    let newPipeline;
    if (ms === 0) {
        // Eliminar el paso delay si existe
        newPipeline = pipeline.filter((_, i) => i !== idx);
    } else if (idx >= 0) {
        // Actualizar
        newPipeline = pipeline.map((s, i) => i === idx
            ? { ...s, parameters: { ...s.parameters, delay_ms: ms } }
            : s
        );
    } else {
        // Crear nuevo paso Delay
        const delayStep = {
            type: 'Delay',
            channel,
            parameters: { delay_ms: ms, subsample: false }
        };
        // Insertar antes del primer paso de filtros
        const filterIdx = pipeline.findIndex(s => s.type === 'Filter');
        newPipeline = filterIdx >= 0
            ? [...pipeline.slice(0, filterIdx), delayStep, ...pipeline.slice(filterIdx)]
            : [...pipeline, delayStep];
    }

    await patchConfig({ pipeline: newPipeline });
}
