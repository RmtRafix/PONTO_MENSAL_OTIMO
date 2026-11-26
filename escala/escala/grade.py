from datetime import date
from html import escape

from feriados import feriados_no_mes
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
SIGLA_DIA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


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


def _cor_dia(dia, quinto, feriados):
    nome_feriado = feriados.get(dia)
    if dia.weekday() == 6 or nome_feriado:
        fundo, texto = VERMELHO, BRANCO
    elif dia.weekday() == 5:
        fundo, texto = AZUL_ESCURO, BRANCO
    elif quinto is not None and dia == quinto:
        fundo, texto = QUINTO, QUINTO_TINTA
    else:
        fundo, texto = AZUL, BRANCO
    titulo = DIAS_SEMANA[dia.weekday()]
    if nome_feriado:
        titulo = f"{titulo} · {nome_feriado}"
    return fundo, texto, titulo


def _canto(rotulo, z):
    return (
        "<th style='position:sticky;left:0;z-index:"
        f"{z};background:{AZUL};color:{BRANCO};text-align:left;padding:4px 10px;"
        f"border:1px solid {AZUL_ESCURO};font-weight:600;'>{escape(rotulo)}</th>"
    )


def _th_dia(conteudo, fundo, texto, titulo, miudo):
    tamanho = "10px" if miudo else "13px"
    return (
        f"<th title='{escape(titulo)}' "
        f"style='background:{fundo};color:{texto};padding:4px 0;"
        f"border:1px solid {LINHA};text-align:center;min-width:36px;"
        f"font-weight:600;font-size:{tamanho};'>{escape(conteudo)}</th>"
    )


def tabela_mensal(df_mes, ano, mes):
    quinto = quinto_dia_util(ano, mes)
    feriados = dict(feriados_no_mes(ano, mes))
    dias = []
    numeros = []
    for coluna in df_mes.columns:
        if coluna == "Balconista":
            continue
        dia = date(ano, mes, int(coluna))
        fundo, texto, titulo = _cor_dia(dia, quinto, feriados)
        dias.append(_th_dia(SIGLA_DIA[dia.weekday()], fundo, texto, titulo, True))
        numeros.append(_th_dia(str(coluna), fundo, texto, titulo, False))
    cabecalho_dia = _canto("Dia", 3) + "".join(dias)
    cabecalho_num = _canto("Balconista", 2) + "".join(numeros)

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
        f"<span style='background:{VERMELHO};color:{BRANCO};padding:0 6px;border-radius:4px;'>dom / feriado</span>"
        f"<span style='background:{QUINTO};color:{QUINTO_TINTA};padding:0 6px;border-radius:4px;'>5º útil</span>"
        "</div>"
    )
    return (
        "<div style='overflow-x:auto;max-width:100%;background:#fff;"
        f"border:1px solid {LINHA};border-radius:10px;padding:4px;'>"
        "<table style='border-collapse:collapse;font-size:13px;white-space:nowrap;width:100%;'>"
        f"<thead><tr>{cabecalho_dia}</tr><tr>{cabecalho_num}</tr></thead>"
        f"<tbody>{''.join(linhas)}</tbody>"
        "</table></div>"
        + legenda
    )
