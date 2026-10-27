# Relatório: investigação do 2º turno de 2026

Gerado por `ferramentas/gerar-relatorio.py` a partir de `resultados/`. Regras: [`docs/PRE_REGISTRO.md`](docs/PRE_REGISTRO.md), publicadas antes de qualquer conta por seção. Base: as 499.248 seções do 2º turno (boletim, registro digital do voto e log de cada urna), as do 1º turno e as de 2022, todas do TSE.

## O que o projeto não consegue dizer

- **Quem votou em quem.** O voto é secreto; a transferência do 1º para o 2º turno é estimada por inferência ecológica, com intervalo.
- **Se a urna registrou o voto que o eleitor digitou.** O projeto confere que os arquivos de cada urna são coerentes entre si (boletim, registro de cada voto e log) e com o total oficial; não tem como conferir o dedo do eleitor. Não há voto em papel no Brasil.
- **A assinatura digital dos boletins** não foi verificada.
- **Intenção** de qualquer pessoa ou órgão.

## A conta dos votos

Do 1º para o 2º turno, o Lula ganhou **10,38 milhões** e o Flávio **3,72 milhões**. No saldo, isso saiu de 9,32 milhões de votos dos outros candidatos, 2,96 milhões de quem voltou a votar e 1,82 milhão de quem deixou de votar branco ou nulo (soma das 499.176 seções que existem nos dois turnos).

## Caminho da defesa: de onde vieram os votos

Estimativa seção a seção, por UF, com intervalo de 90% (`resultados/d2_transferencia.json`):

| Eleitores que... | foram para o Lula | foram para o Flávio |
|---|---|---|
| votaram no Augusto Cury | 1,83 milhão (1,82 milhão a 1,84 milhão) | 0,96 milhão (0,94 milhão a 0,97 milhão) |
| votaram no Renan Santos | 1,07 milhão (1,06 milhão a 1,08 milhão) | 0,93 milhão (0,92 milhão a 0,94 milhão) |
| votaram no Ronaldo Caiado | 0,85 milhão (0,84 milhão a 0,86 milhão) | 1,36 milhão (1,35 milhão a 1,37 milhão) |
| votaram no Zema ou nos demais | 0,18 milhão (0,17 milhão a 0,18 milhão) | 0,31 milhão (0,30 milhão a 0,31 milhão) |
| votaram branco ou nulo | 3,72 milhões (3,71 milhões a 3,73 milhões) | 0,07 milhão (0,07 milhão a 0,08 milhão) |
| não votaram no 1º turno | 3,20 milhões (3,18 milhões a 3,22 milhões) | 0,77 milhão (0,76 milhão a 0,79 milhão) |
| votaram no Flávio no 1º turno | 0,10 milhão (0,10 milhão a 0,11 milhão) | 55,31 milhões (55,30 milhões a 55,32 milhões) |

⚠️ O intervalo mede só a variação entre seções; o erro do próprio modelo é maior, como mostra o teste de 2022 abaixo.

Validação em 2022 (o mesmo modelo, comparado com o Datafolha de 5 a 7/10/2022): eleitores do Ciro, modelo 40,3% Lula e 42,4% Bolsonaro, Datafolha 31% e 42%; eleitores da Tebet, modelo 37,8% e 44,2%, Datafolha 31% e 29%. O modelo acertou o lado dos eleitores do Ciro e errou o da Tebet: os números de origem acima são a melhor estimativa disponível, não uma medida exata.

**As cidades que viraram:** no Brasil, 211 municípios foram do Flávio no 1º turno para o Lula no 2º e 1 fez o contrário; outros 2 empataram no 1º turno e foram do Lula no 2º. No exterior, 6 cidades foram do Flávio para o Lula e 3 do Lula para o Flávio. A frente do Lula aumentou em 97,1% dos 5.571 municípios (`resultados/d4_municipios.csv`). Contra 2002 a 2022 (rodada 5, `resultados/rodada5_municipios_por_ano.csv`): 2002: 793 viraram (110 para o PT, 683 para o adversário), o PT ganhou mais votos que o adversário em 31,2% e ficou com 41,5% do que os 2 ganharam no Sul; 2006: 913 viraram (912 para o PT, 1 para o adversário), o PT ganhou mais votos que o adversário em 98,8% e ficou com 121,4% do que os 2 ganharam no Sul; 2010: 325 viraram (30 para o PT, 295 para o adversário), o PT ganhou mais votos que o adversário em 30,4% e ficou com 25,1% do que os 2 ganharam no Sul; 2014: 348 viraram (71 para o PT, 277 para o adversário), o PT ganhou mais votos que o adversário em 26,5% e ficou com 30,2% do que os 2 ganharam no Sul; 2018: 146 viraram (121 para o PT, 25 para o adversário), o PT ganhou mais votos que o adversário em 69,9% e ficou com 53,7% do que os 2 ganharam no Sul; 2022: 251 viraram (0 para o PT, 251 para o adversário), o PT ganhou mais votos que o adversário em 12,8% e ficou com 18,0% do que os 2 ganharam no Sul; 2026: 212 viraram (211 para o PT, 1 para o adversário), o PT ganhou mais votos que o adversário em 93,8% e ficou com 60,6% do que os 2 ganharam no Sul.

