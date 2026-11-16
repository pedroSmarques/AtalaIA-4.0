# Notificações Web Push — ATALAIA 4.0

O que o back-end e o JS do grupo precisam fornecer para as telas funcionarem.

---

## 1. Front-end (JS do grupo)

**a) Registrar o Service Worker** (uma vez, após login):
```js
navigator.serviceWorker.register('/sw.js');
```

**b) Pedir permissão** (banner `#pushBanner` já está nas telas — acionar ao clicar em "Permitir"):
```js
Notification.requestPermission().then(perm => {
  if (perm === 'granted') subscribePush();
});
```

**c) Criar subscription e enviar ao servidor:**
```js
async function subscribePush() {
  const sw  = await navigator.serviceWorker.ready;
  const sub = await sw.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: '<VAPID_PUBLIC_KEY>'  // gerado pelo back-end
  });
  await fetch('/api/push/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(sub)   // back-end grava em usuarios.token_push
  });
}
```

**d) Service Worker (`sw.js`) recebe o push:**
```js
self.addEventListener('push', e => {
  const data = e.data.json();
  self.registration.showNotification(data.titulo, {
    body: data.corpo,
    icon: '/icon.png',
    data: { url: data.url }   // ex: /supervisor/alertas/2894
  });
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  clients.openWindow(e.notification.data.url);
});
```

---

## 2. Back-end (Python)

- **Instalar:** `pip install pywebpush`
- **Gerar chaves VAPID** (uma vez):
  ```bash
  python -m pywebpush --gen-keys
  ```
  Salvar `VAPID_PRIVATE_KEY` e `VAPID_PUBLIC_KEY` no `.env`.

- **Rota de subscription:**
  ```python
  @app.route('/api/push/subscribe', methods=['POST'])
  @login_obrigatorio
  def salvar_subscription():
      sub = request.json
      # gravar sub['endpoint'] + sub['keys'] em usuarios.token_push (JSON)
  ```

- **Disparar push ao criar incidente:**
  ```python
  from pywebpush import webpush
  webpush(
      subscription_info=json.loads(usuario.token_push),
      data=json.dumps({'titulo': 'Novo alerta', 'corpo': tipo_infracao, 'url': f'/supervisor/alertas/{id}'}),
      vapid_private_key=VAPID_PRIVATE_KEY,
      vapid_claims={'sub': 'mailto:admin@atalaia.com'}
  )
  # Registrar resultado em notificacoesPush (status_envio: enviado / falha)
  ```

---

## 3. Variáveis esperadas pelas telas

| Variável no HTML | Tipo | De onde vem |
|---|---|---|
| `notif_nao_lidas` | `int` | `session` ou query COUNT |
| `notificacoes` | `list[NotificacaoPush]` com `.incidente.tipo_infracao.nome`, `.data_hora_envio` | DAO |
| `token_push` | gravado em `usuarios.token_push` via rota `/api/push/subscribe` | — |
