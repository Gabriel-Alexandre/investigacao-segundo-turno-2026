"""Uma linha por seção do 2º turno, cruzando os quatro arquivos que o TSE publica: hora de recebimento (aux.json),
boletim (bu.dat), registro digital do voto (rdv.dat) e log da urna (log.jez).

Saída: dados/derivados/t2_secoes.parquet (sem identificador de mesário nem de eleitor).

Horas: boletim e log trazem a hora local da urna; a votação foi das 8h às 17h de Brasília em todo o país, prorrogada
até as 19h onde a urna ainda estava aberta. O fim normal em hora local é 17h menos a diferença para Brasília.

Uso: python ferramentas/derivar-t2.py [ufs separadas por vírgula | todas]
"""

from __future__ import annotations

import collections
import json
import sqlite3
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from investigacao import ber, bu, log  # noqa: E402

UFS = ["ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr", "rj",
       "rn", "ro", "rr", "rs", "sc", "se", "sp", "to", "zz"]
FUSO = {"ac": -2, "am": -1, "rr": -1, "ro": -1, "mt": -1, "ms": -1}  # horas em relação a Brasília (outubro, sem horário de verão)
LULA, FLAVIO = 13, 22
RAJADA_N, RAJADA_S = 10, 15  # pré-registro A7: 10 ou mais votos seguidos com menos de 15 s entre eles


def rdv_presidente(b: bytes) -> collections.Counter:
    """Votos de presidente no RDV: tipo 2 nominal (com o número digitado), 3 branco, 4 nulo."""
    out = collections.Counter()

    def walk(nodes):
        for cls, tag, cons, v in nodes:
            if not cons:
                continue
            if (len(v) == 3 and v[0][:3] == (2, 1, False) and v[2][1] == 16 and v[2][2]
                    and all(x[2] and 1 <= len(x[3]) <= 2 and x[3][0][1] == 10 for x in v[2][3])):
                if ber.as_int(v[0][3]) != 1:
                    continue
                for x in v[2][3]:
                    tipo = ber.as_int(x[3][0][3])
                    dig = x[3][1][3].decode() if len(x[3]) == 2 else ""
                    out[(tipo, dig)] += 1
            else:
                walk(v)

    walk(ber.parse(b))
    return out


def partes(url: str):
    p = url.split("/")
    i = p.index("dados")
    return p[i + 2], p[i + 3], p[i + 4]  # municipio, zona, secao


