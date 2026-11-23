from datetime import date
from html import escape

from modelo import DIAS_SEMANA, quinto_dia_util


AZUL = "#173989"
AZUL_ESCURO = "#112B67"
TINTA = "#0F1C3F"
LINHA = "#E4E4E7"
BRISA = "#E6F4FB"
TINT = "#DCE5F9"
FOLGA = "#DFF2E8"
FOLGA_TINTA = "#05553B"
QUINTO = "#FFF0DB"
QUINTO_TINTA = "#5C3000"
VERMELHO = "#D0261E"
BRANCO = "#FFFFFF"
NOME = "#F4F7FC"


def _celula(valor):
    if valor == "F":
        return FOLGA, FOLGA_TINTA, "600"
    if valor == "T1":
        return BRISA, AZUL, "600"
    if valor == "T2":
        return TINT, AZUL, "600"
    if valor == "T3":
        return AZUL, BRANCO, "600"
    return BRANCO, TINTA, "400"


def tabela_mensal(df_mes, ano, mes):
    quinto = quinto_dia_util(ano, mes)
    cabecalhos = [
        "<th style='position:sticky;left:0;z-index:2;background:"
        f"{AZUL};color:{BRANCO};text-align:left;padding:7px 10px;"
        f"border:1px solid {AZUL_ESCURO};font-weight:600;'>Balconista</th>"
    ]
    for coluna in df_mes.columns:
        if coluna == "Balconista":
            continue
        dia = date(ano, mes, int(coluna))
        if dia.weekday() == 6:
            fundo, texto = VERMELHO, BRANCO
        elif dia.weekday() == 5:
            fundo, texto = AZUL_ESCURO, BRANCO
        elif quinto is not None and dia == quinto:
            fundo, texto = QUINTO, QUINTO_TINTA
        else:
            fundo, texto = AZUL, BRANCO
        cabecalhos.append(
            f"<th title='{escape(DIAS_SEMANA[dia.weekday()])}' "
            f"style='background:{fundo};color:{texto};padding:7px 0;"
            f"border:1px solid {LINHA};text-align:center;min-width:34px;"
            f"font-weight:600;'>{escape(str(coluna))}</th>"
        )

    linhas = []
    for _, serie in df_mes.iterrows():
        celulas = [
            "<td style='position:sticky;left:0;z-index:1;background:"
            f"{NOME};color:{TINTA};text-align:left;padding:5px 10px;"
            f"border:1px solid {LINHA};font-weight:600;white-space:nowrap;'>"
            f"{escape(str(serie['Balconista']))}</td>"
        ]
        for coluna in df_mes.columns:
            if coluna == "Balconista":
                continue
            valor = str(serie[coluna])
            fundo, texto, peso = _celula(valor)
            celulas.append(
                f"<td style='background:{fundo};color:{texto};text-align:center;"
                f"padding:5px 0;border:1px solid {LINHA};font-weight:{peso};"
                f"font-size:12px;'>{escape(valor)}</td>"
            )
        linhas.append(f"<tr>{''.join(celulas)}</tr>")

    legenda = (
        "<div style='display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:8px;"
        f"color:{TINTA};font-size:12px;'>"
        f"<span><b style='color:{AZUL}'>T1</b> abertura</span>"
        f"<span><b style='color:{AZUL}'>T2</b> intermediário</span>"
        f"<span style='background:{AZUL};color:{BRANCO};padding:0 6px;border-radius:4px;'>T3</span> fechamento"
        f"<span style='background:{FOLGA};color:{FOLGA_TINTA};padding:0 6px;border-radius:4px;'>F</span> folga"
        f"<span style='background:{AZUL_ESCURO};color:{BRANCO};padding:0 6px;border-radius:4px;'>sáb</span>"
        f"<span style='background:{VERMELHO};color:{BRANCO};padding:0 6px;border-radius:4px;'>dom</span>"
        f"<span style='background:{QUINTO};color:{QUINTO_TINTA};padding:0 6px;border-radius:4px;'>5º útil</span>"
        "</div>"
    )
    return (
        "<div style='overflow-x:auto;max-width:100%;background:#fff;"
        f"border:1px solid {LINHA};border-radius:10px;padding:4px;'>"
        "<table style='border-collapse:collapse;font-size:13px;white-space:nowrap;width:100%;'>"
        f"<thead><tr>{''.join(cabecalhos)}</tr></thead>"
        f"<tbody>{''.join(linhas)}</tbody>"
        "</table></div>"
        + legenda
    )
