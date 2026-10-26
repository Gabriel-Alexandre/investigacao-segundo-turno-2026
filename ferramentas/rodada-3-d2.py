"""D2: de onde vieram os votos. Transferência do 1º para o 2º turno estimada seção a seção (inferência ecológica).

Modelo: em cada UF, a composição do 2º turno de cada seção (Lula, Flávio, branco e nulo, abstenção, como fração do
eleitorado) é a composição do 1º turno vezes uma matriz de transferência B (cada linha soma 1, valores entre 0 e 1),
estimada por mínimos quadrados ponderados pelo eleitorado da seção. Intervalo: 40 reamostragens das seções.
Validação obrigatória (pré-registro D2): o mesmo modelo no 1º -> 2º turno de 2022, comparado com o Datafolha de 5 a 7/10/2022
(eleitores do Ciro: 42% Bolsonaro, 31% Lula; da Tebet: 31% Lula, 29% Bolsonaro; Poder360, íntegra da pesquisa).

Saída: resultados/d2_transferencia.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

R = Path(__file__).resolve().parents[1]
K = ["uf", "municipio", "zona", "secao"]
RNG = np.random.default_rng(20261026)
NBOOT = 40


def estimar(X: np.ndarray, Y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """X: frações do 1º turno (n x p), Y: frações do 2º (n x q), w: pesos. Devolve B (p x q), linhas somando 1."""
    p, q = X.shape[1], Y.shape[1]
    w = w / w.sum()  # escala: sem isso o otimizador para cedo (a soma dos pesos passa de 10^7)
    Xw = X * w[:, None]
    G = Xw.T @ X
    H = Xw.T @ Y

    def f(b):
        B = b.reshape(p, q)
        return float(np.trace(B.T @ G @ B) - 2 * np.trace(B.T @ H))

    def g(b):
        B = b.reshape(p, q)
        return (2 * (G @ B - H)).ravel()

    cons = [{"type": "eq", "fun": (lambda b, i=i: b.reshape(p, q)[i].sum() - 1), "jac": (lambda b, i=i: _row(i, p, q))} for i in range(p)]
    b0 = np.full(p * q, 1.0 / q)
    r = minimize(f, b0, jac=g, bounds=[(0, 1)] * (p * q), constraints=cons, method="SLSQP", options={"maxiter": 2000, "ftol": 1e-15})
    if not r.success:
        raise RuntimeError(f"otimizador nao convergiu: {r.message}")
    return r.x.reshape(p, q)


def _row(i, p, q):
    v = np.zeros(p * q)
    v[i * q:(i + 1) * q] = 1
    return v


def fluxos(df: pd.DataFrame, entrada: list[str], saida: list[str], aptos: str) -> dict:
    """Estimativa e intervalo de 90% dos votos que foram de cada origem para cada destino, somando as UFs."""
    total = np.zeros((len(entrada), len(saida)))
    boots = np.zeros((NBOOT, len(entrada), len(saida)))
    por_uf = {}
    for uf, g in df.groupby("uf"):
        g = g[g[aptos] > 0]
        if len(g) < 30:
            continue
        X = g[entrada].to_numpy(float) / g[aptos].to_numpy(float)[:, None]
        Y = g[saida].to_numpy(float)
        Y = Y / Y.sum(1, keepdims=True)
        w = g[aptos].to_numpy(float)
        tot_in = g[entrada].sum().to_numpy(float)
        B = estimar(X, Y, w)
        por_uf[uf] = np.round(B, 4).tolist()
        total += B * tot_in[:, None]
        for k in range(NBOOT):
            idx = RNG.integers(0, len(g), len(g))
            cont = np.bincount(idx, minlength=len(g)).astype(float)
            Bk = estimar(X, Y, w * cont)
            boots[k] += Bk * tot_in[:, None]
    lo, hi = np.percentile(boots, 5, axis=0), np.percentile(boots, 95, axis=0)
    res = {}
    for i, e in enumerate(entrada):
        res[e] = {s: {"votos": int(total[i, j]), "de": int(lo[i, j]), "ate": int(hi[i, j])} for j, s in enumerate(saida)}
    return {"fluxos": res, "matriz_por_uf": por_uf}


def main():
    t1 = pd.read_parquet(R / "dados/derivados/t1_secoes.parquet")
    t2 = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
    for t, cols in ((t1, ["aptos", "comparecimento", "lula", "flavio", "cury", "renan", "caiado", "zema", "demais", "branco", "nulo"]),
                    (t2, ["aptos", "comparecimento", "bu_lula", "bu_flavio", "bu_branco", "bu_nulo"])):
        for c in cols:
            t[c] = pd.to_numeric(t[c], errors="coerce")
    for c in ["lula", "flavio", "cury", "renan", "caiado", "zema", "demais", "branco", "nulo"]:
        t1.loc[t1.aptos.notna(), c] = t1.loc[t1.aptos.notna(), c].fillna(0)  # sem voto na seção = zero
    d = t1.merge(t2[K + ["aptos", "comparecimento", "bu_lula", "bu_flavio", "bu_branco", "bu_nulo"]], on=K, suffixes=("", "_2"))
    d = d.dropna(subset=["aptos", "comparecimento", "aptos_2", "comparecimento_2", "bu_lula", "bu_flavio"])
    d = d[d.uf != "zz"]
    d["demais_1t"] = d.zema + d.demais
    d["bn_1t"] = d.branco + d.nulo
    d["abst_1t"] = d.aptos - d.comparecimento
    d["bn_2t"] = d.bu_branco + d.bu_nulo
    d["abst_2t"] = d.aptos_2 - d.comparecimento_2
    ent = ["lula", "flavio", "cury", "renan", "caiado", "demais_1t", "bn_1t", "abst_1t"]
    sai = ["bu_lula", "bu_flavio", "bn_2t", "abst_2t"]
    r26 = fluxos(d, ent, sai, "aptos")

    a = pd.read_parquet(R / "dados/derivados/s2022_t1.parquet")
    b = pd.read_parquet(R / "dados/derivados/s2022_t2.parquet")
    for t in (a, b):
        for c in ["lula", "bolsonaro", "tebet", "ciro", "outros", "branco", "nulo"]:
            if c not in t:
                t[c] = 0
    a = a.rename(columns={c: c + "_1" for c in a.columns if c not in K})
    b = b.rename(columns={c: c + "_2" for c in b.columns if c not in K})
    e = a.merge(b, on=K)
    e = e[e.uf.str.lower() != "zz"]
    for c in e.columns:
        if c not in K:
            e[c] = pd.to_numeric(e[c], errors="coerce").fillna(0)
    e["uf"] = e.uf.str.lower()
    e["bn_1"] = e.branco_1 + e.nulo_1
    e["abst_1"] = e.aptos_1 - e.comparecimento_1
    e["bn_2"] = e.branco_2 + e.nulo_2
    e["abst_2"] = e.aptos_2 - e.comparecimento_2
    r22 = fluxos(e, ["lula_1", "bolsonaro_1", "tebet_1", "ciro_1", "outros_1", "bn_1", "abst_1"], ["lula_2", "bolsonaro_2", "bn_2", "abst_2"], "aptos_1")

    def entre_quem_votou(fl, origem, a_, b_, bn):
        x = fl["fluxos"][origem]
        t = x[a_]["votos"] + x[b_]["votos"] + x[bn]["votos"]
        return {"para_lula_pct": round(x[a_]["votos"] / t * 100, 1), "para_o_outro_pct": round(x[b_]["votos"] / t * 100, 1), "branco_nulo_pct": round(x[bn]["votos"] / t * 100, 1)}
    val22 = {"ciro_modelo": entre_quem_votou(r22, "ciro_1", "lula_2", "bolsonaro_2", "bn_2"),
             "tebet_modelo": entre_quem_votou(r22, "tebet_1", "lula_2", "bolsonaro_2", "bn_2"),
             "datafolha_5_7_out_2022": {"ciro": {"lula": 31, "bolsonaro": 42, "branco_nulo": 22, "indecisos": 5},
                                        "tebet": {"lula": 31, "bolsonaro": 29, "branco_nulo": 28, "indecisos": 12}}}
    val22["mesmo_lado_que_o_datafolha"] = bool(val22["ciro_modelo"]["para_o_outro_pct"] > val22["ciro_modelo"]["para_lula_pct"])

    resumo = {}
    for dest, nome in (("bu_lula", "lula"), ("bu_flavio", "flavio")):
        resumo[nome] = {o: r26["fluxos"][o][dest] for o in ent}
    ganhoL = {o: resumo["lula"][o]["votos"] for o in ent if o != "lula"}
    out = {"modelo": "transferência por UF, mínimos quadrados com restrições, 40 reamostragens, intervalo de 90%",
           "secoes": int(len(d)), "2026_votos_do_2t_por_origem": resumo,
           "2026_quem_votou_no_lula_no_1t_foi_para": r26["fluxos"]["lula"], "2026_quem_votou_no_flavio_no_1t_foi_para": r26["fluxos"]["flavio"],
           "2026_eleitores_de_cada_candidato_entre_quem_votou_no_2t": {o: entre_quem_votou(r26, o, "bu_lula", "bu_flavio", "bn_2t") for o in ent if o not in ("abst_1t",)},
           "validacao_2022": val22, "matriz_por_uf_2026": r26["matriz_por_uf"]}
    (R / "resultados/d2_transferencia.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "matriz_por_uf_2026"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
