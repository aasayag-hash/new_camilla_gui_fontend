// channelPanel.js — Panel lateral de canales IN/OUT con selección y bypass
import { Events } from '../core/events.js';
import { GLOBAL_HEX_COLORS } from '../core/utils.js';
import {
    getInLabels, getOutLabels, getVisibleIn, getVisibleOut,
    setVisibleIn, setVisibleOut, toggleBypass, isBypassed
} from '../core/state.js';
import { t } from '../core/i18n.js';

const panel = () => document.getElementById('channel-panel');

export function initChannelPanel() {
    Events.on('config:updated', render);
    Events.on('lang:changed', render);
    render();
}

function render() {
    const el = panel();
    if (!el) return;
    el.innerHTML = '';

    const inLabels  = getInLabels();
    const outLabels = getOutLabels();

    // ── Sección IN ──────────────────────────────────────────────────────
    if (inLabels.length > 0) {
        el.appendChild(makeSectionLabel('IN'));
        el.appendChild(makeAllBtn('in', inLabels));
        inLabels.forEach((lbl, i) => el.appendChild(makeChBtn('in', i, lbl, GLOBAL_HEX_COLORS[i % 32])));
        const sep = document.createElement('hr');
        sep.className = 'ch-separator';
        el.appendChild(sep);
    }

    // ── Sección OUT ─────────────────────────────────────────────────────
    if (outLabels.length > 0) {
        el.appendChild(makeSectionLabel('OUT'));
        el.appendChild(makeAllBtn('out', outLabels));
        outLabels.forEach((lbl, i) => el.appendChild(makeChBtn('out', i, lbl, GLOBAL_HEX_COLORS[(i + 16) % 32])));
    }
}

function makeSectionLabel(text) {
    const el = document.createElement('div');
    el.className = 'ch-section-label';
    el.textContent = text;
    return el;
}

function makeAllBtn(target, labels) {
    const btn = document.createElement('button');
    btn.className = 'ch-all-btn ch-btn';
    btn.textContent = target === 'in' ? t('all_in') : t('all_out');

    btn.addEventListener('click', () => {
        const vis = target === 'in' ? getVisibleIn() : getVisibleOut();
        const all = new Set(labels.map((_, i) => i));
        // toggle: si todos están activos, deseleccionar; si no, seleccionar todos
        const newSet = vis.size === labels.length ? new Set() : all;
        if (target === 'in') setVisibleIn(newSet);
        else setVisibleOut(newSet);
        render();
    });
    return btn;
}

function makeChBtn(target, index, label, color) {
    const btn = document.createElement('button');
    btn.className = 'ch-btn';
    const vis = target === 'in' ? getVisibleIn() : getVisibleOut();
    if (vis.has(index)) btn.classList.add('selected');
    if (isBypassed(target, index)) btn.classList.add('bypassed');
    btn.style.setProperty('--ch-color', color);
    btn.title = label;

    // Indicador de color
    const dot = document.createElement('span');
    dot.style.display = 'inline-block';
    dot.style.width = '7px';
    dot.style.height = '7px';
    dot.style.borderRadius = '50%';
    dot.style.backgroundColor = color;
    dot.style.marginRight = '5px';
    dot.style.flexShrink = '0';
    btn.appendChild(dot);
    btn.appendChild(document.createTextNode(label));

    // Click izquierdo: toggle visibilidad
    btn.addEventListener('click', e => {
        if (e.button !== 0) return;
        const vis = target === 'in' ? getVisibleIn() : getVisibleOut();
        const newSet = new Set(vis);
        if (newSet.has(index)) newSet.delete(index); else newSet.add(index);
        if (target === 'in') setVisibleIn(newSet);
        else setVisibleOut(newSet);
        render();
    });

    // Click derecho: toggle bypass EQ
    btn.addEventListener('contextmenu', e => {
        e.preventDefault();
        toggleBypass(target, index);
        render();
    });

    return btn;
}
