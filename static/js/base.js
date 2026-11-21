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
    if (e.key === 'Escape') {
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

// Modal genérico: data-modal-open="id" / data-modal-close / .modal-overlay
function initModais() {
  document.querySelectorAll('[data-modal-open]').forEach(btn => {
    btn.addEventListener('click', () => {
      const overlay = document.getElementById(btn.dataset.modalOpen);
      overlay?.classList.add('aberto');
    });
  });

  document.querySelectorAll('[data-modal-close], .modal-fechar').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.modal-overlay')?.classList.remove('aberto');
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) overlay.classList.remove('aberto');
    });
  });
}

atualizarData();
initNotificacoes();
initPushBanner();
initFiltros();
initModais();
