from pathlib import Path

import streamlit as st


LOGO_DROGA_CLARA = Path(__file__).resolve().parent / "assets" / "logo_completo.png"

st.set_page_config(page_title="Escala 5x2 · DrogaClara", layout="wide")

st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {
        background: #173989;
        border-bottom: 1px solid #112b67;
    }
    header[data-testid="stHeader"] a,
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] span,
    header[data-testid="stHeader"] p {
        color: #ffffff;
    }
    header[data-testid="stHeader"] a[aria-current="page"] {
        background: #112b67;
        border-radius: 8px;
    }
    div[data-testid="stHorizontalBlock"]:has(.st-key-gerar_mensal) {
        background: #173989;
        border-radius: 10px;
        padding: 8px;
        align-items: center;
    }
    .st-key-gerar_mensal button,
    .st-key-salvar_mensal button,
    .st-key-exportar_mensal button {
        background: #ffffff;
        color: #173989;
        border: 1px solid transparent;
        font-weight: 600;
    }
    .st-key-salvar_mensal button:disabled,
    .st-key-exportar_mensal button:disabled {
        background: rgba(255, 255, 255, 0.35);
        color: rgba(255, 255, 255, 0.9);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pagina = st.navigation(
    [
        st.Page(
            "app_pages/mensal.py",
            title="Escala mensal",
            icon=":material/calendar_month:",
            default=True,
            help=(
                "Gera o mês inteiro por balconista, com descanso de 11 horas "
                "entre turnos e revezamento de fim de semana."
            ),
        ),
        st.Page(
            "app_pages/referencia.py",
            title="Referência de vendas",
            icon=":material/monitoring:",
            help=(
                "Curva de vendas, funcionários e carga. "
                "Um gráfico para dias úteis e outro para o fim de semana."
            ),
        ),
        st.Page(
            "app_pages/historico.py",
            title="Histórico",
            icon=":material/inventory_2:",
            help=(
                "Escalas já gravadas, com código, filial e competência. "
                "Filtre e abra a grade de uma gravação."
            ),
        ),
    ],
    position="top",
)

marca, texto = st.columns([1, 5], vertical_alignment="center")
marca.image(LOGO_DROGA_CLARA, width="stretch")
texto.caption("DrogaClara · Escala dos balconistas · jornada 5x2")
st.title(pagina.title, icon=pagina.icon)
pagina.run()
