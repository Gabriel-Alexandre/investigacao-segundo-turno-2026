# Rodadas da investigação

Cada rodada traz o que foi medido, com o arquivo de onde sai cada número. As regras são as do [`PRE_REGISTRO.md`](PRE_REGISTRO.md).

## Rodada 1 · 26/10/2026 (bloco P e a curva da noite)

### Bloco P · Probabilidade, pelo Brasil

| Conta | Resultado | Arquivo |
|---|---|---|
| P1 · presidente: o líder do 1º turno ganhou o 2º | **7 de 7** (1989 a 2022). A menor frente de um líder até 2026 era de **5,23 pontos** (2022); em 2026 foi **1,87**, a menor da série | `resultados/p_historico.json` |
| P1 · chance de virada só pela contagem (regra de Laplace, 0 em 7) | **11%** (1 em 9) | idem |
| P2 · governador: 2º turnos de 1994 a 2022 | **92**, com **25 viradas (27%)** | idem |
| P2 · governador com o líder abaixo de 50% e frente de até 3 pontos | **10 viradas em 18 (56%)**; o modelo pela frente dá **50%** para 1,87 ponto | idem |
| P3 · o líder da média das pesquisas da última semana ganhou (2º turnos de 2014 a 2022, presidente e governador) | **38 de 43 (88%)**; erro médio da frente: 5,0 pontos | `resultados/p3_pesquisas.json` |
| P3 · presidente | 2014 e 2018: o líder das pesquisas ganhou. **2022: a média das 22 pesquisas registradas da última semana tinha o Bolsonaro 0,3 ponto à frente**, e o Lula ganhou | idem |
| P5 · quem venceu Minas no 1º turno de presidente venceu a eleição | **8 de 8** (1994 a 2022); quebrou em 2026 | `resultados/p_historico.json` |
| P7 · a combinação de 2026 (o líder do 1º turno também liderava as pesquisas, e perdeu), 2014 a 2022 | **1 em 30** (governador do PA, 2014). Em disputa com frente de até 3 pontos e líder abaixo de 50%: **1 em 4** | `resultados/p7_brasil.json` |
| P4 · Polymarket: o favorito da véspera ganhou (89 eleições nacionais de jan/2024 a out/2026, uma por votação) | **74 de 89 (83%)** | `resultados/p4_polymarket.json` |
| P4 · com o favorito entre 75% e 85% (a faixa do Flávio, 76,6%) | **9 de 13**; antes do 2º turno do Brasil, o favorito dessa faixa perdeu **3 de 12** (Senegal 2024, Tailândia 2026, 1º turno da Colômbia 2026) | idem |
| P4 · com o favorito acima de 85% | **48 de 49** | idem |
| P4 · Brasil 2026 | errou os dois: 1º turno (Lula 72,5%, o Flávio liderou) e 2º turno (Flávio 76,6%, o Lula venceu) | idem |

### D5 · A curva da noite (346 versões oficiais com voto)

| Momento | Seções | Vantagem do Lula |
|---|---|---|
| 1ª versão, 17h06 | 0,25% | +15,3 pontos |
| pausa: nenhuma versão nova de 17h07 a 19h01 | 0,29% | 115 minutos |
| o Flávio passa à frente, 19h44 | 13,65% | −0,02 |
| maior vantagem do Flávio, 20h02 | 24,69% | −1,02 |
| o Lula volta à frente, 20h24 | 47,24% | +0,01 |
| fim, 23h27 | 100% | +3,57 |
| outro intervalo sem versão nova: 22h22 a 23h27 | 99,99% | 65 minutos |

Arquivo: `resultados/d5_curva_noite.json`. Os dois intervalos (115 e 65 minutos) entram no teste A8 com a hora de recebimento de cada boletim.

### P7 · A probabilidade combinada (as duas contas do pré-registro)

| Conta | Resultado |
|---|---|
| (a) como se fossem independentes: virada em presidente (11%) × favorito de 75% a 85% perder (25%) × Minas falhar (10%) | **0,28% (cerca de 1 em 360)**. É o limite de quão raro seria se as três coisas não tivessem relação |
| (b) com a dependência: nos 2º turnos de 2014 a 2022, o líder do 1º turno que também liderava as pesquisas perdeu | **3,3% (1 em 30)** |
| (b) o mesmo em disputa com frente de até 3 pontos e líder abaixo de 50% | **25% (1 em 4)** |
| referência: virada de governador com frente de 1,87 ponto | **50%** |

