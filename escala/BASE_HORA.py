import pyodbc
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(override=True)

servidor = os.getenv('SERVIDOR')
basedados = os.getenv('BASEDADOS')
login = os.getenv('LOGIN')
senha = os.getenv('SENHA')
token = os.getenv('TOKEN_BOT')
frases_json = os.getenv('DICIONARIO_FRASES')
ids_json = os.getenv('DICIONARIO_IDS')


conexao_banco = pyodbc.connect(f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={servidor};DATABASE={basedados};UID={login};PWD={senha};TrustServerCertificate=yes; timeout=5000')

query = '''
    DECLARE
        @MesAtual      datetime = DATEFROMPARTS(YEAR(GETDATE()), MONTH(GETDATE()), 1),
        @DtInicio      datetime,
        @DtFimExclusivo datetime;

    SET @DtInicio       = DATEADD(MONTH, -3, @MesAtual);
    SET @DtFimExclusivo = DATEADD(MONTH,  1, @MesAtual);

    WITH BaseFiltrada AS (
        SELECT
            t.CD_FILIAL,
            t.CD_VD,
            t.CD_VEND,
            TRY_CONVERT(datetime, t.DT_CONSD, 103) AS DtConsd
        FROM PDV_VD_IT t
        WHERE t.CD_EMP = 1
        AND t.DT_CONSD IS NOT NULL
    ),
    PeriodoValido AS (
        SELECT
            b.CD_FILIAL,
            b.CD_VD,
            b.CD_VEND,
            -- Trunca direto para o início da hora sem precisar de um terceiro CTE
            DATEADD(HOUR, DATEDIFF(HOUR, 0, b.DtConsd), 0) AS FaixaHora
        FROM BaseFiltrada b
        WHERE b.DtConsd >= @DtInicio
        AND b.DtConsd <  @DtFimExclusivo
    )
    SELECT
        CD_FILIAL,
        FaixaHora AS InicioHora,
        DATEADD(HOUR, 1, FaixaHora) AS FimHora,
        DATEPART(HOUR, FaixaHora) AS HoraInicio,
        CASE ((DATEDIFF(DAY, '19000101', FaixaHora) % 7) + 7) % 7
            WHEN 0 THEN 'Segunda-feira'
            WHEN 1 THEN 'Terça-feira'
            WHEN 2 THEN 'Quarta-feira'
            WHEN 3 THEN 'Quinta-feira'
            WHEN 4 THEN 'Sexta-feira'
            WHEN 5 THEN 'Sábado'
            WHEN 6 THEN 'Domingo'
        END AS DiaSemana,
        COUNT(DISTINCT CD_VD)   AS Qtd_Vendas_Distintas,
        COUNT(DISTINCT CD_VEND) AS Qtd_Vendedores_Distintos
    FROM PeriodoValido
    GROUP BY
        CD_FILIAL,
        FaixaHora
    ORDER BY
        CD_FILIAL,
        FaixaHora;
'''
lista_dias = ['Sábado','Domingo']

try:
    df_horas_filial = pd.read_sql(query, conexao_banco)

    df_filtrado = df_horas_filial[
        (~df_horas_filial['DiaSemana'].isin(lista_dias))
        & (df_horas_filial['HoraInicio'] > 5)
    ]

    df_grafico_geral = (df_filtrado.groupby(['CD_FILIAL', 'HoraInicio'], as_index=False).agg(
            P75_Vendas=('Qtd_Vendas_Distintas', lambda s: s.quantile(0.8)),
            Moda_Vendedores=(
                'Qtd_Vendedores_Distintos',
                lambda s: s.mode().max() if not s.mode().empty else pd.NA,
            ),
        ).sort_values(['CD_FILIAL', 'HoraInicio']))
 
    df_grafico_geral['CARGA_DE_TRABALHO'] = df_grafico_geral['P75_Vendas']/df_grafico_geral['Moda_Vendedores']
    df_grafico_geral = df_grafico_geral.rename(columns={'P75_Vendas':'Clientes',
                                                        'Moda_Vendedores':'Colaboradores',
                                                        'CARGA_DE_TRABALHO':'Carga'})



    df_filtrado_fin = df_horas_filial[
        (df_horas_filial['DiaSemana'].isin(lista_dias))
        & (df_horas_filial['HoraInicio'] > 5)
    ]

    df_grafico_geral_fin = (df_filtrado_fin.groupby(['CD_FILIAL', 'HoraInicio'], as_index=False).agg(
            P75_Vendas=('Qtd_Vendas_Distintas', lambda s: s.quantile(0.8)),
            Moda_Vendedores=(
                'Qtd_Vendedores_Distintos',
                lambda s: s.mode().max() if not s.mode().empty else pd.NA,
            ),
        ).sort_values(['CD_FILIAL', 'HoraInicio']))
 
    df_grafico_geral_fin['CARGA_DE_TRABALHO'] = df_grafico_geral_fin['P75_Vendas']/df_grafico_geral_fin['Moda_Vendedores']
    df_grafico_geral_fin = df_grafico_geral_fin.rename(columns={'P75_Vendas':'Clientes',
                                                        'Moda_Vendedores':'Colaboradores',
                                                        'CARGA_DE_TRABALHO':'Carga'})

    
    df_horas_filial.to_parquet('base_geral.parquet', index=False)
    df_grafico_geral_fin.to_parquet('base_grafico_hora_fim_de_semana.parquet', index=False)
    df_grafico_geral.to_parquet('base_grafico_hora.parquet', index=False)
    conexao_banco.close()
except Exception as e:
    print(f"Erro ao processar dados: {e}")
    conexao_banco.close()






