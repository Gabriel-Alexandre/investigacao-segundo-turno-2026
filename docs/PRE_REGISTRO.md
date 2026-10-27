# Pré-registro: investigação do 2º turno de 2026

**Escrito em 26/10/2026, o dia seguinte ao 2º turno, antes de qualquer conta seção a seção.** O commit deste arquivo é a prova da ordem: as regras vieram antes dos resultados por seção. Toda mudança depois dele entra na §9, numerada, datada, dizendo se veio **antes** ou **depois** de ver números.

## 1. A pergunta e o jeito de responder

**A pergunta:** o resultado do 2º turno (Lula 51,79%, Flávio 48,21%, depois de o Flávio terminar o 1º turno na frente com 47,03% contra 45,16%) é o que os dados de seção, o histórico do Brasil e o que costuma acontecer em outras eleições sustentam, ou há sinais de fraude? E qual a probabilidade de isso ter acontecido?

**O jeito de responder, pedido do autor:** dois caminhos, com o mesmo rigor e o mesmo espaço no relatório.

| Caminho | Ponto de partida | O que procura |
|---|---|---|
| **D · Defesa** | o resultado é legítimo | a explicação: de onde vieram os votos, por que as pesquisas e os mercados erraram |
| **A · Acusação** | o resultado é fraude | a evidência: as marcas que uma fraude deixaria nos boletins, nos registros do voto e nos logs das urnas |

Os dois caminhos usam os **mesmos dados**. Cada teste da acusação tem um limiar escrito aqui; quando o limiar é passado, o relatório diz **"sinal encontrado"**, com o tamanho, sem relativizar. Um sinal só conta como **evidência** se aparecer do lado do Lula e não aparecer do mesmo tamanho no lado do Flávio nem no 2º turno de 2022 (a régua de medida, §6). O bloco **P** (probabilidade) é comum aos dois.

## 2. O que já foi visto antes de escrever

- O resultado oficial final do país e de cada UF nos dois turnos de 2026 (o arquivo de Presidente do TSE gravado na noite, `dados/noite/`).
- As 2.554 versões do arquivo nacional e das UFs gravadas de 17h20 de 25/10 às 06h56 de 26/10, e as contas parciais feitas às 20h29 com 52% das seções (`dados/noite/contas-parciais-20h29/`).
- A conta do saldo nacional: Lula +10.376.694, Flávio +3.721.538; outros candidatos 9.316.747, abstenção −2.960.239, brancos e nulos −1.821.246.
- Reportagens sobre as pesquisas da véspera, a Polymarket, a abstenção, a prorrogação até as 19h e a pausa da divulgação de 17h07 a 19h01.
- Um teste de 40 seções de Roraima do 2º turno, para conferir que o coletor e os leitores funcionam (sem conta de resultado).
- **Nada** por seção ou por município do 2º turno foi analisado. A coleta completa começou em 26/10/2026, às 07h30, antes deste commit; nenhuma conta roda sobre ela antes do commit.

## 3. Os dados

| Dado | Fonte | Para quê |
|---|---|---|
| hora de recebimento, boletim (`bu.dat`), registro digital do voto (`rdv.dat`) e log da urna (`log.jez`) de cada seção do **2º turno** | `resultados.tse.jus.br/oficial/ele2026/arquivo-urna/3221/` | tudo |
| hora de recebimento e boletim de cada seção do **1º turno** | `.../arquivo-urna/3220/` | comparação seção a seção |
| boletins de urna de **2022** por seção (CSV do TSE com hash publicado) | `dadosabertos.tse.jus.br` | régua de 2022 |
| votação por candidato de **1994 a 2022** (presidente e governador, os dois turnos) | `cdn.tse.jus.br/.../votacao_candidato_munzona_AAAA.zip` | probabilidade (P1, P2, P5) |
| pesquisas registradas no TSE e histórico de pesquisas de 2º turno | projetos `previsao-segundo-turno-2026` e `presidente-primeiro-turno-2026` (cópia com hash) e capturas | P3 |
| histórico de preço e resolução dos mercados de eleição | API pública da Polymarket (`gamma-api.polymarket.com`, `clob.polymarket.com`) | P4 |
| 2º turnos presidenciais de outros países desde 1990 | listas públicas com segunda fonte de cada caso | P6 |
| a cronologia da prorrogação e da pausa | `dados/noite/docs-da-noite/PAUSA_DA_VOTACAO.md` e capturas | A7, A8 |

