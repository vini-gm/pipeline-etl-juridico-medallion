import pytest
import pandas as pd
from src.pipeline_etl import RelatorioJuridico

@pytest.fixture
def etl():
    return RelatorioJuridico("fake.csv")

def test_conversao_valor(etl):
    etl.df_base = pd.DataFrame({
        "Valor da causa": ["R$ 1.000,00", "R$ 2.500,50\nR$ 2.600,00"],
        "Órgão Julgador": ["1T", "2T"],
        "Relator": ["Des. A", "Des. B"],
        "UF": ["SP", "RJ"],
        "Situação do processo": ["CONCLUÍDO", "PENDENTE"],
        "Data da Extração": ["01/01/2025", "02/01/2025"],
        "Código Matéria": ["1.2.3", "4.5.6"],
        "Matéria": ["Assunto X", "Assunto Y"]
    })
    etl._transformar_e_limpar_dados()
    assert etl.df_base.loc[0, 'Valor da causa'] == 1000.0
    assert etl.df_base.loc[1, 'Valor da causa'] == 2600.0

def test_padronizacao_orgao(etl):
    etl.df_base = pd.DataFrame({
        "Órgão Julgador": ["1T", "Corte Especial", "Não Informado"],
        "Relator": ["Des. X", "Presidente", "Des. Y"],
        "Valor da causa": ["R$ 1,00", "R$ 2,00", "R$ 3,00"],
        "UF": ["DF", "SP", "MG"],
        "Situação do processo": ["PENDENTE", "CONCLUÍDO", "PENDENTE"],
        "Data da Extração": ["01/01/2025", "02/01/2025", "03/01/2025"],
        "Código Matéria": ["1.0", "2.0", "3.0"],
        "Matéria": ["A", "B", "C"]
    })
    etl._transformar_e_limpar_dados()
    assert etl.df_base.loc[0, 'Órgão Padronizado'] == 'PRIMEIRA TURMA'
    assert etl.df_base.loc[1, 'Órgão Padronizado'] == 'CORTE ESPECIAL'
    assert etl.df_base.loc[2, 'Órgão Padronizado'] == 'Não Informado'

def test_combinar_codigos_assuntos(etl):
    linha = {'Código Matéria': '1.2.3\n4.5.6', 'Matéria': 'Assunto A\nAssunto B'}
    res = etl._combinar_codigos_e_assuntos(linha)
    assert res == ['1.2.3 - Assunto A', '4.5.6 - Assunto B']