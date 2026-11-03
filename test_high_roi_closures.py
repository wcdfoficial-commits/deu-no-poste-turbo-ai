import sqlite3
import pandas as pd
from collections import defaultdict, Counter

db_path = r"C:\Users\Derley\.gemini\antigravity\scratch\deu_no_poste_analytics\deu_no_poste_12m.db"
conn = sqlite3.connect(db_path)
df = pd.read_sql("SELECT * FROM resultados WHERE is_cabeca = 1 ORDER BY id_sorteio ASC", conn)
conn.close()

df["sufixo"] = df["milhar"].str[2:]
df["next_sufixo"] = df["sufixo"].shift(-1)
df["next_milhar"] = df["milhar"].shift(-1)
df["next_extracao"] = df["extracao"].shift(-1)
df["next_bicho"] = df["bicho"].shift(-1)

# Simular para todos os pares de dezenas com ocorrência >= 10
trans = defaultdict(Counter)
for _, r in df.dropna(subset=["next_sufixo"]).iterrows():
    trans[r["sufixo"]][r["next_sufixo"]] += 1

results_dez = []
for orig, cnt in trans.items():
    tot = sum(cnt.values())
    if tot >= 12: # Filtro de relevância estatística
        for dest, c in cnt.items():
            if c >= 2:
                prob = (c / tot) * 100
                custo = tot * 100
                retorno = c * 4578 # Paga Milhar (4000) + Centena (500) + Dezena (60) + Grupo (18)
                lucro = retorno - custo
                roi = (lucro / custo) * 100
                if roi > 0:
                    results_dez.append({
                        "origem": orig,
                        "destino": dest,
                        "acertos": c,
                        "total_jogos": tot,
                        "taxa": prob,
                        "custo": custo,
                        "retorno": retorno,
                        "lucro": lucro,
                        "roi": roi
                    })

df_res = pd.DataFrame(results_dez).sort_values("lucro", ascending=False)
print("=== TOP 10 FECHAMENTOS DE 100 CARTÕES (DEZENA -> DEZENA) ===")
for _, r in df_res.head(12).iterrows():
    print(f"Dezena [{r['origem']}] -> Fecha 100 Milhares de [{r['destino']}]: Acertos: {r['acertos']}/{r['total_jogos']}x ({r['taxa']:.1f}%) | Custo: R$ {r['custo']} | Retorno: R$ {r['retorno']} | Lucro: R$ {r['lucro']:+} (ROI: {r['roi']:+.1f}%)")

# Também testar fechamento por HORÁRIO FIXO
# Ex: PTM -> PT
print("\n=== TOP FECHAMENTOS DE 100 CARTÕES ESPECÍFICOS: PTM -> PT ===")
ptm_to_pt = df[(df["extracao"] == "PTM") & (df["next_extracao"] == "PT")]
trans_ptm = defaultdict(Counter)
for _, r in ptm_to_pt.dropna(subset=["next_sufixo"]).iterrows():
    trans_ptm[r["bicho"]][r["next_sufixo"]] += 1

res_ptm = []
for b_orig, cnt in trans_ptm.items():
    tot = sum(cnt.values())
    if tot >= 8:
        for dez_dest, c in cnt.items():
            if c >= 2:
                prob = (c / tot) * 100
                custo = tot * 100
                retorno = c * 4578
                lucro = retorno - custo
                roi = (lucro / custo) * 100
                if roi > 0:
                    res_ptm.append({
                        "bicho_orig": b_orig,
                        "dez_dest": dez_dest,
                        "acertos": c,
                        "total": tot,
                        "taxa": prob,
                        "lucro": lucro,
                        "roi": roi
                    })

for r in sorted(res_ptm, key=lambda x: x["lucro"], reverse=True)[:10]:
    print(f"PTM [{r['bicho_orig']:<9}] -> PT fecha Dezena [{r['dez_dest']}]: {r['acertos']}/{r['total']}x ({r['taxa']:.1f}%) | Lucro: R$ {r['lucro']:+} (ROI: {r['roi']:+.1f}%)")