**A noite:** refeita pela hora de recebimento de cada boletim, acompanha as versões oficiais gravadas ao vivo com diferença média de 0,07 ponto. As trocas de liderança seguem a ordem de chegada das regiões (`resultados/d5_reconstruida.json`).

**A ordem de chegada contra a ordem embaralhada (rodada 6):** na ordem real, a liderança trocou 1 vez em 2022 (às 18h43, com 67,6% das seções) e 2 vezes em 2026 (19h44 e 20h24). Em 3000 ordens embaralhadas, a última troca aconteceu, na mediana, com 0,033% das seções contadas em 2022 e 0,007% em 2026, e nenhuma ordem trocou depois de 5%: em ordem aleatória o líder se define nas primeiras centenas de seções, e a troca tardia vem da ordem em que as regiões chegam. As 10 maiores quedas da curva de 2022 entre as seções 55 mil e 90 mil têm, em média, 0,011 ponto; em 9 delas entraram seções de Salvador, e as seções de cada queda deram, em média, 59,4% ao Lula (`resultados/rodada6_curva.json`, `resultados/rodada6_quedas_2022.csv`, gráficos `g13` e `g14`).

**As pesquisas:** 19 institutos na última semana; 17 davam o Flávio na frente. A média deu 49,18% ao Lula; a urna deu 51,79%: erro de 5,2 pontos na frente. Nos 2º turnos de 2014 a 2022, o erro médio da frente foi de 5,0 pontos.

## Caminho da acusação: as marcas que uma fraude deixaria

| Teste | O que o dado mostra | Resultado pelo pré-registro |
|---|---|---|
| A1 · votos sem origem na seção | excesso do Lula 148.092 votos, do Flávio 1.724; em 2022, quem cresceu mais (Bolsonaro) teve 78.107 e o outro 3.672. O excesso do Lula é 3,34% da margem | **sinal encontrado** |
| A2 · votos que somem | seções em que o Flávio perdeu voto com o comparecimento subindo: 6,85%; o mesmo para o Lula: 0,09%; em 2022, o candidato que cresceu menos: 4,75% | não encontrado |
| A3 · enchimento de urna | 4.042 seções com salto de comparecimento acima do normal do município (quase uma por município); 857 com mais de 80% para o Lula e 72 para o Flávio. Pela proporção do próprio município, o esperado era 548 e 86 (razão 1,56 e 0,84); em 2022, com o mesmo controle, 1,25 e 1,35. Nessas seções do Lula, o salto médio foi de 7,0 pontos e a liberação sem digital ficou 0,86 ponto acima dos mesmos municípios. Canto 95/95 da impressão digital: 0,013% das seções em 2026, 0,007% em 2022 | **sinal encontrado** |
| A4 · RDV contra boletim | votos do Lula e do Flávio iguais em 499.177 de 499.177 seções; 586 diferem só no nulo (um tipo de voto do RDV, só nos 6 estados com governador no 2º turno, que o boletim soma como nulo) | sinal pela letra da regra, explicado: nenhum voto de candidato difere |
| A5 · log contra boletim | 0,29% das seções diferentes, sempre com menos votos no log; 1.432 de 1.435 tiveram urna trocada no dia | não encontrado |
| A6 · votos depois das 17h | 34.810 votos (0,027%), 13 depois das 19h; teto: 0,79% da margem. As 34 seções acima de 30% são de urna trocada | sinal pela letra da regra, explicado pela troca de urna; a margem não é tocada |
| A7 · rajadas e liberação sem digital | rajadas: 0,000% dos votos. Sem digital: 13,1% onde o Lula venceu, 12,3% onde o Flávio venceu; última hora contra a primeira: 0,30 e 0,30 | não encontrado |
| A8 · boletins da pausa e do fim da noite | desvio do previsto pelo 1º turno da mesma seção: pausa -0,33 ponto (erro padrão 0,12); últimos 2% 0,32 (erro padrão 0,02), abaixo do limite de 1 ponto, mas diferente de zero (sobretudo RJ e SP, onde o modelo nacional erra para cima, ver revisão Y1). Na cauda o Lula teve 54,1% no 2º turno e 46,8% no 1º, nas mesmas seções | não encontrado |
| A9 · urnas trocadas | desvio do previsto: -0,04 ponto em 2.000 seções | não encontrado |
| A10 · unanimidades e zerados | mais de 95% para o Lula: 1.686 seções no 2º turno de 2026 (contra 39 do Flávio), 1.415 no 1º turno e 2.369 no 2º turno de 2022; 1.666 delas já davam mais de 90% ao Lula no 1º turno. Flávio zerado depois de ter voto no 1º turno: 56 seções; Lula: 0 | **sinal encontrado** |
| A11 · resíduos agrupados | municípios acima de 3 erros padrão a favor do Lula: 500; a favor do Flávio: 1.197 (de 5.688) | listados para conferência em resultados/a11_municipios.csv |

