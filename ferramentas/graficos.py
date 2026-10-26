"""Gráficos do vídeo, 1920x1080, só a partir de resultados/ e dados/derivados/. Saída: resultados/figuras/video/"""
from __future__ import annotations

import csv, json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1]
OUT = R / "resultados/figuras/video"
L, F, B, OK, SINAL = "#C8553D", "#2D6A8A", "#6B6B6B", "#3C8D5A", "#D9A31A"
FONTE = "Fonte: TSE (boletins, RDV e logs por seção) · github.com/Gabriel-Alexandre/investigacao-segundo-turno-2026 · análise feita pelo Claude"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 22, "axes.spines.top": False, "axes.spines.right": False})


def j(nome):
    return json.loads((R / "resultados" / nome).read_text(encoding="utf-8"))


def fig(titulo, sub=None):
    f = plt.figure(figsize=(19.2, 10.8), dpi=100)
    f.text(0.04, 0.93, titulo, fontsize=40, weight="bold")
    if sub:
        f.text(0.04, 0.885, sub, fontsize=24, color=B)
    f.text(0.04, 0.025, FONTE, fontsize=15, color=B)
    return f


def salvar(f, nome):
    OUT.mkdir(parents=True, exist_ok=True)
    f.savefig(OUT / nome)
    plt.close(f)


def mil(v):
    return f"{v / 1e6:.2f} mi".replace(".", ",")


def g01_conta():
    r3 = j("rodada3.json")["D1_saldo"]["brasil"]
    f = fig("De onde saíram os votos a mais no 2º turno", "saldo do 1º para o 2º turno, somando todas as seções")
    ax = f.add_axes([0.07, 0.14, 0.88, 0.68])
    itens = [("Votos dos outros\ncandidatos no 1º turno", r3["outros_1t"], B), ("Abstenção\nque caiu", r3["abstencao_caiu"], B),
             ("Branco e nulo\nque caíram", r3["branco_nulo_caiu"], B), ("Lula\nganhou", r3["lula_ganhou"], L), ("Flávio\nganhou", r3["flavio_ganhou"], F)]
    ax.bar([i[0] for i in itens], [i[1] for i in itens], color=[i[2] for i in itens])
    for k, (_, v, _) in enumerate(itens):
        ax.text(k, v * 1.02, mil(v), ha="center", fontsize=28, weight="bold")
    ax.set_yticks([])
    ax.axvline(2.5, color=B, lw=1, ls=":")
    salvar(f, "g01_a_conta_dos_votos.png")


def g02_origem():
    d = j("d2_transferencia.json")["2026_votos_do_2t_por_origem"]
    nomes = {"flavio": "Flávio (1º turno), trocou", "cury": "Augusto Cury", "renan": "Renan Santos", "caiado": "Ronaldo Caiado", "demais_1t": "Zema e demais",
             "bn_1t": "Branco e nulo", "abst_1t": "Não votou no 1º turno", "lula": "Lula (1º turno)"}
    f = fig("De onde vieram os votos de cada um no 2º turno", "transferência estimada seção a seção (inferência ecológica), com intervalo de 90%")
    ax = f.add_axes([0.25, 0.14, 0.7, 0.68])
    ordem = ["cury", "renan", "caiado", "demais_1t", "bn_1t", "abst_1t", "flavio"]
    y = np.arange(len(ordem))
    vl = [d["lula"][o]["votos"] for o in ordem]
    vf = [0 if o == "flavio" else d["flavio"][o]["votos"] for o in ordem]  # os votos que o Flávio manteve ficam fora: só o que mudou
    ax.barh(y + 0.2, vl, 0.4, color=L, label="foram para o Lula")
    ax.barh(y - 0.2, vf, 0.4, color=F, label="foram para o Flávio")
    for k, o in enumerate(ordem):
        ax.text(vl[k], k + 0.2, " " + mil(vl[k]), va="center", fontsize=18)
        ax.text(vf[k], k - 0.2, " " + mil(vf[k]), va="center", fontsize=18)
    ax.set_yticks(y)
    ax.set_yticklabels([nomes[o] for o in ordem])
    ax.set_xticks([])
    ax.legend(loc="lower right", frameon=False)
    salvar(f, "g02_de_onde_vieram.png")


