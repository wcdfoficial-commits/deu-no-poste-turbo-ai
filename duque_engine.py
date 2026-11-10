"""
Módulo Duque Turbo AI (Fechamento 3 Bichos & Blindagem Pro)
DEU NO POSTE ANALYTICS PRO
Integração de Fechamentos Matemáticos Otimizados com IA Preditiva e Radar de Co-Atraso
"""

import sqlite3
from typing import Dict, Any, List, Optional
from itertools import combinations
from collections import defaultdict, Counter

from database import DB_PATH, BICHO_INFO, get_connection

def obter_dezenas_ordenadas(grupo: int) -> List[Dict[str, Any]]:
    """
    Retorna as 4 dezenas de um grupo com a frequência real no banco (1º ao 5º prêmio),
    ordenadas da mais quente (frequente) para a mais fria.
    """
    conn = get_connection()
    cursor = conn.cursor()
    dezenas_bicho = BICHO_INFO[grupo]["dezenas"]
    placeholders = ",".join(["?"] * len(dezenas_bicho))
    
    cursor.execute(f"""
        SELECT dezena, COUNT(*) as qtd
        FROM resultados
        WHERE dezena IN ({placeholders}) AND premio_num BETWEEN 1 AND 5
        GROUP BY dezena
    """, dezenas_bicho)
    rows = dict(cursor.fetchall())
    conn.close()
    
    res = []
    for d in dezenas_bicho:
        res.append({
            "dezena": d,
            "saidas": rows.get(d, 0)
        })
    res.sort(key=lambda x: x["saidas"], reverse=True)
    return res

