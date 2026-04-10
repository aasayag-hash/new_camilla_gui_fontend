// mixerTab.js — Orchestrator del tab Mixer
import { MixerCanvas } from './mixerCanvas.js';

let _mixer = null;

export function initMixerTab() {
    const scroll  = document.getElementById('mixer-scroll');
    const tooltip = document.getElementById('mixer-tooltip');

    if (!scroll) return;

    const canvas = document.createElement('canvas');
    canvas.id = 'mixer-canvas';
    scroll.appendChild(canvas);

    _mixer = new MixerCanvas(canvas, tooltip);
}
