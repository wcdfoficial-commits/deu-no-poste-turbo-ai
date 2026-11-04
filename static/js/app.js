let currentPage = 1;
let totalPages = 1;
let listaBichosCache = [];
let fullGamesCache = { t1: "", t2: "", t3: "" };
let retryCount = 0;
let isInitialized = false;

// --------------------------------------------------------------------------
// AUTENTICAÇÃO E CONTROLE DE ACESSO
// --------------------------------------------------------------------------
const AUTH_TOKEN_KEY = "deu_no_poste_auth_token";
const AUTH_USER_KEY = "deu_no_poste_auth_user";
const THEME_KEY = "deu_no_poste_theme";

function checkAuth() {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  const user = localStorage.getItem(AUTH_USER_KEY) || "Admin";
  const overlay = document.getElementById("login-overlay");
  const userDisplay = document.getElementById("user-name-display");

  if (userDisplay) userDisplay.textContent = user;

  if (token) {
    if (overlay) {
      overlay.classList.add("hidden");
      overlay.style.display = "none";
    }
    if (!isInitialized) {
      isInitialized = true;
      initApp();
    }
  } else {
    if (overlay) {
      overlay.classList.remove("hidden");
      overlay.style.display = "flex";
      const loginUser = document.getElementById("login-username");
      if (loginUser) loginUser.focus();
    }
  }
}

function alternarAbaAuth(aba) {
  const tabLogin = document.getElementById("tab-btn-login");
  const tabReg = document.getElementById("tab-btn-register");
  const formLogin = document.getElementById("login-form");
  const formReg = document.getElementById("register-form");
  const msgBox = document.getElementById("auth-msg-box");

  if (msgBox) {
    msgBox.classList.remove("show", "success");
  }

  if (aba === "register") {
    if (tabLogin) tabLogin.classList.remove("active");
    if (tabReg) tabReg.classList.add("active");
    if (formLogin) {
      formLogin.classList.add("auth-form-hidden");
      formLogin.style.display = "none";
    }
    if (formReg) {
      formReg.classList.remove("auth-form-hidden");
      formReg.style.display = "flex";
    }
    const regUser = document.getElementById("reg-username");
    if (regUser) regUser.focus();
  } else {
    if (tabReg) tabReg.classList.remove("active");
    if (tabLogin) tabLogin.classList.add("active");
    if (formReg) {
      formReg.classList.add("auth-form-hidden");
      formReg.style.display = "none";
    }
    if (formLogin) {
      formLogin.classList.remove("auth-form-hidden");
      formLogin.style.display = "flex";
    }
    const loginUser = document.getElementById("login-username");
    if (loginUser) loginUser.focus();
  }
}

function toggleSenhaVisibilidade(inputId = "login-password") {
  const passEl = document.getElementById(inputId);
  if (!passEl) return;
  passEl.type = passEl.type === "password" ? "text" : "password";
}

async function realizarLogin(event) {
  if (event) { event.preventDefault(); event.stopPropagation(); }
  
  const userEl = document.getElementById("login-username");
  const passEl = document.getElementById("login-password");
  const msgBox = document.getElementById("auth-msg-box");
  const msgText = document.getElementById("auth-msg-text");
  const msgIcon = document.getElementById("auth-msg-icon");
  const loginCard = document.getElementById("login-card");
  const btnSubmit = document.getElementById("btn-submit-login");

  const username = userEl ? userEl.value.trim() : "";
  const password = passEl ? passEl.value.trim() : "";

  if (!username || !password) {
    if (msgBox) {
      if (msgText) msgText.textContent = "Por favor, digite seu usuário/e-mail e a senha.";
      if (msgIcon) msgIcon.textContent = "⚠️";
      msgBox.classList.remove("success");
      msgBox.classList.add("show");
    }
    return;
  }

  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<span>⏳ Entrando...</span>`;
  }

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();

    if (res.ok && data.status === "success") {
      localStorage.setItem(AUTH_TOKEN_KEY, data.token);
      localStorage.setItem(AUTH_USER_KEY, data.user);
      
      const userDisplay = document.getElementById("user-name-display");
      if (userDisplay) userDisplay.textContent = data.user;

      if (msgBox) msgBox.classList.remove("show");

      const overlay = document.getElementById("login-overlay");
      if (overlay) {
        overlay.classList.add("hidden");
        overlay.style.display = "none";
      }

      showToast(`Bem-vindo(a), ${data.user}! Terminal analítico liberado.`);
      
      if (!isInitialized) {
        isInitialized = true;
        initApp();
      }
    } else {
      if (loginCard) {
        loginCard.classList.remove("shake");
        void loginCard.offsetWidth;
        loginCard.classList.add("shake");
      }
      if (msgBox) {
        if (msgText) msgText.textContent = data.detail || "Credenciais incorretas! Acesso não autorizado.";
        if (msgIcon) msgIcon.textContent = "⚠️";
        msgBox.classList.remove("success");
        msgBox.classList.add("show");
      }
      if (passEl) {
        passEl.value = "";
        passEl.focus();
      }
    }
  } catch (e) {
    if (msgBox) {
      if (msgText) msgText.textContent = "Falha ao conectar com o servidor.";
      if (msgIcon) msgIcon.textContent = "⚠️";
      msgBox.classList.remove("success");
      msgBox.classList.add("show");
    }
  } finally {
    if (btnSubmit) {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = `<span>⚡ Entrar no Terminal</span>`;
    }
  }
}

async function realizarCadastro(event) {
  if (event) event.preventDefault();

  const userEl = document.getElementById("reg-username");
  const emailEl = document.getElementById("reg-email");
  const passEl = document.getElementById("reg-password");
  const msgBox = document.getElementById("auth-msg-box");
  const msgText = document.getElementById("auth-msg-text");
  const msgIcon = document.getElementById("auth-msg-icon");
  const loginCard = document.getElementById("login-card");
  const btnSubmit = document.getElementById("btn-submit-reg");

  const username = userEl ? userEl.value.trim() : "";
  const email = emailEl ? emailEl.value.trim() : "";
  const password = passEl ? passEl.value.trim() : "";

  if (!username || !email || !password) {
    if (msgBox) {
      if (msgText) msgText.textContent = "Por favor, preencha todos os campos do cadastro.";
      if (msgIcon) msgIcon.textContent = "⚠️";
      msgBox.classList.remove("success");
      msgBox.classList.add("show");
    }
    return;
  }

  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<span>⏳ Criando sua conta...</span>`;
  }

  try {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password })
    });

    const data = await res.json();

    if (res.ok && data.status === "success") {
      localStorage.setItem(AUTH_TOKEN_KEY, data.token);
      localStorage.setItem(AUTH_USER_KEY, data.user);

      const userDisplay = document.getElementById("user-name-display");
      if (userDisplay) userDisplay.textContent = data.user;

      if (msgBox) {
        if (msgText) msgText.textContent = data.message || "Conta criada com sucesso!";
        if (msgIcon) msgIcon.textContent = "✅";
        msgBox.classList.remove("show");
        msgBox.classList.add("show", "success");
      }

      showToast(`Conta criada com sucesso! Bem-vindo(a), ${data.user}!`);

      setTimeout(() => {
        const overlay = document.getElementById("login-overlay");
        if (overlay) {
          overlay.classList.add("hidden");
          overlay.style.display = "none";
        }
        if (!isInitialized) {
          isInitialized = true;
          initApp();
        }
      }, 700);
    } else {
      if (loginCard) {
        loginCard.classList.remove("shake");
        void loginCard.offsetWidth;
        loginCard.classList.add("shake");
      }
      if (msgBox) {
        if (msgText) msgText.textContent = data.detail || "Erro ao criar conta. Verifique os dados.";
        if (msgIcon) msgIcon.textContent = "⚠️";
        msgBox.classList.remove("success");
        msgBox.classList.add("show");
      }
    }
  } catch (e) {
    if (msgBox) {
      if (msgText) msgText.textContent = "Falha de conexão com o servidor ao cadastrar.";
      if (msgIcon) msgIcon.textContent = "⚠️";
      msgBox.classList.remove("success");
      msgBox.classList.add("show");
    }
  } finally {
    if (btnSubmit) {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = `<span>✨ Cadastrar & Começar</span>`;
    }
  }
}

function fazerLogout() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
  
  const userEl = document.getElementById("login-username");
  const passEl = document.getElementById("login-password");
  if (userEl) userEl.value = "";
  if (passEl) passEl.value = "";
  
  alternarAbaAuth("login");
  
  const overlay = document.getElementById("login-overlay");
  if (overlay) {
    overlay.classList.remove("hidden");
    overlay.style.display = "flex";
  }
  
  showToast("Sessão finalizada com sucesso.");
}

// --------------------------------------------------------------------------
// GERENCIADOR DOS 3 TEMAS PROFISSIONAIS
// --------------------------------------------------------------------------
const THEME_NAMES = {
  quant: "💎 Bloomberg Quant Terminal",
  gold: "👑 VIP Executive Gold",
  studio: "🌌 Apple SaaS Studio"
};

