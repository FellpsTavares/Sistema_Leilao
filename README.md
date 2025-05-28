# Sistema de Controle de Leilões em Python

## Introdução

Este documento detalha a implementação de um sistema de controle de leilões desenvolvido em Python. O sistema foi projetado para gerenciar o cadastro de leilões, participantes e lances, aplicando um conjunto específico de regras de negócio. Uma característica fundamental deste projeto é a inclusão de testes unitários abrangentes, garantindo 100% de cobertura do código implementado, o que assegura a robustez e a confiabilidade das funcionalidades.

O sistema atual opera inteiramente em memória, sem persistência de dados em banco de dados ou arquivos. Ele foca na lógica de negócio principal, servindo como um núcleo sólido para futuras expansões, como a integração com um banco de dados (por exemplo, MySQL) e o desenvolvimento de interfaces gráficas ou APIs web.

## Arquitetura e Estrutura do Projeto

O projeto está organizado em uma estrutura de diretórios clara, separando o código fonte dos testes:

```
leilao_system/
├── src/                     # Diretório contendo o código fonte do sistema
│   ├── __init__.py          # Marca o diretório como um pacote Python
│   ├── models.py            # Define as classes de modelo (Participante, Lance, Leilao, EstadoLeilao)
│   ├── sistema.py           # Contém a classe principal SistemaLeiloes para gerenciar o sistema
│   └── exceptions.py        # Define as exceções customizadas
├── tests/                   # Diretório contendo os testes unitários
│   ├── __init__.py          # Marca o diretório como um pacote Python
│   ├── test_models.py       # Testes unitários para as classes em models.py
│   └── test_sistema.py      # Testes unitários para a classe SistemaLeiloes
├── .coverage                # Arquivo gerado pelo coverage (após execução dos testes)
└── coverage_report.txt    # Relatório de cobertura de testes gerado
```

### Componentes Principais

*   **`src/models.py`**: Este módulo define as entidades centrais do sistema:
    *   `Participante`: Representa um participante do leilão, com atributos como nome, CPF (único), email (único) e data de nascimento. Inclui validações básicas para CPF e email.
    *   `Lance`: Representa um lance feito por um participante em um leilão. Contém o participante e o valor do lance.
    *   `EstadoLeilao`: Enumeração (`Enum`) que define os possíveis estados de um leilão: `INATIVO`, `ABERTO`, `FINALIZADO`, `EXPIRADO`.
    *   `Leilao`: Representa um item a ser leiloado. Possui nome, lance mínimo, datas de início e término, estado atual e uma lista de lances recebidos. Implementa a lógica de transição de estados, validação de lances e regras de alteração/exclusão.
*   **`src/exceptions.py`**: Define exceções customizadas (`ParticipanteInvalido`, `LeilaoInvalido`, `LanceInvalido`) para lidar com erros específicos do domínio do problema, tornando o tratamento de erros mais claro e específico.
*   **`src/sistema.py`**: Contém a classe `SistemaLeiloes`, que atua como a fachada principal do sistema. Ela gerencia coleções de leilões e participantes (atualmente em dicionários na memória) e expõe métodos para realizar as operações principais: cadastrar/alterar/excluir participantes e leilões, propor lances, listar leilões (com filtros), listar lances de um leilão, obter maior/menor lance, obter ganhador e simular a notificação do ganhador.
*   **`tests/`**: Contém os testes unitários utilizando o framework `unittest` do Python e a biblioteca `freezegun` para controlar o tempo em testes que dependem de datas e horas. Os testes cobrem todas as classes e métodos, incluindo cenários de sucesso, falha e casos de borda, garantindo 100% de cobertura.

## Funcionalidades e Regras de Negócio

O sistema implementa as seguintes funcionalidades e regras:

### 1. Cadastro e Manutenção de Leilões

*   **Criação**: Um leilão é criado com nome, lance mínimo, data/hora de início e data/hora de término.
*   **Estado Inicial**: Todo leilão recém-criado inicia no estado `INATIVO`.
*   **Transição para ABERTO**: Um leilão passa para o estado `ABERTO` automaticamente quando a data/hora atual alcança ou ultrapassa a data/hora de início definida. Somente leilões `ABERTOS` podem receber lances.
*   **Transição para FINALIZADO**: Um leilão passa para o estado `FINALIZADO` automaticamente quando a data/hora atual alcança ou ultrapassa a data/hora de término E ele recebeu pelo menos um lance.
*   **Transição para EXPIRADO**: Um leilão passa para o estado `EXPIRADO` automaticamente quando a data/hora atual alcança ou ultrapassa a data/hora de término E ele NÃO recebeu nenhum lance.
*   **Restrições de Alteração/Exclusão**: Leilões nos estados `ABERTO` ou `FINALIZADO` não podem ser alterados ou excluídos. Apenas leilões `INATIVO` ou `EXPIRADO` podem sofrer modificações ou ser removidos.
*   **Restrição de Estado**: Leilões `EXPIRADO` não podem transitar para `FINALIZADO`.

