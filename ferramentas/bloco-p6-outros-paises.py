"""P6: em outros países, quem liderou o 1º turno presidencial perdeu o 2º? Quanto isso depende da frente?

Base fixada antes da conta: países com eleição direta de presidente em dois turnos e eleições competitivas, de 1990 a
2025 (lista PAISES abaixo). Para cada país, as páginas da categoria "Presidential elections in <país>" da Wikipédia
em inglês; em cada página, a tabela {{Election results}} com os votos do 1º turno (votesN) e do 2º (votesN_2).
Entra a eleição que teve 2º turno (pelo menos dois candidatos com votesN_2). Brasil fica de fora (é o P1).

Saída: resultados/p6_outros_paises.json, resultados/p6_segundos_turnos.csv, capturas em dados/capturas/wikipedia-p6/
"""
from __future__ import annotations

import csv, hashlib, json, math, re, subprocess, time, urllib.parse
from pathlib import Path

R = Path(__file__).resolve().parents[1]
CAP = R / "dados" / "capturas" / "wikipedia-p6"
PAISES = ["Argentina", "Bolivia", "Chile", "Colombia", "Costa Rica", "the Dominican Republic", "Ecuador", "El Salvador",
          "Guatemala", "Peru", "Uruguay", "Austria", "Bulgaria", "Croatia", "Cyprus", "the Czech Republic", "Finland", "France",
          "Lithuania", "Montenegro", "North Macedonia", "Poland", "Portugal", "Romania", "Serbia", "Slovakia", "Slovenia",
          "Ukraine", "Moldova", "Georgia (country)", "Ghana", "Senegal", "Benin", "Cape Verde", "Liberia", "Sierra Leone",
          "Indonesia", "Mongolia", "Timor-Leste", "Panama", "Haiti", "Madagascar", "Malawi", "Guinea-Bissau", "São Tomé and Príncipe"]
API = "https://en.wikipedia.org/w/api.php"


