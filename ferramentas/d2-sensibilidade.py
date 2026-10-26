"""D2, sensibilidade: o mesmo modelo de transferência com os dados agregados por município (em vez de seção), para comparar
com o projeto do vídeo 19, que estima por município. Saída: resultados/d2_sensibilidade.json"""
import importlib.util, json
from pathlib import Path
import numpy as np, pandas as pd
R = Path(__file__).resolve().parents[1]
s = importlib.util.spec_from_file_location("d2", R / "ferramentas/rodada-3-d2.py"); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
K = m.K
t1 = pd.read_parquet(R / "dados/derivados/t1_secoes.parquet"); t2 = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
for c in ["aptos", "comparecimento", "lula", "flavio", "cury", "renan", "caiado", "zema", "demais", "branco", "nulo"]:
    t1[c] = pd.to_numeric(t1[c], errors="coerce")
    if c not in ("aptos", "comparecimento"):
        t1.loc[t1.aptos.notna(), c] = t1.loc[t1.aptos.notna(), c].fillna(0)
for c in ["aptos", "comparecimento", "bu_lula", "bu_flavio", "bu_branco", "bu_nulo"]:
    t2[c] = pd.to_numeric(t2[c], errors="coerce")
d = t1.merge(t2[K + ["aptos", "comparecimento", "bu_lula", "bu_flavio", "bu_branco", "bu_nulo"]], on=K, suffixes=("", "_2"))
d = d.dropna(subset=["aptos", "aptos_2", "bu_lula"]); d = d[d.uf != "zz"]
d["outros"] = d.cury + d.renan + d.caiado + d.zema + d.demais
d["bn_1t"] = d.branco + d.nulo; d["abst_1t"] = d.aptos - d.comparecimento
d["bn_2t"] = d.bu_branco + d.bu_nulo; d["abst_2t"] = d.aptos_2 - d.comparecimento_2
ent = ["lula", "flavio", "outros", "bn_1t", "abst_1t"]; sai = ["bu_lula", "bu_flavio", "bn_2t", "abst_2t"]
out = {}
for nivel, chave in (("secao", K), ("municipio", ["uf", "municipio"])):
    g = d.groupby(chave, as_index=False)[ent + sai + ["aptos"]].sum() if nivel == "municipio" else d
    tot = np.zeros((len(ent), len(sai)))
    for uf, gu in g.groupby("uf"):
        gu = gu[gu.aptos > 0]
        if len(gu) < 15:
            continue
        X = gu[ent].to_numpy(float) / gu.aptos.to_numpy(float)[:, None]
        Y = gu[sai].to_numpy(float); Y = Y / Y.sum(1, keepdims=True)
        B = m.estimar(X, Y, gu.aptos.to_numpy(float))
        tot += B * gu[ent].sum().to_numpy(float)[:, None]
    r = {e: {s_: int(tot[i, j]) for j, s_ in enumerate(sai)} for i, e in enumerate(ent)}
    o = r["outros"]
    r["outros_entre_quem_votou_lula_pct"] = round(o["bu_lula"] / (o["bu_lula"] + o["bu_flavio"] + o["bn_2t"]) * 100, 1)
    r["outros_entre_quem_votou_flavio_pct"] = round(o["bu_flavio"] / (o["bu_lula"] + o["bu_flavio"] + o["bn_2t"]) * 100, 1)
    r["lula_vindo_dos_outros"] = o["bu_lula"]; r["lula_vindo_de_bn_e_abstencao"] = r["bn_1t"]["bu_lula"] + r["abst_1t"]["bu_lula"]
    out[nivel] = r
(R / "resultados/d2_sensibilidade.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
for k, v in out.items():
    print(k, {kk: v[kk] for kk in ["outros_entre_quem_votou_lula_pct", "outros_entre_quem_votou_flavio_pct", "lula_vindo_dos_outros", "lula_vindo_de_bn_e_abstencao"]})