Todo arquivo baixado tem endereço, hora, tamanho e sha256 (`dados/brutos/<turno>/<uf>.sqlite`, `dados/MANIFESTO.json`).

## 4. Caminho D · Defesa

| # | Teste | Saída |
|---|---|---|
| D1 | **Saldo por seção:** para cada seção (mesmo eleitorado nos dois turnos), a variação do Lula, do Flávio, da abstenção e de brancos e nulos, e os votos dos outros candidatos no 1º turno | a conta dos 10,38 milhões somada de baixo para cima, por UF e município |
| D2 | **Transferência de votos (inferência ecológica):** modelo de transição por seção, categorias de entrada Lula, Flávio, Cury, Renan Santos, Caiado, demais, branco e nulo, abstenção; de saída Lula, Flávio, branco e nulo, abstenção. Validação obrigatória: o mesmo modelo no 1º → 2º turno de **2022**, comparado com pesquisas que perguntaram o voto do 1º turno | quantos votos de cada origem foram para cada candidato, com intervalo |
| D3 | **Abstenção:** onde ela caiu e subiu, e se a queda acompanha o ganho do Lula seção a seção | correlação e o quanto ela explica |
| D4 | **As cidades que viraram:** municípios em que o Flávio venceu o 1º turno e o Lula o 2º (e o contrário), em pontos e em votos; o que cada fator explica (votos dos outros, abstenção, branco e nulo, região, tamanho, voto do Lula em 2022) | lista, mapa e regressão |
| D5 | **A curva da noite:** a reconstrução pela hora de recebimento, conferida contra as 2.554 versões oficiais; a ordem de chegada por região depois da pausa | se a ordem de chegada explica as trocas de liderança |
| D6 | **As pesquisas:** o erro de cada instituto e o filtro de quem vai votar (as seções onde a abstenção mais caiu votaram mais no Lula?) | o tamanho do erro e o que o explica |

## 5. Caminho A · Acusação

Cada teste diz a marca que a fraude deixaria e o limiar a partir do qual o relatório escreve **"sinal encontrado"**.

