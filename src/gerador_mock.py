import csv
import pandas as pd
from faker import Faker
import random
from loguru import logger
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# Pasta de Logs
Path("logs").mkdir(exist_ok=True)
logger.add(
    "logs/{time:YYYY-MM-DD}_pipeline.log",
    rotation="1 day",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# Caminhos
PASTA_REFERENCIAS = Path(__file__).parent.parent / 'data' / 'referencias'
PASTA_BRONZE = Path(__file__).parent.parent / 'data' / 'bronze'
PASTA_BRONZE.mkdir(parents=True, exist_ok=True)

fake = Faker('pt_BR')
QTD_REGISTROS = 10000

# Simulando uma equipe de 12 Procuradores e 15 Relatores
LISTA_PROCURADORES = ["Francisco da Paz", "Isabela da Paz", "Anthony Nogueira", "Brayan Teixeira", "Liz Guerra",
                      "Luiz Miguel Albuquerque", "Cecilia Costela", "Leonardo Sales", "Benjamin Moraes", "Rafael Ramos",
                      "Ana Laura Vargas", "Evelyn da Cruz"]
LISTA_RELATORES = [f"{fake.first_name()} {fake.last_name()}" for _ in range(15)]


data_inicio = datetime.now() - timedelta(days=180)
data_fim = datetime.now()
dias_uteis = pd.date_range(start=data_inicio, end=data_fim, freq='B').strftime('%d/%m/%Y').tolist()
dias_uteis_set = set(dias_uteis)

pesos_mensais = {
    1: 0.3,   # janeiro
    2: 0.3,   # fevereiro
    7: 0.4,   # julho
    8: 0.4,   # agosto
    12: 0.5   # dezembro
}
pesos_dias = [pesos_mensais.get(int(dia[3:5]), 1.0) for dia in dias_uteis]

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

def gerar_valor_sujo():
    val1 = round(random.uniform(1000, 50000), 2)
    if random.random() > 0.7:
        val2 = round(val1 * 1.1, 2)
        return f"R$ {val1:,.2f}\nR$ {val2:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
    return f"R$ {val1:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')

def gerar_uf_suja():
    uf1 = fake.state_abbr()
    if random.random() > 0.5:
        uf2 = fake.state_abbr()
        return f"{uf1}\n{uf2}"
    return uf1

def gerar_orgao_variado():
    mapa_orgaos = [
        '1T', 'T1', '1ª Turma', 'PRIMEIRA TURMA', 'PRIMEIRATURMA',
        '2T', 'T2', '2ª Turma', 'SEGUNDA TURMA', 'SEGUNDATURMA',
        '3T', 'T3', '3ª Turma', 'TERCEIRA TURMA', 'TERCEIRATURMA',
        '4T', 'T4', '4ª Turma', 'QUARTA TURMA', 'QUARTATURMA',
        '5T', 'T5', '5ª Turma', 'QUINTA TURMA', 'QUINTATURMA',
        '6T', 'T6', '6ª Turma', 'SEXTA TURMA', 'SEXTATURMA',
        'CE', 'Corte Especial', 'CORTE ESPECIAL', 'CORTEESPECIAL',
        '1S', 'S1', '1ª Seção', 'PRIMEIRA SEÇÃO', 'PRIMEIRASEÇÃO',
        '2S', 'S2', '2ª Seção', 'SEGUNDA SEÇÃO', 'SEGUNDASEÇÃO',
        '3S', 'S3', '3ª Seção', 'TERCEIRA SEÇÃO', 'TERCEIRASEÇÃO',
        'Não Informado',
    ]
    return random.choice(mapa_orgaos)

def gerar_processo(procurador):
    data_extracao = random.choices(dias_uteis, weights=pesos_dias, k=1)[0]
    numero = f"{random.randint(1000000, 9999999)}-{random.randint(10, 99)}.{random.randint(2020, 2026)}.4.01.{random.randint(3000, 4000)}"
    classe = random.choice(lista_classes)
    relator = random.choice(LISTA_RELATORES)
    orgao = gerar_orgao_variado()
    valor = gerar_valor_sujo()
    uf = gerar_uf_suja()
    polo = random.choice(['Autor', 'Réu', 'Terceiro'])
    situacao = random.choice([
        'CONCLUÍDO - SENTENÇA', 'CONCLUÍDO - ACÓRDÃO',
        'PENDENTE DE ANÁLISE', 'AGUARDANDO PRAZO', 'TRIAGEM'
    ])

    qtd_materias = random.choices([1, 2, 3, 4], weights=[60, 20, 15, 5], k=1)[0]
    materias_escolhidas = random.sample(lista_materias, k=min(qtd_materias, len(lista_materias)))

    codigos = []
    assuntos = []
    for m in materias_escolhidas:
        if ' - ' in m:
            cod, desc = m.split(' - ', 1)
            codigos.append(cod.strip())
            assuntos.append(desc.strip())
        else:
            codigos.append(m.strip())
            assuntos.append('')
    codigo_mat = '\n'.join(codigos)
    assunto_mat = '\n'.join(assuntos)

    return {
        "Data da Extração": data_extracao,
        "Número": numero,
        "Classe": classe,
        "Procurador Responsável": procurador,
        "Relator": relator,
        "Órgão Julgador": orgao,
        "Valor da causa": valor,
        "UF": uf,
        "Polo": polo,
        "Situação do processo": situacao,
        "Código Matéria": codigo_mat,
        "Matéria": assunto_mat
    }

def main():
    logger.info(f">>> GERANDO {QTD_REGISTROS} PROCESSOS SINTÉTICOS COM DADOS 'SUJOS' <<<")

    afastamentos_set = {p: set() for p in LISTA_PROCURADORES}
    for procurador in LISTA_PROCURADORES:
        if random.random() < 0.3:
            duracao = random.randint(5, 15)
            inicio = data_inicio + timedelta(days=random.randint(0, max(0, (data_fim - data_inicio).days - duracao)))
            for i in range(duracao):
                dia = inicio + timedelta(days=i)
                dia_str = dia.strftime('%d/%m/%Y')
                if dia_str in dias_uteis_set:
                    afastamentos_set[procurador].add(dia_str)

    grupos_por_data = defaultdict(list)
    for _ in range(QTD_REGISTROS):
        proc = gerar_processo("")
        data = proc["Data da Extração"]
        grupos_por_data[data].append(proc)

    dados = []
    for data, processos_do_dia in grupos_por_data.items():
        ativos = [p for p in LISTA_PROCURADORES if data not in afastamentos_set[p]]
        if not ativos:
            ativos = LISTA_PROCURADORES[:]

        procuradores_escolhidos = random.choices(ativos, k=len(processos_do_dia))
        for proc, procurador in zip(processos_do_dia, procuradores_escolhidos):
            proc["Procurador Responsável"] = procurador
            dados.append(proc)

    df = pd.DataFrame(dados).astype(str)
    arquivo_saida = PASTA_BRONZE / 'dados_brutos_simulados.csv'
    df.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')

    logger.success(f"Base gerada em: {arquivo_saida}")

if __name__ == "__main__":
    random.seed(42)
    Faker.seed(42)

    main()