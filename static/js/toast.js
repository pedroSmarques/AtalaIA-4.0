// toast.js — avisos rápidos (sucesso, erro, aviso). Carregado no painel e no login.
// Os avisos vindos do servidor (flash) já chegam em HTML; mostrarToast() cria os do navegador.
(function () {
  const ICONES = {
    sucesso: '<path d="M5 12.5l4.2 4.2L19 7"/>',
    erro:    '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5M12 16.4v.1"/>',
    aviso:   '<path d="M12 3.5l9.5 16.5h-19z"/><path d="M12 10v4.5M12 17.4v.1"/>',
    info:    '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.6v.1"/>'
  };
  const FECHAR = '<path d="M6 6l12 12M18 6L6 18"/>';
  const reduzMovimento = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function svg(conteudo) {
    return `<svg viewBox="0 0 24 24" aria-hidden="true">${conteudo}</svg>`;
  }

  function caixa() {
    let c = document.getElementById('toasts');
    if (!c) {
      c = document.createElement('div');
      c.id = 'toasts';
      c.className = 'toasts';
      document.body.appendChild(c);
    }
    return c;
  }

  function remover(toast) {
    if (!toast.isConnected || toast.classList.contains('saindo')) return;
    if (reduzMovimento()) { toast.remove(); return; }
    toast.classList.add('saindo');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
    setTimeout(() => toast.remove(), 400);   // garantia se o evento não vier
  }

  // liga o temporizador (com pausa ao passar o mouse ou focar) e o botão fechar
  function iniciar(toast) {
    if (toast.dataset.pronto) return;
    toast.dataset.pronto = '1';
    const duracao = Number(toast.dataset.duracao) || 5000;
    toast.style.setProperty('--duracao', duracao + 'ms');
    let restante = duracao, inicio = Date.now(), timer = null;
    const agendar = () => { inicio = Date.now(); timer = setTimeout(() => remover(toast), restante); };
    const pausar  = () => { clearTimeout(timer); restante -= Date.now() - inicio; };
    const retomar = () => { if (restante > 0) agendar(); };
    toast.addEventListener('mouseenter', pausar);
    toast.addEventListener('mouseleave', retomar);
    toast.addEventListener('focusin', pausar);
    toast.addEventListener('focusout', retomar);
    toast.querySelector('.toast-fechar')?.addEventListener('click', () => { clearTimeout(timer); remover(toast); });
    agendar();
  }

  // tipo: 'sucesso' | 'erro' | 'aviso' | 'info'
  window.mostrarToast = function (tipo, mensagem) {
    if (!ICONES[tipo]) tipo = 'info';
    const toast = document.createElement('div');
    toast.className = `toast toast-${tipo}`;
    toast.setAttribute('role', tipo === 'erro' ? 'alert' : 'status');
    toast.dataset.duracao = tipo === 'erro' ? '8000' : '5000';
    toast.innerHTML =
      `<span class="toast-icone">${svg(ICONES[tipo])}</span>` +
      '<p class="toast-texto"></p>' +
      `<button type="button" class="toast-fechar" aria-label="Fechar aviso">${svg(FECHAR)}</button>` +
      '<span class="toast-barra" aria-hidden="true"></span>';
    toast.querySelector('.toast-texto').textContent = mensagem;   // texto puro: sem HTML injetado
    caixa().appendChild(toast);
    iniciar(toast);
    return toast;
  };

  function iniciarExistentes() {
    document.querySelectorAll('.toast').forEach(iniciar);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciarExistentes);
  else iniciarExistentes();
})();
