import re
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import os

BICHO_MAP = {
    1: "Avestruz", 2: "Águia", 3: "Burro", 4: "Borboleta", 5: "Cachorro",
    6: "Cabra", 7: "Carneiro", 8: "Camelo", 9: "Cobra", 10: "Coelho",
    11: "Cavalo", 12: "Elefante", 13: "Galo", 14: "Gato", 15: "Jacaré",
    16: "Leão", 17: "Macaco", 18: "Porco", 19: "Pavão", 20: "Peru",
    21: "Touro", 22: "Tigre", 23: "Urso", 24: "Veado", 25: "Vaca"
}

DIAS_SEMANA = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

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
    
    # Check for Federal
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
    except Exception as e:
        return date_str, []

    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    dia_sem = DIAS_SEMANA[dt.weekday()]
    
    # Find all extraction headers
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
            
        # Parse table with 1º to 7º prizes
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
            
            # Group and bicho
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

if __name__ == "__main__":
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    
    # Test for 3 days
    print("Testing extraction for last 3 days...")
    for d in ["2026-10-30", "2026-10-31", "2026-11-01"]:
        _, items = fetch_day(session, d)
        print(f"Date {d}: {len(items)} prize records parsed.")
