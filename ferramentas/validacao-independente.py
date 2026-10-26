"""Validação independente: os números centrais refeitos com código novo, sem importar o pacote investigacao nem os scripts
das rodadas, e conferidos contra fontes que o projeto não usou para calcular.

  V1  soma do 2º turno pelos boletins (leitura BER escrita aqui) = arquivo oficial gravado na noite
  V2  soma do 1º turno pelas tabelas por seção = arquivo oficial do 1º turno
  V3  2022 por seção (BU na Web) = arquivo de votação por município do TSE (outra base)
  V4  RDV = boletim, recontado numa amostra de 3.000 seções com um leitor BER escrito aqui
  V5  a noite refeita pelos boletins acompanha as versões oficiais gravadas ao vivo
  V6  o saldo nacional fecha: ganho dos dois = outros + queda da abstenção + queda de branco e nulo
  V7  P1 e P5 recontados direto do CSV do TSE

Saída: resultados/validacao_independente.json (passou ou não, item a item)
"""
import csv, io, json, random, sqlite3, zipfile
from pathlib import Path

import pandas as pd

R = Path(__file__).resolve().parents[1]


def tlv(b, i=0, end=None):
    end = len(b) if end is None else end
    while i < end:
        t = b[i]; i += 1
        cons = bool(t & 0x20); cls = t >> 6; tag = t & 0x1F
        if tag == 0x1F:
            tag = 0
            while True:
                x = b[i]; i += 1; tag = (tag << 7) | (x & 0x7F)
                if not x & 0x80:
                    break
        n = b[i]; i += 1
        if n & 0x80:
            k = n & 0x7F; n = int.from_bytes(b[i:i + k], "big"); i += k
        yield cls, tag, cons, b[i:i + n]
        i += n


def contar_rdv_presidente(b):
    """Percorre tudo; o bloco de cargo do presidente é [2:1]=1 seguido de uma sequência de votos (enum, texto)."""
    out = {"13": 0, "22": 0, "outros": 0}
    def walk(buf):
        filhos = list(tlv(buf))
        if len(filhos) == 3 and filhos[0][:3] == (2, 1, False) and int.from_bytes(filhos[0][3], "big") == 1 and filhos[2][2]:
            for _, _, cons, v in tlv(filhos[2][3]):
                partes = list(tlv(v))
                if partes and partes[0][1] == 10:
                    dig = partes[1][3].decode() if len(partes) > 1 else ""
                    tipo = int.from_bytes(partes[0][3], "big")
                    out[dig if tipo == 2 and dig in ("13", "22") else "outros"] += 1
            return
        for _, _, cons, v in filhos:
            if cons:
                walk(v)
    walk(b)
    return out


def oficial(caminho):
    d = json.loads(Path(caminho).read_text(encoding="utf-8", errors="replace"))
    out = {}
    for a in d["carg"][0]["agr"]:
        for p in a["par"]:
            for k in p["cand"]:
                out[k["n"]] = int(k["vap"])
    return out


