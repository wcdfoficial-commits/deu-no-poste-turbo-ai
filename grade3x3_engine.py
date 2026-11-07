"""
Módulo Grade 3x3 Turbo (Hashtag Engine) + Puxadas + Histórico 24h
DEU NO POSTE ANALYTICS PRO
"""

import sqlite3
from typing import Dict, Any, List, Optional
from database import DB_PATH, BICHO_INFO

# Tabela tradicional de Puxadas do Jogo do Bicho
PUXADAS = {
    1: [25, 2, 10],   # Avestruz puxa Vaca, Águia, Coelho
    2: [1, 9, 11],    # Águia puxa Avestruz, Cobra, Cavalo
    3: [11, 13, 24],  # Burro puxa Cavalo, Galo, Veado
    4: [14, 7, 5],    # Borboleta puxa Gato, Carneiro, Cachorro
    5: [4, 14, 18],   # Cachorro puxa Borboleta, Gato, Porco
    6: [7, 8, 9],     # Cabra puxa Carneiro, Camelo, Cobra
    7: [6, 4, 16],    # Carneiro puxa Cabra, Borboleta, Leão
    8: [6, 7, 9],     # Camelo puxa Cabra, Carneiro, Cobra
    9: [13, 15, 2],   # Cobra puxa Galo, Jacaré, Águia
    10: [1, 14, 19],  # Coelho puxa Avestruz, Gato, Pavão
    11: [3, 2, 24],   # Cavalo puxa Burro, Águia, Veado
    12: [13, 14, 15], # Elefante puxa Galo, Gato, Jacaré
    13: [9, 3, 12],   # Galo puxa Cobra, Burro, Elefante
    14: [4, 5, 10],   # Gato puxa Borboleta, Cachorro, Coelho
    15: [9, 12, 16],  # Jacaré puxa Cobra, Elefante, Leão
    16: [7, 15, 18],  # Leão puxa Carneiro, Jacaré, Porco
    17: [18, 19, 20], # Macaco puxa Porco, Pavão, Peru
    18: [17, 16, 5],  # Porco puxa Macaco, Leão, Cachorro
    19: [17, 10, 20], # Pavão puxa Macaco, Coelho, Peru
    20: [17, 19, 21], # Peru puxa Macaco, Pavão, Touro
    21: [20, 22, 23], # Touro puxa Peru, Tigre, Urso
    22: [21, 23, 24], # Tigre puxa Touro, Urso, Veado
    23: [21, 22, 25], # Urso puxa Touro, Tigre, Vaca
    24: [3, 11, 22],  # Veado puxa Burro, Cavalo, Tigre
    25: [1, 23, 24]   # Vaca puxa Avestruz, Urso, Veado
}

MULTIPLICADORES = {
    "centena": {"cabeca": 600.0, "cercado": 120.0},
    "milhar": {"cabeca": 4000.0, "cercado": 800.0},
    "dezena": {"cabeca": 60.0, "cercado": 12.0},
    "grupo": {"cabeca": 18.0, "cercado": 3.6}
}

