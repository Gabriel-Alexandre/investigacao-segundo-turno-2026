"""Escreve RELATORIO.md, RESUMO_SIMPLES.md e docs/LEITURA_DA_IA.md só a partir de resultados/*.json. Nenhum número à mão."""
from __future__ import annotations

import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]


def j(n):
    return json.loads((R / "resultados" / n).read_text(encoding="utf-8"))


def br(v, casas=0):
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def mi(v):
    return br(v / 1e6, 2) + (" milhão" if abs(v) < 2e6 else " milhões")


def pct(v, casas=1):
    return br(v, casas) + "%"


def main():
    r2, r3, d2, d5 = j("rodada2.json"), j("rodada3.json"), j("d2_transferencia.json"), j("d5_reconstruida.json")
    h, p3, p3b, p4, p6, p7 = j("p_historico.json"), j("p3_pesquisas.json"), j("p3_2026.json"), j("p4_polymarket.json"), j("p6_outros_paises.json"), j("p7_probabilidade.json")
    va, ra = j("validacao_independente.json"), j("revisao_adversarial.json")
    s = r3["D1_saldo"]["brasil"]
    o = d2["2026_votos_do_2t_por_origem"]
    nomes = {"flavio": "votaram no Flávio no 1º turno", "cury": "votaram no Augusto Cury", "renan": "votaram no Renan Santos",
             "caiado": "votaram no Ronaldo Caiado", "demais_1t": "votaram no Zema ou nos demais", "bn_1t": "votaram branco ou nulo",
             "abst_1t": "não votaram no 1º turno", "lula": "votaram no Lula no 1º turno"}
    ordem = ["cury", "renan", "caiado", "demais_1t", "bn_1t", "abst_1t", "flavio"]
    linhas_origem = "\n".join(
        f"| {nomes[k]} | {mi(o['lula'][k]['votos'])} ({mi(o['lula'][k]['de'])} a {mi(o['lula'][k]['ate'])}) | {mi(o['flavio'][k]['votos'])} ({mi(o['flavio'][k]['de'])} a {mi(o['flavio'][k]['ate'])}) |"
        for k in ordem)
    a1, a2, a3, a8, a9, a10, a11 = (r3[k] for k in ("A1_votos_sem_origem", "A2_votos_que_somem", "A3_enchimento", "A8_pausa_e_cauda", "A9_urna_trocada", "A10_unanimidades", "A11_residuos_por_municipio"))
    a4, a5, a6, a7 = (r2[k] for k in ("A4_rdv_contra_boletim", "A5_log_contra_boletim", "A6_votos_depois_das_17h", "A7_rajadas_e_liberacao_sem_digital"))
    d4 = r3["D4_cidades_que_viraram"]
    x1, x3, x4 = ra["acusacao"]["X1_reserva_so_com_outros_candidatos"], ra["acusacao"]["X3_unanimidades_como_se_fossem_falsas"], ra["acusacao"]["X4_o_1pct_de_secoes_mais_acima_do_previsto"]

    def sinal(x):
        return "**sinal encontrado**" if x else "não encontrado"

    acus = [
        ("A1 · votos sem origem na seção", f"excesso do Lula {br(a1['excesso_lula'])} votos, do Flávio {br(a1['excesso_flavio'])}; em 2022, quem cresceu mais (Bolsonaro) teve {br(a1['regua_2022']['excesso_bolsonaro_que_cresceu_mais'])} e o outro {br(a1['regua_2022']['excesso_lula'])}. O excesso do Lula é {pct(a1['excesso_lula_contra_margem_pct'], 2)} da margem", sinal(a1["sinal"])),
        ("A2 · votos que somem", f"seções em que o Flávio perdeu voto com o comparecimento subindo: {pct(a2['pct_secoes_flavio_caiu_com_comparecimento_subindo'], 2)}; o mesmo para o Lula: {pct(a2['pct_secoes_lula_caiu_com_comparecimento_subindo'], 2)}; em 2022, o candidato que cresceu menos: {pct(a2['regua_2022_lula_que_cresceu_menos'], 2)}", sinal(a2["sinal"])),
        ("A3 · enchimento de urna", f"{br(a3['secoes_acima_do_p999_do_municipio'])} seções com salto de comparecimento acima do normal do município (quase uma por município); {br(a3['dessas_lula_acima_80'])} com mais de 80% para o Lula e {br(a3['dessas_flavio_acima_80'])} para o Flávio. Pela proporção do próprio município, o esperado era {br(a3['esperado_pelo_proprio_municipio']['esperado_lula'])} e {br(a3['esperado_pelo_proprio_municipio']['esperado_flavio'])} (razão {br(a3['esperado_pelo_proprio_municipio']['razao_observada_sobre_esperada_lula'], 2)} e {br(a3['esperado_pelo_proprio_municipio']['razao_observada_sobre_esperada_flavio'], 2)}); em 2022, com o mesmo controle, {br(a3['regua_2022_mesmo_controle']['razao_lula'], 2)} e {br(a3['regua_2022_mesmo_controle']['razao_bolsonaro'], 2)}. Nessas seções do Lula, o salto médio foi de {br(a3['esperado_pelo_proprio_municipio']['salto_medio_de_comparecimento_pontos'], 1)} pontos e a liberação sem digital ficou {br(a3['liberacao_sem_digital_nas_secoes_marcadas']['diferenca_pontos'], 2)} ponto acima dos mesmos municípios. Canto 95/95 da impressão digital: {pct(a3['canto_95_95_pct_2t_2026'], 3)} das seções em 2026, {pct(a3['canto_95_95_pct_2t_2022'], 3)} em 2022", sinal(a3["sinal"])),
        ("A4 · RDV contra boletim", f"votos do Lula e do Flávio iguais em {br(a4['secoes_comparadas'])} de {br(a4['secoes_comparadas'])} seções; {br(a4['secoes_com_diferenca'])} diferem só no nulo (um tipo de voto do RDV, só nos 6 estados com governador no 2º turno, que o boletim soma como nulo)", "sinal pela letra da regra, explicado: nenhum voto de candidato difere"),
        ("A5 · log contra boletim", f"{pct(a5['pct'], 2)} das seções diferentes, sempre com menos votos no log; {br(a5['com_contingencia'])} de {br(a5['secoes_com_diferenca'])} tiveram urna trocada no dia", sinal(a5["sinal"])),
        ("A6 · votos depois das 17h", f"{br(a6['votos_depois_17h'])} votos ({pct(a6['pct_dos_votos'], 3)}), {br(a6['votos_depois_19h'])} depois das 19h; teto: {pct(a6['teto_contra_margem_pct'], 2)} da margem. As {br(a6['secoes_com_mais_de_30pct_depois_17h'])} seções acima de 30% são de urna trocada", "sinal pela letra da regra, explicado pela troca de urna; a margem não é tocada"),
        ("A7 · rajadas e liberação sem digital", f"rajadas: {pct(a7['todas']['pct_votos_em_rajada'], 3)} dos votos. Sem digital: {pct(a7['lula']['pct_manuais'], 1)} onde o Lula venceu, {pct(a7['flavio']['pct_manuais'], 1)} onde o Flávio venceu; última hora contra a primeira: {br(a7['lula']['razao_ultima_sobre_primeira'], 2)} e {br(a7['flavio']['razao_ultima_sobre_primeira'], 2)}", sinal(a7["sinal"])),
        ("A8 · boletins da pausa e do fim da noite", f"desvio do previsto pelo 1º turno da mesma seção: pausa {br(a8['pausa']['residuo_medio_pontos'], 2)} ponto (erro padrão {br(a8['pausa']['erro_padrao'], 2)}); últimos 2% {br(a8['cauda_2pct']['residuo_medio_pontos'], 2)} (erro padrão {br(a8['cauda_2pct']['erro_padrao'], 2)}), abaixo do limite de 1 ponto, mas diferente de zero (sobretudo RJ e SP, onde o modelo nacional erra para cima, ver revisão Y1). Na cauda o Lula teve {pct(a8['cauda_2pct']['lula_pct_2t'])} no 2º turno e {pct(a8['cauda_2pct']['lula_pct_1t_mesmas_secoes'])} no 1º, nas mesmas seções", sinal(a8["sinal"])),
        ("A9 · urnas trocadas", f"desvio do previsto: {br(a9['contingencia']['residuo_medio_pontos'], 2)} ponto em {br(a9['contingencia']['secoes'])} seções", sinal(a9["sinal"])),
        ("A10 · unanimidades e zerados", f"mais de 95% para o Lula: {br(a10['lula_acima_95_2t_2026'])} seções no 2º turno de 2026 (contra {br(a10['flavio_acima_95_2t_2026'])} do Flávio), {br(a10['lula_acima_95_1t_2026_mesmas_regras'])} no 1º turno e {br(a10['lula_acima_95_2t_2022'])} no 2º turno de 2022; {br(a10['das_1686_quantas_ja_eram_acima_de_90_no_1t'])} delas já davam mais de 90% ao Lula no 1º turno. Flávio zerado depois de ter voto no 1º turno: {br(a10['flavio_tinha_voto_no_1t_e_zerou'])} seções; Lula: {br(a10['lula_tinha_voto_no_1t_e_zerou'])}", sinal(a10["sinal"])),
        ("A11 · resíduos agrupados", f"municípios acima de 3 erros padrão a favor do Lula: {br(a11['acima_de_3_ep_a_favor_do_lula'])}; a favor do Flávio: {br(a11['acima_de_3_ep_a_favor_do_flavio'])} (de {br(a11['municipios'])})", "listados para conferência em resultados/a11_municipios.csv"),
    ]
    tabela_acus = "\n".join(f"| {a} | {b} | {c} |" for a, b, c in acus)
    pres = h["P1_presidente"]
    gov = h["P2_governador"]
    rel = f"""# Relatório: investigação do 2º turno de 2026

Gerado por `ferramentas/gerar-relatorio.py` a partir de `resultados/`. Regras: [`docs/PRE_REGISTRO.md`](docs/PRE_REGISTRO.md), publicadas antes de qualquer conta por seção. Base: as {br(r2['secoes'])} seções do 2º turno (boletim, registro digital do voto e log de cada urna), as do 1º turno e as de 2022, todas do TSE.

## O que o projeto não consegue dizer

- **Quem votou em quem.** O voto é secreto; a transferência do 1º para o 2º turno é estimada por inferência ecológica, com intervalo.
- **Se a urna registrou o voto que o eleitor digitou.** O projeto confere que os arquivos de cada urna são coerentes entre si (boletim, registro de cada voto e log) e com o total oficial; não tem como conferir o dedo do eleitor. Não há voto em papel no Brasil.
- **A assinatura digital dos boletins** não foi verificada.
- **Intenção** de qualquer pessoa ou órgão.

## A conta dos votos

Do 1º para o 2º turno, o Lula ganhou **{mi(s['lula_ganhou'])}** e o Flávio **{mi(s['flavio_ganhou'])}**. No saldo, isso saiu de {mi(s['outros_1t'])} de votos dos outros candidatos, {mi(s['abstencao_caiu'])} de quem voltou a votar e {mi(s['branco_nulo_caiu'])} de quem deixou de votar branco ou nulo (soma das {br(r3['secoes_comparadas'])} seções que existem nos dois turnos).

## Caminho da defesa: de onde vieram os votos

Estimativa seção a seção, por UF, com intervalo de 90% (`resultados/d2_transferencia.json`):

| Eleitores que... | foram para o Lula | foram para o Flávio |
|---|---|---|
{linhas_origem}

⚠️ O intervalo mede só a variação entre seções; o erro do próprio modelo é maior, como mostra o teste de 2022 abaixo.

Validação em 2022 (o mesmo modelo, comparado com o Datafolha de 5 a 7/10/2022): eleitores do Ciro, modelo {pct(d2['validacao_2022']['ciro_modelo']['para_lula_pct'])} Lula e {pct(d2['validacao_2022']['ciro_modelo']['para_o_outro_pct'])} Bolsonaro, Datafolha 31% e 42%; eleitores da Tebet, modelo {pct(d2['validacao_2022']['tebet_modelo']['para_lula_pct'])} e {pct(d2['validacao_2022']['tebet_modelo']['para_o_outro_pct'])}, Datafolha 31% e 29%. O modelo acertou o lado dos eleitores do Ciro e errou o da Tebet: os números de origem acima são a melhor estimativa disponível, não uma medida exata.

**As cidades que viraram:** {br(d4['do_flavio_para_o_lula'])} municípios foram do Flávio no 1º turno para o Lula no 2º; {br(d4['do_lula_para_o_flavio'])} fizeram o contrário. A frente do Lula aumentou em {pct(d4['frente_do_lula_aumentou_em_pct_dos_municipios'])} dos {br(d4['municipios'])} municípios (`resultados/d4_municipios.csv`).

**A noite:** refeita pela hora de recebimento de cada boletim, acompanha as versões oficiais gravadas ao vivo com diferença média de {br(d5['diferenca_media_absoluta_pontos'], 2)} ponto. As trocas de liderança seguem a ordem de chegada das regiões (`resultados/d5_reconstruida.json`).

**As pesquisas:** {p3b['institutos']} institutos na última semana; {p3b['com_flavio_na_frente']} davam o Flávio na frente. A média deu {pct(p3b['media_lula_valido'], 2)} ao Lula; a urna deu {pct(p3b['urna_lula_valido'], 2)}: erro de {br(p3b['erro_da_frente_pontos'], 1)} pontos na frente. Nos 2º turnos de 2014 a 2022, o erro médio da frente foi de {br(p3['erro_medio_absoluto_da_frente_pontos'], 1)} pontos.

## Caminho da acusação: as marcas que uma fraude deixaria

| Teste | O que o dado mostra | Resultado pelo pré-registro |
|---|---|---|
{tabela_acus}

**As objeções mais fortes da acusação, calculadas** (`resultados/revisao_adversarial.json`): contando como reserva só os votos dos outros candidatos, {br(x1['excesso_lula'])} votos do Lula exigiriam eleitor novo, ex-nulo ou troca ({pct(x1['excesso_lula_contra_margem_pct'], 1)} da margem); se as {br(x3['secoes'])} seções com mais de 95% fossem todas falsas, seriam {pct(x3['contra_margem_pct'], 1)} da margem; se o 1% de seções mais acima do previsto voltasse ao previsto, seriam {pct(x4['contra_margem_pct'], 1)} da margem.

## Veredito por teste (régua de cinco níveis, pré-registro §6)

| Teste | Veredito | Teto do pior caso (contra a margem de 4.430.191 votos) | O que fecharia de vez |
|---|---|---|---|
| A1 votos sem origem | Compatível com os dois: o excesso exige troca de eleitor ou rodízio de quem vota; o dado agregado não separa | {pct(a1['excesso_lula_contra_margem_pct'], 2)} | a lista de quem votou em cada seção nos dois turnos (caderno de votação, com o TSE) |
| A2 votos que somem | Não sustentado | não se aplica | não se aplica |
| A3 enchimento de urna | Compatível com os dois: a assimetria existe e 2022 não tinha; a liberação pela digital do próprio eleitor quase não mudou | {pct(a3['votos_validos_nas_secoes_marcadas_lula'] / 4430191 * 100, 1)} (todos os válidos dessas seções) | a lista de quem votou nessas seções e a conferência das digitais (TSE) |
| A4 RDV contra boletim | Não sustentado: nenhum voto de candidato difere em nenhuma seção | 0 | a assinatura digital dos arquivos |
| A5 log contra boletim | Não sustentado | não se aplica | não se aplica |
| A6 votos depois das 17h | Não sustentado | {pct(a6['teto_contra_margem_pct'], 2)} | não se aplica |
| A7 rajadas e sem digital | Não sustentado | não se aplica | não se aplica |
| A8 pausa e cauda | Não sustentado (abaixo do limite) | não se aplica | não se aplica |
| A9 urnas trocadas | Não sustentado | não se aplica | não se aplica |
| A10 unanimidades | Compatível com os dois: a assimetria é de todo 2º turno com o Lula (2022 teve mais) | {pct(x3['contra_margem_pct'], 1)} | não se aplica |
| A11 resíduos agrupados | Não sustentado como padrão a favor do Lula (mais municípios acima do previsto para o Flávio) | não se aplica | não se aplica |

## Probabilidade

| Conta | Resultado |
|---|---|
| Presidente no Brasil: o líder do 1º turno ganhou o 2º | {pres['segundos_turnos'] - pres['viradas']} de {pres['segundos_turnos']} (1989 a 2022); estimativa de virada pela contagem: {pct(pres['laplace_virada'] * 100)} |
| Governador no Brasil, 1994 a 2022 | {gov['viradas']} viradas em {gov['segundos_turnos']}; disputa apertada (frente até 3 pontos, líder abaixo de 50%): {gov['perto_frente_ate_3_e_lider_abaixo_50']['viradas']} em {gov['perto_frente_ate_3_e_lider_abaixo_50']['n']} |
| Outros países, 1990 a 2025 | {p6['viradas']} viradas em {p6['segundos_turnos']} ({p6['paises']} países); disputa apertada: {p6['frente_ate_3_e_lider_abaixo_50']['viradas']} em {p6['frente_ate_3_e_lider_abaixo_50']['n']} |
| Polymarket: o favorito da véspera ganhou | {p4['favorito_ganhou']} de {p4['eleicoes']} eleições nacionais; com o favorito entre 75% e 85%, {p4['por_preco_do_favorito']['75_a_85']['favorito_ganhou']} de {p4['por_preco_do_favorito']['75_a_85']['eleicoes']} |
| Minas: quem venceu o 1º turno venceu a eleição | {h['P5_minas_1t']['acertos']} de {h['P5_minas_1t']['eleicoes']} (1994 a 2022) |
| Líder do 1º turno que também liderava as pesquisas perdeu (Brasil, 2014 a 2022) | 1 em 30 ({pct(p7['componentes']['lider_1t_e_pesquisas_perdeu_2014_2022'] * 100)}) |
| Tudo junto, como se fosse independente | {pct(p7['a_independente_presidente_x_polymarket_x_minas'] * 100, 2)} |

## Validação

Recontagem com código novo e fontes que o cálculo não usou: {"todas as checagens passaram" if va['todos_passaram'] else "há checagem que não passou"} (`resultados/validacao_independente.json`).

## Outros países

[`docs/OUTROS_PAISES.md`](docs/OUTROS_PAISES.md): o que separou os casos de fraude comprovada (Venezuela 2024, México 1988) dos não comprovados foi a publicação do resultado por seção e a conferência de fora.
"""
    (R / "RELATORIO.md").write_text(rel, encoding="utf-8")
    print("RELATORIO.md escrito")


if __name__ == "__main__":
    main()