| # | Teste | A marca da fraude | Limiar do sinal |
|---|---|---|---|
| A1 | **Votos sem origem:** em cada seção, *reserva* = votos dos outros no 1º turno + queda da abstenção + queda de brancos e nulos; *excesso* = ganho do candidato − reserva, quando positivo (exige eleitor trocando de lado) | voto transferido de um candidato para o outro aparece como excesso concentrado de um lado | o excesso somado do Lula passa de **2 vezes** o do Flávio **e** a razão passa de 2 vezes a razão equivalente de 2022 (quem cresceu mais ÷ o outro); ou **mais de 50%** do excesso do Lula cai em **1%** das seções |
| A2 | **Votos que somem:** seções em que o Flávio teve menos votos no 2º turno que no 1º com o comparecimento subindo | tirar de um para dar ao outro | proporção de seções do Flávio maior que **2 vezes** a mesma conta para o Lula e para o 2º turno de 2022 |
| A3 | **Enchimento de urna:** salto de comparecimento muito acima das outras seções do mesmo município (acima do percentil 99,9 da variação do município) com voto concentrado (acima de 80% para um candidato); e a impressão digital comparecimento × votação (massa acima de 95% de comparecimento e 95% de votação) | comparecimento inflado junto com voto de um lado | seções marcadas do Lula acima de **2 vezes** as do Flávio, ou massa no canto da impressão digital acima de **3 vezes** a do 1º turno e de 2022 |
| A4 | **Registro do voto contra boletim:** o RDV traz cada voto da seção; a soma dele por candidato tem de ser igual ao boletim | boletim alterado sem alterar o registro de cada voto | **qualquer** seção com diferença é sinal, listada uma a uma |
| A5 | **Log contra boletim:** votos computados no log contra comparecimento do boletim; hora de encerramento do log contra hora de recebimento | voto registrado fora da urna, ou boletim de outra urna | diferença acima de **0,5%** das seções (no 1º turno, o leitor bateu em 99,7%) |
| A6 | **Votos depois do horário:** votos computados depois das 17h locais, por seção, por UF e nos 3 municípios da BA citados na decisão; e quem venceu nessas seções contra o 1º turno delas | a prorrogação usada para votar além do que a fila justificava | votos depois das 17h somando mais que **10%** da margem final (443 mil) ou seções com mais de 30% dos votos depois das 17h |
| A7 | **Votos em rajada e liberação sem digital:** sequências de 10 ou mais votos seguidos com menos de 15 s entre eles; votos liberados sem a digital do eleitor (pelo mesário ou por dado digitado), pela hora do dia | voto em nome de eleitor ausente | rajadas ou liberações manuais concentradas no fim do dia em seções onde o Lula cresceu, acima de **2 vezes** o padrão da manhã e do espelho |
| A8 | **A pausa e a cauda da noite:** boletins recebidos durante a pausa (17h07 a 19h01) e os últimos 2% recebidos; o resultado deles contra o previsto pelo 1º turno das mesmas seções | boletins "guardados" e trocados durante a parada | desvio médio do previsto acima de **1 ponto** e de 3 erros padrão a favor de um candidato |
| A9 | **Urnas substituídas:** urnas de contingência no log; onde, quantas contra o 1º turno, e o resultado nelas contra o 1º turno da mesma seção | troca de equipamento para mudar votos | desvio médio acima de **2 pontos** a favor de um candidato |
| A10 | **Zerados e unanimidades:** seções em que um candidato tinha votos no 1º turno e ficou com zero no 2º, ou com mais de 95% dos votos válidos | manipulação grosseira por seção | mais de **2 vezes** de um lado que do outro, ou acima do 1º turno e de 2022 |
| A11 | **Resíduos agrupados:** o 2º turno previsto pelo 1º da mesma seção (modelo ajustado em todo o país); municípios e zonas onde o Lula passa muito do previsto | fraude localizada em um lugar | municípios acima de 3 erros padrão listados; agrupamento geográfico medido |

## 6. A régua de medida e o veredito

- **Régua:** cada teste da acusação é feito também para o Flávio e no 2º turno de 2022 quando o dado existe. Isso não serve para diminuir o sinal; serve para saber se ele é do lado do Lula ou é o que toda eleição produz.
- **Veredito por teste**, em cinco níveis: **Confirmado** (prova direta, como uma diferença entre RDV e boletim) · **Indício forte** (sinal acima do limiar só de um lado) · **Compatível com os dois** (o dado não separa: diz qual documento separaria) · **Não sustentado** (o sinal previsto pela fraude não aparece) · **Desmentido** (o fato alegado é falso).
- **Toda conclusão traz o teto do pior caso:** quanto o sinal poderia ter movido, contra a margem de **4.430.191 votos**.
- **Ao fim, os dois caminhos lado a lado**, e a leitura da IA marcada como opinião.

## 7. Bloco P · A probabilidade do que aconteceu

O autor pediu a probabilidade de o resultado ter acontecido dado o histórico. Cada conta tem a base escrita aqui.