### 2. Listagem de Leilões

*   É possível listar todos los leilões cadastrados.
*   A listagem pode ser filtrada por:
    *   **Estado**: Exibir apenas leilões em um estado específico (`INATIVO`, `ABERTO`, `FINALIZADO`, `EXPIRADO`).
    *   **Intervalo de Datas**: Exibir leilões cuja data de início OU data de término esteja dentro de um intervalo de datas fornecido (data inicial e/ou data final do intervalo).
    *   **Combinação**: É possível combinar filtros de estado e data.

### 3. Cadastro e Manutenção de Participantes

*   **Criação**: Um participante é cadastrado com nome, CPF (único), email (único) e data de nascimento.
*   **Validação**: CPF e Email são validados para garantir unicidade no sistema.
*   **Restrição de Exclusão**: Um participante não pode ser excluído se já tiver realizado algum lance em qualquer leilão.

### 4. Lances

*   **Pré-requisito**: Somente participantes previamente cadastrados podem fazer lances.
*   **Estado do Leilão**: Lances só são aceitos em leilões que estão no estado `ABERTO`.
*   **Imutabilidade**: Um lance, uma vez feito, não pode ser alterado.
*   **Valor Mínimo**: Todo lance deve ter um valor maior que o lance mínimo definido para o leilão.
*   **Valor Progressivo**: Cada novo lance para um mesmo leilão deve ser estritamente maior que o valor do último lance registrado para aquele leilão.
*   **Restrição de Sequência**: Um mesmo participante não pode fazer dois lances consecutivos para o mesmo leilão. Outro participante deve fazer um lance intermediário.
*   **Ganhador**: Quando um leilão atinge sua data/hora de término e possui lances, o participante que fez o maior lance válido é considerado o ganhador.
*   **Listagem de Lances**: É possível obter a lista de todos os lances feitos para um leilão específico, ordenada crescentemente pelo valor do lance.
*   **Maior e Menor Lance**: É possível consultar qual foi o maior e o menor lance válido efetuado para um leilão específico.
*   **Notificação do Ganhador**: O sistema inclui uma funcionalidade (atualmente simulada via `print`) para notificar o ganhador por email, parabenizando-o pelo arremate e informando o valor final.

## Como Usar e Executar os Testes

### Pré-requisitos

*   Python 3.11 ou superior.
*   Pip (gerenciador de pacotes Python).

### Instalação de Dependências

As únicas dependências externas necessárias para executar os testes são `coverage` (para medir a cobertura dos testes) e `freezegun` (para controlar o tempo nos testes). Instale-as usando pip:

```bash
pip3 install coverage freezegun
```

### Executando os Testes Unitários

Para executar todos os testes unitários e verificar se todas as funcionalidades estão operando conforme esperado, navegue até o diretório raiz do projeto (`leilao_system/`) e execute o seguinte comando:

```bash
python3 -m unittest discover -s ./tests -p 'test_*.py'
```

Este comando descobrirá e executará todos os arquivos de teste (`test_*.py`) dentro do diretório `tests/`.

### Verificando a Cobertura dos Testes

Para executar os testes e gerar um relatório de cobertura, garantindo que 100% do código fonte no diretório `src/` foi exercitado pelos testes, use o `coverage`:

1.  **Execute os testes com coverage:**
    ```bash
    coverage run --source=src -m unittest discover -s ./tests -p 'test_*.py'
    ```
    Isso executará os testes e coletará dados de cobertura, salvando-os no arquivo `.coverage`.

2.  **Gere o relatório de cobertura no terminal:**
    ```bash
    coverage report -m
    ```
    Este comando exibirá um relatório resumido no terminal, mostrando a porcentagem de cobertura para cada arquivo em `src/` e as linhas que não foram cobertas (a coluna `Miss` deve estar vazia ou indicar linhas que são comentários/docstrings para cobertura de 100% das linhas executáveis).

3.  **(Opcional) Gere um relatório HTML detalhado:**
    ```bash
    coverage html
    ```
    Isso criará um diretório `htmlcov/` com um relatório HTML interativo, onde você pode navegar e ver exatamente quais linhas foram cobertas em cada arquivo.

### Relatório de Cobertura Atual

O relatório de cobertura gerado após a última execução dos testes (`coverage_report.txt`) confirma que 100% das linhas de código executáveis nos módulos `src/exceptions.py`, `src/models.py` e `src/sistema.py` foram cobertas pelos testes unitários.

