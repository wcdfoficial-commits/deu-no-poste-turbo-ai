import sqlite3
import pandas as pd
from collections import defaultdict, Counter

db_path = r"C:\Users\Derley\.gemini\antigravity\scratch\deu_no_poste_analytics\deu_no_poste_12m.db"
conn = sqlite3.connect(db_path)
df = pd.read_sql("SELECT * FROM resultados WHERE is_cabeca = 1 ORDER BY id_sorteio ASC", conn)
conn.close()

df["dt"] = pd.to_datetime(df["data"])

GEMEAS = ["00", "11", "22", "33", "44", "55", "66", "77", "88", "99"]
BAIXAS = ["01", "02", "03", "04", "05", "06", "07", "08", "09"]
REDONDAS = ["10", "20", "30", "40", "50", "60", "70", "80", "90"]

CENTENAS_00X = [f"00{i}" for i in range(1, 10)]
CENTENAS_0X0 = [f"0{i}0" for i in range(1, 10)]

# 1. ANÁLISE 24H: MESMO HORÁRIO NO DIA SEGUINTE
# Ex: Se saiu PTM com dezena X hoje, o que sai no PTM amanhã?
# Ex: Se saiu PT com dezena X hoje, o que sai na PT amanhã?

df["next_dt_ext"] = df.groupby("extracao")["dt"].shift(-1)
df["next_dez_ext"] = df.groupby("extracao")["dezena"].shift(-1)
df["next_cent_ext"] = df.groupby("extracao")["centena"].shift(-1)
df["next_mil_ext"] = df.groupby("extracao")["milhar"].shift(-1)
df["next_bicho_ext"] = df.groupby("extracao")["bicho"].shift(-1)
df["diff_days_ext"] = (df["next_dt_ext"] - df["dt"]).dt.days

# Apenas dias estritamente consecutivos no mesmo horário (diff_days == 1)
df_24h_ext = df[df["diff_days_ext"] == 1].copy()

print("="*75)
print("1. PUXADAS ESPECÍFICAS DE 24 HORAS (MESMO HORÁRIO DE HOJE PARA AMANHÃ)")
print("="*75)

# A) Puxadas das Gêmeas em 24h
print("\n--- GÊMEAS EM 24H (MESMO HORÁRIO) ---")
gemeas_24h = df_24h_ext[df_24h_ext["dezena"].isin(GEMEAS)]
print(f"Total de ocorrências de Gêmeas em dias consecutivos: {len(gemeas_24h)}")

trans_g_24h = defaultdict(Counter)
bicho_trans_g = defaultdict(Counter)
for _, r in gemeas_24h.iterrows():
    trans_g_24h[r["dezena"]][r["next_dez_ext"]] += 1
    bicho_trans_g[r["dezena"]][r["next_bicho_ext"]] += 1

top_g_24h = []
for d_orig, cnt in trans_g_24h.items():
    tot = sum(cnt.values())
    if tot >= 10:
        for d_dest, c in cnt.items():
            if c >= 2:
                prob = (c / tot) * 100
                top_g_24h.append((d_orig, d_dest, c, tot, prob, prob/1.0))

print("Top Dezenas Gêmeas que puxam Dezenas Específicas em 24h (mesmo horário):")
for orig, dest, c, tot, prob, lift in sorted(top_g_24h, key=lambda x: x[4], reverse=True)[:8]:
    print(f"  Dezena [{orig}] hoje -> Dezena [{dest}] amanhã : {c}/{tot}x ({prob:.1f}%) | Força: {lift:.1f}x o acaso")

# Bichos puxados pelas gêmeas em 24h
print("\nTop Bichos puxados pelas Gêmeas em 24h (mesmo horário):")
for d_orig, cnt in bicho_trans_g.items():
    tot = sum(cnt.values())
    if tot >= 12:
        b_top, c_top = cnt.most_common(1)[0]
        p_top = (c_top / tot) * 100
        if p_top >= 15.0: # Quase 4x do acaso
            print(f"  Dezena Gêmea [{d_orig}] hoje -> Bicho [{b_top:<9}] amanhã : {c_top}/{tot}x ({p_top:.1f}%) | Força: {p_top/4.0:.2f}x")

