"""
Classes:
    As classes de processos da Fazenda Pública abrangem ações envolvendo entes públicos
    (União, Estados, Municípios, autarquias) no polo ativo ou passivo, organizadas pelas
    Tabelas Processuais Unificadas (TPUs) do CNJ. As principais incluem Ação de Procedimento
    Comum, Execução Fiscal, Mandado de Segurança, Ação Civil Pública e Cumprimento de Sentença
    contra a Fazenda Pública

    - Principais Classes Processuais (Tabelas Unificadas):
        Execução Fiscal: Ações para cobrança de débitos tributários e não tributários (Federal,
                        Estadual, Municipal).
        Execução contra a Fazenda Pública (EFP): Processo para cobrar valores devidos pelo Estado.
        Mandado de Segurança: Ação para proteger direito líquido e certo contra ilegalidade de
                        autoridade pública.
        Ação de Procedimento Comum: Ações cíveis gerais (cobrança, indenização) contra ou movidas pela Fazenda.
        Juizado Especial da Fazenda Pública: Processos de menor complexidade e valor (até 60 salários mínimos)
                        contra Estados/Municípios.
        Ação Civil Pública: Defesa de interesses difusos ou coletivos.
        Cumprimento de Sentença (Classe 156): Execução individual derivada de ações coletivas.

Códigos e Matérias:

"""
import csv
import pandas as pd
from faker import Faker
import random
from loguru import logger
from pathlib import Path

