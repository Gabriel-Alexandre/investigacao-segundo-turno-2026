# Investigação do 2º turno de 2026

Análise aberta do 2º turno da eleição presidencial de 2026 (25/10/2026): a apuração pelos boletins de urna, o 1º contra o 2º turno seção a seção, as cidades que viraram, de onde vieram os votos a mais do Lula, a prorrogação da votação até as 19h, as pesquisas, a Polymarket e a probabilidade do resultado dado o histórico.

A investigação segue **dois caminhos com o mesmo rigor**: a **defesa** (o resultado é legítimo, procurar a explicação) e a **acusação** (o resultado é fraude, procurar a evidência). As regras de cada teste foram escritas antes de qualquer conta por seção: [`docs/PRE_REGISTRO.md`](docs/PRE_REGISTRO.md).

| Onde | O quê |
|---|---|
| [`docs/PRE_REGISTRO.md`](docs/PRE_REGISTRO.md) | as perguntas, os testes, os limiares e a régua, escritos antes |
| [`dados/noite/`](dados/noite/) | as 2.554 versões do arquivo oficial de Presidente gravadas durante a apuração (17h20 de 25/10 a 06h56 de 26/10), com sha256 |
| `dados/brutos/` (fora do git) | boletim, registro digital do voto e log da urna de cada seção, baixados do TSE por `python -m investigacao.coleta` |
| `investigacao/` | os leitores (boletim, log) e o coletor |
| `ESTADO.md` | onde o trabalho parou |

Fonte dos dados: Tribunal Superior Eleitoral (resultados.tse.jus.br e dadosabertos.tse.jus.br). Análise feita com o Claude.
