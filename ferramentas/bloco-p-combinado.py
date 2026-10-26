"""P7 (parte Brasil): a combinacao de 2026 nos 2os turnos de 2014 a 2022 (presidente e governador).

Junta resultados/p_segundos_turnos.csv (TSE) e resultados/p3_disputas.csv (pesquisas). Para cada disputa:
o lider do 1o turno era tambem o lider da media das pesquisas da ultima semana? e perdeu?
Saida: resultados/p7_brasil.json e resultados/p7_disputas.csv
"""
import csv, json
from pathlib import Path
R = Path(__file__).resolve().parents[1]
t = {(int(r["ano"]), r["cargo"], r["uf"]): r for r in csv.DictReader(open(R / "resultados/p_segundos_turnos.csv", encoding="utf-8"))}
p = {(int(r["ano"]), r["cargo"], r["uf"]): r for r in csv.DictReader(open(R / "resultados/p3_disputas.csv", encoding="utf-8"))}
linhas = []
for k, r in t.items():
    if k not in p:
        continue
    q = p[k]
    virada = r["virada"] == "1"
    lider_pesquisa_venceu = q["lider_das_pesquisas_venceu"] == "1"
    # o lider das pesquisas era o lider do 1o turno?  (se nao houve virada, o vencedor e o lider do 1o turno)
    pesquisa_com_lider_1t = (lider_pesquisa_venceu and not virada) or (not lider_pesquisa_venceu and virada)
    linhas.append({"ano": k[0], "cargo": k[1], "uf": k[2], "frente_1t": float(r["frente_1t_pontos"]), "lider_1t_pct": float(r["lider_1t_pct"]),
                   "pesquisas_com_o_lider_do_1t": int(pesquisa_com_lider_1t), "virada": int(virada),
                   "combinacao_2026": int(pesquisa_com_lider_1t and virada)})
def resumo(sub):
    n = len(sub); c = sum(x["combinacao_2026"] for x in sub); base = [x for x in sub if x["pesquisas_com_o_lider_do_1t"]]
    return {"disputas": n, "lider_1t_e_lider_das_pesquisas": len(base), "desses_perdeu": sum(x["virada"] for x in base),
            "taxa_condicional": round(sum(x["virada"] for x in base) / len(base), 4) if base else None,
            "combinacao_2026_sobre_todas": c, "laplace_combinacao": round((c + 1) / (n + 2), 4)}
out = {"todas_2014_2022": resumo(linhas),
       "frente_ate_3_e_lider_abaixo_50": resumo([x for x in linhas if x["frente_1t"] <= 3 and x["lider_1t_pct"] < 50]),
       "frente_ate_5": resumo([x for x in linhas if x["frente_1t"] <= 5]),
       "casos_da_combinacao": [x for x in linhas if x["combinacao_2026"]]}
(R / "resultados/p7_brasil.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
with open(R / "resultados/p7_disputas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(sorted(linhas, key=lambda x: (x["ano"], x["uf"])))
print(json.dumps(out, indent=1, ensure_ascii=False))

# ---- P7 final: as duas contas do pre-registro (independente e com dependencia) ----
h = json.loads((R / "resultados/p_historico.json").read_text(encoding="utf-8"))
pm = json.loads((R / "resultados/p4_polymarket.json").read_text(encoding="utf-8"))
fav = [x for x in csv.DictReader(open(R / "dados/derivados/polymarket_eleicoes.csv", encoding="utf-8"))
       if not x["fora"] and 0.75 <= float(x["preco_favorito"]) < 0.85 and x["vespera_utc"] < "2026-10-24"]
perdeu_antes = sum(1 for x in fav if x["acertou"] == "0")
p_pres = h["P1_presidente"]["laplace_virada"]
p_pm = perdeu_antes / len(fav)
p_mg = (0 + 1) / (h["P5_minas_1t"]["eleicoes"] + 2)
p7 = {
    "componentes": {
        "virada_presidente_laplace": p_pres,
        "favorito_polymarket_75_a_85_perdeu_antes_de_2026_10_24": {"perdeu": perdeu_antes, "de": len(fav), "taxa": round(p_pm, 4)},
        "minas_1t_falhar_laplace": round(p_mg, 4),
        "lider_1t_e_pesquisas_perdeu_2014_2022": out["todas_2014_2022"]["taxa_condicional"],
        "mesmo_em_disputa_apertada": out["frente_ate_3_e_lider_abaixo_50"]["taxa_condicional"],
        "virada_governador_frente_1_87": h["P2_governador"]["logistica"]["p_virada_com_frente_1_87"],
    },
    "a_independente_presidente_x_polymarket_x_minas": round(p_pres * p_pm * p_mg, 5),
    "b_dependente_brasil_lider_1t_e_pesquisas_perdeu": out["todas_2014_2022"]["taxa_condicional"],
    "b_dependente_em_disputa_apertada": out["frente_ate_3_e_lider_abaixo_50"]["taxa_condicional"],
}
(R / "resultados/p7_probabilidade.json").write_text(json.dumps(p7, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(p7, indent=1, ensure_ascii=False))
