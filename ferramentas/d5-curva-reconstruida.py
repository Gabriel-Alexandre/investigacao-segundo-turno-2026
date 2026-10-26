"""D5 (parte 2): a noite refeita pela hora de recebimento de cada boletim, conferida contra as versões oficiais gravadas ao vivo.

Ordena as seções pela hora de recebimento (aux.json), acumula os votos e compara a vantagem do Lula com a de cada versão
oficial no mesmo horário de geração. Mostra também de que região vinham os boletins em cada trecho da noite e o que
explica as duas trocas de liderança.

Saída: resultados/d5_reconstruida.json e resultados/d5_reconstruida.csv
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1]
REG = {"ac": "Norte", "am": "Norte", "ap": "Norte", "pa": "Norte", "ro": "Norte", "rr": "Norte", "to": "Norte", "al": "Nordeste", "ba": "Nordeste",
       "ce": "Nordeste", "ma": "Nordeste", "pb": "Nordeste", "pe": "Nordeste", "pi": "Nordeste", "rn": "Nordeste", "se": "Nordeste", "df": "Centro-Oeste",
       "go": "Centro-Oeste", "ms": "Centro-Oeste", "mt": "Centro-Oeste", "es": "Sudeste", "mg": "Sudeste", "rj": "Sudeste", "sp": "Sudeste",
       "pr": "Sul", "rs": "Sul", "sc": "Sul", "zz": "Exterior"}


def main():
    d = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
    for c in ["bu_lula", "bu_flavio"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=["bu_lula"])
    d["rec"] = pd.to_datetime(d.recebido, errors="coerce")
    d = d.dropna(subset=["rec"]).sort_values("rec")
    d["regiao"] = d.uf.map(REG)
    d["cL"], d["cF"] = d.bu_lula.cumsum(), d.bu_flavio.cumsum()
    d["n"] = np.arange(1, len(d) + 1)
    d["vant"] = (d.cL - d.cF) / (d.cL + d.cF) * 100
    viva = pd.read_csv(R / "resultados/d5_curva_noite.csv")
    viva["gerado"] = pd.to_datetime(viva.gerado)
    pos = np.searchsorted(d.rec.values, viva.gerado.values, side="right") - 1
    viva["vant_reconstruida"] = np.where(pos >= 0, d.vant.values[np.clip(pos, 0, None)], np.nan)
    viva["secoes_reconstruidas_pct"] = np.where(pos >= 0, (pos + 1) / 499248 * 100, np.nan)
    viva["diferenca"] = viva.vant_reconstruida - viva.vantagem_lula
    dep1 = viva[viva.pct_secoes >= 1]
    # regiões por trecho
    cortes = ["2026-10-25 17:00", "2026-10-25 19:01:56", "2026-10-25 19:44:50", "2026-10-25 20:24:19", "2026-10-25 21:10", "2026-10-26 12:00"]
    trechos = {}
    for a, b in zip(cortes, cortes[1:]):
        g = d[(d.rec >= a) & (d.rec < b)]
        if len(g):
            trechos[f"{a[11:16]} a {b[11:16]}"] = {"secoes": int(len(g)), "lula_pct": round(float(g.bu_lula.sum() / (g.bu_lula.sum() + g.bu_flavio.sum()) * 100), 2),
                                                 "regioes_pct": (g.regiao.value_counts(normalize=True) * 100).round(1).to_dict()}
    out = {"versoes_comparadas_depois_de_1pct": int(len(dep1)),
           "diferenca_media_absoluta_pontos": round(float(dep1.diferenca.abs().mean()), 3),
           "diferenca_maxima_absoluta_pontos": round(float(dep1.diferenca.abs().max()), 3),
           "secoes_por_hora_de_recebimento": trechos,
           "nota": "a versão oficial é gerada depois que o boletim é totalizado; a reconstrução usa a hora de recebimento do boletim"}
    viva.to_csv(R / "resultados/d5_reconstruida.csv", index=False)
    (R / "resultados/d5_reconstruida.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