```
Name                  Stmts   Miss  Cover   Missing
---------------------------------------------------
src/__init__.py           0      0   100%
src/exceptions.py         6      0   100%
src/models.py           128      0   100%
src/sistema.py          143      0   100%
---------------------------------------------------
TOTAL                   277      0   100%
```

## Limitações Conhecidas

*   **Persistência**: O sistema opera totalmente em memória. Todos os dados (leilões, participantes, lances) são perdidos quando a aplicação é encerrada.
*   **Interface**: Não há interface gráfica ou de linha de comando para interação direta do usuário. O uso se dá através da instanciação da classe `SistemaLeiloes` e chamada de seus métodos em um script Python.
*   **Notificação de Email**: A notificação do ganhador é apenas simulada através de uma saída no console (`print`). Nenhuma integração real com serviços de email foi implementada.
*   **Concorrência**: O sistema não foi projetado para lidar com acesso concorrente. Em um ambiente multiusuário, seria necessário implementar mecanismos de bloqueio ou usar um banco de dados que gerencie a concorrência.
*   **Validações**: As validações implementadas são básicas (ex: formato de CPF e email, unicidade). Validações mais complexas (ex: validação real de CPF, regras de data de nascimento) não estão presentes.

## Orientações para Integração com Banco de Dados (MySQL)

A próxima etapa natural para este sistema seria adicionar persistência de dados usando um banco de dados relacional como o MySQL. Aqui estão algumas orientações:

1.  **Escolha de ORM ou Conector**: Decida se usará um Object-Relational Mapper (ORM) como SQLAlchemy ou um conector de banco de dados direto como `mysql-connector-python`.
    *   **SQLAlchemy (Recomendado)**: Abstrai as queries SQL, facilita o mapeamento entre objetos Python e tabelas do banco de dados, e simplifica migrações de esquema. Exigiria a definição de modelos SQLAlchemy correspondentes às classes `Participante`, `Leilao`, `Lance` e o gerenciamento de sessões.
    *   **Conector Direto**: Requer escrita manual de queries SQL para todas as operações CRUD (Create, Read, Update, Delete). Pode ser mais simples para projetos pequenos, mas menos manutenível a longo prazo.

2.  **Adaptação da Classe `SistemaLeiloes`**: A classe `SistemaLeiloes` precisará ser refatorada significativamente. Ao invés de armazenar os dados em dicionários (`_participantes`, `_leiloes`), ela interagirá com o banco de dados:
    *   Métodos de cadastro (`cadastrar_participante`, `cadastrar_leilao`) criarão novos registros no banco.
    *   Métodos de busca (`buscar_participante_por_cpf`, `buscar_leilao_por_nome`) executarão queries `SELECT`.
    *   Métodos de alteração/exclusão (`alterar_leilao`, `excluir_participante`, `excluir_leilao`) executarão queries `UPDATE` ou `DELETE`.
    *   Métodos de listagem (`listar_leiloes`, `listar_lances_leilao`) executarão queries `SELECT` com filtros e ordenação apropriados.
    *   A lógica de `propor_lance_sistema` precisará buscar o participante e o leilão no banco, adicionar o lance (possivelmente em uma tabela separada de lances relacionada ao leilão) e salvar as alterações.

3.  **Adaptação das Classes de Modelo**: Se usar um ORM, as classes em `models.py` podem precisar ser redefinidas como modelos do ORM (ex: classes que herdam de `declarative_base()` no SQLAlchemy). Se usar um conector direto, as classes podem permanecer como estão, mas a lógica de carregar/salvar dados delas virá da classe `SistemaLeiloes`.

4.  **Gerenciamento de Conexão**: Implementar a lógica para conectar-se ao banco de dados MySQL, gerenciar conexões e transações.

5.  **Testes**: Os testes unitários precisarão ser adaptados. Pode ser necessário usar um banco de dados de teste em memória (como SQLite) ou mocks mais sofisticados para simular as interações com o banco de dados sem depender de uma instância real do MySQL durante os testes.

6.  **Migrações de Esquema**: Se usar SQLAlchemy, ferramentas como Alembic podem ser usadas para gerenciar as migrações do esquema do banco de dados conforme o modelo de dados evolui.

## Conclusão

O sistema de controle de leilões fornece uma base lógica sólida e bem testada para as funcionalidades solicitadas. A cobertura de 100% dos testes garante um alto nível de confiança na implementação das regras de negócio. Embora atualmente limitado pela falta de persistência e interface, o design modular facilita futuras expansões e integrações, como a conexão com um banco de dados MySQL.