function mudarTema(themeName) {
  if (!["quant", "gold", "studio"].includes(themeName)) return;

  document.documentElement.setAttribute("data-theme", themeName);
  document.body.setAttribute("data-theme", themeName);
  localStorage.setItem(THEME_KEY, themeName);

  document.querySelectorAll(".btn-theme-pill").forEach(btn => {
    if (btn.getAttribute("data-theme-name") === themeName) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  showToast(`Layout alterado: ${THEME_NAMES[themeName] || themeName}`);
}

function carregarTemaSalvo() {
  const savedTheme = localStorage.getItem(THEME_KEY) || "quant";
  document.documentElement.setAttribute("data-theme", savedTheme);
  document.body.setAttribute("data-theme", savedTheme);

  document.querySelectorAll(".btn-theme-pill").forEach(btn => {
    if (btn.getAttribute("data-theme-name") === savedTheme) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
}

// --------------------------------------------------------------------------
// NOTIFICADOR TOAST
// --------------------------------------------------------------------------
function showToast(msg, isSuccess = true) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  const icon = document.getElementById("toast-icon");
  const msgEl = document.getElementById("toast-msg");
  
  if (icon) icon.textContent = isSuccess ? "✅" : "⚠️";
  if (msgEl) msgEl.textContent = msg;
  toast.classList.add("show");
  
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

// --------------------------------------------------------------------------
// ALTERNADOR DE ABAS
// --------------------------------------------------------------------------
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));
  
  const targetTab = document.getElementById(tabId);
  if (targetTab) targetTab.classList.add("active");
  
  const btns = Array.from(document.querySelectorAll(".tab-btn"));
  const clickedBtn = btns.find(b => b.getAttribute("onclick")?.includes(tabId));
  if (clickedBtn) clickedBtn.classList.add("active");

  if (tabId === "tab-autopilot") {
    carregarStatusAutoPilot();
    carregarMonitoramentoAssertividade();
  }
}

// --------------------------------------------------------------------------
// INICIALIZAÇÃO COM AUTO-RETRY
// --------------------------------------------------------------------------
async function initApp() {
  console.log("Iniciando DEU NO POSTE ANALYTICS PRO...");
  const ok = await carregarStatus();
  if (ok) {
    await carregarBichos();
    await carregarPredicoes();
    await carregarResultados(1);
    await carregarFilaApostas();
    await carregarEstatisticasCiclos();
    await carregarStatusAutoPilot();
    await carregarMonitoramentoAssertividade();
    setInterval(carregarStatusAutoPilot, 30000);
  } else {
    if (retryCount < 6) {
      retryCount++;
      console.log(`Servidor conectando. Tentativa ${retryCount}/6 em 1.5s...`);
      setTimeout(initApp, 1500);
    }
  }
}

// --------------------------------------------------------------------------
// CARREGAR STATUS DO BANCO
// --------------------------------------------------------------------------
async function carregarStatus() {
  try {
    const res = await fetch("/api/status");
    if (!res.ok) return false;
    const data = await res.json();
    
    const elSorteios = document.getElementById("stat-total-sorteios");
    const elPremios = document.getElementById("stat-total-premios");
    const elPeriodo = document.getElementById("stat-periodo");
    const elUltimo = document.getElementById("stat-ultimo");
    
    if (elSorteios) elSorteios.textContent = Number(data.total_sorteios).toLocaleString("pt-BR");
    if (elPremios) elPremios.textContent = Number(data.total_registros).toLocaleString("pt-BR");
    if (elPeriodo) elPeriodo.textContent = `${data.data_inicio} a ${data.data_fim}`;
    
    if (elUltimo && data.ultimo_sorteio) {
      elUltimo.textContent = `${data.ultimo_sorteio.data} (${data.ultimo_sorteio.extracao})`;
    }
    return true;
  } catch (e) {
    return false;
  }
}

// --------------------------------------------------------------------------
// CARREGAR BICHOS COM ÍCONES
// --------------------------------------------------------------------------
async function carregarBichos() {
  try {
    const res = await fetch("/api/bichos");
    if (!res.ok) return;
    listaBichosCache = await res.json();
    
    const selectFiltro = document.getElementById("filtro-bicho");
    const selectPuxada = document.getElementById("puxada-select-bicho");
    
    if (selectFiltro) {
      selectFiltro.innerHTML = '<option value="">Todos os Bichos</option>';
      listaBichosCache.forEach(b => {
        const opt = document.createElement("option");
        opt.value = b.nome;
        opt.textContent = `${b.icone} ${b.grupo} - ${b.nome}`;
        selectFiltro.appendChild(opt);
      });
    }
    
    if (selectPuxada) {
      selectPuxada.innerHTML = "";
      listaBichosCache.forEach(b => {
        const opt = document.createElement("option");
        opt.value = b.nome;
        opt.textContent = `${b.icone} Grupo ${b.grupo} - ${b.nome} (${b.dezenas.join(", ")})`;
        selectPuxada.appendChild(opt);
      });
      consultarPuxada();
    }
  } catch (e) {
    console.error("Erro ao carregar lista de bichos:", e);
  }
}

// --------------------------------------------------------------------------
// CARREGAR PREDIÇÕES IA E GATILHOS ESPECIAIS
// --------------------------------------------------------------------------
async function carregarPredicoes() {
  try {
    const res = await fetch("/api/predicoes");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;
    
    const ult = data.ultimo_sorteio;
    const radar = data.radar_analitico;
    const est = data.estrategias;
    
    // Banner Superior
    const elTitulo = document.getElementById("banner-sorteio-titulo");
    const elBadge = document.getElementById("banner-bicho-badge");
    const elMilhar = document.getElementById("banner-milhar");
    const elCentena = document.getElementById("banner-centena");
    const elDezena = document.getElementById("banner-dezena");
    const elParidade = document.getElementById("banner-paridade");
    
    if (elTitulo) elTitulo.textContent = `${ult.extracao} (${ult.horario}) - ${ult.data}`;
    if (elBadge) {
      elBadge.innerHTML = `
        <div class="bicho-badge" style="font-size: 1.15rem; padding: 0.45rem 0.9rem; background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.4);">
          <span class="bicho-icon">${ult.icone}</span>
          <span>Grupo ${ult.grupo} - ${ult.bicho}</span>
        </div>
      `;
    }
    if (elMilhar) elMilhar.textContent = ult.milhar;
    if (elCentena) elCentena.textContent = ult.centena;
    if (elDezena) elDezena.textContent = ult.dezena;
    if (elParidade) elParidade.textContent = radar.tendencia_paridade;
    
    // Gatilhos Especiais Ativos (Gêmeas, Inversão 01-09, Centenas Raras)
    const containerEspeciais = document.getElementById("container-gatilhos-especiais");
    if (containerEspeciais) {
      if (data.gatilhos_especiais_ativos && data.gatilhos_especiais_ativos.length > 0) {
        containerEspeciais.style.display = "block";
        containerEspeciais.innerHTML = "";
        data.gatilhos_especiais_ativos.forEach(g => {
          const cardG = document.createElement("div");
          cardG.className = "card";
          cardG.style.borderColor = g.cor;
          cardG.style.marginBottom = "0.85rem";
          cardG.innerHTML = `
            <div class="card-header" style="margin-bottom: 0.5rem;">
              <div class="card-title" style="color: ${g.cor}; font-size: 1.05rem;">
                <span>⚡</span> ${g.titulo}
              </div>
              <span class="card-badge" style="background: rgba(255,255,255,0.08); color: ${g.cor}; border: 1px solid ${g.cor};">${g.badge}</span>
            </div>
            <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 0.65rem;">${g.descricao}</p>
            <div style="display: flex; flex-wrap: wrap; gap: 1.25rem; font-size: 0.88rem;">
              <div>Taxa Dinâmica de Assertividade: <strong style="color: ${g.cor}; font-size: 0.95rem;">${g.taxa_acerto}</strong></div>
              <div>Amostragem: <span style="color: var(--text-muted);">${g.amostra}</span></div>
              <div>Força Estatística: <strong style="color: var(--text-main);">${g.forca}</strong></div>
            </div>
          `;
          containerEspeciais.appendChild(cardG);
        });
      } else {
        containerEspeciais.style.display = "none";
      }
    }

    // Nível 1: Dezena
    const elT1Inv = document.getElementById("t1-investimento");
    const elT1Taxa = document.getElementById("t1-taxa");
    const elT1Amostra = document.getElementById("t1-amostra");
    const elT1Roi = document.getElementById("t1-roi");
    const elT1Dez = document.getElementById("t1-dezenas");
    if (elT1Inv) elT1Inv.textContent = est.nivel_1.investimento;
    if (elT1Taxa) elT1Taxa.textContent = est.nivel_1.taxa_historica;
    if (elT1Amostra) elT1Amostra.textContent = est.nivel_1.amostra_historica;
    if (elT1Roi) elT1Roi.textContent = est.nivel_1.roi_estimado;
    if (elT1Dez) elT1Dez.textContent = est.nivel_1.dezenas_formatadas;
    fullGamesCache.t1 = est.nivel_1.dezenas_formatadas;
    
    // Nível 2: Centena
    const elT2Inv = document.getElementById("t2-investimento");
    const elT2Taxa = document.getElementById("t2-taxa");
    const elT2Amostra = document.getElementById("t2-amostra");
    const elT2Roi = document.getElementById("t2-roi");
    const elT2Cent = document.getElementById("t2-centenas");
    if (elT2Inv) elT2Inv.textContent = est.nivel_2.investimento;
    if (elT2Taxa) elT2Taxa.textContent = est.nivel_2.taxa_historica;
    if (elT2Amostra) elT2Amostra.textContent = est.nivel_2.amostra_historica;
    if (elT2Roi) elT2Roi.textContent = est.nivel_2.roi_estimado;
    if (elT2Cent) elT2Cent.textContent = est.nivel_2.centenas.join(", ");
    fullGamesCache.t2 = est.nivel_2.centenas.join("\n");
    
    // Nível 3: Milhar
    const elT3Inv = document.getElementById("t3-investimento");
    const elT3Taxa = document.getElementById("t3-taxa");
    const elT3Amostra = document.getElementById("t3-amostra");
    const elT3Roi = document.getElementById("t3-roi");
    const elT3Mil = document.getElementById("t3-milhares");
    if (elT3Inv) elT3Inv.textContent = est.nivel_3.investimento;
    if (elT3Taxa) elT3Taxa.textContent = est.nivel_3.taxa_historica;
    if (elT3Amostra) elT3Amostra.textContent = est.nivel_3.amostra_historica;
    if (elT3Roi) elT3Roi.textContent = est.nivel_3.roi_estimado;
    if (elT3Mil) elT3Mil.textContent = est.nivel_3.milhares.join(", ");
    fullGamesCache.t3 = est.nivel_3.milhares.join("\n");
    
    // Top Puxadas Grid
    const gridPuxadas = document.getElementById("grid-puxadas-topo");
    if (gridPuxadas) {
      gridPuxadas.innerHTML = "";
      data.top_puxadas.forEach(p => {
        const pill = document.createElement("div");
        pill.className = "bicho-badge";
        pill.style.padding = "0.5rem 0.9rem";
        pill.innerHTML = `
          <span class="bicho-icon">${p.icone}</span>
          <strong>${p.bicho}</strong> (Gr ${p.grupo})
          <span style="color: var(--primary); font-size: 0.8rem; margin-left: 0.35rem;">${p.taxa}% (${p.lift}x)</span>
        `;
        gridPuxadas.appendChild(pill);
      });
    }
    
  } catch (e) {
    console.error("Erro ao carregar predições:", e);
  }
}

// --------------------------------------------------------------------------
// CARREGAR RESULTADOS COM FILTROS E PAGINAÇÃO
// --------------------------------------------------------------------------
async function carregarResultados(page = 1) {
  currentPage = page;
  const tbody = document.getElementById("tabela-resultados-body");
  if (!tbody) return;
  
  tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; padding: 2rem;">Buscando registros no banco de dados...</td></tr>';
  
  const params = new URLSearchParams({
    page: page,
    page_size: 50
  });
  
  const dIni = document.getElementById("filtro-data-ini")?.value;
  const dFim = document.getElementById("filtro-data-fim")?.value;
  const ext = document.getElementById("filtro-extracao")?.value;
  const bicho = document.getElementById("filtro-bicho")?.value;
  const dez = document.getElementById("filtro-dezena")?.value;
  const mil = document.getElementById("filtro-milhar")?.value;
  const cabeca = document.getElementById("filtro-cabeca")?.checked;
  
  if (dIni) params.append("data_ini", dIni);
  if (dFim) params.append("data_fim", dFim);
  if (ext) params.append("extracao", ext);
  if (bicho) params.append("bicho", bicho);
  if (dez) params.append("dezena", dez);
  if (mil) params.append("milhar", mil);
  if (cabeca) params.append("so_cabeca", "true");
  
  try {
    const res = await fetch(`/api/resultados?${params.toString()}`);
    if (!res.ok) {
      tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; color: var(--danger);">Falha na resposta do servidor.</td></tr>';
      return;
    }
    const data = await res.json();
    
    tbody.innerHTML = "";
    if (data.data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; padding: 2rem; color: var(--text-muted);">Nenhum resultado encontrado para os filtros selecionados.</td></tr>';
      return;
    }
    
    totalPages = data.pages;
    const pagInfo = document.getElementById("paginacao-info");
    const btnPrev = document.getElementById("btn-prev-page");
    const btnNext = document.getElementById("btn-next-page");
    
    if (pagInfo) pagInfo.textContent = `Página ${data.page} de ${data.pages} (${data.total.toLocaleString("pt-BR")} registros encontrados)`;
    if (btnPrev) btnPrev.disabled = (currentPage <= 1);
    if (btnNext) btnNext.disabled = (currentPage >= totalPages);
    
    data.data.forEach(r => {
      const tr = document.createElement("tr");
      const isCabeca = r.premio_num === 1;
      
      tr.innerHTML = `
        <td>${r.data}</td>
        <td>${r.horario || "--:--"}</td>
        <td><strong>${r.extracao}</strong></td>
        <td>
          <span class="${isCabeca ? 'badge-premio-1' : ''}">${r.premio}</span>
        </td>
        <td class="milhar-highlight">${r.milhar}</td>
        <td>${r.centena}</td>
        <td><strong>${r.dezena}</strong></td>
        <td>${r.grupo}</td>
        <td>
          <div class="bicho-badge">
            <span class="bicho-icon">${r.icone}</span>
            <span>${r.bicho}</span>
          </div>
        </td>
        <td>${r.soma_milhar}</td>
        <td><span style="font-size: 0.75rem; color: ${r.paridade_dezena === 'PAR' ? '#38bdf8' : '#f472b6'};">${r.paridade_dezena}</span></td>
      `;
      tbody.appendChild(tr);
    });
    
  } catch (e) {
    tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; color: var(--danger);">Falha na consulta ao banco de dados.</td></tr>';
  }
}

function aplicarFiltros(page = 1) {
  carregarResultados(page);
}

function resetFiltros() {
  const elIni = document.getElementById("filtro-data-ini");
  const elFim = document.getElementById("filtro-data-fim");
  const elExt = document.getElementById("filtro-extracao");
  const elBicho = document.getElementById("filtro-bicho");
  const elDez = document.getElementById("filtro-dezena");
  const elMil = document.getElementById("filtro-milhar");
  const elCab = document.getElementById("filtro-cabeca");
  
  if (elIni) elIni.value = "";
  if (elFim) elFim.value = "";
  if (elExt) elExt.value = "";
  if (elBicho) elBicho.value = "";
  if (elDez) elDez.value = "";
  if (elMil) elMil.value = "";
  if (elCab) elCab.checked = false;
  
  carregarResultados(1);
}

function mudarPagina(delta) {
  const novaPagina = currentPage + delta;
  if (novaPagina >= 1 && novaPagina <= totalPages) {
    carregarResultados(novaPagina);
  }
}

// --------------------------------------------------------------------------
// SINCRONIZAR RESULTADOS
// --------------------------------------------------------------------------
async function sincronizarResultados() {
  const btn = document.getElementById("btn-sync");
  const icon = document.getElementById("sync-icon");
  
  if (btn) btn.disabled = true;
  if (icon) {
    icon.style.display = "inline-block";
    icon.style.animation = "spin 1s linear infinite";
  }
  
  try {
    const res = await fetch("/api/sync", { method: "POST" });
    const data = await res.json();
    
    showToast(data.mensagem || "Sincronização realizada com sucesso!");
    await carregarStatus();
    await carregarPredicoes();
    await carregarResultados(1);
  } catch (e) {
    showToast("Erro ao conectar com servidor de sincronização.", false);
  } finally {
    if (btn) btn.disabled = false;
    if (icon) icon.style.animation = "none";
  }
}

// --------------------------------------------------------------------------
// CONSULTAR PUXADAS
// --------------------------------------------------------------------------
async function consultarPuxada() {
  const select = document.getElementById("puxada-select-bicho");
  if (!select) return;
  const bicho = select.value;
  if (!bicho) return;
  
  const saidaBox = document.getElementById("puxada-saida-container");
  const entradaBox = document.getElementById("puxada-entrada-container");
  
  if (saidaBox) saidaBox.innerHTML = '<div style="color: var(--text-muted);">Calculando matriz de puxada...</div>';
  if (entradaBox) entradaBox.innerHTML = '<div style="color: var(--text-muted);">Calculando matriz de entrada...</div>';
  
  try {
    const res = await fetch(`/api/puxadas?bicho=${encodeURIComponent(bicho)}`);
    const data = await res.json();
    
    if (saidaBox) {
      saidaBox.innerHTML = "";
      data.este_bicho_puxa.forEach((p, idx) => {
        const row = document.createElement("div");
        row.className = "tier-metric";
        row.innerHTML = `
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <strong style="color: var(--text-muted); font-size: 0.8rem;">#${idx+1}</strong>
            <span class="bicho-badge"><span class="bicho-icon">${p.icone}</span> ${p.bicho} (Gr ${p.grupo})</span>
          </div>
          <div>
            <strong style="color: var(--primary);">${p.taxa}%</strong>
            <span style="font-size: 0.75rem; color: var(--text-muted);">(${p.vezes}x / ${p.lift}x do acaso)</span>
          </div>
        `;
        saidaBox.appendChild(row);
      });
    }
    
    if (entradaBox) {
      entradaBox.innerHTML = "";
      data.puxado_principalmente_por.forEach((p, idx) => {
        const row = document.createElement("div");
        row.className = "tier-metric";
        row.innerHTML = `
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <strong style="color: var(--text-muted); font-size: 0.8rem;">#${idx+1}</strong>
            <span class="bicho-badge"><span class="bicho-icon">${p.icone}</span> ${p.bicho} (Gr ${p.grupo})</span>
          </div>
          <div>
            <strong style="color: var(--accent);">${p.taxa}%</strong>
            <span style="font-size: 0.75rem; color: var(--text-muted);">(${p.vezes}x / ${p.lift}x do acaso)</span>
          </div>
        `;
        entradaBox.appendChild(row);
      });
    }
    
  } catch (e) {
    if (saidaBox) saidaBox.innerHTML = '<div style="color: var(--danger);">Erro ao consultar puxadas.</div>';
  }
}

// --------------------------------------------------------------------------
// CONFERIR APOSTAS
// --------------------------------------------------------------------------
async function conferirApostas() {
  const tipoEl = document.getElementById("conf-tipo");
  const textoEl = document.getElementById("conf-apostas");
  const resDiv = document.getElementById("conf-resultado");
  
  if (!textoEl || !textoEl.value.trim()) {
    showToast("Cole ao menos um número de aposta para conferir.", false);
    return;
  }
  
  const rawText = textoEl.value.trim();
  const apostas = rawText.split(/[\n,;\s]+/).filter(a => a.trim().length > 0);
  
  if (apostas.length === 0) {
    showToast("Nenhuma aposta válida encontrada.", false);
    return;
  }
  
  if (resDiv) {
    resDiv.style.display = "block";
    resDiv.innerHTML = '<div style="color: var(--text-muted);">Conferindo apostas contra o último resultado oficial...</div>';
  }
  
  try {
    const res = await fetch("/api/conferir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tipo: tipoEl.value,
        apostas: apostas
      })
    });
    
    if (!res.ok) {
      const err = await res.json();
      resDiv.innerHTML = `<div style="color: var(--danger);">${err.detail || 'Erro ao processar bilhete.'}</div>`;
      return;
    }
    
    const data = await res.json();
    
    let html = `
      <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 8px; padding: 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.75rem;">
          <div>
            <div style="font-size: 0.8rem; color: var(--text-muted);">Sorteio Conferido</div>
            <strong style="font-size: 1.1rem; color: #fff;">${data.sorteio_conferido}</strong>
          </div>
          <div style="text-align: right;">
            <div style="font-size: 0.8rem; color: var(--text-muted);">1º Prêmio (Cabeça)</div>
            <strong class="milhar-highlight">${data.milhar_sorteada}</strong> (${data.bicho_sorteado})
          </div>
        </div>
        
        <div style="display: flex; gap: 1.5rem; margin-bottom: 1rem; font-size: 0.95rem;">
          <div>Total de Apostas: <strong>${data.total_apostas}</strong></div>
          <div>Acertos: <strong style="color: ${data.total_acertos > 0 ? 'var(--primary)' : 'var(--text-muted)'};">${data.total_acertos}</strong></div>
          <div>Prêmio Total Estimado: <strong style="color: ${data.premio_total > 0 ? 'var(--accent-gold)' : 'var(--text-muted)'}; font-size: 1.1rem;">R$ ${data.premio_total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</strong></div>
        </div>
    `;
    
    if (data.total_acertos > 0) {
      html += `<div style="margin-top: 1rem;"><div style="font-weight: 700; margin-bottom: 0.5rem; color: var(--primary);">🎯 Bilhetes Premiados:</div>`;
      data.acertos.forEach(h => {
        html += `
          <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 6px; padding: 0.6rem 0.85rem; margin-bottom: 0.4rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong style="color: #fff; font-family: monospace; font-size: 1rem;">${h.aposta}</strong>
              <span style="color: var(--text-muted); font-size: 0.85rem; margin-left: 0.5rem;">${h.premio}</span>
            </div>
            <strong style="color: var(--primary);">+ R$ ${h.retorno_estimado.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</strong>
          </div>
        `;
      });
      html += `</div>`;
    } else {
      html += `
        <div style="color: var(--text-muted); font-size: 0.92rem; padding: 0.5rem 0;">
          Nenhum acerto premiado neste sorteio específico. Acompanhe os palpites e fechamentos da IA para o próximo horário!
        </div>
      `;
    }
    
    html += `</div>`;
    resDiv.innerHTML = html;
    
  } catch (e) {
    resDiv.innerHTML = '<div style="color: var(--danger);">Falha ao processar conferência do bilhete.</div>';
  }
}

