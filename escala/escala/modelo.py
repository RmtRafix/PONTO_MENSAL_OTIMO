import calendar
from datetime import date, datetime, timedelta

import pandas as pd
from ortools.sat.python import cp_model


DIAS_SEMANA = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
TURNOS = ['T1', 'T2', 'T3']
JORNADA = timedelta(hours=9, minutes=24)
FORMATO_HORA = "%H:%M"
DESCANSO_MINIMO = 11 * 60

TABELA_SEG_SEX = {
    'A': ('06:00', '21:00'), 'B': ('06:00', '22:00'), 'C': ('06:00', '23:00'),
    'D': ('06:30', '21:00'), 'E': ('06:30', '22:00'), 'F': ('06:40', '20:00'),
    'G': ('07:00', '20:00'), 'H': ('07:00', '21:00'), 'I': ('07:00', '22:00'),
    'J': ('07:00', '23:00')
}

TABELA_SABADO = {
    'A': ('06:00', '22:00'), 'B': ('06:00', '23:00'), 'C': ('06:40', '19:00'),
    'D': ('07:00', '19:00'), 'E': ('07:00', '20:00'), 'F': ('07:00', '21:00'),
    'G': ('07:00', '22:00'), 'H': ('07:00', '23:00')
}

TABELA_DOMINGO = {
    'A': None,
    'B': ('06:00', '22:00'), 'C': ('06:00', '23:00'), 'D': ('07:00', '19:00'),
    'E': ('07:00', '20:00'), 'F': ('07:00', '22:00'), 'G': ('07:00', '23:00'),
    'H': ('08:00', '14:00'), 'I': ('08:00', '14:10'), 'J': ('08:00', '16:00'),
    'K': ('08:00', '16:20'), 'L': ('08:00', '20:00')
}


def decodificar_classificacao(classificacao):
    c_seg_sex, c_sab, c_dom = classificacao[0], classificacao[1], classificacao[2]
    return {
        'Segunda': TABELA_SEG_SEX[c_seg_sex], 'Terça': TABELA_SEG_SEX[c_seg_sex],
        'Quarta': TABELA_SEG_SEX[c_seg_sex], 'Quinta': TABELA_SEG_SEX[c_seg_sex],
        'Sexta': TABELA_SEG_SEX[c_seg_sex], 'Sábado': TABELA_SABADO[c_sab],
        'Domingo': TABELA_DOMINGO[c_dom]
    }


def calcular_horarios_turnos(horario_abertura, horario_fechamento):
    abertura = datetime.strptime(horario_abertura, FORMATO_HORA)
    fechamento = datetime.strptime(horario_fechamento, FORMATO_HORA)

    # A jornada não pode começar antes da abertura nem terminar depois do fechamento.
    # Em domingo curto (ex.: 08:00–16:20) os três turnos cabem na mesma faixa.
    t1_inicio = abertura
    t1_fim = min(abertura + JORNADA, fechamento)

    t3_fim = fechamento
    t3_inicio = max(fechamento - JORNADA, abertura)

    meio_tempo = (t3_inicio - t1_inicio) / 2
    t2_inicio = t1_inicio + meio_tempo
    t2_fim = min(t2_inicio + JORNADA, fechamento)

    def faixa(inicio, fim):
        return f"{inicio.strftime(FORMATO_HORA)} às {fim.strftime(FORMATO_HORA)}"

    return {
        'T1': faixa(t1_inicio, t1_fim),
        'T2': faixa(t2_inicio, t2_fim),
        'T3': faixa(t3_inicio, t3_fim),
    }


def expediente_tem_um_turno(horario_abertura, horario_fechamento):
    abertura = datetime.strptime(horario_abertura, FORMATO_HORA)
    fechamento = datetime.strptime(horario_fechamento, FORMATO_HORA)
    return (fechamento - abertura) <= JORNADA


def texto_expediente(horario):
    if horario is None:
        return "fechada"
    return f"{horario[0]} às {horario[1]}"


def legenda_letras(classificacao):
    letra_semana, letra_sabado, letra_domingo = classificacao[0], classificacao[1], classificacao[2]
    return (
        f"- **{letra_semana}** — segunda a sexta, {texto_expediente(TABELA_SEG_SEX[letra_semana])}\n"
        f"- **{letra_sabado}** — sábado, {texto_expediente(TABELA_SABADO[letra_sabado])}\n"
        f"- **{letra_domingo}** — domingo, {texto_expediente(TABELA_DOMINGO[letra_domingo])}"
    )


