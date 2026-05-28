from pathlib import Path
from loguru import logger
from src.extractor import DataExtractor
from src.transform import DataTransformer
from src.load import DataLoader

# Configurações de pastas e logs
Path("logs").mkdir(exist_ok=True)
logger.add(
    "logs/{time:YYYY-MM-DD}_pipeline.log",
    rotation="1 day",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

PASTA_BRONZE = Path(__file__).parent.parent / 'data' / 'bronze'
PASTA_SILVER = Path(__file__).parent.parent / 'data' / 'silver'
PASTA_SILVER.mkdir(parents=True, exist_ok=True)
PASTA_GOLD = Path(__file__).parent.parent / 'data' / 'gold'
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

def main():
    logger.info(">>> INICIANDO PIPELINE <<<")
    try:
        # 1. Extraction (Bronze)
        extractor = DataExtractor(ARQUIVO_ENTRADA)
        df_bruto = extractor.carregar_dados()

        # 2. Transformation
        transformer = DataTransformer(df_bruto, MAPA_ORGAOS)
        transformer.transformar_e_limpar_dados()

        # 3. Loading Silver
        loader = DataLoader()
        loader.exportar_dataframe(transformer.df_base, nome_arquivo="base_limpa", pasta_destino=PASTA_SILVER)

        # 4. Loading Gold
        resultados_gold = transformer.executar_transformacoes()
        loader.exportar(resultados_gold, pasta_destino=PASTA_GOLD)

        logger.success(">>> PIPELINE EXECUTADO COM SUCESSO <<<")
    except Exception as e:
        logger.critical(f"Falha crítica no pipeline: {e}")
        raise

if __name__ == "__main__":
    main()