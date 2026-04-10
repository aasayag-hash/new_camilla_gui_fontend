// crossTab.js — Orchestrator del tab Crossover
import { CrossGraph }     from './crossGraph.js';
import { initCrossTable } from './crossTable.js';

let _graph = null;

export function initCrossTab() {
    const canvas  = document.getElementById('cross-canvas');
    const tooltip = document.getElementById('cross-tooltip');
    const tableWrap = document.getElementById('cross-table-wrap');

    if (canvas) {
        _graph = new CrossGraph(canvas, tooltip);
    }
    if (tableWrap) {
        initCrossTable(tableWrap);
    }
}

export function redrawCross() {
    _graph?.draw();
}
