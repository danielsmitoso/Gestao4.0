"""Planilha de exemplo FICTÍCIA no mesmo formato da planilha da equipe.

Serve para conhecer o app sem dado real e como modelo de preenchimento.
As datas são relativas à data-base, para sempre haver ações atrasadas, da
semana e futuras.
"""
from __future__ import annotations

import copy
import io
from datetime import date, timedelta

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

FUNDO_ENTREGA = PatternFill("solid", fgColor="FF6666FF")
FUNDO_CABECALHO = PatternFill("solid", fgColor="FF3D1A9E")
LINHA_CABECALHO = 7
N_SEMANAS = 6

# (frente, [(entrega, [ação | ("#subgrupo",) ...])]); ação = (nome, resp, status, peso, dias_ate_prazo, comentário)
EXEMPLO = [
    ("Fábrica de Placas", [
        ("Equipe", [
            ("Contratação de operador de plotter", "Ana", "Concluído", 2, -12, "Concluído"),
            ("Integração do novo supervisor", "Ana", "Em andamento", 3, 4, "Agenda de integração enviada"),
            ("Escala de férias do 1º semestre", "Ana", "À iniciar", 1, 20, ""),
        ]),
        ("Manutenção da fábrica", [
            ("Ar-condicionado da produção", "Facilities", "À iniciar", 3, 2, "Abertura de chamado Facilities"),
            ("Troca de lâmpadas do galpão", "Facilities", "Em andamento", 1, -3, "Aguardando retorno do fornecedor"),
            ("Revisão dos compressores", "Bruno", "À iniciar", 2, None, ""),
        ]),
        ("Plano de produção", [
            ("#Estoque",),
            ("Definir estoque padrão por tipo de placa", "Carla", "Em andamento", 3, -5, "Levantando histórico"),
            ("Catalogar placas prontas", "Diego", "Concluído", 2, -2, "Concluído"),
            ("#Execução",),
            ("Plano de impressão semanal", "Bruno", "À iniciar", 3, 6, ""),
            ("Planejamento de entregas às unidades", "Bruno, Carla", "Em andamento", 2, 15, "Rotas em revisão"),
            ("Placas sem informação da unidade", "", "", None, None, ""),
        ]),
    ]),
    ("Centralização", [
        ("Padronização dos formulários", [
            ("Desenho do fluxo de solicitação", "Diego", "Concluído", 2, -20, "Concluído"),
            ("Formulário Hub Sul", "Diego", "Concluído", 1, -9, "Concluído"),
            ("Formulário Hub Norte", "Diego", "Em andamento", 1, -1, "Em teste com a unidade"),
            ("Operação assistida", "Bruno", "À iniciar", 3, 30, ""),
        ]),
        ("Kick-off com as unidades", [
            ("Passo a passo para solicitantes", "Diego", "Concluído", 2, -4, "Concluído"),
            ("Treinamento das unidades", "Diego", "Em andamento", 3, 3, "2 de 5 unidades treinadas"),
            ("E-mail formalizando a transição", "Ana", "Em andamento", 2, -6, "Enviado para 3 hubs"),
        ]),
    ]),
    ("Novos Negócios", [
        ("Projeto Alfa - Orçamento", [
            ("Pacote de conservação", "Eva / Bruno", "Em andamento", 2, 10, "Premissas validadas"),
            ("Sinalização horizontal", "Eva", "À iniciar", 2, None, ""),
            ("Sinalização vertical", "", "À iniciar", 2, None, ""),
        ]),
    ]),
]


# Versão 2 = a mesma planilha uma semana depois (para o modo demonstração mostrar histórico)
MUDANCAS_V2 = {
    "Integração do novo supervisor": dict(status="Concluído", comentario="Concluído"),
    "Ar-condicionado da produção": dict(status="Em andamento", dias=9, comentario="Técnico agendado"),
    "Formulário Hub Norte": dict(status="Concluído", comentario="Concluído"),
    "Treinamento das unidades": dict(dias=10, comentario="3 de 5 unidades treinadas"),
    "Catalogar placas prontas": dict(nome="Catalogar as placas prontas"),
}
REMOVIDAS_V2 = {"Escala de férias do 1º semestre"}
NOVAS_V2 = {"Projeto Alfa - Orçamento": [("Manutenção de EPS", "Eva", "À iniciar", 1, 12, "")]}


