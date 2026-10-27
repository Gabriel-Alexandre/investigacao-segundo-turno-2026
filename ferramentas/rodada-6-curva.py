"""Rodada 6: o vídeo do "professor de matemática" que circulou em 26/10 (live gravada, transcrição no repositório de
documentação do canal). Duas afirmações dele viram teste, com os boletins de 2022 e de 2026:

  C1  "numa eleição de 51% a 49%, era esperado que a liderança se invertesse várias vezes ao longo da apuração";
      ele embaralhou a ordem de chegada das urnas mais de 3 mil vezes e viu "várias inversões"
  C2  na curva do Bolsonaro em ordem de chegada aparecem "vales igualmente espaçados", que seriam "um algoritmo que
      liga e desliga" penalizando o candidato

Como se testa:
  C1  a curva acumulada (a parte do candidato da direita nos votos dos 2) em ordem de chegada de cada boletim, contra
      3.000 ordens embaralhadas; conta as trocas de liderança no total, depois de 1% e depois de 5% das seções
  C2  na ordem real de 2022, cada queda brusca da curva (janela de 200 seções) é aberta: de onde são as seções que
      entraram nela e quanto o Lula teve nelas. Se a queda é um lote de seções de um mesmo lugar com muito voto no Lula,
      ela é a chegada daquele lugar, e cada seção tem o boletim público para conferir

Fontes: boletim de urna na web do 2º turno de 2022 (TSE, coluna DT_BU_RECEBIDO, `dados/brutos/bweb2022/`) e os boletins
do 2º turno de 2026 deste projeto (coluna `recebido`). Saída: resultados/rodada6_curva.json e rodada6_quedas_2022.csv
"""
from __future__ import annotations

import io, json, zipfile
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1]
B22 = R / "dados/brutos/bweb2022"
N_EMBARALHADAS = 3000
SEMENTE = 20261026


def secoes_2022() -> pd.DataFrame:
    partes = []
    for z in sorted(B22.glob("bweb_2t_*.zip")):
        zz = zipfile.ZipFile(z)
        nome = next(n for n in zz.namelist() if n.lower().endswith(".csv"))
        with zz.open(nome) as h:
            d = pd.read_csv(io.TextIOWrapper(h, encoding="latin1"), sep=";", dtype=str,
                            usecols=["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "CD_CARGO_PERGUNTA",
                                     "DT_BU_RECEBIDO", "NR_VOTAVEL", "QT_VOTOS"])
        d = d[d.CD_CARGO_PERGUNTA == "1"]
        d["v"] = pd.to_numeric(d.QT_VOTOS, errors="coerce").fillna(0)
        k = ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DT_BU_RECEBIDO"]
        p = d[d.NR_VOTAVEL.isin(["13", "22"])].pivot_table(index=k, columns="NR_VOTAVEL", values="v", aggfunc="sum").fillna(0).reset_index()
        partes.append(p.rename(columns={"13": "esq", "22": "dir"}))
    s = pd.concat(partes, ignore_index=True)
    s["rec"] = pd.to_datetime(s.DT_BU_RECEBIDO, dayfirst=True, errors="coerce")
    return s.rename(columns={"SG_UF": "uf", "CD_MUNICIPIO": "mun", "NM_MUNICIPIO": "nome", "NR_ZONA": "zona", "NR_SECAO": "secao"})


def secoes_2026() -> pd.DataFrame:
    d = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet", columns=["uf", "municipio", "zona", "secao", "recebido", "bu_lula", "bu_flavio"])
    d["esq"] = pd.to_numeric(d.bu_lula, errors="coerce").fillna(0)
    d["dir"] = pd.to_numeric(d.bu_flavio, errors="coerce").fillna(0)
    d["rec"] = pd.to_datetime(d.recebido, errors="coerce")
    return d.rename(columns={"municipio": "mun"}).assign(uf=lambda x: x.uf.str.upper())


def trocas(diff: np.ndarray, inicio: int) -> int:
    """Quantas vezes o sinal da diferença acumulada (direita menos esquerda) muda depois da seção `inicio`."""
    c = np.cumsum(diff)[inicio:]
    s = np.sign(c)
    s = s[s != 0]
    return int((s[1:] != s[:-1]).sum())


