# Estado do projeto — Gerador de Escala 5x2

Leia este arquivo antes de alterar o código. Ele descreve o que o sistema faz hoje, onde cada regra mora e o que ainda não existe. Ao terminar uma mudança, atualize este arquivo no mesmo trabalho.

Atualizado em 23/11/2026.

## O que é

Gerador de escala dos balconistas das filiais do Grupo MA, jornada 5x2. A pessoa trabalha 5 dias e folga 2. A presença é de 9 horas e 24 minutos, com 1 hora de intervalo dentro desse bloco. O intervalo não é posicionado pelo solver: a janela inteira é o turno.

A navegação tem três abas: Escala mensal, Referência de vendas e Histórico. A semanal continua no código (`app_pages/semanal.py`) e não entra na navegação. Não apague a semanal ao mexer na mensal.

O solver ainda usa `Balconista_1` … por dentro. Na tela, a lista começa em Balconista 1, Balconista 2… e a pessoa troca pelo nome. Nome vazio volta ao padrão. Não há matrícula, ETL nem feriado.

## Como rodar

- Poetry, Python `>= 3.13`. Não instale pacote novo sem pedir.
- Venv que já tem Streamlit e OR-Tools: `C:\Users\Higor Rodrigues\AppData\Local\pypoetry\Cache\virtualenvs\escala-9qGyQUL_-py3.13`. Não crie outra venv. `poetry run` no sandbox cria um ambiente vazio.
- App: a partir de `escala/`,

```text
python -m streamlit run escala/teste.streamlit.py
```

- URL local usada nos testes: http://127.0.0.1:8765
- O processo do Streamlit guarda `modelo.py` importado. Depois de mudar o solver, mate o processo da porta e suba de novo. Só salvar o arquivo não basta.
- Skill de Streamlit, sob demanda: `escala/escala/.agents/skills/developing-with-streamlit`.

## Mapa dos arquivos

Tudo que importa está em `escala/escala/`.

| Arquivo | Função |
|---|---|
| `teste.streamlit.py` | Entrada. `st.navigation` no topo: Escala mensal, Referência de vendas e Histórico. |
| `app_pages/semanal.py` | Tela da semana. Fora da navegação. |
| `app_pages/mensal.py` | Tela do mês. Gera a grade e grava no banco. |
| `app_pages/historico.py` | Lista as escalas gravadas, com filtro, e reabre a grade. |
| `app_pages/referencia.py` | Curva de vendas: um gráfico de dias úteis e outro de fim de semana. |
| `banco.py` | SQLite da escala gravada. Sem Streamlit. O arquivo fica em `escala/escala/dados/escalas.sqlite`. |
| `grade.py` | Tabela HTML do mês, usada na geração e no histórico. |
| `planilha.py` | Excel da escala: capa e grade. Sem Streamlit. |
| `datalake.py` | Lê o `DATALAKE_PROVISORIO` e calcula dia de pico, hora de pico e turno de pico. Sem Streamlit. |
| `painel.py` | Sidebar compartilhada: filial, mínimos, pico, legendas. No mês também pede ano e mês. |
| `modelo.py` | Tabelas de horário, cálculo dos turnos e os dois solvers CP-SAT. Sem Streamlit. |

Dependências locais em `escala/pyproject.toml`: Streamlit 1.67, pandas 3, numpy 2, OR-Tools 9 (`ortools.sat.python.cp_model`), openpyxl, pyodbc, dotenv. O `pyodbc` e o `dotenv` só servem ao `BASE_HORA.py`. O deploy na nuvem usa `escala/escala/requirements.txt`, sem esses dois.

Tema em `escala/.streamlit/config.toml` e uma cópia em `.streamlit/config.toml` na raiz, para o Streamlit Cloud achar o arquivo. Paleta da Droga Clara, visual claro: azul `#173989`, fundo `#F4F7FC`, vermelho `#D0261E`, folga `#DFF2E8`. A barra de cima e a barra Gerar/Salvar/Exportar são azul com botão claro. Claro e escuro do sistema usam a mesma paleta, para a tela não voltar ao tema escuro.

## Repositório

GitHub: https://github.com/RmtRafix/PONTO_MENSAL_OTIMO, branch `main`. O commit `6893bd6` inclui o código, o SQLite `escala/escala/dados/escalas.sqlite` e os três parquets do datalake. O `.env` não entra no git: tem senha do SQL Server e token.

A chave SSH deste computador foi recusada pelo GitHub. O `origin` ficou em HTTPS, que é o login que conseguiu enviar.

