"""Bloco P3: o líder das pesquisas perdeu o 2º turno? Brasil, presidente e governador, 2014, 2018 e 2022.

Pesquisas: base de pesquisas da reta final do Pindograma (cópia, com sha256, do projeto previsao-segundo-turno-2026),
só 2º turno, divulgadas nos últimos 7 dias antes da votação, estimuladas. Por pesquisa, a parte de cada um dos dois
candidatos entre os dois (votos válidos). Por disputa: a última pesquisa de cada instituto, e a média delas.
Resultado: dados/derivados/historico_turnos.csv (TSE).

Saída: resultados/p3_pesquisas.json e resultados/p3_disputas.csv
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ.parent / "previsao-segundo-turno-2026" / "dados" / "derivados" / "copias"
COPIAS = RAIZ / "dados" / "copias"
ARQS = ["pindograma-late-polls-2012-2018.csv", "pindograma-late-polls-2022.csv"]


def copiar() -> dict:
    COPIAS.mkdir(parents=True, exist_ok=True)
    man = {}
    for a in ARQS:
        if not (COPIAS / a).exists():
            shutil.copy2(ORIGEM / a, COPIAS / a)
        man[a] = {"origem": f"previsao-segundo-turno-2026/dados/derivados/copias/{a}",
                  "sha256": hashlib.sha256((COPIAS / a).read_bytes()).hexdigest()}
    return man


def resultados() -> dict:
    out = {}
    with open(RAIZ / "dados" / "derivados" / "historico_turnos.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["turno"] != "2":
                continue
            k = (int(r["ano"]), r["cargo"], r["uf"])
            out.setdefault(k, {})[int(r["nr_candidato"])] = int(r["votos_nominais"])
    return out


def main() -> None:
    man = copiar()
    a = pd.read_csv(COPIAS / ARQS[0], low_memory=False)
    a = a.rename(columns={"QT_ENTREVISTADOS": "n"})
    b = pd.read_csv(COPIAS / ARQS[1], low_memory=False)
    b = b.rename(columns={"QT_ENTREVISTADO": "n"})
    cols = ["year", "NR_IDENTIFICACAO_PESQUISA", "SG_UE", "CD_CARGO", "estimulada", "scenario_id", "result",
            "DT_FIM_PESQUISA", "turno", "NUMERO_CANDIDATO", "pretty_name", "second_round_date"]
    p = pd.concat([a[cols], b[cols]], ignore_index=True)
    p = p[(p.turno == 2) & (p.CD_CARGO.isin([1, 3])) & (p.year.isin([2014, 2018, 2022])) & (p.estimulada != 0)]
    p["fim"] = pd.to_datetime(p.DT_FIM_PESQUISA)
    p["eleicao"] = pd.to_datetime(p.second_round_date)
    p = p[(p.fim >= p.eleicao - timedelta(days=7)) & (p.fim < p.eleicao)]
    res = resultados()
    disputas = []
    acertos_pesquisa = total_pesquisa = 0
    for (ano, cargo_cd, ue), g in p.groupby(["year", "CD_CARGO", "SG_UE"]):
        cargo = "presidente" if cargo_cd == 1 else "governador"
        uf = "BR" if cargo_cd == 1 else str(ue)
        r = res.get((int(ano), cargo, uf))
        if not r or len(r) < 2:
            continue
        dois = sorted(r, key=lambda c: -r[c])[:2]
        venc = dois[0]
        tot = r[dois[0]] + r[dois[1]]
        frente_real = (r[dois[0]] - r[dois[1]]) / tot * 100
        ultimas = []
        for inst, gi in g.groupby("pretty_name"):
            ult = gi[gi.fim == gi.fim.max()]
            pid = ult.NR_IDENTIFICACAO_PESQUISA.iloc[0]
            cen = ult[ult.NR_IDENTIFICACAO_PESQUISA == pid]
            cen = cen[cen.scenario_id == cen.scenario_id.iloc[0]]
            v = {int(c): float(x) for c, x in zip(cen.NUMERO_CANDIDATO, cen.result)}
            if dois[0] not in v or dois[1] not in v or v[dois[0]] + v[dois[1]] == 0:
                continue
            s = v[dois[0]] + v[dois[1]]
            frente = (v[dois[0]] - v[dois[1]]) / s * 100  # positivo = pesquisa a favor de quem venceu
            ultimas.append({"instituto": inst, "frente_vencedor": frente})
            total_pesquisa += 1
            acertos_pesquisa += int(frente > 0)
        if not ultimas:
            continue
        media = sum(x["frente_vencedor"] for x in ultimas) / len(ultimas)
        disputas.append({"ano": int(ano), "cargo": cargo, "uf": uf, "institutos": len(ultimas),
                         "frente_media_pesquisas_para_o_vencedor": round(media, 2),
                         "frente_real_do_vencedor": round(frente_real, 2),
                         "erro_media": round(media - frente_real, 2),
                         "lider_das_pesquisas_venceu": int(media > 0), "empate_nas_pesquisas": int(media == 0)})
    n = len(disputas)
    erros = [abs(d["erro_media"]) for d in disputas]
    out = {"copias": man, "disputas": n,
           "lider_das_pesquisas_venceu": sum(d["lider_das_pesquisas_venceu"] for d in disputas),
           "pesquisas_individuais": total_pesquisa, "pesquisas_que_apontaram_o_vencedor": acertos_pesquisa,
           "erro_medio_absoluto_da_frente_pontos": round(sum(erros) / n, 2),
           "erros_maiores_que_7_pontos_na_frente": sum(1 for e in erros if e > 7),
           "presidente": [d for d in disputas if d["cargo"] == "presidente"]}
    (RAIZ / "resultados" / "p3_pesquisas.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    with open(RAIZ / "resultados" / "p3_disputas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(disputas[0].keys()))
        w.writeheader()
        w.writerows(disputas)
    print(json.dumps({k: v for k, v in out.items() if k != "copias"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
