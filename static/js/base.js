// base.js — funções compartilhadas por todas as páginas da aplicação

// Atualiza o elemento #dataAtual com a data de hoje formatada
function atualizarData() {
  const el = document.getElementById('dataAtual');
  if (!el) return;
  const hoje = new Date();
  const texto = hoje.toLocaleDateString('pt-BR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  });
  el.textContent = texto.charAt(0).toUpperCase() + texto.slice(1);
}

// Toggle do painel de notificações
function initNotificacoes() {
  const btn    = document.getElementById('btnNotif');
  const painel = document.getElementById('notifPainel');
  if (!btn || !painel) return;

  btn.addEventListener('click', e => {
    e.stopPropagation();
    const aberto = painel.classList.toggle('aberto');
    btn.setAttribute('aria-expanded', String(aberto));
  });

  document.addEventListener('click', e => {
    if (!painel.contains(e.target) && e.target !== btn) {
      painel.classList.remove('aberto');
      btn.setAttribute('aria-expanded', 'false');
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && painel.classList.contains('aberto')) {
      painel.classList.remove('aberto');
      btn.setAttribute('aria-expanded', 'false');
      btn.focus();
    }
  });
}

// Banner de permissão de notificações push
function initPushBanner() {
  const banner = document.getElementById('pushBanner');
  if (!banner) return;

  // só mostra se o navegador suporta e ainda não foi decidido
  if (!('Notification' in window) || Notification.permission !== 'default') {
    banner.classList.add('oculto');
    return;
  }

  document.getElementById('btnPermitirPush')?.addEventListener('click', () => {
    Notification.requestPermission().then(p => {
      banner.classList.add('oculto');
      // Back-end: após permissão concedida, o SW deve registrar e enviar o token_push ao servidor
      if (p === 'granted') console.info('[Atalaia] Push permitido — registrar SW e enviar token_push.');
    });
  });

  document.getElementById('btnRecusarPush')?.addEventListener('click', () => {
    banner.classList.add('oculto');
    sessionStorage.setItem('pushBannerRecusado', '1');
  });

  if (sessionStorage.getItem('pushBannerRecusado')) banner.classList.add('oculto');
}

// Filtros de tabela genéricos (data-filtro / data-status)
function initFiltros() {
  document.querySelectorAll('.filtros').forEach(grupo => {
    const botoes = grupo.querySelectorAll('.filtro');
    botoes.forEach(btn => {
      btn.addEventListener('click', () => {
        botoes.forEach(b => b.classList.remove('ativo'));
        btn.classList.add('ativo');
        const filtro = btn.dataset.filtro;
        document.querySelectorAll('.linha[data-status]').forEach(linha => {
          const mostrar = filtro === 'todos' || linha.dataset.status === filtro;
          linha.classList.toggle('oculto', !mostrar);
        });
      });
    });
  });
}

// ---------------------------------------------------------------
// Modais: data-modal-open="id" abre, data-modal-close / Esc / clique fora fecham.
// Foco vai para o primeiro campo, fica preso no modal e volta ao botão que abriu.
// ---------------------------------------------------------------
let _modalAberto = null;
let _modalOrigem = null;

function abrirModal(id, origem) {
  const overlay = typeof id === 'string' ? document.getElementById(id) : id;
  if (!overlay) return;
  _modalOrigem = origem || document.activeElement;
  _modalAberto = overlay;
  overlay.classList.add('aberto');
  overlay.setAttribute('aria-hidden', 'false');
  document.documentElement.classList.add('modal-aberto');
  requestAnimationFrame(() => {
    const alvo = overlay.querySelector('input:not([type=hidden]):not([type=radio]), select, textarea') ||
                 overlay.querySelector('button, a[href]');
    alvo?.focus();
  });
}

function fecharModal(overlay = _modalAberto) {
  if (!overlay) return;
  overlay.classList.remove('aberto');
  overlay.setAttribute('aria-hidden', 'true');
  document.documentElement.classList.remove('modal-aberto');
  // limpa o formulário e os erros para a próxima abertura
  overlay.querySelectorAll('form').forEach(limparFormulario);
  if (_modalAberto === overlay) {
    _modalAberto = null;
    _modalOrigem?.focus?.();
    _modalOrigem = null;
  }
}

function initModais() {
  document.querySelectorAll('[data-modal-open]').forEach(btn => {
    btn.addEventListener('click', () => abrirModal(btn.dataset.modalOpen, btn));
  });

  document.querySelectorAll('[data-modal-close]').forEach(btn => {
    btn.addEventListener('click', () => fecharModal(btn.closest('.modal-overlay')));
  });

  // clique fora (no fundo escurecido) fecha
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('mousedown', e => { if (e.target === overlay) fecharModal(overlay); });
  });

  document.addEventListener('keydown', e => {
    if (!_modalAberto) return;
    if (e.key === 'Escape') { e.preventDefault(); fecharModal(); return; }
    if (e.key !== 'Tab') return;
    const lista = [..._modalAberto.querySelectorAll(
      'a[href], button:not([disabled]), input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])'
    )].filter(el => el.offsetParent !== null || el.type === 'radio');
    if (!lista.length) return;
    const primeiro = lista[0], ultimo = lista[lista.length - 1];
    if (e.shiftKey && document.activeElement === primeiro) { e.preventDefault(); ultimo.focus(); }
    else if (!e.shiftKey && document.activeElement === ultimo) { e.preventDefault(); primeiro.focus(); }
  });
}

