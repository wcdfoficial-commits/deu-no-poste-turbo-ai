import sqlite3
import os
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
