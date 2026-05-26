import pytest
import pandas as pd
from src.transform import DataTransformer

MAPA_ORGAOS_TESTE = {
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

@pytest.fixture
def transformer_vazio():
    """Fixture que inicializa o transformador com um DataFrame vazio para ser preenchido nos testes."""
    df_vazio = pd.DataFrame()
    return DataTransformer(df_vazio, MAPA_ORGAOS_TESTE)

def test_conversao_valor(transformer_vazio):
    # Preparamos o dado bruto simulando a Camada Bronze
    transformer_vazio.df_base = pd.DataFrame({
        "Valor da causa": ["R$ 1.000,00", "R$ 2.500,50\nR$ 2.600,00"],
        "Órgão Julgador": ["1T", "CE"],
        "Relator": ["Des. A", "Des. B"],
        "UF": ["SP", "RJ"],
        "Situação do processo": ["CONCLUÍDO", "PENDENTE"],
        "Data da Extração": ["01/05/2026", "02/05/2026"]
    })

    # Executa a limpeza da camada Silver
    transformer_vazio.transformar_e_limpar_dados()

    assert transformer_vazio.df_base.loc[0, 'Valor da causa'] == 1000.0
    assert transformer_vazio.df_base.loc[1, 'Valor da causa'] == 2600.0

def test_padronizacao_orgao(transformer_vazio):
    transformer_vazio.df_base = pd.DataFrame({
        "Órgão Julgador": ["1T", "Corte Especial", "Não Informado"],
        "Relator": ["Des. X", "Presidente", "Des. Y"],
        "Valor da causa": ["R$ 1,00", "R$ 2,00", "R$ 3,00"],
        "UF": ["DF", "SP", "MG"],
        "Situação do processo": ["PENDENTE", "CONCLUÍDO", "PENDENTE"],
        "Data da Extração": ["01/05/2026", "02/05/2026", "03/05/2026"]
    })

    transformer_vazio.transformar_e_limpar_dados()
    assert transformer_vazio.df_base.loc[0, 'Órgão Padronizado'] == 'PRIMEIRA TURMA'
    assert transformer_vazio.df_base.loc[1, 'Órgão Padronizado'] == 'CORTE ESPECIAL'
    assert transformer_vazio.df_base.loc[2, 'Órgão Padronizado'] == 'Não Informado'

def test_combinar_codigos_assuntos(transformer_vazio):
    linha = {'Código Matéria': '1.2.3\n4.5.6', 'Matéria': 'Assunto A\nAssunto B'}
    res = transformer_vazio._combinar_codigos_e_assuntos(linha)
    assert res == ['1.2.3 - Assunto A', '4.5.6 - Assunto B']