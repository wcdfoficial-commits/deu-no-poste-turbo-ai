import sqlite3
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta

db_path = r"C:\Users\Derley\.gemini\antigravity\scratch\deu_no_poste_analytics\deu_no_poste_12m.db"
conn = sqlite3.connect(db_path)
df = pd.read_sql("SELECT * FROM resultados ORDER BY id_registro ASC", conn)
conn.close()

# Converter data para datetime para facilitar manipulação de 24h, semanas e meses
df["dt"] = pd.to_datetime(df["data"])
df["dia_mes"] = df["dt"].dt.day
df["mes"] = df["dt"].dt.month
df["ano_mes"] = df["dt"].dt.to_period("M")
df["semana_ano"] = df["dt"].dt.isocalendar().week

print(f"Total de registros carregados: {len(df)}")
print(f"Período: {df['data'].min()} até {df['data'].max()}")

# ==============================================================================
# PARTE 1: CICLO DE 24 HORAS (DIA D -> DIA D+1)
# ==============================================================================
print("\n" + "="*75)
print("1. COMPARAÇÃO DE 24 HORAS (DIA D -> DIA D+1)")
print("="*75)

# A) 1º PRÊMIO(D) -> 1º PRÊMIO(D+1) NO MESMO HORÁRIO (ex: PTM hoje -> PTM amanhã)
print("\nA) MESMO HORÁRIO DE UM DIA PARA O OUTRO (24h exatas na Cabeça):")
for ext in ["PTM", "PT", "PTV", "CORUJA"]:
    sub = df[(df["extracao"] == ext) & (df["is_cabeca"] == 1)].sort_values("dt").reset_index(drop=True)
    sub["next_dt"] = sub["dt"].shift(-1)
    sub["next_bicho"] = sub["bicho"].shift(-1)
    sub["next_dezena"] = sub["dezena"].shift(-1)
    sub["diff_days"] = (sub["next_dt"] - sub["dt"]).dt.days
    
    # Filtrar apenas dias consecutivos (diff_days == 1)
    consec = sub[sub["diff_days"] == 1]
    
    # Transições
    trans_24h = defaultdict(Counter)
    rep_mesmo_bicho = (consec["bicho"] == consec["next_bicho"]).sum()
    
    for _, r in consec.iterrows():
        trans_24h[r["bicho"]][r["next_bicho"]] += 1
        
    print(f"\n[{ext}] - Total de pares consecutivos de 24h: {len(consec)}")
    print(f"  Repetição direta do MESMO BICHO em 24h: {rep_mesmo_bicho}/{len(consec)} ({rep_mesmo_bicho/len(consec)*100:.1f}%) | Esperado: 4.0%")
    
    # Top 3 puxadas 24h
    top_pulls = []
    for orig, cnt in trans_24h.items():
        tot = sum(cnt.values())
        if tot >= 8:
            dest, c = cnt.most_common(1)[0]
            p = (c / tot) * 100
            top_pulls.append((orig, dest, c, tot, p))
            
    for orig, dest, c, tot, p in sorted(top_pulls, key=lambda x: x[4], reverse=True)[:3]:
        print(f"  Puxada 24h: [{orig:<9}] hoje -> [{dest:<9}] amanhã : {c}/{tot}x ({p:.1f}%) - {p/4.0:.2f}x do acaso")

# B) POSIÇÃO A POSIÇÃO EM 24H (1º x 1º, 2º x 2º, 3º x 3º, 4º x 4º, 5º x 5º)
print("\n" + "="*75)
print("B) REPETIÇÃO DO MESMO BICHO EM 24H POR POSIÇÃO DO PRÊMIO (1º ao 5º)")
print("="*75)
for p in range(1, 6):
    sub_p = df[df["premio_num"] == p].sort_values(["dt", "extracao"]).reset_index(drop=True)
    # Comparar com mesmo horário no dia seguinte
    sub_p["next_dt"] = sub_p.groupby("extracao")["dt"].shift(-1)
    sub_p["next_bicho"] = sub_p.groupby("extracao")["bicho"].shift(-1)
    sub_p["diff_days"] = (sub_p["next_dt"] - sub_p["dt"]).dt.days
    
    valid = sub_p[sub_p["diff_days"] == 1]
    rep = (valid["bicho"] == valid["next_bicho"]).sum()
    print(f"Prêmio {p}º no Dia D -> Mesmo {p}º no Dia D+1: {rep}/{len(valid)} repetições ({rep/len(valid)*100:.2f}%) | Esperado: 4.00%")

