"""Histórico: compara a planilha nova com o que já está gravado e calcula,
a partir das fotos de cada importação, o estado atual e a evolução.

Identidade de uma demanda = frente › entrega › ação (texto normalizado: sem
acento, minúsculo, espaços simples). Subgrupo não entra: mudar uma ação de
subgrupo não cria demanda nova. Quando a ação é renomeada, a prévia sugere a
correspondência por semelhança de texto e a pessoa confirma.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field

import pandas as pd

from modules import importador as imp
from modules import regras

SIMILARIDADE_MINIMA = 0.75
CAMPOS_COMPARADOS = [("status", "Status"), ("data", "Prazo"), ("responsavel", "Responsável"), ("peso", "Peso")]


# ---------------------------------------------------------------------------
# Chave da demanda
# ---------------------------------------------------------------------------
def normalizar(texto: str) -> str:
    t = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().lower()


def chaves(df: pd.DataFrame) -> list[str]:
    """frente|entrega|ação normalizados; repetições na mesma entrega ganham #2, #3..."""
    vistos: dict[str, int] = {}
    saida = []
    for f, e, a in zip(df["frente"], df["entrega"], df["acao"]):
        base = f"{normalizar(f)}|{normalizar(e)}|{normalizar(a)}"
        vistos[base] = vistos.get(base, 0) + 1
        saida.append(base if vistos[base] == 1 else f"{base}#{vistos[base]}")
    return saida


def _igual(a, b) -> bool:
    vazio_a = a is None or (isinstance(a, float) and pd.isna(a)) or a == ""
    vazio_b = b is None or (isinstance(b, float) and pd.isna(b)) or b == ""
    if vazio_a or vazio_b:
        return vazio_a and vazio_b
    return a == b


