"""Uma linha por seção do 1º turno de 2026 (hora de recebimento e boletim), só Presidente.

Saída: dados/derivados/t1_secoes.parquet: uf, municipio, zona, secao, recebido, aptos, comparecimento, e os votos de
Lula (13), Flávio (22), Cury (70), Renan Santos (14), Caiado (55), Zema (30), demais nominais, branco e nulo.

Uso: python ferramentas/derivar-t1.py [ufs | todas]
"""
from __future__ import annotations

import json
import sqlite3
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
from investigacao import bu  # noqa: E402

UFS = ["ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr", "rj",
       "rn", "ro", "rr", "rs", "sc", "se", "sp", "to", "zz"]
NUM = {13: "lula", 22: "flavio", 70: "cury", 14: "renan", 55: "caiado", 30: "zema"}


def partes(url):
    p = url.split("/")
    i = p.index("dados")
    return p[i + 2], p[i + 3], p[i + 4]


def uma_uf(uf: str) -> pd.DataFrame:
    con = sqlite3.connect(R / "dados" / "brutos" / "t1" / f"{uf}.sqlite")
    sec = {}
    for url, st, body in con.execute("SELECT url, status, body FROM raw"):
        if "/config/" in url:
            continue
        m, z, s = partes(url)
        r = sec.setdefault((m, z, s), {"uf": uf, "municipio": m, "zona": z, "secao": s})
        if st != 200:
            continue
        if url.endswith("-aux.json"):
            d = json.loads(body)
            r["situacao"] = d.get("st")
            hs = d.get("hashes", [])
            tot = [h for h in hs if h.get("st") == "Totalizado"] or hs
            if tot:
                r["recebido"] = f'{tot[-1]["dr"][6:]}-{tot[-1]["dr"][3:5]}-{tot[-1]["dr"][:2]} {tot[-1]["hr"]}'
        elif url.endswith("-bu.dat"):
            try:
                b = bu.decode(body)
            except Exception as e:  # noqa: BLE001
                r["erro_bu"] = repr(e)[:80]
                continue
            r.update(aptos=b.aptos, comparecimento=b.comparecimento,
                     branco=sum(v for k, v in b.votos.items() if k[0] == 1 and k[1] == 2),
                     nulo=sum(v for k, v in b.votos.items() if k[0] == 1 and k[1] == 3))
            demais = 0
            for k, v in b.votos.items():
                if k[0] == 1 and k[1] == 1:
                    nm = NUM.get(k[3])
                    if nm:
                        r[nm] = r.get(nm, 0) + v
                    else:
                        demais += v
            r["demais"] = demais
    con.close()
    df = pd.DataFrame(list(sec.values()))
    for c in list(NUM.values()) + ["demais"]:
        if c not in df:
            df[c] = 0
    return df


def main():
    ufs = UFS if len(sys.argv) < 2 or sys.argv[1] == "todas" else sys.argv[1].split(",")
    out = R / "dados" / "derivados" / "t1"
    out.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=8) as ex:
        for uf, df in zip(ufs, ex.map(uma_uf, ufs)):
            df.to_parquet(out / f"{uf}.parquet", index=False)
            print(uf, len(df), flush=True)
    todas = pd.concat([pd.read_parquet(p) for p in sorted(out.glob("*.parquet"))], ignore_index=True)
    todas.to_parquet(R / "dados" / "derivados" / "t1_secoes.parquet", index=False)
    print("total", len(todas))


if __name__ == "__main__":
    main()
