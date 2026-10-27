"""Rodada 7 (27/10/2026), pelo retorno do autor ao roteiro:

  R7a  o vídeo do professor, lido de novo. A crítica dele não era sobre embaralhar a ordem: era que, com zoom, a linha do
       Bolsonaro de 2022 desce "linearmente", com "vales igualmente espaçados", "como se fosse um programa" penalizando o
       candidato. O teste certo: refazer a curva com o resultado que cada seção teria se repetisse o próprio 1º turno
       (mais a mudança do país entre os turnos), na mesma ordem de chegada. Se a curva prevista desce no mesmo ritmo e cai
       nos mesmos lugares, a descida é a ordem em que as seções chegaram, com o voto de cada uma parecido com o dela mesma
       no 1º turno; se a curva real desce e a prevista não, sobra algo que a composição não explica.
  R7b  a conclusão por critério com os pesos do autor (emenda 4, `PRE_REGISTRO.md`): os arquivos das urnas passam a pesar
       menos, porque batem nas duas lentes; o comportamento dos votos pesa mais, somado ao que o projeto do vídeo 19
       mediu (cópia com sha256 em `dados/copias/`).

Saída: resultados/rodada7.json
"""
from __future__ import annotations

import hashlib, importlib.util, json, shutil
from pathlib import Path

import numpy as np
import pandas as pd

R = Path(__file__).resolve().parents[1]
sp = importlib.util.spec_from_file_location("r6", R / "ferramentas/rodada-6-curva.py")
r6 = importlib.util.module_from_spec(sp); sp.loader.exec_module(r6)
CH = ["uf", "mun", "zona", "secao"]
P19 = R.parent / "pesquisas-e-resultado-segundo-turno-2026" / "resultados" / "RESUMO.json"


def primeiro_turno(ano: int) -> pd.DataFrame:
    if ano == 2022:
        d = pd.read_parquet(R / "dados/derivados/s2022_t1.parquet")
        return pd.DataFrame({"uf": d.uf.astype(str), "mun": d.municipio.astype(str), "zona": d.zona.astype(str),
                             "secao": d.secao.astype(str), "esq1": d.lula, "dir1": d.bolsonaro})
    d = pd.read_parquet(R / "dados/derivados/t1_secoes.parquet", columns=["uf", "municipio", "zona", "secao", "lula", "flavio"])
    return pd.DataFrame({"uf": d.uf.str.upper(), "mun": d.municipio, "zona": d.zona, "secao": d.secao,
                         "esq1": pd.to_numeric(d.lula, errors="coerce"), "dir1": pd.to_numeric(d.flavio, errors="coerce")})


def ordenar(s: pd.DataFrame) -> pd.DataFrame:
    s = s.dropna(subset=["rec"]).sort_values(["rec", "uf", "mun", "zona", "secao"]).reset_index(drop=True)
    for c in CH:
        s[c] = s[c].astype(str)
    return s