def _fmt(campo: str, v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
        return "—"
    if campo == "data":
        return v.strftime("%d/%m/%Y")
    if campo == "peso":
        return f"{v:g}"
    return str(v)


# ---------------------------------------------------------------------------
# Estado atual e fotos
# ---------------------------------------------------------------------------
def _fotos(base: dict) -> pd.DataFrame:
    """Fotos válidas com a data de posição e a ordem da importação."""
    imps = base["importacoes"].reset_index(drop=True).assign(ordem=lambda d: range(len(d)))
    sit = base["situacoes"].merge(imps[["id", "data_posicao", "ordem", "enviado_por"]],
                                  left_on="importacao_id", right_on="id", how="inner").drop(columns="id")
    return sit.sort_values(["demanda_id", "ordem"]).reset_index(drop=True)


def _como_acoes(sit: pd.DataFrame) -> pd.DataFrame:
    """Fotos no mesmo formato do importador (para reaproveitar regras.py)."""
    df = sit.rename(columns={"demanda_id": "id"}).copy()
    df["pct"] = df["status"].map(imp._pct)
    for c in ("subgrupo", "responsavel", "comentario", "nota"):
        df[c] = df[c].fillna("")
    return df[["id"] + imp.COLUNAS].reset_index(drop=True)


def estado_atual(base: dict) -> pd.DataFrame:
    """Uma linha por demanda (a foto mais recente), com os campos derivados:
    ativa, incluida_em, concluida_na_ultima, concluida_em, prazo_original,
    vezes_prazo_alterado e todos os comentários já registrados."""
    if base["importacoes"].empty:
        return pd.DataFrame(columns=["id"] + imp.COLUNAS)
    fotos = _fotos(base)
    ultima = int(fotos["ordem"].max()) if len(fotos) else -1
    extras = []
    for dem_id, g in fotos.groupby("demanda_id", sort=False):
        status = list(g["status"])
        concluida = [s == "Concluído" for s in status]
        concluida_em = None
        if concluida[-1] and not all(concluida):
            i = len(concluida) - 1
            while i > 0 and concluida[i - 1]:
                i -= 1
            concluida_em = g["data_posicao"].iloc[i]
        abertas = g[~pd.Series(concluida, index=g.index)]
        datas_abertas = [d for d in abertas["data"] if d is not None]
        mudancas = 0
        datas, ests = list(g["data"]), status
        for k in range(1, len(g)):
            if ests[k - 1] != "Concluído" and datas[k - 1] is not None and datas[k] is not None and datas[k] != datas[k - 1]:
                mudancas += 1
        comentarios = list(dict.fromkeys(c for h in g["historico"] for c in h))
        ultima_ordem = int(g["ordem"].iloc[-1])
        anterior_concl = len(g) > 1 and concluida[-2]
        extras.append({
            "demanda_id": dem_id,
            "ativa": ultima_ordem == ultima,
            "incluida_em": g["data_posicao"].iloc[0],
            "visto_por_ultimo_em": g["data_posicao"].iloc[-1],
            "concluida_em": concluida_em,
            "concluida_na_ultima": bool(concluida[-1] and ultima_ordem == ultima and len(g) > 1 and not anterior_concl),
            "prazo_original": datas_abertas[0] if datas_abertas else None,
            "vezes_prazo_alterado": mudancas,
            "comentarios": comentarios,
        })
    ultimas = fotos.groupby("demanda_id", sort=False).tail(1)
    atual = _como_acoes(ultimas).merge(pd.DataFrame(extras), left_on="id", right_on="demanda_id").drop(columns="demanda_id")
    return atual.sort_values(["aba", "linha"]).reset_index(drop=True)


def ultima_importacao(base: dict) -> dict | None:
    imps = base["importacoes"]
    return None if imps.empty else imps.iloc[-1].to_dict()


def evolucao(base: dict, frentes: list[str] | None = None) -> pd.DataFrame:
    """Indicadores de cada importação, calculados na data de posição dela."""
    fotos = _fotos(base)
    if frentes:
        fotos = fotos[fotos["frente"].isin(frentes)]
    linhas = []
    for (ordem, dpos, quem), g in fotos.groupby(["ordem", "data_posicao", "enviado_por"]):
        ind = regras.indicadores(regras.classificar(_como_acoes(g), dpos))
        linhas.append({"ordem": ordem, "data_posicao": dpos, "enviado_por": quem, **ind})
    return pd.DataFrame(linhas)


def eventos(base: dict) -> pd.DataFrame:
    """O que mudou de uma importação para a seguinte."""
    fotos = _fotos(base)
    imps = base["importacoes"].reset_index(drop=True)
    linhas = []
    estado: dict[int, dict] = {}   # última foto conhecida de cada demanda
    ativos_antes: set[int] = set()
    for ordem, imp_row in imps.iterrows():
        g = fotos[fotos["ordem"] == ordem]
        ativos = set(g["demanda_id"])
        comum = dict(ordem=ordem, data_posicao=imp_row["data_posicao"], enviado_por=imp_row["enviado_por"])
        for r in g.to_dict("records"):
            nome = f"{r['frente']} › {r['entrega']} › {r['acao']}"
            anterior = estado.get(r["demanda_id"])
            if anterior is None:
                if ordem > 0:
                    linhas.append({**comum, "demanda_id": r["demanda_id"], "demanda": nome, "tipo": "Nova demanda",
                                   "de": "", "para": r["status"]})
            else:
                if r["demanda_id"] not in ativos_antes:
                    linhas.append({**comum, "demanda_id": r["demanda_id"], "demanda": nome,
                                   "tipo": "Voltou para a planilha", "de": "", "para": r["status"]})
                if normalizar(anterior["acao"]) != normalizar(r["acao"]) or                         normalizar(anterior["entrega"]) != normalizar(r["entrega"]):
                    linhas.append({**comum, "demanda_id": r["demanda_id"], "demanda": nome, "tipo": "Renomeada",
                                   "de": f"{anterior['entrega']} › {anterior['acao']}", "para": f"{r['entrega']} › {r['acao']}"})
                for campo, rotulo in CAMPOS_COMPARADOS:
                    if not _igual(anterior[campo], r[campo]):
                        linhas.append({**comum, "demanda_id": r["demanda_id"], "demanda": nome, "tipo": rotulo,
                                       "de": _fmt(campo, anterior[campo]), "para": _fmt(campo, r[campo])})
            estado[r["demanda_id"]] = r
        for dem_id in ativos_antes - ativos:
            r = estado[dem_id]
            linhas.append({**comum, "demanda_id": dem_id, "demanda": f"{r['frente']} › {r['entrega']} › {r['acao']}",
                           "tipo": "Saiu da planilha", "de": r["status"], "para": ""})
        ativos_antes = ativos
    return pd.DataFrame(linhas, columns=["ordem", "data_posicao", "enviado_por", "demanda_id", "demanda", "tipo", "de", "para"])


# ---------------------------------------------------------------------------
# Prévia da importação
# ---------------------------------------------------------------------------
@dataclass
class Plano:
    linhas: pd.DataFrame                      # planilha nova + chave, demanda_id, tipo, mudancas
    removidas: pd.DataFrame                   # demandas ativas que não vieram na planilha nova
    renomeacoes: list[dict] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)   # avisos de estrutura da planilha (importador)

    def contagem(self, tipo: str) -> int:
        return int((self.linhas["tipo"] == tipo).sum())

    def resumo(self) -> dict:
        return {"acoes": len(self.linhas), "novas": self.contagem("nova"), "atualizadas": self.contagem("atualizada"),
                "sem_mudanca": self.contagem("sem_mudanca"), "voltaram": self.contagem("voltou"),
                "sairam": len(self.removidas), "renomeadas": len(self.renomeacoes), "avisos": self.avisos}