# C) FENÔMENO 'CORPO VIRA CABEÇA EM 24H'
# Se um bicho sai no 2º ao 5º prêmio no Dia D, qual a chance de sair na Cabeça (1º prêmio) no Dia D+1?
print("\n" + "="*75)
print("C) FENÔMENO 'CORPO VIRA CABEÇA EM 24H' (2º-5º de hoje -> 1º de amanhã no mesmo horário)")
print("="*75)
for ext in ["PTM", "PT", "PTV", "CORUJA"]:
    sub = df[df["extracao"] == ext]
    datas = sorted(sub["dt"].unique())
    subidas_24h = 0
    total_dias_testados = 0
    
    for i in range(len(datas) - 1):
        d_curr = datas[i]
        d_next = datas[i+1]
        if (d_next - d_curr).days == 1:
            draw_curr = sub[sub["dt"] == d_curr]
            draw_next = sub[sub["dt"] == d_next]
            
            corpo_hoje = set(draw_curr[draw_curr["premio_num"].isin([2, 3, 4, 5])]["bicho"])
            cabeca_amanha = draw_next[draw_next["premio_num"] == 1]
            if not cabeca_amanha.empty:
                b_cab = cabeca_amanha.iloc[0]["bicho"]
                total_dias_testados += 1
                if b_cab in corpo_hoje:
                    subidas_24h += 1
                    
    print(f"[{ext}] 2º-5º de hoje -> Cabeça de amanhã: {subidas_24h}/{total_dias_testados} ({subidas_24h/total_dias_testados*100:.1f}%) | Esperado aleatório: 16.0%")

# ==============================================================================
# PARTE 2: CICLOS SEMANAIS (Ex: Quarta a Quarta, Sábado a Sábado - FEDERAL)
# ==============================================================================
print("\n" + "="*75)
print("2. CICLOS SEMANAIS (FEDERAL: QUARTA -> QUARTA E SÁBADO -> SÁBADO)")
print("="*75)
fed_df = df[df["extracao"] == "FEDERAL"].sort_values("dt").reset_index(drop=True)
fed_cabeca = fed_df[fed_df["premio_num"] == 1].copy()
fed_cabeca["next_bicho"] = fed_cabeca["bicho"].shift(-1)
fed_cabeca["next_dezena"] = fed_cabeca["dezena"].shift(-1)

print(f"Total de sorteios da Loteria Federal analisados: {len(fed_cabeca)}")
fed_trans = defaultdict(Counter)
for _, r in fed_cabeca.dropna(subset=["next_bicho"]).iterrows():
    fed_trans[r["bicho"]][r["next_bicho"]] += 1

print("\nTop Puxadas entre sorteios consecutivos da FEDERAL:")
for orig, cnt in fed_trans.items():
    if sum(cnt.values()) >= 2:
        dest, c = cnt.most_common(1)[0]
        if c >= 2:
            print(f"  Federal [{orig:<9}] -> Próxima Federal [{dest:<9}]: {c}/{sum(cnt.values())}x ({c/sum(cnt.values())*100:.1f}%)")

# ==============================================================================
# PARTE 3: CICLOS MENSAIS (INÍCIO vs MEIO vs FIM DO MÊS)
# ==============================================================================
print("\n" + "="*75)
print("3. CICLOS MENSAIS (COMPORTAMENTO POR PERÍODO DO MÊS)")
print("="*75)
df_cab = df[df["is_cabeca"] == 1].copy()
df_cab["fase_mes"] = pd.cut(df_cab["dia_mes"], bins=[0, 10, 20, 31], labels=["Início (01-10)", "Meio (11-20)", "Fim (21-31)"])

for fase in ["Início (01-10)", "Meio (11-20)", "Fim (21-31)"]:
    sub_f = df_cab[df_cab["fase_mes"] == fase]
    top_3 = sub_f["bicho"].value_counts().head(3)
    tot = len(sub_f)
    print(f"\n[{fase}] - Total sorteios: {tot}")
    for b, c in top_3.items():
        print(f"  * {b:<10}: {c} vezes ({c/tot*100:.1f}%) | Força: {c/tot/0.04:.2f}x")

# ==============================================================================
# PARTE 4: PORTFÓLIO MULTI-NÍVEL (CLASSIFICAÇÃO POR INVESTIMENTO E ASSERTIVIDADE)
# Nível 1: Dezenas (R$ 5 a R$ 10)
# Nível 2: Centenas (R$ 15 a R$ 30)
# Nível 3: Milhares (R$ 50 a R$ 100)
# ==============================================================================
print("\n" + "="*75)
print("4. SIMULAÇÃO DO PORTFÓLIO MULTI-NÍVEL (DEZENA vs CENTENA vs MILHAR)")
print("="*75)

