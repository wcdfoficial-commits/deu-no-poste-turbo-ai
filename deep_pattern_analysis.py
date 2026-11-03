import sqlite3
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

db_path = r"C:\Users\Derley\.gemini\antigravity\scratch\deu_no_poste_analytics\deu_no_poste_12m.db"
conn = sqlite3.connect(db_path)

# Carregar dados ordenados cronologicamente
df = pd.read_sql("SELECT * FROM resultados ORDER BY id_registro ASC", conn)
conn.close()

# Filtrar apenas 1º prêmio (cabeça) ordenado por id_sorteio
df_cabeca = df[df["is_cabeca"] == 1].sort_values("id_sorteio").reset_index(drop=True)

print(f"Total de sorteios na cabeça analisados: {len(df_cabeca)}")

# ==============================================================================
# 1. MATRIZ DE TRANSIÇÃO (PUXADA GERAL NA CABEÇA: B_t -> B_t+1)
# ==============================================================================
transitions = defaultdict(Counter)
for i in range(len(df_cabeca) - 1):
    curr_b = df_cabeca.iloc[i]["bicho"]
    next_b = df_cabeca.iloc[i+1]["bicho"]
    transitions[curr_b][next_b] += 1

print("\n" + "="*70)
print("1. TOP TRANSIÇÕES GERAIS (BICHO QUE MAIS PUXA OUTRO BICHO NA CABEÇA)")
print("Baseline aleatório esperado = 4.0% (1/25)")
print("="*70)

top_general_transitions = []
for curr_b, counter in transitions.items():
    total_occurrences = sum(counter.values())
    for next_b, count in counter.most_common(2):
        prob = (count / total_occurrences) * 100
        lift = prob / 4.0
        top_general_transitions.append({
            "bicho_origem": curr_b,
            "bicho_destino": next_b,
            "vezes": count,
            "total_origem": total_occurrences,
            "probabilidade": prob,
            "lift": lift
        })

top_gen_df = pd.DataFrame(top_general_transitions).sort_values("probabilidade", ascending=False)
for _, r in top_gen_df.head(15).iterrows():
    print(f"Quando sai [{r['bicho_origem']:<9}] -> Próximo: [{r['bicho_destino']:<9}] | {r['vezes']:>2}/{r['total_origem']}x ({r['probabilidade']:>4.1f}%) | Força: {r['lift']:.2f}x o esperado")

# ==============================================================================
# 2. PUXADAS POR HORÁRIO ESPECÍFICO (TRANSIÇÃO ENTRE EXTRAÇÕES FIXAS)
# Ex: PTM -> PT, PT -> PTV, PTV -> PTN/FED, CORUJA -> PPT (Overnight)
# ==============================================================================
print("\n" + "="*70)
print("2. PUXADAS ESPECÍFICAS DE HORÁRIO A HORÁRIO")
print("="*70)

# Criar tabela dinâmica pivotada por id_sorteio e extração
df_cabeca["next_bicho"] = df_cabeca["bicho"].shift(-1)
df_cabeca["next_extracao"] = df_cabeca["extracao"].shift(-1)
df_cabeca["next_grupo"] = df_cabeca["grupo"].shift(-1)
df_cabeca["next_data"] = df_cabeca["data"].shift(-1)

# A) DA CORUJA (21:20) PARA A PPT (09:20 do dia seguinte) - "Puxada da Madrugada"
coruja_to_ppt = df_cabeca[(df_cabeca["extracao"] == "CORUJA") & (df_cabeca["next_extracao"] == "PPT")]
print(f"\nA) PUXADA DA MADRUGADA: CORUJA (21:20) -> PPT (09:20 dia seguinte) [Total amostras: {len(coruja_to_ppt)}]")
trans_overnight = defaultdict(Counter)
for _, r in coruja_to_ppt.iterrows():
    trans_overnight[r["bicho"]][r["next_bicho"]] += 1

overnight_list = []
for orig, cnt in trans_overnight.items():
    tot = sum(cnt.values())
    if tot >= 8: # Amostra mínima
        for dest, c in cnt.most_common(1):
            p = (c / tot) * 100
            overnight_list.append({"origem": orig, "destino": dest, "acertos": c, "total": tot, "taxa": p})

for r in sorted(overnight_list, key=lambda x: x["taxa"], reverse=True)[:10]:
    print(f"CORUJA [{r['origem']:<9}] -> PPT [{r['destino']:<9}] : {r['acertos']}/{r['total']}x ({r['taxa']:.1f}%) - {r['taxa']/4.0:.2f}x do acaso")

# B) DO PTM (11:20) PARA A PT (14:20)
ptm_to_pt = df_cabeca[(df_cabeca["extracao"] == "PTM") & (df_cabeca["next_extracao"] == "PT")]
print(f"\nB) PUXADA DA TARDE 1: PTM (11:20) -> PT (14:20) [Total amostras: {len(ptm_to_pt)}]")
trans_ptm_pt = defaultdict(Counter)
for _, r in ptm_to_pt.iterrows():
    trans_ptm_pt[r["bicho"]][r["next_bicho"]] += 1

