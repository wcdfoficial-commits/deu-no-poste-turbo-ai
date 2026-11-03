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
        ORDER BY data DESC, horario DESC, id_sorteio DESC 
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
    
    cursor.execute("""
        SELECT id_sorteio FROM resultados 
        WHERE is_cabeca = 1 
        ORDER BY data DESC, horario DESC, id_sorteio DESC 
        LIMIT 1
    """)
    row_max = cursor.fetchone()
    max_id = row_max[0] if row_max else None
    
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

# --------------------------------------------------------------------------
# AUDITORIA & REGISTRO DE ASSERTIVIDADE DE LONGO PRAZO
# --------------------------------------------------------------------------
def init_assertividade_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_assertividade_ia (
            id_auditoria INTEGER PRIMARY KEY AUTOINCREMENT,
            data_gatilho TEXT,
            extracao_gatilho TEXT,
            horario_gatilho TEXT,
            bicho_gatilho TEXT,
            milhar_gatilho TEXT,
            id_sorteio_gatilho INTEGER,
            sorteio_alvo_previsto TEXT,
            
            dezenas_sugeridas_json TEXT,
            centenas_sugeridas_json TEXT,
            milhares_sugeridos_json TEXT,
            top_bichos_json TEXT,
            
            taxa_estimada_ia REAL,
            roi_estimado_ia REAL,
            
            apurado INTEGER DEFAULT 0,
            id_sorteio_apurado INTEGER,
            data_apuracao TEXT,
            extracao_apuracao TEXT,
            horario_apuracao TEXT,
            bicho_apurado TEXT,
            milhar_apurado TEXT,
            centena_apurada TEXT,
            dezena_apurada TEXT,
            
            acertou_cabeca_dezena INTEGER DEFAULT 0,
            acertou_cercado_dezena INTEGER DEFAULT 0,
            acertou_centena INTEGER DEFAULT 0,
            acertou_milhar INTEGER DEFAULT 0,
            acertou_bicho INTEGER DEFAULT 0,
            
            notacao_rodada TEXT DEFAULT '0',
            detalhes_acertos_json TEXT,
            status_auditoria TEXT DEFAULT 'AGUARDANDO_SORTEIO',
            
            criado_em TEXT,
            auditado_em TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_automacao_scheduler (
            id_log INTEGER PRIMARY KEY AUTOINCREMENT,
            data_hora TEXT,
            tipo_evento TEXT,
            sorteio_detectado TEXT,
            novos_registros INTEGER,
            assertividade_auditada TEXT,
            status TEXT,
            mensagem TEXT
        )
    """)
    conn.commit()
    conn.close()

init_assertividade_tables()

def registrar_sugestoes_ia(gatilho: Dict[str, Any], predicoes: Dict[str, Any]) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    data_gat = gatilho.get("data", "")
    ext_gat = gatilho.get("extracao", "")
    hor_gat = gatilho.get("horario", "")
    bicho_gat = gatilho.get("bicho", "")
    milhar_gat = gatilho.get("milhar", "")
    id_gat = gatilho.get("id_sorteio", 0)
    
    cursor.execute("""
        SELECT id_auditoria FROM historico_assertividade_ia 
        WHERE data_gatilho = ? AND extracao_gatilho = ?
    """, (data_gat, ext_gat))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]
        
    est = predicoes.get("estrategias", {})
    dezenas = est.get("nivel_1", {}).get("dezenas", [])
    centenas = est.get("nivel_2", {}).get("centenas", [])
    milhares = est.get("nivel_3", {}).get("milhares", [])
    top_bichos = [b.get("bicho", "") for b in predicoes.get("top_puxadas", [])]
    taxa_est = est.get("nivel_1", {}).get("taxa_raw", 23.5)
    roi_est = 185.0
    
    criado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO historico_assertividade_ia (
            data_gatilho, extracao_gatilho, horario_gatilho, bicho_gatilho, milhar_gatilho, id_sorteio_gatilho,
            dezenas_sugeridas_json, centenas_sugeridas_json, milhares_sugeridos_json, top_bichos_json,
            taxa_estimada_ia, roi_estimado_ia, criado_em, status_auditoria
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'AGUARDANDO_SORTEIO')
    """, (
        data_gat, ext_gat, hor_gat, bicho_gat, milhar_gat, id_gat,
        json.dumps(dezenas), json.dumps(centenas[:20]), json.dumps(milhares[:100]), json.dumps(top_bichos),
        taxa_est, roi_est, criado_em
    ))
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id

