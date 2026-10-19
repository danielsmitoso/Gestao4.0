# Gestão de Demandas NTec — proposta do primeiro esboço

> Versão 0.1 · 19/10/2026 · base: `Gestão 4.0 - NTec.xlsx`
> Visual navegável com os dados reais: `esboco/esboco_painel.html` (abre no navegador)

## 1. Objetivo

Repetir a lógica do DimConservação: **sobe a planilha → o app lê, confere e
gera sozinho os painéis**. A equipe continua preenchendo o Excel como hoje (sem
mudar hábito na Fase 1); o app passa a responder, em segundos, as perguntas da
reunião semanal:

1. Quanto já avançamos, no geral e por frente?
2. O que está atrasado, e o que destrava?
3. O que vence esta semana?
4. Quem está sobrecarregado, e o que depende de outra área?
5. Os dados estão bons o suficiente para confiar nos números?

## 2. O que a planilha atual já tem (diagnóstico)

| Item | Como está hoje | Leitura de gestão |
|---|---|---|
| Estrutura | 1 aba por **frente** (Fábrica de Placas, Centralização, Novos Negócios, Horizontal, Vertical, Verde) → linha roxa = **entrega** → linhas abaixo = **ações** (às vezes com um subgrupo em negrito no meio) | Já é uma EAP de 3 níveis: Portfólio › Frente › Entrega › Ação. O app usa essa hierarquia. |
| Status | À iniciar / Em andamento / Concluído | Bom e simples. Falta um estado **Impedido** (aguardando terceiro). |
| % | Derivado do status (0 / 50 / 100%) | Mantido. Avanço ponderado = Σ(peso × %) ÷ Σ peso, igual à planilha. |
| Peso | 1, 2 ou 3 | Mantido (criticidade/esforço). |
| Data | **Uma coluna só** para "prevista/conclusão" | Principal problema: não dá para medir atraso real nem cumprimento de prazo. |
| Comentários | Colunas semanais (13/10, 20/10 … 22/12) | Ótimo: vira histórico; o app mostra o último comentário. |

**Números de hoje (19/10/2026):** 85 ações reais em 4 frentes com conteúdo,
avanço geral de **47%**, 29 concluídas, **12 atrasadas**, 13 vencem em 7 dias,
**30 sem data prevista**, 17 paradas aguardando terceiros. Horizontal e
Vertical só têm o modelo vazio.

**Problemas de dado encontrados** (o app mostra isso na aba "Qualidade"):
10 ações sem responsável, 13 sem status, 12 sem peso, responsáveis múltiplos
("Lucas, Luiz e Carol"), áreas de apoio como responsável (Facilities, Frotas,
Unidade), entregas com data 12/01/2023, erros #NUM!/#DIV/0! nas linhas-mãe e
anotações soltas na coluna "Avanço".

## 3. Regras de sinalização (o "farol")

Toda ação recebe **um** sinal, sempre com ícone + texto (nunca só cor):

| Sinal | Regra |
|---|---|
| ✔ Concluída | Status = Concluído |
| ⚠ Atrasada | Não concluída e data prevista < hoje |
| ⏰ Vence em 7 dias | Não concluída e prazo nos próximos 7 dias |
| ● No prazo | Não concluída e prazo depois de 7 dias |
| ○ Sem prazo | Não concluída e sem data |
| ⏳ Aguardando (marcador extra) | Comentário cita chamado, retorno, requisição, "aguardando", "em análise" |

Farol da **entrega** (linha roxa): 🔴 se alguma ação está atrasada · 🟡 se algo
vence na semana ou mais da metade está sem prazo · 🟢 caso contrário · ✔ quando
todas concluídas.

> A decidir: hoje uma única ação atrasada de peso 1 já deixa a entrega
> vermelha. Alternativa: vermelho só se atrasada com peso 3 ou ≥ 20% do peso.

## 4. Painéis do app (abas, no padrão do DimConservação)

0. **Topo:** logo Motiva, nome da área/unidade, data de posição, upload da
   planilha, filtros por frente e responsável (valem para todas as abas).
1. **📊 Visão geral:** 7 cards (avanço, ações, concluídas, atrasadas, vencem
   em 7 dias, sem prazo, aguardando terceiros), status por frente (barra
   empilhada), avanço ponderado por frente e **pontos de atenção gerados
   automaticamente** em bullet points.
