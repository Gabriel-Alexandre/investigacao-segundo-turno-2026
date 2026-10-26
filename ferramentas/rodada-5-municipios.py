"""Rodada 5: as cidades que viraram são normais? (pedido do autor para o roteiro: "comparar com outras eleições, se é normal
ganhar ou aumentar em tantos municípios, e se é normal o Lula ganhar mais que o Flávio no Sul")

  M1  municípios que viraram entre os turnos (o líder entre os 2 finalistas no 1º turno perde o município no 2º), nos 2 sentidos
  M2  em quantos municípios o PT ganhou mais votos que o adversário entre os turnos
  M3  a parte do PT no que os 2 ganharam, por região

Mesmas fontes da rodada 4 (votação por candidato e município do TSE, 2002 a 2022; boletins por seção de 2026 deste projeto).
O exterior (ZZ) fica fora. M2 e M3 refazem por outro caminho a rodada 7 do projeto do vídeo 19 (quem_ganhou_mais_por_ano.csv).

Também corrige o D4 da rodada 3 sem refazer a rodada inteira: o empate exato no 1º turno (2 municípios, Trabiju e Crixás do
Tocantins) era contado como do Flávio, e as cidades do exterior entravam na conta das que viraram. Refaz o vencedor em
resultados/d4_municipios.csv e o bloco D4 de resultados/rodada3.json com a mesma função da rodada 3 (d4_resumo).

Saída: resultados/rodada5_municipios_por_ano.csv, resultados/d4_municipios.csv e resultados/rodada3.json (bloco D4)
"""
from __future__ import annotations

import csv, importlib.util
from pathlib import Path

R = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("r4", R / "ferramentas/rodada-4-normalidade.py")
r4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(r4)
import pandas as pd

REGIAO = {**{u: "Norte" for u in "AC AM AP PA RO RR TO".split()}, **{u: "Nordeste" for u in "AL BA CE MA PB PE PI RN SE".split()},
          **{u: "Centro-Oeste" for u in "DF GO MS MT".split()}, **{u: "Sudeste" for u in "ES MG RJ SP".split()},
          **{u: "Sul" for u in "PR RS SC".split()}}
ADV = {2002: 45, 2006: 45, 2010: 45, 2014: 45, 2018: 17, 2022: 22}


def tabela(a):
    if a < 2026:
        v = r4.votos_municipio(a)
        v = v[v.SG_UF != "ZZ"]
        p = v[v.NR_CANDIDATO.astype(int).isin([13, ADV[a]])].copy()
        p["quem"] = (p.NR_CANDIDATO.astype(int) == 13).map({True: "pt", False: "ad"})
        q = p.pivot_table(index=["SG_UF", "CD_MUNICIPIO"], columns=["NR_TURNO", "quem"], values="v", aggfunc="sum").dropna()
        d = pd.DataFrame({"uf": q.index.get_level_values(0), "pt1": q[("1", "pt")].values, "ad1": q[("1", "ad")].values,
                          "pt2": q[("2", "pt")].values, "ad2": q[("2", "ad")].values})
    else:
        q = r4.votos_2026()
        q = q[q.uf != "zz"]
        d = pd.DataFrame({"uf": q.uf.str.upper().values, "pt1": q.lula.values, "ad1": q.flavio.values,
                          "pt2": q.bu_lula.values, "ad2": q.bu_flavio.values})
    return d


def corrigir_d4():
    import json
    import numpy as np
    sp = importlib.util.spec_from_file_location("r3", R / "ferramentas/rodada-3.py")
    r3 = importlib.util.module_from_spec(sp); sp.loader.exec_module(r3)
    mm = pd.read_csv(R / "resultados/d4_municipios.csv", dtype={"municipio": str})
    mm["venc1"] = np.select([mm.lula1 > mm.flavio1, mm.lula1 < mm.flavio1], ["lula", "flavio"], "empate")
    mm["venc2"] = np.select([mm.lula2 > mm.flavio2, mm.lula2 < mm.flavio2], ["lula", "flavio"], "empate")
    mm.to_csv(R / "resultados/d4_municipios.csv", index=False)
    j = json.loads((R / "resultados/rodada3.json").read_text(encoding="utf-8"))
    j["D4_cidades_que_viraram"] = r3.d4_resumo(mm)
    (R / "resultados/rodada3.json").write_text(json.dumps(j, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({k: v for k, v in j["D4_cidades_que_viraram"].items() if k != "maiores_em_eleitores"}, ensure_ascii=False))


def main():
    corrigir_d4()
    linhas = []
    for a in [2002, 2006, 2010, 2014, 2018, 2022, 2026]:
        d = tabela(a)
        n = len(d)
        pt_virou = int(((d.pt1 < d.ad1) & (d.pt2 > d.ad2)).sum())
        ad_virou = int(((d.pt1 > d.ad1) & (d.pt2 < d.ad2)).sum())
        gpt, gad = d.pt2 - d.pt1, d.ad2 - d.ad1
        mais = int((gpt > gad).sum())
        lin = {"ano": a, "municipios": n, "viraram_para_o_pt": pt_virou, "viraram_para_o_adversario": ad_virou,
               "viraram_total": pt_virou + ad_virou, "viraram_pct": round((pt_virou + ad_virou) / n * 100, 2),
               "pt_ganhou_mais_votos_em": mais, "pt_ganhou_mais_votos_pct": round(mais / n * 100, 1)}
        d["reg"] = d.uf.map(REGIAO)
        for reg, g in d.groupby("reg"):
            gp, ga = (g.pt2 - g.pt1).sum(), (g.ad2 - g.ad1).sum()
            lin[f"parte_do_pt_{reg}"] = round(gp / (gp + ga) * 100, 1)
        linhas.append(lin)
        print(lin, flush=True)
    with open(R / "resultados/rodada5_municipios_por_ano.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)


if __name__ == "__main__":
    main()
