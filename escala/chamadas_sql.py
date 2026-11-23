consulta_metas = '''
    SELECT CD_FILIAL as CodFilial, 
        VLR_VD as META_VENDA, 
        QTDE_CUPONS as META_CLIENTES, 
        QTDE_ITENS as META_ITENS,
        (VLR_VD / QTDE_CUPONS) as META_TKM,
        (QTDE_ITENS / QTDE_CUPONS) as META_IPC
    FROM V_EST_META_FILIAL_DIARIO_TOTAL
    WHERE 1=1
    AND ANO_META = YEAR(GETDATE()) AND MES_META = MONTH(GETDATE()) AND DAY(DT_META) = DAY(GETDATE())
        '''

consulta_vendas_cp = '''
                SELECT v1.DT_VD,
                YEAR(v1.DT_VD) AS 'ANO',
                MONTH(v1.DT_VD) AS 'MES',
                v1.CD_FILIAL as 'CodFilial',
                v2.NR_ECF AS 'CD_VD',
                V2.CD_VD AS 'NM_VENDA_UN',
                v1.CD_PROD,
                v1.QT_IT,
                v1.TOT_IT,
                v1.VLR_CUSTO_MEDIO as 'VLR_CUSTO'
            FROM(
                SELECT*
                FROM PDV_VD_IT
                WHERE 1=1
                AND YEAR(DT_VD) = YEAR(GETDATE()) AND MONTH(DT_VD) = MONTH(GETDATE()) AND DAY(DT_VD) = DAY(GETDATE())
                )v1
            LEFT JOIN(
                SELECT*
                FROM PDV_VD
                WHERE 1=1
                AND YEAR(DT_VD) = YEAR(GETDATE()) AND MONTH(DT_VD) = MONTH(GETDATE()) AND DAY(DT_VD) = DAY(GETDATE())
            )v2 ON v1.CD_VD = v2.CD_VD AND v1.CD_FILIAL = v2.CD_FILIAL

            LEFT JOIN(
                SELECT*
                FROM V_BI_EST_PROD
            )v3  ON v1.CD_PROD = v3.Produto

            WHERE v2.ST_VD = 0 -- AQUI FILTRA APENAS VENDAS NÃO CANCELADAS
            AND V1.ST_IT NOT IN (2)
        '''

consulta_vendas_nf = '''
                SELECT             
                   v1.DT_EMI_NF AS 'DT_VD',
                   YEAR(v1.DT_EMI_NF) AS 'ANO',
                   MONTH(v1.DT_EMI_NF) AS 'MES',
                   v1.CD_FILIAL as 'CodFilial',
                   v2.NF_NF as 'CD_VD',
                   V2.CD_NF as 'NM_VENDA_UN',
                   v1.CD_PROD,
                   v1.QT_IT,
                   (v1.VLR_TOT_IT-v1.VLR_DESC) AS TOT_IT, -- EQUIVALE A VENDA LIOQUIDA DO BI
                   v1.VLR_CUSTO_IT AS 'VLR_CUSTO'

                FROM (
                    SELECT*
                    FROM V_EST_NF_SAI_IT
                    WHERE 1=1
                    AND YEAR(DT_EMI_NF) = YEAR(GETDATE()) AND MONTH(DT_EMI_NF) = MONTH(GETDATE()) AND DAY(DT_EMI_NF) = DAY(GETDATE())
                    AND STS_NF = 0
                    AND TP_MOV = 0
                    AND TP_MOV_OP_TRANSA = 1
                )v1

                LEFT JOIN (
                    SELECT*
                    FROM EST_NF_SAI
                    WHERE 1=1
                    AND YEAR(DT_EMI_NF) = YEAR(GETDATE()) AND MONTH(DT_EMI_NF) = MONTH(GETDATE()) AND DAY(DT_EMI_NF) = DAY(GETDATE())
                    AND CD_NT_MOV = 1 
                )v2 ON v1.CD_NF = v2.CD_NF and v1.CD_FILIAL = V2.CD_FILIAL
            '''


consulta_dev_cp = '''
                SELECT v1.DT_DEVO AS 'DT_VD',
                    YEAR(v1.DT_DEVO) AS 'ANO',
                    MONTH(v1.DT_DEVO) AS 'MES',
                    v1.CD_FILIAL as 'CodFilial',
                    v2.NR_ECF as 'CD_VD',
                    v1.CD_VD AS 'NM_VENDA_UN',
                    v1.CD_PROD,
                    (v1.QT_IT*-1) AS 'QT_IT',
                    (V1.VLR_IT*V1.QT_IT)*-1 AS 'TOT_IT', -- EQUIVALE A VENDA LIOQUIDA DO BI
                    (v1.VLR_CUSTO*0) AS VLR_CUSTO

                FROM(
                SELECT*
                FROM PDV_VD_DEV_EST_PROD_IMP
                WHERE 1=1
                AND YEAR(DT_DEVO) = YEAR(GETDATE()) AND MONTH(DT_DEVO) = MONTH(GETDATE()) AND DAY(DT_DEVO) = DAY(GETDATE())
                )v1
                LEFT JOIN(
                SELECT*
                FROM  V_PDV_VD_DEVO
                )v2 ON v1.CD_VD = v2.CD_VD and v1.CD_FILIAL = v2.CD_FILIAL
 
        '''


consulta_dev_nf = '''

                --- DEVOLUÇÕES NF
                SELECT             
                   v1.DT_EMI_NF AS 'DT_VD',
                   YEAR(v1.DT_EMI_NF) AS 'ANO',
                   MONTH(v1.DT_EMI_NF) AS 'MES',
                   v1.CD_FILIAL as 'CodFilial',
                   v1.NR_NF AS 'CD_VD',
                   v1.CD_PROD,
                   v1.QT_IT *-1 AS 'QT_IT',
                   (v1.VLR_TOT_IT-v1.VLR_DESC)*-1 AS TOT_IT, -- EQUIVALE A VENDA LIOQUIDA DO BI
                   v1.VLR_CUSTO_IT*0 AS VLR_CUSTO

                FROM (
                    SELECT*
                    FROM V_EST_NF_ENT_IT
                    WHERE 1=1
                    AND YEAR(DT_EMI_NF) = YEAR(GETDATE()) AND MONTH(DT_EMI_NF) = MONTH(GETDATE()) AND DAY(DT_EMI_NF) = DAY(GETDATE())
                    AND STS_NF = 0
                    AND TP_MOV = 11
                    AND TP_MOV_OP_TRANSA = 0
                    AND CD_NT_MOV = 3
                )v1

        '''


consulta_recarga = '''

        SELECT DT_CUPOM AS 'DT_VD',
            YEAR(DT_CUPOM) AS 'ANO',
            MONTH(DT_CUPOM) AS 'MES',
            CD_FILIAL as 'CodFilial',
            CD_CTR as 'CD_VD',
            NR_COO AS 'NM_VENDA_UN',
            999999 AS 'CD_PROD',
            1 AS 'QT_IT',
            VLR_TOT_CUPOM AS 'TOT_IT',
            (VLR_TOT_CUPOM* 0.955) AS 'VLR_CUSTO'

        FROM PDV_CUPOM_NAO_FISCAL
        WHERE 1=1
        AND YEAR(DT_CUPOM) = YEAR(GETDATE()) AND MONTH(DT_CUPOM) = MONTH(GETDATE()) AND DAY(DT_CUPOM) = DAY(GETDATE())
        AND TP_CUPOM_NAO_FISCAL = 3
        AND ST_CUPOM = 0

'''