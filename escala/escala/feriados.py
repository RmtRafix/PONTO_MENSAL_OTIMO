from datetime import date, timedelta


def pascoa(ano):
    # Algoritmo gregoriano anônimo. A sexta-feira santa e Corpus Christi saem daqui.
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    el = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * el) // 451
    mes = (h + el - 7 * m + 114) // 31
    dia = ((h + el - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def feriados_do_ano(ano):
    # Nacionais e os três feriados municipais de Belo Horizonte.
    # Carnaval, cinzas e vésperas ficam de fora: são ponto facultativo, não feriado.
    domingo_pascoa = pascoa(ano)
    feriados = {
        date(ano, 1, 1): "Confraternização Universal",
        domingo_pascoa - timedelta(days=2): "Sexta-feira Santa",
        date(ano, 4, 21): "Tiradentes",
        date(ano, 5, 1): "Dia do Trabalho",
        domingo_pascoa + timedelta(days=60): "Corpus Christi",
        date(ano, 8, 15): "Assunção de Nossa Senhora",
        date(ano, 9, 7): "Independência",
        date(ano, 10, 12): "Nossa Senhora Aparecida",
        date(ano, 11, 2): "Finados",
        date(ano, 11, 15): "Proclamação da República",
        date(ano, 12, 8): "Imaculada Conceição",
        date(ano, 12, 25): "Natal",
    }
    if ano >= 2024:
        feriados[date(ano, 11, 20)] = "Consciência Negra"
    return feriados


def feriados_no_mes(ano, mes):
    return sorted(
        (dia, nome)
        for dia, nome in feriados_do_ano(ano).items()
        if dia.year == ano and dia.month == mes
    )
