# Pré-registro: a noite do 2º turno de 2026

**Escrito em 24/10/2026, às 23h, antes da votação de 25/10/2026.** Nenhum voto do 2º turno existia quando este arquivo foi escrito: o arquivo nacional do TSE para o 2º turno (`ele2026/6258`) estava no ar com 0 seções totalizadas (gerado em 24/10/2026 19:19:13).

O commit deste arquivo é a prova de que as regras abaixo vieram **antes** do resultado. Toda mudança depois dele entra na §9, datada, dizendo se veio antes ou depois de ver números.

## 1. As três perguntas

| | Pergunta | Saída |
|---|---|---|
| **A** | A apuração de 25/10 seguiu o padrão das apurações anteriores (o 1º turno de 2026 e o 2º turno de 2022)? Houve parada na divulgação? | a curva da noite, a queda da vantagem de quem começou na frente, a maior parada, a hora da definição, e um veredito por item |
| **B** | A projeção publicada em 21/10 (`previsao-segundo-turno-2026`, `a0d1853`) bateu com a urna? | o erro em pontos do número final e de cada uma das 3 partes, o vencedor, a faixa de 1 ponto e os 4 estados que acertaram as 6 eleições |
| **C** | As 27 pesquisas do 2º turno registradas no TSE acertaram? | o erro de cada pesquisa e de cada instituto, o lado do erro, e quem chegou mais perto |

## 2. O que já foi visto antes de escrever

- O resultado do 1º turno de 2026, por UF.
- A projeção do 2º turno: **Flávio Bolsonaro 50,8% e Lula 49,2% dos votos válidos**, com 1 ponto para cada lado; partes: pesquisas 50,97%, histórico 50,57%, crescimento 50,84% (Flávio).
- As 27 pesquisas do 2º turno coletadas até 21/10 e as 17 usadas na projeção (16 com Flávio na frente).
- As curvas de apuração reconstruídas pelos boletins de urna no projeto `apuracao-eleicoes-2026` (`b595664`): 1º turno de 2026 e 1º e 2º turnos de 2022.
- Nenhuma pesquisa publicada depois de 21/10 entra em B ou C.

Todos esses arquivos são copiados para `dados/referencias/`, com o sha256 e o commit de origem em `dados/referencias/MANIFESTO.json`.

## 3. A medida comum

Toda porcentagem de candidato é sobre os **votos válidos** (`vap` do candidato ÷ `vv`), com duas casas. A **vantagem** é Flávio menos Lula, em pontos. A porcentagem da apuração é a de **seções totalizadas** (`pstn` do arquivo do TSE).

## 4. A · A noite da apuração

### 4.1 A coleta

- `ferramentas/coletar-ao-vivo.py` lê o arquivo nacional de Presidente do 2º turno (`oficial/ele2026/6258/dados/br/br-c0001-e006258-u.json`) a cada **20 segundos**, e os arquivos das 27 UFs e do exterior em rodízio (um arquivo a cada 5 segundos, cada UF a cada ~2,5 minutos).
- Toda versão nova (número de geração `idg` diferente) é gravada inteira, com a hora da leitura e o sha256, em `dados/brutos/ao-vivo/` e no `dados/MANIFESTO_AO_VIVO.jsonl`.
- Começa às 16h50 de 25/10 e para 30 minutos depois de o arquivo nacional marcar a totalização final (`tf = s`), ou às 02h de 26/10, o que vier primeiro.
- Limite de requisições: menos de 1 por segundo; em erro 429 ou 5xx, espera dobrada até 2 minutos.

### 4.2 O padrão, escrito antes

Nas duas apurações de referência, o candidato que começou na frente viu a vantagem encolher conforme os estados do Nordeste chegaram por último:

| Referência | Vantagem com 10% das seções | No fim | Queda |
|---|---|---|---|
| 2º turno de 2022 (Bolsonaro menos Lula) | +4,02 | −1,80 | **5,83 pontos** |
| 1º turno de 2026 (Flávio menos Lula) | +10,55 | +1,87 | **8,68 pontos** |

**Regra A1 (a queda).** Seja *Q* = vantagem com 10% das seções totalizadas menos a vantagem no fim. A noite está **dentro do padrão** se *Q* ficar entre **3,8 e 10,7 pontos** (o intervalo das duas referências, com 2 pontos de folga de cada lado). Abaixo de 3,8 ou acima de 10,7: **fora do padrão**, e o relatório diz quanto.

**Regra A2 (a ordem de chegada).** Às 18h30, o Centro-Oeste e o Sul devem estar **acima** da fração nacional de seções totalizadas e o Nordeste **abaixo**, como no 1º turno de 2026 (pelos boletins: Centro-Oeste 60,8%, Sul 56,4%, nacional 35,3%, Nordeste 27,2%, Sudeste 25,7%). Se o Nordeste estiver acima da nacional: fora do padrão. (A série por região do 2º turno de 2022 não está nos arquivos do projeto de origem; por isso a referência aqui é só o 1º turno de 2026.)