2. **🗂️ Frentes e entregas:** cada entrega com farol, barra de avanço e prazo
   final; abre para ver as ações com sinal e último comentário.
3. **👥 Responsáveis:** ações em aberto, atrasadas e peso em aberto por pessoa;
   áreas de apoio separadas como "dependência externa".
4. **📅 Prazos:** atrasadas → vencem em 7 dias → mais adiante → sem prazo.
5. **📝 Pauta semanal:** roteiro pronto da reunião: concluído na semana,
   atrasado (o que destrava?), compromissos da semana, impedimentos.
6. **🔎 Qualidade dos dados:** o que impede um indicador confiável.
7. **📑 Exportar:** PowerPoint executivo (capa, painel, 1 slide por frente,
   pauta) e Excel consolidado (base única, pronta para Power BI).

## 5. Importação

- **Fase 1 — lê a planilha como está.** Procura em cada aba a linha de
  cabeçalho com "Tarefa"; linha em negrito com fundo roxo = entrega; negrito
  sem fundo = subgrupo; demais = ações. Ignora linhas-modelo ("AÇÕES",
  "TAREFA PRINCIPAL" vazias). Recalcula avanço e prazos (não confia nas
  fórmulas da planilha, que têm erros).
- **Fase 2 — planilha modelo** (como a do inventário no DimConservação), com
  lista suspensa e aba de instruções. Mudanças propostas:
  1. separar **Data prevista** e **Data de conclusão**;
  2. incluir status **Impedido** + campo "Depende de";
  3. **um** responsável principal por ação (apoio em outra coluna);
  4. coluna **Data de início** (permite "avanço esperado × real");
  5. coluna **Frente** explícita (aceita tudo numa aba só ou uma aba por frente).

## 6. Indicadores para as próximas versões

| Indicador | Para que serve | Precisa de |
|---|---|---|
| Avanço esperado × real (curva S simplificada) | Saber se a frente está adiantada ou atrasada no todo | Data de início + prevista |
| % entregue no prazo | Confiabilidade dos compromissos | Data prevista e de conclusão separadas |
| Atraso médio (dias) | Tamanho do atraso, não só a quantidade | Idem |
| Evolução semanal | Se a situação melhora ou piora | Guardar cada importação (foto da semana) |
| Idade do impedimento | Há quanto tempo algo está parado esperando terceiro | Status "Impedido" com data |

## 7. Arquitetura (igual ao DimConservação)

```
app.py                  # Streamlit, abas acima, CSS Motiva (#5E22F3 / #3D1A9E / #EDE8FB)
modules/
  importador.py         # lê a planilha atual (Fase 1) e o modelo novo (Fase 2)
  regras.py             # sinais, farol, avanço ponderado, pontos de atenção
  qualidade.py          # checagens de dados
  export_pptx.py        # relatório executivo (reaproveita o do DimConservação)
  export_excel.py       # base consolidada
dados_exemplo/          # planilha fictícia para demonstração
tests/test_app.py       # roda o app com a planilha de exemplo
```

## 8. Roadmap sugerido

| Fase | Entrega | Critério de pronto |
|---|---|---|
| 0 — Esboço (agora) | Este documento + visual navegável | Equipe valida painéis e regras do farol |
| 1 — MVP | App Streamlit lendo a planilha atual, 7 abas, PPTX semanal | Reunião semanal feita a partir do app |
| 2 — Padronização | Planilha modelo, datas separadas, Impedido | Aba Qualidade com < 10% de pendências |
| 3 — Histórico | Guardar cada importação; evolução semanal, curva S | 4 semanas seguidas de histórico |
| 4 — Integração | Ler direto do SharePoint/Lists (Forms/Power Automate já usados pela equipe) | Sem upload manual |

## 9. Decisões em aberto

1. **Dado sensível:** a planilha tem temas de RH (desligamentos, contratações
   com nomes). Mesma questão pendente do DimConservação sobre publicar no
   Streamlit Cloud: sugerimos rodar local ou com dados fictícios até decidir.
2. Regra do farol vermelho (ver seção 3).
3. "Em andamento" continua valendo 50% fixo, ou a pessoa informa o %?
4. Quem é o público do painel: só a equipe NTec, ou gestão superior também?
   (muda o nível de detalhe do PowerPoint)
5. As abas Horizontal e Vertical vão ser preenchidas, ou saem do escopo?
