import pandas as pd
from pathlib import Path
from loguru import logger

class DataLoader:
    """Responsável unicamente pela carga (L) e exportação dos dados processados."""

    def exportar_dataframe(self, df: pd.DataFrame, nome_arquivo: str, pasta_destino: Path) -> None:
        """Salva um DataFrame específico para a camada Silver."""
        if df.empty:
            logger.warning(f"DataFrame para {nome_arquivo} está vazio. Ignorando exportação.")
            return

        pasta_destino.mkdir(parents=True, exist_ok=True)

        caminho_parquet = pasta_destino / f"{nome_arquivo}.parquet"
        df.to_parquet(caminho_parquet, index=False)
        logger.success(f"Camada SILVER persistida: {caminho_parquet.name}")

    def exportar(self, dicionario_resultados: dict, pasta_destino: Path) -> None:
        logger.info(f"Salvando resultados finais na camada Gold: {pasta_destino}")
        pasta_destino.mkdir(parents=True, exist_ok=True)

        for nome, df in dicionario_resultados.items():
            if df.empty: continue

            # Tratamento de data para o Looker Studio
            df_csv = df.copy()
            for col in df_csv.select_dtypes(include=['datetime64']).columns:
                df_csv[col] = df_csv[col].dt.strftime('%Y-%m-%d')

            # Exporta CSV
            caminho_csv = pasta_destino / f"{nome}.csv"
            df_csv.to_csv(caminho_csv, index=False, encoding='utf-8-sig')
            logger.success(f"Arquivo CSV gerado: {caminho_csv.name}")

            # Exporta Parquet
            caminho_parquet = pasta_destino / f"{nome}.parquet"
            df.to_parquet(caminho_parquet, index=False)
            logger.success(f"Arquivo Parquet gerado: {caminho_parquet.name}")