O deploy no Streamlit Community Cloud ainda não foi feito. A tela de login em https://share.streamlit.io pediu a conta do usuário. Quando entrar:

- Repositório `RmtRafix/PONTO_MENSAL_OTIMO`, branch `main`
- Arquivo principal `escala/escala/teste.streamlit.py`

O app na nuvem lê o SQLite e os parquets do repositório. Gravação nova no Cloud não persiste depois que o processo reinicia.

## Classificação da filial

Código de 3 letras. A primeira vale de segunda a sexta, a segunda é sábado, a terceira é domingo. Cada letra aponta para abertura e fechamento nas tabelas `TABELA_SEG_SEX`, `TABELA_SABADO` e `TABELA_DOMINGO` em `modelo.py`. Domingo `A` é loja fechada (`None`).

Exemplo real, loja 12, `ADK`:

- A: segunda a sexta, 06:00–21:00
- D: sábado, 07:00–19:00
- K: domingo, 08:00–16:20

O mapa de filial fica em `painel.py` (`ID_LOJA_CLASS`). Faltam os ids 9, 10 e 20. A classificação ainda é manual.

## Turnos

`calcular_horarios_turnos` monta três janelas de 9h24:

- T1 começa na abertura.
- T3 termina no fechamento.
- T2 começa no meio do caminho entre o início de T1 e o início de T3.

Se o expediente é menor ou igual a 9h24, os três horários colapsam na abertura–fechamento. Domingo da ADK é esse caso (08:00–16:20). O modelo então só usa T1 e zera T2 e T3. Ninguém começa antes de abrir nem fica depois de fechar.

De segunda a sexta o horário é o mesmo. Sábado e domingo mudam.

## Dia e turno de pico

Vêm do `DATALAKE_PROVISORIO` e ficam travados na sidebar. A filial, os mínimos, os balconistas, o ano e o mês continuam editáveis.

Os três parquets foram gerados por `escala/BASE_HORA.py`:

- `base_geral.parquet` — venda por filial, hora e dia da semana, de 01/08/2026 a 11/11/2026.
- `base_grafico_hora.parquet` — dias úteis, percentil 80 de vendas e moda de colaboradores por hora.
- `base_grafico_hora_fim_de_semana.parquet` — o mesmo, sábado e domingo juntos.

Dia de pico: maior média de vendas por dia da semana, só entre os dias em que a filial abre. O 5º dia útil de cada mês fica de fora dessa média, porque o pagamento puxa o pico para a data em que ele cai. Turno de pico: turno cujo meio fica mais perto da hora de maior venda na curva desse período (dias úteis ou fim de semana), no horário do dia de pico. Dia curto continua só com T1. A referência pinta o dia de pico em vermelho e, no gráfico do período, a faixa do turno e a hora.

Filial, balconistas, mínimos, ano e mês usam `persist_state="session"`. Trocar de aba não devolve esses filtros ao padrão.

## Escala gravada

O botão Salvar escala, na tela do mês, grava a grade que está na tela. O banco é SQLite, em `escala/escala/dados/escalas.sqlite`, para migrar depois para MySQL.

Cada gravação tem um código `ddmmaaaa-` mais 8 dígitos. A data é a da gravação. A tabela `escalas` guarda a filial, a classificação, a competência, a equipe, os mínimos e o pico em colunas, porque são os filtros do histórico. A grade vai numa coluna `grade_json`: uma lista de dicionários, uma linha por balconista. Não é uma tabela de células, porque a escala é sempre lida inteira. No MySQL essa coluna vira `JSON`.

O Histórico filtra por código, filial, ano, mês e data de gravação, e reabre a mesma grade. Na geração, a coluna do balconista começa como Balconista 1, Balconista 2… e aceita o nome da pessoa. Gerar, Salvar e Exportar ficam na mesma barra. O Excel tem a capa com a filial e a competência, e a aba da grade. O histórico também exporta a escala aberta.

## Regras da escala semanal

Função `gerar_escala_filial`. Uma semana genérica, sem data.

Duras:

- Cada pessoa soma exatamente 5 turnos.
- No máximo 1 turno por dia.
- Loja fechada: ninguém trabalha.
- Dia longo: T1 e T3 têm pelo menos o mínimo simultâneo. T2 não tem piso.
- Dia curto: só T1 tem o piso. T2 e T3 ficam em zero.
- Domingo aberto usa o mínimo de domingo, que não pode passar do mínimo de segunda a sábado.
- O dia de pico tem pelo menos o dobro do mínimo daquele dia e não fica com menos gente que nenhum outro dia. Folga no pico é permitida. Não é obrigatório escalar todo mundo.