// --------------------------------------------------------------------------
// COPIAR JOGOS
// --------------------------------------------------------------------------
function copiarTexto(elemId) {
  let text = "";
  if (elemId === "t1-dezenas") text = fullGamesCache.t1;
  else if (elemId === "t2-centenas") text = fullGamesCache.t2;
  else if (elemId === "t3-milhares") text = fullGamesCache.t3;
  else {
    const el = document.getElementById(elemId);
    if (el) text = el.textContent;
  }
  
  if (text) {
    navigator.clipboard.writeText(text).then(() => {
      showToast("Jogos copiados para a área de transferência!");
    }).catch(() => {
      showToast("Falha ao copiar jogos.", false);
    });
  }
}

// --------------------------------------------------------------------------
// FILA DE APOSTAS & CONFERÊNCIA DE CICLOS (G0 A G12)
// --------------------------------------------------------------------------
async function enviarParaFila(nivel) {
  let nome = "";
  let tipo = "";
  let apostas = [];
  let custo = 5.0;

  if (nivel === "t1") {
    nome = "Nível 1: DEZENA DINÂMICA (5 Dezenas)";
    tipo = "dezena";
    custo = 5.0;
    if (fullGamesCache.t1) {
      apostas = fullGamesCache.t1.split(/[\s,]+/).map(x => x.trim()).filter(x => x.length > 0);
    }
  } else if (nivel === "t2") {
    nome = "Nível 2: CENTENA COM PROTEÇÃO (20 Centenas)";
    tipo = "centena";
    custo = 20.0;
    if (fullGamesCache.t2) {
      apostas = fullGamesCache.t2.split(/[\n,;]+/).map(x => x.trim()).filter(x => x.length > 0);
    }
  } else if (nivel === "t3") {
    nome = "Nível 3: MILHAR FECHAMENTO 100 (100 Milhares)";
    tipo = "milhar";
    custo = 100.0;
    if (fullGamesCache.t3) {
      apostas = fullGamesCache.t3.split(/[\n,;]+/).map(x => x.trim()).filter(x => x.length > 0);
    }
  }

  if (apostas.length === 0) {
    showToast("Aguarde os palpites da IA serem gerados antes de enviar para a fila.", false);
    return;
  }

  try {
    const res = await fetch("/api/fila/adicionar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nome_estrategia: nome,
        tipo: tipo,
        apostas: apostas,
        custo_por_rodada: custo
      })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      showToast("🎯 Jogo enviado para a Fila de Monitoramento (G0 a G12)!");
      await carregarFilaApostas();
      switchTab("tab-conferidor");
    } else {
      showToast("Falha ao adicionar jogo na fila.", false);
    }
  } catch (e) {
    showToast("Erro ao comunicar com o servidor.", false);
  }
}