def get(url: str) -> bytes:
    for t in range(5):
        r = subprocess.run(["curl", "-s", "--max-time", "60", "-A", "investigacao-segundo-turno-2026 (github.com/Gabriel-Alexandre)", url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout
        time.sleep(2 + t)
    return b""


def membros(pais: str) -> list[str]:
    cat = f"Category:Presidential elections in {pais}"
    u = f"{API}?action=query&list=categorymembers&cmtitle={urllib.parse.quote(cat)}&cmlimit=500&format=json&cmtype=page"
    for t in range(6):
        try:
            d = json.loads(get(u) or b"{}")
            break
        except json.JSONDecodeError:
            time.sleep(5 + 5 * t)
    else:
        raise RuntimeError(f"categoria ilegivel: {cat}")
    return [m["title"] for m in d.get("query", {}).get("categorymembers", [])]


def bloco(texto: str) -> list[dict]:
    """Candidatos com votos do 1º e do 2º turno da primeira tabela {{Election results}} que tiver 2º turno."""
    for m in re.finditer(r"\{\{\s*Election results", texto):
        trecho = texto[m.end(): m.end() + 20000]
        fim = trecho.find("\n}}")
        trecho = trecho[: fim if fim > 0 else 20000]
        campos = dict(re.findall(r"\|\s*([a-z]+\d+(?:_2)?)\s*=\s*([^|\n]*)", trecho))
        cands = []
        for i in range(1, 60):
            v1 = campos.get(f"votes{i}")
            if v1 is None:
                continue
            nome = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", campos.get(f"cand{i}", "")).strip()
            try:
                a = int(re.sub(r"[^\d]", "", v1) or 0)
                b = int(re.sub(r"[^\d]", "", campos.get(f"votes{i}_2", "") or "0") or 0)
            except ValueError:
                continue
            cands.append({"cand": nome, "v1": a, "v2": b})
        if sum(1 for c in cands if c["v2"] > 0) >= 2 and all(c["cand"] for c in cands[:2]):
            return cands
    return []


def main():
    CAP.mkdir(parents=True, exist_ok=True)
    linhas, man = [], {}
    for pais in PAISES:
        for titulo in membros(pais):
            ano = re.match(r"^(\d{4})", titulo)
            if not ano or not (1990 <= int(ano.group(1)) <= 2025):
                continue
            nome = re.sub(r"[^\w-]", "_", titulo)[:120] + ".wikitext"
            if (CAP / nome).exists() and (CAP / nome).stat().st_size > 500:
                raw = (CAP / nome).read_bytes()
            else:
                raw = get(f"https://en.wikipedia.org/w/index.php?title={urllib.parse.quote(titulo)}&action=raw")
                (CAP / nome).write_bytes(raw)
                time.sleep(0.3)
            man[nome] = hashlib.sha256(raw).hexdigest()
            c = bloco(raw.decode("utf-8", "replace"))
            if not c:
                continue
            val1 = sum(x["v1"] for x in c)
            o1 = sorted(c, key=lambda x: -x["v1"])
            o2 = sorted(c, key=lambda x: -x["v2"])
            lider, seg = o1[0], o1[1]
            if val1 == 0 or o2[1]["v2"] == 0:
                continue
            linhas.append({"pais": pais, "eleicao": titulo, "ano": int(ano.group(1)), "lider_1t": lider["cand"],
                           "lider_1t_pct": round(lider["v1"] / val1 * 100, 2), "segundo_1t": seg["cand"],
                           "frente_1t_pontos": round((lider["v1"] - seg["v1"]) / val1 * 100, 2), "vencedor_2t": o2[0]["cand"],
                           "virada": int(o2[0]["cand"] != lider["cand"])})
    # duas páginas para a mesma eleição: fica uma
    vistos, uni = set(), []
    for x in linhas:
        k = (x["pais"], x["ano"], x["lider_1t"], x["vencedor_2t"])
        if k not in vistos:
            vistos.add(k)
            uni.append(x)
    with open(R / "resultados/p6_segundos_turnos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(uni[0].keys())); w.writeheader(); w.writerows(sorted(uni, key=lambda x: (x["pais"], x["ano"])))
    n = len(uni); v = sum(x["virada"] for x in uni)
    perto = [x for x in uni if x["frente_1t_pontos"] <= 3 and x["lider_1t_pct"] < 50]
    xs = [x["frente_1t_pontos"] for x in uni]; ys = [x["virada"] for x in uni]
    a = b = 0.0
    for _ in range(200):
        ga = gb = haa = hab = hbb = 0.0
        for x, y in zip(xs, ys):
            p = 1 / (1 + math.exp(-(a + b * x))); w_ = p * (1 - p)
            ga += y - p; gb += (y - p) * x; haa += w_; hab += w_ * x; hbb += w_ * x * x
        det = haa * hbb - hab * hab
        if det == 0:
            break
        da, db = (hbb * ga - hab * gb) / det, (haa * gb - hab * ga) / det
        a, b = a + da, b + db
        if abs(da) + abs(db) < 1e-10:
            break
    out = {"paises": len({x["pais"] for x in uni}), "segundos_turnos": n, "viradas": v, "taxa": round(v / n, 4),
           "frente_ate_3_e_lider_abaixo_50": {"n": len(perto), "viradas": sum(x["virada"] for x in perto)},
           "frente_ate_2": {"n": len([x for x in uni if x["frente_1t_pontos"] <= 2]), "viradas": sum(x["virada"] for x in uni if x["frente_1t_pontos"] <= 2)},
           "logistica_p_virada_frente_1_87": round(1 / (1 + math.exp(-(a + b * 1.87))), 4),
           "viradas_lista": [f'{x["eleicao"]}: {x["lider_1t"]} ({x["lider_1t_pct"]}%, frente {x["frente_1t_pontos"]}) -> {x["vencedor_2t"]}' for x in uni if x["virada"]]}
    (R / "dados" / "MANIFESTO_P6.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
    (R / "resultados/p6_outros_paises.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "viradas_lista"}, indent=1, ensure_ascii=False))
    print("\n".join(out["viradas_lista"]))


if __name__ == "__main__":
    main()
