"""D5 (parte 1): a curva da noite pelas versoes oficiais gravadas ao vivo (dados/noite/versoes-tse/br).

Saida: resultados/d5_curva_noite.csv (hora de geracao, % de secoes, votos e % de Lula e Flavio, vantagem do Lula)
e resultados/d5_curva_noite.json (pausa, trocas de lideranca, maior vantagem de cada um, hora em que passou de 50%).
"""
import csv, json
from pathlib import Path
R = Path(__file__).resolve().parents[1]
linhas = []
for p in (R / "dados/noite/versoes-tse/br").glob("*.json"):
    d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
    c = {}
    for a in d["carg"][0]["agr"]:
        for pa in a["par"]:
            for k in pa["cand"]:
                c[k["nmu"]] = int(k["vap"])
    l, f = c.get("LULA", 0), c.get("FLAVIO BOLSONARO", 0)
    if l + f == 0:
        continue
    linhas.append({"gerado": f'{d["dg"][6:]}-{d["dg"][3:5]}-{d["dg"][:2]} {d["hg"]}', "pct_secoes": float(d["s"]["pstn"].replace(",", ".")),
                   "lula": l, "flavio": f, "lula_pct": round(l / (l + f) * 100, 3), "vantagem_lula": round((l - f) / (l + f) * 100, 3)})
linhas.sort(key=lambda x: (x["gerado"], x["pct_secoes"]))
with open(R / "resultados/d5_curva_noite.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)
trocas = [b for a, b in zip(linhas, linhas[1:]) if (a["vantagem_lula"] > 0) != (b["vantagem_lula"] > 0)]
dep1 = [x for x in linhas if x["pct_secoes"] >= 1]
out = {"versoes": len(linhas), "primeira": linhas[0], "ultima": linhas[-1],
       "trocas_de_lideranca": [{"gerado": t["gerado"], "pct_secoes": t["pct_secoes"], "vantagem_lula": t["vantagem_lula"]} for t in trocas],
       "maior_vantagem_flavio_depois_de_1pct": min(dep1, key=lambda x: x["vantagem_lula"]),
       "maior_vantagem_lula_depois_de_1pct": max(dep1, key=lambda x: x["vantagem_lula"]),
       "maior_intervalo_sem_nova_versao_min": max(((b, a) for a, b in zip(linhas, linhas[1:])), key=lambda ab: ab[0]["gerado"] > ab[1]["gerado"] and 0)[0]["gerado"]}
from datetime import datetime
ts = [datetime.fromisoformat(x["gerado"]) for x in linhas]
gaps = sorted(((ts[i + 1] - ts[i]).total_seconds() / 60, linhas[i]["gerado"], linhas[i + 1]["gerado"], linhas[i]["pct_secoes"]) for i in range(len(ts) - 1))[-3:]
out["maiores_intervalos_sem_nova_versao"] = [{"minutos": round(g[0], 1), "de": g[1], "ate": g[2], "pct_secoes": g[3]} for g in gaps[::-1]]
del out["maior_intervalo_sem_nova_versao_min"]
(R / "resultados/d5_curva_noite.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
print(json.dumps(out, indent=1, ensure_ascii=False))