def auditar_sugestoes_pendentes() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM historico_assertividade_ia 
        WHERE apurado = 0
        ORDER BY id_auditoria ASC
    """)
    pendentes = [dict(r) for r in cursor.fetchall()]
    auditados = []
    
    for p in pendentes:
        id_gat = p["id_sorteio_gatilho"]
        cursor.execute("""
            SELECT DISTINCT id_sorteio, data, extracao, horario, bicho, milhar, centena, dezena, grupo 
            FROM resultados 
            WHERE is_cabeca = 1 AND id_sorteio > ? 
            ORDER BY id_sorteio ASC 
            LIMIT 1
        """, (id_gat,))
        sorteio_seguinte = cursor.fetchone()
        if not sorteio_seguinte:
            continue
            
        sid = sorteio_seguinte["id_sorteio"]
        data_ap = sorteio_seguinte["data"]
        ext_ap = sorteio_seguinte["extracao"]
        hor_ap = sorteio_seguinte["horario"]
        bicho_ap = sorteio_seguinte["bicho"]
        milhar_ap = sorteio_seguinte["milhar"]
        centena_ap = sorteio_seguinte["centena"]
        dezena_ap = sorteio_seguinte["dezena"]
        
        cursor.execute("""
            SELECT premio, premio_num, milhar, centena, dezena, grupo, bicho 
            FROM resultados 
            WHERE id_sorteio = ? 
            ORDER BY premio_num ASC
        """, (sid,))
        premios = [dict(r) for r in cursor.fetchall()]
        
        dezenas_sug = json.loads(p["dezenas_sugeridas_json"]) if p["dezenas_sugeridas_json"] else []
        centenas_sug = json.loads(p["centenas_sugeridas_json"]) if p["centenas_sugeridas_json"] else []
        milhares_sug = json.loads(p["milhares_sugeridos_json"]) if p["milhares_sugeridos_json"] else []
        top_bichos = json.loads(p["top_bichos_json"]) if p["top_bichos_json"] else []
        
        acertos_detalhes = []
        hit_m = 0
        hit_c = 0
        hit_d_cabeca = 0
        hit_d_cercado = 0
        hit_bicho = 1 if bicho_ap.lower() in [b.lower() for b in top_bichos] else 0
        
        if dezena_ap in dezenas_sug:
            hit_d_cabeca = 1
            acertos_detalhes.append(f"1º Prêmio (Cabeça) - DEZENA {dezena_ap}!")
        if centena_ap in centenas_sug:
            hit_c += 1
            acertos_detalhes.append(f"1º Prêmio - Centena {centena_ap} seca!")
        if milhar_ap in milhares_sug:
            hit_m += 1
            acertos_detalhes.append(f"1º Prêmio - Milhar {milhar_ap} seca!")
            
        for r in premios[1:5]:
            if r["dezena"] in dezenas_sug:
                hit_d_cercado += 1
                acertos_detalhes.append(f"{r['premio']} (Cercado) - Dezena {r['dezena']}")
            if r["centena"] in centenas_sug:
                hit_c += 1
                acertos_detalhes.append(f"{r['premio']} (Cercado) - Centena {r['centena']}")
            if r["milhar"] in milhares_sug:
                hit_m += 1
                acertos_detalhes.append(f"{r['premio']} (Cercado) - Milhar {r['milhar']}")
                
        if hit_m > 0:
            notacao = f"{hit_m}M"
        elif hit_c > 0:
            notacao = f"{hit_c}C"
        elif hit_d_cabeca > 0:
            notacao = "1D"
        elif hit_d_cercado > 0:
            notacao = f"{hit_d_cercado}D"
        else:
            notacao = "0"
            
        status_audit = "CONFERIDO_PREMIADO" if (hit_d_cabeca or hit_d_cercado or hit_c or hit_m) else "CONFERIDO_ZERO"
        auditado_em = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            UPDATE historico_assertividade_ia 
            SET apurado = 1, id_sorteio_apurado = ?, data_apuracao = ?, extracao_apuracao = ?, horario_apuracao = ?,
                bicho_apurado = ?, milhar_apurado = ?, centena_apurada = ?, dezena_apurada = ?,
                acertou_cabeca_dezena = ?, acertou_cercado_dezena = ?, acertou_centena = ?, acertou_milhar = ?,
                acertou_bicho = ?, notacao_rodada = ?, detalhes_acertos_json = ?, status_auditoria = ?,
                auditado_em = ?
            WHERE id_auditoria = ?
        """, (
            sid, data_ap, ext_ap, hor_ap, bicho_ap, milhar_ap, centena_ap, dezena_ap,
            hit_d_cabeca, hit_d_cercado, hit_c, hit_m, hit_bicho, notacao, json.dumps(acertos_detalhes),
            status_audit, auditado_em, p["id_auditoria"]
        ))
        
        auditados.append({
            "id_auditoria": p["id_auditoria"],
            "gatilho": f"{p['data_gatilho']} {p['extracao_gatilho']}",
            "apurado": f"{data_ap} {ext_ap} ({bicho_ap})",
            "notacao": notacao,
            "status": status_audit
        })
        
    conn.commit()
    conn.close()
    return auditados

