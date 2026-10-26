# Dados locais (fora do git)

| Pasta | O quê | Tamanho aproximado | Pode apagar? |
|---|---|---|---|
| `dados/brutos/t2/` | os 4 arquivos de cada seção do 2º turno (SQLite por UF, com sha256 de cada resposta) | 85 GB | sim, depois do vídeo; refaz com `python -m investigacao.coleta t2 todas` (se o TSE mantiver os arquivos no ar) |
| `dados/brutos/t1/` | hora de recebimento e boletim do 1º turno | ~6 GB | sim |
| `dados/brutos/bweb2022/`, `bweb2026/`, `historico/`, `polymarket/` | arquivos do TSE e respostas da Polymarket | ~6 GB | sim; os manifestos (`dados/MANIFESTO_*.json`) ficam no git |
| `dados/derivados/t1/`, `t2/` | tabelas por UF | ~30 MB | sim (as tabelas nacionais `t1_secoes.parquet`, `t2_secoes.parquet` estão no git) |

O que nunca se apaga: `dados/noite/` (as versões da noite não se baixam de novo; estão no git).
