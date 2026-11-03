import re
import time
import sqlite3
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import os

from database import DB_PATH, BICHO_INFO

DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
HORARIO_ORDEM = {"PPT": 1, "PTM": 2, "PT": 3, "PTV": 4, "PTN": 5, "FEDERAL": 5, "CORUJA": 6, "EXTRA": 7}

def get_bicho_grupo(dezena_str):
    try:
        d = int(dezena_str)
        g = 25 if d == 0 else ((d - 1) // 4) + 1
        info = BICHO_INFO.get(g, {"nome": "", "icone": ""})
        return f"{g:02d}", info["nome"]
    except Exception:
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

def fetch_date_results(session, date_str):
    url = f"https://www.resultadofacil.com.br/resultado-do-jogo-do-bicho/rj/do-dia/{date_str}"
    try:
        r = session.get(url, timeout=12)
        if r.status_code != 200:
            return []
    except Exception:
        return []

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
            
        for tr in tables[0].find_all("tr"):
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
            d_val = int(dezena)
            
            rows.append({
                "data": date_str,
                "dia_semana": dia_sem,
                "horario": horario,
                "extracao": extracao,
                "ordem_horario": HORARIO_ORDEM.get(extracao, 9),
                "premio": f"{premio_num}º",
                "premio_num": premio_num,
                "is_cabeca": 1 if premio_num == 1 else 0,
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
            
    return rows

def sync_latest_results():
    """
    Sincronizador Inteligente Incremental:
    Lê a última data no banco e busca apenas datas recentes/atuais que ainda não constam.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(data) FROM resultados")
    max_data_res = cursor.fetchone()
    max_data = max_data_res[0] if max_data_res and max_data_res[0] else "2025-11-01"
    
    # Gerar intervalo de datas do último dia registrado até a data atual
    dt_start = datetime.strptime(max_data, "%Y-%m-%d")
    dt_end = datetime.now()
    
    dates_to_check = []
    curr = dt_start
    while curr <= dt_end:
        dates_to_check.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
        
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    new_records_count = 0
    
    for d_str in dates_to_check:
        day_rows = fetch_date_results(session, d_str)
        if not day_rows:
            continue
            
        # Garantir ordenação cronológica rigorosa das extrações antes de gravar
        day_rows.sort(key=lambda r: (r.get("ordem_horario", 9), r.get("horario", ""), r.get("premio_num", 0)))
            
        for row in day_rows:
            # Checar se já existe no banco
            cursor.execute("""
                SELECT id_registro FROM resultados 
                WHERE data = ? AND extracao = ? AND premio_num = ?
            """, (row["data"], row["extracao"], row["premio_num"]))
            
            if not cursor.fetchone():
                # Obter próximo id_registro
                cursor.execute("SELECT MAX(id_registro), MAX(id_sorteio) FROM resultados")
                m_reg, m_sort = cursor.fetchone()
                next_reg = (m_reg or 0) + 1
                
                # Checar se id_sorteio para essa data/extracao ja existe
                cursor.execute("""
                    SELECT id_sorteio FROM resultados 
                    WHERE data = ? AND extracao = ? LIMIT 1
                """, (row["data"], row["extracao"]))
                s_row = cursor.fetchone()
                sort_id = s_row[0] if s_row else ((m_sort or 0) + 1)
                
                cursor.execute("""
                    INSERT INTO resultados (
                        id_registro, id_sorteio, data, dia_semana, horario, extracao,
                        premio, premio_num, is_cabeca, milhar, centena, dezena, unidade,
                        grupo, bicho, soma_milhar, paridade_dezena, faixa_dezena, quadrante
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    next_reg, sort_id, row["data"], row["dia_semana"], row["horario"], row["extracao"],
                    row["premio"], row["premio_num"], row["is_cabeca"], row["milhar"], row["centena"],
                    row["dezena"], row["unidade"], row["grupo"], row["bicho"], row["soma_milhar"],
                    row["paridade_dezena"], row["faixa_dezena"], row["quadrante"]
                ))
                new_records_count += 1
                
        conn.commit()
        
    conn.close()
    return {
        "status": "success",
        "novos_registros": new_records_count,
        "datas_verificadas": dates_to_check,
        "mensagem": f"Sincronização concluída: {new_records_count} novos registros adicionados." if new_records_count > 0 else "Banco de dados já está 100% atualizado com as últimas apurações."
    }

if __name__ == "__main__":
    res = sync_latest_results()
    print(res)