ptm_list = []
for orig, cnt in trans_ptm_pt.items():
    tot = sum(cnt.values())
    if tot >= 8:
        for dest, c in cnt.most_common(1):
            p = (c / tot) * 100
            ptm_list.append({"origem": orig, "destino": dest, "acertos": c, "total": tot, "taxa": p})

for r in sorted(ptm_list, key=lambda x: x["taxa"], reverse=True)[:10]:
    print(f"PTM [{r['origem']:<9}] -> PT [{r['destino']:<9}] : {r['acertos']}/{r['total']}x ({r['taxa']:.1f}%) - {r['taxa']/4.0:.2f}x do acaso")

# C) DO PTV (16:00) PARA A PTN/FEDERAL (18:20 / 19:00)
ptv_to_ptn = df_cabeca[(df_cabeca["extracao"] == "PTV") & (df_cabeca["next_extracao"].isin(["PTN", "FEDERAL"]))]
print(f"\nC) PUXADA DA NOITE: PTV (16:00) -> PTN/FEDERAL [Total amostras: {len(ptv_to_ptn)}]")
trans_ptv = defaultdict(Counter)
for _, r in ptv_to_ptn.iterrows():
    trans_ptv[r["bicho"]][r["next_bicho"]] += 1

ptv_list = []
for orig, cnt in trans_ptv.items():
    tot = sum(cnt.values())
    if tot >= 8:
        for dest, c in cnt.most_common(1):
            p = (c / tot) * 100
            ptv_list.append({"origem": orig, "destino": dest, "acertos": c, "total": tot, "taxa": p})

for r in sorted(ptv_list, key=lambda x: x["taxa"], reverse=True)[:10]:
    print(f"PTV [{r['origem']:<9}] -> NOITE [{r['destino']:<9}] : {r['acertos']}/{r['total']}x ({r['taxa']:.1f}%) - {r['taxa']/4.0:.2f}x do acaso")

# ==============================================================================
# 3. FENÔMENO DO "ECO" (SUBIDA DO 2º-5º PRÊMIO PARA O 1º PRÊMIO SEGUINTE)
# Se um bicho aparece entre o 2º e 5º prêmio, qual a chance de ele "subir" para a cabeça no próximo sorteio?
# ==============================================================================
print("\n" + "="*70)
print("3. TESTE DO FENÔMENO DE SUBIDA: BICHOS DO 2º-5º PRÊMIO QUE SUBEM PARA A CABEÇA")
print("Baseline esperado se for aleatório = 4 bichos no 2º ao 5º -> 4 * 4% = 16.0%")
print("="*70)

sorteios_ids = sorted(df["id_sorteio"].unique())
subida_count = 0
total_sorteios_analisados = 0
subidas_por_bicho = Counter()

for s_id in sorteios_ids[:-1]:
    # Prêmios do sorteio atual
    draw_curr = df[df["id_sorteio"] == s_id]
    bichos_corpo = set(draw_curr[draw_curr["premio_num"].isin([2, 3, 4, 5])]["bicho"])
    
    # Cabeça do sorteio seguinte
    draw_next = df[(df["id_sorteio"] == s_id + 1) & (df["premio_num"] == 1)]
    if draw_next.empty:
        continue
    bicho_cabeca_next = draw_next.iloc[0]["bicho"]
    
    total_sorteios_analisados += 1
    if bicho_cabeca_next in bichos_corpo:
        subida_count += 1
        subidas_por_bicho[bicho_cabeca_next] += 1

pct_subida = (subida_count / total_sorteios_analisados) * 100
print(f"Total de sorteios consecutivos avaliados: {total_sorteios_analisados}")
print(f"Vezes em que o bicho da Cabeça estava presente no 2º-5º prêmio do sorteio IMEDIATAMENTE ANTERIOR:")
print(f"-> {subida_count} vezes ({pct_subida:.2f}% de acerto!) | Baseline aleatório: 16.0%")
print(f"Top Bichos que MAIS SUBIRAM do corpo para a cabeça:")
for b, c in subidas_por_bicho.most_common(5):
    print(f"  - {b}: subiu {c} vezes")

# ==============================================================================
# 4. PADRÕES DE PARIDADE E FAIXA NA CABEÇA (SÉRIES E REVERSÕES)
# ==============================================================================
print("\n" + "="*70)
print("4. ANÁLISE DE PARIDADE E FAIXA: PROBABILIDADE DE REVERSÃO APÓS SEQUÊNCIAS")
print("="*70)

paridades = list(df_cabeca["paridade_dezena"])
seq_par = 0
reversao_apos_par = Counter()
for i in range(len(paridades) - 1):
    curr = paridades[i]
    nxt = paridades[i+1]
    if curr == "PAR":
        seq_par += 1
        reversao_apos_par[seq_par] += 1
    else:
        seq_par = 0

