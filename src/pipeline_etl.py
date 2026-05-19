import pandas as pd
import numpy as np
from pathlib import Path
from loguru import logger

# Pasta de Logs
Path("logs").mkdir(exist_ok=True)
logger.add(
    "logs/pipeline.log",
    rotation="5 MB",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

PASTA_BRONZE = Path(__file__).parent.parent / 'data' / 'bronze'
PASTA_SILVER = Path(__file__).parent.parent /'data'/ 'silver'
PASTA_GOLD = Path(__file__).parent.parent / 'data'/ 'gold'
PASTA_SILVER.mkdir(parents=True, exist_ok=True)
PASTA_GOLD.mkdir(parents=True, exist_ok=True)

ARQUIVO_ENTRADA = PASTA_BRONZE / 'dados_brutos_simulados.csv'

MAPA_ORGAOS = {
    '1T': 'PRIMEIRA TURMA', 'T1': 'PRIMEIRA TURMA', 'PRIMEIRATURMA': 'PRIMEIRA TURMA', '1TURMA': 'PRIMEIRA TURMA',
    '2T': 'SEGUNDA TURMA', 'T2': 'SEGUNDA TURMA', 'SEGUNDATURMA': 'SEGUNDA TURMA', '2TURMA': 'SEGUNDA TURMA',
    '3T': 'TERCEIRA TURMA', 'T3': 'TERCEIRA TURMA', 'TERCEIRATURMA': 'TERCEIRA TURMA', '3TURMA': 'TERCEIRA TURMA',
    '4T': 'QUARTA TURMA', 'T4': 'QUARTA TURMA', 'QUARTATURMA': 'QUARTA TURMA', '4TURMA': 'QUARTA TURMA',
    '5T': 'QUINTA TURMA', 'T5': 'QUINTA TURMA', 'QUINTATURMA': 'QUINTA TURMA', '5TURMA': 'QUINTA TURMA',
    '6T': 'SEXTA TURMA', 'T6': 'SEXTA TURMA', 'SEXTATURMA': 'SEXTA TURMA', '6TURMA': 'SEXTA TURMA',
    'CE': 'CORTE ESPECIAL', 'CORTEESPECIAL': 'CORTE ESPECIAL',
    '1S': 'PRIMEIRA SEÇÃO', 'S1': 'PRIMEIRA SEÇÃO', 'PRIMEIRASEÇÃO': 'PRIMEIRA SEÇÃO', '1SEÇÃO': 'PRIMEIRA SEÇÃO',
    '2S': 'SEGUNDA SEÇÃO', 'S2': 'SEGUNDA SEÇÃO', 'SEGUNDASEÇÃO': 'SEGUNDA SEÇÃO', '2SEÇÃO': 'SEGUNDA SEÇÃO',
    '3S': 'TERCEIRA SEÇÃO', 'S3': 'TERCEIRA SEÇÃO', 'TERCEIRASEÇÃO': 'TERCEIRA SEÇÃO', '3SEÇÃO': 'TERCEIRA SEÇÃO',
    '4S': 'QUARTA SEÇÃO', 'S4': 'QUARTA SEÇÃO', 'QUARTASEÇÃO': 'QUARTA SEÇÃO', '4SEÇÃO': 'QUARTA SEÇÃO',
    '5S': 'QUINTA SEÇÃO', 'S5': 'QUINTA SEÇÃO', 'QUINTASEÇÃO': 'QUINTA SEÇÃO', '5SEÇÃO': 'QUINTA SEÇÃO'
}

class RelatorioJuridico:
    """
    Classe responsável pelo pipeline de ETL dos processos de uma equipe.
    Simula a arquitetura original utilizada na PGFN, adaptada para dados sintéticos.
    """

    def __init__(self, arquivo_entrada):
        self.arquivo_entrada = Path(arquivo_entrada)
        self.df_base = pd.DataFrame()
        self.resultados = {}
        self.calendario_dias_uteis = pd.DataFrame()

    def carregar_dados(self) -> None:
        logger.info(f"Carregando dados de: {self.arquivo_entrada}")

        if not self.arquivo_entrada.exists():
            logger.error("Arquivo de entrada não encontrado. Rode o gerador_dados.py primeiro.")
            raise FileNotFoundError("Base de dados mock não encontrada.")
        self.df_base = pd.read_csv(self.arquivo_entrada, dtype=str)
        logger.info(f"Dados carregados: {len(self.df_base)} registros.")

    def _transformar_e_limpar_dados(self) -> None:
        logger.info("Aplicando transformação e limpeza...")
        df = self.df_base

        valor_causa = df['Valor da causa'].str.split('\n').str[-1]
        valor_causa = valor_causa.str.replace('R$', '', regex=False) \
            .str.replace('.', '', regex=False) \
            .str.replace(',', '.', regex=False) \
            .str.strip()
        df['Valor da causa'] = pd.to_numeric(valor_causa, errors='coerce').fillna(0.0)

        orgao_clean = df['Órgão Julgador'].str.replace(r'[\sªº]', '', regex=True).str.upper()
        df['Órgão Padronizado'] = orgao_clean.map(MAPA_ORGAOS)
        mask_nulo = df['Órgão Padronizado'].isna()
        mask_presidente = df['Relator'].str.upper().str.contains('PRESIDENTE', na=False)
        df.loc[mask_nulo & mask_presidente, 'Órgão Padronizado'] = df.loc[mask_nulo & mask_presidente, 'Relator']
        df['Órgão Padronizado'] = df['Órgão Padronizado'].fillna(df['Órgão Julgador'])

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
    def _combinar_codigos_e_assuntos(linha):
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

    def _gerar_dim_materias(self) -> None:
        """
        Gera tabela dimensional explodida por Matéria.
        Técnica: Explode (Transforma lista em linhas).
        """
        logger.debug("Gerando tabela dimensional de Matéria...")

        df = self.df_base[['Data da Extração', 'Número', 'Órgão Padronizado', 'Código Matéria', 'Matéria']].copy()

        df['Código Matéria'] = df['Código Matéria'].fillna('').str.strip()
        df['Matéria'] = df['Matéria'].fillna('').str.strip()

        df['Lista Matérias'] = df.apply(self._combinar_codigos_e_assuntos, axis=1)

        df_explode = df.explode('Lista Matérias')
        df_explode = df_explode[df_explode['Lista Matérias'].notna() & (df_explode['Lista Matérias'] != '')]

        cols_dim = ['Data da Extração', 'Número', 'Órgão Padronizado', 'Lista Matérias']
        self.resultados['dim_materias'] = df_explode[cols_dim]


    def _gerar_dim_regionalizacao_uf(self) -> None:
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


    def _gerar_dim_polo(self) -> None:
        """Gera tabela filtrada apenas para Polos Relevantes"""
        logger.debug("Gerando tabela de Polo...")
        df = self.df_base.copy()
        filtro_polo = df['Polo'].str.upper().isin(['AUTOR', 'RÉU'])
        df_final = df[filtro_polo][['Data da Extração', 'Número', 'Polo']]
        self.resultados['dim_polo'] = df_final


    def _salvar_silver(self) -> None:
        """Persiste a base limpa (Silver) em disco."""
        caminho_silver = PASTA_SILVER / "base_limpa.csv"
        df_silver = self.df_base.copy()
        if 'Data da Extração' in df_silver.columns:
            df_silver['Data da Extração'] = df_silver['Data da Extração'].dt.strftime('%Y-%m-%d')
        df_silver.to_csv(caminho_silver, index=False, encoding='utf-8-sig')
        logger.info(f"Camada Silver salva em: {caminho_silver}")


    def processar_relatorios(self) -> None:
        """Orquestrador Principal da Transformação"""
        self.df_base.drop_duplicates(subset=['Número', 'Classe'], keep='last', inplace=True)

        # Transformações Gerais (Base)
        self._transformar_e_limpar_dados()
        self._gerar_calendario()

        self._salvar_silver()

        # Geração das Tabelas (Fato e Dimensões)
        self._gerar_performance_procurador()
        self._gerar_base_analitica()
        self._gerar_dim_materias()
        self._gerar_dim_regionalizacao_uf()
        self._gerar_dim_polo()

    def _gerar_performance_procurador(self) -> None:
        logger.debug("Calculando performance (com dias zerados)...")

        df = self.df_base.dropna(subset=['Data da Extração'])

        df_agg = df.groupby(['Data da Extração', 'Procurador Responsável']).size().reset_index(name='Qtd_Processos')
        if not self.calendario_dias_uteis.empty:
            procuradores = pd.DataFrame({'Procurador Responsável': df['Procurador Responsável'].unique()})
            datas = self.calendario_dias_uteis.copy().rename(columns={'Data': 'Data da Extração'})
            datas['key'] = 1
            procuradores['key'] = 1
            template_completo = pd.merge(datas, procuradores, on='key').drop('key', axis=1)
            df_final = pd.merge(template_completo, df_agg, on=['Data da Extração', 'Procurador Responsável'],
                                how='left')
            df_final['Qtd_Processos'] = df_final['Qtd_Processos'].fillna(0).astype(int)
            self.resultados['performance_procurador'] = df_final

    def _gerar_base_analitica(self) -> None:
        logger.debug("Gerando base analítica final...")
        df = self.df_base.copy()
        df['pendentes'] = df['Status Normalizado'] == 'PENDENTE'
        colunas_base = ['Data da Extração', 'Número', 'Classe', 'Procurador Responsável', 'Polo', 'Órgão Padronizado',
                        'Relator', 'Valor da causa', 'Status Normalizado', 'pendentes', 'UF_1', 'UF_2', 'Código Matéria',
                        'Matéria'
                        ]
        self.resultados['base_analitica'] = df[colunas_base].copy()

    def exportar_dados(self) -> None:
        logger.info(f"Salvando resultados em {PASTA_GOLD}...")

        for nome, df in self.resultados.items():
            if df.empty: continue

            df_csv = df.copy()
            for colunas in df_csv.select_dtypes(include=['datetime64']).columns:
                df_csv[colunas] = df_csv[colunas].dt.strftime('%Y-%m-%d')
            caminho_csv = PASTA_GOLD / f"{nome}.csv"
            df_csv.to_csv(caminho_csv, index=False, encoding='utf-8-sig')
            logger.success(f"Arquivo gerado: {caminho_csv.name}")

            caminho_parquet = PASTA_GOLD / f"{nome}.parquet"
            df.to_parquet(caminho_parquet, index=False)
            logger.success(f"Arquivo gerado: {caminho_parquet.name}")


    def executar(self) -> None:
        self.carregar_dados()
        self.processar_relatorios()
        self.exportar_dados()

def main():
    logger.info(">>> INICIANDO PIPELINE (MOCK) <<<")
    try:
        etl = RelatorioJuridico(ARQUIVO_ENTRADA)
        etl.executar()
        logger.success("Pipeline finalizado com sucesso.")

    except Exception as e:
        logger.exception(f"Erro crítico no pipeline: {e}")

if __name__ == "__main__":
    main()