Objetivo, em `Minimize`:

- Cabeça do dia de pico, peso 1000. Empurra o pico para o menor tamanho que ainda seja o dia mais cheio.
- Empate com outro dia, peso 10. Prefere o pico estritamente mais cheio.
- Pessoas no turno de pico, peso −1. Desempate fraco. Por isso o T2 só aparece quando sobra gente nesse dia. Nos outros dias T1 e T3 bastam para a cobertura, e o solver não abre o turno do meio.

A semanal não tem descanso de 11 horas, não reveza fim de semana e não fixa o turno de segunda a sexta.

## Regras da escala mensal

Função `gerar_escala_mensal`. Recebe ano e mês. As semanas são de segunda a domingo. Semana cortada pelo começo ou pelo fim do mês não exige os 5 dias. Semana completa exige.

O que a semanal já faz, vale em cada semana do mês: 5x2, cobertura, dia de pico, mínimo de domingo, turno único no dia curto.

Só no mês:

1. Descanso de 11 horas, duro. Entre o fim de um turno e o início do próximo dia têm de sobrar 11 horas. Quem sai às 22:00 não entra às 06:00. Na ADK, T3 de um dia de semana seguido de T1 no dia seguinte é proibido. Os pares saem de `pares_sem_descanso`.
2. Fim de semana, preferência. Evita a mesma pessoa de folga em dois fins de semana seguidos e tenta revezar. Não trava a escala. Loja fechada no domingo: domingo é folga de todo mundo e a troca fica no sábado. Loja aberta: folga de fim de semana significa sábado e domingo sem trabalho.
3. 5º dia útil do mês, preferência. Conta só segunda a sexta, sem feriado. O solver reduz a folga nesse dia ao mínimo que as regras duras permitem. Pode zerar se couber. Não é restrição dura.
4. Mesmo turno de segunda a sexta, preferência. Dentro de cada semana, a pessoa repete T1, T2 ou T3 nos dias úteis em que trabalha. Folga no meio não conta como troca. Sábado e domingo ficam de fora. Se a cobertura ou as 11 horas impedirem, a troca continua possível.

Pesos do `Minimize` mensal, para não inverter a prioridade sem querer:

| Termo | Peso |
|---|---|
| Pessoas no dia de pico | +1000 |
| Empate do pico com outro dia | +10 |
| Pessoas no turno de pico | −1 |
| Dois fins de semana seguidos de folga | +100 |
| Cada folga de fim de semana | −30 |
| Teto de folgas de fim de semana por pessoa | +5 |
| Pessoas no 5º dia útil | −1500 |
| Cada turno diferente usado de segunda a sexta | +400 |

O solver mensal tem limite de 30 segundos. Se estourar, a tela pede para gerar de novo.

Na loja 12, novembro de 2026, 10 balconistas e mínimo 1, as 40 escalas de segunda a sexta ficaram cada uma num turno só.

## Tela do mês

Uma grade só. Linha = balconista. Coluna = dia 1…N. Célula curta: `T1`, `T2`, `T3` ou `F`.

Cabeçalho: dia de semana azul (`#173989`), sábado azul escuro (`#112B67`), domingo vermelho (`#D0261E`), 5º dia útil âmbar (`#FFF0DB`). O horário de cada turno continua na legenda da sidebar, porque a coluna do dia não cabe o texto `06:00 às 15:24`.

T1 em azul bem claro (`#E6F4FB`), T2 em azul claro (`#DCE5F9`), T3 no azul fechado com texto branco, folga em verde (`#DFF2E8`). Uma legenda curta fica embaixo da grade.

## O que não fazer sem combinar

- Não instalar stack nova.
- Não transformar a preferência de fim de semana, do 5º dia útil ou do turno repetido em restrição dura. As três foram pedidas como “quando der”.
- Não exigir T2 em todo dia. Ele não cobre abertura nem fechamento, e no domingo curto está desligado de propósito.
- Não modelar feriado nem intervalo dentro do turno até isso ser pedido. O nome na grade é só rótulo: o solver continua em `Balconista_1` ….
- Não apontar o mínimo de domingo acima do mínimo de segunda a sábado. A tela e o `validar_parametros` bloqueiam.
- Não soltar o dia de pico nem o turno de pico. Os dois vêm do datalake e a tela deixa travado.
