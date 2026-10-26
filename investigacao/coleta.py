"""Coleta dos arquivos publicos do TSE por secao, nos dois turnos de 2026.

Base: apuracao-eleicoes-2026/apuracao/coleta.py (1o turno), com o pleito e os tipos de arquivo como parametro.
Cada resposta fica num SQLite por turno e UF (dados/brutos/<turno>/<uf>.sqlite) com URL, hora da coleta (UTC),
status, tamanho, sha256 e o corpo. Retomavel: o que ja esta salvo nao e baixado de novo.

  1o turno: pleito 3220  (hora de recebimento + boletim)
  2o turno: pleito 3221  (hora de recebimento + boletim + registro digital do voto + log da urna)

Uso: python -m investigacao.coleta <t1|t2> [ufs separadas por virgula | todas] [--teto 120] [--so N] [--tipos bu,busa,rdv,log]
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import aiohttp

BASE = "https://resultados.tse.jus.br/oficial/ele2026"
PLEITOS = {"t1": "3220", "t2": "3221"}
TIPOS_PADRAO = {"t1": ("bu", "busa"), "t2": ("bu", "busa", "rdv", "log")}
UA = "investigacao-segundo-turno-2026/0.1 (analise aberta, coleta com teto de requisicoes; github.com/Gabriel-Alexandre)"
UFS = ["ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to", "zz"]
RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"

SCHEMA = """
CREATE TABLE IF NOT EXISTS raw (
  url TEXT PRIMARY KEY, status INTEGER NOT NULL, fetched_utc TEXT NOT NULL,
  nbytes INTEGER NOT NULL, sha256 TEXT, body BLOB
);
"""


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def abrir(turno: str, uf: str) -> sqlite3.Connection:
    d = BRUTOS / turno
    d.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(d / f"{uf}.sqlite")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.executescript(SCHEMA)
    return con


def url_config(pl: str, uf: str) -> str:
    return f"{BASE}/arquivo-urna/{pl}/config/{uf}/{uf}-p00{pl}-cs.json"


def url_aux(pl: str, uf: str, mun: str, zona: str, secao: str) -> str:
    return f"{BASE}/arquivo-urna/{pl}/dados/{uf}/{mun}/{zona}/{secao}/p00{pl}-{uf}-m{mun}-z{zona}-s{secao}-aux.json"


def url_arq(pl: str, uf: str, mun: str, zona: str, secao: str, h: str, nome: str) -> str:
    return f"{BASE}/arquivo-urna/{pl}/dados/{uf}/{mun}/{zona}/{secao}/{h}/{nome}"


class Limitador:
    """Teto de requisicoes por segundo, adaptativo: cai ao receber 429 e sobe devagar enquanto tudo responde."""

    def __init__(self, por_segundo: float):
        self.teto = por_segundo
        self.taxa = por_segundo
        self._prox = 0.0
        self._lock = asyncio.Lock()
        self._ok = 0
        self.penalizacoes = 0

    async def esperar(self) -> None:
        async with self._lock:
            agora_ = time.monotonic()
            if self._prox > agora_:
                await asyncio.sleep(self._prox - agora_)
                agora_ = self._prox
            self._prox = agora_ + 1.0 / self.taxa

    def penalizar(self) -> None:
        self.taxa = max(5.0, self.taxa * 0.6)
        self._ok = 0
        self.penalizacoes += 1

    def sucesso(self) -> None:
        self._ok += 1
        if self._ok >= 150:
            self._ok = 0
            self.taxa = min(self.teto, self.taxa * 1.08)


async def baixar(sessao: aiohttp.ClientSession, lim: Limitador, url: str, tentativas: int = 10):
    ultimo = None
    for t in range(tentativas):
        await lim.esperar()
        try:
            async with sessao.get(url) as r:
                corpo = await r.read()
                if r.status in (200, 404, 403):
                    lim.sucesso()
                    return r.status, corpo
                if r.status == 429:
                    lim.penalizar()
                    espera = float(r.headers.get("Retry-After", 0) or 0) or min(30, 1.6**t)
                    await asyncio.sleep(espera)
                    ultimo = "HTTP 429"
                    continue
                ultimo = f"HTTP {r.status}"
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            ultimo = repr(e)
        await asyncio.sleep(min(30, 1.5**t))
    return 0, (ultimo or "falha").encode()


def salvo(con: sqlite3.Connection, url: str) -> bool:
    return con.execute("SELECT 1 FROM raw WHERE url=? AND status IN (200,404)", (url,)).fetchone() is not None


def guardar(con: sqlite3.Connection, url: str, status: int, corpo: bytes) -> None:
    sha = hashlib.sha256(corpo).hexdigest() if status == 200 else None
    con.execute(
        "INSERT OR REPLACE INTO raw(url,status,fetched_utc,nbytes,sha256,body) VALUES (?,?,?,?,?,?)",
        (url, status, agora(), len(corpo), sha, corpo if status == 200 else None),
    )


def secoes_da_uf(con: sqlite3.Connection, pl: str, uf: str):
    """Lista (mun, zona, secao, principal) da config. Secao agregada traz 'nsp' (a secao principal)."""
    row = con.execute("SELECT body FROM raw WHERE url=? AND status=200", (url_config(pl, uf),)).fetchone()
    cfg = json.loads(row[0])
    out = []
    for abr in cfg["abr"]:
        for mu in abr["mu"]:
            for zo in mu["zon"]:
                for se in zo["sec"]:
                    out.append((mu["cd"], zo["cd"], se["ns"], se.get("nsp")))
    return out


async def coletar_uf(turno: str, uf: str, lim: Limitador, concorrencia: int, tipos, so: int | None = None) -> dict:
    pl = PLEITOS[turno]
    con = abrir(turno, uf)
    timeout = aiohttp.ClientTimeout(total=120, connect=20)
    conector = aiohttp.TCPConnector(limit=concorrencia, ttl_dns_cache=300)
    async with aiohttp.ClientSession(headers={"User-Agent": UA}, timeout=timeout, connector=conector) as sessao:
        cu = url_config(pl, uf)
        if not salvo(con, cu):
            st, corpo = await baixar(sessao, lim, cu)
            guardar(con, cu, st, corpo)
            con.commit()
        if con.execute("SELECT status FROM raw WHERE url=?", (cu,)).fetchone()[0] != 200:
            return {"uf": uf, "erro": "config indisponivel"}
        secoes = secoes_da_uf(con, pl, uf)
        if so:
            secoes = secoes[:so]
        proprias = [s for s in secoes if not s[3]]
        feitas = 0
        sem = asyncio.Semaphore(concorrencia)
        escrita = asyncio.Lock()
        t0 = time.monotonic()

        async def uma(mun, zona, secao):
            nonlocal feitas
            async with sem:
                ua = url_aux(pl, uf, mun, zona, secao)
                if salvo(con, ua):
                    st, corpo = con.execute("SELECT status, body FROM raw WHERE url=?", (ua,)).fetchone()
                else:
                    st, corpo = await baixar(sessao, lim, ua)
                    async with escrita:
                        guardar(con, ua, st, corpo)
                if st == 200:
                    dado = json.loads(corpo)
                    for h in dado.get("hashes", []):
                        for arq in h.get("arq", []):
                            if arq.get("tp") in tipos:
                                ub = url_arq(pl, uf, mun, zona, secao, h["hash"], arq["nm"])
                                if not salvo(con, ub):
                                    stb, cb = await baixar(sessao, lim, ub)
                                    async with escrita:
                                        guardar(con, ub, stb, cb)
                feitas += 1
                if feitas % 1000 == 0:
                    async with escrita:
                        con.commit()
                    dt = time.monotonic() - t0
                    print(f"{agora()} {turno} {uf} {feitas}/{len(proprias)} secoes  {feitas/dt:.1f}/s  taxa={lim.taxa:.0f}  429={lim.penalizacoes}", flush=True)

        await asyncio.gather(*[uma(*s[:3]) for s in proprias])
        con.commit()
    n = con.execute("SELECT COUNT(*) FROM raw").fetchone()[0]
    falhas = con.execute("SELECT COUNT(*) FROM raw WHERE status NOT IN (200,404)").fetchone()[0]
    con.close()
    return {"turno": turno, "uf": uf, "secoes": len(secoes), "proprias": len(proprias), "itens": n, "falhas": falhas}


def resumo_da_uf(turno: str, uf: str) -> str:
    """sha256 sobre as linhas 'url<TAB>sha256' ordenadas (o mesmo resumo do projeto do 1o turno)."""
    con = abrir(turno, uf)
    h = hashlib.sha256()
    for url, sha in con.execute("SELECT url, COALESCE(sha256,'-') FROM raw ORDER BY url"):
        h.update(f"{url}\t{sha}\n".encode())
    con.close()
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("turno", choices=["t1", "t2"])
    ap.add_argument("ufs", nargs="?", default="todas")
    ap.add_argument("--teto", type=float, default=120.0)
    ap.add_argument("--concorrencia", type=int, default=96)
    ap.add_argument("--so", type=int, default=None)
    ap.add_argument("--tipos", default=None)
    a = ap.parse_args()
    ufs = UFS if a.ufs == "todas" else a.ufs.split(",")
    tipos = tuple(a.tipos.split(",")) if a.tipos else TIPOS_PADRAO[a.turno]
    async def todas() -> None:
        lim = Limitador(a.teto)  # um limitador so, no mesmo laco de eventos, para todas as UFs
        for uf in ufs:
            r = await coletar_uf(a.turno, uf, lim, a.concorrencia, tipos, a.so)
            print(json.dumps(r, ensure_ascii=False), flush=True)
            log = RAIZ / "dados" / "brutos" / "COLETA.jsonl"
            with open(log, "a", encoding="utf-8") as f:
                f.write(json.dumps({"hora": agora(), "tipos": list(tipos), **r}, ensure_ascii=False) + "\n")

    asyncio.run(todas())
    sys.exit(0)


if __name__ == "__main__":
    main()
