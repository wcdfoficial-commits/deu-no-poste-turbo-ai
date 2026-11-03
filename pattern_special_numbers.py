import sqlite3
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from datetime import datetime, timedelta

db_path = r"C:\Users\Derley\.gemini\antigravity\scratch\deu_no_poste_analytics\deu_no_poste_12m.db"
conn = sqlite3.connect(db_path)
df = pd.read_sql("SELECT * FROM resultados ORDER BY id_registro ASC", conn)
conn.close()

df["dt"] = pd.to_datetime(df["data"])
df_cabeca = df[df["is_cabeca"] == 1].sort_values("id_sorteio").reset_index(drop=True)

# Definição dos grupos de estudo
GEMEAS = ["00", "11", "22", "33", "44", "55", "66", "77", "88", "99"]
BAIXAS_ZERO = ["01", "02", "03", "04", "05", "06", "07", "08", "09"]
REDONDAS_ZERO = ["10", "20", "30", "40", "50", "60", "70", "80", "90"]

CENTENAS_00X = [f"00{i}" for i in range(1, 10)] # 001 a 009
CENTENAS_0X0 = [f"0{i}0" for i in range(1, 10)] # 010, 020, ..., 090

print("="*75)
print("ESTUDO ESTATÍSTICO: FAMÍLIAS ESPECIAIS DE DEZENAS E CENTENAS (12 MESES)")
print(f"Total de registros na cabeça: {len(df_cabeca)} sorteios | Total de dias: {df_cabeca['data'].nunique()}")
print("="*75)

# ==============================================================================
# 1. FREQUÊNCIA BASE DAS FAMÍLIAS NA CABEÇA (1º PRÊMIO)
# ==============================================================================
total_sorteios = len(df_cabeca)
cnt_gemeas = df_cabeca["dezena"].isin(GEMEAS).sum()
cnt_baixas = df_cabeca["dezena"].isin(BAIXAS_ZERO).sum()
cnt_redondas = df_cabeca["dezena"].isin(REDONDAS_ZERO).sum()
cnt_c_00x = df_cabeca["centena"].isin(CENTENAS_00X).sum()
cnt_c_0x0 = df_cabeca["centena"].isin(CENTENAS_0X0).sum()

print("\n1. FREQUÊNCIA HISTÓRICA BASE (NA CABEÇA):")
print(f"  - Dezenas Gêmeas (10 dezenas): {cnt_gemeas}/{total_sorteios} ({cnt_gemeas/total_sorteios*100:.2f}%) | Esperado: 10.0%")
print(f"  - Dezenas 01-09 (9 dezenas): {cnt_baixas}/{total_sorteios} ({cnt_baixas/total_sorteios*100:.2f}%) | Esperado: 9.0%")
print(f"  - Dezenas 10-90 (9 dezenas): {cnt_redondas}/{total_sorteios} ({cnt_redondas/total_sorteios*100:.2f}%) | Esperado: 9.0%")
print(f"  - Centenas 001-009 (9 centenas): {cnt_c_00x}/{total_sorteios} ({cnt_c_00x/total_sorteios*100:.2f}%) | Esperado: 0.9%")
print(f"  - Centenas 010-090 (9 centenas): {cnt_c_0x0}/{total_sorteios} ({cnt_c_0x0/total_sorteios*100:.2f}%) | Esperado: 0.9%")

# ==============================================================================
# 2. ANÁLISE DE 24 HORAS (DIA D -> DIA D+1)
# Agrupando pelo que saiu no Dia D (na cabeça) vs o que sai no Dia D+1 (na cabeça)
# ==============================================================================
datas_ordenadas = sorted(df_cabeca["dt"].unique())

