"""P4 (curadoria): de polymarket_favoritos.csv, fica uma linha por eleição nacional, no mercado de quem vence.

Regras (todas aplicadas por código; o motivo de cada exclusão vai para a tabela):
  1. Sai o que não é "quem vence a eleição nacional": comparação "X ou Y", "quais partidos entram", disputa interna de
     partido, eleição especial de um distrito, eleição estadual ou regional, apoio de candidato, candidato de partido
     para eleição futura, e mercado cujo favorito ou vencedor é "Other" ou uma pergunta.
  2. Primeiro-ministro "depois da eleição" conta só se não houver mercado de vencedor da mesma eleição; primeiro-ministro
     sem eleição (escolha do parlamento ou do presidente) sai.
  3. Uma por eleição: mesmo país com véspera a menos de 10 dias = a mesma eleição (fica o mercado de vencedor).
     1º turno e resultado final contam separados quando a véspera de cada um cai em votações diferentes.
Saída: dados/derivados/polymarket_eleicoes.csv e resultados/p4_polymarket.json
"""
import csv, json, re
from datetime import datetime
from pathlib import Path

R = Path(__file__).resolve().parents[1]
FORA = [
    (r"more-votes-to|-vs-|-or-", "comparação entre dois partidos"),
    (r"which-parties|enter-parliamen", "quais partidos entram"),
    (r"leadership|deputy-leadership|national-rally-candidate", "disputa interna de partido"),
    (r"special-election|^ga-1|^nj-1|^ca-0|^ca-1|^texas", "eleição especial de um distrito"),
    (r"sachsen|mecklenburg|rhineland|negeri|oblast|gubernatorial|ngatangiia|bc-conservative", "eleição estadual, regional ou de distrito"),
    (r"endorse", "apoio de candidato"),
    (r"^portugal-legislative-election$", "pergunta de porcentagem, não de vencedor"),
    (r"^next-french-prime-minister|^next-prime-minister-of-vietnam|^next-prime-minister-of-kosovo|-invested$|^next-prime-minister-of-romania|^party-of-next-prime-minister-of-romania|^next-japanese-prime-minister|^next-chancellor-of-germany", "chefe de governo escolhido sem eleição naquele momento"),
]
ALIAS = {"presidential": "united", "which": "united", "2024": "ireland", "irish": "ireland", "prime": None, "next": None, "party": None,
         "thai": "thailand", "latvian": "latvia", "slovenian": "slovenia", "mexican": "mexico", "2026": "malaysia", "sao": "sao-tome", "uk": "uk"}


def pais(slug: str) -> str:
    s = re.sub(r"^(next-prime-mini?ste?r-of-(the-)?|party-of-next-prime-minister-of-|prime-minister-of-|which-party-wins-|which-party-will-win-the-\d+-)", "", slug)
    t = s.split("-")[0]
    if slug.startswith("presidential-election-winner-2024") or slug.startswith("which-party-will-win-the-2024-united"):
        return "united"
    return ALIAS.get(t, t) or t


def main():
    linhas = list(csv.DictReader(open(R / "dados/derivados/polymarket_favoritos.csv", encoding="utf-8")))
    saida = []
    for x in linhas:
        motivo = ""
        for pat, m in FORA:
            if re.search(pat, x["slug"]):
                motivo = m
                break
        fav, ven = x["favorito"] or "", x["vencedor"] or ""
        if not motivo and (fav in ("Other", "", "nan") or ven in ("Other", "", "nan") or "?" in fav or ">" in fav):
            motivo = "favorito ou vencedor é 'Other' ou uma pergunta"
        x["pais"] = pais(x["slug"])
        x["chefe_de_governo"] = int(bool(re.match(r"^(next-prime|prime-minister|party-of-next|pakistan-election)", x["slug"])))
        x["fora"] = motivo
        saida.append(x)
    # 2 e 3: uma por eleição. Preferência: presidente > vencedor da eleição parlamentar > chefe de governo
    def nivel(x):
        if "presidential" in x["slug"] or "president" in x["slug"]:
            return 0
        return 2 if x["chefe_de_governo"] else 1
    def turno1(x):
        return "1st-round" in x["slug"] or "first-round" in x["slug"]
    validas = sorted([x for x in saida if not x["fora"]], key=lambda x: (x["pais"], x["vespera_utc"]))
    for x in validas:
        if x["fora"]:
            continue
        for y in validas:
            if y is x or y["fora"] or y["pais"] != x["pais"]:
                continue
            d = (datetime.fromisoformat(x["vespera_utc"]) - datetime.fromisoformat(y["vespera_utc"])).days
            # mesma votação: mesmo país e véspera a menos de 10 dias (se forem 1º turno e resultado final no mesmo
            # momento, fica o resultado final); chefe de governo até 200 dias de um vencedor parlamentar = mesma eleição
            mesma = abs(d) < 10 or (nivel(x) == 2 and nivel(y) == 1 and abs(d) <= 200)
            pior = (nivel(x), turno1(x)) >= (nivel(y), turno1(y))
            if mesma and pior:
                x["fora"] = "a mesma eleição já está em outro mercado"
                break
    final = [x for x in saida if not x["fora"]]
    with open(R / "dados/derivados/polymarket_eleicoes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(saida[0].keys()))
        w.writeheader()
        w.writerows(sorted(saida, key=lambda x: x["vespera_utc"]))
    n = len(final)
    a = sum(int(x["acertou"]) for x in final)
    def faixa(lo, hi):
        g = [x for x in final if lo <= float(x["preco_favorito"]) < hi]
        return {"eleicoes": len(g), "favorito_ganhou": sum(int(x["acertou"]) for x in g)}
    erros = [{"eleicao": x["slug"], "vespera_utc": x["vespera_utc"], "favorito": x["favorito"], "preco": float(x["preco_favorito"]), "vencedor": x["vencedor"]}
             for x in final if x["acertou"] == "0"]
    out = {"eleicoes": n, "favorito_ganhou": a, "taxa": round(a / n, 4),
           "por_preco_do_favorito": {"50_a_65": faixa(0, 0.65), "65_a_75": faixa(0.65, 0.75), "75_a_85": faixa(0.75, 0.85), "85_ou_mais": faixa(0.85, 1.01)},
           "erros": sorted(erros, key=lambda e: e["vespera_utc"])}
    (R / "resultados/p4_polymarket.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
