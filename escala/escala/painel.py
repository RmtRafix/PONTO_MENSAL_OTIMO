from datetime import date
from pathlib import Path

import streamlit as st

from datalake import carregar_bases, montar_referencia
from modelo import DIAS_SEMANA, decodificar_classificacao, legenda_letras, legenda_turnos


ID_LOJA_CLASS = {
    1: 'HEH', 2: 'FCA', 3: 'BAB', 4: 'IGF', 5: 'HEJ', 6: 'JHG', 7: 'IGF',
    8: 'IGK', 11: 'EFL', 12: 'ADK', 13: 'HFA', 14: 'HDA', 15: 'DDA', 16: 'HFA',
    17: 'HDA', 18: 'IGF', 19: 'CBC', 21: 'DDA', 22: 'GDA', 23: 'HDH', 24: 'HDA',
    25: 'IGF', 26: 'DDA', 27: 'IGF', 28: 'HDA', 29: 'IGF', 30: 'DEA', 31: 'IGD',
    32: 'HFL', 33: 'ADA', 34: 'IGF', 35: 'HDI', 36: 'IGE', 37: 'HFE', 38: 'HFK',
    39: 'DDA', 40: 'IGF', 41: 'IGF', 42: 'DDK', 43: 'HEH', 44: 'HDA',
}

MESES = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

OPCOES_TURNO = {
    "T1 (Abertura)": "T1",
    "T2 (Intermediário)": "T2",
    "T3 (Fechamento)": "T3",
}
ROTULO_TURNO = {codigo: rotulo for rotulo, codigo in OPCOES_TURNO.items()}
LOGO_DROGA_CLARA = Path(__file__).resolve().parent / "assets" / "logo_completo.png"


@st.cache_data(show_spinner=False)
def _ler_datalake():
    return carregar_bases()


def colorir_celula(val):
    if isinstance(val, str):
        if val == "F" or "FOLGA" in val:
            return "background-color: #DFF2E8; color: #05553B"
        if val == "T1":
            return "background-color: #E6F4FB; color: #173989"
        if val == "T2":
            return "background-color: #DCE5F9; color: #173989"
        if val == "T3" or "às" in val:
            return "background-color: #173989; color: #FFFFFF"
    return ""


def estilo_escala(df):
    colunas = [coluna for coluna in df.columns if coluna not in ('Loja', 'Classificação', 'Balconista')]
    return df.style.map(colorir_celula, subset=colunas)


def painel_loja(mensal=False):
    st.sidebar.image(LOGO_DROGA_CLARA, width="stretch")
    st.sidebar.header("Parâmetros da loja")
    id_loja = st.sidebar.selectbox(
        "Filial", ID_LOJA_CLASS, key="filial", persist_state="session"
    )
    classificacao = ID_LOJA_CLASS[id_loja]
    st.sidebar.markdown(f"**Classificação:** {classificacao}")
    st.sidebar.caption("Significado das letras")
    st.sidebar.markdown(legenda_letras(classificacao))

    qtd_balconistas = st.sidebar.selectbox(
        "Balconistas Disponíveis",
        range(1, 21),
        index=4,
        key="qtd_balconistas",
        persist_state="session",
    )

    abre_domingo = decodificar_classificacao(classificacao)['Domingo'] is not None
    rotulo_minimo = (
        "Mínimo Simultâneo (Segunda a Sábado)"
        if abre_domingo
        else "Mínimo Simultâneo na Loja"
    )
    min_simultaneos = st.sidebar.selectbox(
        rotulo_minimo, range(1, 21), index=0, key="min_semana", persist_state="session"
    )

    min_simultaneos_domingo = None
    if abre_domingo:
        opcoes_domingo = list(range(1, min_simultaneos + 1))
        atual_domingo = st.session_state.get("min_domingo")
        if atual_domingo not in opcoes_domingo:
            if isinstance(atual_domingo, int) and atual_domingo > opcoes_domingo[-1]:
                st.session_state.min_domingo = opcoes_domingo[-1]
            else:
                st.session_state.min_domingo = opcoes_domingo[0]
        min_simultaneos_domingo = st.sidebar.selectbox(
            "Mínimo Simultâneo no Domingo",
            opcoes_domingo,
            key="min_domingo",
            persist_state="session",
            help="Piso de abertura e fechamento só no domingo. Não passa do mínimo de segunda a sábado.",
        )
    else:
        st.sidebar.caption("Esta filial não abre no domingo.")

    geral, uteis, fds = _ler_datalake()
    referencia = montar_referencia(geral, uteis, fds, id_loja, classificacao)
    if referencia is None:
        st.sidebar.error("Esta filial não tem venda no datalake provisório.")
        dia_pico = None
        turno_pico = None
    else:
        st.session_state["dia_pico_vendas"] = referencia["dia_pico"]
        dia_pico = st.sidebar.selectbox(
            "Dia de Pico (vendas)",
            DIAS_SEMANA,
            disabled=True,
            key="dia_pico_vendas",
            help=(
                "Dia com maior média de vendas, entre os dias em que a filial abre. "
                "O 5º dia útil de cada mês fica de fora, porque o pagamento puxa a média. "
                "Calculado no datalake e travado."
            ),
        )
        st.session_state["turno_pico_rotulo"] = ROTULO_TURNO[referencia["turno_pico"]]
        turno_rotulo = st.sidebar.selectbox(
            "Turno de Pico (vendas)",
            list(OPCOES_TURNO),
            disabled=True,
            key="turno_pico_rotulo",
            help=(
                "Turno que cobre a hora de maior movimento na curva do período do dia de pico. "
                "Calculado no datalake e travado."
            ),
        )
        turno_pico = OPCOES_TURNO[turno_rotulo]
        st.sidebar.caption(
            f"Hora de pico: {referencia['hora_pico']:02d}:00 · "
            f"{referencia['turno_pico']} {referencia['faixa_turno']}"
        )

    st.sidebar.caption("Turnos desta filial")
    st.sidebar.markdown(legenda_turnos(classificacao))

    ano = None
    mes = None
    if mensal:
        hoje = date.today()
        anos = list(range(hoje.year - 1, hoje.year + 3))
        ano = st.sidebar.selectbox(
            "Ano", anos, index=anos.index(hoje.year), key="ano_escala", persist_state="session"
        )
        mes = st.sidebar.selectbox(
            "Mês", MESES, index=hoje.month - 1, key="mes_escala", persist_state="session"
        )
        mes = MESES.index(mes) + 1
        st.sidebar.caption("Regras extras do mês")
        st.sidebar.markdown(
            "- Entre o fim de um turno e o início do próximo, pelo menos 11 horas.\n"
            "- No máximo duas folgas seguidas. Três dias corridos de folga não entra.\n"
            "- O par de duas folgas seguidas fica no mínimo que a cobertura deixar.\n"
            "- A folga de fim de semana reveza quando der. Não trava a escala.\n"
            "- Domingo fechado é folga de todo mundo; a troca fica no sábado.\n"
            "- No 5º dia útil, a escala deixa o menor número possível de folgas.\n"
            "- De segunda a sexta, a pessoa repete o mesmo turno sempre que der."
        )

    return {
        "id_loja": id_loja,
        "classificacao": classificacao,
        "qtd_balconistas": qtd_balconistas,
        "min_simultaneos": min_simultaneos,
        "min_simultaneos_domingo": min_simultaneos_domingo,
        "dia_pico": dia_pico,
        "turno_pico": turno_pico,
        "referencia": referencia,
        "ano": ano,
        "mes": mes,
    }