def legenda_turnos(classificacao):
    horarios = decodificar_classificacao(classificacao)
    blocos = (
        ("Segunda a sexta", horarios["Segunda"]),
        ("Sábado", horarios["Sábado"]),
        ("Domingo", horarios["Domingo"]),
    )
    partes = []
    for nome, faixa in blocos:
        if faixa is None:
            partes.append(f"**{nome}:** fechada")
            continue
        turnos = calcular_horarios_turnos(faixa[0], faixa[1])
        linha = (
            f"**{nome}** ({texto_expediente(faixa)})\n"
            f"- T1 abertura: {turnos['T1']}\n"
            f"- T2 intermediário: {turnos['T2']}\n"
            f"- T3 fechamento: {turnos['T3']}"
        )
        if len(set(turnos.values())) == 1:
            linha += "\n- Os três turnos usam o mesmo horário."
        partes.append(linha)
    return "\n\n".join(partes)


def _minutos(hhmm):
    hora, minuto = hhmm.split(":")
    return int(hora) * 60 + int(minuto)


def intervalos_turnos(horario_abertura, horario_fechamento):
    faixas = calcular_horarios_turnos(horario_abertura, horario_fechamento)
    intervalos = {}
    for turno, texto in faixas.items():
        inicio, fim = texto.split(" às ")
        intervalos[turno] = (_minutos(inicio), _minutos(fim))
    return intervalos


def pares_sem_descanso(horarios_loja):
    pares = []
    for indice, nome in enumerate(DIAS_SEMANA):
        seguinte = DIAS_SEMANA[(indice + 1) % 7]
        atual = horarios_loja[nome]
        proximo = horarios_loja[seguinte]
        if atual is None or proximo is None:
            continue
        turnos_atual = intervalos_turnos(atual[0], atual[1])
        turnos_proximo = intervalos_turnos(proximo[0], proximo[1])
        for turno, (_, fim) in turnos_atual.items():
            for turno_seguinte, (inicio, _) in turnos_proximo.items():
                if (24 * 60 - fim) + inicio < DESCANSO_MINIMO:
                    pares.append((nome, turno, seguinte, turno_seguinte))
    return pares


def validar_parametros(horarios_loja, min_simultaneos, min_simultaneos_domingo, dia_pico):
    domingo_aberto = horarios_loja['Domingo'] is not None
    if domingo_aberto:
        if min_simultaneos_domingo is None:
            raise ValueError("Informe o mínimo de balconistas no domingo.")
        if min_simultaneos_domingo > min_simultaneos:
            raise ValueError(
                "O mínimo de domingo não pode ser maior que o mínimo de segunda a sábado."
            )
    if horarios_loja[dia_pico] is None:
        raise ValueError("O dia de pico cai num dia em que a filial está fechada.")
    return domingo_aberto


