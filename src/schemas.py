import pandera as pa

# Definimos o que ESPERAMOS do arquivo "dados_brutos_simulados.csv"
schema_bronze = pa.DataFrameSchema({
    "Número": pa.Column(str, required=True),
    "Data da Extração": pa.Column(str, required=True),
    "Órgão Julgador": pa.Column(str, required=True),
    "Valor da causa": pa.Column(str, required=True),
    "Situação do processo": pa.Column(str, required=True),
    "Procurador Responsável": pa.Column(str, required=True),
    "UF": pa.Column(str, required=True),
    "Polo": pa.Column(str, required=True),
    "Classe": pa.Column(str, required=True),
    "Relator": pa.Column(str, required=True),
    "Código Matéria": pa.Column(str, required=True, nullable=True),
    "Matéria": pa.Column(str, required=True, nullable=True),
})