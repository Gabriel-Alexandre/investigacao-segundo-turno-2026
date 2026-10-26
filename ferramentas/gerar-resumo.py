"""Escreve RESUMO_SIMPLES.md, docs/LEITURA_DA_IA.md e docs/REVISAO_ADVERSARIAL.md a partir de resultados/*.json."""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]


def j(n):
    return json.loads((R / "resultados" / n).read_text(encoding="utf-8"))


def br(v, c=0):
    return f"{v:,.{c}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mi(v):
    return br(v / 1e6, 2) + (" milhão" if abs(v) < 2e6 else " milhões")


def main():
    r2, r3, d2, p3b, p4, p6, p7, h, ra, va = (j(n) for n in ("rodada2.json", "rodada3.json", "d2_transferencia.json", "p3_2026.json", "p4_polymarket.json",
                                                            "p6_outros_paises.json", "p7_probabilidade.json", "p_historico.json", "revisao_adversarial.json", "validacao_independente.json"))
    s = r3["D1_saldo"]["brasil"]
    o = d2["2026_votos_do_2t_por_origem"]["lula"]
    a1, a3, a10 = r3["A1_votos_sem_origem"], r3["A3_enchimento"], r3["A10_unanimidades"]
    novos = o["bn_1t"]["votos"] + o["abst_1t"]["votos"]
    outros = o["cury"]["votos"] + o["renan"]["votos"] + o["caiado"]["votos"] + o["demais_1t"]["votos"]
    resumo = f"""# Resumo simples

**A pergunta:** o Lula teve {mi(s['lula_ganhou'])} de votos a mais no 2º turno do que no 1º. De onde vieram, a apuração tem sinal de fraude, e quão raro foi o que aconteceu?

**Como foi feito:** todas as {br(r2['secoes'])} seções do 2º turno, com o boletim, o registro de cada voto (RDV) e o log de cada urna; as do 1º turno e as de 2022; o histórico do TSE desde 1989; as pesquisas; a Polymarket; e 180 segundos turnos de outros países. Dois caminhos com o mesmo peso: um procurando a explicação, outro procurando a fraude. As regras foram publicadas antes das contas.

## De onde vieram os votos (estimativa)

- **{mi(novos)}** de quem não votou ou votou branco e nulo no 1º turno ({mi(o['abst_1t']['votos'])} e {mi(o['bn_1t']['votos'])}).
- **{mi(outros)}** de quem votou nos outros candidatos: Cury {mi(o['cury']['votos'])}, Renan Santos {mi(o['renan']['votos'])}, Caiado {mi(o['caiado']['votos'])}.
- **{mi(o['flavio']['votos'])}** de quem tinha votado no Flávio.
- É uma estimativa por seção, sem saber o voto de ninguém; o teste em 2022 acertou um dos dois grupos que deu para conferir.

## O que a procura pela fraude achou

- **Nada nos arquivos das urnas:** o registro de cada voto bate com o boletim em todas as seções; o log bate com o boletim, tirando urnas trocadas no dia; os votos depois das 17h foram {br(r2['A6_votos_depois_das_17h']['votos_depois_17h'])}, menos de 1% da margem.
- **Três sinais passaram do limite escrito antes**, todos pequenos perto da margem de 4,43 milhões:
  - {br(a1['excesso_lula'])} votos do Lula que exigem eleitor trocando de lado ou rodízio de quem vota na seção ({br(a1['excesso_lula_contra_margem_pct'], 1)}% da margem);
  - {br(a3['dessas_lula_acima_80'])} seções com salto de comparecimento e mais de 80% para o Lula, mais do que o esperado, numa assimetria que 2022 não tinha; ali o voto a mais veio liberado pela digital do próprio eleitor;
  - {br(a10['lula_acima_95_2t_2026'])} seções com mais de 95% para o Lula contra {br(a10['flavio_acima_95_2t_2026'])} do Flávio, mas 2022 teve {br(a10['lula_acima_95_2t_2022'])} e quase todas já eram assim no 1º turno.
- Nenhum dos três separa fraude de comportamento do eleitor; o que separaria está com o TSE (a lista de quem votou em cada seção).

## Quão raro foi

- **Presidente no Brasil:** o líder do 1º turno nunca tinha perdido (7 de 7). Mas nunca tinha tido uma frente tão pequena (1,87 ponto).
- **Disputas tão apertadas:** governador no Brasil, {h['P2_governador']['perto_frente_ate_3_e_lider_abaixo_50']['viradas']} viradas em {h['P2_governador']['perto_frente_ate_3_e_lider_abaixo_50']['n']}; outros países, {p6['frente_ate_3_e_lider_abaixo_50']['viradas']} em {p6['frente_ate_3_e_lider_abaixo_50']['n']}.
- **Pesquisas:** {p3b['com_flavio_na_frente']} de {p3b['institutos']} institutos davam o Flávio; o erro, de {br(p3b['erro_da_frente_pontos'], 1)} pontos na frente, é do tamanho do erro médio do Brasil.
- **Polymarket:** o favorito ganhou {p4['favorito_ganhou']} de {p4['eleicoes']} eleições; na faixa do Flávio, perdeu 3 de 12 antes do Brasil.
- **A combinação** (liderou o 1º turno, liderou as pesquisas e perdeu): 1 em 30 no Brasil de 2014 a 2022. Somando tudo como se fosse independente: {br(p7['a_independente_presidente_x_polymarket_x_minas'] * 100, 2)}%.

Raro não quer dizer fraudado: a resposta sobre fraude está nos testes dos arquivos, não na raridade.

Tudo refeito com código novo e outras fontes: {"passou" if va['todos_passaram'] else "não passou"}. Relatório completo: [`RELATORIO.md`](RELATORIO.md).
"""
    (R / "RESUMO_SIMPLES.md").write_text(resumo, encoding="utf-8")
    leitura = f"""# Leitura da IA

Opinião do Claude sobre os resultados, marcada como opinião. Os números estão no [`RELATORIO.md`](../RELATORIO.md); a decisão do que dizer no vídeo é do autor.

**Opinião 1, sobre de onde vieram os votos.** Os números apontam que a virada veio sobretudo de quem não tinha votado ou tinha anulado no 1º turno e passou a votar no Lula, e de parte dos eleitores do Cury. Isso combina com três medidas independentes: a abstenção caiu em {br(r3['D3_abstencao']['abstencao_caiu_em_pct_das_secoes'], 1)}% das seções; o ganho do Lula foi maior onde ela mais caiu; e as pesquisas erraram justamente no filtro de quem ia votar. A comparação que sustenta: o modelo de transferência dá {mi(novos)} vindos de abstenção e nulo.

**Opinião 2, sobre a fraude.** Os testes que olham os arquivos de cada urna, que são onde uma fraude que muda votos teria de aparecer, não acharam nada: o registro de cada voto bate com o boletim nas {br(r2['A4_rdv_contra_boletim']['secoes_comparadas'])} seções. Os três sinais que passaram do limite medem comportamento de seção e somam, cada um, menos de 7% da margem. Para virar o resultado, uma fraude teria de mover mais de 2,2 milhões de votos sem deixar diferença entre o RDV e o boletim em nenhuma seção. A comparação que sustenta: na Venezuela de 2024 e no México de 1988, a fraude apareceu justamente porque o resultado por seção não existia ou não batia; aqui ele existe e bate.

**Opinião 3, sobre a raridade.** Foi raro para presidente no Brasil e para quem olhava as pesquisas e a Polymarket. Não foi raro para uma disputa com 1,87 ponto de frente e o líder com 47%: nesse tamanho, metade das disputas vira, no Brasil e fora dele.

**O que fica em aberto, e quem responde:** a lista de quem votou em cada seção nos dois turnos (para separar troca de eleitor de rodízio de quem vota, sinais A1 e A3) e a assinatura digital dos arquivos. As duas estão com o TSE.
"""
    (R / "docs/LEITURA_DA_IA.md").write_text(leitura, encoding="utf-8")
    ac, de = ra["acusacao"], ra["defesa"]
    rev = "# Revisão adversarial\n\nDois papéis, cada objeção virando conta (`resultados/revisao_adversarial.json`, gerado por `ferramentas/revisao-adversarial.py`).\n\n## Advogado da acusação\n\n"
    for k, v in ac.items():
        rev += f"- **{v['objecao']}.** " + "; ".join(f"{kk.replace('_', ' ')}: {br(vv, 2) if isinstance(vv, float) else (br(vv) if isinstance(vv, int) else vv)}" for kk, vv in v.items() if kk not in ("objecao", "leitura")) + ".\n"
    rev += "\n## Advogado da defesa\n\n"
    for k, v in de.items():
        itens = []
        for kk, vv in v.items():
            if kk == "objecao":
                continue
            itens.append(f"{kk.replace('_', ' ')}: {json.dumps(vv, ensure_ascii=False) if isinstance(vv, dict) else vv}")
        rev += f"- **{v['objecao']}.** " + "; ".join(itens) + ".\n"
    rev += "\nNenhuma objeção muda o resultado de um teste; o efeito de cada uma está publicado acima. A revisão foi feita pela mesma IA, não por pessoa (limite declarado).\n"
    (R / "docs/REVISAO_ADVERSARIAL.md").write_text(rev, encoding="utf-8")
    print("ok")


if __name__ == "__main__":
    main()