def dezena_to_grupo(dez_str: str) -> int:
    try:
        d = int(dez_str)
        return 25 if d == 0 else ((d - 1) // 4) + 1
    except Exception:
        return 1

def build_grade_3x3(g1: int, g2: int) -> Dict[str, Any]:
    """
    Constrói a grade 3x3 do Jogo da Velha baseada nos grupos 1 e 2 da PPT
    usando a regra das diferenças estritas ("pauzinhos").
    """
    tl = g1 // 10
    tr = g1 % 10
    bl = g2 // 10
    br = g2 % 10

    tm = max(0, abs(tl - tr) - 1)
    rm = max(0, abs(tr - br) - 1)
    bm = max(0, abs(bl - br) - 1)
    lm = max(0, abs(tl - bl) - 1)
    center = max(0, abs(lm - rm) - 1)

    matriz = [
        [tl, tm, tr],
        [lm, center, rm],
        [bl, bm, br]
    ]

    celulas = [
        {"pos": "0,0", "linha": 0, "col": 0, "valor": tl, "tipo": "vertice", "origem": f"1º Prêmio PPT (Dezena Grupo {g1:02d})"},
        {"pos": "0,1", "linha": 0, "col": 1, "valor": tm, "tipo": "diferenca", "origem": f"Entre {tl} e {tr}"},
        {"pos": "0,2", "linha": 0, "col": 2, "valor": tr, "tipo": "vertice", "origem": f"1º Prêmio PPT (Unidade Grupo {g1:02d})"},
        {"pos": "1,0", "linha": 1, "col": 0, "valor": lm, "tipo": "diferenca", "origem": f"Entre {tl} e {bl}"},
        {"pos": "1,1", "linha": 1, "col": 1, "valor": center, "tipo": "centro", "origem": f"Eixo Central entre {lm} e {rm}"},
        {"pos": "1,2", "linha": 1, "col": 2, "valor": rm, "tipo": "diferenca", "origem": f"Entre {tr} e {br}"},
        {"pos": "2,0", "linha": 2, "col": 0, "valor": bl, "tipo": "vertice", "origem": f"2º Prêmio PPT (Dezena Grupo {g2:02d})"},
        {"pos": "2,1", "linha": 2, "col": 1, "valor": bm, "tipo": "diferenca", "origem": f"Entre {bl} e {br}"},
        {"pos": "2,2", "linha": 2, "col": 2, "valor": br, "tipo": "vertice", "origem": f"2º Prêmio PPT (Unidade Grupo {g2:02d})"}
    ]

    return {
        "matriz": matriz,
        "celulas": celulas,
        "grupo_1": g1,
        "grupo_2": g2,
        "digitos_unicos": sorted(list(set([tl, tm, tr, lm, center, rm, bl, bm, br])))
    }

def extrair_caminhos_grade(grid: List[List[int]]) -> Dict[str, List[str]]:
    moves = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    centenas = set()
    milhares = set()
    dezenas = set()

    def dfs(r, c, path, visited):
        val = "".join(str(grid[pr][pc]) for pr, pc in path)
        if len(path) == 2:
            dezenas.add(val)
        elif len(path) == 3:
            centenas.add(val)
        elif len(path) == 4:
            milhares.add(val)
            return

        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 3 and 0 <= nc < 3 and (nr, nc) not in visited:
                visited.add((nr, nc))
                dfs(nr, nc, path + [(nr, nc)], visited)
                visited.remove((nr, nc))

    for r in range(3):
        for c in range(3):
            dfs(r, c, [(r, c)], {(r, c)})

    # Linhas e diagonais diretas garantidas
    linhas = [
        [grid[0][0], grid[0][1], grid[0][2]],
        [grid[1][0], grid[1][1], grid[1][2]],
        [grid[2][0], grid[2][1], grid[2][2]],
        [grid[0][0], grid[1][0], grid[2][0]],
        [grid[0][1], grid[1][1], grid[2][1]],
        [grid[0][2], grid[1][2], grid[2][2]],
        [grid[0][0], grid[1][1], grid[2][2]],
        [grid[0][2], grid[1][1], grid[2][0]],
    ]
    for lin in linhas:
        c1 = f"{lin[0]}{lin[1]}{lin[2]}"
        c2 = f"{lin[2]}{lin[1]}{lin[0]}"
        centenas.add(c1)
        centenas.add(c2)
        dezenas.add(c1[-2:])
        dezenas.add(c2[-2:])

    return {
        "centenas": sorted(list(centenas)),
        "milhares": sorted(list(milhares)),
        "dezenas": sorted(list(dezenas))
    }

def obter_dados_contexto(data_alvo: Optional[str] = None) -> Dict[str, Any]:
    """
    Busca o sorteio PPT do dia (para montar a grade), o sorteio imediatamente anterior
    (para cálculo das puxadas) e as últimas 24h de sorteios.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Pega os últimos registros com PPT
    query_ppt = """
        SELECT data, id_sorteio, extracao FROM resultados 
        WHERE extracao = 'PPT' 
        ORDER BY data DESC, id_sorteio DESC LIMIT 1
    """
    if data_alvo:
        cursor.execute("SELECT data, id_sorteio, extracao FROM resultados WHERE extracao = 'PPT' AND data <= ? ORDER BY data DESC LIMIT 1", (data_alvo,))
    else:
        cursor.execute(query_ppt)
    row_ppt = cursor.fetchone()

    if not row_ppt:
        # Fallback genérico caso banco esteja vazio
        conn.close()
        return {
            "ppt_data": "Exemplo",
            "g1": 9,
            "g2": 13,
            "bicho_1": "Cobra",
            "bicho_2": "Galo",
            "ultimo_sorteio": None,
            "historico_24h": []
        }

    id_ppt = row_ppt["id_sorteio"]
    data_ppt = row_ppt["data"]

    # Busca prêmios 1 e 2 da PPT
    cursor.execute("""
        SELECT premio_num, milhar, centena, dezena, grupo, bicho 
        FROM resultados 
        WHERE id_sorteio = ? AND premio_num IN (1, 2)
        ORDER BY premio_num ASC
    """, (id_ppt,))
    premios_ppt = [dict(r) for r in cursor.fetchall()]

    g1 = int(premios_ppt[0]["grupo"]) if len(premios_ppt) > 0 else 9
    g2 = int(premios_ppt[1]["grupo"]) if len(premios_ppt) > 1 else 13
    b1 = premios_ppt[0]["bicho"] if len(premios_ppt) > 0 else "Cobra"
    b2 = premios_ppt[1]["bicho"] if len(premios_ppt) > 1 else "Galo"

    # 2. Pega o sorteio mais recente do banco (para puxadas ativas)
    cursor.execute("""
        SELECT id_sorteio, data, horario, extracao 
        FROM resultados 
        ORDER BY data DESC, horario DESC, id_sorteio DESC LIMIT 1
    """)
    ult_row = cursor.fetchone()
    ultimo_sorteio = None
    if ult_row:
        cursor.execute("SELECT * FROM resultados WHERE id_sorteio = ? ORDER BY premio_num ASC", (ult_row["id_sorteio"],))
        ultimo_sorteio = {
            "id_sorteio": ult_row["id_sorteio"],
            "data": ult_row["data"],
            "horario": ult_row["horario"],
            "extracao": ult_row["extracao"],
            "premios": [dict(r) for r in cursor.fetchall()]
        }

    # 3. Pega as últimas 24h de sorteios (últimos 5 sorteios)
    cursor.execute("""
        SELECT DISTINCT id_sorteio, data, horario, extracao 
        FROM resultados 
        ORDER BY data DESC, horario DESC, id_sorteio DESC LIMIT 5
    """)
    recentes_sorteios = [dict(r) for r in cursor.fetchall()]
    historico_24h = []
    for s in recentes_sorteios:
        cursor.execute("SELECT * FROM resultados WHERE id_sorteio = ? ORDER BY premio_num ASC", (s["id_sorteio"],))
        historico_24h.append({
            "meta": s,
            "premios": [dict(r) for r in cursor.fetchall()]
        })

    conn.close()
    return {
        "ppt_data": data_ppt,
        "ppt_id": id_ppt,
        "g1": g1,
        "g2": g2,
        "bicho_1": b1,
        "bicho_2": b2,
        "premios_ppt": premios_ppt,
        "ultimo_sorteio": ultimo_sorteio,
        "historico_24h": historico_24h
    }

def gerar_top_k_grade3x3(
    qtd_cartoes: int = 3,
    modalidade: str = "centena",
    posicao: str = "cabeca",
    valor_aposta: float = 1.0,
    bicho_preferido: Optional[str] = None,
    data_alvo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executa a seleção e ranqueamento multicamada das melhores alternativas.
    """
    contexto = obter_dados_contexto(data_alvo)
    grid_info = build_grade_3x3(contexto["g1"], contexto["g2"])
    pools = extrair_caminhos_grade(grid_info["matriz"])

    if modalidade == "milhar":
        candidatos_base = pools["milhares"]
    elif modalidade == "dezena":
        candidatos_base = pools["dezenas"]
    elif modalidade == "grupo":
        # grupos derivados das dezenas da grade
        grupos_set = set(dezena_to_grupo(d) for d in pools["dezenas"])
        candidatos_base = [f"{g:02d}" for g in sorted(grupos_set)]
    else: # centena
        candidatos_base = pools["centenas"]

    # Extrai informações para pontuação
    ultimo_sorteio = contexto.get("ultimo_sorteio")
    prev_cabeca_grp = None
    prev_dezenas = set()
    if ultimo_sorteio and ultimo_sorteio.get("premios"):
        cab = ultimo_sorteio["premios"][0]
        prev_cabeca_grp = int(cab["grupo"])
        for p in ultimo_sorteio["premios"]:
            prev_dezenas.add(str(p["dezena"]).zfill(2))

    # Dezenas das últimas 24h
    l24_dezenas = []
    for s in contexto.get("historico_24h", []):
        for p in s.get("premios", []):
            l24_dezenas.append(str(p["dezena"]).zfill(2))

    linhas_retas = [
        [grid_info["matriz"][0][0], grid_info["matriz"][0][1], grid_info["matriz"][0][2]],
        [grid_info["matriz"][1][0], grid_info["matriz"][1][1], grid_info["matriz"][1][2]],
        [grid_info["matriz"][2][0], grid_info["matriz"][2][1], grid_info["matriz"][2][2]],
        [grid_info["matriz"][0][0], grid_info["matriz"][1][0], grid_info["matriz"][2][0]],
        [grid_info["matriz"][0][1], grid_info["matriz"][1][1], grid_info["matriz"][2][1]],
        [grid_info["matriz"][0][2], grid_info["matriz"][1][2], grid_info["matriz"][2][2]],
        [grid_info["matriz"][0][0], grid_info["matriz"][1][1], grid_info["matriz"][2][2]],
        [grid_info["matriz"][0][2], grid_info["matriz"][1][1], grid_info["matriz"][2][0]],
    ]

    scored = []
    for cand in candidatos_base:
        score = 5.0 # base score
        motivos = []

        if modalidade == "grupo":
            grp_num = int(cand)
            bicho_nome = BICHO_INFO.get(grp_num, {}).get("nome", "")
            icone = BICHO_INFO.get(grp_num, {}).get("icone", "🎯")
            dez_ref = BICHO_INFO.get(grp_num, {}).get("dezenas", ["00"])[0]
        else:
            dez_ref = cand[-2:]
            grp_num = dezena_to_grupo(dez_ref)
            bicho_nome = BICHO_INFO.get(grp_num, {}).get("nome", "")
            icone = BICHO_INFO.get(grp_num, {}).get("icone", "🎯")

        # Filtro de bicho preferido se solicitado pelo usuário
        if bicho_preferido and bicho_preferido != "Todos":
            if bicho_nome.lower() != bicho_preferido.lower() and f"{grp_num:02d}" != bicho_preferido:
                continue

        # 1. Puxada clássica do último bicho
        if prev_cabeca_grp and grp_num in PUXADAS.get(prev_cabeca_grp, []):
            score += 3.5
            puxador = BICHO_INFO.get(prev_cabeca_grp, {}).get("nome", f"Grupo {prev_cabeca_grp:02d}")
            motivos.append(f"Puxada clássica do {puxador} que saiu na cabeça do último sorteio")

        # 2. Eco do sorteio anterior
        if dez_ref in prev_dezenas:
            score += 2.5
            motivos.append(f"Dezena {dez_ref} presente no sorteio anterior (efeito repetição)")

        # 3. Frequência 24h
        contagem = l24_dezenas.count(dez_ref)
        if 1 <= contagem <= 3:
            score += 1.8
            motivos.append(f"Dezena ativa no ciclo (apareceu {contagem}x nas últimas 24h)")
        elif contagem == 0:
            score += 1.2
            motivos.append(f"Dezena atrasada no ciclo de 24h (potencial de compensação)")

        # 4. Estrutura geométrica na grade
        if modalidade in ["centena", "milhar"]:
            digitos_cand = [int(ch) for ch in cand[-3:]]
            for lin in linhas_retas:
                if digitos_cand == lin or digitos_cand == lin[::-1]:
                    score += 2.2
                    motivos.append("Alinhamento direto na grade (linha ou diagonal limpa)")
                    break

        # Motivo fallback caso tenha poucos
        if not motivos:
            motivos.append("Combinação adjacente fechada no quadrante da grade")

        # Nível de relevância
        rel_label = "Alta Relevância" if score >= 8.5 else ("Média-Alta" if score >= 7.0 else "Equilibrada")

        scored.append({
            "numero": cand,
            "grupo": f"{grp_num:02d}",
            "bicho": bicho_nome,
            "icone": icone,
            "dezena": dez_ref,
            "score": round(score, 1),
            "nivel": rel_label,
            "motivos": motivos
        })

    # Ordena pelo score decrescente
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_cartoes = scored[:qtd_cartoes]

    # Resumo financeiro
    mults = MULTIPLICADORES.get(modalidade, {"cabeca": 600.0, "cercado": 120.0})
    mult_ativo = mults["cabeca"] if posicao == "cabeca" else mults["cercado"]
    custo_total = len(top_cartoes) * valor_aposta
    premio_por_cartao = valor_aposta * mult_ativo

    return {
        "status": "success",
        "parametros": {
            "qtd_solicitada": qtd_cartoes,
            "qtd_gerada": len(top_cartoes),
            "modalidade": modalidade,
            "posicao": posicao,
            "valor_por_cartao": valor_aposta,
            "custo_total": custo_total,
            "multiplicador": mult_ativo,
            "premio_potencial_por_cartao": premio_por_cartao,
            "bicho_preferido": bicho_preferido or "Todos"
        },
        "contexto_sorteio": {
            "ppt_data": contexto["ppt_data"],
            "ppt_id": contexto.get("ppt_id"),
            "g1": f"{contexto['g1']:02d}",
            "g2": f"{contexto['g2']:02d}",
            "bicho_1": contexto["bicho_1"],
            "bicho_2": contexto["bicho_2"],
            "ultimo_sorteio": {
                "extracao": ultimo_sorteio["extracao"] if ultimo_sorteio else "N/A",
                "horario": ultimo_sorteio["horario"] if ultimo_sorteio else "N/A",
                "bicho_cabeca": ultimo_sorteio["premios"][0]["bicho"] if (ultimo_sorteio and ultimo_sorteio.get("premios")) else "N/A"
            } if ultimo_sorteio else None
        },
        "grade_3x3": grid_info,
        "cartoes": top_cartoes
    }