def uma_uf(uf: str) -> pd.DataFrame:
    con = sqlite3.connect(RAIZ / "dados" / "brutos" / "t2" / f"{uf}.sqlite")
    sec = {}
    for url, st, body in con.execute("SELECT url, status, body FROM raw"):
        if "/config/" in url:
            continue
        m, z, s = partes(url)
        r = sec.setdefault((m, z, s), {"uf": uf, "municipio": m, "zona": z, "secao": s})
        if st != 200:
            if url.endswith("-aux.json"):
                r["aux_status"] = st
            continue
        if url.endswith("-aux.json"):
            d = json.loads(body)
            r["aux_status"] = 200
            r["situacao"] = d.get("st")
            hs = d.get("hashes", [])
            r["n_hashes"] = len(hs)
            tot = [h for h in hs if h.get("st") == "Totalizado"] or hs
            if tot:
                r["recebido"] = f'{tot[-1]["dr"][6:]}-{tot[-1]["dr"][3:5]}-{tot[-1]["dr"][:2]} {tot[-1]["hr"]}'
        elif url.endswith("-bu.dat"):
            try:
                b = bu.decode(body)
            except Exception as e:  # noqa: BLE001
                r["erro_bu"] = repr(e)[:80]
                continue
            r.update(aptos=b.aptos, comparecimento=b.comparecimento, abertura=b.abertura, encerramento=b.encerramento,
                     bu_lula=b.votos.get((1, 1, LULA, LULA), 0), bu_flavio=b.votos.get((1, 1, FLAVIO, FLAVIO), 0),
                     bu_branco=sum(v for k, v in b.votos.items() if k[0] == 1 and k[1] == 2),
                     bu_nulo=sum(v for k, v in b.votos.items() if k[0] == 1 and k[1] == 3),
                     bu_outros_nominais=sum(v for k, v in b.votos.items() if k[0] == 1 and k[1] == 1 and k[3] not in (LULA, FLAVIO)))
        elif url.endswith("-rdv.dat"):
            try:
                c = rdv_presidente(body)
            except Exception as e:  # noqa: BLE001
                r["erro_rdv"] = repr(e)[:80]
                continue
            r.update(rdv_lula=c.get((2, "13"), 0), rdv_flavio=c.get((2, "22"), 0),
                     rdv_branco=sum(v for k, v in c.items() if k[0] == 3),
                     rdv_nulo=sum(v for k, v in c.items() if k[0] == 4),
                     rdv_outros=sum(v for k, v in c.items() if k[0] not in (2, 3, 4) or (k[0] == 2 and k[1] not in ("13", "22"))))
        elif url.endswith("-log.jez"):
            try:
                L = log.ler_log(log.ler_jez(body), b"sem-identificador")
            except Exception as e:  # noqa: BLE001
                r["erro_log"] = repr(e)[:80]
                continue
            fim17 = (17 + FUSO.get(uf, 0)) * 3600
            fim19 = (19 + FUSO.get(uf, 0)) * 3600
            t = sorted(e[0] for e in L.eleitores)
            tipos = collections.Counter(e[1] for e in L.eleitores)
            depois17 = [e for e in L.eleitores if e[0] >= fim17]
            # rajadas
            rajadas, votos_em_rajada, seq = 0, 0, 1
            for a, b2 in zip(t, t[1:]):
                if b2 - a < RAJADA_S:
                    seq += 1
                else:
                    if seq >= RAJADA_N:
                        rajadas += 1
                        votos_em_rajada += seq
                    seq = 1
            if seq >= RAJADA_N:
                rajadas += 1
                votos_em_rajada += seq
            r.update(log_votos=len(t), log_primeiro_voto_s=t[0] if t else None, log_ultimo_voto_s=t[-1] if t else None,
                     log_encerrar_s=L.encerrar_s, log_contingencia=int(L.contingencia), log_ja_votou=len(L.ja_votou),
                     log_biometrica=tipos.get("biometrica", 0), log_manual_mesario=tipos.get("manual_mes", 0),
                     log_manual_sem_digital=tipos.get("manual_sem", 0), log_outra=tipos.get("outra", 0),
                     log_votos_depois_17h=len(depois17), log_votos_depois_19h=sum(1 for e in L.eleitores if e[0] >= fim19),
                     log_manuais_depois_17h=sum(1 for e in depois17 if e[1] != "biometrica"),
                     log_rajadas=rajadas, log_votos_em_rajada=votos_em_rajada,
                     log_manuais_ultima_hora=sum(1 for e in L.eleitores if fim17 - 3600 <= e[0] < fim17 and e[1] != "biometrica"),
                     log_manuais_primeira_hora=sum(1 for e in L.eleitores if (8 + FUSO.get(uf, 0)) * 3600 <= e[0] < (9 + FUSO.get(uf, 0)) * 3600 and e[1] != "biometrica"))
    con.close()
    return pd.DataFrame(list(sec.values()))


def main() -> None:
    ufs = UFS if len(sys.argv) < 2 or sys.argv[1] == "todas" else sys.argv[1].split(",")
    saida = RAIZ / "dados" / "derivados" / "t2"
    saida.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=8) as ex:
        for uf, df in zip(ufs, ex.map(uma_uf, ufs)):
            df.to_parquet(saida / f"{uf}.parquet", index=False)
            print(uf, len(df), flush=True)
    todas = pd.concat([pd.read_parquet(p) for p in sorted(saida.glob("*.parquet"))], ignore_index=True)
    todas.to_parquet(RAIZ / "dados" / "derivados" / "t2_secoes.parquet", index=False)
    print("total", len(todas))


if __name__ == "__main__":
    main()