def _dados(versao: int):
    dados = copy.deepcopy(EXEMPLO)
    if versao == 1:
        return dados
    for _, entregas in dados:
        for j, (entrega, acoes) in enumerate(entregas):
            novas = []
            for a in acoes:
                if len(a) > 1 and a[0] in REMOVIDAS_V2:
                    continue
                if len(a) > 1 and a[0] in MUDANCAS_V2:
                    m = MUDANCAS_V2[a[0]]
                    nome, resp, status, peso, dias, coment = a
                    a = (m.get("nome", nome), resp, m.get("status", status), peso, m.get("dias", dias),
                         m.get("comentario", coment))
                novas.append(a)
            novas += NOVAS_V2.get(entrega, [])
            entregas[j] = (entrega, novas)
    return dados


def _aba(wb, frente, entregas, base: date):
    ws = wb.create_sheet(frente)
    ws["C2"] = frente.upper()
    ws["C2"].font = Font(bold=True, size=16, color="FF3D1A9E")
    ws["C3"] = "LISTA DE TAREFAS PENDENTES"
    semanas = [(base - timedelta(days=base.weekday()) + timedelta(weeks=i - 1)) for i in range(N_SEMANAS)]
    cab = ["Avanço", "Tarefa", "Responsável", "Status", "Peso", "%", "Data Prevista/conclusão"] + \
          [f"{s:%d/%m/%Y}" for s in semanas]
    for j, t in enumerate(cab, start=2):
        c = ws.cell(LINHA_CABECALHO, j, t)
        c.font = Font(bold=True, color="FFFFFFFF")
        c.fill = FUNDO_CABECALHO
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    status_dv = DataValidation(type="list", formula1='"À iniciar,Em andamento,Concluído"', allow_blank=True)
    peso_dv = DataValidation(type="list", formula1='"1,2,3"', allow_blank=True)
    ws.add_data_validation(status_dv)
    ws.add_data_validation(peso_dv)

    r = LINHA_CABECALHO + 1
    for entrega, acoes in entregas:
        c = ws.cell(r, 3, entrega)
        c.font, c.fill = Font(bold=True, color="FFFFFFFF"), FUNDO_ENTREGA
        r += 1
        for a in acoes:
            if len(a) == 1:
                ws.cell(r, 3, a[0][1:]).font = Font(bold=True)
                r += 1
                continue
            nome, resp, status, peso, dias, coment = a
            ws.cell(r, 3, nome)
            ws.cell(r, 4, resp or None)
            ws.cell(r, 5, status or None)
            ws.cell(r, 6, peso)
            ws.cell(r, 7, {"Concluído": 1, "Em andamento": 0.5}.get(status, 0)).number_format = "0%"
            if dias is not None:
                ws.cell(r, 8, base + timedelta(days=dias)).number_format = "DD/MM/YYYY"
            if coment:
                ws.cell(r, 9 + N_SEMANAS - 2, coment)  # comentário na semana corrente
            status_dv.add(f"E{r}")
            peso_dv.add(f"F{r}")
            r += 1
    for col, w in {"C": 45, "D": 16, "E": 14, "F": 7, "G": 7, "H": 14}.items():
        ws.column_dimensions[col].width = w


def gerar_planilha_exemplo(base: date | None = None, versao: int = 1) -> bytes:
    base = base or date.today()
    wb = openpyxl.Workbook()
    instr = wb.active
    instr.title = "Instruções"
    linhas = [
        "PLANILHA DE EXEMPLO (dados fictícios) — mesmo formato da planilha da equipe",
        "",
        "• Uma aba por FRENTE. Linha 7: cabeçalho com 'Tarefa' na coluna C.",
        "• ENTREGA (tarefa principal): texto em negrito com fundo colorido.",
        "• SUBGRUPO (opcional): texto em negrito sem fundo.",
        "• AÇÃO: demais linhas — Responsável, Status (À iniciar / Em andamento / Concluído), Peso (1 a 3),",
        "  Data prevista (ou de conclusão, se concluída) e comentários por semana nas colunas seguintes.",
        "• O app recalcula % e avanço; as fórmulas da planilha não são usadas.",
    ]
    for i, t in enumerate(linhas, 1):
        instr.cell(i, 1, t)
    instr["A1"].font = Font(bold=True, size=13, color="FF5E22F3")
    instr.column_dimensions["A"].width = 110
    for frente, entregas in _dados(versao):
        _aba(wb, frente, entregas, base)
    modelo = wb.create_sheet("Modelo vazio")  # mostra que aba só com modelo é ignorada
    modelo.cell(LINHA_CABECALHO, 3, "Tarefa")
    modelo.cell(LINHA_CABECALHO + 1, 3, "TAREFA PRINCIPAL").font = Font(bold=True)
    modelo.cell(LINHA_CABECALHO + 1, 3).fill = FUNDO_ENTREGA
    for r in range(LINHA_CABECALHO + 2, LINHA_CABECALHO + 6):
        modelo.cell(r, 3, "AÇÕES")
    saida = io.BytesIO()
    wb.save(saida)
    return saida.getvalue()
