"""Bloco P (P1, P2, P5) a partir de dados/derivados/historico_turnos.csv (TSE, 1994 a 2022) e do 2026 gravado na noite.

P1: presidente, quem liderou o 1º turno ganhou o 2º?  (1989 não está no CDN do TSE: entra de dados/manuais/presidente_1989.csv)
P2: governador, todos os 2º turnos; taxa de virada geral e com frente de até 3 pontos e líder abaixo de 50%;
    modelo logístico P(virada) pela frente do líder no 1º turno, avaliado em 1,87 ponto.
P5: quem venceu Minas no 1º turno de presidente venceu a eleição?

Saída: resultados/p_historico.json e resultados/p_segundos_turnos.csv
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def ler():
    d = defaultdict(dict)  # (ano, cargo, uf, turno) -> {cand: votos}
    nomes = {}
    with open(RAIZ / "dados" / "derivados" / "historico_turnos.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (int(r["ano"]), r["cargo"], r["uf"], int(r["turno"]))
            d[k][r["nr_candidato"]] = d[k].get(r["nr_candidato"], 0) + int(r["votos_nominais"])
            nomes[(int(r["ano"]), r["cargo"], r["uf"], r["nr_candidato"])] = r["nome_urna"]
    m = RAIZ / "dados" / "manuais" / "presidente_1989.csv"
    if m.exists():
        with open(m, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                k = (1989, "presidente", "BR", int(r["turno"]))
                d[k][r["nr_candidato"]] = int(r["votos"])
                nomes[(1989, "presidente", "BR", r["nr_candidato"])] = r["nome_urna"]
    return d, nomes


def corridas(d, nomes, cargo):
    out = []
    for (ano, cg, uf, turno), v1 in d.items():
        if cg != cargo or turno != 1:
            continue
        if cargo == "presidente" and uf != "BR":
            continue
        v2 = d.get((ano, cg, uf, 2))
        if not v2 or len([x for x in v2.values() if x > 0]) < 2:
            continue
        val1 = sum(v1.values())
        ordem = sorted(v1.items(), key=lambda x: -x[1])
        lider, seg = ordem[0], ordem[1]
        venc2 = max(v2.items(), key=lambda x: x[1])
        val2 = sum(v2.values())
        out.append({
            "ano": ano, "cargo": cargo, "uf": uf,
            "lider_1t": nomes[(ano, cg, uf, lider[0])], "lider_1t_pct": round(lider[1] / val1 * 100, 2),
            "segundo_1t": nomes[(ano, cg, uf, seg[0])], "segundo_1t_pct": round(seg[1] / val1 * 100, 2),
            "frente_1t_pontos": round((lider[1] - seg[1]) / val1 * 100, 2),
            "vencedor_2t": nomes[(ano, cg, uf, venc2[0])], "vencedor_2t_pct": round(venc2[1] / val2 * 100, 2),
            "virada": int(venc2[0] != lider[0]),
        })
    return sorted(out, key=lambda x: (x["ano"], x["uf"]))


def logistica(xs, ys, iters=200):
    """Regressão logística simples P(y=1) = 1 / (1 + exp(-(a + b x))), por Newton-Raphson."""
    a = b = 0.0
    for _ in range(iters):
        ga = gb = haa = hab = hbb = 0.0
        for x, y in zip(xs, ys):
            p = 1 / (1 + math.exp(-(a + b * x)))
            ga += y - p
            gb += (y - p) * x
            w = p * (1 - p)
            haa += w
            hab += w * x
            hbb += w * x * x
        det = haa * hbb - hab * hab
        if det == 0:
            break
        da = (hbb * ga - hab * gb) / det
        db = (haa * gb - hab * ga) / det
        a, b = a + da, b + db
        if abs(da) + abs(db) < 1e-10:
            break
    return a, b


def main() -> None:
    d, nomes = ler()
    pres = corridas(d, nomes, "presidente")
    gov = corridas(d, nomes, "governador")
    # Minas: vencedor de MG no 1º turno de presidente contra o vencedor da eleição
    minas = []
    for ano in sorted({k[0] for k in d if k[1] == "presidente"}):
        v1 = d.get((ano, "presidente", "MG", 1))
        br2 = d.get((ano, "presidente", "BR", 2)) or d.get((ano, "presidente", "BR", 1))
        if not v1 or not br2:
            continue
        mg1 = max(v1.items(), key=lambda x: x[1])[0]
        vencedor = max(br2.items(), key=lambda x: x[1])[0]
        minas.append({"ano": ano, "mg_1t": nomes[(ano, "presidente", "MG", mg1)], "vencedor": nomes[(ano, "presidente", "BR", vencedor)],
                      "acertou": int(mg1 == vencedor)})
    viradas_gov = sum(x["virada"] for x in gov)
    perto = [x for x in gov if x["frente_1t_pontos"] <= 3 and x["lider_1t_pct"] < 50]
    xs = [x["frente_1t_pontos"] for x in gov]
    ys = [x["virada"] for x in gov]
    a, b = logistica(xs, ys)
    p_187 = 1 / (1 + math.exp(-(a + b * 1.87)))
    res = {
        "P1_presidente": {"segundos_turnos": len(pres), "viradas": sum(x["virada"] for x in pres),
                          "laplace_virada": round((sum(x["virada"] for x in pres) + 1) / (len(pres) + 2), 4),
                          "corridas": pres},
        "P2_governador": {"segundos_turnos": len(gov), "viradas": viradas_gov,
                          "taxa_virada": round(viradas_gov / len(gov), 4),
                          "perto_frente_ate_3_e_lider_abaixo_50": {"n": len(perto), "viradas": sum(x["virada"] for x in perto),
                                                                     "taxa": round(sum(x["virada"] for x in perto) / len(perto), 4) if perto else None},
                          "logistica": {"a": a, "b": b, "p_virada_com_frente_1_87": round(p_187, 4)}},
        "P5_minas_1t": {"eleicoes": len(minas), "acertos": sum(x["acertou"] for x in minas), "anos": minas},
    }
    (RAIZ / "resultados").mkdir(exist_ok=True)
    (RAIZ / "resultados" / "p_historico.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    with open(RAIZ / "resultados" / "p_segundos_turnos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(gov[0].keys()))
        w.writeheader()
        w.writerows(pres + gov)
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk not in ("corridas", "anos")} for k, v in res.items()}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
