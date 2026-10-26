"""Emenda 1 (coleta): SP, TO e exterior do 1º turno pelo boletim de urna publicado em arquivo único por UF (BU na Web,
dados abertos do TSE, conferido contra o hash .sha512 publicado ao lado).

Motivo: em 26/10 às 14h45, faltando 30.656 seções de SP, TO e exterior, o servidor de resultados do TSE passou a
responder 429 (limite de acesso) e a coleta parou. O BU na Web é o mesmo boletim, em outro servidor do TSE.
Antes de usar, o arquivo é conferido contra as 73 mil seções de SP já baixadas pelo coletor (mesmos votos por seção).

Saída: dados/derivados/t1/<uf>.parquet para sp, to e zz (mesmo esquema de ferramentas/derivar-t1.py) e
resultados/emenda1_conferencia_bweb.json
"""
import hashlib, json, shutil, sqlite3, sys, urllib.request, zipfile
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
URLS = {"sp": "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/buweb/bweb_1t_SP_051020261403.zip",
        "to": "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/buweb/bweb_1t_TO_051020261403.zip",
        "zz": "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/buweb/bweb_1t_ZZ_051020261403.zip"}
BR = R / "dados/brutos/bweb2026"
NUM = {"13": "lula", "22": "flavio", "70": "cury", "14": "renan", "55": "caiado", "30": "zema"}
UA = {"User-Agent": "investigacao-segundo-turno-2026 (github.com/Gabriel-Alexandre)"}


def baixar(url):
    BR.mkdir(parents=True, exist_ok=True)
    dest = BR / url.rsplit("/", 1)[1]
    pub = urllib.request.urlopen(urllib.request.Request(url + ".sha512", headers=UA), timeout=60).read().decode("latin1").split()[0].lower()
    if not (dest.exists() and hashlib.sha512(dest.read_bytes()).hexdigest() == pub):
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f, 1 << 20)
        if hashlib.sha512(dest.read_bytes()).hexdigest() != pub:
            raise RuntimeError("hash diferente")
    return dest, pub


def ler(uf):
    dest, pub = baixar(URLS[uf])
    z = zipfile.ZipFile(dest)
    nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    cols = {"CD_MUNICIPIO": "municipio", "NR_ZONA": "zona", "NR_SECAO": "secao", "CD_CARGO_PERGUNTA": "cargo", "DS_TIPO_VOTAVEL": "tipo",
            "NR_VOTAVEL": "numero", "QT_VOTOS": "votos", "QT_APTOS": "aptos", "QT_COMPARECIMENTO": "comparecimento", "DT_BU_RECEBIDO": "recebido"}
    partes = []
    with z.open(nome) as fh:
        for ch in pd.read_csv(fh, sep=";", encoding="latin1", dtype=str, usecols=lambda c: c in cols, chunksize=1_000_000, keep_default_na=False):
            ch = ch.rename(columns=cols)
            ch = ch[ch.cargo == "1"].copy()
            ch["votos"] = pd.to_numeric(ch.votos, errors="coerce").fillna(0).astype(int)
            t = ch.tipo.str.lower()
            ch["col"] = "demais"
            ch.loc[t.str.startswith("branco"), "col"] = "branco"
            ch.loc[t.str.startswith("nulo"), "col"] = "nulo"
            for n, nm in NUM.items():
                ch.loc[t.str.startswith("nominal") & (ch.numero == n), "col"] = nm
            partes.append(ch)
    d = pd.concat(partes, ignore_index=True)
    d["municipio"] = d.municipio.str.zfill(5)
    d["zona"] = d.zona.str.zfill(4)
    d["secao"] = d.secao.str.zfill(4)
    k = ["municipio", "zona", "secao"]
    sec = d.groupby(k, as_index=False)[["aptos", "comparecimento", "recebido"]].first()
    piv = d.pivot_table(index=k, columns="col", values="votos", aggfunc="sum", fill_value=0).reset_index()
    out = sec.merge(piv, on=k, how="left")
    out.insert(0, "uf", uf)
    for c in ("aptos", "comparecimento"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["recebido"] = pd.to_datetime(out.recebido, format="%d/%m/%Y %H:%M:%S", errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    for c in list(NUM.values()) + ["demais", "branco", "nulo"]:
        if c not in out:
            out[c] = 0
    out["fonte"] = "bweb"
    return out, pub


def main():
    import importlib.util
    s = importlib.util.spec_from_file_location("d1", R / "ferramentas/derivar-t1.py")
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    conf = {}
    for uf in URLS:
        b, pub = ler(uf)
        if uf == "sp":
            a = m.uma_uf("sp").dropna(subset=["aptos"])
            for c in ["lula", "flavio", "cury", "renan", "caiado", "zema", "demais", "branco", "nulo"]:
                a[c] = pd.to_numeric(a[c], errors="coerce").fillna(0)
            x = a.merge(b, on=["uf", "municipio", "zona", "secao"], suffixes=("_coletor", "_bweb"))
            iguais = sum(int((x[f"{c}_coletor"] == x[f"{c}_bweb"]).all()) for c in ["lula", "flavio", "cury", "renan", "caiado", "branco", "nulo", "aptos", "comparecimento"])
            dif = int(((x.lula_coletor != x.lula_bweb) | (x.flavio_coletor != x.flavio_bweb) | (x.aptos_coletor != x.aptos_bweb)).sum())
            conf["sp"] = {"secoes_baixadas_pelo_coletor": int(len(a)), "casadas_com_o_bweb": int(len(x)), "secoes_com_diferenca": dif,
                          "colunas_iguais_em_todas": iguais, "de_colunas": 9, "sha512_publicado": pub}
        else:
            conf[uf] = {"sha512_publicado": pub}
        b.to_parquet(R / f"dados/derivados/t1/{uf}.parquet", index=False)
        conf[uf]["secoes_bweb"] = int(len(b))
        print(uf, conf[uf], flush=True)
    todas = pd.concat([pd.read_parquet(p) for p in sorted((R / "dados/derivados/t1").glob("*.parquet"))], ignore_index=True)
    todas.to_parquet(R / "dados/derivados/t1_secoes.parquet", index=False)
    conf["total_secoes_1t"] = int(len(todas))
    (R / "resultados/emenda1_conferencia_bweb.json").write_text(json.dumps(conf, indent=1, ensure_ascii=False), encoding="utf-8")
    print("total", len(todas))


if __name__ == "__main__":
    main()
