// API client - todos los wrappers fetch() para el backend CamillaGUI
// Base URL se configura desde login.js en window.CAMILLA_BASE

function base() {
    return window.CAMILLA_BASE || 'http://localhost:5005';
}

function debugLog(type, method, path, data, response) {
    const panel = document.getElementById('debug-output');
    if (!panel) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const color = type === 'SEND' ? '#4ade80' : type === 'RECV' ? '#60a5fa' : '#f87171';
    const arrow = type === 'SEND' ? '→' : type === 'RECV' ? '←' : '✕';
    
    let content = `<span style="color:#666">[${timestamp}]</span> <span style="color:${color}">${arrow} ${method} ${path}</span>`;
    
    if (type === 'SEND' && data) {
        const dataStr = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
        content += `<pre style="margin:2px 0 5px 20px; color:#888; font-size:10px; max-height:60px; overflow:auto;">${dataStr.substring(0, 500)}</pre>`;
    }
    
    if (type === 'RECV' && response) {
        const respStr = typeof response === 'string' ? response : JSON.stringify(response, null, 2);
        content += `<pre style="margin:2px 0 5px 20px; color:#aaa; font-size:10px; max-height:80px; overflow:auto;">${respStr.substring(0, 800)}</pre>`;
    }
    
    if (type === 'ERROR') {
        content += `<span style="color:#f87171"> - ${data}</span>`;
    }
    
    const div = document.createElement('div');
    div.innerHTML = content;
    div.style.marginBottom = '5px';
    panel.appendChild(div);
    panel.scrollTop = panel.scrollHeight;
}

async function get(path) {
    debugLog('SEND', 'GET', path, null, null);
    try {
        const r = await fetch(`${base()}${path}`, { cache: 'no-store' });
        if (!r.ok) {
            debugLog('ERROR', 'GET', path, `HTTP ${r.status}`, null);
            throw new Error(`HTTP ${r.status} en GET ${path}`);
        }
        const ct = r.headers.get('content-type') || '';
        let data;
        if (ct.includes('application/json')) {
            data = await r.json();
        } else {
            data = await r.text();
        }
        debugLog('RECV', 'GET', path, null, data);
        return data;
    } catch (err) {
        debugLog('ERROR', 'GET', path, err.message, null);
        throw err;
    }
}

async function post(path, body, isText = false) {
    debugLog('SEND', 'POST', path, body, null);
    try {
        const opts = {
            method: 'POST',
            cache: 'no-store',
        };
        if (body instanceof FormData) {
            opts.body = body;
        } else if (isText) {
            opts.headers = { 'Content-Type': 'text/plain' };
            opts.body = body;
        } else {
            opts.headers = { 'Content-Type': 'application/json' };
            opts.body = typeof body === 'string' ? body : JSON.stringify(body);
        }
        const r = await fetch(`${base()}${path}`, opts);
        if (!r.ok) {
            const txt = await r.text();
            debugLog('ERROR', 'POST', path, `HTTP ${r.status}: ${txt}`, null);
            throw new Error(`HTTP ${r.status} en POST ${path}: ${txt}`);
        }
        const ct = r.headers.get('content-type') || '';
        let data;
        if (ct.includes('application/json')) {
            data = await r.json();
        } else {
            data = await r.text();
        }
        debugLog('RECV', 'POST', path, null, data);
        return data;
    } catch (err) {
        debugLog('ERROR', 'POST', path, err.message, null);
        throw err;
    }
}

// ── Status ──────────────────────────────────────────────────────────
export async function getStatus() {
    return get('/api/status');
}

// ── Configuración ────────────────────────────────────────────────────
export async function getConfig() {
    return get('/api/getconfig');
}

export async function setConfig(configJson) {
    return post('/api/setconfig', configJson);
}

export async function validateConfig(configJson) {
    return post('/api/validateconfig', configJson);
}

export async function getActiveConfigFilename() {
    return get('/api/getactiveconfigfilename');
}

export async function setActiveConfigFile(name) {
    return post('/api/setactiveconfigfile', { name });
}

export async function storedConfigs() {
    return get('/api/storedconfigs');
}

// ── Parámetros ───────────────────────────────────────────────────────
export async function getParam(name) {
    return get(`/api/getparam/${name}`);
}

export async function setParam(name, value) {
    return post(`/api/setparam/${name}`, { value });
}

export async function setParamIndex(name, index, value) {
    return post(`/api/setparamindex/${name}/${index}`, { value });
}

// ── Archivos ─────────────────────────────────────────────────────────
export async function uploadConfigs(formData) {
    return post('/api/uploadconfigs', formData);
}

export async function deleteConfigs(names) {
    return post('/api/deleteconfigs', names);
}

export async function storedCoeffs() {
    return get('/api/storedcoeffs');
}

export async function uploadCoeffs(formData) {
    return post('/api/uploadcoeffs', formData);
}

export async function deleteCoeffs(names) {
    return post('/api/deletecoeffs', names);
}

// ── Conversión de Formatos ────────────────────────────────────────────
export async function configToYml(configJson) {
    return post('/api/configtoyml', configJson, true);
}

export async function ymlToJson(yamlText) {
    return post('/api/ymlconfigtojsonconfig', yamlText, true);
}

export async function eqApoToJson(text, channels) {
    return post(`/api/eqapotojson?channels=${channels}`, text, true);
}

// ── Evaluación de Filtros ────────────────────────────────────────────
export async function evalFilter(spec) {
    return post('/api/evalfilter', spec);
}

export async function evalFilterStep(spec) {
    return post('/api/evalfilterstep', spec);
}

// ── Dispositivos ─────────────────────────────────────────────────────
export async function getBackends() {
    return get('/api/backends');
}

export async function getCaptureDevices(backend) {
    return get(`/api/capturedevices/${backend}`);
}

export async function getPlaybackDevices(backend) {
    return get(`/api/playbackdevices/${backend}`);
}

// ── GUI Config ───────────────────────────────────────────────────────
export async function getGuiConfig() {
    return get('/api/guiconfig');
}

// ── Log ──────────────────────────────────────────────────────────────
export async function getLogFile() {
    return get('/api/logfile');
}