// ---------------------------------------------------------------
// Formulários: validação com mensagem embaixo do campo, máscara de CPF,
// mostrar/ocultar senha e botão "carregando" ao enviar.
// ---------------------------------------------------------------
function mensagemDoCampo(el) {
  const v = el.validity;
  if (v.valueMissing)    return el.dataset.msgObrigatorio || 'Preencha este campo.';
  if (v.typeMismatch)    return el.type === 'email' ? 'Informe um e-mail válido, como nome@empresa.com.' : 'Valor inválido.';
  if (v.tooShort)        return `Use pelo menos ${el.minLength} caracteres.`;
  if (v.patternMismatch) return el.dataset.msg || 'Formato inválido.';
  if (v.rangeUnderflow || v.rangeOverflow) return `Informe um valor entre ${el.min} e ${el.max}.`;
  if (v.badInput)        return 'Valor inválido.';
  return el.validationMessage || 'Valor inválido.';
}

function mostrarErro(el) {
  const campo = el.closest('.campo') || el.parentElement;
  campo.classList.add('campo-erro');
  let msg = campo.querySelector('.msg-erro');
  if (!msg) {
    msg = document.createElement('p');
    msg.className = 'msg-erro';
    msg.id = `${el.id || el.name}Erro`;
    campo.appendChild(msg);
  }
  msg.textContent = mensagemDoCampo(el);
  el.setAttribute('aria-invalid', 'true');
  const ids = (el.getAttribute('aria-describedby') || '').split(' ').filter(i => i && i !== msg.id);
  el.setAttribute('aria-describedby', [...ids, msg.id].join(' '));
}

function limparErro(el) {
  const campo = el.closest('.campo') || el.parentElement;
  campo.classList.remove('campo-erro');
  const msg = campo.querySelector('.msg-erro');
  if (msg) {
    const ids = (el.getAttribute('aria-describedby') || '').split(' ').filter(i => i && i !== msg.id);
    ids.length ? el.setAttribute('aria-describedby', ids.join(' ')) : el.removeAttribute('aria-describedby');
    msg.remove();
  }
  el.removeAttribute('aria-invalid');
}

function limparFormulario(form) {
  form.reset();
  form.querySelectorAll('.campo-erro').forEach(c => c.classList.remove('campo-erro'));
  form.querySelectorAll('.msg-erro').forEach(m => m.remove());
  form.querySelectorAll('[aria-invalid]').forEach(el => el.removeAttribute('aria-invalid'));
  form.querySelectorAll('.input-toggle').forEach(t => definirSenhaVisivel(t, false));
  form.querySelectorAll('.btn.carregando').forEach(b => { b.classList.remove('carregando'); b.removeAttribute('aria-busy'); });
  delete form.dataset.enviando;
}