def curva(s: pd.DataFrame, ano: int, rng) -> dict:
    s = s.dropna(subset=["rec"]).sort_values(["rec", "uf", "mun", "zona", "secao"]).reset_index(drop=True)
    n = len(s)
    diff = (s.dir - s.esq).to_numpy(dtype=np.float64)
    c = np.cumsum(diff)
    sg = np.sign(c)
    mud = np.where((sg[1:] != sg[:-1]) & (sg[1:] != 0) & (sg[:-1] != 0))[0] + 1
    real = {"secoes": n, "trocas_depois_de_100_secoes": trocas(diff, 100), "trocas_depois_de_1pct": trocas(diff, n // 100),
            "trocas_depois_de_5pct": trocas(diff, n // 20),
            "onde_foram_as_trocas_pct_das_secoes": [round(float(i / n * 100), 2) for i in mud if i > 100],
            "hora_das_trocas": [str(s.rec.iloc[i]) for i in mud if i > 100]}
    t100, t1, t5, ult = [], [], [], []
    for _ in range(N_EMBARALHADAS):
        p = rng.permutation(diff)
        cc = np.cumsum(p)
        g = np.sign(cc)
        m = np.where((g[1:] != g[:-1]) & (g[1:] != 0) & (g[:-1] != 0))[0] + 1
        t100.append(int((m > 100).sum())); t1.append(int((m > n // 100).sum())); t5.append(int((m > n // 20).sum()))
        ult.append(float(m.max() / n * 100) if len(m) else 0.0)
    t100, t1, t5, ult = map(np.array, (t100, t1, t5, ult))
    emb = {"ordens": N_EMBARALHADAS, "trocas_depois_de_100_secoes_media": round(float(t100.mean()), 2),
           "trocas_depois_de_1pct_media": round(float(t1.mean()), 3), "trocas_depois_de_5pct_media": round(float(t5.mean()), 3),
           "ordens_com_alguma_troca_depois_de_1pct_pct": round(float((t1 > 0).mean() * 100), 2),
           "ordens_com_alguma_troca_depois_de_5pct_pct": round(float((t5 > 0).mean() * 100), 2),
           "ultima_troca_pct_das_secoes_mediana": round(float(np.median(ult)), 3),
           "ultima_troca_pct_das_secoes_p99": round(float(np.percentile(ult, 99)), 3)}
    return {"ano": ano, "ordem_real": real, "embaralhadas": emb,
            "parte_final_da_direita_pct": round(float(s.dir.sum() / (s.dir.sum() + s.esq.sum()) * 100), 2)}, s


def quedas(s: pd.DataFrame, a: int = 55000, b: int = 90000, janela: int = 60, n: int = 10) -> pd.DataFrame:
    """As n maiores quedas da parte acumulada da direita no trecho que o vídeo mostra (por volta das seções 60 mil a
    85 mil de 2022), em janelas de `janela` seções, separadas por pelo menos 800 seções; cada uma aberta pelo que
    entrou nela."""
    cd, ce = np.cumsum(s.dir.to_numpy()), np.cumsum(s.esq.to_numpy())
    parte = cd / np.maximum(cd + ce, 1) * 100
    d = parte[a + janela:b] - parte[a:b - janela]
    eventos = []
    for k in np.argsort(d):
        i = int(k) + a + janela
        if all(abs(i - e) > 800 for e in eventos):
            eventos.append(i)
        if len(eventos) >= n:
            break
    linhas = []
    for i in sorted(eventos):
        w = s.iloc[i - janela:i]
        g = w.groupby(["uf", "nome"]).agg(secoes=("secao", "size"), esq=("esq", "sum"), dir=("dir", "sum")).sort_values("secoes", ascending=False)
        top = g.index[0]
        linhas.append({"secao_na_ordem": i, "hora": str(s.rec.iloc[i]), "queda_pontos": round(float(parte[i] - parte[i - janela]), 4),
                       "parte_da_direita_antes": round(float(parte[i - janela]), 3),
                       "lula_pct_nas_secoes_que_entraram": round(float(w.esq.sum() / max(w.esq.sum() + w.dir.sum(), 1) * 100), 1),
                       "municipio_com_mais_secoes": f"{top[1]} ({top[0]})", "secoes_dele": int(g.secoes.iloc[0]),
                       "lula_pct_nele": round(float(g.esq.iloc[0] / max(g.esq.iloc[0] + g.dir.iloc[0], 1) * 100), 1),
                       "tem_secoes_de_salvador": bool(((w.uf == "BA") & (w.nome == "SALVADOR")).any())})
    return pd.DataFrame(linhas)


def trocas_distintas(r: dict) -> int:
    """Trocas depois de 1% das seções, agrupando as que caem no mesmo minuto (o sinal oscila dentro de um lote que chega
    no mesmo segundo ou no seguinte)."""
    return len({h[:16] for h, pc in zip(r["hora_das_trocas"], r["onde_foram_as_trocas_pct_das_secoes"]) if pc > 1})


def main():
    rng = np.random.default_rng(SEMENTE)
    s22 = secoes_2022()
    r22, o22 = curva(s22, 2022, rng)
    s26 = secoes_2026()
    r26, o26 = curva(s26, 2026, rng)
    q = quedas(o22)
    q.to_csv(R / "resultados/rodada6_quedas_2022.csv", index=False)
    gaps = np.diff(q.secao_na_ordem.to_numpy())
    for r in (r22, r26):
        r["ordem_real"]["trocas_distintas_depois_de_1pct"] = trocas_distintas(r["ordem_real"])
    out = {"C1_inversoes": [r22, r26],
           "C2_quedas_2022": {"trecho_secoes": [55000, 90000], "janela_secoes": 60, "quedas": int(len(q)),
                              "intervalo_entre_quedas_secoes": [int(x) for x in gaps],
                              "queda_media_pontos": round(float(q.queda_pontos.mean()), 4),
                              "lula_pct_medio_nas_secoes_das_quedas": round(float(q.lula_pct_nas_secoes_que_entraram.mean()), 1),
                              "quedas_com_secoes_de_salvador": int(q.tem_secoes_de_salvador.sum()),
                              "quedas": q.to_dict("records")},
           "secoes_2022_sem_hora": int(s22.rec.isna().sum())}
    (R / "resultados/rodada6_curva.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str)[:6000])


if __name__ == "__main__":
    main()
