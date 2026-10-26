"""Rodada 4: o que aconteceu em 2026 é normal comparado com 2002 a 2022? (pedido do autor, as perguntas do vídeo 19 refeitas aqui
com os dados deste projeto, para os dois vídeos se conferirem)

  N1  votos livres: quanto do que estava livre entre os turnos foi para o PT e para o adversário, e quem os eliminados apoiaram
  N2  comparecimento: quanto a abstenção mudou entre os turnos e em quantos municípios o comparecimento subiu
  N3  espalhamento: em quantos municípios a diferença andou para o mesmo lado do país, e em quantos o PT ganhou votos

Fontes: votação por candidato e município do TSE (1994 a 2022, já baixada), detalhe da votação por município do TSE
(comparecimento, 2002 a 2026, baixado aqui), boletins por seção de 2026 deste projeto, e a tabela de apoios de 2º turno
conferida com fonte pelo projeto do vídeo 19 (cópia com sha256 em dados/copias/).

Saída: resultados/rodada4_normalidade.json e resultados/rodada4_por_ano.csv
"""
from __future__ import annotations

import csv, hashlib, io, json, shutil, urllib.request, zipfile
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[1]
BR = R / "dados/brutos/detalhe"
HIST = R / "dados/brutos/historico"
URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_munzona/detalhe_votacao_munzona_{a}.zip"
ANOS = [2002, 2006, 2010, 2014, 2018, 2022]
PT = 13
APOIOS_ORIGEM = R.parent / "pesquisas-e-resultado-segundo-turno-2026" / "dados/agentes/apoios_segundo_turno.csv"


def baixar(a):
    BR.mkdir(parents=True, exist_ok=True)
    d = BR / f"detalhe_votacao_munzona_{a}.zip"
    if not d.exists():
        with urllib.request.urlopen(urllib.request.Request(URL.format(a=a), headers={"User-Agent": "investigacao-segundo-turno-2026"}), timeout=300) as r, open(d, "wb") as f:
            shutil.copyfileobj(r, f)
    return d


def ler_csv_brasil(z: zipfile.ZipFile, cols):
    nome = next(n for n in z.namelist() if n.upper().endswith("_BRASIL.CSV"))
    with z.open(nome) as h:
        return pd.read_csv(io.TextIOWrapper(h, encoding="latin1"), sep=";", dtype=str, usecols=lambda c: c in cols)


def comparecimento(a):
    z = zipfile.ZipFile(baixar(a))
    d = ler_csv_brasil(z, {"NR_TURNO", "CD_CARGO", "SG_UF", "CD_MUNICIPIO", "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"})
    d = d[d.CD_CARGO == "1"]
    for c in ("QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"):
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0)
    m = d.groupby(["NR_TURNO", "SG_UF", "CD_MUNICIPIO"], as_index=False)[["QT_APTOS", "QT_COMPARECIMENTO"]].sum()
    nac = d.groupby("NR_TURNO")[["QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"]].sum()
    return m, nac


def votos_municipio(a):
    """Votos de presidente por município, turno e candidato (arquivo _BRASIL da votação por candidato)."""
    z = zipfile.ZipFile(HIST / f"votacao_candidato_munzona_{a}.zip")
    d = ler_csv_brasil(z, {"NR_TURNO", "CD_CARGO", "SG_UF", "CD_MUNICIPIO", "NR_CANDIDATO", "QT_VOTOS_NOMINAIS"})
    d = d[d.CD_CARGO == "1"]
    d["v"] = pd.to_numeric(d.QT_VOTOS_NOMINAIS, errors="coerce").fillna(0)
    return d.groupby(["NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NR_CANDIDATO"], as_index=False).v.sum()


def votos_2026():
    t1 = pd.read_parquet(R / "dados/derivados/t1_secoes.parquet")
    t2 = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
    for c in ["lula", "flavio", "cury", "renan", "caiado", "zema", "demais"]:
        t1[c] = pd.to_numeric(t1[c], errors="coerce").fillna(0)
    for c in ["bu_lula", "bu_flavio"]:
        t2[c] = pd.to_numeric(t2[c], errors="coerce").fillna(0)
    a = t1.groupby(["uf", "municipio"], as_index=False)[["lula", "flavio", "cury", "renan", "caiado", "zema", "demais"]].sum()
    b = t2.groupby(["uf", "municipio"], as_index=False)[["bu_lula", "bu_flavio"]].sum()
    return a.merge(b, on=["uf", "municipio"])


