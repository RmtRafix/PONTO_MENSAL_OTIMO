from pathlib import Path

import pandas as pd

from modelo import (
    DIAS_SEMANA,
    calcular_horarios_turnos,
    decodificar_classificacao,
    expediente_tem_um_turno,
    intervalos_turnos,
    quinto_dia_util,
)


PASTA = Path(__file__).resolve().parent / "DATALAKE_PROVISORIO"

NOME_PARA_DIA = {
    "Segunda-feira": "Segunda",
    "Terça-feira": "Terça",
    "Quarta-feira": "Quarta",
    "Quinta-feira": "Quinta",
    "Sexta-feira": "Sexta",
    "Sábado": "Sábado",
    "Domingo": "Domingo",
}


def carregar_bases():
    return (
        pd.read_parquet(PASTA / "base_geral.parquet"),
        pd.read_parquet(PASTA / "base_grafico_hora.parquet"),
        pd.read_parquet(PASTA / "base_grafico_hora_fim_de_semana.parquet"),
    )


def _rotulo_hora(hora):
    return f"{int(hora):02d}:00"


def _curva(base, filial):
    sub = base.loc[base["CD_FILIAL"] == int(filial)].sort_values("HoraInicio")
    if sub.empty:
        return sub
    curva = sub.copy()
    curva["Hora"] = curva["HoraInicio"].map(_rotulo_hora)
    curva["Clientes"] = curva["Clientes"].round(1)
    curva["Carga"] = curva["Carga"].round(2)
    return curva[["Hora", "HoraInicio", "Clientes", "Colaboradores", "Carga"]]


def _quintos_dias_uteis(datas):
    # O 5º dia útil concentra pagamento e puxa a média do dia da semana para ele.
    meses = {(dia.year, dia.month) for dia in datas}
    quintos = set()
    for ano, mes in meses:
        quinto = quinto_dia_util(ano, mes)
        if quinto is not None:
            quintos.add(quinto)
    return quintos


def _medias_por_dia(geral, filial):
    sub = geral.loc[geral["CD_FILIAL"] == int(filial)].copy()
    if sub.empty:
        return {}
    sub["data"] = sub["InicioHora"].dt.normalize()
    diario = sub.groupby(["data", "DiaSemana"], as_index=False)["Qtd_Vendas_Distintas"].sum()
    datas = diario["data"].dt.date
    diario = diario.loc[~datas.isin(_quintos_dias_uteis(datas))]
    if diario.empty:
        return {}
    media = diario.groupby("DiaSemana")["Qtd_Vendas_Distintas"].mean()
    return {
        NOME_PARA_DIA[nome]: float(valor)
        for nome, valor in media.items()
        if nome in NOME_PARA_DIA
    }


def _hora_de_pico(curva):
    ordenada = curva.sort_values(
        ["Clientes", "Carga", "HoraInicio"],
        ascending=[False, False, True],
    )
    return int(ordenada.iloc[0]["HoraInicio"])


def _turno_da_hora(abertura, fechamento, hora):
    # Dia curto só tem T1. Nos outros, a hora de pico pode cair na sobreposição:
    # fica o turno cujo meio está mais perto dessa hora.
    if expediente_tem_um_turno(abertura, fechamento):
        return "T1"
    intervalos = intervalos_turnos(abertura, fechamento)
    inicio = hora * 60
    fim = (hora + 1) * 60
    centro = (inicio + fim) / 2
    cobrem = []
    for turno, (ini, fim_turno) in intervalos.items():
        if ini < fim and fim_turno > inicio:
            meio = (ini + fim_turno) / 2
            cobrem.append((abs(meio - centro), turno))
    if cobrem:
        cobrem.sort()
        return cobrem[0][1]
    return min(
        intervalos,
        key=lambda turno: abs(sum(intervalos[turno]) / 2 - centro),
    )


def _horas_do_turno(abertura, fechamento, turno, horas_na_curva):
    ini, fim = intervalos_turnos(abertura, fechamento)[turno]
    presentes = {int(hora) for hora in horas_na_curva}
    return [
        _rotulo_hora(hora)
        for hora in range(24)
        if hora in presentes and ini < (hora + 1) * 60 and fim > hora * 60
    ]


def montar_referencia(geral, uteis, fds, filial, classificacao):
    vendas = geral.loc[geral["CD_FILIAL"] == int(filial)]
    medias = _medias_por_dia(geral, filial)
    if vendas.empty or not medias:
        return None

    horarios = decodificar_classificacao(classificacao)
    abertos = [dia for dia in DIAS_SEMANA if horarios[dia] is not None and dia in medias]
    if not abertos:
        return None

    dia_pico = max(abertos, key=lambda dia: medias[dia])
    fim_de_semana = dia_pico in ("Sábado", "Domingo")
    curva_uteis = _curva(uteis, filial)
    curva_fds = _curva(fds, filial)
    curva_pico = curva_fds if fim_de_semana else curva_uteis
    if curva_pico.empty:
        return None

    hora_pico = _hora_de_pico(curva_pico)
    abertura, fechamento = horarios[dia_pico]
    turno_pico = _turno_da_hora(abertura, fechamento, hora_pico)
    return {
        "dia_pico": dia_pico,
        "turno_pico": turno_pico,
        "hora_pico": hora_pico,
        "faixa_turno": calcular_horarios_turnos(abertura, fechamento)[turno_pico],
        "fim_de_semana": fim_de_semana,
        "medias": medias,
        "horarios": horarios,
        "curva_uteis": curva_uteis,
        "curva_fds": curva_fds,
        "horas_turno": _horas_do_turno(
            abertura, fechamento, turno_pico, curva_pico["HoraInicio"]
        ),
        "inicio": vendas["InicioHora"].min(),
        "fim": vendas["InicioHora"].max(),
    }