def curva_prevista(ano: int, s: pd.DataFrame) -> dict:
    t1 = primeiro_turno(ano)
    if ano == 2022:  # o boletim na web de 2022 não tem zero à esquerda; o derivado do 1º turno também não
        for c in CH[1:]:
            s[c] = s[c].str.lstrip("0"); t1[c] = t1[c].str.lstrip("0")
    m = s.merge(t1, on=CH, how="left")
    casadas = float(m.esq1.notna().mean() * 100)
    tot2 = (m.esq + m.dir).to_numpy(float)
    p1 = (m.esq1 / (m.esq1 + m.dir1)).to_numpy(float)
    nac1 = float(m.esq1.sum() / (m.esq1.sum() + m.dir1.sum()))
    nac2 = float(m.esq.sum() / (m.esq.sum() + m.dir.sum()))
    p1 = np.where(np.isfinite(p1), p1, nac1)
    pred_esq = tot2 * np.clip(p1 + (nac2 - nac1), 0, 1)
    real = np.cumsum(m.dir.to_numpy(float)) / np.maximum(np.cumsum(tot2), 1) * 100
    prev = np.cumsum(tot2 - pred_esq) / np.maximum(np.cumsum(tot2), 1) * 100
    n = len(m); i1 = n // 100
    out = {"secoes": n, "casadas_com_o_1o_turno_pct": round(casadas, 2),
           "diferenca_media_entre_as_curvas_depois_de_1pct_pontos": round(float(np.abs(real[i1:] - prev[i1:]).mean()), 3),
           "diferenca_maxima_depois_de_1pct_pontos": round(float(np.abs(real[i1:] - prev[i1:]).max()), 3),
           "correlacao_das_curvas_depois_de_1pct": round(float(np.corrcoef(real[i1:], prev[i1:])[0, 1]), 4)}
    # trocas de liderança na prevista
    g = np.sign(prev - 50)
    mud = np.where((g[1:] != g[:-1]) & (g[1:] != 0) & (g[:-1] != 0))[0] + 1
    out["trocas_na_prevista_depois_de_1pct"] = sorted({str(s.rec.iloc[i])[:16] for i in mud if i > i1})
    g = np.sign(real - 50)
    mud = np.where((g[1:] != g[:-1]) & (g[1:] != 0) & (g[:-1] != 0))[0] + 1
    out["trocas_na_real_depois_de_1pct"] = sorted({str(s.rec.iloc[i])[:16] for i in mud if i > i1})
    if ano == 2022:
        a, b = 55000, 90000
        x = np.arange(a, b)
        sr, _ = np.polyfit(x, real[a:b], 1); sp_, _ = np.polyfit(x, prev[a:b], 1)
        res = real[a:b] - np.polyval(np.polyfit(x, real[a:b], 1), x)
        r2 = 1 - res.var() / real[a:b].var()
        q = pd.read_csv(R / "resultados/rodada6_quedas_2022.csv")
        quedas = []
        for i in q.secao_na_ordem.astype(int):
            quedas.append({"secao_na_ordem": int(i), "queda_real_pontos": round(float(real[i] - real[i - 60]), 4),
                           "queda_prevista_pontos": round(float(prev[i] - prev[i - 60]), 4)})
        out["trecho_do_video_55k_a_90k"] = {
            "descida_real_por_10_mil_secoes_pontos": round(float(sr * 1e4), 4),
            "descida_prevista_por_10_mil_secoes_pontos": round(float(sp_ * 1e4), 4),
            "quanto_a_reta_explica_da_curva_real_r2": round(float(r2), 3),
            "quedas_que_tambem_aparecem_na_prevista": int(sum(1 for z in quedas if z["queda_prevista_pontos"] < 0)),
            "quedas": quedas}
    return out