function aplicarMascaraCpf(el) {
  const d = el.value.replace(/\D/g, '').slice(0, 11);
  let r = d;
  if (d.length > 9)      r = `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6, 9)}-${d.slice(9)}`;
  else if (d.length > 6) r = `${d.slice(0, 3)}.${d.slice(3, 6)}.${d.slice(6)}`;
  else if (d.length > 3) r = `${d.slice(0, 3)}.${d.slice(3)}`;
  el.value = r;
}

function definirSenhaVisivel(botao, visivel) {
  const input = botao.closest('.input-icone')?.querySelector('input');
  if (!input) return;
  input.type = visivel ? 'text' : 'password';
  botao.setAttribute('aria-pressed', String(visivel));
  botao.setAttribute('aria-label', visivel ? 'Ocultar senha' : 'Mostrar senha');
}

function initFormularios() {
  // máscara do CPF (digita só números; o campo formata)
  document.querySelectorAll('input[data-mascara="cpf"]').forEach(el => {
    el.addEventListener('input', () => aplicarMascaraCpf(el));
  });

  // mostrar/ocultar senha
  document.querySelectorAll('[data-mostrar-senha]').forEach(botao => {
    botao.addEventListener('click', () => definirSenhaVisivel(botao, botao.getAttribute('aria-pressed') !== 'true'));
  });

  document.querySelectorAll('form[data-validar]').forEach(form => {
    // some o erro quando a pessoa volta a digitar
    form.addEventListener('input', e => { if (e.target.matches('input, select, textarea')) limparErro(e.target); });
    form.addEventListener('change', e => { if (e.target.matches('select')) limparErro(e.target); });

    form.addEventListener('submit', e => {
      if (form.dataset.enviando) { e.preventDefault(); return; }
      const invalidos = [...form.elements].filter(el => el.willValidate && !el.checkValidity());
      form.querySelectorAll('.campo-erro').forEach(c => c.classList.remove('campo-erro'));
      form.querySelectorAll('.msg-erro').forEach(m => m.remove());
      if (invalidos.length) {
        e.preventDefault();
        invalidos.forEach(mostrarErro);
        invalidos[0].focus();
        return;
      }
      // válido: botão de envio fica "carregando" (o valor do botão ainda é enviado)
      const enviar = e.submitter || form.querySelector('button[type=submit]');
      form.dataset.enviando = '1';
      if (enviar) { enviar.classList.add('carregando'); enviar.setAttribute('aria-busy', 'true'); }
    });
  });

  // se a página voltar do histórico com o botão preso em "carregando", libera
  window.addEventListener('pageshow', e => {
    if (e.persisted) document.querySelectorAll('form[data-validar]').forEach(f => {
      delete f.dataset.enviando;
      f.querySelectorAll('.btn.carregando').forEach(b => { b.classList.remove('carregando'); b.removeAttribute('aria-busy'); });
    });
  });
}

