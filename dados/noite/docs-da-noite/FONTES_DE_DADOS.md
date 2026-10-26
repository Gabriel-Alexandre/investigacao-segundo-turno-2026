# Fontes de dados

| Fonte | Endereço | Testado | Uso |
|---|---|---|---|
| TSE, Presidente do 2º turno, país | `https://resultados.tse.jus.br/oficial/ele2026/6258/dados/br/br-c0001-e006258-u.json` | ✅ 24/10, 23h14: no ar, 0 seções totalizadas, gerado 24/10 19:19:13 | coleta ao vivo (A, B, C) |
| TSE, Presidente do 2º turno, UF e exterior | `.../6258/dados/<uf>/<uf>-c0001-e006258-u.json` (27 UFs e `zz`) | ✅ as 28 responderam 200 | A2, B por estado |
| TSE, Presidente do 1º turno (final) | `.../6257/dados/<abr>/<abr>-c0001-e006257-u.json` | ✅ copiado com sha256 | 1º × 2º turno, ensaio |
| Projeção de 21/10 | `previsao-segundo-turno-2026` (`a0d1853`) | ✅ copiado com sha256 | B e C |
| Curvas do 1º turno de 2026 e de 2022 por boletim de urna | `apuracao-eleicoes-2026` (`b595664`) | ✅ copiado com sha256 | régua de A |

Campos usados do arquivo do TSE: `idg` (número da versão), `dg`/`hg` (data e hora de geração), `s.pstn`, `s.st`, `s.ts` (seções), `e.te`, `e.est`, `e.esnt`, `e.c`, `e.a` (eleitorado), `v.vv` (válidos), e `vap`, `e`, `st` de cada candidato (votos, eleito, situação). O arquivo vem em latin-1; o leitor tenta utf-8 e cai para latin-1.

⚠️ O TSE sobrescreve o arquivo a cada atualização: a série da noite só existe se alguém guardar. É isso que o coletor faz.
