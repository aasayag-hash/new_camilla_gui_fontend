// API client - todos los wrappers fetch() para el backend CamillaGUI
// Base URL se configura desde login.js en window.CAMILLA_BASE

function base() {
    return window.CAMILLA_BASE || 'http://localhost:5005';
}

async function get(path) {
    const r = await fetch(`${base()}${path}`, { cache: 'no-store' });
    if (!r.ok) throw new Error(`HTTP ${r.status} en GET ${path}`);
    const ct = r.headers.get('content-type') || '';
    if (ct.includes('application/json')) return r.json();
    return r.text();
}

async function post(path, body, isText = false) {
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
        throw new Error(`HTTP ${r.status} en POST ${path}: ${txt}`);
    }
    const ct = r.headers.get('content-type') || '';
    if (ct.includes('application/json')) return r.json();
    return r.text();
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