async function carregarFilaApostas() {
  const container = document.getElementById("container-fila-apostas");
  const countEl = document.getElementById("contagem-fila");
  if (!container) return;

  try {
    const res = await fetch("/api/fila");
    if (!res.ok) return;
    const lista = await res.json();

    if (countEl) countEl.textContent = lista.length;

    if (lista.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted);">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📥</div>
          <div style="font-size: 1.05rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.25rem;">Nenhum jogo na fila de monitoramento</div>
          <p style="font-size: 0.88rem;">Clique no botão <strong>"📥 Monitorar (G0-G12)"</strong> em qualquer palpite da IA ou use o botão <strong>"Nova Aposta Manual"</strong> acima.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = "";

    for (const aposta of lista) {
      const card = document.createElement("div");
      card.className = "card-fila-item";

      let badgeStatus = `<span class="badge-status-andamento">⏳ ${aposta.status}</span>`;
      if (aposta.status && aposta.status.includes("PREMIADO")) {
        badgeStatus = `<span class="badge-status-premiado">🏆 ${aposta.status}</span>`;
      } else if (aposta.status && aposta.status.includes("ENCERRADO")) {
        badgeStatus = `<span class="badge-status-encerrado">❌ ${aposta.status}</span>`;
      }

      const amostraNum = aposta.apostas.slice(0, 16).join(", ") + (aposta.apostas.length > 16 ? ` ... (+${aposta.apostas.length - 16} números)` : "");

      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.75rem;">
          <div>
            <div style="font-size: 1.05rem; font-weight: 800; color: var(--text-main); display: flex; align-items: center; gap: 0.5rem;">
              <span>🎫</span> ${aposta.nome_estrategia}
            </div>
            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
              Sorteio Gatilho: <strong>${aposta.data_gatilho} (${aposta.extracao_gatilho} ${aposta.horario_gatilho || ''})</strong> - ${aposta.bicho_gatilho} | Milhar: ${aposta.milhar_gatilho}
            </div>
          </div>
          <div>${badgeStatus}</div>
        </div>

        <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: 6px; padding: 0.6rem 0.85rem; font-family: var(--font-mono); font-size: 0.86rem; color: var(--accent); margin-bottom: 0.85rem; word-break: break-all;">
          ${amostraNum}
        </div>

        ${aposta.resultado_resumo ? `
          <div style="background: rgba(16,185,129,0.06); border: 1px dashed rgba(16,185,129,0.3); border-radius: 6px; padding: 0.5rem 0.85rem; font-family: var(--font-mono); font-size: 0.82rem; color: #fff; margin-bottom: 0.85rem; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <span style="color: var(--accent); font-weight: 700;">🎰 Fita de Gales:</span>
            <span>${aposta.resultado_resumo}</span>
          </div>
        ` : ''}

        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.85rem; font-size: 0.85rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.75rem;">
          <div style="display: flex; gap: 1.25rem; color: var(--text-muted);">
            <div>Custo/Rodada: <strong style="color: var(--text-main);">R$ ${Number(aposta.custo_por_rodada).toFixed(2)}</strong></div>
            <div>Sorteios Posteriores Apurados: <strong style="color: var(--accent);">${aposta.sorteios_posteriores_disponiveis} rodadas</strong></div>
          </div>

          <div style="display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;">
            <select id="select-sorteio-${aposta.id_aposta}" style="padding: 0.45rem 0.65rem; border-radius: 6px; background: rgba(0,0,0,0.5); border: 1px solid var(--border); color: #fff; font-size: 0.82rem;">
              <option value="">⚡ Ciclo Completo (G0 a G12)</option>
            </select>

            <button class="btn-filter" style="padding: 0.45rem 0.95rem; font-size: 0.82rem;" onclick="dispararConferencia(${aposta.id_aposta})">
              <span>🔍</span> Conferir
            </button>

            <button class="btn-reset" style="padding: 0.45rem 0.65rem; font-size: 0.82rem; color: var(--danger); border-color: rgba(244,63,94,0.3);" onclick="removerJogoFila(${aposta.id_aposta})" title="Excluir Jogo da Fila">
              <span>🗑️</span>
            </button>
          </div>
        </div>
      `;

      container.appendChild(card);
      preencherSelectSorteios(aposta.id_aposta);
    }
  } catch (e) {
    console.error("Erro ao carregar fila:", e);
  }
}

async function preencherSelectSorteios(idAposta) {
  const sel = document.getElementById(`select-sorteio-${idAposta}`);
  if (!sel) return;

  try {
    const res = await fetch(`/api/fila/${idAposta}/sorteios-posteriores`);
    if (!res.ok) return;
    const sorteios = await res.json();

    sorteios.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.id_sorteio;
      opt.textContent = `${s.gale_tag} (Rodada ${s.rodada_num}) - ${s.data} ${s.extracao} (${s.bicho})`;
      sel.appendChild(opt);
    });
  } catch (e) {
    console.error("Erro ao carregar sorteios posteriores:", e);
  }
}

function dispararConferencia(idAposta) {
  const sel = document.getElementById(`select-sorteio-${idAposta}`);
  const idSorteioAlvo = sel && sel.value ? parseInt(sel.value) : null;
  conferirCiclo(idAposta, idSorteioAlvo);
}

function renderizarFitaRibbon(lista) {
  if (!lista || lista.length === 0) {
    return '<span style="color: var(--text-muted); font-size: 0.85rem;">Nenhuma rodada apurada ainda.</span>';
  }
  let html = '';
  lista.forEach((item, i) => {
    if (item.tipo === "divisor_24h") {
      html += `
        <span class="fita-seta">➔</span>
        <span class="badge-divisor-24h" title="Transição para o próximo dia (Ciclo 24h)">${item.rotulo}</span>
        <span class="fita-seta">➔</span>
      `;
    } else {
      if (i > 0 && lista[i-1].tipo !== "divisor_24h") {
        html += `<span class="fita-seta">➔</span>`;
      }
      let nClass = "notacao-0";
      if (item.notacao && item.notacao.includes("M")) nClass = "notacao-1m";
      else if (item.notacao && item.notacao.includes("C")) nClass = "notacao-1c";
      else if (item.notacao && item.notacao.includes("D")) nClass = "notacao-1d";
      else if (item.notacao && item.notacao.includes("G")) nClass = "notacao-1g";

      html += `
        <div class="fita-item-box" title="${item.gale} (${item.rodada}ª Rodada) - ${item.acertou ? 'Premiado' : 'Sem acerto'}">
          <span class="fita-item-gale">${item.gale}</span>
          <span class="badge-notacao ${nClass}">${item.notacao}</span>
        </div>
      `;
    }
  });
  return html;
}

async function conferirCiclo(idAposta, idSorteioAlvo = null) {
  const painel = document.getElementById("painel-auditoria-ciclo");
  if (!painel) return;

  painel.style.display = "block";
  painel.innerHTML = '<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Processando auditoria de ciclo multi-rodadas (G0 a G12)...</div>';
  painel.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const res = await fetch(`/api/fila/${idAposta}/conferir`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_sorteio_alvo: idSorteioAlvo })
    });

    if (!res.ok) {
      painel.innerHTML = '<div style="color: var(--danger); padding: 1.5rem;">Falha ao conferir ciclo de aposta.</div>';
      return;
    }

    const data = await res.json();

    let bannerClass = data.ciclo_premiado ? "badge-status-premiado" : "badge-status-andamento";
    let bannerTitle = data.ciclo_premiado
      ? `🎉 PREMIADO NO ${data.gale_vencedor} (${data.rodadas_necessarias}ª Rodada)!`
      : (data.total_rodadas_verificadas === 0 ? "⏳ AGUARDANDO NOVAS APURAÇÕES" : `⏳ EM ANDAMENTO - ${data.total_rodadas_verificadas} Rodadas Verificadas`);

    let html = `
      <div class="card-header" style="border-bottom: 1px solid var(--border); padding-bottom: 0.85rem; margin-bottom: 1rem;">
        <div>
          <div style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700;">Auditoria de Ciclo & Gestão de Gales</div>
          <div style="font-size: 1.25rem; font-weight: 800; color: #fff; margin-top: 0.2rem;">
            ${data.nome_estrategia}
          </div>
          <div style="font-size: 0.85rem; color: var(--text-muted);">
            Sorteio Gatilho: <strong>${data.gatilho.data} (${data.gatilho.extracao})</strong> - ${data.gatilho.bicho} (Milhar: ${data.gatilho.milhar})
          </div>
        </div>
        <span class="${bannerClass}" style="font-size: 0.95rem; padding: 0.45rem 0.9rem;">${bannerTitle}</span>
      </div>

      <!-- Scorecard Financeiro do Ciclo -->
      <div class="scorecard-ciclo">
        <div class="score-box">
          <span>Rodadas Necessárias</span>
          <strong style="color: ${data.ciclo_premiado ? '#10b981' : '#38bdf8'};">
            ${data.ciclo_premiado ? `${data.gale_vencedor} (${data.rodadas_necessarias}ª Rodada)` : `${data.total_rodadas_verificadas} Rodadas`}
          </strong>
        </div>
        <div class="score-box">
          <span>Investimento Total</span>
          <strong style="color: var(--text-main);">R$ ${Number(data.custo_total_acumulado).toFixed(2)}</strong>
        </div>
        <div class="score-box">
          <span>Prêmio Total Bruto</span>
          <strong style="color: #fbbf24;">R$ ${Number(data.premio_total_acumulado).toFixed(2)}</strong>
        </div>
        <div class="score-box" style="border-color: ${data.saldo_liquido > 0 ? 'rgba(16,185,129,0.4)' : 'rgba(244,63,94,0.4)'};">
          <span>Saldo Líquido Real</span>
          <strong style="color: ${data.saldo_liquido > 0 ? '#10b981' : '#f43f5e'};">
            ${data.saldo_liquido >= 0 ? '+' : ''} R$ ${Number(data.saldo_liquido).toFixed(2)}
          </strong>
        </div>
      </div>

      <!-- Fita Progressiva Registrada (Ribbon Visual) -->
      <div style="margin-top: 1.25rem; background: rgba(0,0,0,0.35); border: 1px solid var(--border); border-radius: 8px; padding: 1rem 1.25rem;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.75rem;">
          <div style="font-weight: 800; font-size: 0.95rem; color: #fff; display: flex; align-items: center; gap: 0.5rem;">
            <span>🎰</span> Registro Progressivo nos Gales (Catálogo de Acertos):
          </div>
          <div style="font-size: 0.8rem; color: var(--text-muted);">
            Auditoria Rodada a Rodada & Ciclo 24h
          </div>
        </div>
        
        <div class="fita-ribbon-container" style="margin: 0; background: transparent; border: none; padding: 0;">
          ${renderizarFitaRibbon(data.fita_progressiva_lista)}
        </div>

        <div style="display: flex; gap: 1.25rem; flex-wrap: wrap; margin-top: 0.85rem; padding-top: 0.65rem; border-top: 1px solid rgba(255,255,255,0.06); font-size: 0.8rem; color: var(--text-muted);">
          <div>Acertos de Milhar: <strong style="color: #fde047;">${data.totais_catalogo ? data.totais_catalogo.milhar_m : 0} (1M)</strong></div>
          <div>Acertos de Centena: <strong style="color: #38bdf8;">${data.totais_catalogo ? data.totais_catalogo.centena_c : 0} (1C)</strong></div>
          <div>Acertos de Dezena: <strong style="color: #34d399;">${data.totais_catalogo ? data.totais_catalogo.dezena_d : 0} (1D)</strong></div>
          <div>Rodadas sem Acerto: <strong style="color: #94a3b8;">${data.totais_catalogo ? data.totais_catalogo.erros_zero : 0} (0)</strong></div>
        </div>
      </div>
    `;

    if (data.rodadas.length > 0) {
      html += `
        <div style="margin-top: 1.5rem;">
          <div style="font-weight: 800; font-size: 1rem; margin-bottom: 0.75rem; color: var(--text-main);">
            📊 Detalhamento Rodada a Rodada (Evolução do Ciclo):
          </div>
          <div class="stepper-timeline">
      `;

      data.rodadas.forEach((r, idx) => {
        const isWin = r.acertou;
        let badgeNotacaoClass = "notacao-0";
        if (r.notacao && r.notacao.includes("M")) badgeNotacaoClass = "notacao-1m";
        else if (r.notacao && r.notacao.includes("C")) badgeNotacaoClass = "notacao-1c";
        else if (r.notacao && r.notacao.includes("D")) badgeNotacaoClass = "notacao-1d";
        else if (r.notacao && r.notacao.includes("G")) badgeNotacaoClass = "notacao-1g";

        const diaBadgeClass = r.dia_badge && r.dia_badge.includes("Dia 2") ? "badge-dia-2" : "badge-dia-1";

        if (idx === 6) {
          html += `
            <div style="text-align: center; margin: 1.25rem 0 0.85rem;">
              <span class="badge-divisor-24h">🌙 Transição para o Ciclo de 24h (2º Dia • Sorteios 7 a 12 • Abertura PPT 09:20)</span>
            </div>
          `;
        }

        html += `
          <div class="step-card ${isWin ? 'step-win' : ''}">
            <div style="display: flex; align-items: center; gap: 0.85rem; flex-wrap: wrap;">
              <div style="display: flex; align-items: center; gap: 0.4rem;">
                <span class="gale-pill">${r.gale} (Rodada ${r.rodada})</span>
                <span class="badge-dia ${diaBadgeClass}">${r.dia_badge}</span>
                <span class="badge-notacao ${badgeNotacaoClass}">${r.notacao}</span>
              </div>
              <div>
                <strong style="color: #fff;">${r.data} (${r.extracao} ${r.horario})</strong>
                <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.15rem;">
                  1º Prêmio: <strong class="milhar-highlight">${r.milhar_cabeca}</strong> (${r.bicho_cabeca})
                </div>
              </div>
            </div>

            <div style="text-align: right;">
              <div style="font-size: 0.82rem; color: var(--text-muted);">
                Custo Acumulado: <strong>R$ ${Number(r.custo_acumulado).toFixed(2)}</strong>
              </div>
              <div style="margin-top: 0.2rem;">
                ${isWin 
                  ? `<strong style="color: #10b981; font-size: 1.05rem;">🎉 PREMIADO (+ R$ ${Number(r.premio_rodada).toFixed(2)})</strong>` 
                  : `<span style="color: var(--text-muted); font-size: 0.85rem;">Sem acerto nesta rodada</span>`
                }
              </div>
            </div>
          </div>
        `;
      });

      html += `</div></div>`;
    } else {
      html += `
        <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
          Ainda não foram apurados sorteios posteriores ao gatilho deste jogo. Clique em <strong>"Sincronizar Próximos Resultados"</strong> para checar novas extrações.
        </div>
      `;
    }

    painel.innerHTML = html;
    await carregarFilaApostas();

  } catch (e) {
    painel.innerHTML = '<div style="color: var(--danger); padding: 1.5rem;">Erro de conexão ao conferir aposta.</div>';
  }
}

async function removerJogoFila(idAposta) {
  if (!confirm("Deseja realmente remover este jogo da fila de monitoramento?")) return;

  try {
    const res = await fetch(`/api/fila/${idAposta}`, { method: "DELETE" });
    if (res.ok) {
      showToast("Jogo removido da fila com sucesso.");
      await carregarFilaApostas();
      const painel = document.getElementById("painel-auditoria-ciclo");
      if (painel) painel.style.display = "none";
    }
  } catch (e) {
    showToast("Erro ao excluir jogo.", false);
  }
}

async function sincronizarFilaEAtualizar() {
  const icon = document.getElementById("sync-fila-icon");
  if (icon) icon.style.animation = "spin 1s linear infinite";

  try {
    const res = await fetch("/api/sync", { method: "POST" });
    const data = await res.json();
    showToast(data.mensagem || "Resultados sincronizados com sucesso!");
    await carregarStatus();
    await carregarFilaApostas();
    await carregarResultados(1);
    await carregarPredicoes();
  } catch (e) {
    showToast("Erro ao sincronizar resultados.", false);
  } finally {
    if (icon) icon.style.animation = "none";
  }
}

function toggleSecaoNovaAposta() {
  const secao = document.getElementById("secao-nova-aposta");
  if (!secao) return;
  secao.style.display = secao.style.display === "none" ? "block" : "none";
}

async function salvarNovaApostaManual(event) {
  if (event) event.preventDefault();

  const nome = document.getElementById("manual-nome")?.value.trim() || "Aposta Manual";
  const tipo = document.getElementById("manual-tipo")?.value || "dezena";
  const custo = parseFloat(document.getElementById("manual-custo")?.value || 5.0);
  const rawText = document.getElementById("manual-apostas")?.value.trim() || "";

  const apostas = rawText.split(/[\n,;\s]+/).map(a => a.trim()).filter(a => a.length > 0);

  if (apostas.length === 0) {
    showToast("Informe ao menos um número de aposta.", false);
    return;
  }

  try {
    const res = await fetch("/api/fila/adicionar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        nome_estrategia: nome,
        tipo: tipo,
        apostas: apostas,
        custo_por_rodada: custo
      })
    });

    if (res.ok) {
      showToast("Aposta manual inserida na fila com sucesso!");
      toggleSecaoNovaAposta();
      document.getElementById("form-nova-aposta")?.reset();
      await carregarFilaApostas();
    } else {
      showToast("Erro ao salvar aposta.", false);
    }
  } catch (e) {
    showToast("Erro de conexão.", false);
  }
}

async function carregarEstatisticasCiclos() {
  const containerDicas = document.getElementById("container-dicas-filtros-ciclos");
  const tbody = document.getElementById("tabela-maturacao-body");

  try {
    const res = await fetch("/api/ciclos/estatisticas");
    if (!res.ok) return;
    const data = await res.json();

    if (containerDicas && data.recomendacoes_filtros) {
      containerDicas.innerHTML = "";
      data.recomendacoes_filtros.forEach(r => {
        const card = document.createElement("div");
        card.className = "card";
        card.style.background = "rgba(0,0,0,0.3)";
        card.style.border = "1px solid var(--border)";
        card.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <div style="font-weight: 800; font-size: 0.95rem; color: #fff;">${r.titulo}</div>
            <span class="card-badge badge-green">${r.tag}</span>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.5rem; line-height: 1.4;">${r.descricao}</p>
          <div style="font-size: 0.82rem; color: var(--accent); font-weight: 700;">Cobertura Estatística: ${r.taxa_cobertura}</div>
        `;
        containerDicas.appendChild(card);
      });
    }

    if (tbody && data.curva_maturacao) {
      tbody.innerHTML = "";
      data.curva_maturacao.forEach(g => {
        const tr = document.createElement("tr");
        const isOptimal = ["G0", "G1", "G2", "G3"].includes(g.gale);
        const diaClass = g.is_dia_2 ? "badge-dia-2" : "badge-dia-1";
        
        let notacaoHtml = `
          <div style="display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;">
            <span class="badge-dia ${diaClass}">${g.dia_badge}</span>
            <span style="font-family: var(--font-mono); font-size: 0.82rem; font-weight: 700; color: #fff;">
              ${g.notacao_sequencia}
            </span>
            ${g.is_repique_24h ? `<span class="badge-repique">⚡ +62% REPIQUE</span>` : ''}
          </div>
          <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.2rem;">
            <strong style="color: ${isOptimal ? '#34d399' : 'var(--accent)'};">${g.notacao_desc}</strong> • <em>${g.notacao_detalhe}</em>
          </div>
        `;

        tr.innerHTML = `
          <td><strong style="color: ${isOptimal ? 'var(--primary)' : 'var(--text-main)'}; font-family: var(--font-mono);">${g.gale}</strong></td>
          <td>${g.rodada}ª Rodada</td>
          <td>${g.acertos.toLocaleString("pt-BR")} acertos</td>
          <td><strong style="color: var(--accent);">${g.taxa_individual}%</strong></td>
          <td><strong style="color: #10b981;">${g.taxa_acumulada}%</strong></td>
          <td>${notacaoHtml}</td>
          <td>
            <span style="font-size: 0.78rem; color: ${isOptimal ? '#10b981' : (g.is_repique_24h ? '#38bdf8' : 'var(--text-muted)')}; font-weight: ${isOptimal || g.is_repique_24h ? '700' : '400'};">
              ${g.avaliacao}
            </span>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (e) {
    console.error("Erro ao carregar estatísticas de ciclos:", e);
  }
}

// --------------------------------------------------------------------------
// PILOTO AUTOMÁTICO & AUDITORIA DE ASSERTIVIDADE DE LONGO PRAZO
// --------------------------------------------------------------------------
async function carregarStatusAutoPilot() {
  try {
    const res = await fetch("/api/autopilot/status");
    if (!res.ok) return;
    const data = await res.json();

    const elHeaderProx = document.getElementById("header-proxima-extracao");
    const elTexto = document.getElementById("autopilot-status-texto");
    const elUltima = document.getElementById("autopilot-ultima-varredura");
    const elProx = document.getElementById("autopilot-proxima-extracao");
    const elTotal = document.getElementById("autopilot-total-varreduras");

    if (elHeaderProx) elHeaderProx.textContent = data.proxima_extracao;
    if (elTexto) elTexto.textContent = data.status_operacional;
    if (elUltima) elUltima.textContent = data.ultima_checagem;
    if (elProx) elProx.textContent = data.proxima_extracao;
    if (elTotal) elTotal.textContent = `${data.total_varreduras} varreduras`;
  } catch (e) {
    console.error("Erro ao carregar status do piloto automático:", e);
  }
}

async function carregarMonitoramentoAssertividade() {
  const containerRegime = document.getElementById("container-regime-ia");
  const elTaxaGlobal = document.getElementById("metric-taxa-global");
  const elTaxaEst = document.getElementById("metric-taxa-estimada");
  const elDesvio = document.getElementById("metric-desvio");
  const elTaxa24h = document.getElementById("metric-taxa-24h");
  const elTaxaCabeca = document.getElementById("metric-taxa-cabeca");
  const elTaxaCercado = document.getElementById("metric-taxa-cercado");
  const elTotalAudit = document.getElementById("metric-total-auditados");
  const tbody = document.getElementById("tabela-auditoria-body");

  try {
    const res = await fetch("/api/assertividade/monitoramento");
    if (!res.ok) return;
    const data = await res.json();

    const reg = data.regime_ia;
    const resGeral = data.resumo_geral;

    if (containerRegime && reg) {
      containerRegime.className = `regime-card ${reg.classe}`;
      containerRegime.innerHTML = `
        <div>
          <div style="font-size: 0.8rem; text-transform: uppercase; font-weight: 800; color: ${reg.cor}; letter-spacing: 0.5px;">
            Diagnóstico de Regime & Calibração Automática
          </div>
          <div style="font-size: 1.3rem; font-weight: 800; color: #fff; margin: 0.2rem 0;">
            ${reg.titulo}
          </div>
          <p style="font-size: 0.88rem; color: var(--text-muted); margin: 0.25rem 0 0.5rem; line-height: 1.4;">
            ${reg.descricao}
          </p>
          <div style="font-size: 0.84rem; color: #fff; font-weight: 600;">
            <span style="color: ${reg.cor}; font-weight: 800;">Ajuste Ativo:</span> ${reg.recomendacao}
          </div>
        </div>
        <div style="text-align: right;">
          <div style="font-size: 0.78rem; color: var(--text-muted);">Assertividade nas Últimas 24h</div>
          <div style="font-size: 2.2rem; font-weight: 900; color: ${reg.cor}; line-height: 1;">
            ${resGeral.taxa_recente_24h}%
          </div>
          <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.2rem;">
            vs ${resGeral.taxa_estimada_media}% nominal
          </div>
        </div>
      `;
    }

    const desvioVal = (resGeral.taxa_real_global - resGeral.taxa_estimada_media).toFixed(1);
    const desvioStr = desvioVal >= 0 ? `+${desvioVal}% (Convergência Alta)` : `${desvioVal}%`;

    if (elTaxaGlobal) elTaxaGlobal.textContent = `${resGeral.taxa_real_global}%`;
    if (elTaxaEst) elTaxaEst.textContent = `${resGeral.taxa_estimada_media}%`;
    if (elDesvio) elDesvio.textContent = desvioStr;
    if (elTaxa24h) elTaxa24h.textContent = `${resGeral.taxa_recente_24h}%`;
    if (elTaxaCabeca) elTaxaCabeca.textContent = `${resGeral.taxa_real_cabeca}%`;
    if (elTaxaCercado) elTaxaCercado.textContent = `${resGeral.taxa_real_cercado}%`;
    if (elTotalAudit) elTotalAudit.textContent = `${resGeral.total_auditados} extrações`;

    if (tbody && data.historico_auditorias) {
      tbody.innerHTML = "";
      data.historico_auditorias.forEach(h => {
        const tr = document.createElement("tr");
        const isWin = h.status_auditoria === "CONFERIDO_PREMIADO";
        
        let notacaoClass = "notacao-0";
        if (h.notacao_rodada && h.notacao_rodada.includes("M")) notacaoClass = "notacao-1m";
        else if (h.notacao_rodada && h.notacao_rodada.includes("C")) notacaoClass = "notacao-1c";
        else if (h.notacao_rodada && h.notacao_rodada.includes("D")) notacaoClass = "notacao-1d";

        const dezenasPrev = h.dezenas_sugeridas ? h.dezenas_sugeridas.slice(0, 5).join(", ") : "--";

        tr.innerHTML = `
          <td>
            <strong style="color: #fff;">${h.data_gatilho}</strong>
            <div style="font-size: 0.78rem; color: var(--text-muted);">${h.extracao_gatilho} ${h.horario_gatilho || ''} (${h.bicho_gatilho || ''})</div>
          </td>
          <td>
            <strong style="color: var(--accent);">${h.extracao_apuracao || 'Pendente'}</strong>
            <div style="font-size: 0.78rem; color: var(--text-muted);">${h.data_apuracao || ''} ${h.horario_apuracao || ''}</div>
          </td>
          <td>
            <span style="font-family: var(--font-mono); color: #fff; font-size: 0.85rem; font-weight: 700;">${dezenasPrev}</span>
          </td>
          <td>
            ${h.apurado 
              ? `<span style="font-family: var(--font-mono); font-weight: 800; color: #fff;">${h.milhar_apurado}</span> <span style="font-size: 0.8rem; color: var(--text-muted);">(${h.bicho_apurado})</span>` 
              : `<span style="color: var(--text-muted);">Aguardando apuração...</span>`}
          </td>
          <td>
            <span class="badge-notacao ${notacaoClass}">${h.notacao_rodada}</span>
            ${h.detalhes_acertos && h.detalhes_acertos.length > 0 ? `
              <div style="font-size: 0.72rem; color: #34d399; margin-top: 0.2rem;">${h.detalhes_acertos[0]}</div>
            ` : ''}
          </td>
          <td>
            <span class="${isWin ? 'badge-status-premiado' : (h.apurado ? 'badge-status-encerrado' : 'badge-status-andamento')}">
              ${isWin ? '🏆 PREMIADO' : (h.apurado ? '0 (SEM ACERTO)' : '⏳ AGUARDANDO')}
            </span>
          </td>
          <td style="font-size: 0.8rem; color: var(--text-muted);">
            ${h.criado_em}
          </td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (e) {
    console.error("Erro ao carregar monitoramento de assertividade:", e);
  }
}

async function executarCicloAutoPilotAgora() {
  const btn = document.getElementById("btn-force-autopilot");
  if (btn) btn.disabled = true;
  showToast("Executando varredura e auditoria automática agora...");

  try {
    const res = await fetch("/api/autopilot/executar", { method: "POST" });
    if (res.ok) {
      const data = await res.json();
      showToast(`Varredura concluída: ${data.novos_registros} novos registros. ${data.auditorias_processadas} auditorias.`);
      await carregarStatus();
      await carregarStatusAutoPilot();
      await carregarMonitoramentoAssertividade();
      await carregarPredicoes();
      await carregarFilaApostas();
    } else {
      showToast("Falha ao executar ciclo do piloto automático.", false);
    }
  } catch (e) {
    showToast("Erro de comunicação.", false);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// --------------------------------------------------------------------------
// EVENT LISTENERS DE INICIALIZAÇÃO
// --------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  carregarTemaSalvo();
  checkAuth();
});

window.addEventListener("load", () => {
  const token = localStorage.getItem(AUTH_TOKEN_KEY);
  if (token) {
    const el = document.getElementById("stat-total-sorteios");
    if (el && el.textContent === "...") {
      initApp();
    }
  }
});



// ==========================================================================
// MÓDULO: COMO JOGAR NO JOGO DO BICHO - AULA MATEMÁTICA DU ZAZÁ
// ==========================================================================
let zazaSorteioAtual = "aula_zaza";
let zazaDadosAula = null;
let zazaRegras = {};
let zazaBichos = [];
let zazaExemplos = [];
let zazaSorteioAtivo = [];

async function carregarModuloZaza() {
  try {
    const res = await fetch("/api/regras-apostas");
    if (!res.ok) return;
    const data = await res.json();
    zazaDadosAula = data;
    zazaRegras = data.regras || {};
    zazaBichos = data.bichos || [];
    zazaExemplos = data.exemplos_aula || [];
    zazaSorteioAtivo = data.sorteio_aula || [];

    renderizarSorteioAtivoZaza();
    renderizarExemplosZaza();
    renderizarCardsRegrasZaza();
    renderizarBichosZaza();
    atualizarInterfaceModalidadeZaza();
  } catch (e) {
    console.error("Erro ao carregar módulo do Zazá:", e);
  }
}

function carregarSorteioAulaZaza() {
  zazaSorteioAtual = "aula_zaza";
  if (zazaDadosAula && zazaDadosAula.sorteio_aula) {
    zazaSorteioAtivo = zazaDadosAula.sorteio_aula;
  }
  const titleEl = document.getElementById("zaza-sorteio-titulo");
  const badgeEl = document.getElementById("zaza-sorteio-badge");
  if (titleEl) titleEl.textContent = "Exemplo Hipotético da Aula (Prof. Zazá)";
  if (badgeEl) {
    badgeEl.textContent = "Aula Matemática du Zazá";
    badgeEl.style.borderColor = "#f59e0b";
    badgeEl.style.color = "#f59e0b";
  }
  renderizarSorteioAtivoZaza();
  showToast("🎓 Sorteio da aula do Professor Zazá ativo!");
}

async function carregarUltimoSorteioRealZaza() {
  try {
    const res = await fetch("/api/resultados?page=1&page_size=10");
    if (!res.ok) return;
    const data = await res.json();
    if (!data.data || data.data.length === 0) {
      showToast("Nenhum sorteio registrado na base.", false);
      return;
    }
    
    const idPrimeiro = data.data[0].id_sorteio;
    const premiosReal = data.data.filter(r => r.id_sorteio === idPrimeiro).slice(0, 5);
    
    zazaSorteioAtual = "ultimo";
    zazaSorteioAtivo = premiosReal.map(r => ({
      premio: r.premio,
      premio_num: r.premio_num,
      milhar: r.milhar,
      centena: r.centena,
      dezena: r.dezena,
      grupo: r.grupo,
      bicho: r.bicho,
      icone: r.icone
    }));

    const titleEl = document.getElementById("zaza-sorteio-titulo");
    const badgeEl = document.getElementById("zaza-sorteio-badge");
    if (titleEl) titleEl.textContent = `Último Sorteio Oficial: ${premiosReal[0].data} (${premiosReal[0].extracao})`;
    if (badgeEl) {
      badgeEl.textContent = "Base Oficial Deu no Poste";
      badgeEl.style.borderColor = "var(--primary)";
      badgeEl.style.color = "var(--primary)";
    }
    renderizarSorteioAtivoZaza();
    showToast("🔄 Último sorteio real da base carregado!");
  } catch (e) {
    showToast("Falha ao buscar sorteio real.", false);
  }
}

function renderizarSorteioAtivoZaza() {
  const container = document.getElementById("zaza-draw-container");
  if (!container || !zazaSorteioAtivo) return;

  container.innerHTML = zazaSorteioAtivo.map((p, idx) => {
    const isCabeca = p.premio_num === 1;
    return `
      <div class="zaza-prize-card ${isCabeca ? 'cabeca' : ''}">
        <div class="premio-label">
          <span>${p.premio}</span>
          ${isCabeca ? '<span class="card-badge badge-gold" style="font-size: 0.65rem; padding: 0.1rem 0.4rem;">CABEÇA</span>' : ''}
        </div>
        <div class="milhar-val">${p.milhar}</div>
        <div class="bicho-val">
          <span style="font-size: 1.15rem;">${p.icone || '🎲'}</span>
          <strong>${p.bicho}</strong>
          <span style="color: var(--text-muted); font-size: 0.78rem;">(G${p.grupo})</span>
        </div>
        <div class="breakdown">
          <span>Centena: <strong style="color: #fff;">${p.centena}</strong></span>
          <span>•</span>
          <span>Dezena: <strong style="color: var(--accent-gold);">${p.dezena}</strong></span>
        </div>
      </div>
    `;
  }).join("");
}

function renderizarExemplosZaza() {
  const container = document.getElementById("zaza-exemplos-buttons");
  if (!container || !zazaExemplos) return;

  container.innerHTML = zazaExemplos.map(ex => `
    <button type="button" class="zaza-ex-btn" id="btn-ex-${ex.id}" onclick="selecionarExemploZaza('${ex.id}')">
      <div class="ex-title">
        <span>${ex.titulo}</span>
        <span class="ex-mult">${ex.mult_esperado}x</span>
      </div>
      <div class="ex-desc">${ex.explicacao}</div>
    </button>
  `).join("");
}

async function selecionarExemploZaza(exId) {
  const ex = zazaExemplos.find(e => e.id === exId);
  if (!ex) return;

  if (zazaSorteioAtual !== "aula_zaza") {
    carregarSorteioAulaZaza();
  }

  document.querySelectorAll(".zaza-ex-btn").forEach(b => b.classList.remove("active"));
  const btn = document.getElementById(`btn-ex-${exId}`);
  if (btn) btn.classList.add("active");

  const tipoEl = document.getElementById("zaza-tipo");
  const posEl = document.getElementById("zaza-posicao");
  const valEl = document.getElementById("zaza-valor");
  const apoEl = document.getElementById("zaza-apostas");

  if (tipoEl) tipoEl.value = ex.tipo;
  if (posEl) posEl.value = ex.posicao;
  if (valEl) valEl.value = ex.valor.toFixed(2);
  if (apoEl) apoEl.value = ex.aposta;

  atualizarInterfaceModalidadeZaza();
  await executarConferenciaZaza();
}

function atualizarInterfaceModalidadeZaza() {
  const tipo = document.getElementById("zaza-tipo")?.value || "grupo";
  const regra = zazaRegras[tipo];
  const groupPos = document.getElementById("group-posicao-zaza");
  const labelApostas = document.getElementById("zaza-label-apostas");
  const hintApostas = document.getElementById("zaza-hint-apostas");
  const infoRegra = document.getElementById("zaza-info-regra-resumo");

  if (!regra) return;

  if (groupPos) {
    if (!regra.suporta_cabeca) {
      groupPos.style.opacity = "0.5";
      groupPos.style.pointerEvents = "none";
      const selPos = document.getElementById("zaza-posicao");
      if (selPos) selPos.value = "cercado";
    } else {
      groupPos.style.opacity = "1";
      groupPos.style.pointerEvents = "auto";
    }
  }

  if (tipo === "grupo") {
    if (labelApostas) labelApostas.textContent = "Animal / Grupo Escolhido";
    if (hintApostas) hintApostas.textContent = "Ex: Tigre ou 22";
    if (infoRegra) infoRegra.textContent = "Regra da aula: 18x na cabeça ou 3,6x do 1º ao 5º prêmio (18 ÷ 5 = 3,6x).";
  } else if (tipo === "dezena") {
    if (labelApostas) labelApostas.textContent = "Dezena Escolhida (2 algarismos)";
    if (hintApostas) hintApostas.textContent = "Ex: 87 (ou várias separadas por vírgula)";
    if (infoRegra) infoRegra.textContent = "Regra da aula: 60x na cabeça ou 12x do 1º ao 5º prêmio (60 ÷ 5 = 12x).";
  } else if (tipo === "centena") {
    if (labelApostas) labelApostas.textContent = "Centena Escolhida (3 algarismos)";
    if (hintApostas) hintApostas.textContent = "Ex: 587";
    if (infoRegra) infoRegra.textContent = "Regra da aula: 600x na cabeça ou 120x do 1º ao 5º prêmio (600 ÷ 5 = 120x).";
  } else if (tipo === "milhar") {
    if (labelApostas) labelApostas.textContent = "Milhar Escolhida (4 algarismos)";
    if (hintApostas) hintApostas.textContent = "Ex: 1587";
    if (infoRegra) infoRegra.textContent = "Regra da aula: 4.000x na cabeça ou 800x do 1º ao 5º prêmio (4000 ÷ 5 = 800x).";
  } else if (tipo === "duque_grupo") {
    if (labelApostas) labelApostas.textContent = "2 Animais para Duque de Grupo";
    if (hintApostas) hintApostas.textContent = "Ex: Cavalo e Galo (ou 11 e 13)";
    if (infoRegra) infoRegra.textContent = "Regra da aula: 18,5x se ambos saírem entre os 5 prêmios (ordem irrelevante).";
  } else if (tipo === "duque_dezena") {
    if (labelApostas) labelApostas.textContent = "2 Dezenas para Duque de Dezenas";
    if (hintApostas) hintApostas.textContent = "Ex: 44 e 23";
    if (infoRegra) infoRegra.textContent = "Regra da aula: 300x se ambas as dezenas saírem entre os 5 prêmios.";
  } else if (tipo === "terno_grupo") {
    if (labelApostas) labelApostas.textContent = "3 Animais para Terno de Grupo";
    if (hintApostas) hintApostas.textContent = "Ex: Cabra, Tigre e Pavão";
    if (infoRegra) infoRegra.textContent = "Regra da aula: 130x se os 3 animais saírem entre os 5 prêmios.";
  } else if (tipo === "terno_dezena") {
    if (labelApostas) labelApostas.textContent = "3 Dezenas para Terno de Dezenas";
    if (hintApostas) hintApostas.textContent = "Ex: 87, 52 e 75";
    if (infoRegra) infoRegra.textContent = "Regra da aula: 3.000x se as 3 dezenas saírem entre os 5 prêmios.";
  }

  atualizarMultiplicadorDisplayZaza();
}

function atualizarMultiplicadorDisplayZaza() {
  const tipo = document.getElementById("zaza-tipo")?.value || "grupo";
  const pos = document.getElementById("zaza-posicao")?.value || "cabeca";
  const valor = parseFloat(document.getElementById("zaza-valor")?.value || 10.0);
  const display = document.getElementById("zaza-display-mult");
  const regra = zazaRegras[tipo];

  if (!display || !regra) return;

  let mult = 0;
  if (!regra.suporta_cabeca || pos === "cercado") {
    mult = regra.mult_cercado;
  } else {
    mult = regra.mult_cabeca;
  }

  const retornoUnitario = valor * mult;
  display.innerHTML = `<span>${mult}x</span> <span style="font-size: 0.88rem; color: var(--text-muted); font-weight: 500;">(Retorno: <strong style="color: var(--primary);">R$ ${retornoUnitario.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</strong>)</span>`;
}

function setValorApostaZaza(val) {
  const input = document.getElementById("zaza-valor");
  if (input) {
    input.value = Number(val).toFixed(2);
    atualizarMultiplicadorDisplayZaza();
  }
}

function limparSimuladorZaza() {
  const inputApostas = document.getElementById("zaza-apostas");
  if (inputApostas) inputApostas.value = "";
  const resDiv = document.getElementById("zaza-resultado-container");
  if (resDiv) resDiv.style.display = "none";
  document.querySelectorAll(".zaza-ex-btn").forEach(b => b.classList.remove("active"));
}

function selecionarBichoParaAposta(grupoNum, bichoNome) {
  const tipo = document.getElementById("zaza-tipo")?.value || "grupo";
  const txt = document.getElementById("zaza-apostas");
  if (!txt) return;

  if (tipo === "grupo") {
    txt.value = bichoNome;
  } else if (tipo === "duque_grupo" || tipo === "terno_grupo") {
    if (!txt.value.trim()) {
      txt.value = bichoNome;
    } else {
      txt.value += ` e ${bichoNome}`;
    }
  } else {
    const bicho = zazaBichos.find(b => b.grupo === grupoNum);
    if (bicho && bicho.dezenas) {
      txt.value = bicho.dezenas.join(", ");
    }
  }
  showToast(`${bichoNome} selecionado!`);
  atualizarMultiplicadorDisplayZaza();
}

async function submeterConferenciaZaza(e) {
  if (e) e.preventDefault();
  await executarConferenciaZaza();
}

async function executarConferenciaZaza() {
  const tipo = document.getElementById("zaza-tipo")?.value || "grupo";
  const pos = document.getElementById("zaza-posicao")?.value || "cabeca";
  const valor = parseFloat(document.getElementById("zaza-valor")?.value || 10.0);
  const rawText = document.getElementById("zaza-apostas")?.value.trim() || "";
  const resDiv = document.getElementById("zaza-resultado-container");

  if (!rawText) {
    showToast("Informe o palpite ou número a ser conferido.", false);
    return;
  }

  const apostas = rawText.split(/[\n,;]+/).map(a => a.trim()).filter(a => a.length > 0);

  if (resDiv) {
    resDiv.style.display = "block";
    resDiv.innerHTML = '<div style="color: var(--text-muted); padding: 1rem; text-align: center;">Auditando palpites contra o sorteio ativo...</div>';
  }

  try {
    const res = await fetch("/api/conferir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tipo: tipo,
        posicao: pos,
        valor_aposta: valor,
        apostas: apostas,
        origem_sorteio: zazaSorteioAtual
      })
    });

    if (!res.ok) {
      const err = await res.json();
      resDiv.innerHTML = `<div style="color: var(--danger); padding: 1rem;">${err.detail || 'Erro ao processar conferência.'}</div>`;
      return;
    }

    const data = await res.json();
    const isPremiado = data.total_acertos > 0;

    let html = `
      <div class="zaza-receipt-card" style="border-left: 4px solid ${isPremiado ? 'var(--primary)' : 'var(--border)'};">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
          <div>
            <div style="font-size: 0.78rem; color: var(--text-muted); text-transform: uppercase;">Resultado da Auditoria Oficial</div>
            <strong style="font-size: 1.15rem; color: #fff;">${data.nome_modalidade} • ${data.posicao === 'cabeca' ? 'Na Cabeça (1º Prêmio)' : '1º ao 5º Prêmio (Cercado)'}</strong>
          </div>
          <div>
            ${isPremiado ? `
              <span class="card-badge" style="background: rgba(16, 185, 129, 0.2); color: var(--primary); border: 1px solid var(--primary); font-size: 0.95rem; font-weight: 900; padding: 0.35rem 0.85rem;">
                🎉 BILHETE CONTEMPLADO!
              </span>
            ` : `
              <span class="card-badge" style="background: rgba(148, 163, 184, 0.15); color: var(--text-muted); border: 1px solid var(--border); font-size: 0.85rem; padding: 0.35rem 0.75rem;">
                NÃO CONTEMPLADO
              </span>
            `}
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.85rem; margin-bottom: 1.25rem;">
          <div style="background: rgba(0,0,0,0.3); padding: 0.65rem; border-radius: 6px; border: 1px solid var(--border);">
            <div style="font-size: 0.72rem; color: var(--text-muted);">Total de Apostas</div>
            <strong style="font-size: 1.1rem; color: #fff;">${data.total_apostas}</strong>
          </div>
          <div style="background: rgba(0,0,0,0.3); padding: 0.65rem; border-radius: 6px; border: 1px solid var(--border);">
            <div style="font-size: 0.72rem; color: var(--text-muted);">Investimento Total</div>
            <strong style="font-size: 1.1rem; color: #fff;">R$ ${data.investimento_total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</strong>
          </div>
          <div style="background: rgba(0,0,0,0.3); padding: 0.65rem; border-radius: 6px; border: 1px solid var(--border);">
            <div style="font-size: 0.72rem; color: var(--text-muted);">Acertos</div>
            <strong style="font-size: 1.1rem; color: ${isPremiado ? 'var(--primary)' : 'var(--text-muted)'};">${data.total_acertos}</strong>
          </div>
          <div style="background: rgba(0,0,0,0.3); padding: 0.65rem; border-radius: 6px; border: 1px solid var(--border);">
            <div style="font-size: 0.72rem; color: var(--text-muted);">Retorno Bruto</div>
            <strong style="font-size: 1.25rem; color: ${isPremiado ? 'var(--accent-gold)' : 'var(--text-muted)'};">R$ ${data.premio_total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</strong>
          </div>
          <div style="background: rgba(0,0,0,0.3); padding: 0.65rem; border-radius: 6px; border: 1px solid var(--border);">
            <div style="font-size: 0.72rem; color: var(--text-muted);">Lucro Líquido</div>
            <strong style="font-size: 1.25rem; color: ${data.lucro_liquido > 0 ? 'var(--primary)' : (data.lucro_liquido < 0 ? 'var(--danger)' : 'var(--text-muted)')};">
              ${data.lucro_liquido >= 0 ? '+' : ''} R$ ${data.lucro_liquido.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
            </strong>
          </div>
        </div>
    `;

    if (data.detalhes && data.detalhes.length > 0) {
      html += `<div style="font-size: 0.85rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem;">Detalhamento das Apostas:</div>`;
      data.detalhes.forEach(d => {
        const hit = d.acertou;
        html += `
          <div style="background: ${hit ? 'rgba(16, 185, 129, 0.08)' : 'rgba(255,255,255,0.02)'}; border: 1px solid ${hit ? 'rgba(16, 185, 129, 0.35)' : 'var(--border)'}; border-radius: 6px; padding: 0.65rem 0.85rem; margin-bottom: 0.4rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            <div>
              <strong style="color: #fff; font-family: var(--font-mono); font-size: 0.98rem;">${d.info_aposta || d.aposta}</strong>
              <div style="font-size: 0.78rem; color: ${hit ? 'var(--primary)' : 'var(--text-muted)'}; margin-top: 0.15rem;">
                ${hit ? `🎯 ${d.premios_atingidos.join(' • ')} (${d.multiplicador}x)` : '❌ Não contemplado neste sorteio'}
              </div>
            </div>
            <div style="text-align: right;">
              <div style="font-size: 0.72rem; color: var(--text-muted);">Apostado: R$ ${d.valor_apostado.toFixed(2)}</div>
              <strong style="font-size: 1rem; color: ${hit ? 'var(--primary)' : 'var(--text-muted)'};">
                ${hit ? `+ R$ ${d.retorno.toLocaleString('pt-BR', {minimumFractionDigits: 2})}` : 'R$ 0,00'}
              </strong>
            </div>
          </div>
        `;
      });
    }

    html += `</div>`;
    resDiv.innerHTML = html;

  } catch (e) {
    resDiv.innerHTML = '<div style="color: var(--danger); padding: 1rem;">Falha na comunicação com o servidor.</div>';
  }
}