def g03_curva():
    v = pd.read_csv(R / "resultados/d5_reconstruida.csv", parse_dates=["gerado"])
    f = fig("A noite da apuração", "vantagem do Lula em pontos, versão a versão do arquivo oficial do TSE")
    ax = f.add_axes([0.08, 0.14, 0.88, 0.68])
    ax.plot(v.gerado, v.vantagem_lula, color=L, lw=4, label="arquivo oficial gravado ao vivo", drawstyle="steps-post")
    ax.plot(v.gerado, v.vant_reconstruida, color=B, lw=2, ls="--", label="refeita pela hora de cada boletim", drawstyle="steps-post")
    ax.axhline(0, color="black", lw=1)
    ax.axvspan(pd.Timestamp("2026-10-25 17:07"), pd.Timestamp("2026-10-25 19:02"), color=SINAL, alpha=0.2)
    ax.text(pd.Timestamp("2026-10-25 17:15"), 10, "pausa: votação\nprorrogada até 19h", fontsize=20)
    ax.set_ylim(-5, 16)
    ax.set_xlim(pd.Timestamp("2026-10-25 17:00"), pd.Timestamp("2026-10-25 23:40"))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Hh%M"))
    ax.legend(frameon=False, loc="upper right")
    salvar(f, "g03_a_noite.png")


def g04_testes():
    r2, r3 = j("rodada2.json"), j("rodada3.json")
    linhas = [("RDV contra boletim (Lula e Flávio)", "499.177 de 499.177 seções iguais", OK),
              ("Log contra boletim", f'{r2["A5_log_contra_boletim"]["pct"]:.2f}% diferentes, quase todas urna trocada'.replace(".", ","), OK),
              ("Votos depois das 17h", f'{r2["A6_votos_depois_das_17h"]["votos_depois_17h"]:,} votos'.replace(",", ".") + f' = {r2["A6_votos_depois_das_17h"]["teto_contra_margem_pct"]}% da margem'.replace(".", ","), OK),
              ("Votos em rajada / sem digital", "mesmo padrão nos dois lados", OK),
              ("Votos sem origem na seção", (f'sinal: {r3["A1_votos_sem_origem"]["excesso_lula"]/1000:.0f} mil votos, ' + f'{r3["A1_votos_sem_origem"]["excesso_lula_contra_margem_pct"]}% da margem'.replace(".", ",")) if r3["A1_votos_sem_origem"]["sinal"] else "não encontrado", SINAL if r3["A1_votos_sem_origem"]["sinal"] else OK),
              ("Votos que somem", "sinal" if r3["A2_votos_que_somem"]["sinal"] else "não encontrado", SINAL if r3["A2_votos_que_somem"]["sinal"] else OK),
              ("Enchimento de urna", f'sinal: {r3["A3_enchimento"]["dessas_lula_acima_80"]} seções; 2022 não tinha a assimetria' if r3["A3_enchimento"]["sinal"] else "não encontrado", SINAL if r3["A3_enchimento"]["sinal"] else OK),
              ("Boletins da pausa e do fim da noite", "sinal" if r3["A8_pausa_e_cauda"]["sinal"] else "não encontrado", SINAL if r3["A8_pausa_e_cauda"]["sinal"] else OK),
              ("Urnas trocadas", "sinal" if r3["A9_urna_trocada"]["sinal"] else "não encontrado", SINAL if r3["A9_urna_trocada"]["sinal"] else OK),
              ("Seções com mais de 95%", f'sinal: {r3["A10_unanimidades"]["lula_acima_95_2t_2026"]:,} contra {r3["A10_unanimidades"]["flavio_acima_95_2t_2026"]}; 2022 teve {r3["A10_unanimidades"]["lula_acima_95_2t_2022"]:,}'.replace(",", ".") if r3["A10_unanimidades"]["sinal"] else "não encontrado", SINAL if r3["A10_unanimidades"]["sinal"] else OK)]
    f = fig("Os testes de quem procura a fraude", "cada um com o limite escrito antes de abrir as seções")
    for k, (t, res, c) in enumerate(linhas):
        y = 0.80 - k * 0.064
        f.text(0.05, y, t, fontsize=26)
        f.text(0.52, y, res, fontsize=24, color=c, weight="bold")
    salvar(f, "g04_testes_da_acusacao.png")


def g05_pesquisas():
    p = j("p3_2026.json")
    u = p["ultima_de_cada_instituto"]
    f = fig("As pesquisas da última semana contra a urna", "parte do Lula nos votos dos dois, última pesquisa de cada instituto")
    ax = f.add_axes([0.25, 0.12, 0.7, 0.72])
    y = np.arange(len(u))
    ax.scatter([x["lula_valido"] for x in u], y, s=180, color=[L if x["lula_valido"] > 50 else F for x in u])
    ax.axvline(p["urna_lula_valido"], color=L, lw=4)
    ax.text(p["urna_lula_valido"], len(u) - 0.5, f' urna: {p["urna_lula_valido"]:.2f}%'.replace(".", ","), color=L, fontsize=24, weight="bold")
    ax.axvline(50, color=B, lw=1, ls=":")
    ax.set_yticks(y)
    ax.set_yticklabels([x["instituto"] for x in u], fontsize=17)
    ax.set_xlim(46, 53)
    salvar(f, "g05_pesquisas_contra_a_urna.png")