**As objeções mais fortes da acusação, calculadas** (`resultados/revisao_adversarial.json`): contando como reserva só os votos dos outros candidatos, 2.585.677 votos do Lula exigiriam eleitor novo, ex-nulo ou troca (58,4% da margem); se as 1.686 seções com mais de 95% fossem todas falsas, seriam 6,8% da margem; se o 1% de seções mais acima do previsto voltasse ao previsto, seriam 1,6% da margem.

## Veredito por teste (régua de cinco níveis, pré-registro §6)

| Teste | Veredito | Teto do pior caso (contra a margem de 4.430.191 votos) | O que fecharia de vez |
|---|---|---|---|
| A1 votos sem origem | Compatível com os dois: o excesso exige troca de eleitor ou rodízio de quem vota; o dado agregado não separa | 3,34% | a lista de quem votou em cada seção nos dois turnos (caderno de votação, com o TSE) |
| A2 votos que somem | Não sustentado | não se aplica | não se aplica |
| A3 enchimento de urna | Compatível com os dois: a assimetria existe e 2022 não tinha; a liberação pela digital do próprio eleitor quase não mudou | 4,2% (todos os válidos dessas seções) | a lista de quem votou nessas seções e a conferência das digitais (TSE) |
| A4 RDV contra boletim | Não sustentado: nenhum voto de candidato difere em nenhuma seção | 0 | a assinatura digital dos arquivos |
| A5 log contra boletim | Não sustentado | não se aplica | não se aplica |
| A6 votos depois das 17h | Não sustentado | 0,79% | não se aplica |
| A7 rajadas e sem digital | Não sustentado | não se aplica | não se aplica |
| A8 pausa e cauda | Não sustentado (abaixo do limite) | não se aplica | não se aplica |
| A9 urnas trocadas | Não sustentado | não se aplica | não se aplica |
| A10 unanimidades | Compatível com os dois: a assimetria é de todo 2º turno com o Lula (2022 teve mais) | 6,8% | não se aplica |
| A11 resíduos agrupados | Não sustentado como padrão a favor do Lula (mais municípios acima do previsto para o Flávio) | não se aplica | não se aplica |

## Probabilidade

| Conta | Resultado |
|---|---|
| Presidente no Brasil: o líder do 1º turno ganhou o 2º | 7 de 7 (1989 a 2022); estimativa de virada pela contagem: 11,1% |
| Governador no Brasil, 1994 a 2022 | 25 viradas em 92; disputa apertada (frente até 3 pontos, líder abaixo de 50%): 10 em 18 |
| Outros países, 1990 a 2025 | 61 viradas em 180 (41 países); disputa apertada: 17 em 37 |
| Polymarket: o favorito da véspera ganhou | 74 de 89 eleições nacionais; com o favorito entre 75% e 85%, 9 de 13 |
| Minas: quem venceu o 1º turno venceu a eleição | 8 de 8 (1994 a 2022) |
| Líder do 1º turno que também liderava as pesquisas perdeu (Brasil, 2014 a 2022) | 1 em 30 (3,3%) |
| Tudo junto, como se fosse independente | 0,28% |

## Validação

Recontagem com código novo e fontes que o cálculo não usou: todas as checagens passaram (`resultados/validacao_independente.json`).

## Outros países

[`docs/OUTROS_PAISES.md`](docs/OUTROS_PAISES.md): o que separou os casos de fraude comprovada (Venezuela 2024, México 1988) dos não comprovados foi a publicação do resultado por seção e a conferência de fora.