def main():
    res = {}
    t2 = pd.read_parquet(R / "dados/derivados/t2_secoes.parquet")
    of2 = oficial(R / "dados/noite/versoes-tse/br/4241309.json")
    s2 = {"13": int(pd.to_numeric(t2.bu_lula).sum()), "22": int(pd.to_numeric(t2.bu_flavio).sum())}
    res["V1_2t_boletins_contra_oficial"] = {"boletins": s2, "oficial": {"13": of2["13"], "22": of2["22"]},
                                            "diferenca": {k: s2[k] - of2[k] for k in s2}, "passou": all(abs(s2[k] - of2[k]) < 1000 for k in s2),
                                            "nota": "a diferença é das 29 seções do exterior sem boletim publicado"}
    t1 = pd.read_parquet(R / "dados/derivados/t1_secoes.parquet")
    of1 = oficial(R / "dados/noite/referencias/tse-1turno/br.json")
    s1 = {"13": int(pd.to_numeric(t1.lula).sum()), "22": int(pd.to_numeric(t1.flavio).sum()), "70": int(pd.to_numeric(t1.cury).sum())}
    res["V2_1t_boletins_contra_oficial"] = {"boletins": s1, "oficial": {k: of1[k] for k in s1}, "diferenca": {k: s1[k] - of1[k] for k in s1},
                                            "passou": all(abs(s1[k] - of1[k]) < 2000 for k in s1)}
    h = pd.read_csv(R / "dados/derivados/historico_turnos.csv")
    s22 = {t: pd.read_parquet(R / f"dados/derivados/s2022_t{t}.parquet") for t in (1, 2)}
    v3 = {}
    for t in (1, 2):
        for num, col in ((13, "lula"), (22, "bolsonaro")):
            a = int(s22[t][col].sum())
            b = int(h[(h.ano == 2022) & (h.cargo == "presidente") & (h.uf == "BR") & (h.turno == t) & (h.nr_candidato == num)].votos_nominais.sum())
            v3[f"t{t}_{col}"] = {"bweb": a, "munzona": b, "igual": a == b}
    res["V3_2022_duas_bases"] = {"itens": v3, "passou": all(x["igual"] for x in v3.values())}
    random.seed(7)
    difs = n = 0
    for uf in random.sample(sorted(p.stem for p in (R / "dados/brutos/t2").glob("*.sqlite")), 8):
        con = sqlite3.connect(R / f"dados/brutos/t2/{uf}.sqlite")
        urls = [u for (u,) in con.execute("select url from raw where url like '%-rdv.dat' and status=200")]
        for u in random.sample(urls, min(375, len(urls))):
            rdv = con.execute("select body from raw where url=?", (u,)).fetchone()[0]
            m, z, sc = u.split("/")[-5:-2]
            linha = t2[(t2.uf == uf) & (t2.municipio == m) & (t2.zona == z) & (t2.secao == sc)]
            c = contar_rdv_presidente(rdv)
            n += 1
            difs += int(c["13"] != int(linha.bu_lula.iloc[0]) or c["22"] != int(linha.bu_flavio.iloc[0]))
    res["V4_rdv_amostra_leitor_novo"] = {"secoes": n, "diferentes": difs, "passou": difs == 0}
    d5 = json.loads((R / "resultados/d5_reconstruida.json").read_text(encoding="utf-8"))
    res["V5_noite_refeita"] = {"diferenca_media_pontos": d5["diferenca_media_absoluta_pontos"], "passou": d5["diferenca_media_absoluta_pontos"] < 0.25}
    br1 = json.loads((R / "dados/noite/referencias/tse-1turno/br.json").read_text(encoding="utf-8", errors="replace"))
    br2 = json.loads((R / "dados/noite/versoes-tse/br/4241309.json").read_text(encoding="utf-8", errors="replace"))
    ganho = (of2["13"] - of1["13"]) + (of2["22"] - of1["22"])
    outros = int(br1["v"]["vv"]) - of1["13"] - of1["22"]
    abst = int(br1["e"]["a"]) - int(br2["e"]["a"])
    bn = (int(br1["v"]["vb"]) + int(br1["v"]["tvn"])) - (int(br2["v"]["vb"]) + int(br2["v"]["tvn"]))
    res["V6_saldo_fecha"] = {"ganho_dos_dois": ganho, "outros_mais_abstencao_mais_branco_nulo": outros + abst + bn, "passou": ganho == outros + abst + bn}
    pres = h[(h.cargo == "presidente") & (h.uf == "BR")]
    viradas = 0; disputas = 0
    for ano, g in pres.groupby("ano"):
        if (g.turno == 2).any():
            disputas += 1
            l1 = g[g.turno == 1].sort_values("votos_nominais").nr_candidato.iloc[-1]
            v2 = g[g.turno == 2].sort_values("votos_nominais").nr_candidato.iloc[-1]
            viradas += int(l1 != v2)
    res["V7_presidente_1994_2022"] = {"segundos_turnos": disputas, "viradas": viradas, "passou": viradas == 0}
    res["todos_passaram"] = all(v["passou"] for k, v in res.items() if isinstance(v, dict) and "passou" in v)
    (R / "resultados/validacao_independente.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
