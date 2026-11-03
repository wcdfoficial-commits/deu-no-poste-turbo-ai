import re
import os
import time
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

base_dir = r"C:\Users\Derley\.gemini\antigravity\scratch\deu_no_poste_analytics"
sqlite_path = os.path.join(base_dir, "deu_no_poste_12m.db")

conn = sqlite3.connect(sqlite_path)
df_existing = pd.read_sql("SELECT * FROM resultados", conn)
conn.close()

# Identify missing dates
extracted_dates = set(df_existing["data"])
start_date = datetime(2025, 11, 1)
end_date = datetime(2026, 11, 2)
all_dates = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end_date - start_date).days + 1)]
missing = [d for d in all_dates if d not in extracted_dates]

print(f"Total de datas no período: {len(all_dates)}")
print(f"Já existentes no banco: {len(extracted_dates)}")
print(f"Datas a recuperar: {len(missing)}")

BICHO_MAP = {
    1: "Avestruz", 2: "Águia", 3: "Burro", 4: "Borboleta", 5: "Cachorro",
    6: "Cabra", 7: "Carneiro", 8: "Camelo", 9: "Cobra", 10: "Coelho",
    11: "Cavalo", 12: "Elefante", 13: "Galo", 14: "Gato", 15: "Jacaré",
    16: "Leão", 17: "Macaco", 18: "Porco", 19: "Pavão", 20: "Peru",
    21: "Touro", 22: "Tigre", 23: "Urso", 24: "Veado", 25: "Vaca"
}
DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
HORARIO_ORDEM = {"PPT": 1, "PTM": 2, "PT": 3, "PTV": 4, "PTN": 5, "FEDERAL": 5, "CORUJA": 6, "EXTRA": 7}

