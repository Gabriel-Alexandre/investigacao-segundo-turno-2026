# Revisão adversarial

Dois papéis, cada objeção virando conta (`resultados/revisao_adversarial.json`, gerado por `ferramentas/revisao-adversarial.py`).

## Advogado da acusação

- **a volta de quem faltou e a queda do nulo podem esconder troca; conte só os votos dos outros candidatos.** excesso lula: 2.585.677; excesso flavio: 120.033; excesso lula contra margem pct: 58,36.
- **a prorrogação favoreceu um lado.** votos depois 17h onde o lula venceu: 20.127; contra margem pct: 0,45.
- **seções com mais de 95% para o Lula podem ser manipuladas.** secoes: 1.686; vantagem do lula nelas: 299.018; contra margem pct: 6,75; ja eram acima de 90 no 1t: 1.666.
- **a fraude pode estar espalhada no 1% de seções que mais passaram do previsto pelo 1º turno.** secoes: 4.991; residuo medio pontos: 6,67; votos a mais do lula se voltassem ao previsto: 70.225; contra margem pct: 1,59.

## Advogado da defesa

- **um modelo único para o país marca como anomalia o que é diferença regional.** residuo medio por regiao: {"Centro-Oeste": -0.592, "Exterior": -0.998, "Nordeste": 0.026, "Norte": -0.11, "Sudeste": 0.38, "Sul": -0.726}.
- **seção com mais de 95% para o Lula é comum no Nordeste e em aldeias, não só em 2026.** lula acima 95 em 2022: 2369; bolsonaro acima 95 em 2022: 21.
- **inferência ecológica pode inventar transferências.** ciro modelo: {"para_lula_pct": 40.3, "para_o_outro_pct": 42.4, "branco_nulo_pct": 17.3}; tebet modelo: {"para_lula_pct": 37.8, "para_o_outro_pct": 44.2, "branco_nulo_pct": 18.0}; datafolha 5 7 out 2022: {"ciro": {"lula": 31, "bolsonaro": 42, "branco_nulo": 22, "indecisos": 5}, "tebet": {"lula": 31, "bolsonaro": 29, "branco_nulo": 28, "indecisos": 12}}; mesmo lado que o datafolha: True.

Nenhuma objeção muda o resultado de um teste; o efeito de cada uma está publicado acima. A revisão foi feita pela mesma IA, não por pessoa (limite declarado).
