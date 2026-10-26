"""Bloco P (P1, P2, P5): os 2º turnos de presidente e governador no Brasil, de 1989 a 2022, pelos arquivos do TSE.

Baixa votacao_candidato_munzona_AAAA.zip (cdn.tse.jus.br), guarda sha256 em dados/MANIFESTO_HISTORICO.json e grava
dados/derivados/historico_turnos.csv: uma linha por (ano, cargo, uf, turno, candidato) com os votos nominais.
Presidente: uf = "BR" (soma de todas as UFs e do exterior) e também por UF (para a regra de Minas).

Uso: python ferramentas/historico-turnos.py
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos" / "historico"
DERIV = RAIZ / "dados" / "derivados"
URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{ano}.zip"
ANOS = [1989, 1994, 1998, 2002, 2006, 2010, 2014, 2018, 2022]
CARGOS = {"1": "presidente", "3": "governador"}


def baixar(ano: int) -> Path | None:
    BRUTOS.mkdir(parents=True, exist_ok=True)
    destino = BRUTOS / f"votacao_candidato_munzona_{ano}.zip"
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    req = urllib.request.Request(URL.format(ano=ano), headers={"User-Agent": "investigacao-segundo-turno-2026"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r, open(destino, "wb") as f:
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
    except Exception as e:  # 1989 pode nao existir no CDN
        print(f"{ano}: {e}", flush=True)
        if destino.exists():
            destino.unlink()
        return None
    return destino


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    manifesto = {}
    votos: dict[tuple, int] = defaultdict(int)
    nomes: dict[tuple, str] = {}
    for ano in ANOS:
        p = baixar(ano)
        if p is None:
            continue
        manifesto[p.name] = {"url": URL.format(ano=ano), "bytes": p.stat().st_size, "sha256": sha256(p),
                             "lido_em": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        z = zipfile.ZipFile(p)
        for nome in z.namelist():
            if not nome.upper().endswith("_BRASIL.CSV"):
                continue  # o arquivo _BRASIL tem todas as UFs e o exterior (em 1998 e 2002 o presidente so esta nele)
            with z.open(nome) as h:
                leitor = csv.DictReader(io.TextIOWrapper(h, encoding="latin1"), delimiter=";")
                for r in leitor:
                    cargo = CARGOS.get(r["CD_CARGO"])
                    if not cargo:
                        continue
                    turno = int(r["NR_TURNO"])
                    v = int(r["QT_VOTOS_NOMINAIS"] or 0)
                    if v < 0:
                        continue
                    cand = r["NR_CANDIDATO"]
                    uf = r["SG_UF"]
                    votos[(ano, cargo, uf, turno, cand)] += v
                    nomes[(ano, cargo, uf, cand)] = r["NM_URNA_CANDIDATO"]
                    if cargo == "presidente":
                        nomes[(ano, cargo, "BR", cand)] = r["NM_URNA_CANDIDATO"]
                    if cargo == "presidente":
                        votos[(ano, cargo, "BR", turno, cand)] += v
        print(f"{ano}: lido", flush=True)
    DERIV.mkdir(parents=True, exist_ok=True)
    with open(DERIV / "historico_turnos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ano", "cargo", "uf", "turno", "nr_candidato", "nome_urna", "votos_nominais"])
        for k in sorted(votos):
            ano, cargo, uf, turno, cand = k
            w.writerow([ano, cargo, uf, turno, cand, nomes[(ano, cargo, uf, cand)], votos[k]])
    (RAIZ / "dados" / "MANIFESTO_HISTORICO.json").write_text(json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8")
    print("ok", len(votos))
    sys.exit(0)


if __name__ == "__main__":
    main()
