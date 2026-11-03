import re
import time
import sqlite3
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# Mapeamento oficial dos 25 bichos
BICHO_MAP = {
    1: "Avestruz", 2: "Águia", 3: "Burro", 4: "Borboleta", 5: "Cachorro",
    6: "Cabra", 7: "Carneiro", 8: "Camelo", 9: "Cobra", 10: "Coelho",
    11: "Cavalo", 12: "Elefante", 13: "Galo", 14: "Gato", 15: "Jacaré",
    16: "Leão", 17: "Macaco", 18: "Porco", 19: "Pavão", 20: "Peru",
    21: "Touro", 22: "Tigre", 23: "Urso", 24: "Veado", 25: "Vaca"
}

DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

HORARIO_ORDEM = {
    "PPT": 1,
    "PTM": 2,
    "PT": 3,
    "PTV": 4,
    "PTN": 5,
    "FEDERAL": 5,
    "CORUJA": 6,
    "EXTRA": 7
}

def get_bicho_grupo(dezena_str):
    try:
        d = int(dezena_str)
        if d == 0:
            g = 25
        else:
            g = ((d - 1) // 4) + 1
        return f"{g:02d}", BICHO_MAP.get(g, "")
    except Exception:
        return "", ""

def normalize_extracao(title):
    title_upper = title.upper()
    horario = ""
    extracao = ""
    
    if "FEDERAL" in title_upper:
        extracao = "FEDERAL"
        horario = "19:00"
    else:
        m_time = re.search(r'(\d{2}:\d{2})', title)
        if m_time:
            horario = m_time.group(1)
        
        if "CORUJA" in title_upper:
            extracao = "CORUJA"
        elif "PTN" in title_upper:
            extracao = "PTN"
        elif "PTV" in title_upper:
            extracao = "PTV"
        elif "PTM" in title_upper:
            extracao = "PTM"
        elif "PPT" in title_upper or "09:20" in title_upper:
            extracao = "PPT"
        elif "PT" in title_upper:
            extracao = "PT"
        else:
            extracao = "EXTRA"
            
    return horario, extracao

def fetch_day(session, date_str):
    url = f"https://www.resultadofacil.com.br/resultado-do-jogo-do-bicho/rj/do-dia/{date_str}"
    try:
        r = session.get(url, timeout=12)
        if r.status_code != 200:
            return date_str, []
    except Exception:
        return date_str, []

    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dia_sem = DIAS_SEMANA[dt.weekday()]
    
    for h in soup.find_all(["h2", "h3"]):
        title = h.get_text(" ", strip=True)
        if not ("RJ" in title or "FEDERAL" in title or "Jogo do Bicho" in title):
            continue
        if "outras datas" in title.lower() or "palpites" in title.lower() or title.strip() == "Resultado do Jogo do Bicho do Rio de Janeiro":
            continue
            
        horario, extracao = normalize_extracao(title)
        
        parent = h.find_parent("div")
        if not parent:
            continue
            
        tables = parent.find_all("table")
        if not tables:
            continue
            
        main_table = tables[0]
        for tr in main_table.find_all("tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
            if not cols or "Pr" in cols[0] or len(cols) < 2:
                continue
                
            m_premio = re.search(r'(\d+)º?', cols[0])
            if not m_premio:
                continue
            premio_num = int(m_premio.group(1))
            if premio_num > 7:
                continue
                
            milhar_digits = re.sub(r'\D', '', cols[1])
            if not milhar_digits:
                continue
                
            milhar_fmt = f"{int(milhar_digits):04d}" if len(milhar_digits) <= 4 else milhar_digits[-4:]
            centena = milhar_fmt[-3:]
            dezena = milhar_fmt[-2:]
            unidade = milhar_fmt[-1:]
            
            grupo, bicho = get_bicho_grupo(dezena)
            soma_digitos = sum(int(c) for c in milhar_fmt)
            d_val = int(dezena)
            paridade = "PAR" if d_val % 2 == 0 else "ÍMPAR"
            faixa = "BAIXA" if d_val < 50 else "ALTA"
            quadrante = f"Q{(d_val // 25) + 1}"
            
            rows.append({
                "data": date_str,
                "dia_semana": dia_sem,
                "horario": horario,
                "extracao": extracao,
                "ordem_horario": HORARIO_ORDEM.get(extracao, 9),
                "premio": f"{premio_num}º",
                "premio_num": premio_num,
                "milhar": milhar_fmt,
                "centena": centena,
                "dezena": dezena,
                "unidade": unidade,
                "grupo": grupo,
                "bicho": bicho,
                "soma_milhar": soma_digitos,
                "paridade_dezena": paridade,
                "faixa_dezena": faixa,
                "quadrante": quadrante
            })
            
    return date_str, rows

def main():
    base_dir = r"C:\Users\Derley\.gemini\antigravity\scratch\deu_no_poste_analytics"
    os.makedirs(base_dir, exist_ok=True)
    
    start_date = datetime(2025, 11, 1)
    end_date = datetime(2026, 11, 2)
    delta = (end_date - start_date).days + 1
    
    dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta)]
    print(f"Iniciando raspagem de {len(dates)} dias consecutivos (de {dates[0]} até {dates[-1]})...")
    
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    all_rows = []
    failed_dates = []
    
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_day, session, d): d for d in dates}
        completed = 0
        for f in as_completed(futures):
            d, rows = f.result()
            completed += 1
            if rows:
                all_rows.extend(rows)
            else:
                failed_dates.append(d)
                
            if completed % 50 == 0 or completed == len(dates):
                print(f"Progresso: {completed}/{len(dates)} dias concluídos ({len(all_rows)} registros)...")
                
    t1 = time.time()
    print(f"Extração concluída em {t1 - t0:.2f} segundos!")
    print(f"Total de registros capturados: {len(all_rows)}")
    if failed_dates:
        print(f"Dias sem sorteios/retorno: {len(failed_dates)} (geralmente feriados excepcionais)")

    # Converter para DataFrame e ordenar cronologicamente
    df = pd.DataFrame(all_rows)
    df.sort_values(by=["data", "ordem_horario", "premio_num"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    
    # Criar ID de sorteio sequencial
    # Um sorteio é identificado unicamente por data + extracao
    df["sorteio_key"] = df["data"] + "_" + df["extracao"]
    sorteio_map = {k: idx + 1 for idx, k in enumerate(df["sorteio_key"].unique())}
    df["id_sorteio"] = df["sorteio_key"].map(sorteio_map)
    
    # Reorganizar colunas
    cols_order = [
        "id_sorteio", "data", "dia_semana", "horario", "extracao",
        "premio", "premio_num", "milhar", "centena", "dezena", "unidade",
        "grupo", "bicho", "soma_milhar", "paridade_dezena", "faixa_dezena", "quadrante"
    ]
    df = df[cols_order]
    
    # Salvar em CSV (versão internacional e versão Excel BR com ponto e vírgula)
    csv_path = os.path.join(base_dir, "deu_no_poste_12m.csv")
    csv_excel_path = os.path.join(base_dir, "deu_no_poste_12m_excel.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")
    df.to_csv(csv_excel_path, index=False, sep=";", encoding="utf-8-sig")
    print(f"Salvo CSV: {csv_path}")
    print(f"Salvo CSV Excel: {csv_excel_path}")
    
    # Salvar em SQLite
    sqlite_path = os.path.join(base_dir, "deu_no_poste_12m.db")
    conn = sqlite3.connect(sqlite_path)
    df.to_sql("resultados", conn, if_exists="replace", index=False)
    
    # Criar índices para consultas ultrarrápidas
    cursor = conn.cursor()
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_data ON resultados(data);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracao ON resultados(extracao);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_premio ON resultados(premio_num);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_grupo ON resultados(grupo);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bicho ON resultados(bicho);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_milhar ON resultados(milhar);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_centena ON resultados(centena);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dezena ON resultados(dezena);")
    conn.commit()
    conn.close()
    print(f"Salvo SQLite: {sqlite_path} com índices criados.")
    
    # Salvar em Excel (.xlsx)
    xlsx_path = os.path.join(base_dir, "deu_no_poste_12m.xlsx")
    df.to_excel(xlsx_path, index=False, sheet_name="Resultados_12M")
    print(f"Salvo Excel: {xlsx_path}")
    
    # Gerar Resumo Estatístico para Validação
    total_sorteios = df["id_sorteio"].nunique()
    total_premios = len(df)
    primeiros_premios = df[df["premio_num"] == 1]
    top_bichos_1p = primeiros_premios["bicho"].value_counts().head(5)
    
    print("\n" + "="*50)
    print("RESUMO DA BASE DE DADOS CONSTRUÍDA:")
    print(f"Período: {df['data'].min()} até {df['data'].max()}")
    print(f"Total de sorteios sequenciais (extrações): {total_sorteios}")
    print(f"Total de registros de prêmios (linhas): {total_premios}")
    print(f"Top 5 Bichos mais sorteados na Cabeça (1º Prêmio):")
    for b, c in top_bichos_1p.items():
        print(f"  - {b}: {c} vezes")
    print("="*50)

if __name__ == "__main__":
    main()