**Regra A3 (a parada).** Uma **parada** é um intervalo em que o arquivo nacional não muda de versão por mais de **10 minutos**, com a apuração entre 1% e 99% das seções. No 1º turno de 2026, a tela de Presidente ficou de **19h06 a 20h08** sem atualizar (62 minutos, pelos pontos publicados pela imprensa e pela reconstrução por boletim). O relatório dá a maior parada da noite em minutos e compara com os 62.

**Regra A4 (a definição).** A hora da definição é a primeira versão do arquivo nacional em que um candidato aparece como eleito (`e = s`). O relatório dá essa hora e a porcentagem das seções naquele momento. Referência: no 2º turno de 2022, os boletins chegaram a 99% das seções às 20h00.

**Regra A5 (a troca de liderança).** O relatório diz se houve troca de liderança durante a noite e com quantos % das seções. No 2º turno de 2022 houve, com 67,6% das seções; no 1º turno de 2026, só no primeiro meio por cento das seções.

**Veredito de A:** *"a apuração seguiu o padrão"* se A1, A2 e A3 estiverem dentro (parada de até 30 minutos); se qualquer uma ficar fora, o veredito diz qual e quanto. ⛔ O projeto não diz o porquê de uma parada: a causa técnica não é pública.

## 5. B · A projeção contra a urna

O número publicado em 21/10 **não muda**. O relatório mede:

| Medida | Como |
|---|---|
| Erro do número final | Flávio na urna menos 50,85 (o número sem arredondar); diz também contra o 50,8 apresentado |
| Acertou o vencedor? | sim se o candidato com mais votos válidos for o que a projeção pôs na frente |
| Dentro da faixa de 1 ponto? | sim se o Flávio na urna ficar entre 49,8 e 51,8 |
| Erro de cada parte | pesquisas (50,97), histórico (50,57), crescimento (50,84) contra a urna; a parte mais perto |
| Contra o teste do passado | o erro de hoje comparado com o erro médio de 1,8 ponto que o teste do passado mostrou |
| Os estados | os 4 estados que acertaram as 6 eleições (MG, TO, AM, AP): quem venceu em cada um e se a regra *"quem ganha ali ganha o país"* continuou valendo; Minas em destaque |
| Estado por estado | o crescimento projetado por UF (`r_por_uf.csv`) contra a urna de cada UF; erro médio e os 3 maiores |
| O que mudou do 1º para o 2º turno | as UFs em que o vencedor mudou entre os turnos, e a variação da vantagem em cada UF |

## 6. C · As pesquisas contra a urna

| Medida | Como |
|---|---|
| Erro de cada pesquisa | Flávio em votos válidos na pesquisa (`anti_valido` de `pesquisas_2026_todas.csv`) menos Flávio na urna |
| O lado do erro | quantas deram ao Flávio **menos** do que a urna e quantas **mais** |
| Acertou o vencedor? | quantas puseram na frente quem venceu |
| Dentro da margem? | erro em válidos até a margem de erro declarada da pesquisa (a margem é sobre votos totais; o relatório diz isso) |
| Por instituto | a última pesquisa de cada um dos 17 institutos (`p_pesquisas_usadas.csv`); ordem do mais perto ao mais longe |
| A média simples | a média das últimas de cada instituto contra a urna, ao lado da projeção |
| Contra o 1º turno | no 1º turno, os 10 institutos conferidos na véspera deram ao Flávio menos voto do que a urna (vídeo 7); o relatório diz se o lado do erro se repetiu |

## 7. Validação

- Os totais da última versão do arquivo nacional são refeitos pela soma dos 27 arquivos de UF mais o exterior; diferença tem que ser zero (ou o relatório diz qual UF não fechou).
- `ferramentas/validacao-independente.py` refaz os números de B e C lendo os CSV de referência sem importar o pacote `noite`.
- Ensaio antes: o pipeline inteiro roda hoje com uma noite **simulada a partir do 1º turno** (`ferramentas/ensaio-1turno.py`), com todas as saídas marcadas como ENSAIO. Os números do ensaio não são resultado e não entram no relatório final.

## 8. O que o projeto não faz

- Não diz a causa de uma parada nem de um erro de pesquisa.
- Não confere a assinatura dos boletins nem o que acontece dentro do sistema do TSE.
- Não refaz a curva por boletim de urna (isso sai dias depois, quando os arquivos por seção forem publicados).
- Não recomenda voto e não julga candidato.

## 9. Emendas

**Emenda 1 · 25/10/2026, 00h40, antes da votação (nenhum voto do 2º turno existia).** Na revisão do código, a IA viu que o TSE pode gerar uma versão nova do arquivo sem que o número mude, e aí uma tela parada passaria sem ser contada. A regra A3 passa a contar também o intervalo de mais de 10 minutos em que o **número de seções totalizadas não muda**, mesmo com versão nova. A maior parada é a maior das duas medidas. E um intervalo em que a própria coleta ficou fora do ar (sem batida a cada 2 minutos) **não conta** contra o TSE: o relatório mostra, marcado como buraco da coleta.

**Conta registrada junto (não muda regra):** a faixa da regra A1 (3,8 a 10,7) tem 6,9 pontos de largura, porque as duas referências já ficam 2,9 pontos uma da outra. Ela separa uma noite normal de uma muito diferente, e não separa uma noite parecida com 2022 de uma parecida com o 1º turno; o relatório dá a queda em número para essa comparação.
