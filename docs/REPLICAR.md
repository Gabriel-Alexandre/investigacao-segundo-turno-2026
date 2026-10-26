# Como refazer tudo

```bash
python -m pip install aiohttp pandas pyarrow numpy scipy matplotlib pytest
python -m investigacao.coleta t2 todas      # 2º turno: ~5 h, ~85 GB
python -m investigacao.coleta t1 todas      # 1º turno: ~2,5 h
python ferramentas/bweb-2026-1t.py          # SP, TO e exterior do 1º turno pelo BU na Web (emenda 1)
python ferramentas/historico-2022.py        # régua de 2022
python ferramentas/historico-turnos.py      # TSE 1994 a 2022
python ferramentas/derivar-t2.py todas
python ferramentas/derivar-t1.py todas      # depois rode bweb-2026-1t.py de novo para SP, TO e exterior
python ferramentas/municipios-nomes.py
python ferramentas/rodada-2.py
python ferramentas/rodada-3.py
python ferramentas/rodada-3-d2.py
python ferramentas/d5-curva-da-noite.py && python ferramentas/d5-curva-reconstruida.py
python ferramentas/bloco-p-historico.py && python ferramentas/bloco-p-pesquisas.py && python ferramentas/pesquisas-2026.py
python ferramentas/polymarket.py && python ferramentas/polymarket-curadoria.py
python ferramentas/bloco-p6-outros-paises.py && python ferramentas/bloco-p-combinado.py
python ferramentas/validacao-independente.py && python ferramentas/revisao-adversarial.py
python ferramentas/gerar-relatorio.py && python ferramentas/gerar-resumo.py && python ferramentas/graficos.py
python ferramentas/conferir-linguagem.py && python -m pytest -q
```

O TSE pode responder 429 (limite de acesso): o coletor reduz a velocidade sozinho e retoma de onde parou.