dia_d_to_d1 = []
for i in range(len(datas_ordenadas) - 1):
    d_curr = datas_ordenadas[i]
    d_next = datas_ordenadas[i+1]
    diff = (d_next - d_curr).days
    if diff == 1: # Dias estritamente consecutivos
        draws_d = df_cabeca[df_cabeca["dt"] == d_curr]
        draws_d1 = df_cabeca[df_cabeca["dt"] == d_next]
        
        dia_d_to_d1.append({
            "d_curr": d_curr,
            "d_next": d_next,
            "dezenas_d": list(draws_d["dezena"]),
            "bichos_d": list(draws_d["bicho"]),
            "centenas_d": list(draws_d["centena"]),
            "milhares_d": list(draws_d["milhar"]),
            "dezenas_d1": list(draws_d1["dezena"]),
            "bichos_d1": list(draws_d1["bicho"]),
            "centenas_d1": list(draws_d1["centena"]),
            "milhares_d1": list(draws_d1["milhar"]),
            # PTM de hoje vs PTM de amanha
            "ptm_d": draws_d[draws_d["extracao"] == "PTM"],
            "ptm_d1": draws_d1[draws_d1["extracao"] == "PTM"],
            # PT de hoje vs PT de amanha
            "pt_d": draws_d[draws_d["extracao"] == "PT"],
            "pt_d1": draws_d1[draws_d1["extracao"] == "PT"],
            # Coruja de hoje vs Coruja de amanha
            "coruja_d": draws_d[draws_d["extracao"] == "CORUJA"],
            "coruja_d1": draws_d1[draws_d1["extracao"] == "CORUJA"]
        })

print(f"\nTotal de pares de dias consecutivos (24h) avaliados: {len(dia_d_to_d1)}")

# ------------------------------------------------------------------------------
# A) COMPORTAMENTO DAS DEZENAS GÊMEAS EM 24H
# ------------------------------------------------------------------------------
print("\n" + "="*70)
print("A) DEZENAS GÊMEAS (00, 11, 22, 33, 44, 55, 66, 77, 88, 99) EM 24H")
print("="*70)

dias_com_gemea = 0
dias_gemea_puxou_gemea_24h = 0
dias_gemea_repetiu_mesma_24h = 0
bichos_puxados_por_gemeas_24h = Counter()
dezenas_puxadas_por_gemeas_24h = Counter()

for par in dia_d_to_d1:
    gemeas_no_dia_d = [d for d in par["dezenas_d"] if d in GEMEAS]
    if gemeas_no_dia_d:
        dias_com_gemea += 1
        # No dia seguinte saiu gêmea na cabeça?
        gemeas_d1 = [d for d in par["dezenas_d1"] if d in GEMEAS]
        if gemeas_d1:
            dias_gemea_puxou_gemea_24h += 1
            # Repetiu a MESMA gêmea?
            if any(g in par["dezenas_d1"] for g in gemeas_no_dia_d):
                dias_gemea_repetiu_mesma_24h += 1
                
        # Bichos e dezenas que saíram no Dia D+1
        for b in par["bichos_d1"]:
            bichos_puxados_por_gemeas_24h[b] += 1
        for d in par["dezenas_d1"]:
            dezenas_puxadas_por_gemeas_24h[d] += 1

print(f"Total de dias em que saiu GÊMEA na cabeça no Dia D: {dias_com_gemea}/{len(dia_d_to_d1)} ({dias_com_gemea/len(dia_d_to_d1)*100:.1f}%)")
print(f"Dias em que SAIU GÊMEA no Dia D+1: {dias_gemea_puxou_gemea_24h}/{dias_com_gemea} ({dias_gemea_puxou_gemea_24h/dias_com_gemea*100:.1f}%)")
print(f"Dias em que REPETIU A MESMA GÊMEA em 24h: {dias_gemea_repetiu_mesma_24h}/{dias_com_gemea} ({dias_gemea_repetiu_mesma_24h/dias_com_gemea*100:.1f}%)")

print("\nTop 5 Bichos mais atraídos no Dia D+1 após saída de Gêmea:")
for b, c in bichos_puxados_por_gemeas_24h.most_common(5):
    print(f"  * {b:<10}: {c} vezes no dia seguinte ({c/(dias_com_gemea*5.5)*100:.1f}%)")

# ------------------------------------------------------------------------------
# B) COMPORTAMENTO DAS DEZENAS 01 A 09 EM 24H
# ------------------------------------------------------------------------------
print("\n" + "="*70)
print("B) DEZENAS 01 A 09 (BAIXAS COM ZERO INICIAL) EM 24H")
print("="*70)

dias_com_baixas = 0
dias_baixas_puxou_redondas_24h = 0
dias_baixas_puxou_baixas_24h = 0
espelhamento_direto_24h = 0 # Ex: 02 puxou 20, 03 puxou 30...

