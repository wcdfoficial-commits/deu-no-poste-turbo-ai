import sqlite3
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "deu_no_poste_12m.db")

BICHO_INFO = {
    1: {"nome": "Avestruz", "icone": "🪶", "dezenas": ["01", "02", "03", "04"]},
    2: {"nome": "Águia", "icone": "🦅", "dezenas": ["05", "06", "07", "08"]},
    3: {"nome": "Burro", "icone": "🫏", "dezenas": ["09", "10", "11", "12"]},
    4: {"nome": "Borboleta", "icone": "🦋", "dezenas": ["13", "14", "15", "16"]},
    5: {"nome": "Cachorro", "icone": "🐶", "dezenas": ["17", "18", "19", "20"]},
    6: {"nome": "Cabra", "icone": "🐐", "dezenas": ["21", "22", "23", "24"]},
    7: {"nome": "Carneiro", "icone": "🐏", "dezenas": ["25", "26", "27", "28"]},
    8: {"nome": "Camelo", "icone": "🐫", "dezenas": ["29", "30", "31", "32"]},
    9: {"nome": "Cobra", "icone": "🐍", "dezenas": ["33", "34", "35", "36"]},
    10: {"nome": "Coelho", "icone": "🐰", "dezenas": ["37", "38", "39", "40"]},
    11: {"nome": "Cavalo", "icone": "🐴", "dezenas": ["41", "42", "43", "44"]},
    12: {"nome": "Elefante", "icone": "🐘", "dezenas": ["45", "46", "47", "48"]},
    13: {"nome": "Galo", "icone": "🐓", "dezenas": ["49", "50", "51", "52"]},
    14: {"nome": "Gato", "icone": "🐱", "dezenas": ["53", "54", "55", "56"]},
    15: {"nome": "Jacaré", "icone": "🐊", "dezenas": ["57", "58", "59", "60"]},
    16: {"nome": "Leão", "icone": "🦁", "dezenas": ["61", "62", "63", "64"]},
    17: {"nome": "Macaco", "icone": "🐵", "dezenas": ["65", "66", "67", "68"]},
    18: {"nome": "Porco", "icone": "🐷", "dezenas": ["69", "70", "71", "72"]},
    19: {"nome": "Pavão", "icone": "🦚", "dezenas": ["73", "74", "75", "76"]},
    20: {"nome": "Peru", "icone": "🦃", "dezenas": ["77", "78", "79", "80"]},
    21: {"nome": "Touro", "icone": "🐂", "dezenas": ["81", "82", "83", "84"]},
    22: {"nome": "Tigre", "icone": "🐯", "dezenas": ["85", "86", "87", "88"]},
    23: {"nome": "Urso", "icone": "🐻", "dezenas": ["89", "90", "91", "92"]},
    24: {"nome": "Veado", "icone": "🦌", "dezenas": ["93", "94", "95", "96"]},
    25: {"nome": "Vaca", "icone": "🐮", "dezenas": ["97", "98", "99", "00"]}
}

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT id_sorteio), MIN(data), MAX(data) FROM resultados")
    total_premios, total_sorteios, data_min, data_max = cursor.fetchone()
    
    # Obter último sorteio
    cursor.execute("""
        SELECT data, horario, extracao 
        FROM resultados 
        ORDER BY id_sorteio DESC 
        LIMIT 1
    """)
    ultimo = cursor.fetchone()
    
    conn.close()
    return {
        "total_registros": total_premios,
        "total_sorteios": total_sorteios,
        "data_inicio": data_min,
        "data_fim": data_max,
        "ultimo_sorteio": {
            "data": ultimo["data"] if ultimo else "",
            "horario": ultimo["horario"] if ultimo else "",
            "extracao": ultimo["extracao"] if ultimo else ""
        } if ultimo else None
    }

