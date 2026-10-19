# Passo a passo: publicar o app com memória online

São **3 contas gratuitas**, todas entrando com o mesmo login do GitHub:

| # | Conta | Para quê |
|---|---|---|
| 1 | **GitHub** | Guarda o código do app (repositório **privado**) |
| 2 | **Supabase** | O banco de dados online, onde fica a memória (o histórico) |
| 3 | **Streamlit Cloud** | Publica o app num link que qualquer pessoa do time abre |

Leva uns 30 minutos, e só precisa ser feito **uma vez**. Criar conta e fazer login
é algo que só o dono da conta pode fazer. Siga na ordem.

> Se você já tem a conta do GitHub e do Streamlit Cloud do DimConservação, use as
> mesmas e pule o que já existe.

---

## Parte 1: GitHub (código)

1. Acesse https://github.com/signup e crie a conta (e-mail, senha, nome de usuário).
   Confirme o e-mail.
2. Instale o **GitHub Desktop** (https://desktop.github.com) e entre com essa conta.
3. No GitHub Desktop: **File › Add local repository** e escolha a pasta
   `Projetos\Gestão 4.0`. Se ele disser que a pasta não é um repositório, clique em
   **"create a repository"** e depois em **Create repository**.
4. **Antes de confirmar, confira a lista de arquivos à esquerda.** Ela **NÃO** pode ter:
   - `Gestão 4.0 - NTec.xlsx` (a planilha real)
   - a pasta `esboco/`
   - a pasta `dados_locais/`
   - `.streamlit/secrets.toml`

   O `.gitignore` já esconde esses itens. Se algum deles aparecer, pare e me chame.
5. Escreva "Primeira versão" no campo **Summary** e clique em **Commit to main**.
6. Clique em **Publish repository**, **mantenha marcada a opção "Keep this code
   private"** e confirme.

> ⚠️ Não use o "upload de arquivos" pelo site do GitHub: ele ignora o `.gitignore` e
> sobe a planilha real junto. Isso já aconteceu no DimConservação.

---

## Parte 2: Supabase (banco de dados)

1. Acesse https://supabase.com, clique em **Start your project** e depois em
   **Continue with GitHub**. Autorize.
2. Clique em **New project**:
   - **Organization:** a que ele criar (plano Free).
   - **Project name:** `gestao-demandas`
   - **Database Password:** clique em **Generate a password**, depois em **Copy**,
     e **guarde essa senha** num lugar seguro (ela vai ser usada no passo 4).
     Use uma senha **só com letras e números**: símbolos como `@ # / ?` quebram
     a conexão.
   - **Region:** **South America (São Paulo)**.
   - Clique em **Create new project** e espere uns 2 minutos até ficar pronto.
3. No topo da página do projeto, clique no botão **Connect**.
4. Na janela que abrir:
   - aba **Connection String**, tipo **URI**;
   - em **Method**, escolha **Session pooler** (o "Direct connection" não funciona
     no Streamlit Cloud);
   - copie o endereço. Ele tem este formato:
     `postgresql://postgres.abcdefgh:[YOUR-PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres`
   - **troque `[YOUR-PASSWORD]`** (com os colchetes) pela senha do passo 2.
     Guarde esse endereço completo para a Parte 3.

Você **não precisa criar tabelas**: o app cria tudo sozinho na primeira vez que
abrir. As tabelas ficam num espaço separado chamado `gestao`, que não fica exposto
na API pública do Supabase.

> **Atenção:** no plano gratuito, o Supabase **pausa o projeto depois de 7 dias sem
> uso**. Se o app mostrar "Não foi possível conectar ao banco de dados", entre em
> supabase.com, abra o projeto e clique em **Restore project**. Com uso semanal,
> isso não deve acontecer.

---

## Parte 3: Streamlit Cloud (link do app)

1. Acesse https://share.streamlit.io e entre com **Continue with GitHub**. Se ele pedir
   acesso aos **repositórios privados**, autorize.
2. Clique em **Create app** e depois em **Deploy a public app from GitHub**.
   O app fica num link público, mas protegido pela senha do time.
3. Preencha:
   - **Repository:** `seu-usuario/gestao-4.0` (o que você publicou na Parte 1)
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** por exemplo `gestaodemandas` (o link fica `gestaodemandas.streamlit.app`)
4. Clique em **Advanced settings**:
   - **Python version:** 3.12
   - **Secrets:** cole o texto abaixo, trocando os dois valores:

     ```toml
     [app]
     senha = "UMA-SENHA-PARA-O-TIME"

     [banco]
     url = "COLE-AQUI-O-ENDERECO-DA-PARTE-2"
     ```

   - Clique em **Save**.
5. Clique em **Deploy**. A primeira vez leva alguns minutos.

---

## Parte 4: Primeiro uso

1. Abra o link do app e digite a senha do time.
2. Abra **📥 Importar planilha atualizada**, preencha **Seu nome** e envie a planilha.
3. Confira a prévia. Na primeira vez, todas as ações aparecem como "Novas".
4. Clique em **💾 Gravar importação**. Pronto: a memória começou.
5. Mande para o time o **link** e a **senha**. Melhor em mensagens separadas, e nunca
   num lugar público.

### Rotina semanal (qualquer pessoa do time)

1. Atualiza a planilha no Excel, do jeito de sempre.
2. Abre o link, preenche o nome e sobe a planilha.
3. Confere a prévia: o que é novo, o que mudou, o que saiu, e se há alguma
   "parece a mesma demanda com outro nome".
4. Clica em **Gravar importação**.

Se gravou o arquivo errado: aba **🕓 Histórico › ↩️ Desfazer a última importação**.

> **Uma pessoa por vez.** Se duas pessoas gravarem a mesma semana, não quebra nada:
> vira duas fotos no histórico. Mas o ideal é combinar quem sobe a planilha.

---

## Trocar a senha do time

Streamlit Cloud › seu app › **⋮ › Settings › Secrets** › altere a linha `senha` ›
**Save**. O app reinicia em segundos, e todo mundo vai precisar da senha nova.

## (Opcional) Usar o banco online também no app local

Na pasta `.streamlit`, copie `secrets.toml.exemplo` para `secrets.toml` e preencha
os mesmos valores da Parte 3. O `Abrir_App.bat` passa a usar o banco do time.
Sem esse arquivo, o app local usa um banco só da sua máquina (`dados_locais/`).

## Atualizações do app

Quando o código mudar: no GitHub Desktop, **Commit to main** e depois **Push origin**.
O Streamlit Cloud publica sozinho no mesmo link. Os dados do banco não são afetados.
