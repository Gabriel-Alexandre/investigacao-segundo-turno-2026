"""Confere o texto público: travessão, palavras que julgam intenção ou concluem fraude em geral, e recomendação de voto."""
import re, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
ARQS = [R / "RELATORIO.md", R / "RESUMO_SIMPLES.md", R / "README.md", R / "docs/LEITURA_DA_IA.md", R / "docs/OUTROS_PAISES.md", R / "docs/RODADAS.md", R / "docs/REVISAO_ADVERSARIAL.md"]
PROIBIDO = [("—", "travessão"), (r"\bhouve fraude\b", "conclusão geral de fraude"), (r"\bnão houve fraude\b", "conclusão geral de que não houve fraude"),
            (r"\bprovou que\b", "prova geral"), (r"\bfraudulent[ao]s?\b", "rótulo de fraude em seção"), (r"\bvote em\b", "recomendação de voto"),
            (r"\bmentiu\b", "julgamento de intenção"), (r"\bmanipularam\b", "julgamento de intenção")]
erros = []
for a in ARQS:
    if not a.exists():
        continue
    for n, linha in enumerate(a.read_text(encoding="utf-8").splitlines(), 1):
        for pat, nome in PROIBIDO:
            if re.search(pat, linha, re.I) and "PROIBIDO" not in linha:
                erros.append(f"{a.name}:{n}: {nome}: {linha.strip()[:100]}")
print("\n".join(erros) if erros else "linguagem ok")
sys.exit(1 if erros else 0)