// Navegação: painel "Mais" (celular/tablet) e menu do avatar (Sair)
function initNavegacao() {
  const btn    = document.getElementById('btnMais');
  const painel = document.getElementById('painelMais');
  const fundo  = document.getElementById('maisFundo');
  if (btn && painel && fundo) {
    const principal = document.querySelector('.principal');
    const desktop   = window.matchMedia('(min-width: 1024px)');
    const aberto    = () => btn.getAttribute('aria-expanded') === 'true';

    // elementos que recebem foco dentro do painel (+ o botão que o controla)
    const focaveis = () => [...painel.querySelectorAll('a[href], button:not([disabled])'), btn];

    function abrir() {
      painel.classList.add('aberto');
      fundo.classList.add('aberto');
      document.documentElement.classList.add('mais-aberto');
      btn.setAttribute('aria-expanded', 'true');
      if (principal) principal.inert = true;          // conteúdo de trás fica fora do alcance
      requestAnimationFrame(() => painel.querySelector('a[href], button')?.focus());
    }

    function fechar(devolverFoco = true) {
      if (!aberto()) return;
      painel.classList.remove('aberto');
      fundo.classList.remove('aberto');
      document.documentElement.classList.remove('mais-aberto');
      btn.setAttribute('aria-expanded', 'false');
      if (principal) principal.inert = false;
      if (devolverFoco) btn.focus();
    }

    btn.addEventListener('click', () => (aberto() ? fechar() : abrir()));
    fundo.addEventListener('click', () => fechar());
    // ao navegar (clicar num link do painel ou voltar pelo histórico) o painel fecha
    painel.querySelectorAll('a[href]').forEach(a => a.addEventListener('click', () => fechar(false)));
    window.addEventListener('pageshow', () => fechar(false));
    desktop.addEventListener('change', e => { if (e.matches) fechar(false); });

    document.addEventListener('keydown', e => {
      if (!aberto()) return;
      if (e.key === 'Escape') { e.preventDefault(); fechar(); return; }
      if (e.key !== 'Tab') return;
      // foco preso: Tab circula só entre os itens do painel e o botão que o controla
      e.preventDefault();
      const lista = focaveis();
      const i = lista.indexOf(document.activeElement);
      const prox = e.shiftKey ? (i <= 0 ? lista.length - 1 : i - 1) : (i + 1) % lista.length;
      lista[prox].focus();
    });
  }

  const avatar = document.getElementById('btnAvatar');
  const opcoes = document.getElementById('menuAvatar');
  if (avatar && opcoes) {
    const definirAvatar = aberto => {
      opcoes.classList.toggle('aberto', aberto);
      avatar.setAttribute('aria-expanded', String(aberto));
    };
    avatar.addEventListener('click', e => {
      e.stopPropagation();
      definirAvatar(avatar.getAttribute('aria-expanded') !== 'true');
    });
    document.addEventListener('click', e => { if (!opcoes.contains(e.target)) definirAvatar(false); });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && opcoes.classList.contains('aberto')) { definirAvatar(false); avatar.focus(); }
    });
  }
}

// ---------------------------------------------------------------
// Avatares: se a foto não carregar, some e ficam as iniciais.
// ---------------------------------------------------------------
function initAvatares() {
  // o evento "error" de <img> não borbulha: captura na fase de captura
  document.addEventListener('error', e => {
    if (e.target.matches?.('img.av-img')) e.target.remove();
  }, true);
  document.querySelectorAll('img.av-img').forEach(img => {
    if (img.complete && img.naturalWidth === 0) img.remove();
  });
}

// ---------------------------------------------------------------
// Meu perfil: prévia da foto escolhida e aviso imediato de tipo/tamanho.
// (a validação que vale é a do servidor — esta é só para a pessoa não esperar o envio)
// ---------------------------------------------------------------
function initPerfil() {
  const input = document.getElementById('campoFoto');
  if (!input) return;
  const avatar = document.getElementById('perfilAvatar');
  const aviso  = document.getElementById('fotoErro');
  const campo  = input.closest('.campo');
  const remover = document.getElementById('removerFoto');
  const MAX = 2 * 1024 * 1024;
  const TIPOS = ['image/jpeg', 'image/png', 'image/webp'];
  let urlPrevia = null;

  const mostrarAviso = texto => {
    aviso.textContent = texto || '';
    aviso.hidden = !texto;
    campo.classList.toggle('campo-erro', Boolean(texto));
  };

  input.addEventListener('change', () => {
    const arquivo = input.files[0];
    if (urlPrevia) { URL.revokeObjectURL(urlPrevia); urlPrevia = null; }
    mostrarAviso('');
    if (!arquivo) return;
    if (!TIPOS.includes(arquivo.type)) {
      mostrarAviso('Envie uma imagem em JPG, PNG ou WebP.');
      input.value = '';
      return;
    }
    if (arquivo.size > MAX) {
      mostrarAviso('A foto deve ter no máximo 2 MB.');
      input.value = '';
      return;
    }
    urlPrevia = URL.createObjectURL(arquivo);
    avatar.querySelector('.av-img')?.remove();
    const img = document.createElement('img');
    img.className = 'av-img';
    img.alt = '';
    img.src = urlPrevia;
    avatar.querySelector('.av')?.appendChild(img);
    if (remover) remover.checked = false;
  });

  remover?.addEventListener('change', () => {
    if (remover.checked) {
      input.value = '';
      mostrarAviso('');
      avatar.querySelector('.av-img')?.remove();
    }
  });
}

atualizarData();
initAvatares();
initPerfil();
initNavegacao();
initNotificacoes();
initPushBanner();
initFiltros();
initModais();
initFormularios();