for par in dia_d_to_d1:
    baixas_d = [d for d in par["dezenas_d"] if d in BAIXAS_ZERO]
    if baixas_d:
        dias_com_baixas += 1
        # No dia seguinte saiu 01-09?
        if any(d in BAIXAS_ZERO for d in par["dezenas_d1"]):
            dias_baixas_puxou_baixas_24h += 1
        # No dia seguinte saiu redonda (10, 20, ..., 90)?
        if any(d in REDONDAS_ZERO for d in par["dezenas_d1"]):
            dias_baixas_puxou_redondas_24h += 1
            
        # Teste do espelho inverso: ex: 02 -> 20, 05 -> 50, etc.
        for b in baixas_d:
            digito = b[1] # '1' a '9'
            espelho = f"{digito}0"
            if espelho in par["dezenas_d1"]:
                espelhamento_direto_24h += 1

print(f"Total de dias com dezenas 01-09 no Dia D: {dias_com_baixas}/{len(dia_d_to_d1)} ({dias_com_baixas/len(dia_d_to_d1)*100:.1f}%)")
print(f"Dia D+1 teve outra dezena 01-09: {dias_baixas_puxou_baixas_24h}/{dias_com_baixas} ({dias_baixas_puxou_baixas_24h/dias_com_baixas*100:.1f}%)")
print(f"Dia D+1 teve dezena redonda (10-90): {dias_baixas_puxou_redondas_24h}/{dias_com_baixas} ({dias_baixas_puxou_redondas_24h/dias_com_baixas*100:.1f}%)")
print(f"Ocorrência de Inversão Direta em 24h (ex: 02 hoje -> 20 amanhã): {espelhamento_direto_24h} vezes!")

# ------------------------------------------------------------------------------
# C) COMPORTAMENTO DAS DEZENAS 10 A 90 (REDONDAS FINAIS ZERO) EM 24H
# ------------------------------------------------------------------------------
print("\n" + "="*70)
print("C) DEZENAS REDONDAS 10 A 90 EM 24H")
print("="*70)

dias_com_redondas = 0
espelho_redonda_para_baixa = 0 # Ex: 20 hoje -> 02 amanhã
bichos_pos_redondas = Counter()

for par in dia_d_to_d1:
    red_d = [d for d in par["dezenas_d"] if d in REDONDAS_ZERO]
    if red_d:
        dias_com_redondas += 1
        for r in red_d:
            dig = r[0]
            espelho_b = f"0{dig}"
            if espelho_b in par["dezenas_d1"]:
                espelho_redonda_para_baixa += 1
        for b in par["bichos_d1"]:
            bichos_pos_redondas[b] += 1

print(f"Total de dias com redondas (10-90) no Dia D: {dias_com_redondas}/{len(dia_d_to_d1)} ({dias_com_redondas/len(dia_d_to_d1)*100:.1f}%)")
print(f"Inversão Direta em 24h (ex: 70 hoje -> 07 amanhã): {espelho_redonda_para_baixa} vezes!")
print("Top 5 Bichos no Dia D+1 após saírem dezenas redondas:")
for b, c in bichos_pos_redondas.most_common(5):
    print(f"  * {b:<10}: {c} vezes")

# ------------------------------------------------------------------------------
# D) AS CENTENAS 001 A 009 E 010 A 090
# ------------------------------------------------------------------------------
print("\n" + "="*70)
print("D) CENTENAS RARAS: 001-009 E 010-090")
print("="*70)

# Localizar todos os sorteios onde saíram centenas 001-009 e 010-090
sub_c00x = df_cabeca[df_cabeca["centena"].isin(CENTENAS_00X)]
sub_c0x0 = df_cabeca[df_cabeca["centena"].isin(CENTENAS_0X0)]

print(f"Centenas 001-009 na cabeça: {len(sub_c00x)} saídas no ano")
for _, r in sub_c00x.iterrows():
    print(f"  Data: {r['data']} | Horário: {r['extracao']} | Milhar: {r['milhar']} | Bicho: {r['bicho']}")

print(f"\nCentenas 010-090 na cabeça: {len(sub_c0x0)} saídas no ano")
for _, r in sub_c0x0.head(10).iterrows():
    print(f"  Data: {r['data']} | Horário: {r['extracao']} | Milhar: {r['milhar']} | Bicho: {r['bicho']}")

