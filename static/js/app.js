let currentPage = 1;
let totalPages = 1;
let listaBichosCache = [];
let fullGamesCache = { t1: "", t2: "", t3: "" };
let retryCount = 0;

// Toast Notifier
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

// Tab Switcher
function switchTab(tabId) {
  document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));
  
  const targetTab = document.getElementById(tabId);
  if (targetTab) targetTab.classList.add("active");
  
  const btns = Array.from(document.querySelectorAll(".tab-btn"));
  const clickedBtn = btns.find(b => b.getAttribute("onclick")?.includes(tabId));
  if (clickedBtn) clickedBtn.classList.add("active");
}

// Função de Inicialização Completa com Auto-Retry
async function initApp() {
  console.log("Iniciando carregamento do DEU NO POSTE TURBO AI...");
  const ok = await carregarStatus();
  if (ok) {
    await carregarBichos();
    await carregarPredicoes();
    await carregarResultados(1);
  } else {
    // Se o servidor ainda estiver inicializando, tenta novamente
    if (retryCount < 6) {
      retryCount++;
      console.log(`Servidor ainda iniciando. Tentativa ${retryCount}/6 em 1.5s...`);
      setTimeout(initApp, 1500);
    }
  }
}

// Carregar Status
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
    console.warn("Aguardando servidor responder /api/status...", e.message);
    return false;
  }
}

// Carregar Lista de Bichos com Ícones
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
    console.error("Erro ao carregar bichos:", e);
  }
}

// Carregar Predições LOTO TURBO AI
async function carregarPredicoes() {
  try {
    const res = await fetch("/api/predicoes");
    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== "success") return;
    
    const ult = data.ultimo_sorteio;
    const radar = data.radar_analitico;
    const est = data.estrategias;
    
    // Banner
    const elTitulo = document.getElementById("banner-sorteio-titulo");
    const elBadge = document.getElementById("banner-bicho-badge");
    const elMilhar = document.getElementById("banner-milhar");
    const elCentena = document.getElementById("banner-centena");
    const elDezena = document.getElementById("banner-dezena");
    const elParidade = document.getElementById("banner-paridade");
    
    if (elTitulo) elTitulo.textContent = `${ult.extracao} (${ult.horario}) - ${ult.data}`;
    if (elBadge) {
      elBadge.innerHTML = `
        <div class="bicho-badge" style="font-size: 1.1rem; padding: 0.4rem 0.8rem; background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.4);">
          <span class="bicho-icon">${ult.icone}</span>
          <span>${ult.grupo} - ${ult.bicho}</span>
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
          cardG.style.marginBottom = "0.75rem";
          cardG.style.background = "linear-gradient(135deg, rgba(20,24,36,0.95), rgba(15,23,42,0.95))";
          cardG.innerHTML = `
            <div class="card-header" style="margin-bottom: 0.5rem;">
              <div class="card-title" style="color: ${g.cor}; font-size: 1.05rem;">
                <span>⚡</span> ${g.titulo}
              </div>
              <span class="card-badge" style="background: rgba(255,255,255,0.08); color: ${g.cor}; border: 1px solid ${g.cor};">${g.badge}</span>
            </div>
            <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 0.5rem;">${g.descricao}</p>
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

    // Nível 1
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
    
    // Nível 2
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
    
    // Nível 3
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
          <span style="color: var(--primary); font-size: 0.8rem; margin-left: 0.3rem;">${p.taxa}% (${p.lift}x)</span>
        `;
        gridPuxadas.appendChild(pill);
      });
    }
    
  } catch (e) {
    console.error("Erro ao carregar predições:", e);
  }
}

// Carregar Resultados com Filtros Dinâmicos
async function carregarResultados(page = 1) {
  currentPage = page;
  const tbody = document.getElementById("tabela-resultados-body");
  if (!tbody) return;
  
  tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; padding: 2rem;">Buscando registros...</td></tr>';
  
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
    console.error("Erro ao buscar resultados:", e);
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

// Sincronizar Agora
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

// Consultar Puxadas Interativo
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
            <strong style="color: #38bdf8;">${p.taxa}%</strong>
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

// Conferir Apostas
async function conferirApostas() {
  const tipoEl = document.getElementById("conf-tipo");
  const textoEl = document.getElementById("conf-apostas");
  const resDiv = document.getElementById("conf-resultado");
  
  if (!tipoEl || !textoEl || !resDiv) return;
  const tipo = tipoEl.value;
  const texto = textoEl.value;
  
  if (!texto.trim()) {
    showToast("Por favor, digite ou cole suas apostas para conferir.", false);
    return;
  }
  
  const apostas = texto.split(/[\n,;]+/).map(s => s.trim()).filter(s => s.length > 0);
  
  resDiv.style.display = "block";
  resDiv.innerHTML = '<div style="color: var(--text-muted); padding: 1rem;">Auditando bilhete contra o último resultado...</div>';
  
  try {
    const res = await fetch("/api/conferir", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tipo: tipo, apostas: apostas })
    });
    const data = await res.json();
    
    let html = `
      <div style="background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: 8px; padding: 1rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem;">
          <div>Sorteio Auditado: <strong>${data.sorteio_conferido}</strong> | Cabeça: <strong class="milhar-highlight">${data.milhar_sorteada}</strong> (${data.bicho_sorteado})</div>
          <div>Total Jogos: <strong>${data.total_apostas}</strong></div>
        </div>
    `;
    
    if (data.total_acertos > 0) {
      html += `
        <div style="color: var(--primary); font-size: 1.1rem; font-weight: 800; margin-bottom: 0.75rem;">
          🎉 PARABÉNS! ${data.total_acertos} APOSTA(S) PREMIADA(S)! Prêmio Estimado: R$ ${data.premio_total.toLocaleString('pt-BR', {minimumFractionDigits: 2})}
        </div>
        <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.4rem;">
      `;
      data.acertos.forEach(a => {
        html += `
          <li style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); padding: 0.4rem 0.8rem; border-radius: 6px; display: flex; justify-content: space-between;">
            <span>Aposta: <strong>${a.aposta}</strong></span>
            <span>${a.premio} -> <strong>R$ ${a.retorno_estimado.toLocaleString('pt-BR', {minimumFractionDigits: 2})}</strong></span>
          </li>
        `;
      });
      html += `</ul>`;
    } else {
      html += `
        <div style="color: var(--text-muted); font-size: 0.95rem;">
          Nenhum acerto premiado neste sorteio específico. Tente novamente no próximo sorteio com os palpites da IA!
        </div>
      `;
    }
    
    html += `</div>`;
    resDiv.innerHTML = html;
    
  } catch (e) {
    resDiv.innerHTML = '<div style="color: var(--danger);">Falha ao processar conferência do bilhete.</div>';
  }
}

// Copiar Jogos
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

// Disparar inicialização com segurança (tanto se o DOM estiver pronto ou carregando)
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initApp);
} else {
  initApp();
}
window.addEventListener("load", () => {
  const el = document.getElementById("stat-total-sorteios");
  if (el && el.textContent === "...") {
    initApp();
  }
});
