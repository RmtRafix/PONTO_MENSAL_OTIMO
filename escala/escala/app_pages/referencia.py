import streamlit as st

from modelo import DIAS_SEMANA
from painel import painel_loja


def _grafico_dias(referencia):
    categorias = []
    dados = []
    for dia in DIAS_SEMANA:
        fechada = referencia["horarios"][dia] is None
        categorias.append(f"{dia} (fechada)" if fechada else dia)
        if fechada:
            cor = "#E3E8F0"
        elif dia == referencia["dia_pico"]:
            cor = "#D0261E"
        else:
            cor = "#173989"
        dados.append(
            {
                "value": round(float(referencia["medias"].get(dia, 0.0)), 1),
                "itemStyle": {"color": cor},
            }
        )
    return {
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 8, "right": 8, "top": 16, "bottom": 4, "containLabel": True},
        "xAxis": {"type": "category", "data": categorias},
        "yAxis": {"type": "value"},
        "series": [
            {
                "name": "Vendas",
                "type": "bar",
                "data": dados,
                "barMaxWidth": 52,
            }
        ],
    }


def _grafico_hora(curva, destaque):
    fonte = curva[["Hora", "Clientes", "Colaboradores", "Carga"]]
    vendas = {
        "name": "Curva de Vendas",
        "type": "line",
        "yAxisIndex": 0,
        "encode": {"x": "Hora", "y": "Clientes"},
        "smooth": True,
        "showSymbol": False,
        "lineStyle": {"width": 2.5, "color": "#173989"},
        "itemStyle": {"color": "#173989"},
        "z": 3,
    }
    if destaque is not None:
        vendas["markLine"] = {
            "symbol": "none",
            "label": {"show": False},
            "lineStyle": {"color": "#D0261E", "type": "dashed", "width": 1.5},
            "data": [{"xAxis": destaque["hora"]}],
        }
        if destaque["horas_turno"]:
            vendas["markArea"] = {
                "itemStyle": {"color": "rgba(208, 38, 30, 0.12)"},
                "label": {
                    "show": True,
                    "position": "insideTop",
                    "color": "#D0261E",
                    "formatter": f"Turno de pico {destaque['turno']}",
                },
                "data": [
                    [
                        {"xAxis": destaque["horas_turno"][0]},
                        {"xAxis": destaque["horas_turno"][-1]},
                    ]
                ],
            }
    return {
        "legend": {"top": 0},
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 8, "right": 72, "top": 52, "bottom": 4, "containLabel": True},
        "dataset": {"source": fonte},
        "xAxis": {"type": "category"},
        "yAxis": [
            {"type": "value", "name": "Vendas"},
            {
                "type": "value",
                "name": "Funcionários",
                "position": "right",
                "splitLine": {"show": False},
            },
            {
                "type": "value",
                "name": "Carga",
                "position": "right",
                "offset": 58,
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Funcionários",
                "type": "bar",
                "yAxisIndex": 1,
                "encode": {"x": "Hora", "y": "Colaboradores"},
                "itemStyle": {"color": "#E3E8F0"},
                "barMaxWidth": 26,
                "z": 1,
            },
            {
                "name": "Carga de trabalho",
                "type": "line",
                "yAxisIndex": 2,
                "encode": {"x": "Hora", "y": "Carga"},
                "smooth": True,
                "showSymbol": False,
                "lineStyle": {"width": 2, "color": "#2F6FDB"},
                "itemStyle": {"color": "#2F6FDB"},
                "z": 2,
            },
            vendas,
        ],
    }


parametros = painel_loja()
referencia = parametros["referencia"]

if referencia is None or referencia["curva_uteis"].empty or referencia["curva_fds"].empty:
    st.error(
        "Esta filial não tem venda no datalake provisório, "
        "então não há curva nem dia de pico."
    )
    st.stop()

inicio = referencia["inicio"].strftime("%d/%m/%Y")
fim = referencia["fim"].strftime("%d/%m/%Y")
st.caption(
    f"Filial {parametros['id_loja']}, vendas de {inicio} a {fim}. "
    "A curva é o percentil 80 das vendas naquela hora e a barra é a moda de colaboradores. "
    "O dia em laranja é o de maior média, sem o 5º dia útil de cada mês. "
    "A faixa laranja marca o turno que cobre a hora mais cheia "
    "dessa curva, no horário do dia de pico."
)

coluna_dia, coluna_turno, coluna_hora = st.columns(3)
coluna_dia.metric("Dia de pico", referencia["dia_pico"])
coluna_turno.metric(
    "Turno de pico",
    f"{referencia['turno_pico']} · {referencia['faixa_turno']}",
)
coluna_hora.metric("Hora de pico", f"{referencia['hora_pico']:02d}:00")

st.subheader("Vendas por dia da semana")
st.echarts_chart(
    _grafico_dias(referencia),
    height=300,
    key="referencia_dias",
    alt=(
        f"Média de vendas por dia da semana, "
        f"com {referencia['dia_pico']} em destaque"
    ),
)

destaque = {
    "hora": f"{referencia['hora_pico']:02d}:00",
    "turno": referencia["turno_pico"],
    "horas_turno": referencia["horas_turno"],
}
st.subheader("Dias úteis")
st.echarts_chart(
    _grafico_hora(referencia["curva_uteis"], None if referencia["fim_de_semana"] else destaque),
    height=420,
    key="referencia_uteis",
    alt="Curva de vendas, funcionários e carga nos dias úteis",
)
st.subheader("Fim de semana")
st.echarts_chart(
    _grafico_hora(referencia["curva_fds"], destaque if referencia["fim_de_semana"] else None),
    height=420,
    key="referencia_fds",
    alt="Curva de vendas, funcionários e carga no fim de semana",
)
