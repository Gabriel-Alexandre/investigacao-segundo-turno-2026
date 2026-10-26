# A noite de 25/10/2026

Gravado ao vivo por um coletor que leu o arquivo de Presidente do 2º turno do TSE (`oficial/ele2026/6258/dados/<uf>/<uf>-c0001-e006258-u.json`) a cada 20 segundos (país) e em rodízio (UFs), de 17h20 de 25/10 às 06h56 de 26/10. O TSE sobrescreve esse arquivo: estas versões não se baixam de novo.

| Arquivo | O quê |
|---|---|
| `versoes-tse/<uf>/<idg>.json` | cada versão nova do arquivo (2.554) |
| `MANIFESTO_AO_VIVO.jsonl` | hora da leitura, hora de geração, % de seções, sha256, tamanho e endereço de cada versão. ⚠️ O campo `arquivo` aponta para `dados/brutos/ao-vivo/...`, o caminho do projeto original; aqui é `dados/noite/versoes-tse/...` |
| `BATIDAS_AO_VIVO.csv` | cada leitura, mudando ou não |
| `contas-parciais-20h29/` | as contas do projeto da noite feitas com 52% das seções (não são resultado final) |
| `docs-da-noite/` | o pré-registro da noite (escrito às 23h10 de 24/10, antes da votação), a pausa da divulgação com as fontes, a leitura parcial e as fontes |
| `referencias/` | os arquivos do 1º turno e dos projetos anteriores que a noite usou, com o manifesto |
| `historico-git-do-projeto-da-noite.bundle` | o histórico git do projeto da noite (`apuracao-segundo-turno-2026`, apagado do GitHub em 26/10). `git clone historico-git-do-projeto-da-noite.bundle` mostra a ordem dos commits, com o pré-registro em `e1d65f6` (24/10/2026 23h10) |