def main():
    shutil.copy2(APOIOS_ORIGEM, R / "dados/copias/apoios_segundo_turno.csv")
    apoios = pd.read_csv(R / "dados/copias/apoios_segundo_turno.csv")
    man = {"apoios_segundo_turno.csv": hashlib.sha256((R / "dados/copias/apoios_segundo_turno.csv").read_bytes()).hexdigest()}
    h = pd.read_csv(R / "dados/derivados/historico_turnos.csv")
    linhas = []
    for a in ANOS + [2026]:
        if a < 2026:
            br = h[(h.ano == a) & (h.cargo == "presidente") & (h.uf == "BR")]
            t1 = br[br.turno == 1].set_index("nr_candidato").votos_nominais
            t2 = br[br.turno == 2].set_index("nr_candidato").votos_nominais
            adv = int(t2.drop(PT).idxmax())
            pt1, ad1, pt2, ad2 = t1[PT], t1[adv], t2[PT], t2[adv]
            eliminados = int(t1.sum() - pt1 - ad1)
        else:
            pt1, ad1, pt2, ad2 = 53879538, 56104503, 64256232, 59826041
            eliminados = 119300788 - pt1 - ad1
        gpt, gad = pt2 - pt1, ad2 - ad1
        ap = apoios[apoios.ano == a]
        tot = ap.pct_validos_1t.sum()
        lado = {k: round(float(ap[ap.posicao_2t == k].pct_validos_1t.sum() / tot * 100), 1) if tot else None
                for k in ("apoiou o PT", "apoiou o adversário", "neutro ou nulo")}
        if a < 2026:
            m, nac = comparecimento(a)
            abst = {t: float(nac.loc[t, "QT_ABSTENCOES"] / nac.loc[t, "QT_APTOS"] * 100) for t in ("1", "2")}
            mm = m.pivot_table(index=["SG_UF", "CD_MUNICIPIO"], columns="NR_TURNO", values=["QT_APTOS", "QT_COMPARECIMENTO"]).dropna()
            c1 = mm[("QT_COMPARECIMENTO", "1")] / mm[("QT_APTOS", "1")]
            c2 = mm[("QT_COMPARECIMENTO", "2")] / mm[("QT_APTOS", "2")]
        else:
            # o detalhe do TSE de 2026 ainda só tem o 1º turno: aptos e comparecimento vêm dos boletins por seção, e o
            # total nacional do arquivo oficial gravado na noite (1º turno: referência; 2º turno: versão final)
            o1 = json.loads((R / "dados/noite/referencias/tse-1turno/br.json").read_text(encoding="utf-8", errors="replace"))["e"]
            o2 = json.loads((R / "dados/noite/versoes-tse/br/4241309.json").read_text(encoding="utf-8", errors="replace"))["e"]
            abst = {"1": int(o1["a"]) / int(o1["te"]) * 100, "2": int(o2["a"]) / int(o2["te"]) * 100}
            s1 = pd.read_parquet(R / "dados/derivados/t1_secoes.parquet")
            s2 = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
            g = []
            for s in (s1, s2):
                s = s[s.uf != "zz"].copy()
                for c in ("aptos", "comparecimento"):
                    s[c] = pd.to_numeric(s[c], errors="coerce")
                g.append(s.groupby(["uf", "municipio"])[["aptos", "comparecimento"]].sum())
            j_ = g[0].join(g[1], lsuffix="1", rsuffix="2").dropna()
            c1 = j_.comparecimento1 / j_.aptos1
            c2 = j_.comparecimento2 / j_.aptos2
        subiu = float((c2 > c1).mean() * 100)
        # espalhamento
        if a < 2026:
            v = votos_municipio(a)
            p = v[v.NR_CANDIDATO.astype(int).isin([PT, adv])].copy()
            p["quem"] = (p.NR_CANDIDATO.astype(int) == PT).map({True: "pt", False: "ad"})
            q = p.pivot_table(index=["SG_UF", "CD_MUNICIPIO"], columns=["NR_TURNO", "quem"], values="v", aggfunc="sum").dropna()
            pt_1, ad_1, pt_2, ad_2 = q[("1", "pt")], q[("1", "ad")], q[("2", "pt")], q[("2", "ad")]
        else:
            q = votos_2026()
            q = q[q.uf != "zz"]
            pt_1, ad_1, pt_2, ad_2 = q.lula, q.flavio, q.bu_lula, q.bu_flavio
        f1 = (pt_1 - ad_1) / (pt_1 + ad_1)
        f2 = (pt_2 - ad_2) / (pt_2 + ad_2)
        sentido = 1 if (pt2 - ad2) / (pt2 + ad2) > (pt1 - ad1) / (pt1 + ad1) else -1
        mesmo_lado = float((((f2 - f1) * sentido) > 0).mean() * 100)
        linhas.append({"ano": a, "votos_dos_eliminados": eliminados, "pt_ganhou": int(gpt), "adversario_ganhou": int(gad),
                       "parte_do_pt_nos_votos_livres_pct": round(gpt / (gpt + gad) * 100, 1),
                       "eliminados_que_apoiaram_o_pt_pct": lado["apoiou o PT"], "eliminados_que_apoiaram_o_adversario_pct": lado["apoiou o adversário"],
                       "eliminados_neutros_pct": lado["neutro ou nulo"],
                       "abstencao_1t_pct": round(abst["1"], 2), "abstencao_2t_pct": round(abst["2"], 2), "abstencao_variou_pontos": round(abst["2"] - abst["1"], 2),
                       "municipios": int(len(f1)), "municipios_comparecimento_subiu_pct": round(subiu, 1),
                       "municipios_diferenca_para_o_lado_do_pais_pct": round(mesmo_lado, 1), "pt_ganhou_votos_em_municipios": int((pt_2 > pt_1).sum())})
        print(linhas[-1], flush=True)
    for z in sorted(BR.glob("*.zip")):
        man[z.name] = hashlib.sha256(z.read_bytes()).hexdigest()
    (R / "dados/MANIFESTO_DETALHE.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    with open(R / "resultados/rodada4_por_ano.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0])); w.writeheader(); w.writerows(linhas)
    (R / "resultados/rodada4_normalidade.json").write_text(json.dumps({"por_ano": linhas}, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
