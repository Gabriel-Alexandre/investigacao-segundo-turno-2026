"""Revisão adversarial em dois papéis, com a objeção mais forte de cada lado virando conta.

Advogado da acusação: o que o projeto pode ter deixado de ver a favor da fraude.
Advogado da defesa: o que o projeto pode ter exagerado contra o resultado.

Saída: resultados/revisao_adversarial.json (as contas) e docs/REVISAO_ADVERSARIAL.md (gerado a partir delas)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1]
K = ["uf", "municipio", "zona", "secao"]
MARGEM = 64256232 - 59826041


def main():
    t1 = pd.read_parquet(R / "dados/derivados/t1_secoes.parquet")
    t2 = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
    r3 = pd.read_parquet(R / "dados/derivados/r3_secoes.parquet")
    for c in ["aptos", "comparecimento", "lula", "flavio", "cury", "renan", "caiado", "zema", "demais", "branco", "nulo"]:
        t1[c] = pd.to_numeric(t1[c], errors="coerce")
        if c not in ("aptos", "comparecimento"):
            t1.loc[t1.aptos.notna(), c] = t1.loc[t1.aptos.notna(), c].fillna(0)
    for c in ["aptos", "comparecimento", "bu_lula", "bu_flavio", "log_votos_depois_17h"]:
        t2[c] = pd.to_numeric(t2[c], errors="coerce")
    d = t1.merge(t2, on=K, suffixes=("1", "2")).dropna(subset=["aptos1", "bu_lula"])
    d["outros"] = d.cury + d.renan + d.caiado + d.zema + d.demais
    d["dL"] = d.bu_lula - d.lula
    d["dF"] = d.bu_flavio - d.flavio
    out = {"acusacao": {}, "defesa": {}}

    # X1: reserva estrita (só os votos dos outros candidatos): quanto voto do Lula não teria de onde vir?
    eL = (d.dL - d.outros).clip(lower=0)
    eF = (d.dF - d.outros).clip(lower=0)
    out["acusacao"]["X1_reserva_so_com_outros_candidatos"] = {
        "objecao": "a volta de quem faltou e a queda do nulo podem esconder troca; conte só os votos dos outros candidatos",
        "excesso_lula": int(eL.sum()), "excesso_flavio": int(eF.sum()),
        "excesso_lula_contra_margem_pct": round(float(eL.sum()) / MARGEM * 100, 2),
        "leitura": "é o máximo de votos do Lula que exigiria eleitor novo, ex-nulo ou troca direta, seção a seção"}
    # X2: votos depois das 17h nas seções do Lula, todos do Lula
    lula_vence = d.bu_lula > d.bu_flavio
    v17 = int(d.loc[lula_vence, "log_votos_depois_17h"].fillna(0).sum())
    out["acusacao"]["X2_votos_depois_das_17h_todos_do_lula"] = {
        "objecao": "a prorrogação favoreceu um lado", "votos_depois_17h_onde_o_lula_venceu": v17,
        "contra_margem_pct": round(v17 / MARGEM * 100, 2)}
    # X3: os 1.686 acima de 95%: e se fossem todos inventados?
    val = d.bu_lula + d.bu_flavio
    u = d[(val >= 50) & (d.bu_lula / val > 0.95)]
    out["acusacao"]["X3_unanimidades_como_se_fossem_falsas"] = {
        "objecao": "seções com mais de 95% para o Lula podem ser manipuladas", "secoes": int(len(u)),
        "vantagem_do_lula_nelas": int((u.bu_lula - u.bu_flavio).sum()),
        "contra_margem_pct": round(float((u.bu_lula - u.bu_flavio).sum()) / MARGEM * 100, 2),
        "ja_eram_acima_de_90_no_1t": int((u.lula / (u.lula + u.flavio) > 0.90).sum())}
    # X4: as seções com mais resíduo a favor do Lula (1%), somadas
    top = r3.sort_values("res", ascending=False).head(len(r3) // 100)
    top = top.merge(d[K + ["bu_lula", "bu_flavio"]], on=K)
    out["acusacao"]["X4_o_1pct_de_secoes_mais_acima_do_previsto"] = {
        "objecao": "a fraude pode estar espalhada no 1% de seções que mais passaram do previsto pelo 1º turno",
        "secoes": int(len(top)), "residuo_medio_pontos": round(float(top.res.mean()), 2),
        "votos_a_mais_do_lula_se_voltassem_ao_previsto": int((top.res / 100 * (top.bu_lula + top.bu_flavio)).sum()),
        "contra_margem_pct": round(float((top.res / 100 * (top.bu_lula + top.bu_flavio)).sum()) / MARGEM * 100, 2)}
    # Y1: resíduo do modelo por região (o modelo nacional pode puxar uma região)
    out["defesa"]["Y1_residuo_por_regiao"] = {
        "objecao": "um modelo único para o país marca como anomalia o que é diferença regional",
        "residuo_medio_por_regiao": r3.groupby("regiao").res.mean().round(3).to_dict()}
    # Y2: as unanimidades de 2022
    a = pd.read_parquet(R / "dados/derivados/s2022_t2.parquet")
    a = a[(a.lula + a.bolsonaro) >= 50]
    out["defesa"]["Y2_unanimidades_em_2022"] = {
        "objecao": "seção com mais de 95% para o Lula é comum no Nordeste e em aldeias, não só em 2026",
        "lula_acima_95_em_2022": int((a.lula / (a.lula + a.bolsonaro) > 0.95).sum()),
        "bolsonaro_acima_95_em_2022": int((a.lula / (a.lula + a.bolsonaro) < 0.05).sum())}
    # Y3: validação do modelo de transferência em 2022
    d2 = json.loads((R / "resultados/d2_transferencia.json").read_text(encoding="utf-8"))
    out["defesa"]["Y3_modelo_de_transferencia_em_2022"] = {"objecao": "inferência ecológica pode inventar transferências", **d2["validacao_2022"]}
    (R / "resultados/revisao_adversarial.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
