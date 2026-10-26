"""Rodada 3: o 1º contra o 2º turno seção a seção (pré-registro §4 e §5), com a régua de 2022.

Acusação: A1 (votos sem origem), A2 (votos que somem), A3 (enchimento de urna e impressão digital), A8 completo (pausa e
cauda contra o previsto pelo 1º turno da mesma seção), A9 completo (urna trocada), A10 completo (unanimidades e zerados),
A11 (resíduos agrupados por município).
Defesa: D1 (saldo por região e UF), D3 (abstenção), D4 (cidades que viraram). D2 (transferência) fica em rodada-3-d2.py.

Saída: resultados/rodada3.json, resultados/d4_municipios.csv, resultados/a11_municipios.csv, resultados/a3_secoes.csv
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1]
K = ["uf", "municipio", "zona", "secao"]
MARGEM = 64256232 - 59826041
REGIAO = {"ac": "Norte", "am": "Norte", "ap": "Norte", "pa": "Norte", "ro": "Norte", "rr": "Norte", "to": "Norte",
          "al": "Nordeste", "ba": "Nordeste", "ce": "Nordeste", "ma": "Nordeste", "pb": "Nordeste", "pe": "Nordeste", "pi": "Nordeste", "rn": "Nordeste", "se": "Nordeste",
          "df": "Centro-Oeste", "go": "Centro-Oeste", "ms": "Centro-Oeste", "mt": "Centro-Oeste",
          "es": "Sudeste", "mg": "Sudeste", "rj": "Sudeste", "sp": "Sudeste", "pr": "Sul", "rs": "Sul", "sc": "Sul", "zz": "Exterior"}


def num(df, cols):
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def carregar():
    t1 = num(pd.read_parquet(R / "dados/derivados/t1_secoes.parquet"),
             ["aptos", "comparecimento", "lula", "flavio", "cury", "renan", "caiado", "zema", "demais", "branco", "nulo"])
    tem = t1.aptos.notna()  # seção com boletim: candidato sem voto na seção vem vazio do leitor e vale zero
    for c in ["lula", "flavio", "cury", "renan", "caiado", "zema", "demais", "branco", "nulo"]:
        t1.loc[tem, c] = t1.loc[tem, c].fillna(0)
    t2 = num(pd.read_parquet(R / "dados/derivados/t2_secoes.parquet"),
             ["aptos", "comparecimento", "bu_lula", "bu_flavio", "bu_branco", "bu_nulo", "log_contingencia"])
    t1 = t1.rename(columns={c: c + "1" for c in t1.columns if c not in K})
    t2 = t2.rename(columns={"bu_lula": "lula2", "bu_flavio": "flavio2", "aptos": "aptos2", "comparecimento": "comparecimento2",
                            "recebido": "recebido2"})
    t2["bn2"] = t2.bu_branco + t2.bu_nulo
    d = t1.merge(t2, on=K, how="outer", indicator=True)
    return d


def r2022():
    a = num(pd.read_parquet(R / "dados/derivados/s2022_t1.parquet"), ["aptos", "comparecimento"])
    b = num(pd.read_parquet(R / "dados/derivados/s2022_t2.parquet"), ["aptos", "comparecimento"])
    for t in (a, b):
        for c in ["lula", "bolsonaro", "tebet", "ciro", "outros", "branco", "nulo"]:
            if c not in t:
                t[c] = 0
    a = a.rename(columns={c: c + "1" for c in a.columns if c not in K + ["turno"]})
    b = b.rename(columns={c: c + "2" for c in b.columns if c not in K + ["turno"]})
    return a.merge(b, on=K, how="inner")


def excesso(dg, dp, outros1, abst1, abst2, bn1, bn2):
    reserva = outros1 + (abst1 - abst2).clip(lower=0) + (bn1 - bn2).clip(lower=0)
    return (dg - reserva).clip(lower=0), (dp - reserva).clip(lower=0)


def main():
    d = carregar()
    out = {"casamento": d["_merge"].value_counts().to_dict()}
    d = d[d["_merge"] == "both"].copy()
    d = d[(d.aptos1 > 0) & d.lula2.notna() & d.lula1.notna()]
    d["outros1"] = d.cury1 + d.renan1 + d.caiado1 + d.zema1 + d.demais1
    d["bn1"] = d.branco1 + d.nulo1
    d["abst1"] = d.aptos1 - d.comparecimento1
    d["abst2"] = d.aptos2 - d.comparecimento2
    d["dL"] = d.lula2 - d.lula1
    d["dF"] = d.flavio2 - d.flavio1
    d["val2"] = d.lula2 + d.flavio2
    d["lp2"] = d.lula2 / d.val2 * 100
    d["val1"] = d.lula1 + d.flavio1 + d.outros1
    d["lp1"] = d.lula1 / d.val1 * 100
    d["fp1"] = d.flavio1 / d.val1 * 100
    d["op1"] = d.outros1 / d.val1 * 100
    d["regiao"] = d.uf.map(REGIAO)
    out["secoes_comparadas"] = int(len(d))
    out["aptos_iguais_nos_dois_turnos_pct"] = round((d.aptos1 == d.aptos2).mean() * 100, 3)

    # ---------- D1 ----------
    soma = lambda g: {"lula_ganhou": int(g.dL.sum()), "flavio_ganhou": int(g.dF.sum()), "outros_1t": int(g.outros1.sum()),
                      "abstencao_caiu": int((g.abst1 - g.abst2).sum()), "branco_nulo_caiu": int((g.bn1 - g.bn2).sum())}
    out["D1_saldo"] = {"brasil": soma(d), "regiao": {k: soma(g) for k, g in d.groupby("regiao")}}

    # ---------- A1 ----------
    eL, eF = excesso(d.dL, d.dF, d.outros1, d.abst1, d.abst2, d.bn1, d.bn2)
    d["excL"], d["excF"] = eL, eF
    s = d.sort_values("excL", ascending=False)
    top1 = s.head(max(1, len(s) // 100)).excL.sum() / max(1, s.excL.sum())
    a22 = r2022()
    a22["outros1"] = a22.tebet1 + a22.ciro1 + a22.outros1
    a22["abst1"] = a22.aptos1 - a22.comparecimento1
    a22["abst2"] = a22.aptos2 - a22.comparecimento2
    a22["bn1"] = a22.branco1 + a22.nulo1
    a22["bn2"] = a22.branco2 + a22.nulo2
    b_exc, l_exc = excesso(a22.bolsonaro2 - a22.bolsonaro1, a22.lula2 - a22.lula1, a22.outros1, a22.abst1, a22.abst2, a22.bn1, a22.bn2)
    razao26 = float(eL.sum() / max(1, eF.sum()))
    razao22 = float(b_exc.sum() / max(1, l_exc.sum()))
    out["A1_votos_sem_origem"] = {
        "excesso_lula": int(eL.sum()), "excesso_flavio": int(eF.sum()), "razao_2026_lula_sobre_flavio": round(razao26, 3),
        "secoes_com_excesso_lula": int((eL > 0).sum()), "secoes_com_excesso_flavio": int((eF > 0).sum()),
        "parte_do_excesso_lula_no_1pct_das_secoes": round(float(top1), 4),
        "regua_2022": {"secoes": int(len(a22)), "excesso_bolsonaro_que_cresceu_mais": int(b_exc.sum()), "excesso_lula": int(l_exc.sum()),
                       "razao_quem_cresceu_mais": round(razao22, 3)},
        "excesso_lula_contra_margem_pct": round(float(eL.sum()) / MARGEM * 100, 2),
    }
    out["A1_votos_sem_origem"]["sinal"] = bool((razao26 > 2 and razao26 > 2 * razao22) or top1 > 0.5)

    # ---------- A2 ----------
    sobe = d.comparecimento2 > d.comparecimento1
    pF = float(((d.dF < 0) & sobe).mean())
    pL = float(((d.dL < 0) & sobe).mean())
    sobe22 = a22.comparecimento2 > a22.comparecimento1
    pL22 = float((((a22.lula2 - a22.lula1) < 0) & sobe22).mean())
    pB22 = float((((a22.bolsonaro2 - a22.bolsonaro1) < 0) & sobe22).mean())
    out["A2_votos_que_somem"] = {"pct_secoes_flavio_caiu_com_comparecimento_subindo": round(pF * 100, 3),
                                 "pct_secoes_lula_caiu_com_comparecimento_subindo": round(pL * 100, 3),
                                 "regua_2022_lula_que_cresceu_menos": round(pL22 * 100, 3), "regua_2022_bolsonaro": round(pB22 * 100, 3),
                                 "votos_perdidos_pelo_flavio_nessas_secoes": int(-d.loc[(d.dF < 0) & sobe, "dF"].sum()),
                                 "sinal": bool(pF > 2 * pL and pF > 2 * pL22)}

    # ---------- A3 ----------
    d["c1"] = d.comparecimento1 / d.aptos1 * 100
    d["c2"] = d.comparecimento2 / d.aptos2 * 100
    d["dc"] = d.c2 - d.c1
    g = d.groupby(["uf", "municipio"]).dc
    d["n_mun"] = g.transform("size")
    d["p999"] = g.transform(lambda x: x.quantile(0.999))
    marc = d[(d.n_mun >= 20) & (d.dc > d.p999)]
    mL = marc[marc.lp2 > 80]
    mF = marc[marc.lp2 < 20]
    def canto(comp, share):
        return float(((comp >= 95) & (share >= 95)).mean() * 100)
    w2 = d[["lula2", "flavio2"]].max(axis=1) / d.val2 * 100
    w1 = d[["lula1", "flavio1"]].max(axis=1) / d.val1 * 100
    a22["val2"] = a22.lula2 + a22.bolsonaro2
    w22 = a22[["lula2", "bolsonaro2"]].max(axis=1) / a22.val2 * 100
    c22 = a22.comparecimento2 / a22.aptos2 * 100
    out["A3_enchimento"] = {"secoes_acima_do_p999_do_municipio": int(len(marc)), "dessas_lula_acima_80": int(len(mL)), "dessas_flavio_acima_80": int(len(mF)),
                            "canto_95_95_pct_2t_2026": round(canto(d.c2, w2), 4), "canto_95_95_pct_1t_2026": round(canto(d.c1, w1), 4),
                            "canto_95_95_pct_2t_2022": round(canto(c22, w22), 4),
                            "correlacao_comparecimento_lula_2t_2026": round(float(d[["c2", "lp2"]].corr().iloc[0, 1]), 4),
                            "correlacao_comparecimento_lula_2t_2022": round(float(pd.concat([c22, a22.lula2 / a22.val2 * 100], axis=1).corr().iloc[0, 1]), 4)}
    base_l = float((d.lp2 > 80).mean())
    base_f = float((d.lp2 < 20).mean())
    out["A3_enchimento"]["esperado_pela_proporcao_do_pais"] = {"secoes_lula_acima_80_no_pais_pct": round(base_l * 100, 2), "secoes_flavio_acima_80_no_pais_pct": round(base_f * 100, 2),
                                                              "esperado_lula": round(base_l * len(marc), 1), "esperado_flavio": round(base_f * len(marc), 1),
                                                              "razao_observada_sobre_esperada_lula": round(len(mL) / max(1e-9, base_l * len(marc)), 2),
                                                              "razao_observada_sobre_esperada_flavio": round(len(mF) / max(1e-9, base_f * len(marc)), 2)}
    out["A3_enchimento"]["votos_validos_nas_secoes_marcadas_lula"] = int(mL.val2.sum())
    # controle do mesmo lugar: a regra marca quase uma seção por município; o esperado é a proporção do próprio município
    gm = d.groupby(["uf", "municipio"])
    d["pL_mun"] = gm.lp2.transform(lambda x: (x > 80).mean())
    d["pF_mun"] = gm.lp2.transform(lambda x: (x < 20).mean())
    mm_ = d.loc[marc.index]
    out["A3_enchimento"]["esperado_pelo_proprio_municipio"] = {
        "esperado_lula": round(float(mm_.pL_mun.sum()), 1), "esperado_flavio": round(float(mm_.pF_mun.sum()), 1),
        "razao_observada_sobre_esperada_lula": round(len(mL) / max(1e-9, float(mm_.pL_mun.sum())), 3),
        "razao_observada_sobre_esperada_flavio": round(len(mF) / max(1e-9, float(mm_.pF_mun.sum())), 3),
        "salto_medio_de_comparecimento_pontos": round(float(mL.dc.mean()), 2)}
    # o que separa: se o comparecimento a mais fosse de eleitor fantasma, a liberação sem digital subiria nessas seções
    t2l = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")[K + ["log_votos", "log_manual_mesario", "log_manual_sem_digital"]]
    for c in ["log_votos", "log_manual_mesario", "log_manual_sem_digital"]:
        t2l[c] = pd.to_numeric(t2l[c], errors="coerce")
    t2l["pman"] = (t2l.log_manual_mesario + t2l.log_manual_sem_digital) / t2l.log_votos * 100
    dd = d[K].join(t2l.set_index(K)[["pman"]], on=K)
    d["pman"] = dd["pman"].values
    d["pman_mun"] = d.groupby(["uf", "municipio"]).pman.transform("mean")
    mL2 = d.loc[mL.index]
    out["A3_enchimento"]["liberacao_sem_digital_nas_secoes_marcadas"] = {
        "pct_nas_857": round(float(mL2.pman.mean()), 2), "pct_media_dos_mesmos_municipios": round(float(mL2.pman_mun.mean()), 2),
        "diferenca_pontos": round(float((mL2.pman - mL2.pman_mun).mean()), 2)}
    # régua de 2022: o mesmo teste, com o mesmo controle, do 1º para o 2º turno de 2022 (lado do Lula e do Bolsonaro)
    e = a22[(a22.aptos1 > 0) & (a22.aptos2 > 0)].copy()
    e["c1"] = e.comparecimento1 / e.aptos1 * 100
    e["c2"] = e.comparecimento2 / e.aptos2 * 100
    e["dc"] = e.c2 - e.c1
    e["lp2"] = e.lula2 / (e.lula2 + e.bolsonaro2) * 100
    ge = e.groupby(["uf", "municipio"])
    e["n_mun"] = ge.dc.transform("size")
    e["p999"] = ge.dc.transform(lambda x: x.quantile(0.999))
    e["pL_mun"] = ge.lp2.transform(lambda x: (x > 80).mean())
    e["pB_mun"] = ge.lp2.transform(lambda x: (x < 20).mean())
    me = e[(e.n_mun >= 20) & (e.dc > e.p999)]
    out["A3_enchimento"]["regua_2022_mesmo_controle"] = {
        "secoes_marcadas": int(len(me)), "lula_acima_80": int((me.lp2 > 80).sum()), "esperado_lula": round(float(me.pL_mun.sum()), 1),
        "bolsonaro_acima_80": int((me.lp2 < 20).sum()), "esperado_bolsonaro": round(float(me.pB_mun.sum()), 1),
        "razao_lula": round(int((me.lp2 > 80).sum()) / max(1e-9, float(me.pL_mun.sum())), 3),
        "razao_bolsonaro": round(int((me.lp2 < 20).sum()) / max(1e-9, float(me.pB_mun.sum())), 3)}
    out["A3_enchimento"]["sinal"] = bool(len(mL) > 2 * max(1, len(mF)) or out["A3_enchimento"]["canto_95_95_pct_2t_2026"] >
                                         3 * max(out["A3_enchimento"]["canto_95_95_pct_1t_2026"], out["A3_enchimento"]["canto_95_95_pct_2t_2022"], 1e-9))
    marc.assign(lula_pct_2t=marc.lp2)[K + ["c1", "c2", "dc", "lula_pct_2t", "lula1", "flavio1", "lula2", "flavio2"]].to_csv(R / "resultados/a3_secoes.csv", index=False)

    # ---------- modelo do previsto (A8, A9, A11) ----------
    X = np.column_stack([np.ones(len(d)), d.lp1, d.fp1, d.op1, d.dc.fillna(0)])
    y = d.lp2.values
    ok = np.isfinite(X).all(1) & np.isfinite(y)
    beta, *_ = np.linalg.lstsq(X[ok], y[ok], rcond=None)
    d["prev"] = X @ beta
    d["res"] = d.lp2 - d.prev
    sd = float(d.res[ok].std())
    out["modelo_previsto"] = {"coeficientes": [round(float(b), 4) for b in beta], "desvio_dos_residuos": round(sd, 3),
                              "r2": round(1 - float(np.var(d.res[ok]) / np.var(y[ok])), 4)}

    def grupo(m):
        r = d.loc[m, "res"].dropna()
        return {"secoes": int(len(r)), "residuo_medio_pontos": round(float(r.mean()), 3), "erro_padrao": round(float(r.std() / np.sqrt(max(1, len(r)))), 3),
                "lula_pct_2t": round(float(d.loc[m, "lula2"].sum() / d.loc[m, "val2"].sum() * 100), 3),
                "lula_pct_1t_mesmas_secoes": round(float(d.loc[m, "lula1"].sum() / d.loc[m, "val1"].sum() * 100), 3)}

    d["rec2"] = pd.to_datetime(d.recebido2, errors="coerce")
    pausa = (d.rec2 >= "2026-10-25 17:07:01") & (d.rec2 < "2026-10-25 19:01:56")
    corte = d.rec2.quantile(0.98)
    cauda = d.rec2 >= corte
    a8 = {"pausa": grupo(pausa), "cauda_2pct": grupo(cauda), "resto": grupo(~pausa & ~cauda), "depois_22h22": grupo(d.rec2 > "2026-10-25 22:22:01")}
    a8["sinal"] = bool(any(abs(a8[k]["residuo_medio_pontos"]) > 1 and abs(a8[k]["residuo_medio_pontos"]) > 3 * a8[k]["erro_padrao"] for k in ("pausa", "cauda_2pct")))
    out["A8_pausa_e_cauda"] = a8
    a9 = {"contingencia": grupo(d.log_contingencia == 1), "sem_contingencia": grupo(d.log_contingencia != 1)}
    a9["sinal"] = bool(abs(a9["contingencia"]["residuo_medio_pontos"]) > 2)
    out["A9_urna_trocada"] = a9

    # ---------- A10 ----------
    v1 = d[d.val1 >= 50]
    v2 = d[d.val2 >= 50]
    a22v = a22[a22.val2 >= 50]
    out["A10_unanimidades"] = {
        "lula_acima_95_2t_2026": int((v2.lp2 > 95).sum()), "flavio_acima_95_2t_2026": int((v2.lp2 < 5).sum()),
        "lula_acima_95_1t_2026_mesmas_regras": int((v1.lula1 / (v1.lula1 + v1.flavio1) * 100 > 95).sum()),
        "lula_acima_95_2t_2022": int((a22v.lula2 / a22v.val2 * 100 > 95).sum()), "bolsonaro_acima_95_2t_2022": int((a22v.lula2 / a22v.val2 * 100 < 5).sum()),
        "das_1686_quantas_ja_eram_acima_de_90_no_1t": int(((v2.lp2 > 95) & (v2.lula1 / (v2.lula1 + v2.flavio1) * 100 > 90)).sum()),
        "flavio_tinha_voto_no_1t_e_zerou": int(((d.flavio1 > 0) & (d.flavio2 == 0)).sum()),
        "lula_tinha_voto_no_1t_e_zerou": int(((d.lula1 > 0) & (d.lula2 == 0)).sum()),
    }
    a10 = out["A10_unanimidades"]
    # pré-registro A10: mais de 2 vezes de um lado que do outro, OU acima do 1º turno e de 2022
    a10["condicao_lado_contra_lado"] = bool(a10["lula_acima_95_2t_2026"] > 2 * max(1, a10["flavio_acima_95_2t_2026"]))
    a10["condicao_acima_do_1t_e_de_2022"] = bool(a10["lula_acima_95_2t_2026"] > a10["lula_acima_95_1t_2026_mesmas_regras"] and a10["lula_acima_95_2t_2026"] > a10["lula_acima_95_2t_2022"])
    a10["sinal"] = bool(a10["condicao_lado_contra_lado"] or a10["condicao_acima_do_1t_e_de_2022"])

    # ---------- A11 ----------
    m = d.groupby(["uf", "municipio"]).agg(secoes=("res", "size"), residuo=("res", "mean"), sd=("res", "std"),
                                            lula1=("lula1", "sum"), flavio1=("flavio1", "sum"), lula2=("lula2", "sum"), flavio2=("flavio2", "sum"),
                                            val2=("val2", "sum")).reset_index()
    m["z"] = m.residuo / (sd / np.sqrt(m.secoes))
    m["lado"] = np.where(m.z > 3, "lula", np.where(m.z < -3, "flavio", ""))
    m.sort_values("z", ascending=False).to_csv(R / "resultados/a11_municipios.csv", index=False)
    out["A11_residuos_por_municipio"] = {"municipios": int(len(m)), "acima_de_3_ep_a_favor_do_lula": int((m.lado == "lula").sum()),
                                         "acima_de_3_ep_a_favor_do_flavio": int((m.lado == "flavio").sum()),
                                         "votos_validos_nos_municipios_lula": int(m.loc[m.lado == "lula", "val2"].sum()),
                                         "top5_lula": m.sort_values("z", ascending=False).head(5)[["uf", "municipio", "secoes", "residuo", "z"]].round(2).to_dict("records"),
                                         "top5_flavio": m.sort_values("z").head(5)[["uf", "municipio", "secoes", "residuo", "z"]].round(2).to_dict("records")}

    # ---------- D3 ----------
    d["dabst"] = (d.abst2 - d.abst1) / d.aptos1 * 100
    d["dlp"] = d.lp2 - d.lp1
    out["D3_abstencao"] = {"correlacao_queda_da_abstencao_e_ganho_do_lula_pontos": round(float((-d.dabst).corr(d.dlp)), 4),
                           "abstencao_caiu_em_pct_das_secoes": round(float((d.abst2 < d.abst1).mean() * 100), 2),
                           "por_quintil_de_queda": d.assign(q=pd.qcut(-d.dabst, 5, labels=False, duplicates="drop")).groupby("q").apply(
                               lambda g: round(float(g.lula2.sum() / g.val2.sum() * 100 - g.lula1.sum() / (g.lula1.sum() + g.flavio1.sum()) * 100), 3)).to_dict()}

    # ---------- D4 ----------
    mm = d.groupby(["uf", "municipio"]).agg(lula1=("lula1", "sum"), flavio1=("flavio1", "sum"), val1=("val1", "sum"),
                                             lula2=("lula2", "sum"), flavio2=("flavio2", "sum"), val2=("val2", "sum"),
                                             aptos=("aptos2", "sum"), abst1=("abst1", "sum"), abst2=("abst2", "sum"), outros1=("outros1", "sum")).reset_index()
    # empate exato fica como empate (rodada 5: 2 municípios empataram no 1º turno e eram contados como do Flávio)
    mm["venc1"] = np.select([mm.lula1 > mm.flavio1, mm.lula1 < mm.flavio1], ["lula", "flavio"], "empate")
    mm["venc2"] = np.select([mm.lula2 > mm.flavio2, mm.lula2 < mm.flavio2], ["lula", "flavio"], "empate")
    mm["lula_pct_1t"] = mm.lula1 / mm.val1 * 100
    mm["lula_pct_2t"] = mm.lula2 / mm.val2 * 100
    mm["frente_lula_1t_pontos"] = (mm.lula1 - mm.flavio1) / (mm.lula1 + mm.flavio1) * 100
    mm["frente_lula_2t_pontos"] = (mm.lula2 - mm.flavio2) / mm.val2 * 100
    mm["virada_pontos"] = mm.frente_lula_2t_pontos - mm.frente_lula_1t_pontos
    mm["regiao"] = mm.uf.map(REGIAO)
    try:
        nomes = pd.read_csv(R / "dados/derivados/municipios_nomes.csv", dtype=str)
        mm = mm.merge(nomes, on=["uf", "municipio"], how="left")
    except FileNotFoundError:
        pass
    mm.to_csv(R / "resultados/d4_municipios.csv", index=False)
    out["D4_cidades_que_viraram"] = d4_resumo(mm)
    (R / "resultados/rodada3.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    d[K + ["regiao", "lp1", "lp2", "res", "excL", "excF", "dc", "dabst"]].to_parquet(R / "dados/derivados/r3_secoes.parquet", index=False)
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))


def d4_resumo(todos):
    """As cidades que viraram, só no Brasil (o exterior à parte, e o empate exato no 1º turno à parte)."""
    mm = todos[todos.uf != "zz"]
    ex = todos[todos.uf == "zz"]
    f2l = mm[(mm.venc1 == "flavio") & (mm.venc2 == "lula")]
    l2f = mm[(mm.venc1 == "lula") & (mm.venc2 == "flavio")]
    return {"municipios": int(len(mm)), "do_flavio_para_o_lula": int(len(f2l)), "do_lula_para_o_flavio": int(len(l2f)),
            "empatados_no_1t_e_do_lula_no_2t": int(((mm.venc1 == "empate") & (mm.venc2 == "lula")).sum()),
            "empatados_no_1t_e_do_flavio_no_2t": int(((mm.venc1 == "empate") & (mm.venc2 == "flavio")).sum()),
            "exterior_cidades": int(len(ex)), "exterior_do_flavio_para_o_lula": int(((ex.venc1 == "flavio") & (ex.venc2 == "lula")).sum()),
            "exterior_do_lula_para_o_flavio": int(((ex.venc1 == "lula") & (ex.venc2 == "flavio")).sum()),
            "por_regiao_flavio_para_lula": f2l.regiao.value_counts().to_dict(),
            "por_uf_flavio_para_lula": f2l.uf.value_counts().head(10).to_dict(),
            "aptos_nos_que_viraram_para_o_lula": int(f2l.aptos.sum()),
            "maiores_em_eleitores": f2l.sort_values("aptos", ascending=False).head(15)[[c for c in ["uf", "municipio", "nome", "aptos", "frente_lula_1t_pontos", "frente_lula_2t_pontos"] if c in f2l]].round(2).to_dict("records"),
            "frente_do_lula_aumentou_em_pct_dos_municipios": round(float((mm.virada_pontos > 0).mean() * 100), 2),
            "virada_media_pontos": round(float(mm.virada_pontos.mean()), 2)}


if __name__ == "__main__":
    main()
