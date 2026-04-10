// EventBus - Sistema pub/sub global
const _handlers = {};

export const Events = {
    on(event, cb) {
        if (!_handlers[event]) _handlers[event] = [];
        _handlers[event].push(cb);
    },
    off(event, cb) {
        if (!_handlers[event]) return;
        _handlers[event] = _handlers[event].filter(h => h !== cb);
    },
    emit(event, data) {
        (_handlers[event] || []).forEach(cb => { try { cb(data); } catch(e) { console.error(`[Events] Error en handler '${event}':`, e); } });
    }
};
