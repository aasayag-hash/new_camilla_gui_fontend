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

// ── Función principal llamada tras login exitoso ──────────────────────────────
function showApp(ip, port) {
    document.getElementById('screen-login').style.display = 'none';
    document.getElementById('screen-app').style.display   = 'flex';

    // Actualizar título con IP
    const titleEl = document.getElementById('app-title');
    if (titleEl) titleEl.textContent = t('title') + ` — ${ip}:${port}`;
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
function bootstrap() {
    // 1. Login
    initLogin((ip, port) => {
        showApp(ip, port);
    });

    // 2. Modales (cerrar con X o Escape)
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
    // Cerrar modal al click fuera del panel
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', e => {
            if (e.target === overlay) overlay.classList.add('hidden');
        });
    });

    // 3. Botones de cabecera
    initCornerButtons();

    // 4. Channel panel
    initChannelPanel();

    // 5. Tabs
    initTabManager(tabId => {
        // Parar polling VU cuando cambiamos de tab, reanudar al volver
        if (tabId === 'vu') {
            startPolling();
        } else {
            stopPolling();
        }
    });

    // 6. Contenido de cada tab
    initVuTab();
    initEqTab();
    initCrossTab();
    initMixerTab();

    // 7. Idioma — actualizar título app en cambios de lang
    Events.on('lang:changed', () => {
        // Re-aplicar título si está en pantalla app
        const app = document.getElementById('screen-app');
        if (app && app.style.display !== 'none') {
            const titleEl = document.getElementById('app-title');
            if (titleEl) titleEl.textContent = t('title');
        }
        // Re-aplicar título login
        const loginTitle = document.getElementById('login-title');
        if (loginTitle) loginTitle.textContent = t('title');
    });

    // 8. Botón lang en app header
    const btnLangApp = document.getElementById('btn-lang-app');
    if (btnLangApp) {
        btnLangApp.textContent = t('btn_lang');
        const { toggleLang } = await import('./core/i18n.js').catch(() => ({ toggleLang: () => {} }));
        btnLangApp.addEventListener('click', toggleLang);
    }
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootstrap);
} else {
    bootstrap();
}
