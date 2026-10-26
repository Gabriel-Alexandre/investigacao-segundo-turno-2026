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
| P4 · Polymarket | em andamento | — |

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
