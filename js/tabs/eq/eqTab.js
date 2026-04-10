// eqTab.js — Orchestrator del tab EQ
import { EQGraph }    from './eqGraph.js';
import { initEqTable } from './eqTable.js';

let _graph = null;

export function initEqTab() {
    const canvas  = document.getElementById('eq-canvas');
    const tooltip = document.getElementById('eq-tooltip');
    const tableWrap = document.getElementById('eq-table-wrap');

    if (canvas) {
        _graph = new EQGraph(canvas, tooltip);
    }

    if (tableWrap) {
        initEqTable(tableWrap);
    }
}

export function redrawEq() {
    _graph?.draw();
}