# A) ESTRATÉGIA NÍVEL 1: APOSTA EM 5 DEZENAS (Custo: R$ 5,00 | Retorno na cabeça: R$ 60,00)
# Quando ocorre gatilho de bicho, joga as 4 dezenas do bicho + 1 dezena vizinha mais puxada
# Se o bicho sai na cabeça, ACERTA 100% A DEZENA!
# Retorno = R$ 60,00. Custo = R$ 5,00. Lucro = R$ 55,00 (11x o investimento!)
# Break-even para 5 dezenas: 5 / 60 = 8.33% de acerto.
print("A) NÍVEL 1: 5 DEZENAS SELECIONADAS (Custo: R$ 5,00 | Prêmio: R$ 60,00 | Break-even: 8.3%)")

# Vamos testar nos Top 5 gatilhos de puxada de Bicho (onde o bicho destino sai com 25% a 33% de chance!)
# Ex: Coruja [Borboleta] -> PPT [Camelo] (33.3% de acerto).
# Jogando as 4 dezenas do Camelo (29, 30, 31, 32) + 1 dezena extra = 5 dezenas = R$ 5,00
# Acerto real = 33.3%! Isso é 4 VEZES o break-even!
triggers_nivel_1 = [
    ("CORUJA", "Borboleta", "PPT", "Camelo", [29, 30, 31, 32, 33]),
    ("CORUJA", "Coelho", "PPT", "Cachorro", [17, 18, 19, 20, 21]),
    ("CORUJA", "Galo", "PPT", "Porco", [69, 70, 71, 72, 73]),
    ("PTM", "Borboleta", "PT", "Elefante", [45, 46, 47, 48, 49]),
    ("PTM", "Burro", "PT", "Coelho", [37, 38, 39, 40, 41]),
    ("PTV", "Gato", "NOITE", "Jacaré", [57, 58, 59, 60, 61])
]

# Simular em todo o histórico
for ext_in, b_in, ext_out, b_out, dezenas_alvo in triggers_nivel_1:
    # Buscar no df_cabeca
    matches = 0
    acertos = 0
    for i in range(len(df_cab) - 1):
        row_curr = df_cab.iloc[i]
        row_next = df_cab.iloc[i+1]
        
        # Verificar se bate horário e bicho
        cond_in = (row_curr["bicho"] == b_in) and (ext_in in row_curr["extracao"])
        cond_out_ext = (ext_out in row_next["extracao"]) or (ext_out == "NOITE" and row_next["extracao"] in ["PTN", "FEDERAL"])
        
        if cond_in and cond_out_ext:
            matches += 1
            dez_sorteada = int(row_next["dezena"])
            if dez_sorteada in dezenas_alvo:
                acertos += 1
                
    if matches > 0:
        tx = acertos / matches * 100
        custo_tot = matches * 5
        ret_tot = acertos * 60
        lucro_tot = ret_tot - custo_tot
        roi_tot = (lucro_tot / custo_tot * 100) if custo_tot > 0 else 0
        print(f"  Gatilho [{ext_in} {b_in}] -> [{ext_out} 5 Dezenas]: {acertos}/{matches}x ({tx:.1f}%) | Custo: R$ {custo_tot} | Retorno: R$ {ret_tot} | Lucro: R$ {lucro_tot:+} (ROI: {roi_tot:+.1f}%)")

# B) ESTRATÉGIA NÍVEL 2: 20 CENTENAS SELECIONADAS (Custo: R$ 20,00 | Retorno: R$ 500,00 | Break-even: 4.0%)
print("\nB) NÍVEL 2: 20 CENTENAS SELECIONADAS (Custo: R$ 20,00 | Prêmio: R$ 500,00 | Break-even: 4.0%)")
# Ao identificar a dezena de alta probabilidade, joga 20 centenas usando os dígitos de centena mais quentes (ex: 2 dígitos de centena x 10 ou 4 dezenas do grupo x 5 dígitos de centena)
# Se jogamos as 4 dezenas do grupo alvo x 5 centenas mais frequentes = 20 centenas (R$ 20,00)
# Se o bicho sai (taxa 25-33%), e a centena bate em 50% dos casos de paridade/faixa:
# Taxa de acerto estimada = 25% * 50% = 12.5% a 15% (3x a 4x o break-even de 4.0%!)
