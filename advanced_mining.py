import sqlite3
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

db_path = r"C:\Users\Derley\.gemini\antigravity\scratch\deu_no_poste_analytics\deu_no_poste_12m.db"
conn = sqlite3.connect(db_path)
df = pd.read_sql("SELECT * FROM resultados ORDER BY id_registro ASC", conn)
conn.close()

df_cabeca = df[df["is_cabeca"] == 1].sort_values("id_sorteio").reset_index(drop=True)

# 1. REPETIÇÃO DO MESMO BICHO NO MESMO DIA
print("=== 1. REPETIÇÃO DO MESMO BICHO NO MESMO DIA ===")
rep_mesmo_dia_cabeca = 0
dias_com_sorteio = df_cabeca["data"].unique()
total_dias = len(dias_com_sorteio)

bichos_repetidos_dia = []
for d in dias_com_sorteio:
    sub = df_cabeca[df_cabeca["data"] == d]
    bichos = list(sub["bicho"])
    dups = [b for b, count in Counter(bichos).items() if count > 1]
    if dups:
        rep_mesmo_dia_cabeca += 1
        bichos_repetidos_dia.extend(dups)

print(f"Total de dias analisados: {total_dias}")
print(f"Dias em que um bicho se REPETIU na CABEÇA no mesmo dia: {rep_mesmo_dia_cabeca} ({rep_mesmo_dia_cabeca/total_dias*100:.1f}%)")
print(f"Top Bichos que mais dobraram na cabeça no mesmo dia: {Counter(bichos_repetidos_dia).most_common(5)}")

# 2. DEZENAS DOBRADAS (GÊMEAS: 00, 11, 22, 33, 44, 55, 66, 77, 88, 99)
print("\n=== 2. EFEITO DEZENAS GÊMEAS / DOBRADAS ===")
dezenas_gemeas = {"00", "11", "22", "33", "44", "55", "66", "77", "88", "99"}
df_cabeca["is_gemea"] = df_cabeca["dezena"].isin(dezenas_gemeas).astype(int)
df_cabeca["next_is_gemea"] = df_cabeca["is_gemea"].shift(-1)

total_gemeas = df_cabeca["is_gemea"].sum()
total_sorteios = len(df_cabeca)
print(f"Total de dezenas gêmeas na cabeça: {total_gemeas}/{total_sorteios} ({total_gemeas/total_sorteios*100:.1f}%) | Esperado aleatório = 10.0%")

# Quando sai gêmea, qual a chance de sair gêmea logo em seguida?
apos_gemea = df_cabeca[df_cabeca["is_gemea"] == 1]["next_is_gemea"].dropna()
print(f"Quando sai DEZENA GÊMEA na cabeça, próxima também é gêmea: {int(apos_gemea.sum())}/{len(apos_gemea)} ({apos_gemea.mean()*100:.1f}%)")

# 3. TERMINAÇÕES DE DÍGITO (FINAL DA MILHAR / FINAL DA DEZENA: 0 a 9)
print("\n=== 3. TRANSIÇÃO DE TERMINAÇÃO (ÚLTIMO DÍGITO DA MILHAR: 0-9) ===")
df_cabeca["unidade"] = df_cabeca["milhar"].str[-1]
df_cabeca["next_unidade"] = df_cabeca["unidade"].shift(-1)

trans_unid = defaultdict(Counter)
for _, r in df_cabeca.dropna(subset=["next_unidade"]).iterrows():
    trans_unid[r["unidade"]][r["next_unidade"]] += 1

print("Top transições de terminação (Último dígito -> Próximo último dígito):")
for u in sorted(trans_unid.keys()):
    cnt = trans_unid[u]
    tot = sum(cnt.values())
    top_dest, top_c = cnt.most_common(1)[0]
    p = (top_c / tot) * 100
    print(f"Terminação [{u}] -> Próxima [{top_dest}]: {top_c}/{tot}x ({p:.1f}%) | Esperado: 10.0%")

# 4. RAIZ DIGITAL (SOMA REDUZIDA DE 1 A 9)
print("\n=== 4. RAIZ DIGITAL DA MILHAR (1 A 9) ===")
def raiz_digital(milhar_str):
    s = sum(int(c) for c in milhar_str)
    while s > 9:
        s = sum(int(c) for c in str(s))
    return s

df_cabeca["raiz_digital"] = df_cabeca["milhar"].apply(raiz_digital)
print("Distribuição da Raiz Digital na Cabeça:")
for rd, c in df_cabeca["raiz_digital"].value_counts().sort_index().items():
    print(f"  Raiz {rd}: {c} vezes ({c/len(df_cabeca)*100:.1f}%)")

# 5. PUXADAS POR GRUPO DE FAMÍLIA / VIZINHOS
print("\n=== 5. PADRÃO DE VIZINHANÇA DE GRUPOS (G -> G-1 ou G+1) ===")
df_cabeca["grupo_int"] = df_cabeca["grupo"].astype(int)
df_cabeca["next_grupo_int"] = df_cabeca["grupo_int"].shift(-1)

vizinhos_count = 0
total_valid = 0
for _, r in df_cabeca.dropna(subset=["next_grupo_int"]).iterrows():
    g1 = int(r["grupo_int"])
    g2 = int(r["next_grupo_int"])
    total_valid += 1
    # Vizinho considerando ciclo circular 1 a 25
    diff = abs(g1 - g2)
    if diff == 1 or diff == 24 or diff == 0:
        vizinhos_count += 1

p_viz = (vizinhos_count / total_valid) * 100
print(f"Sorteio consecutivo em que o Grupo seguinte é VIZINHO (G-1, G ou G+1): {vizinhos_count}/{total_valid} ({p_viz:.1f}%) | Esperado: 3/25 = 12.0%")

# 6. CONFLUÊNCIA DE OURO: QUANDO UMA DEZENA ALTA OU BAIXA ALTERNA POR HORÁRIO
print("\n=== 6. CONFLUÊNCIA DE FAIXA (ALTA/BAIXA) POR HORÁRIO ===")
for ext in ["PPT", "PTM", "PT", "PTV", "PTN", "CORUJA"]:
    sub = df_cabeca[df_cabeca["extracao"] == ext]
    alta = (sub["faixa_dezena"] == "ALTA").sum()
    baixa = (sub["faixa_dezena"] == "BAIXA").sum()
    tot = len(sub)
    if tot > 0:
        print(f"Horário {ext:<6}: Alta = {alta/tot*100:.1f}% | Baixa = {baixa/tot*100:.1f}% (Total: {tot})")
