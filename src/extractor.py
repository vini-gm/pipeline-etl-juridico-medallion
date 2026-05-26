import pandas as pd
from pathlib import Path
from loguru import logger
from schemas import schema_bronze
import pandera as pa

class DataExtractor:
    """Responsável unicamente pela extração/leitura dos dados brutos."""
    def __init__(self, caminho_entrada: Path):
        self.caminho_entrada = caminho_entrada

    def carregar_dados(self) -> pd.DataFrame:
        logger.info(f"Carregando dados brutos de: {self.caminho_entrada}")
        if not self.caminho_entrada.exists():
            logger.error(f"Arquivo não encontrado: {self.caminho_entrada}")
            raise FileNotFoundError(f"Arquivo {self.caminho_entrada} ausente.")
        df = pd.read_csv(self.caminho_entrada, dtype=str)

        try:
            logger.info("Validando contrato de dados da camada Bronze via Pandera...")
            df_validado = schema_bronze.validate(df)
            logger.success("Contrato de dados validado com sucesso!")
            return df_validado
        except pa.errors.SchemaError as err:
            logger.critical(f"A origem enviou dados fora do padrão: {err}")
            raise