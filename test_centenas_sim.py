import sqlite3
import pandas as pd
from collections import defaultdict, Counter

db_path = r"C:\Users\Derley\.gemini\antigravity\scratch\deu_no_poste_analytics\deu_no_poste_12m.db"
conn = sqlite3.connect(db_path)
df = pd.read_sql("SELECT * FROM resultados WHERE is_cabeca = 1 ORDER BY id_sorteio ASC", conn)
conn.close()

df["centena_digito"] = df["centena"].str[0] # Primeiro dígito da centena (centena pura)
df["next_centena"] = df["centena"].shift(-1)
df["next_dezena"] = df["dezena"].shift(-1)
df["next_bicho"] = df["bicho"].shift(-1)
df["next_extracao"] = df["extracao"].shift(-1)

# Simular Nível 2: Jogar 20 Centenas
# Para os top gatilhos de PTM -> PT e CORUJA -> PPT
# Um bicho tem 4 dezenas. Se jogamos as 5 centenas mais frequentes (ex: dígitos 1, 3, 5, 7, 9 se paridade for ímpar)
# 4 dezenas x 5 dígitos de centena = 20 centenas = R$ 20,00 por entrada.
# Prêmio Centena Seca = R$ 500,00 + Dezena (R$ 60) + Grupo (R$ 18) = R$ 578,00.

triggers = [
    ("CORUJA", "Borboleta", "PPT", "Camelo", ["29", "30", "31", "32"]),
    ("CORUJA", "Coelho", "PPT", "Cachorro", ["17", "18", "19", "20"]),
    ("PTM", "Borboleta", "PT", "Elefante", ["45", "46", "47", "48"]),
    ("PTM", "Burro", "PT", "Coelho", ["37", "38", "39", "40"]),
    ("PTV", "Gato", "NOITE", "Jacaré", ["57", "58", "59", "60"])
]

print("=== SIMULAÇÃO NÍVEL 2: 20 CENTENAS (CUSTO: R$ 20,00 | PRÊMIO: R$ 578,00) ===")
# Dígitos de centena mais quentes do banco: 1, 3, 5, 7, 9 (ímpares) ou 2, 4, 6, 8, 0 (pares)
for ext_in, b_in, ext_out, b_out, dezenas_bicho in triggers:
    matches = 0
    acertos_centena = 0
    acertos_so_dezena = 0
    
    for i in range(len(df) - 1):
        r1 = df.iloc[i]
        r2 = df.iloc[i+1]
        
        c1 = (r1["bicho"] == b_in) and (ext_in in r1["extracao"])
        c2 = (ext_out in r2["extracao"]) or (ext_out == "NOITE" and r2["extracao"] in ["PTN", "FEDERAL"])
        
        if c1 and c2:
            matches += 1
            # Gerar 20 centenas usando os 5 dígitos de centena mais frequentes daquela extração
            dez_sort = r2["dezena"]
            cent_sort = r2["centena"]
            
            # 5 centenas mais frequentes (0, 1, 3, 7, 8)
            digitos_usados = ["0", "1", "3", "7", "8"]
            cartoes = [f"{d}{dez}" for d in digitos_usados for dez in dezenas_bicho]
            
            if cent_sort in cartoes:
                acertos_centena += 1
            elif dez_sort in dezenas_bicho:
                acertos_so_dezena += 1
                
    if matches > 0:
        custo = matches * 20 # 20 cartões de R$ 1,00
        # Se acertou a centena ganha R$ 578 (centena + dezena + grupo)
        # Se errou a centena mas acertou a dezena ganha R$ 78 (dezena + grupo)
        retorno = (acertos_centena * 578) + (acertos_so_dezena * 78)
        lucro = retorno - custo
        roi = (lucro / custo) * 100
        print(f"Gatilho [{ext_in} {b_in}] -> [{ext_out} {b_out}]: {acertos_centena} Centenas + {acertos_so_dezena} Dezenas em {matches} jogos | Custo: R$ {custo} | Retorno: R$ {retorno} | Lucro: R$ {lucro:+} (ROI: {roi:+.1f}%)")