# Pasta de Logs
Path("logs").mkdir(exist_ok=True)
logger.add(
    "logs/pipeline.log",
    rotation="5 MB",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Caminhos
PASTA_REFERENCIAS = Path(__file__).parent.parent / 'data' / 'referencias'
PASTA_BRONZE = Path(__file__).parent.parent / 'data' / 'bronze'
PASTA_BRONZE.mkdir(parents=True, exist_ok=True)

fake = Faker('pt_BR')
QTD_REGISTROS = 10000

logger.info(f">>> GERANDO {QTD_REGISTROS} PROCESSOS SINTÉTICOS COM DADOS 'SUJOS' <<<")

try:
    with open(PASTA_REFERENCIAS / 'classes.csv', 'r', encoding='utf-8-sig') as f:
        leitor_csv = csv.DictReader(f)
        lista_classes = [linha['codigo_descricao'] for linha in leitor_csv if linha['codigo_descricao'].strip()]
except FileNotFoundError:
    logger.error("Arquivo de classes não encontrado em data/referencias/classes.csv")
    raise

try:
    with open(PASTA_REFERENCIAS / 'materias.csv', 'r', encoding='utf-8-sig') as f:
        leitor_csv = csv.reader(f)
        lista_materias = [linha[0].strip() for linha in leitor_csv if linha and linha[0].strip()]
except FileNotFoundError:
    logger.error("Arquivo de matérias não encontrado em data/referencias/materias.csv")
    raise

# Simulando uma equipe de 12 Procuradores e 15 Relatores
LISTA_PROCURADORES = ["Francisco da Paz", "Isabela da Paz", "Anthony Nogueira", "Brayan Teixeira", "Liz Guerra",
                      "Luiz Miguel Albuquerque", "Cecilia Costela", "Leonardo Sales", "Benjamin Moraes", "Rafael Ramos",
                      "Ana Laura Vargas", "Evelyn da Cruz"
                      ]
LISTA_RELATORES = [f"{fake.first_name()} {fake.last_name()}" for _ in range(15)]

def gerar_valor_sujo():
    """
    Ex: 'R$ 10.000,00\nR$ 12.500,50'
    """
    val1 = round(random.uniform(1000, 50000), 2)
    if random.random() > 0.8:  # 20% de chance de ter histórico sujo
        val2 = round(val1 * 1.1, 2)
        return f"R$ {val1:,.2f}\nR$ {val2:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
    return f"R$ {val1:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')


def gerar_uf_suja():
    """
    Simula campo de UF com múltiplos estados (quebra de linha).
    Ex: 'DF\nSP'
    """
    uf1 = fake.state_abbr()
    if random.random() > 0.9:  # 10% de chance de ser multi-estado
        uf2 = fake.state_abbr()
        return f"{uf1}\n{uf2}"
    return uf1


def gerar_orgao_variado():
    """
    Gera variações para testar o mapa de normalização.
    Mistura siglas ('1T') com nomes extensos ('Primeira Turma').
    """
    mapa_orgaos = [
        '1T', 'T1', '1ª Turma', 'PRIMEIRA TURMA', 'PRIMEIRATURMA', '1  Turma',
        '2T', 'T2', '2ª Turma', 'SEGUNDA TURMA', 'SEGUNDATURMA',
        '3T', 'T3', '3ª Turma', 'TERCEIRA TURMA', 'TERCEIRATURMA',
        '4T', 'T4', '4ª Turma', 'QUARTA TURMA', 'QUARTATURMA',
        '5T', 'T5', '5ª Turma', 'QUINTA TURMA', 'QUINTATURMA',
        '6T', 'T6', '6ª Turma', 'SEXTA TURMA', 'SEXTATURMA',
        'CE', 'Corte Especial', 'CORTE ESPECIAL', 'CORTEESPECIAL',
        '1S', 'S1', '1ª Seção', 'PRIMEIRA SEÇÃO', 'PRIMEIRASEÇÃO',
        '2S', 'S2', '2ª Seção', 'SEGUNDA SEÇÃO', 'SEGUNDASEÇÃO',
        '3S', 'S3', '3ª Seção', 'TERCEIRA SEÇÃO', 'TERCEIRASEÇÃO',
        'Não Informado', '', ' '
    ]
    return random.choice(mapa_orgaos)

def gerar_processo():
    data_extracao = fake.date_between(start_date='-180d', end_date='today')

    # Sorteia um dos procuradores da lista fixa. random.choice garante distribuição uniforme
    procurador = random.choice(LISTA_PROCURADORES)
    relator = random.choice(LISTA_RELATORES)
    classe = random.choice(lista_classes)

    qtd_materias = random.choices([1, 2, 3, 4], weights=[60, 20, 15, 5], k=1)[0]
    materias_escolhidas = random.sample(lista_materias, k=min(qtd_materias, len(lista_materias)))

    codigos = []
    assuntos = []
    for m in materias_escolhidas:
        if ' - ' in m:
            codigo, descricao = m.split(' - ', 1)
            codigos.append(codigo.strip())
            assuntos.append(descricao.strip())
        else:
            codigos.append(m.strip())
            assuntos.append('')

    codigo_mat = '\n'.join(codigos)
    assunto_mat = '\n'.join(assuntos)

    return {
        "Data da Extração": data_extracao.strftime('%d/%m/%Y'),
        "Número": f"{random.randint(1000000, 9999999)}-{random.randint(10, 99)}.{random.randint(2020, 2026)}.4.01.{random.randint(3000, 4000)}",
        "Classe": classe,
        "Procurador Responsável": procurador,
        "Relator": relator,
        "Órgão Julgador": gerar_orgao_variado(),
        "Valor da causa": gerar_valor_sujo(),
        "UF": gerar_uf_suja(),
        "Polo": random.choice(['Autor', 'Réu', 'Terceiro']),
        "Situação do processo": random.choice([
            'CONCLUÍDO - SENTENÇA', 'CONCLUÍDO - ACÓRDÃO',
            'PENDENTE DE ANÁLISE', 'AGUARDANDO PRAZO', 'TRIAGEM'
        ]),
        "Código Matéria": codigo_mat,
        "Matéria": assunto_mat
    }

dados = [gerar_processo() for _ in range(QTD_REGISTROS)]
df = pd.DataFrame(dados).astype(str)

arquivo_saida = PASTA_BRONZE / 'dados_brutos_simulados.csv'
df.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')

logger.success(f"Base gerada em: {arquivo_saida}")