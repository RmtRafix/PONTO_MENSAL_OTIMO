import pandas as pd
import streamlit as st

from banco import salvar_escala
from grade import tabela_mensal
from modelo import gerar_escala_mensal
from painel import MESES, painel_loja
from planilha import bytes_excel, nome_arquivo


def _foto(parametros):
    return {
        "id_loja": parametros["id_loja"],
        "classificacao": parametros["classificacao"],
        "qtd_balconistas": parametros["qtd_balconistas"],
        "min_simultaneos": parametros["min_simultaneos"],
        "min_simultaneos_domingo": parametros["min_simultaneos_domingo"],
        "dia_pico": parametros["dia_pico"],
        "turno_pico": parametros["turno_pico"],
        "ano": parametros["ano"],
        "mes": parametros["mes"],
    }


def _diferente(foto, parametros):
    return any(foto[chave] != parametros[chave] for chave in foto)


def _nome_padrao(indice):
    return f"Balconista {indice}"


def _texto_nome(valor, indice):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return _nome_padrao(indice)
    texto = str(valor).strip()
    return texto or _nome_padrao(indice)


def _preparar_nomes(qtd):
    guardados = st.session_state.get("nomes_balconistas")
    nomes = list(guardados) if isinstance(guardados, list) else []
    if len(nomes) < qtd:
        nomes.extend(_nome_padrao(indice) for indice in range(len(nomes) + 1, qtd + 1))
    return [_texto_nome(valor, indice) for indice, valor in enumerate(nomes[:qtd], 1)]


def _nomes_editados(qtd):
    quadro = pd.DataFrame({"Nome": _preparar_nomes(qtd)})
    editado = st.data_editor(
        quadro,
        num_rows="fixed",
        hide_index=True,
        width="stretch",
        key=f"editor_nomes_{qtd}",
        column_config={
            "Nome": st.column_config.TextColumn(
                "Balconista",
                help="Começa como Balconista 1, Balconista 2… Troque pelo nome da pessoa.",
                required=True,
            )
        },
    )
    nomes = [_texto_nome(valor, indice) for indice, valor in enumerate(editado["Nome"], 1)]
    st.session_state["nomes_balconistas"] = nomes
    return nomes


def _com_nomes(grade, nomes):
    if len(grade) != len(nomes):
        return grade
    saida = grade.copy()
    saida["Balconista"] = nomes
    return saida


parametros = painel_loja(mensal=True)

st.caption(
    "Cada linha é um balconista e cada coluna é um dia do mês. "
    "Domingo fica vermelho, sábado em azul escuro e o 5º dia útil em âmbar. "
    "F é folga. T1, T2 e T3 são os turnos da legenda. "
    "Ninguém fica com mais de duas folgas seguidas. "
    "De segunda a sexta, cada pessoa repete o mesmo turno sempre que der. "
    "O dia e o turno de pico vêm da curva de vendas e ficam travados na barra lateral."
)

if parametros["dia_pico"] is None:
    st.error(
        "Esta filial não tem venda no datalake provisório, "
        "então o dia e o turno de pico não fecham."
    )
    st.stop()

competencia = f"{MESES[parametros['mes'] - 1]} {parametros['ano']}"
coluna_loja, coluna_class, coluna_comp, coluna_equipe, coluna_pico = st.columns(5)
coluna_loja.metric("Filial", parametros["id_loja"])
coluna_class.metric("Classificação", parametros["classificacao"])
coluna_comp.metric("Competência", competencia)
coluna_equipe.metric("Balconistas", parametros["qtd_balconistas"])
coluna_pico.metric("Pico", f"{parametros['dia_pico']} · {parametros['turno_pico']}")

st.caption("Os nomes começam em Balconista 1, Balconista 2… Escreva o nome da pessoa na linha.")
nomes = _nomes_editados(parametros["qtd_balconistas"])

gerada = st.session_state.get("escala_gerada")
foto_tela = gerada["parametros"] if gerada else None
grade_tela = None
if gerada and len(nomes) == len(gerada["grade"]):
    grade_tela = _com_nomes(gerada["grade"], nomes)
elif gerada:
    grade_tela = gerada["grade"]
ja_salva = bool(
    gerada
    and gerada.get("codigo")
    and gerada.get("nomes_salvos") == nomes
    and foto_tela is not None
    and not _diferente(foto_tela, parametros)
)
arquivo = None
nome_xls = "escala.xlsx"
if grade_tela is not None and foto_tela is not None:
    codigo_arquivo = gerada.get("codigo") if ja_salva else None
    arquivo = bytes_excel(grade_tela, foto_tela, codigo_arquivo)
    nome_xls = nome_arquivo(foto_tela, codigo_arquivo)

botao_gerar, botao_salvar, botao_exportar, _espaco = st.columns([1, 1, 1.2, 2.4])
gerar = botao_gerar.button(
    "Gerar",
    type="primary",
    icon=":material/play_arrow:",
    width="stretch",
    key="gerar_mensal",
)
salvar = botao_salvar.button(
    "Salvar",
    type="primary",
    icon=":material/save:",
    width="stretch",
    key="salvar_mensal",
    disabled=grade_tela is None or ja_salva,
)
botao_exportar.download_button(
    "Exportar",
    data=arquivo or b"",
    file_name=nome_xls,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
    icon=":material/download:",
    width="stretch",
    key="exportar_mensal",
    disabled=arquivo is None,
)

if gerar:
    with st.spinner("Montando o mês, o descanso de 11 horas e o revezamento..."):
        try:
            df_mes = gerar_escala_mensal(
                parametros["id_loja"],
                parametros["classificacao"],
                parametros["qtd_balconistas"],
                parametros["min_simultaneos"],
                parametros["min_simultaneos_domingo"],
                parametros["dia_pico"],
                parametros["turno_pico"],
                parametros["ano"],
                parametros["mes"],
            )
            st.session_state["escala_gerada"] = {
                "parametros": _foto(parametros),
                "grade": df_mes,
                "codigo": None,
                "nomes_salvos": None,
            }
            st.rerun()
        except ValueError as erro:
            st.error(f"**Falha na geração:** {erro}")

if salvar and gerada and grade_tela is not None:
    codigo = salvar_escala(foto_tela, grade_tela)
    gerada["codigo"] = codigo
    gerada["nomes_salvos"] = list(nomes)
    st.session_state["escala_gerada"] = gerada
    st.rerun()

gerada = st.session_state.get("escala_gerada")
if not gerada:
    st.info("Gere a competência para revisar a grade e gravar um código.")
    st.stop()

foto = gerada["parametros"]
if len(nomes) == len(gerada["grade"]):
    grade_tela = _com_nomes(gerada["grade"], nomes)
else:
    grade_tela = gerada["grade"]
if _diferente(foto, parametros):
    st.warning(
        "A barra lateral mudou depois da geração. "
        "A grade e o salvamento usam os parâmetros de quando ela foi gerada."
    )

st.success(
    f"Escala de {MESES[foto['mes'] - 1]} {foto['ano']} "
    f"da filial {foto['id_loja']} ({foto['classificacao']})."
)
st.html(tabela_mensal(grade_tela, foto["ano"], foto["mes"]))

if gerada.get("codigo") and gerada.get("nomes_salvos") == nomes and not _diferente(foto, parametros):
    st.caption("Código desta gravação")
    st.code(gerada["codigo"], language=None)