def g06_probabilidade():
    h, p6, p7, pm = j("p_historico.json"), j("p6_outros_paises.json"), j("p7_probabilidade.json"), j("p4_polymarket.json")
    c = p7["componentes"]
    itens = [("Presidente no Brasil: o líder do 1º turno perdeu", "0 em 7; estimativa de Laplace", c["virada_presidente_laplace"]),
             ("Governador no Brasil, disputa apertada", f'{h["P2_governador"]["perto_frente_ate_3_e_lider_abaixo_50"]["viradas"]} em {h["P2_governador"]["perto_frente_ate_3_e_lider_abaixo_50"]["n"]}', h["P2_governador"]["perto_frente_ate_3_e_lider_abaixo_50"]["taxa"]),
             ("Outros países, disputa apertada", f'{p6["frente_ate_3_e_lider_abaixo_50"]["viradas"]} em {p6["frente_ate_3_e_lider_abaixo_50"]["n"]}', p6["frente_ate_3_e_lider_abaixo_50"]["viradas"] / p6["frente_ate_3_e_lider_abaixo_50"]["n"]),
             ("Polymarket: favorito de 75% a 85% perdeu", f'{c["favorito_polymarket_75_a_85_perdeu_antes_de_2026_10_24"]["perdeu"]} em {c["favorito_polymarket_75_a_85_perdeu_antes_de_2026_10_24"]["de"]}', c["favorito_polymarket_75_a_85_perdeu_antes_de_2026_10_24"]["taxa"]),
             ("Líder do 1º turno e das pesquisas perdeu (Brasil)", "1 em 30", c["lider_1t_e_pesquisas_perdeu_2014_2022"]),
             ("Tudo junto, como se fosse independente", "cerca de 1 em 360", p7["a_independente_presidente_x_polymarket_x_minas"])]
    f = fig("Quão raro foi o que aconteceu", "cada conta com a sua base; nenhuma delas, sozinha, diz se houve fraude")
    ax = f.add_axes([0.42, 0.12, 0.53, 0.72])
    y = np.arange(len(itens))[::-1]
    ax.barh(y, [i[2] * 100 for i in itens], color=[B, B, B, B, SINAL, SINAL])
    for k, it in zip(y, itens):
        ax.text(it[2] * 100 + 1, k, f'{it[2] * 100:.1f}%'.replace(".", ",") + f"  ({it[1]})", va="center", fontsize=20)
        f.text(0.04, 0.12 + (k + 0.4) * 0.72 / len(itens), it[0], fontsize=19)
    ax.set_yticks([])
    ax.set_xlim(0, 80)
    ax.set_xticks([])
    salvar(f, "g06_quao_raro.png")


def g07_polymarket():
    pm = j("p4_polymarket.json")
    fx = pm["por_preco_do_favorito"]
    nomes = {"50_a_65": "50% a 65%", "65_a_75": "65% a 75%", "75_a_85": "75% a 85%", "85_ou_mais": "85% ou mais"}
    f = fig("A Polymarket acerta?", f'o favorito da véspera ganhou {pm["favorito_ganhou"]} de {pm["eleicoes"]} eleições nacionais (jan/2024 a out/2026)')
    ax = f.add_axes([0.08, 0.14, 0.88, 0.66])
    ks = list(fx)
    ac = [fx[k]["favorito_ganhou"] / fx[k]["eleicoes"] * 100 for k in ks]
    ax.bar([nomes[k] for k in ks], ac, color=[B, B, SINAL, B])
    for i, k in enumerate(ks):
        ax.text(i, ac[i] + 1.5, f'{fx[k]["favorito_ganhou"]} de {fx[k]["eleicoes"]}', ha="center", fontsize=26, weight="bold")
    ax.set_ylim(0, 110)
    ax.set_ylabel("o favorito ganhou (%)")
    ax.set_xlabel("preço do favorito na véspera (o Flávio estava em 76,6%)")
    salvar(f, "g07_polymarket.png")


