import streamlit as st

from modelo import gerar_escala_filial
from painel import estilo_escala, painel_loja


parametros = painel_loja()

st.caption("Simulador da semana, com horários da filial, cobertura e dia de pico.")

if st.button("Gerar Escala Otimizada", type="primary", key="gerar_escala"):
    with st.spinner("Processando combinações e calculando horários..."):
        try:
            df_escala = gerar_escala_filial(
                parametros["id_loja"],
                parametros["classificacao"],
                parametros["qtd_balconistas"],
                parametros["min_simultaneos"],
                parametros["min_simultaneos_domingo"],
                parametros["dia_pico"],
                parametros["turno_pico"],
            )
            st.success("Escala gerada com sucesso!")
            st.dataframe(
                estilo_escala(df_escala),
                width="stretch",
                hide_index=True,
                alt="Escala semanal da filial",
            )
        except ValueError as erro:
            st.error(f"**Falha na geração:** {erro}")
