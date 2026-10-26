"""Nome de cada município, lido da configuração de seções do TSE (cs.json do 2º turno). Saída: dados/derivados/municipios_nomes.csv"""
import csv, json, sqlite3
from pathlib import Path
R = Path(__file__).resolve().parents[1]
linhas = []
for p in sorted((R / "dados/brutos/t2").glob("*.sqlite")):
    uf = p.stem
    b = sqlite3.connect(p).execute("select body from raw where url like '%config%' and status=200").fetchone()[0]
    for abr in json.loads(b)["abr"]:
        for mu in abr["mu"]:
            linhas.append({"uf": uf, "municipio": mu["cd"], "nome": mu["nm"]})
with open(R / "dados/derivados/municipios_nomes.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["uf", "municipio", "nome"]); w.writeheader(); w.writerows(linhas)
print(len(linhas))