def obter_radar_co_atraso(limite: int = 8) -> List[Dict[str, Any]]:
    """
    Calcula o atraso atual (em sorteios consecutivos) de cada par de animais nos 5 prêmios.
    Retorna os pares com maior atraso entre os de boa frequência histórica (Estratégia Sniper).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_sorteio, grupo
        FROM resultados
        WHERE premio_num BETWEEN 1 AND 5
        ORDER BY id_sorteio ASC, premio_num ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    sorteios_grupos = defaultdict(set)
    max_id = 0
    for id_s, grp in rows:
        if grp:
            sorteios_grupos[id_s].add(int(grp))
            if id_s > max_id:
                max_id = id_s

    sorted_ids = sorted(sorteios_grupos.keys())
    total_sorteios = len(sorted_ids)

    # Último id_sorteio em que cada par apareceu junto
    ultimo_visto = {}
    frequencia_par = Counter()

    for id_s in sorted_ids:
        grps = sorted(list(sorteios_grupos[id_s]))
        for gA, gB in combinations(grps, 2):
            pair = (gA, gB)
            ultimo_visto[pair] = id_s
            frequencia_par[pair] += 1

    pares_analisados = []
    for gA in range(1, 26):
        for gB in range(gA + 1, 26):
            pair = (gA, gB)
            last_id = ultimo_visto.get(pair, 0)
            atraso = total_sorteios - sorted_ids.index(last_id) - 1 if last_id in sorted_ids else total_sorteios
            freq = frequencia_par.get(pair, 0)
            media_ciclo = (total_sorteios / freq) if freq > 0 else 999.0

            pares_analisados.append({
                "grupo_a": gA,
                "bicho_a": BICHO_INFO[gA]["nome"],
                "icone_a": BICHO_INFO[gA]["icone"],
                "grupo_b": gB,
                "bicho_b": BICHO_INFO[gB]["nome"],
                "icone_b": BICHO_INFO[gB]["icone"],
                "frequencia_total": freq,
                "frequencia_pct": round((freq / total_sorteios) * 100, 2),
                "atraso_atual": atraso,
                "ciclo_medio": round(media_ciclo, 1),
                "status_sniper": "ALERTA SNIPER 🎯" if atraso >= 35 and freq >= 50 else ("QUENTE 🔥" if atraso >= 25 else "NORMAL")
            })

    # Filtrar pares relevantes e ordenar por atraso decrescente
    pares_analisados = [p for p in pares_analisados if p["frequencia_total"] >= 45]
    pares_analisados.sort(key=lambda x: (x["atraso_atual"], x["frequencia_total"]), reverse=True)
    return pares_analisados[:limite]

def obter_sugestao_ia_duque() -> Dict[str, Any]:
    """
    Gera a recomendação quântica dos 3 melhores bichos para a próxima extração,
    utilizando a combinação de Puxadas da última cabeça + Matriz de Markov + Radar de Atraso.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_sorteio, data, horario, extracao, grupo, bicho, milhar, centena, dezena
        FROM resultados
        WHERE is_cabeca = 1
        ORDER BY id_sorteio DESC, id_registro DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"status": "error", "mensagem": "Nenhum sorteio registrado"}

    id_s, dt, hor, ext, grp_cab, bicho_cab, milhar, cent, dez = row
    grp_cab = int(grp_cab) if grp_cab else 1

    # Buscar bichos mais puxados por este animal na cabeça para os 5 prêmios seguintes
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r2.grupo, COUNT(*) as qtd
        FROM resultados r1
        JOIN resultados r2 ON r2.id_sorteio = r1.id_sorteio + 1
        WHERE r1.is_cabeca = 1 AND r1.grupo = ? AND r2.premio_num BETWEEN 1 AND 5
        GROUP BY r2.grupo
        ORDER BY qtd DESC
        LIMIT 5
    """, (f"{grp_cab:02d}",))
    top_puxados = cursor.fetchall()
    conn.close()

    grupos_recomendados = []
    if top_puxados:
        for r in top_puxados[:3]:
            try:
                grupos_recomendados.append(int(r[0]))
            except:
                pass

    # Fallback se necessário
    if len(grupos_recomendados) < 3:
        puxadas_default = [((grp_cab + 1) % 25) + 1, ((grp_cab + 5) % 25) + 1, ((grp_cab + 12) % 25) + 1]
        for g in puxadas_default:
            if g not in grupos_recomendados:
                grupos_recomendados.append(g)
            if len(grupos_recomendados) == 3:
                break

    # Montar detalhes de cada bicho recomendado
    detalhes_bichos = []
    for g in grupos_recomendados:
        dezs_info = obter_dezenas_ordenadas(g)
        detalhes_bichos.append({
            "grupo": g,
            "grupo_str": f"{g:02d}",
            "nome": BICHO_INFO[g]["nome"],
            "icone": BICHO_INFO[g]["icone"],
            "todas_dezenas": [d["dezena"] for d in dezs_info],
            "dezenas_quentes": [d["dezena"] for d in dezs_info[:2]],
            "dezenas_detalhe": dezs_info
        })

    radar_sniper = obter_radar_co_atraso(limite=6)

    return {
        "status": "success",
        "ultimo_sorteio": {
            "id_sorteio": id_s,
            "data": dt,
            "horario": hor,
            "extracao": ext,
            "cabeca_grupo": f"{grp_cab:02d}",
            "cabeca_bicho": bicho_cab,
            "milhar": milhar,
            "centena": cent,
            "dezena": dez,
            "icone": BICHO_INFO[grp_cab]["icone"]
        },
        "bichos_recomendados": detalhes_bichos,
        "grupos_sugeridos_ids": grupos_recomendados,
        "radar_sniper": radar_sniper
    }

def gerar_fechamento_duque(
    grupos: List[int],
    modo: str = "blindado_pro",
    valor_por_duque: float = 1.0,
    dezenas_custom: Optional[Dict[int, List[str]]] = None
) -> Dict[str, Any]:
    """
    Gera o fechamento de duques de dezenas para 2 ou 3 bichos.
    Modos:
      - 'smart_12': 12 duques (2 dezenas quentes por bicho) -> Baixo custo, ROI +2400%
      - 'blindado_pro': 12 duques + 3 Duques de Grupo (R$ 3) + 1 Terno de Grupo (R$ 1) -> Seguro e Alavancagem
      - 'smart_27': 27 duques (3 dezenas por bicho) -> Corta a fria
      - 'full_48': 48 duques (todas as 4 dezenas) -> Fechamento tradicional 100%
      - 'full_16': 16 duques (apenas 2 bichos)
    """
    if len(grupos) not in (2, 3):
        return {"status": "error", "mensagem": "Selecione 2 ou 3 bichos para o fechamento."}

    # Ajuste automático se selecionar 2 bichos
    if len(grupos) == 2 and modo in ("full_48", "smart_27"):
        modo = "full_16"

    # Seleção de dezenas por grupo
    dezenas_por_grupo = {}
    detalhes_grupos = []

    for g in grupos:
        info_dezs = obter_dezenas_ordenadas(g)
        if dezenas_custom and g in dezenas_custom:
            dezs = dezenas_custom[g]
        elif modo in ("smart_12", "blindado_pro"):
            dezs = [d["dezena"] for d in info_dezs[:2]]
        elif modo == "smart_27":
            dezs = [d["dezena"] for d in info_dezs[:3]]
        else: # full_48, full_16
            dezs = [d["dezena"] for d in info_dezs]

        dezenas_por_grupo[g] = dezs
        detalhes_grupos.append({
            "grupo": g,
            "grupo_str": f"{g:02d}",
            "nome": BICHO_INFO[g]["nome"],
            "icone": BICHO_INFO[g]["icone"],
            "dezenas_escolhidas": dezs,
            "dezenas_todas": BICHO_INFO[g]["dezenas"]
        })

    # Geração dos pares de Duques de Dezenas
    duques = []
    duques_detalhados = []
    
    for gA, gB in combinations(grupos, 2):
        nome_par = f"{BICHO_INFO[gA]['nome']} x {BICHO_INFO[gB]['nome']}"
        for da in dezenas_por_grupo[gA]:
            for db in dezenas_por_grupo[gB]:
                duques.append(f"{da} x {db}")
                duques_detalhados.append({
                    "d1": da,
                    "d2": db,
                    "grupo_a": gA,
                    "grupo_b": gB,
                    "label": f"{da} x {db}",
                    "origem": nome_par
                })

    custo_duques = len(duques) * valor_por_duque
    custo_total = custo_duques

    # Apostas de cobertura (Hedge)
    hedge_duque_grupo = []
    hedge_terno_grupo = None

    if modo == "blindado_pro":
        # 1 aposta em Duque de Grupo para cada par de bichos
        for gA, gB in combinations(grupos, 2):
            hedge_duque_grupo.append({
                "grupo_a": gA,
                "grupo_b": gB,
                "label": f"{BICHO_INFO[gA]['nome']} e {BICHO_INFO[gB]['nome']} (G{gA:02d} e G{gB:02d})",
                "valor": 1.0,
                "premio_potencial": 18.50
            })
        custo_total += len(hedge_duque_grupo) * 1.0

        if len(grupos) == 3:
            hedge_terno_grupo = {
                "grupos": grupos,
                "label": f"{BICHO_INFO[grupos[0]]['nome']}, {BICHO_INFO[grupos[1]]['nome']} e {BICHO_INFO[grupos[2]]['nome']} (G{grupos[0]:02d}, G{grupos[1]:02d}, G{grupos[2]:02d})",
                "valor": 1.0,
                "premio_potencial": 130.00
            }
            custo_total += 1.0

    # Estimativa de prêmios
    premio_duque_unit = valor_por_duque * 300.0
    premio_min_acerto = premio_duque_unit # acerto de 1 duque
    premio_max_acerto = (premio_duque_unit * 3) if len(grupos) == 3 else premio_duque_unit

    if modo == "blindado_pro":
        premio_min_acerto += 18.50
        premio_max_acerto += (18.50 * 3) + 130.00

    lucro_min = premio_min_acerto - custo_total
    roi_min = (lucro_min / custo_total) * 100 if custo_total > 0 else 0

    lucro_max = premio_max_acerto - custo_total
    roi_max = (lucro_max / custo_total) * 100 if custo_total > 0 else 0

    # Texto formatado para o bilhete (copiar e colar)
    linhas_bilhete = [
        f"🎯 *DEU NO POSTE TURBO AI - FECHAMENTO DUQUE TURBO*",
        f"📅 Modo: {modo.upper()} | Bichos: {', '.join([b['nome'] for b in detalhes_grupos])}",
        f"💰 Custo Total: R$ {custo_total:.2f} | Jogos: {len(duques)} duques",
        f"--------------------------------------------------",
        f"📋 *DUQUES DE DEZENAS (R$ {valor_por_duque:.2f} cada):*"
    ]
    for i, d in enumerate(duques, 1):
        linhas_bilhete.append(f"{i:02d}. {d}")

    if hedge_duque_grupo:
        linhas_bilhete.append(f"\n🛡️ *HEDGE: DUQUES DE GRUPO (R$ 1,00 cada):*")
        for h in hedge_duque_grupo:
            linhas_bilhete.append(f"• {h['label']}")

    if hedge_terno_grupo:
        linhas_bilhete.append(f"\n🚀 *SUPER BÔNUS: TERNO DE GRUPO (R$ 1,00):*")
        linhas_bilhete.append(f"• {hedge_terno_grupo['label']}")

    linhas_bilhete.append(f"--------------------------------------------------")
    linhas_bilhete.append(f"⚡ Gerado por https://deu-no-poste-turbo-ai.onrender.com/")

    return {
        "status": "success",
        "modo": modo,
        "grupos": detalhes_grupos,
        "total_duques": len(duques),
        "custo_duques": custo_duques,
        "custo_total": custo_total,
        "valor_por_duque": valor_por_duque,
        "premio_min_acerto": premio_min_acerto,
        "premio_max_acerto": premio_max_acerto,
        "lucro_min": lucro_min,
        "lucro_max": lucro_max,
        "roi_min_pct": round(roi_min, 1),
        "roi_max_pct": round(roi_max, 1),
        "duques": duques,
        "duques_detalhados": duques_detalhados,
        "hedge_duque_grupo": hedge_duque_grupo,
        "hedge_terno_grupo": hedge_terno_grupo,
        "texto_bilhete": "\n".join(linhas_bilhete)
    }

def conferir_fechamento_duque(
    duques: List[str],
    grupos_apostados: List[int],
    id_sorteio: Optional[int] = None,
    modo: str = "blindado_pro",
    valor_por_duque: float = 1.0
) -> Dict[str, Any]:
    """
    Confere os duques de dezenas e coberturas contra o sorteio apurado (ou o último do banco).
    Gera o selo BINGO para cada combinação vencedora.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if id_sorteio:
        cursor.execute("""
            SELECT id_sorteio, data, horario, extracao, premio_num, dezena, grupo, bicho
            FROM resultados
            WHERE id_sorteio = ? AND premio_num BETWEEN 1 AND 5
            ORDER BY premio_num ASC
        """, (id_sorteio,))
    else:
        # Último sorteio disponível com 5 prêmios
        cursor.execute("""
            SELECT id_sorteio FROM resultados 
            WHERE is_cabeca = 1 
            ORDER BY id_sorteio DESC LIMIT 1
        """)
        row = cursor.fetchone()
        last_id = row[0] if row else 1
        cursor.execute("""
            SELECT id_sorteio, data, horario, extracao, premio_num, dezena, grupo, bicho
            FROM resultados
            WHERE id_sorteio = ? AND premio_num BETWEEN 1 AND 5
            ORDER BY premio_num ASC
        """, (last_id,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"status": "error", "mensagem": "Nenhum resultado encontrado para apuração."}

    id_s = rows[0][0]
    data = rows[0][1]
    horario = rows[0][2]
    extracao = rows[0][3]

    dezenas_sorteadas = set()
    grupos_sorteados = set()
    tabela_resultado = []

    for r in rows:
        p_num, dez, grp, bicho = r[4], r[5], r[6], r[7]
        dez_str = f"{int(dez):02d}" if dez is not None else ""
        grp_int = int(grp) if grp is not None else 0
        if dez_str:
            dezenas_sorteadas.add(dez_str)
        if grp_int:
            grupos_sorteados.add(grp_int)

        tabela_resultado.append({
            "premio": f"{p_num}º",
            "dezena": dez_str,
            "grupo": f"{grp_int:02d}",
            "bicho": bicho,
            "icone": BICHO_INFO.get(grp_int, {}).get("icone", "🎲")
        })

    # Conferência dos Duques de Dezenas
    duques_auditados = []
    acertos_duque_count = 0

    for d in duques:
        partes = [p.strip() for p in d.split("x")]
        if len(partes) == 2:
            d1, d2 = partes[0], partes[1]
            acertou = (d1 in dezenas_sorteadas) and (d2 in dezenas_sorteadas)
            if acertou:
                acertos_duque_count += 1
            duques_auditados.append({
                "duque": d,
                "d1": d1,
                "d2": d2,
                "d1_sorteada": d1 in dezenas_sorteadas,
                "d2_sorteada": d2 in dezenas_sorteadas,
                "bingo": acertou,
                "premio_ganho": (valor_por_duque * 300.0) if acertou else 0.0
            })

    # Conferência dos Hedges (se houver)
    acertos_hedge_duque = 0
    hedge_duque_auditados = []
    for gA, gB in combinations(grupos_apostados, 2):
        acertou_grupo = (gA in grupos_sorteados) and (gB in grupos_sorteados)
        if acertou_grupo:
            acertos_hedge_duque += 1
        hedge_duque_auditados.append({
            "par": f"{BICHO_INFO[gA]['nome']} e {BICHO_INFO[gB]['nome']}",
            "bingo": acertou_grupo,
            "premio": 18.50 if acertou_grupo else 0.0
        })

    acertou_terno_grupo = False
    if len(grupos_apostados) == 3 and all(g in grupos_sorteados for g in grupos_apostados):
        acertou_terno_grupo = True

    # Finanças
    custo_total = len(duques) * valor_por_duque
    if modo == "blindado_pro":
        custo_total += len(hedge_duque_auditados) * 1.0
        if len(grupos_apostados) == 3:
            custo_total += 1.0

    retorno_bruto = (acertos_duque_count * valor_por_duque * 300.0)
    if modo == "blindado_pro":
        retorno_bruto += (acertos_hedge_duque * 18.50)
        if acertou_terno_grupo:
            retorno_bruto += 130.00

    lucro_liquido = retorno_bruto - custo_total
    roi_pct = (lucro_liquido / custo_total) * 100 if custo_total > 0 else 0

    return {
        "status": "success",
        "sorteio_apurado": {
            "id_sorteio": id_s,
            "data": data,
            "horario": horario,
            "extracao": extracao,
            "premios": tabela_resultado
        },
        "total_jogos": len(duques),
        "acertos_duque_count": acertos_duque_count,
        "acertos_hedge_duque": acertos_hedge_duque,
        "acertou_terno_grupo": acertou_terno_grupo,
        "teve_bingo": (acertos_duque_count > 0 or acertos_hedge_duque > 0 or acertou_terno_grupo),
        "custo_total": custo_total,
        "retorno_bruto": retorno_bruto,
        "lucro_liquido": lucro_liquido,
        "roi_pct": round(roi_pct, 1),
        "duques_auditados": duques_auditados,
        "hedge_duque_auditados": hedge_duque_auditados
    }
