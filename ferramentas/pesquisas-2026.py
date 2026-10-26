"""P3 em 2026: as pesquisas do 2º turno divulgadas na última semana (fim do campo de 18 a 24/10), lidas da tabela da
Wikipédia em inglês (captura em dados/capturas/wikipedia-pesquisas-2026-raw.wikitext, com a fonte original de cada
pesquisa na própria linha). Por instituto, a última pesquisa; a parte de cada candidato entre os dois.

Saída: resultados/p3_2026.json e resultados/p3_2026_pesquisas.csv
"""
import csv, hashlib, json, re
from pathlib import Path

R = Path(__file__).resolve().parents[1]
CAP = R / "dados/capturas/wikipedia-pesquisas-2026-raw.wikitext"
URNA_LULA = 64256232 / (64256232 + 59826041) * 100


def limpo(c):
    c = re.sub(r"^\s*\|\s*", "", c)
    c = re.sub(r'^style="[^"]*"\s*\|', "", c).strip()
    return re.sub(r"''", "", c).strip()


def main():
    txt = CAP.read_text(encoding="utf-8")
    seg = txt[txt.index("==Second round=="):]
    seg = seg[seg.index("Opinion polls") if "Opinion polls" in seg else 0:]
    linhas = []
    for bloco in seg.split("\n|-")[1:]:
        cel = [limpo(c) for c in bloco.strip().split("\n") if c.startswith("|")]
        if len(cel) < 8 or not re.search(r"\d+\s*Oct", cel[1] or "") or "2026" in cel[1]:
            continue  # "24 October 2026" é a tabela dos agregadores, não pesquisa
        dia = re.findall(r"(\d+)\s*Oct", cel[1])
        try:
            lula, flavio = float(cel[2].replace(",", ".")), float(cel[3].replace(",", "."))
        except ValueError:
            continue
        fonte = re.search(r"url=([^ |}]+)", bloco)
        nome = {"Verita": "Veritá"}.get(cel[0], cel[0])
        linhas.append({"instituto": nome, "campo": cel[1], "fim_campo_dia": int(dia[-1]), "lula": lula, "flavio": flavio,
                       "lula_valido": round(lula / (lula + flavio) * 100, 2), "fonte": fonte.group(1) if fonte else ""})
    semana = [x for x in linhas if 18 <= x["fim_campo_dia"] <= 24]
    ultima = {}
    for x in sorted(semana, key=lambda x: x["fim_campo_dia"]):
        ultima[x["instituto"]] = x
    u = list(ultima.values())
    media = sum(x["lula_valido"] for x in u) / len(u)
    out = {"captura_sha256": hashlib.sha256(CAP.read_bytes()).hexdigest(), "pesquisas_na_semana": len(semana), "institutos": len(u),
           "com_flavio_na_frente": sum(1 for x in u if x["flavio"] > x["lula"]), "com_lula_na_frente": sum(1 for x in u if x["lula"] > x["flavio"]),
           "empate": sum(1 for x in u if x["lula"] == x["flavio"]),
           "media_lula_valido": round(media, 2), "urna_lula_valido": round(URNA_LULA, 2), "erro_da_media_pontos_lula": round(URNA_LULA - media, 2),
           "erro_da_frente_pontos": round(2 * (URNA_LULA - media), 2),
           "ultima_de_cada_instituto": sorted(u, key=lambda x: x["lula_valido"])}
    with open(R / "resultados/p3_2026_pesquisas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys())); w.writeheader(); w.writerows(semana)
    (R / "resultados/p3_2026.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "ultima_de_cada_instituto"}, indent=1, ensure_ascii=False))
    for x in out["ultima_de_cada_instituto"]:
        print(x["instituto"], x["campo"], x["lula_valido"])


if __name__ == "__main__":
    main()
