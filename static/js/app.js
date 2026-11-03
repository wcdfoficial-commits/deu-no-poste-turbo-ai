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
      const passInput = document.getElementById("login-password");
      if (passInput) passInput.focus();
    }
  }
}

function preencherSenhaAdmin() {
  const passEl = document.getElementById("login-password");
  if (passEl) {
    passEl.value = "@As975109";
    showToast("Senha do Administrador inserida!");
  }
}

async function realizarLogin(event) {
  if (event) event.preventDefault();
  
  const userEl = document.getElementById("login-username");
  const passEl = document.getElementById("login-password");
  const errorBox = document.getElementById("login-error-msg");
  const errorText = document.getElementById("login-error-text");
  const loginCard = document.getElementById("login-card");
  const btnSubmit = document.getElementById("btn-submit-login");

  const username = userEl ? userEl.value.trim() : "admin";
  const password = passEl ? passEl.value.trim() : "";

  if (!password) {
    if (errorBox) {
      errorText.textContent = "Por favor, digite a senha de acesso.";
      errorBox.classList.add("show");
    }
    return;
  }

  if (btnSubmit) {
    btnSubmit.disabled = true;
    btnSubmit.innerHTML = `<span>⏳ Autenticando...</span>`;
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

      if (errorBox) errorBox.classList.remove("show");

      const overlay = document.getElementById("login-overlay");
      if (overlay) {
        overlay.classList.add("hidden");
        overlay.style.display = "none";
      }

      showToast(`Bem-vindo, ${data.user}! Terminal liberado.`);
      
      if (!isInitialized) {
        isInitialized = true;
        initApp();
      }
    } else {
      // Erro de autenticação
      if (loginCard) {
        loginCard.classList.remove("shake");
        void loginCard.offsetWidth; // trigger reflow
        loginCard.classList.add("shake");
      }
      if (errorBox) {
        errorText.textContent = data.detail || "Senha incorreta! Acesso não autorizado.";
        errorBox.classList.add("show");
      }
      if (passEl) {
        passEl.value = "";
        passEl.focus();
      }
    }
  } catch (e) {
    if (errorBox) {
      errorText.textContent = "Erro de conexão com o servidor de autenticação.";
      errorBox.classList.add("show");
    }
  } finally {
    if (btnSubmit) {
      btnSubmit.disabled = false;
      btnSubmit.innerHTML = `<span>⚡ Acessar Terminal Analítico</span>`;
    }
  }
}

function toggleSenhaVisibilidade() {
  const passEl = document.getElementById("login-password");
  if (!passEl) return;
  passEl.type = passEl.type === "password" ? "text" : "password";
}

function fazerLogout() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
  
  const passEl = document.getElementById("login-password");
  if (passEl) passEl.value = "";
  
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
    `;

    if (data.rodadas.length > 0) {
      html += `
        <div style="margin-top: 1.5rem;">
          <div style="font-weight: 800; font-size: 1rem; margin-bottom: 0.75rem; color: var(--text-main);">
            📊 Detalhamento Rodada a Rodada (Evolução do Ciclo):
          </div>
          <div class="stepper-timeline">
      `;

      data.rodadas.forEach(r => {
        const isWin = r.acertou;
        html += `
          <div class="step-card ${isWin ? 'step-win' : ''}">
            <div style="display: flex; align-items: center; gap: 0.85rem;">
              <span class="gale-pill">${r.gale} (Rodada ${r.rodada})</span>
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
        tr.innerHTML = `
          <td><strong style="color: ${isOptimal ? 'var(--primary)' : 'var(--text-main)'}; font-family: var(--font-mono);">${g.gale}</strong></td>
          <td>${g.rodada}ª Rodada</td>
          <td>${g.acertos.toLocaleString("pt-BR")} acertos</td>
          <td><strong style="color: var(--accent);">${g.taxa_individual}%</strong></td>
          <td><strong style="color: #10b981;">${g.taxa_acumulada}%</strong></td>
          <td>
            <span style="font-size: 0.78rem; color: ${isOptimal ? '#10b981' : 'var(--text-muted)'};">
              ${isOptimal ? '⭐ Faixa Ótima de Saída (Alta Assertividade)' : 'Zona de Alavancagem / Risco Aumentado'}
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
