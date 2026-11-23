import json
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd


PASTA = Path(__file__).resolve().parent / "dados"
ARQUIVO = PASTA / "escalas.sqlite"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS escalas (
    codigo TEXT PRIMARY KEY,
    criado_em TEXT NOT NULL,
    id_loja INTEGER NOT NULL,
    classificacao TEXT NOT NULL,
    ano INTEGER NOT NULL,
    mes INTEGER NOT NULL,
    qtd_balconistas INTEGER NOT NULL,
    min_simultaneos INTEGER NOT NULL,
    min_simultaneos_domingo INTEGER,
    dia_pico TEXT NOT NULL,
    turno_pico TEXT NOT NULL,
    grade_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_escalas_loja ON escalas (id_loja, ano, mes);
CREATE INDEX IF NOT EXISTS idx_escalas_criado ON escalas (criado_em);
"""


def caminho_banco():
    return ARQUIVO


def conectar():
    PASTA.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(ARQUIVO)
    conexao.row_factory = sqlite3.Row
    conexao.executescript(_SCHEMA)
    return conexao


def _codigo(agora):
    return f"{agora.strftime('%d%m%Y')}-{secrets.randbelow(100_000_000):08d}"


def _registros(df_mes):
    dias = sorted(
        (coluna for coluna in df_mes.columns if coluna != "Balconista"),
        key=lambda coluna: int(coluna),
    )
    ordem = ["Balconista", *dias]
    return df_mes[ordem].to_dict(orient="records")


def grade_de_json(texto):
    df_mes = pd.DataFrame(json.loads(texto))
    dias = sorted(
        (coluna for coluna in df_mes.columns if coluna != "Balconista"),
        key=lambda coluna: int(coluna),
    )
    return df_mes[["Balconista", *dias]]


def salvar_escala(parametros, df_mes, agora=None):
    agora = agora or datetime.now().replace(microsecond=0)
    grade = json.dumps(_registros(df_mes), ensure_ascii=False)
    valores = (
        agora.isoformat(sep=" "),
        int(parametros["id_loja"]),
        parametros["classificacao"],
        int(parametros["ano"]),
        int(parametros["mes"]),
        int(parametros["qtd_balconistas"]),
        int(parametros["min_simultaneos"]),
        parametros["min_simultaneos_domingo"],
        parametros["dia_pico"],
        parametros["turno_pico"],
        grade,
    )
    with conectar() as conexao:
        for _ in range(8):
            codigo = _codigo(agora)
            try:
                conexao.execute(
                    """
                    INSERT INTO escalas (
                        codigo, criado_em, id_loja, classificacao, ano, mes,
                        qtd_balconistas, min_simultaneos, min_simultaneos_domingo,
                        dia_pico, turno_pico, grade_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (codigo, *valores),
                )
                return codigo
            except sqlite3.IntegrityError:
                conexao.rollback()
                continue
    raise RuntimeError("Não foi possível gerar um código único para a escala.")


def _clausulas(id_loja, ano, mes, codigo, criado_de, criado_ate):
    filtros = []
    valores = []
    if id_loja is not None:
        filtros.append("id_loja = ?")
        valores.append(int(id_loja))
    if ano is not None:
        filtros.append("ano = ?")
        valores.append(int(ano))
    if mes is not None:
        filtros.append("mes = ?")
        valores.append(int(mes))
    if codigo:
        filtros.append("codigo LIKE ?")
        valores.append(f"%{codigo.strip()}%")
    if criado_de is not None:
        filtros.append("date(criado_em) >= ?")
        valores.append(criado_de.isoformat())
    if criado_ate is not None:
        filtros.append("date(criado_em) <= ?")
        valores.append(criado_ate.isoformat())
    onde = f"WHERE {' AND '.join(filtros)}" if filtros else ""
    return onde, valores


def listar_escalas(id_loja=None, ano=None, mes=None, codigo=None, criado_de=None, criado_ate=None):
    onde, valores = _clausulas(id_loja, ano, mes, codigo, criado_de, criado_ate)
    with conectar() as conexao:
        linhas = conexao.execute(
            f"""
            SELECT codigo, criado_em, id_loja, classificacao, ano, mes,
                   qtd_balconistas, min_simultaneos, min_simultaneos_domingo,
                   dia_pico, turno_pico
            FROM escalas
            {onde}
            ORDER BY criado_em DESC, codigo DESC
            """,
            valores,
        ).fetchall()
    return pd.DataFrame([dict(linha) for linha in linhas])


def obter_escala(codigo):
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT * FROM escalas WHERE codigo = ?",
            (codigo,),
        ).fetchone()
    if linha is None:
        return None
    registro = dict(linha)
    registro["grade"] = grade_de_json(registro.pop("grade_json"))
    return registro
