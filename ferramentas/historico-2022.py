"""A régua de 2022: boletins de urna por seção do 1º e do 2º turno de 2022 (BU na Web, dados abertos do TSE).

A lista de endereços vem de apuracao-eleicoes-2026/dados/fontes-historicas.json (cópia em dados/copias/, sha256 no
manifesto); cada zip é conferido contra o hash publicado ao lado (.sha512). Só Presidente.

Saída: dados/derivados/s2022_t1.parquet e s2022_t2.parquet, uma linha por seção:
  uf, municipio, zona, secao, aptos, comparecimento, lula (13), bolsonaro (22), outros nominais, branco, nulo
e, no 1º turno, os votos de Simone Tebet (15) e Ciro Gomes (12).

Uso: python ferramentas/historico-2022.py
"""
from __future__ import annotations

import hashlib
import json
import shutil
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[1]
BRUTOS = R / "dados" / "brutos" / "bweb2022"
ORIGEM = R.parent / "apuracao-eleicoes-2026" / "dados" / "fontes-historicas.json"
UA = "investigacao-segundo-turno-2026 (analise aberta; github.com/Gabriel-Alexandre)"
COLS = {"SG_UF": "uf", "CD_MUNICIPIO": "municipio", "NR_ZONA": "zona", "NR_SECAO": "secao", "CD_CARGO_PERGUNTA": "cargo",
        "DS_TIPO_VOTAVEL": "tipo", "NR_VOTAVEL": "numero", "QT_VOTOS": "votos", "QT_APTOS": "aptos", "QT_COMPARECIMENTO": "comparecimento"}


def baixar(url: str) -> Path:
    BRUTOS.mkdir(parents=True, exist_ok=True)
    dest = BRUTOS / url.rsplit("/", 1)[1]
    pub = urllib.request.urlopen(urllib.request.Request(url + ".sha512", headers={"User-Agent": UA}), timeout=60).read().decode("latin1").split()[0].lower()
    if dest.exists() and hashlib.sha512(dest.read_bytes()).hexdigest() == pub:
        return dest
    tmp = dest.with_suffix(".part")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=300) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    if hashlib.sha512(tmp.read_bytes()).hexdigest() != pub:
        raise RuntimeError(f"hash diferente: {url}")
    tmp.replace(dest)
    return dest


def derivar(arg) -> pd.DataFrame:
    url, turno = arg
    z = zipfile.ZipFile(baixar(url))
    nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    partes = []
    with z.open(nome) as fh:
        for ch in pd.read_csv(fh, sep=";", encoding="latin1", dtype=str, usecols=lambda c: c in COLS, chunksize=1_000_000, keep_default_na=False):
            ch = ch.rename(columns=COLS)
            ch = ch[ch.cargo == "1"]
            if ch.empty:
                continue
            ch["votos"] = pd.to_numeric(ch.votos, errors="coerce").fillna(0).astype(int)
            t = ch.tipo.str.lower()
            ch["col"] = "outros"
            ch.loc[t.str.startswith("branco"), "col"] = "branco"
            ch.loc[t.str.startswith("nulo"), "col"] = "nulo"
            for num, nm in (("13", "lula"), ("22", "bolsonaro"), ("15", "tebet"), ("12", "ciro")):
                ch.loc[t.str.startswith("nominal") & (ch.numero == num), "col"] = nm
            partes.append(ch)
    d = pd.concat(partes, ignore_index=True)
    k = ["uf", "municipio", "zona", "secao"]
    sec = d.groupby(k, as_index=False)[["aptos", "comparecimento"]].first()
    piv = d.pivot_table(index=k, columns="col", values="votos", aggfunc="sum", fill_value=0).reset_index()
    out = sec.merge(piv, on=k, how="left")
    for c in ("aptos", "comparecimento"):
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["turno"] = int(turno)
    return out


def main() -> None:
    (R / "dados" / "copias").mkdir(parents=True, exist_ok=True)
    shutil.copy2(ORIGEM, R / "dados" / "copias" / "fontes-historicas.json")
    fontes = json.loads(ORIGEM.read_text(encoding="utf-8"))
    for turno in ("1", "2"):
        tarefas = [(u, turno) for _, u in fontes[f"2022-{turno}"]]
        with ProcessPoolExecutor(max_workers=6) as ex:
            df = pd.concat(list(ex.map(derivar, tarefas)), ignore_index=True)
        df.to_parquet(R / "dados" / "derivados" / f"s2022_t{turno}.parquet", index=False)
        print(turno, len(df), int(df.lula.sum()), int(df.bolsonaro.sum()), flush=True)
    man = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BRUTOS.glob("*.zip"))}
    (R / "dados" / "MANIFESTO_2022.json").write_text(json.dumps(man, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
