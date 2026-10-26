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
EXCLUI = re.compile(r"(margin|turnout|place|abroad|popular vote|by how|%|seats|majority|county|province|district|"
                    r"city|mayor|governor|senate|primary|nominee|recount|announce|debate|vote share|win by|out as|"
                    r"out by|before|resign|called|happen|attorney|specific|runoff\?|any candidate|most votes|"
                    r"national assembly election winner|legislative assembly election winner|by-election|quebec|"
                    r"british columbia|ontario|baden|tuscany|calabria|region|srpska|washington|virginia|new jersey|"
                    r"municipal|local|scotland|wales|catalonia|bavaria|state election|\bstate\b|"
                    r"tongatapu|ongo|hannover)", re.I)


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
    """Preco diario do historico inteiro (a API so devolve hora a hora para mercado antigo numa janela curta)."""
    b = baixar(f"{CLOB}/prices-history?market={token}&interval=max&fidelity=1440", f"hist-dia-{token[:24]}.json")
    return [(int(x["t"]), float(x["p"])) for x in json.loads(b).get("history", [])]


def historico_janela(token: str, ini: int, fim: int) -> list[tuple[int, float]]:
    b = baixar(f"{CLOB}/prices-history?market={token}&startTs={ini}&endTs={fim}&fidelity=60", f"hist-hora-{token[:24]}-{ini}.json")
    return [(int(x["t"]), float(x["p"])) for x in json.loads(b).get("history", [])]


def momento_claro(h: list[tuple[int, float]]) -> int | None:
    for i, (t, p) in enumerate(h):
        if p >= 0.95 and all(pp >= 0.90 for (_, pp) in h[i:]):
            return t
    return None


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
                hist[nome] = (tok, historico(tok))
            except RuntimeError:
                hist[nome] = (tok, [])
        venc = vencedores[0][0]
        tokv, hv = hist.get(venc, (None, []))
        if not hv:
            linhas_ev.append([e["id"], e["slug"], titulo, e.get("endDate"), "excluido", "sem historico de preco"])
            continue
        t_dia = momento_claro(hv) or hv[-1][0]
        # refina hora a hora numa janela de 5 dias antes ate 1 dia depois do dia em que ficou claro
        ini, fim = t_dia - 5 * 86400, t_dia + 86400
        try:
            hh = historico_janela(tokv, ini, fim)
        except RuntimeError:
            hh = []
        t_claro = (momento_claro(hh) if hh else None) or t_dia
        t_ref = t_claro - 24 * 3600
        # candidatos que importam: os com preco diario acima de 0,05 perto da vespera
        relevantes = {n: th for n, th in hist.items() if (preco_em(th[1], t_ref) or 0) >= 0.05 or n == venc}
        precos_ref = {}
        for n, (tk, hd) in relevantes.items():
            try:
                hj = historico_janela(tk, ini, fim)
            except RuntimeError:
                hj = []
            pr = preco_em(hj, t_ref) if hj else None
            precos_ref[n] = pr if pr is not None else preco_em(hd, t_ref)
        precos_ref = {n: p for n, p in precos_ref.items() if p is not None}
        if len(precos_ref) < 2 and not (len(precos_ref) == 1 and len(resolvidos) >= 2):
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
    vistos_el = set()
    for x in favoritos:
        chave = (x["vespera_utc"][:10], re.sub(r"^(next-prime-minist?er-of-|party-of-next-prime-minister-of-|which-party-wins-|which-party-will-win-the-\d+-)", "", x["slug"]).split("-")[0])
        x["repetida"] = int(chave in vistos_el)
        vistos_el.add(chave)
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
    unicos = [x for x in favoritos if not x["repetida"]]
    n = len(unicos)
    a = sum(x["acertou"] for x in unicos)
    fortes = [x for x in unicos if x["preco_favorito"] >= 0.75]
    print(f"eventos lidos {len(evs)}, mercados incluidos {len(favoritos)}, eleicoes {n}, favorito acertou {a} ({a / n * 100:.1f}%); "
          f"favorito acima de 75%: {sum(x['acertou'] for x in fortes)} de {len(fortes)}")


if __name__ == "__main__":
    main()
