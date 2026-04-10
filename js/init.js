/**
 * init.js — Entry point principal. Bootstrap de toda la aplicación.
 * Se carga como módulo ES desde index.html.
 */
import { initLogin }         from './ui/login.js';
import { initChannelPanel }  from './ui/channelPanel.js';
import { initTabManager }    from './ui/tabManager.js';
import { initCornerButtons } from './ui/cornerButtons.js';
import { initVuTab, startPolling, stopPolling } from './tabs/vumeters/vuTab.js';
import { initEqTab }         from './tabs/eq/eqTab.js';
import { initCrossTab }      from './tabs/crossover/crossTab.js';
import { initMixerTab }      from './tabs/mixer/mixerTab.js';
import { Events }            from './core/events.js';
import { t }                 from './core/i18n.js';
import * as API              from './core/api.js';
import { reloadConfig, setFullConfig } from './core/state.js';

const DEFAULT_IP = 'localhost';
const DEFAULT_PORT = '5005';

function autoConnect() {
    const base = `http://${DEFAULT_IP}:${DEFAULT_PORT}`;
    window.CAMILLA_BASE = base;
    
    document.getElementById('screen-login').style.display = 'none';
    document.getElementById('screen-app').style.display = 'flex';
    
    document.getElementById('app-title').textContent = t('title');
    
    API.getStatus()
        .then(() => reloadConfig())
        .then(() => {
            document.getElementById('login-status').textContent = `Conectado a ${base}`;
            document.getElementById('login-status').className = 'ok';
        })
        .catch(err => {
            console.error('Auto-connect error:', err);
            document.getElementById('login-status').textContent = `Error: No se pudo conectar a ${base}`;
            document.getElementById('login-status').className = 'error';
            document.getElementById('screen-login').style.display = 'flex';
            document.getElementById('screen-app').style.display = 'none';
        });
}

function showApp(ip, port) {
    document.getElementById('screen-login').style.display = 'none';
    document.getElementById('screen-app').style.display   = 'flex';

    const titleEl = document.getElementById('app-title');
    if (titleEl) titleEl.textContent = t('title') + ` — ${ip}:${port}`;
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
async function bootstrap() {
    initLogin((ip, port) => {
        showApp(ip, port);
    });

    // Intentar conexión automática primero
    autoConnect();

    // Modales
    document.querySelectorAll('.modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.closest('.modal-overlay')?.classList.add('hidden');
        });
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-overlay:not(.hidden)').forEach(m => {
                m.classList.add('hidden');
            });
        }
    });
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', e => {
            if (e.target === overlay) overlay.classList.add('hidden');
        });
    });

    initCornerButtons();
    initChannelPanel();

    initTabManager(tabId => {
        if (tabId === 'vu') {
            startPolling();
        } else {
            stopPolling();
        }
    });

    initVuTab();
    initEqTab();
    initCrossTab();
    initMixerTab();

    Events.on('lang:changed', () => {
        const app = document.getElementById('screen-app');
        if (app && app.style.display !== 'none') {
            const titleEl = document.getElementById('app-title');
            if (titleEl) titleEl.textContent = t('title');
        }
        const loginTitle = document.getElementById('login-title');
        if (loginTitle) loginTitle.textContent = t('title');
    });

    const btnLangApp = document.getElementById('btn-lang-app');
    if (btnLangApp) {
        btnLangApp.textContent = t('btn_lang');
        const { toggleLang } = await import('./core/i18n.js').catch(() => ({ toggleLang: () => {} }));
        btnLangApp.addEventListener('click', toggleLang);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
} else {
    bootstrap();
}
