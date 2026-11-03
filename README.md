# 🎯 DEU NO POSTE TURBO AI (PRO)

Sistema web profissional de inteligência preditiva e análise estatística para o Jogo do Bicho / Deu no Poste (Rio de Janeiro e Loteria Federal).

Inspirado no modelo analítico do **Loto Fácil Turbo AI**, o sistema utiliza matrizes de transição de Markov, análise de ciclos temporais de 24 horas, reversão de séries de paridade e fechamentos matemáticos com alto retorno sobre o investimento (ROI).

---

## 🚀 Funcionalidades Principais

* **Base Histórica Indexada:** Já vem com **13.664+ registros** (1.952 sorteios sequenciais dos últimos 12 meses) pré-carregados no banco SQLite local.
* **Sincronização Incremental (Delta Update):**
  * Não reprocessa o histórico antigo.
  * Busca apenas os novos sorteios do dia que ainda não constam no banco.
  * Botão de 1 clique **"Sincronizar Agora"** na interface.
* **Painel Preditivo Multi-Nível:**
  * **Nível 1 (R$ 5,00):** Top 5 Dezenas com probabilidade histórica de 27% a 33% (Break-even 8,3% | ROI +220% a +300%).
  * **Nível 2 (R$ 20,00):** 20 Centenas filtradas com proteção automática de dezena (ROI +260% a +767%).
  * **Nível 3 (R$ 100,00):** Fechamento de 100 milhares na dezena-gatilho (ROI +470% a +815%).
  * Botões de cópia rápida para colar em bancas online ou enviar no WhatsApp.
* **Filtros Dinâmicos Avançados:** Filtre por data, horário (PPT, PTM, PT, PTV, PTN, Federal, Coruja), colocação (Cabeça ou Geral), grupo/bicho, dezena, centena, milhar e paridade.
* **Radar de Puxadas Interativo:** Consulte qualquer um dos 25 animais e veja quem ele puxa e quem puxa ele, com porcentagens e histórico de acertos.
* **Conferidor Automático de Bilhetes:** Cole os seus jogos e o sistema audita instantaneamente contra o último sorteio, informando os acertos e prêmios ganhos.
* **Ícones Otimizados dos 25 Bichos:** Identidade visual moderna com micro-badges e ícones discretos para cada animal e grupo.

---

## 💻 Como Rodar Localmente

Certifique-se de ter o Python 3.10+ instalado.

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Inicie o servidor:
```bash
python app.py
```
ou utilizando o Uvicorn:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

3. Abra o navegador em:
```
http://localhost:8000
```

---

## ☁️ Como Fazer Deploy Gratuito no Render via GitHub

1. **Crie um repositório no GitHub** (pode ser público ou privado):
   * Exemplo: `deu-no-poste-turbo-ai`.
2. **Envie os arquivos do projeto para o repositório:**
   * Certifique-se de que os arquivos `app.py`, `database.py`, `sync_engine.py`, `ai_engine.py`, `deu_no_poste_12m.db`, `requirements.txt`, `Procfile`, `render.yaml` e a pasta `static/` estejam no repositório.
3. **No Render (render.com):**
   * Faça login com a sua conta do GitHub.
   * Clique em **"New"** > **"Web Service"**.
   * Selecione o repositório do seu GitHub.
   * O Render identificará automaticamente o ambiente Python:
     * **Build Command:** `pip install -r requirements.txt`
     * **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
     * **Plan:** Free
   * Clique em **"Deploy Web Service"**.
4. Em menos de 2 minutos, o seu sistema estará online com link HTTPS público (ex: `https://deu-no-poste-turbo-ai.onrender.com`) pronto para uso no celular e no computador!