def gerar_escala_filial(id_loja, classificacao, qtd_balconistas, min_simultaneos, min_simultaneos_domingo, dia_pico, turno_pico):
    horarios_loja = decodificar_classificacao(classificacao)
    dias_semana = DIAS_SEMANA
    turnos = TURNOS
    balconistas = [f'Balconista_{i}' for i in range(1, qtd_balconistas + 1)]
    domingo_aberto = validar_parametros(
        horarios_loja, min_simultaneos, min_simultaneos_domingo, dia_pico
    )

    model = cp_model.CpModel()

    x = {}
    for b in balconistas:
        for d in dias_semana:
            for t in turnos:
                x[(b, d, t)] = model.NewBoolVar(f'x_{b}_{d}_{t}')

    for b in balconistas:
        model.Add(sum(x[(b, d, t)] for d in dias_semana for t in turnos) == 5)
        for d in dias_semana:
            model.Add(sum(x[(b, d, t)] for t in turnos) <= 1)

    for d in dias_semana:
        horario = horarios_loja[d]
        if horario is None:
            for b in balconistas:
                for t in turnos:
                    model.Add(x[(b, d, t)] == 0)
        else:
            minimo_dia = min_simultaneos_domingo if d == 'Domingo' else min_simultaneos
            if expediente_tem_um_turno(horario[0], horario[1]):
                model.Add(sum(x[(b, d, 'T1')] for b in balconistas) >= minimo_dia)
                model.Add(sum(x[(b, d, 'T2')] for b in balconistas) == 0)
                model.Add(sum(x[(b, d, 'T3')] for b in balconistas) == 0)
            else:
                model.Add(sum(x[(b, d, 'T1')] for b in balconistas) >= minimo_dia)
                model.Add(sum(x[(b, d, 'T3')] for b in balconistas) >= minimo_dia)

    def pessoas_no_dia(dia):
        return sum(x[(b, dia, t)] for b in balconistas for t in turnos)

    minimo_pico = min_simultaneos_domingo if dia_pico == 'Domingo' else min_simultaneos
    no_pico = pessoas_no_dia(dia_pico)
    # Piso do dia de pico: o dobro do mínimo simultâneo. Folga continua permitida.
    model.Add(no_pico >= 2 * minimo_pico)

    empates = []
    for d in dias_semana:
        if d == dia_pico or horarios_loja[d] is None:
            continue
        presentes = pessoas_no_dia(d)
        model.Add(no_pico >= presentes)
        empate = model.NewBoolVar(f'empate_{d}')
        model.Add(presentes == no_pico).OnlyEnforceIf(empate)
        model.Add(presentes <= no_pico - 1).OnlyEnforceIf(empate.Not())
        empates.append(empate)

    no_turno_pico = sum(x[(b, dia_pico, turno_pico)] for b in balconistas)
    # Menor dia de pico que ainda seja o mais cheio, com folga permitida.
    # O turno de pico só desempata, sem puxar todo mundo para esse dia.
    model.Minimize(no_pico * 1000 + sum(empates) * 10 - no_turno_pico)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        escala = []
        for b in balconistas:
            linha = {'Loja': id_loja, 'Classificação': classificacao, 'Balconista': b}
            for d in dias_semana:
                horario_dia = horarios_loja[d]
                mapa_horas = calcular_horarios_turnos(horario_dia[0], horario_dia[1]) if horario_dia else {}
                trabalhou = False
                for t in turnos:
                    if solver.Value(x[(b, d, t)]) == 1:
                        linha[d] = mapa_horas.get(t, t)
                        trabalhou = True
                if not trabalhou:
                    linha[d] = 'FOLGA' if horario_dia is not None else 'FOLGA (Fechada)'
            escala.append(linha)
        return pd.DataFrame(escala)

    detalhe_domingo = (
        f" e {min_simultaneos_domingo} no domingo"
        if domingo_aberto
        else ""
    )
    raise ValueError(
        f"Inviável matematicamente. Com {qtd_balconistas} balconistas, "
        f"mínimo de {min_simultaneos} de segunda a sábado{detalhe_domingo}, "
        f"e o dia de pico ({dia_pico}) precisando de pelo menos {2 * minimo_pico} pessoas, "
        "as regras de folga e cobertura não fecham."
    )


def quinto_dia_util(ano, mes):
    uteis = 0
    ultimo = calendar.monthrange(ano, mes)[1]
    for dia in range(1, ultimo + 1):
        data = date(ano, mes, dia)
        if data.weekday() < 5:
            uteis += 1
            if uteis == 5:
                return data
    return None


def _semanas_do_mes(ano, mes):
    primeiro = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    ultimo = date(ano, mes, ultimo_dia)
    segunda = primeiro - timedelta(days=primeiro.weekday())
    semanas = []
    cursor = segunda
    while cursor <= ultimo:
        semanas.append([cursor + timedelta(days=i) for i in range(7)])
        cursor += timedelta(days=7)
    return semanas


def _codigo_dia(solver, x, balconista, dia):
    for turno in TURNOS:
        if solver.Value(x[(balconista, dia, turno)]) == 1:
            return turno
    return "F"


