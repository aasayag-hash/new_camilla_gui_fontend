/**
 * Matemáticas de filtros Crossover — puerto JS de calcular_magnitud_crossover() del Python.
 * Soporta Butterworth y LinkwitzRiley de distintos órdenes.
 */

import { logFreqs } from './biquad.js';

const TWO_PI = 2 * Math.PI;

/**
 * Butterworth de orden N (LP o HP) a una frecuencia de corte fc.
 * Retorna magnitud en dB para cada frecuencia en freqs.
 */
function butterworthMag(fc, order, type, freqs, sampleRate) {
    return freqs.map(f => {
        const ratio = f / fc;
        // Magnitud analógica Butterworth
        const mag2 = type === 'Lowpass'
            ? 1 / (1 + Math.pow(ratio, 2 * order))
            : 1 / (1 + Math.pow(1 / ratio, 2 * order));
        return 10 * Math.log10(Math.max(1e-20, mag2));
    });
}

/**
 * Linkwitz-Riley de orden N = 2*M (M = orden del Butterworth base).
 * Es un Butterworth de orden M al cuadrado → mag en dB = 2 * BW_M.
 */
function linkwitzRileyMag(fc, order, type, freqs, sampleRate) {
    const bwOrder = order / 2;
    return freqs.map(f => {
        const ratio = f / fc;
        const mag2bw = type === 'Lowpass'
            ? 1 / (1 + Math.pow(ratio, 2 * bwOrder))
            : 1 / (1 + Math.pow(1 / ratio, 2 * bwOrder));
        // LR = BW^2
        const mag2 = mag2bw * mag2bw;
        return 10 * Math.log10(Math.max(1e-20, mag2));
    });
}

/**
 * Calcula la magnitud (dB) de un filtro crossover.
 * @param {string} xoType  - 'Lowpass' | 'Highpass'
 * @param {string} family  - 'Butterworth' | 'LinkwitzRiley'
 * @param {number} freq    - frecuencia de corte Hz
 * @param {number} order   - orden del filtro (2,4,6,8...)
 * @param {number} sampleRate
 * @param {number[]} freqs
 * @returns {number[]} magnitudes en dB
 */
export function calcularMagnitudCrossover(xoType, family, freq, order, sampleRate, freqs) {
    const fc = Math.max(1, freq);
    if (family === 'LinkwitzRiley' || family === 'LR') {
        return linkwitzRileyMag(fc, order, xoType, freqs, sampleRate);
    }
    // Default: Butterworth
    return butterworthMag(fc, order, xoType, freqs, sampleRate);
}

/**
 * Respuesta combinada de varios filtros crossover (suma de dB).
 * Cada filtro: { type, freq, order, family }
 */
export function calcularCrossoverCombinado(filters, sampleRate, freqs) {
    const total = new Array(freqs.length).fill(0);
    for (const f of filters) {
        const mags = calcularMagnitudCrossover(
            f.type, f.parameters?.type || 'Butterworth',
            f.parameters?.freq || f.freq || 1000,
            f.parameters?.order || f.order || 4,
            sampleRate, freqs
        );
        for (let i = 0; i < total.length; i++) total[i] += mags[i];
    }
    return total;
}

export { logFreqs };