| # | Conta | Base | Medida |
|---|---|---|---|
| P1 | quem liderou o 1º turno de presidente perdeu o 2º | Brasil, 1989 a 2022 (7 segundos turnos) | contagem; estimativa pela regra de Laplace |
| P2 | quem liderou o 1º turno de governador perdeu o 2º | todos os 2º turnos de governador de 1994 a 2022 (TSE) | taxa geral e taxa com a frente do líder até 3 pontos e o líder abaixo de 50%; modelo logístico pela frente, avaliado em 1,87 ponto |
| P3 | o líder das pesquisas perdeu | 2º turnos de presidente desde 1989 (última pesquisa de cada instituto) e de governador desde 2014 | taxa de acerto do líder; distribuição do erro da média contra a urna; chance de um erro do tamanho de 2026 |
| P4 | o favorito da Polymarket perdeu | todos os mercados de vencedor de eleição nacional resolvidos na Polymarket | **taxa de acerto do favorito na véspera** (o favorito ganhou ou não), geral e com o favorito acima de 75% |
| P5 | quem venceu Minas no 1º turno não venceu a eleição | 1989 a 2022 | contagem |
| P6 | o mesmo em outros países | 2º turnos presidenciais desde 1990 | taxa de virada do líder do 1º turno, pela frente |
| P7 | **a probabilidade combinada** | P1 a P6 | duas contas: (a) como se fossem independentes (o limite de quão raro seria); (b) com a dependência tratada (pesquisa, mercado e virada são o mesmo erro visto de lados diferentes), pelo modelo do erro das pesquisas. As duas são publicadas, com a explicação de cada uma |

## 8. Linguagem

- O relatório diz "sinal encontrado" quando o limiar é passado e "não encontrado" quando não é; sem adjetivo.
- Seção marcada por teste é listada com o motivo, como *"fora do padrão, a conferir"*.
- Nenhum julgamento de intenção de pessoa, órgão ou campanha; nenhuma recomendação de voto.
- Identificador de mesário e de eleitor nunca é publicado (código por HMAC com chave local, fora do git).

## 9. Emendas

| # | Data | Antes ou depois de ver números | O quê |
|---|---|---|---|
| 1 | 26/10/2026, 14h55 | antes de qualquer conta de 1º contra 2º turno (só as contas só do 2º turno, rodada 2, tinham rodado) | **Fonte de SP, TO e exterior no 1º turno:** o servidor de resultados do TSE passou a responder 429 faltando 30.656 seções; essas três UFs vêm do boletim de urna em arquivo único por UF (BU na Web, `cdn.tse.jus.br`, conferido pelo `.sha512` publicado). Antes de usar, comparado com as 73.000 seções de SP já baixadas: iguais em todas, nas 9 colunas (`resultados/emenda1_conferencia_bweb.json`) |
| 2 | 26/10/2026 | depois de ver a rodada 2 | **A4 (RDV):** o tipo de voto 6 do RDV, que só aparece nos 6 estados com governador no 2º turno, é contado como nulo, como faz o boletim; o resultado pela letra da regra (586 seções) fica publicado |
| 3 | 26/10/2026 | depois de ver a rodada 2 | **A6:** a proporção de votos depois das 17h é medida também contra o comparecimento do boletim, porque nas urnas trocadas o log só cobre a substituta; o resultado pela letra da regra (34 seções) fica publicado |
| 4 | 27/10/2026 | depois de ver todos os resultados, por decisão do autor | **Os pesos da conclusão por critério.** Os arquivos das urnas passam a pesar menos (eram o critério de maior peso no roteiro): a lista de cada voto bater com o boletim é o esperado nas duas lentes, porque, se a fraude acontecesse dentro do TSE, os arquivos publicados viriam iguais; esse critério só ganharia peso se mostrasse alguma coisa estranha. Nova ordem: (1) o comportamento dos votos, somado ao que o projeto do vídeo 19 mediu; (2) a raridade; (3) os arquivos das urnas. Palavras do autor: *"é normal que tudo bata, do ponto de vista de ser legítimo e do ponto de vista de ser fraude"*. O resultado de cada teste não muda; muda o peso na conclusão (`resultados/rodada7.json`, `R7b_conclusao`) |