def gerar_escala_mensal(
    id_loja,
    classificacao,
    qtd_balconistas,
    min_simultaneos,
    min_simultaneos_domingo,
    dia_pico,
    turno_pico,
    ano,
    mes,
):
    horarios_loja = decodificar_classificacao(classificacao)
    balconistas = [f'Balconista_{i}' for i in range(1, qtd_balconistas + 1)]
    domingo_aberto = validar_parametros(
        horarios_loja, min_simultaneos, min_simultaneos_domingo, dia_pico
    )
    datas = [
        date(ano, mes, dia)
        for dia in range(1, calendar.monthrange(ano, mes)[1] + 1)
    ]
    no_mes = set(datas)
    semanas = _semanas_do_mes(ano, mes)
    indice_pico = DIAS_SEMANA.index(dia_pico)
    minimo_pico = min_simultaneos_domingo if dia_pico == 'Domingo' else min_simultaneos

    model = cp_model.CpModel()
    x = {}
    for balconista in balconistas:
        for dia in datas:
            for turno in TURNOS:
                x[(balconista, dia, turno)] = model.NewBoolVar(
                    f"x_{balconista}_{dia.isoformat()}_{turno}"
                )

    for balconista in balconistas:
        for dia in datas:
            model.Add(sum(x[(balconista, dia, turno)] for turno in TURNOS) <= 1)

    for dia in datas:
        nome = DIAS_SEMANA[dia.weekday()]
        horario = horarios_loja[nome]
        if horario is None:
            for balconista in balconistas:
                for turno in TURNOS:
                    model.Add(x[(balconista, dia, turno)] == 0)
            continue
        minimo_dia = min_simultaneos_domingo if nome == 'Domingo' else min_simultaneos
        if expediente_tem_um_turno(horario[0], horario[1]):
            model.Add(sum(x[(b, dia, 'T1')] for b in balconistas) >= minimo_dia)
            model.Add(sum(x[(b, dia, 'T2')] for b in balconistas) == 0)
            model.Add(sum(x[(b, dia, 'T3')] for b in balconistas) == 0)
        else:
            model.Add(sum(x[(b, dia, 'T1')] for b in balconistas) >= minimo_dia)
            model.Add(sum(x[(b, dia, 'T3')] for b in balconistas) >= minimo_dia)

    for semana in semanas:
        dias_semana = [dia for dia in semana if dia in no_mes]
        if len(dias_semana) != 7:
            continue
        for balconista in balconistas:
            model.Add(
                sum(x[(balconista, dia, turno)] for dia in dias_semana for turno in TURNOS) == 5
            )

    def pessoas_no_dia(dia):
        return sum(x[(b, dia, t)] for b in balconistas for t in TURNOS)

    picos = []
    empates = []
    turnos_pico = []
    for semana in semanas:
        dias_semana = [dia for dia in semana if dia in no_mes]
        dia_do_pico = next((dia for dia in dias_semana if dia.weekday() == indice_pico), None)
        if dia_do_pico is None:
            continue
        no_pico = pessoas_no_dia(dia_do_pico)
        model.Add(no_pico >= 2 * minimo_pico)
        picos.append(no_pico)
        turnos_pico.append(sum(x[(b, dia_do_pico, turno_pico)] for b in balconistas))
        for dia in dias_semana:
            if dia == dia_do_pico or horarios_loja[DIAS_SEMANA[dia.weekday()]] is None:
                continue
            presentes = pessoas_no_dia(dia)
            model.Add(no_pico >= presentes)
            empate = model.NewBoolVar(f"empate_{dia.isoformat()}")
            model.Add(presentes == no_pico).OnlyEnforceIf(empate)
            model.Add(presentes <= no_pico - 1).OnlyEnforceIf(empate.Not())
            empates.append(empate)

    for dia in datas:
        seguinte = dia + timedelta(days=1)
        if seguinte not in no_mes:
            continue
        nome = DIAS_SEMANA[dia.weekday()]
        nome_seguinte = DIAS_SEMANA[seguinte.weekday()]
        for nome_atual, turno, nome_prox, turno_seguinte in pares_sem_descanso(horarios_loja):
            if nome_atual != nome or nome_prox != nome_seguinte:
                continue
            for balconista in balconistas:
                model.Add(
                    x[(balconista, dia, turno)] + x[(balconista, seguinte, turno_seguinte)] <= 1
                )

    # No máximo duas folgas seguidas, no mês inteiro. A virada da semana também conta.
    folga_dia = {}
    for balconista in balconistas:
        for dia in datas:
            folga = model.NewBoolVar(f"folga_{balconista}_{dia.isoformat()}")
            trabalhou = sum(x[(balconista, dia, turno)] for turno in TURNOS)
            model.Add(folga + trabalhou == 1)
            folga_dia[(balconista, dia)] = folga
    for balconista in balconistas:
        for indice in range(len(datas) - 2):
            janela = datas[indice:indice + 3]
            model.Add(sum(folga_dia[(balconista, dia)] for dia in janela) <= 2)

    # Cada par de duas folgas seguidas entra no objetivo. Isolar a folga pesa mais que o fim de semana.
    duas_seguidas = []
    for balconista in balconistas:
        for indice in range(len(datas) - 1):
            hoje = datas[indice]
            amanha = datas[indice + 1]
            par = model.NewBoolVar(f"duas_folgas_{balconista}_{hoje.isoformat()}")
            soma = folga_dia[(balconista, hoje)] + folga_dia[(balconista, amanha)]
            model.Add(soma == 2).OnlyEnforceIf(par)
            model.Add(soma <= 1).OnlyEnforceIf(par.Not())
            duas_seguidas.append(par)

    # Folga de fim de semana é preferência. Domingo fechado fica fixo para todo mundo.
    folgas_por_pessoa = {balconista: [] for balconista in balconistas}
    rotulos_fds = []
    for semana in semanas:
        sabado = semana[5]
        domingo = semana[6]
        if not domingo_aberto:
            if sabado not in no_mes:
                continue
            rotulo = sabado.strftime("%d/%m")
        else:
            if sabado not in no_mes or domingo not in no_mes:
                continue
            rotulo = f"{sabado.strftime('%d/%m')}–{domingo.strftime('%d/%m')}"
        rotulos_fds.append(rotulo)
        for balconista in balconistas:
            if domingo_aberto:
                trabalhou = (
                    sum(x[(balconista, sabado, turno)] for turno in TURNOS)
                    + sum(x[(balconista, domingo, turno)] for turno in TURNOS)
                )
            else:
                trabalhou = sum(x[(balconista, sabado, turno)] for turno in TURNOS)
            folga = model.NewBoolVar(f"folga_fds_{balconista}_{sabado.isoformat()}")
            model.Add(trabalhou == 0).OnlyEnforceIf(folga)
            model.Add(trabalhou >= 1).OnlyEnforceIf(folga.Not())
            folgas_por_pessoa[balconista].append(folga)

    seguidos = []
    folgas_todas = []
    for balconista, folgas in folgas_por_pessoa.items():
        folgas_todas.extend(folgas)
        for anterior, atual in zip(folgas, folgas[1:]):
            seguido = model.NewBoolVar(f"fds_seguido_{balconista}_{anterior.Name()}")
            model.Add(anterior + atual == 2).OnlyEnforceIf(seguido)
            model.Add(anterior + atual <= 1).OnlyEnforceIf(seguido.Not())
            seguidos.append(seguido)

    teto_folga = None
    if len(rotulos_fds) >= 2:
        teto_folga = model.NewIntVar(0, len(rotulos_fds), "teto_folga_fds")
        for folgas in folgas_por_pessoa.values():
            if folgas:
                model.Add(sum(folgas) <= teto_folga)

    # De segunda a sexta, cada pessoa fica o máximo possível no mesmo turno.
    escalas_usadas = []
    for indice_semana, semana in enumerate(semanas):
        dias_uteis = [dia for dia in semana[:5] if dia in no_mes]
        if len(dias_uteis) < 2:
            continue
        for balconista in balconistas:
            for turno in TURNOS:
                usa = model.NewBoolVar(f"usa_{balconista}_{indice_semana}_{turno}")
                model.AddMaxEquality(
                    usa, [x[(balconista, dia, turno)] for dia in dias_uteis]
                )
                escalas_usadas.append(usa)

    objetivo = 0
    if picos:
        objetivo += sum(picos) * 1000
    if empates:
        objetivo += sum(empates) * 10
    if turnos_pico:
        objetivo -= sum(turnos_pico)
    if seguidos:
        objetivo += sum(seguidos) * 100
    if duas_seguidas:
        objetivo += sum(duas_seguidas) * 500
    if folgas_todas:
        # Prefere revezar a folga, sem pesar mais que o dia de pico.
        objetivo -= sum(folgas_todas) * 30
    if teto_folga is not None:
        objetivo += teto_folga * 5
    quinto = quinto_dia_util(ano, mes)
    if (
        quinto in no_mes
        and horarios_loja[DIAS_SEMANA[quinto.weekday()]] is not None
    ):
        # Menos folgas possível no 5º dia útil, sem obrigar folga zero.
        objetivo -= pessoas_no_dia(quinto) * 1500
    if escalas_usadas:
        objetivo += sum(escalas_usadas) * 400
    model.Minimize(objetivo)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    status = solver.Solve(model)
    if status == cp_model.UNKNOWN:
        raise ValueError(
            "O mês não fechou no tempo limite. Gere de novo ou reduza a equipe."
        )
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise ValueError(
            f"Inviável matematicamente. Com {qtd_balconistas} balconistas, "
            "a cobertura, a escala 5x2, o dia de pico, as 11 horas de descanso "
            "ou o limite de duas folgas seguidas não fecham."
        )

    linhas = []
    for balconista in balconistas:
        linha = {"Balconista": balconista}
        for dia in datas:
            linha[str(dia.day)] = _codigo_dia(solver, x, balconista, dia)
        linhas.append(linha)
    return pd.DataFrame(linhas)