Arquivos: `resultados/p7_probabilidade.json`, `dados/derivados/polymarket_eleicoes.csv` (cada eleição, incluída ou não, com o motivo). A Polymarket foi lida pelo DNS público da Cloudflare (o domínio não resolve no DNS local); só dados públicos de preço.

## Rodada 2 · 26/10/2026 (os testes da acusação que só precisam do 2º turno)

Base: as **499.248 seções** do 2º turno, cada uma com hora de recebimento, boletim, registro digital do voto (RDV) e log da urna (`dados/derivados/t2_secoes.parquet`, gerado por `ferramentas/derivar-t2.py`; números em `resultados/rodada2.json`; seções marcadas em `resultados/rodada2_secoes_marcadas.csv`).

| Teste | O que o dado mostra | Limiar do pré-registro | Resultado |
|---|---|---|---|
| Reconciliação | soma dos boletins: Lula 64.255.787, Flávio 59.825.688; oficial: 64.256.232 e 59.826.041. Faltam 445 e 353 votos: 29 seções do exterior sem boletim publicado (e 41 não instaladas) | — | bate, com a diferença nomeada |
| **A4** RDV contra boletim | votos do Lula e do Flávio **iguais em 499.177 de 499.177 seções**. Em 586 seções o nulo do boletim é maior que o nulo do RDV pelo número exato de votos de um tipo que o RDV registra à parte (tipo 6), que **só aparece nos 6 estados com governador no 2º turno** (AC, AM, DF, ES, RN, TO) e que o boletim soma como nulo | qualquer seção com diferença | **sinal encontrado pela letra da regra (586 seções), explicado:** a diferença é de classificação de nulo, nenhum voto de candidato difere |
| **A5** log contra boletim | 1.435 seções (0,29%) com menos votos no log que no boletim; nenhuma com mais. **1.432 delas tiveram urna trocada no dia** (o log é o da substituta) | acima de 0,5% | não encontrado |
| **A6** votos depois das 17h | **34.810 votos** depois das 17h de Brasília (0,03% dos votos) em 30.086 seções; **13 depois das 19h**. Teto: mesmo que todos fossem do Lula, seriam **0,79% da margem**. Salvador: 1.768; Feira de Santana: 147; Lauro de Freitas: 79. Por vencedor da seção: 0,08 por seção onde o Lula venceu, 0,06 onde o Flávio venceu. As 34 seções com mais de 30% dos votos do log depois das 17h são **todas de urna trocada** (o log da substituta só tem os últimos votos; contra o comparecimento do boletim, nenhuma passa de 30%) | mais de 10% da margem, ou seções com mais de 30% dos votos depois das 17h | **sinal encontrado pela letra da regra (34 seções), explicado pela troca de urna**; a margem não é tocada |
| **A7** rajadas e liberação sem digital | rajadas: praticamente zero. Liberação sem digital: 13,1% dos votos onde o Lula venceu, 12,3% onde o Flávio venceu; a última hora tem 0,31 da primeira nas seções do Lula e 0,30 nas do Flávio (o pedido cai no fim do dia, dos dois lados) | 2 vezes o padrão da manhã e do espelho | não encontrado |
| **A8** pausa e cauda (parte 1) | 345 boletins recebidos durante a pausa: Lula 49,5%. Os últimos 2% (depois das 21h08): Lula **54,1%** contra 51,8% no geral, sobretudo RJ e SP. O último boletim chegou às 09h28 de 26/10 | comparação com o 1º turno das mesmas seções | **pendente** (rodada 3) |
| **A9** urna trocada (parte 1) | 2.000 seções; Lula 52,3% contra 51,8% no geral | comparação com o 1º turno | **pendente** (rodada 3) |
| **A10** unanimidades (parte 1) | seções com mais de 95% dos válidos: **1.686 do Lula e 39 do Flávio**; zero votos: Flávio em 88 seções, Lula em 3. As do Lula estão no MA (492), BA (249), AM (230), PI (149), PA (118); comparecimento médio 82,1% (geral 80,9%). Somam 318 mil votos válidos e 299 mil de vantagem do Lula (6,7% da margem) | mais de 2 vezes de um lado que do outro, ou acima do 1º turno e de 2022 | **sinal encontrado (43 vezes mais do lado do Lula)**; a comparação com as mesmas seções no 1º turno e em 2022 decide o veredito (rodada 3) |