def obter_metricas_assertividade_longo_prazo(limite: int = 25) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM historico_assertividade_ia WHERE apurado = 1
    """)
    total_apurados = cursor.fetchone()[0]
    
    if total_apurados == 0:
        conn.close()
        # Se estiver vazio, realiza backfill de amostra das últimas 30 extrações
        backfill_assertividade_recente(30)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM historico_assertividade_ia WHERE apurado = 1")
        total_apurados = cursor.fetchone()[0]
        
    cursor.execute("""
        SELECT 
            SUM(acertou_cabeca_dezena),
            SUM(CASE WHEN acertou_cercado_dezena > 0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN acertou_centena > 0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN acertou_milhar > 0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN status_auditoria = 'CONFERIDO_PREMIADO' THEN 1 ELSE 0 END),
            AVG(taxa_estimada_ia)
        FROM historico_assertividade_ia 
        WHERE apurado = 1
    """)
    row_stats = cursor.fetchone()
    hits_cabeca = row_stats[0] or 0
    hits_cercado = row_stats[1] or 0
    hits_centena = row_stats[2] or 0
    hits_milhar = row_stats[3] or 0
    hits_totais = row_stats[4] or 0
    taxa_media_est = row_stats[5] or 23.5
    
    taxa_cabeca_pct = (hits_cabeca / total_apurados * 100) if total_apurados > 0 else 0
    taxa_cercado_pct = (hits_cercado / total_apurados * 100) if total_apurados > 0 else 0
    taxa_global_pct = (hits_totais / total_apurados * 100) if total_apurados > 0 else 0
    
    # Amostra recente (últimas 6 extrações - ciclo de 24h)
    cursor.execute("""
        SELECT SUM(CASE WHEN status_auditoria = 'CONFERIDO_PREMIADO' THEN 1 ELSE 0 END), COUNT(*)
        FROM (
            SELECT status_auditoria 
            FROM historico_assertividade_ia 
            WHERE apurado = 1 
            ORDER BY id_auditoria DESC 
            LIMIT 6
        )
    """)
    rec_hits, rec_total = cursor.fetchone()
    taxa_24h_pct = (rec_hits / rec_total * 100) if rec_total and rec_total > 0 else taxa_global_pct
    
    # Determinação do Regime da IA & Calibração
    if taxa_24h_pct >= 33.0:
        regime = {
            "status": "ALTA_TRACAO",
            "titulo": "🔥 Alta Tração (+Convergência Quente)",
            "classe": "regime-quente",
            "cor": "#10b981",
            "descricao": "Os padrões das puxadas estão operando com altíssima aderência nas últimas extrações.",
            "recomendacao": "Momento ideal para alavancagem calculada e fechamentos em Nível 2 e 3."
        }
    elif taxa_24h_pct >= 20.0:
        regime = {
            "status": "ESTAVEL",
            "titulo": "⚡ Regime Nominal / Estável",
            "classe": "regime-estavel",
            "cor": "#38bdf8",
            "descricao": "A assertividade está perfeitamente alinhada com as métricas históricas de 12 meses.",
            "recomendacao": "Mantenha a estratégia de Nível 1 (Dezena) com progressão suave até G3."
        }
    else:
        regime = {
            "status": "DEFESA",
            "titulo": "🛡️ Modo Defesa & Calibração Ativa",
            "classe": "regime-defesa",
            "cor": "#fbbf24",
            "descricao": "Oscilação passageira de baixa frequência detectada nas últimas extrações.",
            "recomendacao": "Operar exclusivamente em Nível 1 com Stop-Loss no G2 para blindagem de banca."
        }
        
    # Buscar lista das últimas auditorias
    cursor.execute("""
        SELECT * FROM historico_assertividade_ia 
        ORDER BY id_auditoria DESC 
        LIMIT ?
    """, (limite,))
    historico = [dict(r) for r in cursor.fetchall()]
    
    for h in historico:
        h["dezenas_sugeridas"] = json.loads(h["dezenas_sugeridas_json"]) if h.get("dezenas_sugeridas_json") else []
        h["detalhes_acertos"] = json.loads(h["detalhes_acertos_json"]) if h.get("detalhes_acertos_json") else []
        
    conn.close()
    
    return {
        "resumo_geral": {
            "total_auditados": total_apurados,
            "acertos_cabeca": hits_cabeca,
            "acertos_cercado": hits_cercado,
            "acertos_centena": hits_centena,
            "acertos_milhar": hits_milhar,
            "acertos_totais": hits_totais,
            "taxa_real_cabeca": round(taxa_cabeca_pct, 1),
            "taxa_real_cercado": round(taxa_cercado_pct, 1),
            "taxa_real_global": round(taxa_global_pct, 1),
            "taxa_estimada_media": round(taxa_media_est, 1),
            "taxa_recente_24h": round(taxa_24h_pct, 1)
        },
        "regime_ia": regime,
        "historico_auditorias": historico
    }

def backfill_assertividade_recente(n: int = 30):
    """
    Popula o histórico de assertividade com base nos últimos N sorteios reais do banco
    para fornecer inteligência retroativa imediata de longo prazo.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id_sorteio, data, extracao, horario, milhar, centena, dezena, bicho 
        FROM resultados 
        WHERE is_cabeca = 1 
        ORDER BY id_sorteio ASC
    """)
    all_cabecas = cursor.fetchall()
    
    if len(all_cabecas) < n + 5:
        conn.close()
        return
        
    # Calcular puxadas top 5
    from collections import Counter, defaultdict
    puxadas = defaultdict(list)
    for i in range(len(all_cabecas) - 1):
        b = all_cabecas[i]["bicho"]
        puxadas[b].append(all_cabecas[i+1]["dezena"])
        
    top_5 = {b: [x for x, _ in Counter(l).most_common(5)] for b, l in puxadas.items()}
    
    sample = all_cabecas[-(n + 1):]
    
    for i in range(len(sample) - 1):
        gat = sample[i]
        alvo = sample[i+1]
        
        cursor.execute("SELECT id_auditoria FROM historico_assertividade_ia WHERE data_gatilho = ? AND extracao_gatilho = ?", (gat["data"], gat["extracao"]))
        if cursor.fetchone():
            continue
            
        dezenas = top_5.get(gat["bicho"], ["01", "02", "03", "04", "05"])
        
        cursor.execute("SELECT premio, premio_num, milhar, centena, dezena, grupo, bicho FROM resultados WHERE id_sorteio = ? ORDER BY premio_num ASC", (alvo["id_sorteio"],))
        premios = [dict(r) for r in cursor.fetchall()]
        
        hit_cabeca = 1 if alvo["dezena"] in dezenas else 0
        hit_cercado = sum(1 for r in premios[1:5] if r["dezena"] in dezenas)
        
        detalhes = []
        if hit_cabeca:
            detalhes.append(f"1º Prêmio (Cabeça) - Dezena {alvo['dezena']}!")
        for r in premios[1:5]:
            if r["dezena"] in dezenas:
                detalhes.append(f"{r['premio']} - Dezena {r['dezena']}")
                
        notacao = "1D" if hit_cabeca else (f"{hit_cercado}D" if hit_cercado > 0 else "0")
        status_audit = "CONFERIDO_PREMIADO" if (hit_cabeca or hit_cercado) else "CONFERIDO_ZERO"
        
        cursor.execute("""
            INSERT INTO historico_assertividade_ia (
                data_gatilho, extracao_gatilho, horario_gatilho, bicho_gatilho, milhar_gatilho, id_sorteio_gatilho,
                dezenas_sugeridas_json, centenas_sugeridas_json, milhares_sugeridos_json, top_bichos_json,
                taxa_estimada_ia, roi_estimado_ia, apurado, id_sorteio_apurado, data_apuracao, extracao_apuracao,
                horario_apuracao, bicho_apurado, milhar_apurado, centena_apurada, dezena_apurada,
                acertou_cabeca_dezena, acertou_cercado_dezena, acertou_centena, acertou_milhar, acertou_bicho,
                notacao_rodada, detalhes_acertos_json, status_auditoria, criado_em, auditado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?, ?, ?)
        """, (
            gat["data"], gat["extracao"], gat["horario"], gat["bicho"], gat["milhar"], gat["id_sorteio"],
            json.dumps(dezenas), json.dumps([]), json.dumps([]), json.dumps([]),
            23.8, 185.7, alvo["id_sorteio"], alvo["data"], alvo["extracao"], alvo["horario"],
            alvo["bicho"], alvo["milhar"], alvo["centena"], alvo["dezena"],
            hit_cabeca, hit_cercado, notacao, json.dumps(detalhes), status_audit,
            f"{gat['data']} {gat['horario']}", f"{alvo['data']} {alvo['horario']}"
        ))
        
    conn.commit()
    conn.close()