# B) Puxadas de 01-09 e 10-90 em 24h
print("\n--- DEZENAS 01-09 E 10-90 EM 24H (MESMO HORÁRIO) ---")
b_24h = df_24h_ext[df_24h_ext["dezena"].isin(BAIXAS)]
trans_baixas = defaultdict(Counter)
bicho_trans_b = defaultdict(Counter)
for _, r in b_24h.iterrows():
    trans_baixas[r["dezena"]][r["next_dez_ext"]] += 1
    bicho_trans_b[r["dezena"]][r["next_bicho_ext"]] += 1

print("Top Puxadas de 01-09 em 24h:")
for d_orig, cnt in bicho_trans_b.items():
    tot = sum(cnt.values())
    if tot >= 10:
        b_top, c_top = cnt.most_common(1)[0]
        p = (c_top / tot) * 100
        if p >= 18.0:
            print(f"  Dezena [{d_orig}] hoje -> Bicho [{b_top:<9}] amanhã : {c_top}/{tot}x ({p:.1f}%) | Força: {p/4.0:.2f}x")

r_24h = df_24h_ext[df_24h_ext["dezena"].isin(REDONDAS)]
bicho_trans_r = defaultdict(Counter)
for _, r in r_24h.iterrows():
    bicho_trans_r[r["dezena"]][r["next_bicho_ext"]] += 1

print("\nTop Puxadas de 10-90 em 24h:")
for d_orig, cnt in bicho_trans_r.items():
    tot = sum(cnt.values())
    if tot >= 10:
        b_top, c_top = cnt.most_common(1)[0]
        p = (c_top / tot) * 100
        if p >= 18.0:
            print(f"  Dezena [{d_orig}] hoje -> Bicho [{b_top:<9}] amanhã : {c_top}/{tot}x ({p:.1f}%) | Força: {p/4.0:.2f}x")

# ==============================================================================
# 2. O QUE ACONTECE APÓS SAÍDA DAS CENTENAS 001-009 E 010-090?
# ==============================================================================
print("\n" + "="*75)
print("2. O QUE ACONTECE APÓS SAÍDA DAS CENTENAS 001-009 E 010-090?")
print("===========================================================================")

# No sorteio seguinte imediato (T -> T+1)
idx_00x = df[df["centena"].isin(CENTENAS_00X)].index
next_00x = []
for idx in idx_00x:
    if idx + 1 < len(df):
        next_00x.append(df.iloc[idx + 1])

df_next_00x = pd.DataFrame(next_00x)
print(f"Total de saídas da centena 001-009: {len(df_next_00x)}")
print("Bichos que mais saíram NO SORTEIO SEGUINTE à centena 001-009:")
for b, c in df_next_00x["bicho"].value_counts().head(5).items():
    p = c / len(df_next_00x) * 100
    print(f"  * {b:<10}: {c}/{len(df_next_00x)}x ({p:.1f}%) | Força: {p/4.0:.2f}x")

print("\nDezenas mais frequentes após 001-009:")
for d, c in df_next_00x["dezena"].value_counts().head(5).items():
    p = c / len(df_next_00x) * 100
    print(f"  * Dezena {d}: {c}/{len(df_next_00x)}x ({p:.1f}%)")

idx_0x0 = df[df["centena"].isin(CENTENAS_0X0)].index
next_0x0 = []
for idx in idx_0x0:
    if idx + 1 < len(df):
        next_0x0.append(df.iloc[idx + 1])
df_next_0x0 = pd.DataFrame(next_0x0)
print(f"\nTotal de saídas da centena 010-090: {len(df_next_0x0)}")
print("Bichos que mais saíram NO SORTEIO SEGUINTE à centena 010-090:")
for b, c in df_next_0x0["bicho"].value_counts().head(5).items():
    p = c / len(df_next_0x0) * 100
    print(f"  * {b:<10}: {c}/{len(df_next_0x0)}x ({p:.1f}%) | Força: {p/4.0:.2f}x")