# ==============================================================================
# 3. ANÁLISE SEQUENCIAL IMEDIATA (SORTEIO T -> SORTEIO T+1) PARA ESTAS FAMÍLIAS
# ==============================================================================
print("\n" + "="*70)
print("3. ANÁLISE SEQUENCIAL (SORTEIO T -> T+1) PARA AS FAMÍLIAS ESPECIAIS")
print("="*70)

df_cabeca["next_dezena"] = df_cabeca["dezena"].shift(-1)
df_cabeca["next_centena"] = df_cabeca["centena"].shift(-1)
df_cabeca["next_milhar"] = df_cabeca["milhar"].shift(-1)
df_cabeca["next_bicho"] = df_cabeca["bicho"].shift(-1)

# Quando sai GÊMEA no sorteio T:
gemeas_seq = df_cabeca[df_cabeca["dezena"].isin(GEMEAS)].dropna(subset=["next_dezena"])
seq_gemea_puxa_gemea = (gemeas_seq["next_dezena"].isin(GEMEAS)).sum()
print(f"Quando sai GÊMEA no sorteio T -> Próximo sorteio T+1 é GÊMEA: {seq_gemea_puxa_gemea}/{len(gemeas_seq)} ({seq_gemea_puxa_gemea/len(gemeas_seq)*100:.1f}%) | Esperado: 10.0%")

# Top bichos puxados imediatamente após uma GÊMEA
print("\nTop 5 Bichos imediatamente após GÊMEA:")
for b, c in gemeas_seq["next_bicho"].value_counts().head(5).items():
    print(f"  - {b:<10}: {c}/{len(gemeas_seq)}x ({c/len(gemeas_seq)*100:.1f}%) | Força: {(c/len(gemeas_seq))/0.04:.2f}x")

# Quando sai 01-09 no sorteio T:
baixas_seq = df_cabeca[df_cabeca["dezena"].isin(BAIXAS_ZERO)].dropna(subset=["next_dezena"])
print(f"\nQuando sai DEZENA 01-09 no sorteio T:")
print(f"  Próximo T+1 é 01-09: {baixas_seq['next_dezena'].isin(BAIXAS_ZERO).sum()}/{len(baixas_seq)} ({baixas_seq['next_dezena'].isin(BAIXAS_ZERO).mean()*100:.1f}%) | Esperado: 9.0%")
print(f"  Próximo T+1 é REDONDA (10-90): {baixas_seq['next_dezena'].isin(REDONDAS_ZERO).sum()}/{len(baixas_seq)} ({baixas_seq['next_dezena'].isin(REDONDAS_ZERO).mean()*100:.1f}%) | Esperado: 9.0%")

# Top bichos imediatamente após 01-09
print("Top 5 Bichos imediatamente após DEZENAS 01-09:")
for b, c in baixas_seq["next_bicho"].value_counts().head(5).items():
    print(f"  - {b:<10}: {c}/{len(baixas_seq)}x ({c/len(baixas_seq)*100:.1f}%) | Força: {(c/len(baixas_seq))/0.04:.2f}x")

# Quando sai 10-90 no sorteio T:
redondas_seq = df_cabeca[df_cabeca["dezena"].isin(REDONDAS_ZERO)].dropna(subset=["next_dezena"])
print(f"\nQuando sai DEZENA REDONDA (10-90) no sorteio T:")
print(f"  Próximo T+1 é 01-09 (Espelho): {redondas_seq['next_dezena'].isin(BAIXAS_ZERO).sum()}/{len(redondas_seq)} ({redondas_seq['next_dezena'].isin(BAIXAS_ZERO).mean()*100:.1f}%) | Esperado: 9.0%")
print(f"  Próximo T+1 é REDONDA: {redondas_seq['next_dezena'].isin(REDONDAS_ZERO).sum()}/{len(redondas_seq)} ({redondas_seq['next_dezena'].isin(REDONDAS_ZERO).mean()*100:.1f}%) | Esperado: 9.0%")

# Top bichos imediatamente após 10-90
print("Top 5 Bichos imediatamente após DEZENAS 10-90:")
for b, c in redondas_seq["next_bicho"].value_counts().head(5).items():
    print(f"  - {b:<10}: {c}/{len(redondas_seq)}x ({c/len(redondas_seq)*100:.1f}%) | Força: {(c/len(redondas_seq))/0.04:.2f}x")