def planejar(novo: pd.DataFrame, base: dict, recusar: set[int] = frozenset()) -> Plano:
    """Casa cada linha da planilha nova com uma demanda gravada.

    recusar: ids de demandas cuja sugestão de renomeação a pessoa NÃO aceitou."""
    linhas = novo.copy().reset_index(drop=True)
    linhas["chave"] = chaves(linhas)
    dem = base["demandas"]
    por_chave = dict(zip(dem["chave"], dem["id"])) if len(dem) else {}
    linhas["demanda_id"] = linhas["chave"].map(por_chave).astype("Int64")

    atual = estado_atual(base)
    ativos = atual[atual["ativa"]] if len(atual) else atual
    casados = set(linhas["demanda_id"].dropna().astype(int))
    sobrando = ativos[~ativos["id"].isin(casados)] if len(ativos) else ativos

    # Sugestão de renomeação: linha nova sem par x demanda ativa que sumiu, mesma frente
    renomeacoes = []
    usados: set[int] = set()
    for i in linhas.index[linhas["demanda_id"].isna()]:
        r = linhas.loc[i]
        candidatos = sobrando[(sobrando["frente"] == r["frente"]) & ~sobrando["id"].isin(usados)] if len(sobrando) else sobrando
        alvo = normalizar(f"{r['entrega']} {r['acao']}")
        melhor, nota = None, 0.0
        for c in candidatos.itertuples():
            s = difflib.SequenceMatcher(None, alvo, normalizar(f"{c.entrega} {c.acao}")).ratio()
            if s > nota:
                melhor, nota = c, s
        if melhor is not None and nota >= SIMILARIDADE_MINIMA:
            usados.add(int(melhor.id))
            renomeacoes.append({"demanda_id": int(melhor.id), "linha": int(i), "similaridade": nota,
                                "de": f"{melhor.entrega} › {melhor.acao}", "para": f"{r['entrega']} › {r['acao']}"})
            if int(melhor.id) not in recusar:
                linhas.loc[i, "demanda_id"] = int(melhor.id)

    atual_por_id = atual.set_index("id") if len(atual) else None
    tipos, mudancas = [], []
    for r in linhas.itertuples():
        if pd.isna(r.demanda_id):
            tipos.append("nova")
            mudancas.append("")
            continue
        ant = atual_por_id.loc[int(r.demanda_id)]
        difs = [f"{rot}: {_fmt(c, ant[c])} → {_fmt(c, getattr(r, c))}"
                for c, rot in CAMPOS_COMPARADOS if not _igual(ant[c], getattr(r, c))]
        if normalizar(ant["acao"]) != normalizar(r.acao) or normalizar(ant["entrega"]) != normalizar(r.entrega):
            difs.insert(0, f"Renomeada (era \"{ant['acao']}\")")
        if r.comentario and r.comentario != ant["comentario"]:
            difs.append("Comentário novo")
        tipos.append("voltou" if not ant["ativa"] else "atualizada" if difs else "sem_mudanca")
        mudancas.append("; ".join(difs))
    linhas["tipo"] = tipos
    linhas["mudancas"] = mudancas

    casados = set(linhas["demanda_id"].dropna().astype(int))
    removidas = ativos[~ativos["id"].isin(casados)] if len(ativos) else ativos
    return Plano(linhas=linhas, removidas=removidas, renomeacoes=renomeacoes)
