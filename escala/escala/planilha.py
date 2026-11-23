import io

import pandas as pd


def bytes_excel(grade, foto, codigo=None):
    capa = pd.DataFrame(
        [
            {
                "Código": codigo or "",
                "Filial": foto["id_loja"],
                "Classificação": foto["classificacao"],
                "Ano": foto["ano"],
                "Mês": foto["mes"],
                "Balconistas": foto["qtd_balconistas"],
                "Mínimo": foto["min_simultaneos"],
                "Mínimo domingo": foto["min_simultaneos_domingo"]
                if foto["min_simultaneos_domingo"] is not None
                else "",
                "Dia de pico": foto["dia_pico"],
                "Turno de pico": foto["turno_pico"],
            }
        ]
    )
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as escritor:
        capa.to_excel(escritor, sheet_name="Capa", index=False)
        grade.to_excel(escritor, sheet_name="Escala", index=False)
    return buffer.getvalue()


def nome_arquivo(foto, codigo=None):
    base = f"escala_filial{foto['id_loja']}_{foto['ano']}-{int(foto['mes']):02d}"
    if codigo:
        base = f"{base}_{codigo}"
    return f"{base}.xlsx"
