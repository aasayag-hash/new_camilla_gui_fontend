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
import { reloadConfig }      from './core/state.js';

const DEFAULT_IP = 'localhost';
const DEFAULT_PORT = '5005';

function autoConnect() {
    const base = `http://${DEFAULT_IP}:${DEFAULT_PORT}`;
    window.CAMILLA_BASE = base;
    
    const statusEl = document.getElementById('login-status');
    const appScreen = document.getElementById('screen-app');
    const debugPanel = document.getElementById('debug-panel');
    
    appScreen.style.display = 'flex';
    if (debugPanel) debugPanel.style.display = 'block';
    
    document.getElementById('app-title').textContent = `Conectando a ${base}...`;
    statusEl.textContent = `Conectando a ${base}...`;
    statusEl.className = '';
    
    console.log('[AutoConnect] Intentando conectar a:', base);
    
    API.getStatus()
        .then(data => {
            console.log('[AutoConnect] Estado recibido:', data);
            statusEl.textContent = `✓ Conectado a ${base}`;
            statusEl.className = 'ok';
            document.getElementById('app-title').textContent = t('title');
            return reloadConfig();
        })
        .catch(err => {
            console.error('[AutoConnect] Error:', err);
            let details = `URL: ${base}\n`;
            if (err.message) details += `Error: ${err.message}\n`;
            if (err.status) details += `HTTP Status: ${err.status}\n`;
            if (err.statusText) details += `Status Text: ${err.statusText}\n`;
            details += `\nTiempo: ${new Date().toLocaleString()}`;
            
            statusEl.innerHTML = `
                <div style="text-align: left; padding: 10px;">
                    <strong style="color: #ff6b6b;">⚠ Error de conexión:</strong>
                    <pre style="background: #1a1a2e; padding: 8px; border-radius: 4px; 
                                overflow-x: auto; font-size: 11px; color: #ccc; margin-top:8px;">
${details}
                    </pre>
                    <div style="margin-top:10px; font-size:12px; color:#aaa;">
                        Verifica: <code>sudo systemctl status camillagui</code>
                    </div>
                </div>
            `;
            statusEl.className = 'error';
            document.getElementById('app-title').textContent = '⚠ Sin conexión - CamillaDSP';
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

    autoConnect();

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
