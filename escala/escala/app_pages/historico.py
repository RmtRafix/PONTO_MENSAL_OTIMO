from datetime import date

import streamlit as st

from banco import listar_escalas, obter_escala
from grade import tabela_mensal
from painel import ID_LOJA_CLASS, MESES, painel_loja
from planilha import bytes_excel, nome_arquivo


def _data_legivel(texto):
    data, hora = texto.replace("T", " ").split(" ")
    ano, mes, dia = data.split("-")
    return f"{dia}/{mes}/{ano} {hora[:5]}"


parametros = painel_loja(mensal=True)

st.caption(
    "Escalas já gravadas. O código começa com o dia da gravação, "
    "no formato ddmmaaaa, seguido de oito dígitos."
)

with st.container(border=True):
    coluna_codigo, coluna_filial, coluna_ano, coluna_mes = st.columns(4)
    codigo = coluna_codigo.text_input("Código", key="hist_codigo", placeholder="ddmmaaaa-")
    opcoes_filial = ["Todas", *ID_LOJA_CLASS.keys()]
    filial = coluna_filial.selectbox(
        "Filial",
        opcoes_filial,
        index=opcoes_filial.index(parametros["id_loja"])
        if parametros["id_loja"] in opcoes_filial
        else 0,
        key="hist_filial",
    )
    ano_atual = date.today().year
    opcoes_ano = ["Todos", *range(ano_atual - 1, ano_atual + 2)]
    ano = coluna_ano.selectbox("Ano da escala", opcoes_ano, index=0, key="hist_ano")
    opcoes_mes = ["Todos", *MESES]
    mes = coluna_mes.selectbox("Mês da escala", opcoes_mes, index=0, key="hist_mes")
    usar_periodo = st.checkbox("Filtrar pela data de gravação", key="hist_periodo")
    criado_de = criado_ate = None
    if usar_periodo:
        coluna_de, coluna_ate = st.columns(2)
        criado_de = coluna_de.date_input("Gravada de", value=date.today().replace(day=1), key="hist_de")
        criado_ate = coluna_ate.date_input("Gravada até", value=date.today(), key="hist_ate")

id_loja = None if filial == "Todas" else int(filial)
ano_filtro = None if ano == "Todos" else int(ano)
mes_filtro = None if mes == "Todos" else MESES.index(mes) + 1
encontradas = listar_escalas(
    id_loja=id_loja,
    ano=ano_filtro,
    mes=mes_filtro,
    codigo=codigo,
    criado_de=criado_de,
    criado_ate=criado_ate,
)

st.metric("Escalas encontradas", len(encontradas))
if encontradas.empty:
    st.info("Nenhuma escala gravada com esses filtros.")
    st.stop()

visao = encontradas.copy()
visao["Criada em"] = visao["criado_em"].map(_data_legivel)
visao["Competência"] = visao.apply(
    lambda linha: f"{MESES[int(linha['mes']) - 1]} {int(linha['ano'])}",
    axis=1,
)
visao = visao.rename(
    columns={
        "codigo": "Código",
        "id_loja": "Filial",
        "classificacao": "Classificação",
        "qtd_balconistas": "Balconistas",
        "dia_pico": "Dia de pico",
        "turno_pico": "Turno de pico",
    }
)
st.dataframe(
    visao[
        [
            "Código",
            "Criada em",
            "Filial",
            "Classificação",
            "Competência",
            "Balconistas",
            "Dia de pico",
            "Turno de pico",
        ]
    ],
    width="stretch",
    hide_index=True,
    alt="Histórico de escalas gravadas",
)

escolhida = st.selectbox(
    "Abrir escala",
    encontradas["codigo"].tolist(),
    key="hist_abrir",
)
registro = obter_escala(escolhida)
if registro is None:
    st.error("Essa escala não está mais no banco.")
    st.stop()

st.subheader(registro["codigo"])
resumo_loja, resumo_comp, resumo_equipe, resumo_pico = st.columns(4)
resumo_loja.metric("Filial", f"{registro['id_loja']} · {registro['classificacao']}")
resumo_comp.metric("Competência", f"{MESES[registro['mes'] - 1]} {registro['ano']}")
resumo_equipe.metric("Balconistas", registro["qtd_balconistas"])
resumo_pico.metric("Pico", f"{registro['dia_pico']} · {registro['turno_pico']}")
st.caption(f"Gravada em {_data_legivel(registro['criado_em'])}.")
foto_registro = {
    "id_loja": registro["id_loja"],
    "classificacao": registro["classificacao"],
    "ano": registro["ano"],
    "mes": registro["mes"],
    "qtd_balconistas": registro["qtd_balconistas"],
    "min_simultaneos": registro["min_simultaneos"],
    "min_simultaneos_domingo": registro["min_simultaneos_domingo"],
    "dia_pico": registro["dia_pico"],
    "turno_pico": registro["turno_pico"],
}
st.download_button(
    "Exportar",
    data=bytes_excel(registro["grade"], foto_registro, registro["codigo"]),
    file_name=nome_arquivo(foto_registro, registro["codigo"]),
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
    icon=":material/download:",
    key="exportar_historico",
)
st.html(tabela_mensal(registro["grade"], registro["ano"], registro["mes"]))