# ==============================================================================
# 3. TESTE DE FECHAMENTO: É VANTAJOSO TRABALHAR COM FECHAMENTO DESTAS FAMÍLIAS?
# ==============================================================================
print("\n" + "="*75)
print("3. ANÁLISE DE FECHAMENTOS: VALE A PENA FECHAR ESTAS FAMÍLIAS?")
print("===========================================================================")

# Cenário A: Fechamento das 10 Dezenas Gêmeas (00, 11, 22, ..., 99)
# Custo: 10 dezenas x R$ 1,00 = R$ 10,00 por sorteio.
# Prêmio se bater na cabeça = R$ 60,00.
# Break-even necessário = 10 / 60 = 16.67% de acerto.
# Frequência histórica real das gêmeas na cabeça: 11.58%.
# Jogar Gêmeas SEMPRE = 11.58% < 16.67% -> PREJUÍZO de -30.5%!
# MAS, se jogarmos Gêmeas APENAS quando há um GATILHO de atração de Gêmeas:
print("A) Fechamento das 10 Dezenas Gêmeas (Custo: R$ 10,00 | Prêmio: R$ 60,00 | Break-even: 16.7%)")
print("  - Jogar cegamente todo dia: 11.58% de acerto -> PREJUÍZO (Abaixo do break-even de 16.7%).")

# Identificar gatilhos onde a taxa de saída de Gêmeas supera 20% a 30%!
# Teste: Quais bichos quando saem, o próximo sorteio tem Gêmea?
puxam_gemeas = []
for b_name in df["bicho"].unique():
    sub_b = df[df["bicho"] == b_name]
    indices = sub_b.index
    total_g = 0
    total_occ = 0
    for idx in indices:
        if idx + 1 < len(df):
            total_occ += 1
            if df.iloc[idx + 1]["dezena"] in GEMEAS:
                total_g += 1
    if total_occ >= 50:
        p = total_g / total_occ * 100
        puxam_gemeas.append((b_name, total_g, total_occ, p))

print("\n  Top Bichos que DISPARAM GÊMEAS no próximo sorteio (Gatilhos EV+):")
for b, g_cnt, tot, p in sorted(puxam_gemeas, key=lambda x: x[3], reverse=True)[:5]:
    lucro = (g_cnt * 60) - (tot * 10)
    roi = (lucro / (tot * 10)) * 100
    print(f"    Gatilho [{b:<10}]: Gêmeas no próximo: {g_cnt}/{tot}x ({p:.1f}%) | ROI: {roi:+.1f}% ({'LUCRO' if roi > 0 else 'PREJUÍZO'})")

# Cenário B: Fechamento das 9 Dezenas 01-09
# Custo: R$ 9,00 | Prêmio: R$ 60,00 | Break-even: 9 / 60 = 15.0%
print("\nB) Fechamento das 9 Dezenas 01 a 09 (Custo: R$ 9,00 | Prêmio: R$ 60,00 | Break-even: 15.0%)")
puxam_baixas = []
for b_name in df["bicho"].unique():
    sub_b = df[df["bicho"] == b_name]
    indices = sub_b.index
    total_b = 0
    total_occ = 0
    for idx in indices:
        if idx + 1 < len(df):
            total_occ += 1
            if df.iloc[idx + 1]["dezena"] in BAIXAS:
                total_b += 1
    if total_occ >= 50:
        p = total_b / total_occ * 100
        puxam_baixas.append((b_name, total_b, total_occ, p))

for b, b_cnt, tot, p in sorted(puxam_baixas, key=lambda x: x[3], reverse=True)[:5]:
    lucro = (b_cnt * 60) - (tot * 9)
    roi = (lucro / (tot * 9)) * 100
    print(f"    Gatilho [{b:<10}]: 01-09 no próximo: {b_cnt}/{tot}x ({p:.1f}%) | ROI: {roi:+.1f}%")
