// snack.js — Snackbar/toast global
let _timer = null;

export function showSnack(msg, type = 'info', duration = 2800) {
    const el = document.getElementById('snackbar');
    if (!el) return;
    if (_timer) { clearTimeout(_timer); el.classList.remove('show', 'success', 'error', 'warn'); }
    el.textContent = msg;
    el.className = '';
    if (type !== 'info') el.classList.add(type);
    // Forzar reflow
    void el.offsetWidth;
    el.classList.add('show');
    _timer = setTimeout(() => {
        el.classList.remove('show');
        _timer = null;
    }, duration);
}
