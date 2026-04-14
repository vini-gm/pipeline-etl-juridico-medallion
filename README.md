# ⚖️ Pipeline de ETL Jurídico

Este projeto reproduz a arquitetura de Engenharia de Dados utilizada em uma **Procuradoria** para automação de relatórios gerenciais e Business Intelligence.

O pipeline processa dados brutos de processos judiciais (simulados), aplica regras de negócio complexas (limpeza de valores, padronização de órgãos, regex) e exporta tabelas otimizadas para dashboards.

## 🛠️ Tecnologias Utilizadas
- **Python 3.10+**
- **Pandas & Numpy:** Para manipulação de dados de alta performance (Vectorization).
- **Faker:** Para geração de dados sintéticos realistas.
- **Loguru:** Para observabilidade e logs do processo.

## 🚀 Como Executar

1. **Clone o repositório**
   ```bash
   git clone [https://github.com/vini-gm/pipeline-etl-juridico-replica-v1.git]
   cd pipeline-etl-juridico-replica-v1.git
   ```
2. **Gere os dados simulados (Mock)**
   ```bash
    python gerador_mock.py
   ```
3. **Rode o Pipeline de ETL**
   ```bash
   python pipeline_etl.py
   ```
## 📊 Resultados
O script processa os dados e gera na pasta `output_relatorios/`\
O pipeline transforma os dados brutos em um modelo otimizado para ferramentas de BI (Looker Studio/Power BI), seguindo princípios de **Modelagem Dimensional (Star Schema)**.
### 1. Tabela Fato
* **`base_analitica.csv`**: Consolidação final dos processos com dados limpos.
    * *Tratamentos:* Valores monetários convertidos, datas em ISO-8601, órgãos julgadores padronizados via Regex.

### 2. Tabelas Dimensionais & Agregadas
* **`performance.csv`**: Métricas de produtividade por procurador.
    * Aplicação de **Cross Join** entre calendário e lista de procuradores para identificar dias sem produção (0 processos), garantindo fidelidade nos gráficos temporais.
* **`dim_materias.csv`**: Granularidade por matéria jurídica.
    * Uso de **`explode()`** para transformar listas de códigos (arrays) em linhas individuais.
* **`dim_regionalizacao_uf.csv`**: Normalização geográfica.
    * Uso de **`melt()` (Unpivot)** para transformar colunas de múltiplos estados (`UF_1`, `UF_2`) em uma estrutura vertical para mapas de calor.
* **`dim_polo_pgfn.csv`**: Filtro qualificado dos processos onde a PGFN atua como Autor ou Réu.