def conclusao() -> dict:
    (R / "dados/copias").mkdir(exist_ok=True)
    shutil.copy2(P19, R / "dados/copias/RESUMO_video19.json")
    h = hashlib.sha256((R / "dados/copias/RESUMO_video19.json").read_bytes()).hexdigest()
    r4 = pd.read_csv(R / "resultados/rodada4_por_ano.csv").set_index("ano")
    r3 = json.loads((R / "resultados/rodada3.json").read_text(encoding="utf-8"))
    return {
        "emenda": 4, "copia_do_projeto_do_video_19_sha256": h,
        "criterios": [
            {"ordem": 1, "nome": "o comportamento dos votos", "peso": "maior",
             "o_que_entra": "os 3 sinais deste projeto (A1, A3, A10) e o que sai do padrão de 2002 a 2022 (rodadas 4 e 5 e o projeto do vídeo 19)",
             "a_favor_da_lente_da_fraude": [
                 f"votos dos outros candidatos, de quem voltou e de quem largou branco ou nulo: o PT ficou com {r4.loc[2026,'parte_do_pt_nos_votos_livres_pct']}% com quem saiu apoiando o adversário (nunca desde 2002)",
                 f"comparecimento de {100-r4.loc[2026,'abstencao_1t_pct']:.2f}% para {100-r4.loc[2026,'abstencao_2t_pct']:.2f}% (nunca subiu tanto desde 2002)",
                 "148.092 votos do Lula que não cabem no que estava livre na seção (3,3% da margem)",
                 "857 seções com salto de comparecimento e mais de 80% para o Lula, contra 548 esperadas pelo próprio município",
                 "1.686 seções com mais de 95% para o Lula contra 39 do Flávio"],
             "a_favor_da_lente_legitima": [
                 "o espelho de 2022: o eleitor de quem apoiou o Lula foi 70% para o Bolsonaro",
                 "as pesquisas erraram justamente esse eleitor (projeto do vídeo 19)",
                 "nas 857 seções o voto a mais entrou com a digital do próprio eleitor (liberação sem digital menos de 1% acima do município)",
                 "2022 teve 2.369 seções acima de 95% para o Lula, e as de 2026 já eram assim no 1º turno",
                 "o ganho do Lula aparece no país inteiro, sem lugar onde se concentre, e até nos 1.133 municípios onde ninguém novo foi votar (projeto do vídeo 19)",
                 "os 3 sinais juntos ficam abaixo de 1,1 milhão de votos, menos da metade dos 2,2 milhões que virariam o resultado"],
             "veredito": "a lente do resultado legítimo fica um pouco na frente: os padrões são estranhos de verdade, mas não têm a forma que um voto acrescentado teria (concentrado, sem digital, só onde mais gente voltou)"},
            {"ordem": 2, "nome": "a raridade", "peso": "médio",
             "o_que_entra": "a chance antes da votação e as regras de presidente (projeto do vídeo 19)",
             "veredito": "a lente da fraude fica na frente: a chance do Lula era de 27% pelo vídeo 19, improvável e não impossível; as 4 regras quebraram juntas por serem o mesmo fato"},
            {"ordem": 3, "nome": "os arquivos das urnas", "peso": "menor (emenda 4)",
             "por_que_pesa_menos": "a lista de cada voto bater com o boletim é o esperado nas duas lentes: se a fraude acontecesse dentro do TSE, os arquivos publicados viriam iguais",
             "a_favor_da_lente_legitima": "o boletim é impresso e afixado na seção antes de chegar ao TSE, então um ajuste dentro do TSE teria de bater com o papel de 499 mil seções; o teste de integridade do 2º turno não achou divergência",
             "veredito": "a lente do resultado legítimo fica na frente, com peso pequeno"}],
        "soma": "o resultado legítimo fica um pouco na frente, sem prova para nenhum lado: há padrões estranhos e uma chance pequena; cada um tem uma explicação que já aconteceu antes; prova de fraude não aparece no dado público, e o que esse dado não deixa ver está dentro do TSE (inclusive o processamento entre 17h e 19h, quando a divulgação parou)",
        "a_anulacao": "anular uma eleição exige prova, e o dado público não traz prova",
        "sinais_detalhe": {"A3_liberacao_sem_digital": r3["A3_enchimento"].get("liberacao_sem_digital_nas_secoes_marcadas")}}


def main():
    s22 = ordenar(r6.secoes_2022())
    s26 = ordenar(r6.secoes_2026())
    out = {"R7a_curva_prevista": {"2022": curva_prevista(2022, s22), "2026": curva_prevista(2026, s26)},
           "R7b_conclusao": conclusao()}
    (R / "resultados/rodada7.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "trecho_do_video_55k_a_90k"} for k, v in out["R7a_curva_prevista"].items()}, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out["R7a_curva_prevista"]["2022"]["trecho_do_video_55k_a_90k"].items() if k != "quedas"}, indent=1))


if __name__ == "__main__":
    main()
