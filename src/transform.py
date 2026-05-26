import pandas as pd
import numpy as np
from loguru import logger

class DataTransformer:
    """Responsável unicamente pela transformação e modelagem dos dados."""

    def __init__(self, df_bruto: pd.DataFrame, mapa_orgaos: dict):
        self.df_base = df_bruto.copy()
        self.mapa_orgaos = mapa_orgaos
        self.resultados = {}
        self.calendario_dias_uteis = pd.DataFrame()

    def transformar_e_limpar_dados(self) -> None:
        logger.info("Aplicando transformação e limpeza...")
        df = self.df_base

        valor_causa = df['Valor da causa'].str.split('\n').str[-1]
        valor_causa = valor_causa.str.replace('R$', '', regex=False) \
            .str.replace('.', '', regex=False) \
            .str.replace(',', '.', regex=False) \
            .str.strip()
        df['Valor da causa'] = pd.to_numeric(valor_causa, errors='coerce').fillna(0.0)

        orgao_clean = df['Órgão Julgador'].str.replace(r'[\sªº]', '', regex=True).str.upper()
        df['Órgão Padronizado'] = orgao_clean.map(self.mapa_orgaos)
        mask_nulo = df['Órgão Padronizado'].isna()
        mask_presidente = df['Relator'].str.upper().str.contains('PRESIDENTE', na=False)
        df.loc[mask_nulo & mask_presidente, 'Órgão Padronizado'] = df.loc[mask_nulo & mask_presidente, 'Relator']
        df['Órgão Padronizado'] = df['Órgão Padronizado'].fillna(df['Órgão Julgador'])
        df['Órgão Padronizado'] = df['Órgão Padronizado'].replace(r'^\s*$', 'NÃO INFORMADO', regex=True)

        separar_ufs = df['UF'].str.strip().str.split('\n', expand=True)
        df['UF_1'] = separar_ufs[0].fillna('')
        df['UF_2'] = separar_ufs[1].fillna('') if separar_ufs.shape[1] > 1 else ''

        df['Status Normalizado'] = np.where(
            df['Situação do processo'].str.strip().str.upper().str.startswith('CONCLUÍDO'),
            'CONCLUÍDO',
            'PENDENTE'
        )
        df['Data da Extração'] = pd.to_datetime(df['Data da Extração'], dayfirst=True, errors='coerce')

    def _gerar_calendario(self) -> None:
        """Gera calendário de dias úteis baseado nas datas encontradas"""
        datas = self.df_base['Data da Extração'].dropna()
        if datas.empty: return

        dt_range = pd.date_range(start=datas.min(), end=datas.max(), freq='B')
        self.calendario_dias_uteis = pd.DataFrame({'Data': dt_range})

    @staticmethod
    def _combinar_codigos_e_assuntos(linha) -> list:
        codigos = linha['Código Matéria'].split('\n') if linha['Código Matéria'] else []
        assuntos = linha['Matéria'].split('\n') if linha['Matéria'] else []
        max_len = max(len(codigos), len(assuntos))
        codigos += [''] * (max_len - len(codigos))
        assuntos += [''] * (max_len - len(assuntos))

        resultado = []
        for cod, desc in zip(codigos, assuntos):
            cod = cod.strip()
            desc = desc.strip()
            if cod:
                resultado.append(f"{cod} - {desc}" if desc else cod)
        return resultado

    def gerar_dim_materias(self) -> None:
        logger.debug("Gerando tabela dimensional de Matéria...")
        df = self.df_base[['Data da Extração', 'Número', 'Órgão Padronizado', 'Código Matéria', 'Matéria']].copy()

        df['Código Matéria'] = df['Código Matéria'].fillna('').str.strip()
        df['Matéria'] = df['Matéria'].fillna('').str.strip()
        df['Lista Matérias'] = df.apply(self._combinar_codigos_e_assuntos, axis=1)

        df_explode = df.explode('Lista Matérias')
        df_explode = df_explode[df_explode['Lista Matérias'].notna() & (df_explode['Lista Matérias'] != '')]

        df_explode['Matéria Resumida'] = df_explode['Lista Matérias'].apply(
            lambda x: x if len(x) <= 40 else x[:37] + '...'
        )

        cols_dim = ['Data da Extração', 'Número', 'Órgão Padronizado', 'Lista Matérias', 'Matéria Resumida']
        df_final = df_explode[cols_dim].copy()

        df_final = df_final.rename(columns={'Órgão Padronizado': 'Órgão Julgador'})
        self.resultados['dim_materias'] = df_final

    def gerar_dim_regionalizacao_uf(self) -> None:
        """
        Gera tabela unificada de UFs.
        Técnica: Melt (Unpivot - Transforma colunas UF1/UF2 em linhas).
        """
        logger.debug("Gerando tabela dimensional de UFs...")
        df_uf_em_linhas = self.df_base.melt(
            id_vars=['Data da Extração', 'Número', 'Valor da causa'],
            value_vars=['UF_1', 'UF_2'],
            value_name='UF_Unificada'
        )
        df_final = df_uf_em_linhas[df_uf_em_linhas['UF_Unificada'] != ''].copy()
        self.resultados['dim_regionalizacao_uf'] = df_final

    def gerar_dim_polo(self) -> None:
        """Gera tabela filtrada apenas para Polos Relevantes"""
        logger.debug("Gerando tabela de Polo...")
        df = self.df_base.copy()
        filtro_polo = df['Polo'].str.upper().isin(['AUTOR', 'RÉU'])
        df_final = df[filtro_polo][['Data da Extração', 'Número', 'Polo']]
        self.resultados['dim_polo'] = df_final

    def gerar_performance_procurador(self) -> None:
        logger.debug("Calculando performance (com dias zerados)...")
        df = self.df_base.dropna(subset=['Data da Extração'])

        df_agg = df.groupby(['Data da Extração', 'Procurador Responsável']).size().reset_index(name='Qtd_Processos')
        if not self.calendario_dias_uteis.empty:
            procuradores = pd.DataFrame({'Procurador Responsável': df['Procurador Responsável'].unique()})
            datas = self.calendario_dias_uteis.copy().rename(columns={'Data': 'Data da Extração'})
            datas['key'] = 1
            procuradores['key'] = 1
            template_completo = pd.merge(datas, procuradores, on='key').drop('key', axis=1)
            df_final = pd.merge(template_completo, df_agg, on=['Data da Extração', 'Procurador Responsável'], how='left')
            df_final['Qtd_Processos'] = df_final['Qtd_Processos'].fillna(0).astype(int)
            self.resultados['performance_procurador'] = df_final

    def gerar_base_analitica(self) -> None:
        logger.debug("Gerando base analítica final...")
        df = self.df_base.copy()
        colunas_base = ['Data da Extração', 'Número', 'Classe', 'Procurador Responsável', 'Polo', 'Órgão Padronizado',
                        'Relator', 'Valor da causa', 'Status Normalizado', 'UF_1', 'UF_2', 'Código Matéria',
                        'Matéria']
        df_final = df[colunas_base].copy()

        df_final = df_final.rename(columns={
            'Órgão Padronizado': 'Órgão Julgador',
            'Status Normalizado': 'Status'
        })
        self.resultados['base_analitica'] = df_final

    def executar_transformacoes(self) -> dict:
        """Orquestra a execução de todas as transformações."""
        #self.transformar_e_limpar_dados()
        self._gerar_calendario()
        self.gerar_base_analitica()
        self.gerar_performance_procurador()
        self.gerar_dim_materias()
        self.gerar_dim_regionalizacao_uf()
        self.gerar_dim_polo()
        return self.resultados