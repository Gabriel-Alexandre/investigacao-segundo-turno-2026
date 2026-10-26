# A pausa da apuração: a votação prorrogada até as 19h (25/out/2026)

Escrito durante a noite, depois de a pausa acabar. Não muda nenhuma regra do [pré-registro](PRE_REGISTRO.md): a regra A3 só conta parada com a apuração entre 1% e 99% das seções, e esta pausa aconteceu com menos de 0,3%. Por isso ela é medida à parte (`pausa_fora_da_regra` no `RESUMO.json`) e entra no relatório como fato, sem entrar no veredito.

## O que aconteceu, pelas fontes

| Hora (Brasília) | Fato | Fonte |
|---|---|---|
| 16h32 | o ministro Cristiano Zanin, do STF, recebe a reclamação da coligação Brasil Pronto Pra Mais (a do Lula) contra as prefeituras de Salvador, Feira de Santana e Lauro de Freitas, na Bahia, por falta de ônibus para os eleitores (Reclamação 101.673, sobre a decisão do STF que obriga transporte gratuito em dia de eleição) | [Poder360, íntegra da decisão](https://www.poder360.com.br/integras/leia-a-integra-da-decisao-de-zanin-que-prorroga-votacao-ate-as-19h/) · [Migalhas](https://www.migalhas.com.br/quentes/467195/zanin-prorroga-votacao-ate-as-19h-apos-reclamacao-sobre-transporte) |
| por volta de 17h06 | a decisão: *"determino prorrogação por duas horas, até as 19h, horário de Brasília"*, em todas as seções do país; o TSE cumpre | [InfoMoney, ao vivo](https://www.infomoney.com.br/politica/ao-vivo-eleicoes-segundo-turno-2026/) · [Poder360](https://www.poder360.com.br/integras/leia-a-integra-da-decisao-de-zanin-que-prorroga-votacao-ate-as-19h/) |
| 17h13 | Zanin esclarece: a prorrogação vale só onde as urnas ainda estavam abertas; os votos das seções já encerradas são contados normalmente | [Jornal de Brasília](https://jornaldebrasilia.com.br/noticias/politica-e-poder/zanin-determina-prorrogacao-da-votacao-ate-as-19h-em-todo-o-brasil/) |
| 17h16 | o Ministério Público Eleitoral se manifesta contra a prorrogação | [InfoMoney](https://www.infomoney.com.br/politica/ao-vivo-eleicoes-segundo-turno-2026/) |
| 17h20 a 17h27 | o TSE pausa a totalização com cerca de 0,25% das seções | [InfoMoney, 17h23](https://www.infomoney.com.br/politica/ao-vivo-eleicoes-segundo-turno-2026/) · [Bloomberg Línea, 17h27](https://www.bloomberglinea.com.br/brasil/ao-vivo-brasil-vota-no-2-turno-para-escolher-entre-lula-e-flavio-bolsonaro-como-presidente/) · [Brasil de Fato](https://www.brasildefato.com.br/2026/10/25/tse-pausa-divulgacao-de-resultados-com-025-das-urnas-apuradas-apos-zanin-estender-votacao-ate-as-19h/) |
| 17h49 | o TRE-RS avisa que não reabre seção já encerrada | [Bloomberg Línea](https://www.bloomberglinea.com.br/brasil/ao-vivo-brasil-vota-no-2-turno-para-escolher-entre-lula-e-flavio-bolsonaro-como-presidente/) |
| 18h55 | o TSE anuncia que retoma o recebimento dos boletins, a totalização e a divulgação depois das 19h | [Times Brasil](https://timesbrasil.com.br/brasil/decisao-2026-tse-anuncia-retomada-da-totalizacao-e-divulgacao-dos-votos-apos-as-19h/) |

Contexto citado pelas mesmas reportagens: antes da decisão, o TRE-BA mandou prender em flagrante o secretário de Mobilidade de Salvador pela redução da frota, e a secretaria disse que 75 ônibus foram impedidos de sair da garagem por estarem adesivados com símbolos políticos ([Metro 1](https://www.metro1.com.br/noticias/eleicoes-2026/190401,zanin-determina-prorrogacao-da-votacao-ate-as-19h-em-todo-o-pais)). A campanha do Flávio também tinha pedido mais tempo em estados com chuva e falha de transporte ([Migalhas](https://www.migalhas.com.br/quentes/467195/zanin-prorroga-votacao-ate-as-19h-apos-reclamacao-sobre-transporte)). ⛔ Nada aqui julga a intenção de ninguém: são os fatos publicados, com a fonte.

## O que o arquivo do TSE mostra (`dados/MANIFESTO_AO_VIVO.jsonl`)

| Lido às | Gerado às | Seções |
|---|---|---|
| 17h20m42 (1ª leitura do coletor) | 17h06m31 | 0,25% |
| 19h01m16 | **17h07m01** | 0,29% |
| 19h02m18 | 19h01m56 | 0,37% |
| 19h05m01 | 19h04m36 | 1,10% |

1. **O arquivo público ficou parado de 17h06 até as 19h01.** O coletor leu a mesma versão (17h06m31) de 20 em 20 segundos de 17h20 a 19h01, e a página do TSE mostrava *"Última atualização 25/10/2026 17:06:27"*. Como o arquivo sempre traz a versão mais nova, nenhuma outra saiu entre 17h06 e 17h20.
2. **Uma versão gerada às 17h07 ficou retida e só saiu às 19h01.** Pelo horário de geração, que é o que a análise usa, a pausa foi de 17h07 a 19h01: **115 minutos**.
3. **A apuração só passou de 1% às 19h04**, então a regra A3 começa a contar dali.

O coletor foi ligado às 17h20, e não às 16h50 do plano. Não se perdeu nada: o arquivo das 17h20 ainda era o de 17h06.