def get_bicho_grupo(dezena_str):
    try:
        d = int(dezena_str)
        g = 25 if d == 0 else ((d - 1) // 4) + 1
        return f"{g:02d}", BICHO_MAP.get(g, "")
    except:
        return "", ""

def normalize_extracao(title):
    t_up = title.upper()
    horario, extracao = "", ""
    if "FEDERAL" in t_up:
        extracao, horario = "FEDERAL", "19:00"
    else:
        m = re.search(r'(\d{2}:\d{2})', title)
        if m: horario = m.group(1)
        if "CORUJA" in t_up: extracao = "CORUJA"
        elif "PTN" in t_up: extracao = "PTN"
        elif "PTV" in t_up: extracao = "PTV"
        elif "PTM" in t_up: extracao = "PTM"
        elif "PPT" in t_up or "09:20" in t_up: extracao = "PPT"
        elif "PT" in t_up: extracao = "PT"
        else: extracao = "EXTRA"
    return horario, extracao

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

new_rows = []
for idx, date_str in enumerate(missing):
    url = f"https://www.resultadofacil.com.br/resultado-do-jogo-do-bicho/rj/do-dia/{date_str}"
    for attempt in range(3):
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                dia_sem = DIAS_SEMANA[dt.weekday()]
                
                day_rows = []
                for h in soup.find_all(["h2", "h3"]):
                    title = h.get_text(" ", strip=True)
                    if not ("RJ" in title or "FEDERAL" in title or "Jogo do Bicho" in title): continue
                    if "outras datas" in title.lower() or "palpites" in title.lower() or title.strip() == "Resultado do Jogo do Bicho do Rio de Janeiro": continue
                    horario, extracao = normalize_extracao(title)
                    parent = h.find_parent("div")
                    if not parent: continue
                    tables = parent.find_all("table")
                    if not tables: continue
                    
                    for tr in tables[0].find_all("tr"):
                        cols = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
                        if not cols or "Pr" in cols[0] or len(cols) < 2: continue
                        m_premio = re.search(r'(\d+)º?', cols[0])
                        if not m_premio: continue
                        premio_num = int(m_premio.group(1))
                        if premio_num > 7: continue
                        milhar_digits = re.sub(r'\D', '', cols[1])
                        if not milhar_digits: continue
                        milhar_fmt = f"{int(milhar_digits):04d}" if len(milhar_digits) <= 4 else milhar_digits[-4:]
                        centena = milhar_fmt[-3:]
                        dezena = milhar_fmt[-2:]
                        unidade = milhar_fmt[-1:]
                        grupo, bicho = get_bicho_grupo(dezena)
                        d_val = int(dezena)
                        day_rows.append({
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
                            "soma_milhar": sum(int(c) for c in milhar_fmt),
                            "paridade_dezena": "PAR" if d_val % 2 == 0 else "ÍMPAR",
                            "faixa_dezena": "BAIXA" if d_val < 50 else "ALTA",
                            "quadrante": f"Q{(d_val // 25) + 1}"
                        })
                if day_rows:
                    new_rows.extend(day_rows)
                break
        except Exception:
            time.sleep(0.5)

print(f"Novos registros capturados nesta etapa: {len(new_rows)}")

# Juntar com existentes
df_new = pd.DataFrame(new_rows)
if not df_new.empty:
    if "ordem_horario" not in df_existing.columns:
        df_existing["ordem_horario"] = df_existing["extracao"].map(lambda x: HORARIO_ORDEM.get(x, 9))
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
else:
    df_combined = df_existing

# Remover duplicatas caso haja
df_combined.drop_duplicates(subset=["data", "extracao", "premio_num"], inplace=True)

# Ordenar perfeitamente em ordem cronológica
df_combined.sort_values(by=["data", "ordem_horario", "premio_num"], inplace=True)
df_combined.reset_index(drop=True, inplace=True)

# Criar ID único de sorteio e de registro
df_combined["sorteio_key"] = df_combined["data"] + "_" + df_combined["extracao"]
sorteio_map = {k: idx + 1 for idx, k in enumerate(df_combined["sorteio_key"].unique())}
df_combined["id_sorteio"] = df_combined["sorteio_key"].map(sorteio_map)
df_combined["id_registro"] = range(1, len(df_combined) + 1)
df_combined["is_cabeca"] = (df_combined["premio_num"] == 1).astype(int)

# Colunas finais organizadas
cols_order = [
    "id_registro", "id_sorteio", "data", "dia_semana", "horario", "extracao",
    "premio", "premio_num", "is_cabeca", "milhar", "centena", "dezena", "unidade",
    "grupo", "bicho", "soma_milhar", "paridade_dezena", "faixa_dezena", "quadrante"
]
df_final = df_combined[cols_order]

# Salvar CSVs
csv_path = os.path.join(base_dir, "deu_no_poste_12m.csv")
csv_excel_path = os.path.join(base_dir, "deu_no_poste_12m_excel.csv")
df_final.to_csv(csv_path, index=False, encoding="utf-8")
df_final.to_csv(csv_excel_path, index=False, sep=";", encoding="utf-8-sig")

# Salvar SQLite
conn = sqlite3.connect(sqlite_path)
df_final.to_sql("resultados", conn, if_exists="replace", index=False)
cursor = conn.cursor()
cursor.execute("CREATE INDEX IF NOT EXISTS idx_data ON resultados(data);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_sorteio ON resultados(id_sorteio);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_extracao ON resultados(extracao);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_premio ON resultados(premio_num);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_iscabeca ON resultados(is_cabeca);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_grupo ON resultados(grupo);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_bicho ON resultados(bicho);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_milhar ON resultados(milhar);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_centena ON resultados(centena);")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_dezena ON resultados(dezena);")
conn.commit()
conn.close()

# Salvar Excel
xlsx_path = os.path.join(base_dir, "deu_no_poste_12m.xlsx")
df_final.to_excel(xlsx_path, index=False, sheet_name="Resultados_12M")

print(f"\nBASE CONSOLIDADA COM SUCESSO:")
print(f"- Período: {df_final['data'].min()} até {df_final['data'].max()}")
print(f"- Dias únicos com sorteio: {df_final['data'].nunique()}")
print(f"- Total de sorteios sequenciais (extrações): {df_final['id_sorteio'].nunique()}")
print(f"- Total de prêmios registrados (linhas): {len(df_final)}")
print(f"- Arquivo SQLite: {sqlite_path}")
print(f"- Arquivo CSV: {csv_path}")
print(f"- Arquivo Excel: {xlsx_path}")