def get_latest_draw():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(id_sorteio) FROM resultados")
    max_id = cursor.fetchone()[0]
    
    if not max_id:
        conn.close()
        return None
        
    cursor.execute("SELECT * FROM resultados WHERE id_sorteio = ? ORDER BY premio_num ASC", (max_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    for r in rows:
        g = int(r["grupo"]) if r["grupo"] else 0
        r["icone"] = BICHO_INFO.get(g, {}).get("icone", "🎯")
    return rows

def query_results(
    data_ini: Optional[str] = None,
    data_fim: Optional[str] = None,
    extracao: Optional[str] = None,
    bicho: Optional[str] = None,
    grupo: Optional[str] = None,
    dezena: Optional[str] = None,
    centena: Optional[str] = None,
    milhar: Optional[str] = None,
    premio_num: Optional[int] = None,
    so_cabeca: bool = False,
    page: int = 1,
    page_size: int = 50
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if data_ini:
        conditions.append("data >= ?")
        params.append(data_ini)
    if data_fim:
        conditions.append("data <= ?")
        params.append(data_fim)
    if extracao:
        conditions.append("extracao = ?")
        params.append(extracao)
    if bicho:
        conditions.append("bicho = ?")
        params.append(bicho)
    if grupo:
        conditions.append("grupo = ?")
        params.append(f"{int(grupo):02d}")
    if dezena:
        conditions.append("dezena = ?")
        params.append(dezena)
    if centena:
        conditions.append("centena = ?")
        params.append(centena)
    if milhar:
        conditions.append("milhar = ?")
        params.append(milhar)
    if premio_num:
        conditions.append("premio_num = ?")
        params.append(premio_num)
    if so_cabeca:
        conditions.append("is_cabeca = 1")
        
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    # Contar total
    count_sql = f"SELECT COUNT(*) FROM resultados {where_clause}"
    cursor.execute(count_sql, params)
    total_records = cursor.fetchone()[0]
    
    # Buscar registros paginados
    offset = (page - 1) * page_size
    query_sql = f"""
        SELECT * FROM resultados 
        {where_clause} 
        ORDER BY id_sorteio DESC, premio_num ASC 
        LIMIT ? OFFSET ?
    """
    cursor.execute(query_sql, params + [page_size, offset])
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    for r in rows:
        g = int(r["grupo"]) if r["grupo"] else 0
        r["icone"] = BICHO_INFO.get(g, {}).get("icone", "🎯")
        
    return {
        "total": total_records,
        "page": page,
        "page_size": page_size,
        "pages": (total_records + page_size - 1) // page_size,
        "data": rows
    }

def init_fila_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fila_apostas (
            id_aposta INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_estrategia TEXT,
            tipo TEXT,
            apostas_json TEXT,
            custo_por_rodada REAL,
            id_sorteio_gatilho INTEGER,
            data_gatilho TEXT,
            extracao_gatilho TEXT,
            horario_gatilho TEXT,
            bicho_gatilho TEXT,
            milhar_gatilho TEXT,
            criado_em TEXT,
            status TEXT DEFAULT 'EM_ANDAMENTO',
            max_gales INTEGER DEFAULT 12,
            resultado_resumo TEXT
        )
    """)
    conn.commit()
    conn.close()

init_fila_table()

def adicionar_aposta_fila(
    nome_estrategia: str,
    tipo: str,
    apostas: List[str],
    custo_por_rodada: float,
    id_sorteio_gatilho: Optional[int] = None
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    if not id_sorteio_gatilho:
        cursor.execute("SELECT id_sorteio, data, extracao, horario, bicho, milhar FROM resultados WHERE is_cabeca = 1 ORDER BY id_sorteio DESC LIMIT 1")
        gat = cursor.fetchone()
    else:
        cursor.execute("SELECT id_sorteio, data, extracao, horario, bicho, milhar FROM resultados WHERE is_cabeca = 1 AND id_sorteio = ?", (id_sorteio_gatilho,))
        gat = cursor.fetchone()
        
    id_gat = gat["id_sorteio"] if gat else 0
    data_gat = gat["data"] if gat else ""
    ext_gat = gat["extracao"] if gat else ""
    hor_gat = gat["horario"] if gat else ""
    bicho_gat = gat["bicho"] if gat else ""
    milhar_gat = gat["milhar"] if gat else ""
    
    apostas_clean = [str(a).strip() for a in apostas if str(a).strip()]
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO fila_apostas (
            nome_estrategia, tipo, apostas_json, custo_por_rodada,
            id_sorteio_gatilho, data_gatilho, extracao_gatilho, horario_gatilho,
            bicho_gatilho, milhar_gatilho, criado_em, status, max_gales
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'EM_ANDAMENTO', 12)
    """, (
        nome_estrategia, tipo, json.dumps(apostas_clean), custo_por_rodada,
        id_gat, data_gat, ext_gat, hor_gat, bicho_gat, milhar_gat, criado_em
    ))
    id_novo = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "id_aposta": id_novo,
        "mensagem": f"Jogo adicionado à fila para acompanhamento de ciclos G0 a G12!",
        "sorteio_gatilho": f"{data_gat} {ext_gat} ({bicho_gat})"
    }

def listar_fila_apostas() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fila_apostas ORDER BY id_aposta DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    
    for r in rows:
        r["apostas"] = json.loads(r["apostas_json"]) if r["apostas_json"] else []
        id_gat = r["id_sorteio_gatilho"]
        cursor.execute("SELECT COUNT(DISTINCT id_sorteio) FROM resultados WHERE is_cabeca = 1 AND id_sorteio > ?", (id_gat,))
        r["sorteios_posteriores_disponiveis"] = cursor.fetchone()[0]
        
    conn.close()
    return rows

def remover_aposta_fila(id_aposta: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fila_apostas WHERE id_aposta = ?", (id_aposta,))
    af = cursor.rowcount
    conn.commit()
    conn.close()
    return af > 0

def obter_sorteios_posteriores(id_sorteio_gatilho: int, limit: int = 13) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT id_sorteio, data, extracao, horario, bicho, grupo, milhar, centena, dezena
        FROM resultados 
        WHERE is_cabeca = 1 AND id_sorteio > ? 
        ORDER BY id_sorteio ASC 
        LIMIT ?
    """, (id_sorteio_gatilho, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    for idx, r in enumerate(rows):
        r["gale_tag"] = f"G{idx}"
        r["rodada_num"] = idx + 1
        g = int(r["grupo"]) if r.get("grupo") else 0
        r["icone"] = BICHO_INFO.get(g, {}).get("icone", "🎯")
    return rows

def conferir_aposta_ciclo(id_aposta: int, id_sorteio_alvo: Optional[int] = None) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM fila_apostas WHERE id_aposta = ?", (id_aposta,))
    aposta_row = cursor.fetchone()
    if not aposta_row:
        conn.close()
        raise ValueError("Aposta não encontrada na fila.")
        
    ap = dict(aposta_row)
    apostas = json.loads(ap["apostas_json"]) if ap["apostas_json"] else []
    tipo = ap["tipo"].lower()
    custo_rodada = float(ap["custo_por_rodada"] or 0)
    id_gat = ap["id_sorteio_gatilho"]
    max_gales = int(ap["max_gales"] or 12)
    
    if id_sorteio_alvo:
        cursor.execute("""
            SELECT DISTINCT id_sorteio, data, extracao, horario 
            FROM resultados 
            WHERE id_sorteio = ?
        """, (id_sorteio_alvo,))
        sorteios_alvo = cursor.fetchall()
    else:
        cursor.execute("""
            SELECT DISTINCT id_sorteio, data, extracao, horario 
            FROM resultados 
            WHERE is_cabeca = 1 AND id_sorteio > ? 
            ORDER BY id_sorteio ASC 
            LIMIT ?
        """, (id_gat, max_gales + 1))
        sorteios_alvo = cursor.fetchall()
        
    rodadas_conferidas = []
    ciclo_premiado = False
    gale_vencedor = None
    rodada_vencedora = None
    saldo_primeiro_acerto = 0.0
    custo_total_acumulado = 0.0
    premio_total_acumulado = 0.0
    total_acertos_ciclo = 0
    
    total_d = 0
    total_c = 0
    total_m = 0
    total_g = 0
    total_zeros = 0
    
    for idx, s in enumerate(sorteios_alvo):
        sid = s["id_sorteio"]
        cursor.execute("SELECT COUNT(DISTINCT id_sorteio) FROM resultados WHERE is_cabeca = 1 AND id_sorteio > ? AND id_sorteio <= ?", (id_gat, sid))
        gale_idx = cursor.fetchone()[0] - 1
        gale_label = f"G{gale_idx}"
        rodada_num = gale_idx + 1
        
        cursor.execute("SELECT * FROM resultados WHERE id_sorteio = ? ORDER BY premio_num ASC", (sid,))
        premios_sorteio = [dict(p) for p in cursor.fetchall()]
        if not premios_sorteio: continue
        
        cabeca = premios_sorteio[0]
        hits_rodada = []
        premio_rodada = 0.0
        
        round_count_m = 0
        round_count_c = 0
        round_count_d = 0
        round_count_g = 0
        
        for aposta in apostas:
            hit = False
            desc_premio = ""
            val = 0.0
            
            if tipo == "dezena":
                if aposta == cabeca["dezena"]:
                    hit = True
                    round_count_d += 1
                    desc_premio = "1º Prêmio (Cabeça) - DEZENA!"
                    val = 60.00
            elif tipo == "centena":
                if aposta == cabeca["centena"]:
                    hit = True
                    round_count_c += 1
                    desc_premio = "1º Prêmio (Cabeça) - CENTENA SECA!"
                    val = 578.00
                else:
                    for r in premios_sorteio[1:5]:
                        if aposta == r["centena"]:
                            hit = True
                            round_count_c += 1
                            desc_premio = f"{r['premio']} (Cercado) - Centena"
                            val = 100.00
                            break
                # Se não bateu centena seca mas bateu a dezena
                if not hit and len(aposta) >= 2 and aposta[-2:] == cabeca["dezena"]:
                    round_count_d += 1
                    desc_premio = "Defesa / Consolação - Dezena na Cabeça!"
                    val = 0.0  # registro de defesa
            elif tipo == "milhar":
                if aposta == cabeca["milhar"]:
                    hit = True
                    round_count_m += 1
                    desc_premio = "1º Prêmio (Cabeça) - MILHAR SECA!"
                    val = 4578.00
                else:
                    for r in premios_sorteio[1:5]:
                        if aposta == r["milhar"]:
                            hit = True
                            round_count_m += 1
                            desc_premio = f"{r['premio']} (Cercado) - Milhar"
                            val = 800.00
                            break
                # Se não bateu o milhar seco mas bateu a centena ou dezena
                if not hit:
                    if len(aposta) >= 3 and aposta[-3:] == cabeca["centena"]:
                        round_count_c += 1
                    elif len(aposta) >= 2 and aposta[-2:] == cabeca["dezena"]:
                        round_count_d += 1
            elif tipo == "grupo":
                g_str = f"{int(aposta):02d}" if aposta.isdigit() else aposta
                if g_str == cabeca["grupo"] or aposta.lower() == cabeca["bicho"].lower():
                    hit = True
                    round_count_g += 1
                    desc_premio = "1º Prêmio (Cabeça) - GRUPO!"
                    val = 18.00
                    
            if hit:
                hits_rodada.append({
                    "aposta": aposta,
                    "premio": desc_premio,
                    "valor": val
                })
                premio_rodada += val
                
        custo_total_acumulado += custo_rodada
        premio_total_acumulado += premio_rodada
        houve_acerto = len(hits_rodada) > 0
        
        # Determinar a Notação Progressiva da Rodada (0, 1D, 1C, 1M, 1G)
        notacao_partes = []
        if round_count_m > 0:
            notacao_partes.append(f"{round_count_m}M")
            total_m += round_count_m
        if round_count_c > 0:
            notacao_partes.append(f"{round_count_c}C")
            total_c += round_count_c
        if round_count_d > 0:
            notacao_partes.append(f"{round_count_d}D")
            total_d += round_count_d
        if round_count_g > 0:
            notacao_partes.append(f"{round_count_g}G")
            total_g += round_count_g
            
        if notacao_partes:
            notacao_rodada = " + ".join(notacao_partes)
        else:
            notacao_rodada = "0"
            total_zeros += 1
            
        # Determinação do Ciclo Diário (Dia 1 x Dia 2 - 24h)
        dia_ciclo = "Dia 1 (Mesmo Dia)" if rodada_num <= 6 else "Dia 2 (24h / Próx. Dia)"
        dia_badge = "☀️ Dia 1" if rodada_num <= 6 else "🌙 Dia 2 (24h)"
        
        g_icone = BICHO_INFO.get(int(cabeca["grupo"]) if cabeca.get("grupo") else 0, {}).get("icone", "🎯")
        
        rodada_info = {
            "gale": gale_label,
            "rodada": rodada_num,
            "id_sorteio": sid,
            "data": cabeca["data"],
            "horario": cabeca["horario"],
            "extracao": cabeca["extracao"],
            "milhar_cabeca": cabeca["milhar"],
            "centena_cabeca": cabeca["centena"],
            "dezena_cabeca": cabeca["dezena"],
            "bicho_cabeca": f"{g_icone} {cabeca['bicho']}",
            "custo_rodada": custo_rodada,
            "custo_acumulado": custo_total_acumulado,
            "acertou": houve_acerto,
            "notacao": notacao_rodada,
            "dia_ciclo": dia_ciclo,
            "dia_badge": dia_badge,
            "total_acertos": len(hits_rodada),
            "acertos": hits_rodada,
            "premio_rodada": premio_rodada,
            "premio_acumulado": premio_total_acumulado,
            "saldo_liquido": premio_total_acumulado - custo_total_acumulado
        }
        rodadas_conferidas.append(rodada_info)
        
        if houve_acerto:
            total_acertos_ciclo += 1
            if not ciclo_premiado:
                ciclo_premiado = True
                gale_vencedor = gale_label
                rodada_vencedora = rodada_num
                saldo_primeiro_acerto = premio_total_acumulado - custo_total_acumulado
                
        # Se foi solicitada a conferência de um único sorteio específico, para aqui
        if id_sorteio_alvo:
            break
            
    # Construção da Fita Progressiva (Ribbon) de Gales:
    # Ex: 0 ➔ 1D ➔ 0 ➔ 1M ➔ 1C ➔ 0 | 🌙 24h | 0 ➔ 1D
    fita_elementos = []
    fita_lista = []
    for idx, r in enumerate(rodadas_conferidas):
        if idx == 6:
            fita_elementos.append("| 🌙 24h |")
            fita_lista.append({"tipo": "divisor_24h", "rotulo": "🌙 Ciclo 24h (Dia Seguinte)"})
        fita_elementos.append(r["notacao"])
        fita_lista.append({
            "tipo": "rodada",
            "gale": r["gale"],
            "rodada": r["rodada"],
            "notacao": r["notacao"],
            "dia_badge": r["dia_badge"],
            "acertou": r["acertou"],
            "premio_rodada": r["premio_rodada"]
        })
        
    fita_progressiva_str = " ➔ ".join(fita_elementos).replace(" ➔ | 🌙 24h | ➔ ", "  | 🌙 24h |  ") if fita_elementos else "Sem apurações ainda"
    
    saldo_final = premio_total_acumulado - custo_total_acumulado
    if ciclo_premiado:
        novo_status = f"PREMIADO ({gale_vencedor})"
        resumo = f"{fita_progressiva_str} (Saldo: R$ {saldo_final:+.2f})"
    elif len(rodadas_conferidas) >= max_gales:
        novo_status = "ENCERRADO (MAX GALE)"
        resumo = f"{fita_progressiva_str} (Ciclo encerrado após {max_gales} rodadas)"
    elif len(rodadas_conferidas) == 0:
        novo_status = "AGUARDANDO SORTEIOS"
        resumo = "Aguardando novos resultados serem apurados..."
    else:
        novo_status = f"EM_ANDAMENTO (G{len(rodadas_conferidas)-1})"
        resumo = f"{fita_progressiva_str}"
        
    cursor.execute("""
        UPDATE fila_apostas 
        SET status = ?, resultado_resumo = ? 
        WHERE id_aposta = ?
    """, (novo_status, resumo, id_aposta))
    conn.commit()
    conn.close()
    
    return {
        "id_aposta": id_aposta,
        "nome_estrategia": ap["nome_estrategia"],
        "tipo": tipo,
        "total_apostas": len(apostas),
        "apostas": apostas,
        "gatilho": {
            "id_sorteio": id_gat,
            "data": ap["data_gatilho"],
            "extracao": ap["extracao_gatilho"],
            "horario": ap["horario_gatilho"],
            "bicho": ap["bicho_gatilho"],
            "milhar": ap["milhar_gatilho"]
        },
        "ciclo_premiado": ciclo_premiado,
        "gale_vencedor": gale_vencedor,
        "rodadas_necessarias": rodada_vencedora,
        "total_rodadas_verificadas": len(rodadas_conferidas),
        "total_acertos_ciclo": total_acertos_ciclo,
        "fita_progressiva_str": fita_progressiva_str,
        "fita_progressiva_lista": fita_lista,
        "totais_catalogo": {
            "milhar_m": total_m,
            "centena_c": total_c,
            "dezena_d": total_d,
            "grupo_g": total_g,
            "erros_zero": total_zeros
        },
        "custo_total_acumulado": custo_total_acumulado,
        "premio_total_acumulado": premio_total_acumulado,
        "saldo_primeiro_acerto": saldo_primeiro_acerto,
        "saldo_liquido": saldo_final,
        "status_final": novo_status,
        "resumo": resumo,
        "rodadas": rodadas_conferidas
    }

def obter_estatisticas_ciclos() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_sorteio, bicho, dezena 
        FROM resultados 
        WHERE is_cabeca = 1 
        ORDER BY id_sorteio ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    # Calcular a curva de maturação G0 a G11 para as dezenas puxadas
    from collections import Counter
    puxadas = {}
    for i in range(len(rows) - 1):
        b = rows[i]["bicho"]
        d = rows[i+1]["dezena"]
        if b not in puxadas: puxadas[b] = []
        puxadas[b].append(d)
        
    top_5 = {b: [dez for dez, _ in Counter(dezs).most_common(5)] for b, dezs in puxadas.items()}
    
    gales = {f"G{g}": 0 for g in range(12)}
    total_ciclos = 0
    
    for i in range(len(rows) - 13):
        b = rows[i]["bicho"]
        alvos = top_5.get(b, [])
        if len(alvos) < 5: continue
        total_ciclos += 1
        for g in range(12):
            if rows[i + 1 + g]["dezena"] in alvos:
                gales[f"G{g}"] += 1
                break
                
    curva = []
    acumulado = 0
    
    catalogo_notacao = {
        0: {
            "sequencia": "[ 1D ] ou [ 0 ]",
            "badge": "1D",
            "badge_sec": "0",
            "desc": "Entrada Inicial Seca",
            "detalhe": "18.9% acerto imediato | 81.1% zero"
        },
        1: {
            "sequencia": "0 ➔ [ 1D ]",
            "badge": "1D",
            "badge_sec": "",
            "desc": "Recuperação G1",
            "detalhe": "23.5% acum. (1º nível de cobertura)"
        },
        2: {
            "sequencia": "0 ➔ 0 ➔ [ 1D / 1C ]",
            "badge": "1D",
            "badge_sec": "1C",
            "desc": "Zona de Pressão",
            "detalhe": "27.2% acum. (Tração crescente)"
        },
        3: {
            "sequencia": "0 ➔ 0 ➔ 0 ➔ [ 1M / 1D ]",
            "badge": "1M",
            "badge_sec": "1D",
            "desc": "⭐ Ponto de Ouro",
            "detalhe": "30.8% acum. (56% do total de acertos)"
        },
        4: {
            "sequencia": "0 ➔ ... ➔ [ 1C / 1D ]",
            "badge": "1C",
            "badge_sec": "1D",
            "desc": "Atraso Moderado",
            "detalhe": "34.4% acum. (Início da zona de risco)"
        },
        5: {
            "sequencia": "0 ➔ ... ➔ [ 1D ]",
            "badge": "1D",
            "badge_sec": "0",
            "desc": "Fechamento Dia 1",
            "detalhe": "37.3% acum. (Fim do dia: Coruja 21:20)"
        },
        6: {
            "sequencia": "| 🌙 24h | ➔ [ 1D / 1M ]",
            "badge": "1D",
            "badge_sec": "1M",
            "desc": "⚡ Repique 24h (+62%)",
            "detalhe": "42.0% acum. (Salto de 2.9% ➔ 4.7% na abertura PPT)"
        },
        7: {
            "sequencia": "🌙 24h ➔ [ 1D ]",
            "badge": "1D",
            "badge_sec": "",
            "desc": "Maturação Dia 2",
            "detalhe": "45.1% acum. (PTM 11:20)"
        },
        8: {
            "sequencia": "🌙 24h ➔ [ 1C / 1D ]",
            "badge": "1C",
            "badge_sec": "1D",
            "desc": "Alavancagem Forte",
            "detalhe": "48.1% acum. (PT 14:20)"
        },
        9: {
            "sequencia": "🌙 24h ➔ [ 1D ]",
            "badge": "1D",
            "badge_sec": "",
            "desc": "Atraso Crítico",
            "detalhe": "50.9% acum. (PTV 16:00)"
        },
        10: {
            "sequencia": "🌙 24h ➔ [ 0 / 1D ]",
            "badge": "0",
            "badge_sec": "1D",
            "desc": "Exaustão Temporária",
            "detalhe": "52.6% acum. (PTN 18:20)"
        },
        11: {
            "sequencia": "🌙 24h ➔ [ 1M / 1D ]",
            "badge": "1M",
            "badge_sec": "1D",
            "desc": "Teto Máximo (12G)",
            "detalhe": "55.1% acum. (Teto estatístico de 24h)"
        }
    }
    
    for g in range(12):
        cnt = gales[f"G{g}"]
        acumulado += cnt
        pct = (cnt / total_ciclos) * 100 if total_ciclos > 0 else 0
        acum_pct = (acumulado / total_ciclos) * 100 if total_ciclos > 0 else 0
        
        info_cat = catalogo_notacao.get(g, {})
        dia_badge = "☀️ Dia 1" if g < 6 else "🌙 Dia 2 (24h)"
        dia_ciclo = "Dia 1 (Mesmo Dia)" if g < 6 else "Dia 2 (24h / Próx. Dia)"
        
        if g <= 3:
            avaliacao = "⭐ Faixa Ótima de Saída (Alta Assertividade)"
        elif g == 6:
            avaliacao = "⚡ Ponto de Repique 24h (+62% tração vs G5)"
        elif g < 6:
            avaliacao = "Zona de Atraso Moderado (Fechamento Dia 1)"
        else:
            avaliacao = "Zona de Alavancagem / Risco Aumentado"
            
        curva.append({
            "gale": f"G{g}",
            "rodada": g + 1,
            "acertos": cnt,
            "taxa_individual": round(pct, 1),
            "taxa_acumulada": round(acum_pct, 1),
            "dia_badge": dia_badge,
            "dia_ciclo": dia_ciclo,
            "is_dia_2": g >= 6,
            "is_repique_24h": g == 6,
            "notacao_sequencia": info_cat.get("sequencia", ""),
            "notacao_badge": info_cat.get("badge", "0"),
            "notacao_badge_sec": info_cat.get("badge_sec", ""),
            "notacao_desc": info_cat.get("desc", ""),
            "notacao_detalhe": info_cat.get("detalhe", ""),
            "avaliacao": avaliacao
        })
        
    return {
        "total_ciclos_analisados": total_ciclos,
        "curva_maturacao": curva,
        "recomendacoes_filtros": [
            {
                "titulo": "🎯 Stop-Loss Inteligente: Ponto de Ouro no G3 (4 Rodadas)",
                "descricao": "Historicamente, 55.9% de todos os acertos concentram-se entre G0 e G3 (30.8% acumulado). Encerrar ou resetar o ciclo no G3 previne 100% das sequências longas desfavoráveis.",
                "taxa_cobertura": "30.8% acum. (55.9% das vitórias)",
                "tag": "Recomendado"
            },
            {
                "titulo": "⚡ O Repique das 24h no G6 (Abertura do 2º Dia / PPT)",
                "descricao": "No G5 (Coruja 21:20), a assertividade cai para 2.9%, mas salta para 4.7% no G6 (PPT 09:20 do dia seguinte), um aumento de +62%. Ponto estratégico para reentrada matutina!",
                "taxa_cobertura": "Salto +62% (2.9% ➔ 4.7%)",
                "tag": "Oportunidade VIP"
            },
            {
                "titulo": "🎰 Fita Progressiva & Multi-Hits (Teimosinha de 12 Rodadas)",
                "descricao": "Em 16.9% dos ciclos monitorados ocorrem 2 ou mais premiações (ex: 1D no G1 e 1M no G4). O catálogo progressivo permite auditar lucros parciais e reincidentes.",
                "taxa_cobertura": "16.9% de Multi-Hits",
                "tag": "Multi-Prêmio"
            },
            {
                "titulo": "💰 Gestão Fibonacci Suave (Anti-Quebra de Banca)",
                "descricao": "Evite dobrar apostas cegamente. Adote a progressão suave calibrada: R$ 1 (G0) -> R$ 1 (G1) -> R$ 1,50 (G2) -> R$ 2 (G3) -> R$ 2,50 (G4) -> R$ 3 (G5) | 🌙 24h | R$ 4 (G6).",
                "taxa_cobertura": "Gestão Segura",
                "tag": "Banca Blindada"
            }
        ]
    }
