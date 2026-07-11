// Service worker mínimo: torna o app instalável (PWA).
// Não faz cache de dados — carteira precisa de dados frescos.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (evento) => evento.waitUntil(clients.claim()));
self.addEventListener("fetch", () => {});
