"""Rodada 2: os testes da acusação que só precisam do 2º turno (pré-registro §5), com a régua do lado do Flávio.

  reconciliação: soma dos boletins contra o resultado oficial final (arquivo gravado na noite)
  A4: RDV contra boletim, seção a seção
  A5: log contra boletim (votos computados contra comparecimento)
  A6: votos depois das 17h de Brasília (e depois das 19h), teto contra a margem, e os 3 municípios da BA
  A7: rajadas e liberação sem digital (última hora contra a primeira, seções do Lula contra as do Flávio)
  A8 (parte 1): boletins recebidos durante a pausa e na cauda da noite (a comparação com o 1º turno vem na rodada 3)
  A9 (parte 1): urnas de contingência
  A10 (parte 1): seções com mais de 95% dos válidos para um candidato

Saída: resultados/rodada2.json e resultados/rodada2_secoes_marcadas.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[1]
MARGEM = 64256232 - 59826041
BA3 = {"38490": "Salvador", "35157": "Feira de Santana", "36854": "Lauro de Freitas"}


def main() -> None:
    d = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
    out: dict = {"secoes": int(len(d))}
    for c in ["bu_lula", "bu_flavio", "bu_branco", "bu_nulo", "rdv_lula", "rdv_flavio", "rdv_branco", "rdv_nulo", "comparecimento", "aptos", "log_votos"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    tem_bu = d.bu_lula.notna()
    out["sem_boletim"] = int((~tem_bu).sum())
    out["sem_rdv"] = int(d.rdv_lula.isna().sum())
    out["sem_log"] = int(d.log_votos.isna().sum())
    out["erros_de_leitura"] = {c: int(d[c].notna().sum()) for c in ["erro_bu", "erro_rdv", "erro_log"] if c in d}

    # reconciliação
    ofi = json.loads((R / "dados/noite/versoes-tse/br/4241309.json").read_text(encoding="utf-8", errors="replace"))
    oficial = {}
    for a in ofi["carg"][0]["agr"]:
        for p in a["par"]:
            for k in p["cand"]:
                oficial[k["nmu"]] = int(k["vap"])
    out["reconciliacao"] = {"boletins_lula": int(d.bu_lula.sum()), "oficial_lula": oficial.get("LULA"),
                            "boletins_flavio": int(d.bu_flavio.sum()), "oficial_flavio": oficial.get("FLAVIO BOLSONARO"),
                            "diferenca_lula": int(d.bu_lula.sum()) - oficial.get("LULA", 0),
                            "diferenca_flavio": int(d.bu_flavio.sum()) - oficial.get("FLAVIO BOLSONARO", 0)}

    # A4
    x = d[tem_bu & d.rdv_lula.notna()]
    dif = x[(x.bu_lula != x.rdv_lula) | (x.bu_flavio != x.rdv_flavio) | (x.bu_branco != x.rdv_branco) | (x.bu_nulo != x.rdv_nulo)]
    out["A4_rdv_contra_boletim"] = {"secoes_comparadas": int(len(x)), "secoes_com_diferenca": int(len(dif)),
                                    "votos_lula_diferenca": int((dif.bu_lula - dif.rdv_lula).sum()),
                                    "votos_flavio_diferenca": int((dif.bu_flavio - dif.rdv_flavio).sum()),
                                    "sinal": bool(len(dif) > 0)}

    # A5
    y = d[tem_bu & d.log_votos.notna()]
    dl = y[y.log_votos != y.comparecimento]
    out["A5_log_contra_boletim"] = {"secoes_comparadas": int(len(y)), "secoes_com_diferenca": int(len(dl)),
                                    "pct": round(len(dl) / len(y) * 100, 3),
                                    "log_a_mais": int((dl.log_votos > dl.comparecimento).sum()),
                                    "log_a_menos": int((dl.log_votos < dl.comparecimento).sum()),
                                    "com_contingencia": int(dl.log_contingencia.sum()),
                                    "sinal": bool(len(dl) / len(y) > 0.005)}

    # A6
    d["validos"] = d.bu_lula + d.bu_flavio
    d["lula_pct"] = d.bu_lula / d.validos * 100
    d["venceu"] = (d.bu_lula > d.bu_flavio).map({True: "lula", False: "flavio"})
    dep = d.log_votos_depois_17h.fillna(0)
    out["A6_votos_depois_das_17h"] = {
        "votos_depois_17h": int(dep.sum()), "votos_depois_19h": int(d.log_votos_depois_19h.fillna(0).sum()),
        "secoes_com_voto_depois_17h": int((dep > 0).sum()),
        "pct_dos_votos": round(dep.sum() / d.log_votos.sum() * 100, 3),
        "teto_contra_margem_pct": round(dep.sum() / MARGEM * 100, 2),
        "secoes_com_mais_de_30pct_depois_17h": int((dep / d.log_votos > 0.30).sum()),
        "por_vencedor_da_secao": {k: {"secoes": int(len(g)), "votos_depois_17h": int(g.log_votos_depois_17h.fillna(0).sum()),
                                      "media_por_secao": round(g.log_votos_depois_17h.fillna(0).mean(), 2)} for k, g in d.groupby("venceu")},
        "por_uf_top": d.groupby("uf").log_votos_depois_17h.sum().sort_values(ascending=False).head(8).astype(int).to_dict(),
        "bahia_3_municipios": {nome: {"secoes": int((m := d[(d.uf == "ba") & (d.municipio == cod)]).shape[0]),
                                      "votos_depois_17h": int(m.log_votos_depois_17h.fillna(0).sum()),
                                      "votos_depois_19h": int(m.log_votos_depois_19h.fillna(0).sum()),
                                      "lula_pct": round(m.bu_lula.sum() / (m.bu_lula.sum() + m.bu_flavio.sum()) * 100, 2)}
                               for cod, nome in BA3.items()},
    }
    out["A6_votos_depois_das_17h"]["sinal"] = bool(dep.sum() > 0.10 * MARGEM or out["A6_votos_depois_das_17h"]["secoes_com_mais_de_30pct_depois_17h"] > 0)

    # A7
    def a7(g):
        v = g.log_votos.sum()
        return {"secoes": int(len(g)), "pct_votos_em_rajada": round(g.log_votos_em_rajada.sum() / v * 100, 3),
                "pct_manuais": round((g.log_manual_mesario.sum() + g.log_manual_sem_digital.sum()) / v * 100, 3),
                "manuais_ultima_hora": int(g.log_manuais_ultima_hora.sum()), "manuais_primeira_hora": int(g.log_manuais_primeira_hora.sum()),
                "razao_ultima_sobre_primeira": round(g.log_manuais_ultima_hora.sum() / max(1, g.log_manuais_primeira_hora.sum()), 3)}
    a7r = {k: a7(g) for k, g in d[d.log_votos.notna()].groupby("venceu")}
    a7r["todas"] = a7(d[d.log_votos.notna()])
    a7r["sinal"] = bool(a7r["lula"]["razao_ultima_sobre_primeira"] > 2 * a7r["flavio"]["razao_ultima_sobre_primeira"]
                        or a7r["lula"]["pct_votos_em_rajada"] > 2 * a7r["flavio"]["pct_votos_em_rajada"])
    out["A7_rajadas_e_liberacao_sem_digital"] = a7r

    # A8 parte 1
    d["rec"] = pd.to_datetime(d.recebido, errors="coerce")
    pausa = d[(d.rec >= "2026-10-25 17:07:01") & (d.rec < "2026-10-25 19:01:56")]
    cauda_corte = d.rec.quantile(0.98)
    cauda = d[d.rec >= cauda_corte]
    def lpct(g):
        return round(g.bu_lula.sum() / (g.bu_lula.sum() + g.bu_flavio.sum()) * 100, 3) if len(g) else None
    out["A8_pausa_e_cauda_parte1"] = {"recebidos_na_pausa": int(len(pausa)), "lula_pct_na_pausa": lpct(pausa),
                                      "cauda_2pct_a_partir_de": str(cauda_corte), "secoes_na_cauda": int(len(cauda)), "lula_pct_na_cauda": lpct(cauda),
                                      "lula_pct_geral": lpct(d), "ultimo_recebido": str(d.rec.max()),
                                      "recebidos_depois_22h22": int((d.rec > "2026-10-25 22:22:01").sum()),
                                      "uf_na_cauda": cauda.uf.value_counts().head(8).to_dict()}

    # A9 parte 1
    cont = d[d.log_contingencia == 1]
    out["A9_contingencia_parte1"] = {"secoes": int(len(cont)), "lula_pct": lpct(cont), "lula_pct_geral": lpct(d),
                                     "por_vencedor": cont.venceu.value_counts().to_dict()}

    # A10 parte 1
    v = d[d.validos >= 50]
    out["A10_unanimidades_parte1"] = {"secoes_com_50_ou_mais_validos": int(len(v)),
                                      "lula_acima_95": int((v.lula_pct > 95).sum()), "flavio_acima_95": int((v.lula_pct < 5).sum()),
                                      "lula_zero": int((v.bu_lula == 0).sum()), "flavio_zero": int((v.bu_flavio == 0).sum())}

    marc = pd.concat([dif.assign(motivo="A4 rdv diferente do boletim"), dl.assign(motivo="A5 log diferente do boletim"),
                      d[dep / d.log_votos > 0.30].assign(motivo="A6 mais de 30% dos votos depois das 17h")])
    cols = ["motivo", "uf", "municipio", "zona", "secao", "comparecimento", "log_votos", "bu_lula", "bu_flavio", "rdv_lula", "rdv_flavio",
            "log_votos_depois_17h", "log_contingencia", "recebido"]
    marc[cols].to_csv(R / "resultados/rodada2_secoes_marcadas.csv", index=False)
    (R / "resultados/rodada2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