function renderizarCardsRegrasZaza() {
  const container = document.getElementById("zaza-cards-regras");
  if (!container || !zazaRegras) return;

  container.innerHTML = Object.values(zazaRegras).map(r => `
    <div class="zaza-rule-card">
      <div class="zaza-rule-header">
        <span class="zaza-rule-title">${r.nome}</span>
        <span class="zaza-badge" style="font-size: 0.65rem;">${r.qtd_elementos} ${r.qtd_elementos === 1 ? 'ITEM' : 'ITENS'}</span>
      </div>
      <p style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.4; min-height: 38px;">
        ${r.descricao}
      </p>
      <div class="zaza-rule-payouts">
        ${r.suporta_cabeca ? `
          <div class="zaza-payout-badge highlight">
            <span class="label">Na Cabeça (1º)</span>
            <span class="val">${r.mult_cabeca}X</span>
          </div>
        ` : ''}
        <div class="zaza-payout-badge ${!r.suporta_cabeca ? 'highlight' : ''}">
          <span class="label">1º ao 5º (Cercado)</span>
          <span class="val">${r.mult_cercado}X</span>
        </div>
      </div>
      <div style="font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid rgba(255,255,255,0.06); padding-top: 0.4rem; display: flex; justify-content: space-between;">
        <span>Exemplo da Aula:</span>
        <strong style="color: var(--accent);">${r.exemplo_aula}</strong>
      </div>
    </div>
  `).join("");
}

function renderizarBichosZaza() {
  const container = document.getElementById("zaza-bichos-container");
  if (!container || !zazaBichos) return;

  container.innerHTML = zazaBichos.map(b => `
    <div class="zaza-bicho-item" onclick="selecionarBichoParaAposta('${b.grupo}', '${b.nome}')" title="Clique para escolher ${b.nome}">
      <div class="zaza-bicho-top">
        <span class="zaza-bicho-grupo">GRUPO ${b.grupo}</span>
        <span style="font-size: 1.35rem;">${b.icone}</span>
      </div>
      <div class="zaza-bicho-nome">${b.nome}</div>
      <div class="zaza-bicho-dezenas">
        ${b.dezenas.map(d => `<span class="zaza-dez-chip">${d}</span>`).join("")}
      </div>
    </div>
  `).join("");
}
