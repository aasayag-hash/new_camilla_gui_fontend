// tabManager.js — Gestión de tabs y visibilidad del channel panel
import { t, Events } from '../core/i18n.js';

const TABS = [
    { id: 'vu',    key: 'tab_vu',    panel: true  },
    { id: 'eq',    key: 'tab_eq',    panel: true  },
    { id: 'cross', key: 'tab_cross', panel: true  },
    { id: 'mixer', key: 'tab_mixer', panel: false },
];

let _activeTab = 'vu';
let _onTabChange = null;

export function initTabManager(onTabChange) {
    _onTabChange = onTabChange;
    const bar = document.getElementById('tab-bar');
    if (!bar) return;
    bar.innerHTML = '';

    TABS.forEach(tab => {
        const btn = document.createElement('button');
        btn.className = 'tab-btn';
        btn.id = `tab-btn-${tab.id}`;
        btn.dataset.tab = tab.id;
        btn.textContent = t(tab.key);
        btn.addEventListener('click', () => activateTab(tab.id));
        bar.appendChild(btn);
    });

    Events.on('lang:changed', () => {
        TABS.forEach(tab => {
            const btn = document.getElementById(`tab-btn-${tab.id}`);
            if (btn) btn.textContent = t(tab.key);
        });
    });

    activateTab(_activeTab);
}

export function activateTab(tabId) {
    _activeTab = tabId;
    const tab = TABS.find(t => t.id === tabId);
    if (!tab) return;

    // Activar/desactivar botones de tab
    TABS.forEach(t => {
        const btn = document.getElementById(`tab-btn-${t.id}`);
        if (btn) btn.classList.toggle('active', t.id === tabId);
    });

    // Mostrar/ocultar contenidos
    TABS.forEach(t => {
        const content = document.getElementById(`tab-${t.id}`);
        if (content) content.classList.toggle('active', t.id === tabId);
    });

    // Channel panel: visible solo en tabs que lo necesitan
    const panel = document.getElementById('channel-panel');
    if (panel) panel.classList.toggle('hidden', !tab.panel);

    if (_onTabChange) _onTabChange(tabId);
}

export function getActiveTab() { return _activeTab; }