def g08_cidades():
    m = pd.read_csv(R / "resultados/d4_municipios.csv", dtype={"municipio": str})
    f2l = m[(m.venc1 == "flavio") & (m.venc2 == "lula")]
    l2f = m[(m.venc1 == "lula") & (m.venc2 == "flavio")]
    cont = f2l.uf.str.upper().value_counts().head(12)
    f = fig("As cidades que viraram", f"{len(f2l)} municípios foram do Flávio para o Lula; {len(l2f)} foram do Lula para o Flávio")
    ax = f.add_axes([0.08, 0.14, 0.88, 0.66])
    ax.bar(cont.index, cont.values, color=L)
    for i, v in enumerate(cont.values):
        ax.text(i, v + 1, str(v), ha="center", fontsize=22)
    ax.set_ylabel("municípios que viraram para o Lula")
    salvar(f, "g08_cidades_que_viraram.png")


def g09_digital():
    d = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
    for c in ["aptos", "comparecimento", "bu_lula", "bu_flavio"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d[(d.aptos >= 50)].dropna(subset=["bu_lula"])
    a = pd.read_parquet(R / "dados/derivados/s2022_t2.parquet")
    a = a[a.aptos >= 50]
    f = fig("A impressão digital do comparecimento", "cada ponto é uma seção; enchimento de urna aparece no canto de cima, nos extremos")
    for k, (t, c, v) in enumerate([("2º turno de 2022", a.comparecimento / a.aptos * 100, a.lula / (a.lula + a.bolsonaro) * 100),
                                   ("2º turno de 2026", d.comparecimento / d.aptos * 100, d.bu_lula / (d.bu_lula + d.bu_flavio) * 100)]):
        ax = f.add_axes([0.07 + k * 0.47, 0.14, 0.42, 0.66])
        ax.hist2d(v.clip(0, 100), c.clip(0, 100), bins=100, range=[[0, 100], [40, 100]], cmap="Greys", norm=matplotlib.colors.LogNorm())
        ax.set_title(t, fontsize=26)
        ax.set_xlabel("Lula (% dos votos dos dois)")
        ax.set_ylabel("comparecimento (%)")
    salvar(f, "g09_impressao_digital.png")


def g10_votos_livres():
    d = pd.read_csv(R / "resultados/rodada4_por_ano.csv")
    d = d[d.ano != 2006]  # 2006: o adversário perdeu votos (126% para o PT), fora da escala; dito na nota
    f = fig("Para onde foram os votos livres, eleição por eleição", "parte do PT no que estava livre entre os turnos; embaixo, quem os eliminados apoiaram (2006, fora: 126%)")
    ax = f.add_axes([0.08, 0.16, 0.88, 0.64])
    cores = [L if a == 2026 else (F if a == 2022 else B) for a in d.ano]
    ax.bar(d.ano.astype(str), d.parte_do_pt_nos_votos_livres_pct, color=cores)
    rot = {2002: "apoiaram o PT", 2010: "neutros", 2014: "apoiaram o adversário", 2018: "neutros", 2022: "apoiaram o PT", 2026: "apoiaram o adversário"}
    for i, (a, v) in enumerate(zip(d.ano, d.parte_do_pt_nos_votos_livres_pct)):
        ax.text(i, v + 1.5, f"{v:.0f}%", ha="center", fontsize=28, weight="bold")
        ax.text(i, -9, rot[a], ha="center", fontsize=16, color=B)
    ax.axhline(50, color=B, lw=1, ls=":")
    ax.set_ylim(-12, 90)
    ax.set_yticks([])
    salvar(f, "g10_votos_livres_e_apoios.png")


def g11_abstencao():
    d = pd.read_csv(R / "resultados/rodada4_por_ano.csv")
    f = fig("A abstenção do 1º para o 2º turno", "em pontos; em todas as eleições até 2018 ela subiu no 2º turno")
    ax = f.add_axes([0.08, 0.14, 0.88, 0.66])
    v = d.abstencao_variou_pontos
    ax.bar(d.ano.astype(str), v, color=[L if a == 2026 else B for a in d.ano])
    for i, x in enumerate(v):
        ax.text(i, x + (0.12 if x > 0 else -0.35), f"{x:+.1f}".replace(".", ","), ha="center", fontsize=26, weight="bold")
    ax.axhline(0, color="black", lw=1)
    ax.set_yticks([])
    salvar(f, "g11_abstencao_entre_turnos.png")


def main():
    for g in (g01_conta, g02_origem, g03_curva, g04_testes, g05_pesquisas, g06_probabilidade, g07_polymarket, g08_cidades, g09_digital, g10_votos_livres, g11_abstencao):
        try:
            g()
            print("ok", g.__name__)
        except Exception as e:  # noqa: BLE001
            print("ERRO", g.__name__, repr(e))


if __name__ == "__main__":
    main()
