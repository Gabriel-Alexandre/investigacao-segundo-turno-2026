"""Bloco P4: o favorito da Polymarket ganhou? Taxa de acerto em eleições nacionais resolvidas.

Critério (pré-registro §7, P4): em cada mercado de vencedor de eleição nacional resolvido, o favorito é o candidato
(ou partido) com o maior preço do "sim" 24 horas antes de o resultado ficar claro. "Resultado claro" = o primeiro
momento em que o preço do vencedor passa de 0,95 e não volta abaixo de 0,90. Acertou = o favorito é o vencedor.

O domínio da Polymarket não resolve no DNS local (bloqueio de sites de aposta no Brasil); a leitura usa o DNS
público da Cloudflare (DNS sobre HTTPS) via curl. Só dados públicos de preço; nenhuma conta, nenhuma aposta.

Saída: dados/derivados/polymarket_eventos.csv (todos os eventos lidos, incluídos e excluídos, com o motivo),
dados/derivados/polymarket_favoritos.csv (um por eleição incluída) e dados/brutos/polymarket/ (respostas cruas, sha256
em dados/MANIFESTO_POLYMARKET.json).

Uso: python ferramentas/polymarket.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos" / "polymarket"
DERIV = RAIZ / "dados" / "derivados"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
TAGS = ["elections", "world-elections", "global-elections"]

# eleição nacional de vencedor (presidente, parlamento, chefe de governo)
INCLUI = re.compile(r"(presidential election|parliamentary election|legislative election|general election|"
                    r"prime minist|chancellor|election winner|who will be next president|wins? .*presidential)", re.I)
EXCLUI = re.compile(r"(margin|turnout|place in|1st place|2nd place|second place|abroad|popular vote|by how|%|"
                    r"seats|majority|state |county|province|district|city|mayor|governor|senate|house|primary|"
                    r"nominee|recount|announce|debate|vote share|win by|out as|out by|in 202\d|before|resign|"
                    r"called|happen|attorney|tuscany|calabria|ontario|baden|washington-dc|washington dc|virginia|"
                    r"specific|runoff\?|any candidate|most votes|which party|parties|coalition)", re.I)


def baixar(url: str, nome: str) -> bytes:
    BRUTOS.mkdir(parents=True, exist_ok=True)
    destino = BRUTOS / nome
    if destino.exists() and destino.stat().st_size > 0:
        return destino.read_bytes()
    for t in range(6):
        r = subprocess.run(["curl", "-s", "--max-time", "90", "--doh-url", "https://cloudflare-dns.com/dns-query", url],
                           capture_output=True)
        if r.returncode == 0 and r.stdout[:1] in (b"[", b"{"):
            destino.write_bytes(r.stdout)
            return r.stdout
        time.sleep(2 + 2 * t)
    raise RuntimeError(f"falhou: {url}")


def eventos() -> list[dict]:
    vistos: dict[str, dict] = {}
    for tag in TAGS:
        off = 0
        while True:
            b = baixar(f"{GAMMA}/events?tag_slug={tag}&closed=true&limit=100&offset={off}", f"events-{tag}-{off}.json")
            lote = json.loads(b)
            if not lote:
                break
            for e in lote:
                vistos[e["id"]] = e
            off += 100
    return list(vistos.values())


def historico(token: str) -> list[tuple[int, float]]:
    b = baixar(f"{CLOB}/prices-history?market={token}&interval=max&fidelity=60", f"hist-{token[:24]}.json")
    h = json.loads(b).get("history", [])
    return [(int(x["t"]), float(x["p"])) for x in h]


def preco_em(h: list[tuple[int, float]], t: int) -> float | None:
    antes = [p for (tt, p) in h if tt <= t]
    return antes[-1] if antes else None


def main() -> None:
    evs = eventos()
    linhas_ev, favoritos = [], []
    for e in sorted(evs, key=lambda x: x.get("endDate") or ""):
        titulo = e.get("title", "")
        if not INCLUI.search(titulo):
            linhas_ev.append([e["id"], e["slug"], titulo, e.get("endDate"), "excluido", "nao e mercado de vencedor de eleicao"])
            continue
        if EXCLUI.search(titulo) or EXCLUI.search(e["slug"]):
            linhas_ev.append([e["id"], e["slug"], titulo, e.get("endDate"), "excluido", "submercado, subnacional ou pergunta de outro tipo"])
            continue
        mercados = []
        for m in e.get("markets", []):
            try:
                precos = json.loads(m.get("outcomePrices") or "[]")
                tokens = json.loads(m.get("clobTokenIds") or "[]")
                saidas = json.loads(m.get("outcomes") or "[]")
            except json.JSONDecodeError:
                continue
            if not tokens or not precos:
                continue
            if saidas[:2] == ["Yes", "No"]:
                nome = m.get("groupItemTitle") or m.get("question")
                mercados.append((nome, tokens[0], float(precos[0])))
            else:  # mercado de duas saídas nomeadas (A contra B)
                for i, s in enumerate(saidas):
                    mercados.append((s, tokens[i], float(precos[i])))
        resolvidos = [x for x in mercados if x[2] in (0.0, 1.0)]
        vencedores = [x for x in resolvidos if x[2] == 1.0]
        if len(vencedores) != 1 or len(resolvidos) < 2:
            linhas_ev.append([e["id"], e["slug"], titulo, e.get("endDate"), "excluido", f"resolucao nao unica ({len(vencedores)} vencedores)"])
            continue
        hist = {}
        for nome, tok, _ in resolvidos:
            try:
                hist[nome] = historico(tok)
            except RuntimeError:
                hist[nome] = []
        venc = vencedores[0][0]
        hv = hist.get(venc) or []
        if not hv:
            linhas_ev.append([e["id"], e["slug"], titulo, e.get("endDate"), "excluido", "sem historico de preco"])
            continue
        # resultado claro: primeiro t com p >= 0,95 depois do qual nunca fica abaixo de 0,90
        t_claro = None
        for i, (t, p) in enumerate(hv):
            if p >= 0.95 and all(pp >= 0.90 for (_, pp) in hv[i:]):
                t_claro = t
                break
        if t_claro is None:
            t_claro = hv[-1][0]
        t_ref = t_claro - 24 * 3600
        precos_ref = {n: preco_em(h, t_ref) for n, h in hist.items()}
        precos_ref = {n: p for n, p in precos_ref.items() if p is not None}
        if len(precos_ref) < 2:
            linhas_ev.append([e["id"], e["slug"], titulo, e.get("endDate"), "excluido", "historico nao cobre a vespera"])
            continue
        fav, pfav = max(precos_ref.items(), key=lambda x: x[1])
        linhas_ev.append([e["id"], e["slug"], titulo, e.get("endDate"), "incluido", ""])
        favoritos.append({
            "slug": e["slug"], "titulo": titulo, "fim": (e.get("endDate") or "")[:10],
            "vespera_utc": datetime.fromtimestamp(t_ref, timezone.utc).isoformat(timespec="minutes"),
            "favorito": fav, "preco_favorito": round(pfav, 3), "vencedor": venc,
            "preco_vencedor_vespera": round(precos_ref.get(venc, float("nan")), 3),
            "acertou": int(fav == venc), "volume": e.get("volume"),
        })
    DERIV.mkdir(parents=True, exist_ok=True)
    with open(DERIV / "polymarket_eventos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "slug", "titulo", "fim", "situacao", "motivo"])
        w.writerows(linhas_ev)
    with open(DERIV / "polymarket_favoritos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(favoritos[0].keys()))
        w.writeheader()
        w.writerows(favoritos)
    man = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(BRUTOS.glob("*.json"))}
    (RAIZ / "dados" / "MANIFESTO_POLYMARKET.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    n = len(favoritos)
    a = sum(x["acertou"] for x in favoritos)
    print(f"eventos lidos {len(evs)}, incluidos {n}, favorito acertou {a} ({a / n * 100:.1f}%)")


if __name__ == "__main__":
    main()
