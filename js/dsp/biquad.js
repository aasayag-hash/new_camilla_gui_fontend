/**
 * Matemáticas de filtros Biquad — puerto JS exacto de calcular_magnitud_biquad() del Python.
 * Usado por eqGraph.js para dibujar curvas de respuesta frecuencial.
 */

const TWO_PI = 2 * Math.PI;

/**
 * Calcula la magnitud (dB) de un filtro biquad en un array de frecuencias.
 * @param {string} filterType  - tipo de filtro (Peaking, Highpass, Lowpass, etc.)
 * @param {number} freq        - frecuencia central/corte en Hz
 * @param {number} gain        - ganancia en dB (para Peaking/Shelf)
 * @param {number} q           - factor Q
 * @param {number} sampleRate  - tasa de muestreo en Hz
 * @param {Float64Array|number[]} freqs - array de frecuencias a evaluar
 * @returns {number[]} magnitudes en dB
 */
export function calcularMagnitudBiquad(filterType, freq, gain, q, sampleRate, freqs) {
    const fs = sampleRate;
    const f0 = Math.max(1, freq);
    const A  = Math.pow(10, gain / 40);   // sqrt(10^(dB/20))
    const w0 = TWO_PI * f0 / fs;
    const cosW = Math.cos(w0);
    const sinW = Math.sin(w0);
    const alpha = sinW / (2 * Math.max(0.001, q));

    let b0, b1, b2, a0, a1, a2;

    switch (filterType) {
        case 'Peaking':
        case 'Peaking EQ':
        case 'PeakingEQ':
            b0 =  1 + alpha * A;
            b1 = -2 * cosW;
            b2 =  1 - alpha * A;
            a0 =  1 + alpha / A;
            a1 = -2 * cosW;
            a2 =  1 - alpha / A;
            break;

        case 'Highpass':
        case 'HighPass':
        case 'HPF':
            b0 =  (1 + cosW) / 2;
            b1 = -(1 + cosW);
            b2 =  (1 + cosW) / 2;
            a0 =   1 + alpha;
            a1 =  -2 * cosW;
            a2 =   1 - alpha;
            break;

        case 'Lowpass':
        case 'LowPass':
        case 'LPF':
            b0 =  (1 - cosW) / 2;
            b1 =   1 - cosW;
            b2 =  (1 - cosW) / 2;
            a0 =   1 + alpha;
            a1 =  -2 * cosW;
            a2 =   1 - alpha;
            break;

        case 'Notch':
            b0 =  1;
            b1 = -2 * cosW;
            b2 =  1;
            a0 =  1 + alpha;
            a1 = -2 * cosW;
            a2 =  1 - alpha;
            break;

        case 'Allpass':
        case 'AllPass':
            b0 =  1 - alpha;
            b1 = -2 * cosW;
            b2 =  1 + alpha;
            a0 =  1 + alpha;
            a1 = -2 * cosW;
            a2 =  1 - alpha;
            break;

        case 'LowShelf':
        case 'Lowshelf':
        case 'LSF': {
            const sqrtA2alpha = 2 * Math.sqrt(A) * alpha;
            b0 =  A * ((A + 1) - (A - 1) * cosW + sqrtA2alpha);
            b1 =  2 * A * ((A - 1) - (A + 1) * cosW);
            b2 =  A * ((A + 1) - (A - 1) * cosW - sqrtA2alpha);
            a0 =       (A + 1) + (A - 1) * cosW + sqrtA2alpha;
            a1 = -2  * ((A - 1) + (A + 1) * cosW);
            a2 =       (A + 1) + (A - 1) * cosW - sqrtA2alpha;
            break;
        }

        case 'HighShelf':
        case 'Highshelf':
        case 'HSF': {
            const sqrtA2alpha = 2 * Math.sqrt(A) * alpha;
            b0 =  A * ((A + 1) + (A - 1) * cosW + sqrtA2alpha);
            b1 = -2 * A * ((A - 1) + (A + 1) * cosW);
            b2 =  A * ((A + 1) + (A - 1) * cosW - sqrtA2alpha);
            a0 =       (A + 1) - (A - 1) * cosW + sqrtA2alpha;
            a1 =  2  * ((A - 1) - (A + 1) * cosW);
            a2 =       (A + 1) - (A - 1) * cosW - sqrtA2alpha;
            break;
        }

        case 'BandPass':
        case 'Bandpass':
        case 'BPF':
            b0 =  sinW / 2;
            b1 =  0;
            b2 = -sinW / 2;
            a0 =  1 + alpha;
            a1 = -2 * cosW;
            a2 =  1 - alpha;
            break;

        case 'Free': {
            // Tipo libre: sin ganancia (plano)
            return freqs.map(() => 0);
        }

        case 'Gain': {
            // Ganancia pura (flat shift)
            return freqs.map(() => gain);
        }

        default:
            return freqs.map(() => 0);
    }

    // Normalizar por a0
    b0 /= a0; b1 /= a0; b2 /= a0;
    a1 /= a0; a2 /= a0;

    return Array.from(freqs).map(f => {
        const w = TWO_PI * f / fs;
        // H(e^jw) usando números complejos
        const cosw = Math.cos(w);
        const sinw = Math.sin(w);
        const cos2w = Math.cos(2 * w);
        const sin2w = Math.sin(2 * w);

        const numRe = b0 + b1 * cosw + b2 * cos2w;
        const numIm =      b1 * (-sinw) + b2 * (-sin2w);
        const denRe = 1  + a1 * cosw + a2 * cos2w;
        const denIm =      a1 * (-sinw) + a2 * (-sin2w);

        const numMag2 = numRe * numRe + numIm * numIm;
        const denMag2 = denRe * denRe + denIm * denIm;

        if (denMag2 < 1e-30) return 0;
        const mag = Math.sqrt(numMag2 / denMag2);
        return 20 * Math.log10(Math.max(1e-10, mag));
    });
}

/**
 * Calcula la respuesta combinada de múltiples filtros biquad.
 * @param {Array<{type,freq,gain,q}>} filters
 * @param {number} sampleRate
 * @param {number[]} freqs
 * @returns {number[]} suma de magnitudes en dB
 */
export function calcularMagnitudCombinada(filters, sampleRate, freqs) {
    const total = new Array(freqs.length).fill(0);
    for (const f of filters) {
        const mags = calcularMagnitudBiquad(
            f.type, f.freq || f.frequency || 1000,
            f.gain || 0, f.q || f.bandwidth_or_slope || 0.707,
            sampleRate, freqs
        );
        for (let i = 0; i < total.length; i++) total[i] += mags[i];
    }
    return total;
}

/**
 * Genera array logarítmico de frecuencias entre f1 y f2 con n puntos.
 */
export function logFreqs(f1 = 20, f2 = 20000, n = 512) {
    const out = new Array(n);
    const logF1 = Math.log10(f1);
    const logF2 = Math.log10(f2);
    for (let i = 0; i < n; i++) {
        out[i] = Math.pow(10, logF1 + (logF2 - logF1) * i / (n - 1));
    }
    return out;
}
