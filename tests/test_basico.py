import json
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[1]


def test_secoes_do_2t():
    d = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
    assert len(d) == 499248


def test_soma_do_2t_bate_com_o_oficial():
    r = json.loads((R / "resultados/rodada2.json").read_text(encoding="utf-8"))["reconciliacao"]
    assert abs(r["diferenca_lula"]) < 1000 and abs(r["diferenca_flavio"]) < 1000


def test_rdv_igual_ao_boletim_nos_candidatos():
    r = json.loads((R / "resultados/rodada2.json").read_text(encoding="utf-8"))["A4_rdv_contra_boletim"]
    assert r["votos_lula_diferenca"] == 0 and r["votos_flavio_diferenca"] == 0


def test_validacao_independente():
    r = json.loads((R / "resultados/validacao_independente.json").read_text(encoding="utf-8"))
    assert r["todos_passaram"]


def test_dados_da_noite_intactos():
    import hashlib
    ok = 0
    for linha in open(R / "dados/noite/MANIFESTO_AO_VIVO.jsonl", encoding="utf-8"):
        x = json.loads(linha)
        p = R / x["arquivo"].replace("dados/brutos/ao-vivo", "dados/noite/versoes-tse")
        ok += hashlib.sha256(p.read_bytes()).hexdigest() == x["sha256"]
    assert ok == 2554