print("Probabilidade de saída de ÍMPAR após sequência de PARES na cabeça:")
# Vamos calcular formalmente
for n in [1, 2, 3, 4, 5]:
    # quantas vezes tivemos n pares seguidos e o próximo foi Ímpar vs Par
    n_vezes = 0
    virou_impar = 0
    for i in range(len(paridades) - n):
        if all(paridades[i+k] == "PAR" for k in range(n)):
            n_vezes += 1
            if paridades[i+n] == "ÍMPAR":
                virou_impar += 1
    if n_vezes > 0:
        p = (virou_impar / n_vezes) * 100
        print(f"Após {n} PAR(es) consecutivo(s): {virou_impar}/{n_vezes} vezes virou ÍMPAR ({p:.1f}%)")

# Mesmo para ÍMPAR
print("\nProbabilidade de saída de PAR após sequência de ÍMPARES na cabeça:")
for n in [1, 2, 3, 4, 5]:
    n_vezes = 0
    virou_par = 0
    for i in range(len(paridades) - n):
        if all(paridades[i+k] == "ÍMPAR" for k in range(n)):
            n_vezes += 1
            if paridades[i+n] == "PAR":
                virou_par += 1
    if n_vezes > 0:
        p = (virou_par / n_vezes) * 100
        print(f"Após {n} ÍMPAR(es) consecutivo(s): {virou_par}/{n_vezes} vezes virou PAR ({p:.1f}%)")

# ==============================================================================
# 5. DIAS DA SEMANA E AS "CABINEIRAS" (BICHOS FAVORITOS POR DIA DA SEMANA)
# ==============================================================================
print("\n" + "="*70)
print("5. BICHOS COM MAIOR CONCENTRAÇÃO POR DIA DA SEMANA (NA CABEÇA)")
print("="*70)

dias = df_cabeca["dia_semana"].unique()
for dia in dias:
    df_dia = df_cabeca[df_cabeca["dia_semana"] == dia]
    tot_dia = len(df_dia)
    top_b = df_dia["bicho"].value_counts().head(3)
    print(f"\n[{dia}] (Total {tot_dia} extrações):")
    for b, c in top_b.items():
        pct = (c / tot_dia) * 100
        print(f"  * {b:<10}: {c} vezes ({pct:.1f}%) | Força: {pct/4.0:.2f}x")

# ==============================================================================
# 6. PADRÕES DE DÍGITOS DA MILHAR (SOMA DA MILHAR E FAIXAS)
# ==============================================================================
print("\n" + "="*70)
print("6. SOMA DOS DÍGITOS DA MILHAR NA CABEÇA")
print("="*70)

somas = df_cabeca["soma_milhar"]
print(f"Média da soma dos 4 dígitos da milhar: {somas.mean():.2f}")
print(f"Mediana: {somas.median():.0f}")
print(f"Desvio Padrão: {somas.std():.2f}")
# Faixas de soma
faixa_baixa = (somas <= 14).sum()
faixa_media = ((somas >= 15) & (somas <= 22)).sum()
faixa_alta = (somas >= 23).sum()
print(f"Soma Baixa (0 a 14): {faixa_baixa}/{len(somas)} ({faixa_baixa/len(somas)*100:.1f}%)")
print(f"Soma Média (15 a 22): {faixa_media}/{len(somas)} ({faixa_media/len(somas)*100:.1f}%)")
print(f"Soma Alta (23 a 36): {faixa_alta}/{len(somas)} ({faixa_alta/len(somas)*100:.1f}%)")

# ==============================================================================
# 7. CONFLUÊNCIA DE QUARTA E SÁBADO (DIAS DE LOTERIA FEDERAL)
# ==============================================================================
print("\n" + "="*70)
print("7. PADRÃO ESPECÍFICO DOS DIAS DE FEDERAL (QUARTA E SÁBADO)")
print("="*70)

fed_days = df[df["dia_semana"].isin(["Quarta-feira", "Sábado"])]
# Relação entre PTV (16:00) e a FEDERAL (19:00) nos mesmos dias
ptv_fed_pairs = []
for (data, dia), group in fed_days.groupby(["data", "dia_semana"]):
    ptv = group[(group["extracao"] == "PTV") & (group["premio_num"] == 1)]
    fed = group[(group["extracao"] == "FEDERAL") & (group["premio_num"] == 1)]
    if not ptv.empty and not fed.empty:
        ptv_bicho = ptv.iloc[0]["bicho"]
        fed_bicho = fed.iloc[0]["bicho"]
        ptv_grupo = int(ptv.iloc[0]["grupo"])
        fed_grupo = int(fed.iloc[0]["grupo"])
        ptv_fed_pairs.append({
            "data": data,
            "ptv_bicho": ptv_bicho,
            "fed_bicho": fed_bicho,
            "ptv_grupo": ptv_grupo,
            "fed_grupo": fed_grupo,
            "diff_grupo": abs(ptv_grupo - fed_grupo)
        })

df_pairs = pd.DataFrame(ptv_fed_pairs)
print(f"Total de dias de Federal avaliados (Quarta/Sábado): {len(df_pairs)}")
top_fed_bichos = df_pairs["fed_bicho"].value_counts().head(5)
print("Top Bichos mais sorteados na FEDERAL:")
for b, c in top_fed_bichos.items():
    print(f"  - {b}: {c} vezes ({c/len(df_pairs)*100:.1f}%)")
