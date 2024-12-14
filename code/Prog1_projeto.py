from constantes import *


def ler_config(S):
    """
    Lê o ficheiro de configuração e devolve um dicionário com os parâmetros.
    
    Args:
        S (int): Código da simulação.
    
    Returns:
        dict: Dicionário com os parâmetros da configuração.
    """
    config_file = f"config_{S}.txt"
    parametros = {}

    try:
        with open(config_file, "r") as file:
            for linha in file:
                linha = linha.strip()
                if linha and not linha.startswith("#"):
                    chave, valor = linha.split("=", 1)
                    chave = chave.strip()
                    valor = valor.strip()

                    # Avaliar expressões numéricas, mas não funções ou strings específicas
                    if chave not in ["ACTIVO", "PENSIONISTA"]:
                        try:
                            parametros[chave] = eval(valor)
                        except Exception:
                            parametros[chave] = valor
                    else:
                        parametros[chave] = valor

    except FileNotFoundError:
        print(f"Erro: O ficheiro '{config_file}' não foi encontrado.")
    except Exception as e:
        print(f"Erro ao ler o ficheiro de configuração: {e}")

    return parametros




def nova_pessoa(idade=0):
    """
    Cria uma nova pessoa com os campos necessários.

    Args:
        idade (int): Idade da pessoa (padrão = 0).
    
    Returns:
        dict: Dicionário com os campos da pessoa.
    """
    global CC, SALARIO_BASE, PENSAO_BASE
    
    # Criar o dicionário da pessoa
    pessoa = {
        "cc": CC,
        "nome": f"Pessoa_{CC}",
        "genero": "M" if CC % 2 == 0 else "F",
        "idade": idade,
        "salario": SALARIO_BASE,
        "pensao": PENSAO_BASE
    }

    # Incrementa CC para unicidade
    CC += 1
    return pessoa



def ler_populacao_inicial(S):
    """
    Lê um ficheiro de população inicial e devolve uma lista de pessoas.

    Args:
        S (int): Código da simulação (usado para identificar o ficheiro).
    
    Returns:
        list: Lista de pessoas criadas pela função `nova_pessoa`.
    """
    nome_ficheiro = f"populacao_inicial_{S}.txt"
    populacao = []

    # Abrir e processar o ficheiro corretamente
    with open(nome_ficheiro, "r") as file:
        for linha in file:
            # Divide a linha por vírgulas
            campos = linha.strip().split(",")

            # Garantir que a linha tem pelo menos dois campos
            if len(campos) >= 2 and campos[3].strip().isdigit():
                idade = int(campos[3].strip())  # Extrai a idade correta
                populacao.append(nova_pessoa(idade))

    return populacao


def simula_ano(populacao, ano_corrente):
    """
    Simula a passagem de um ano em termos demográficos.

    Args:
        populacao (list): Lista de pessoas representadas como dicionários.
        ano_corrente (int): Ano atual da simulação.

    Returns:
        list: População atualizada após um ano.
    """
    nova_populacao = []

    # 1. Atualizar idades antes de aplicar mortalidade
    for pessoa in populacao:
        pessoa["idade"] += 1

    # 2. Aplicar mortalidade faixa por faixa
    for faixa_etaria, (intervalo, taxa) in MORTALIDADE.items():
        grupo = [p for p in populacao if p["idade"] in intervalo]
        sobreviventes = exclude_entities(grupo, taxa, ano_corrente)
        nova_populacao.extend(sobreviventes)

    # 3. Calcular nascimentos após remover mortos
    num_nascimentos = len(nova_populacao) // NATALIDADE

    # 4. Adicionar nascimentos somente se houver pelo menos 1
    if num_nascimentos > 0:
        nascimentos = [nova_pessoa(idade=0) for _ in range(num_nascimentos)]
        nova_populacao.extend(nascimentos)

    return nova_populacao


def cobra_seg_social(ano, fundo_pensoes, populacao):
    """
    Calcula as contribuições e pagamentos da segurança social.

    Args:
        ano (int): O ano corrente.
        fundo_pensoes (float): O valor atual do fundo de pensões.
        populacao (list): Lista de pessoas representadas como dicionários.

    Returns:
        float: O valor atualizado do fundo de pensões.
    """
    # Definir variáveis locais baseadas no enunciado
    DESCONTOS = 0.23
    IDADE_REFORMA = 67
    ACTIVO = range(23, IDADE_REFORMA + 1)
    PENSIONISTA = range(IDADE_REFORMA + 1, 102)

    total_contribuicoes = 0
    total_pagamentos = 0

    # Calcular contribuições e pagamentos
    for pessoa in populacao:
        idade = pessoa["idade"]
        salario = pessoa["salario"]
        pensao = pessoa["pensao"]

        if idade in ACTIVO:
            total_contribuicoes += DESCONTOS * salario
        elif idade in PENSIONISTA:
            total_pagamentos += pensao

    # Atualizar fundo de pensões
    fundo_pensoes += total_contribuicoes
    fundo_pensoes -= total_pagamentos

    return fundo_pensoes


### Não há randoms, para facilitar a correcção automática no coderunner
### oferecemos este "filtro" que recebe 
### uma lista com pessoas e devolvemos uma nova lista com os
### sobreviventes de acordo com o ano dado e a percentagem
### de sobreviventes dada

### Não alterem este código

def exclude_entities(entities, p, year):
    """
    Exclude a percentage p of entities deterministically based on the year.

    Parameters:
        entities (list of dict): List of entities.
        p (float): The percentage of entities to exclude (0 <= p <= 1).
        year (int): The year used for deterministic variation.

    Returns:
        list of dict: List of entities that are not excluded.
    """
    num_to_exclude = int(len(entities) * p)
    
    # Calculate a score for each entity based on its index and the year
    entities_sorted = sorted(
        enumerate(entities),
        key=lambda e: (e[0] + year) % 100  # e[0] is the index
    )

    # Exclude the first num_to_exclude entities based on the sorted order
    included_entities = [entity for i, entity in entities_sorted[num_to_exclude:]]
    return included_entities

def simula_epocas(codigo_simulacao):
    # 1. Ler configurações e população inicial
    parametros = ler_config(codigo_simulacao)
    populacao = ler_populacao_inicial(codigo_simulacao)
    fundo_pensoes = parametros["FUNDO_PENSOES_INICIAL"]
    ano_corrente = parametros["ANO_INICIAL"]
    epocas = parametros["EPOCAS"]

    # 2. Mensagem Inicial
    print(f"A simulação começou no ano {ano_corrente}, com população total de {len(populacao)}, e o fundo de pensões a valer {fundo_pensoes}.")

    # 3. Simulação de cada ano
    for _ in range(epocas):
        populacao = simula_ano(populacao, ano_corrente)
        fundo_pensoes = cobra_seg_social(ano_corrente, fundo_pensoes, populacao)

        # Mensagem se o fundo for negativo
        if fundo_pensoes < 0:
            print(f"No ano {ano_corrente}, a população foi {len(populacao)} e o fundo de pensões foi negativo, com valor {fundo_pensoes:.1f}.")
        
        # Avançar para o próximo ano
        ano_corrente += 1

    # 4. Mensagem Final
    print(f"A simulação terminou no ano {ano_corrente - 1}, com população total de {len(populacao)} pessoas e o fundo de pensões vale {fundo_pensoes:.1f}.")

    # 5. Criar o ficheiro de população final
    nome_ficheiro = f"populacao_final_{codigo_simulacao}.txt"
    with open(nome_ficheiro, "w") as f:
        for pessoa in populacao:
            f.write(f"{pessoa['cc']}, {pessoa['nome']}, {pessoa['genero']}, {pessoa['idade']}, {pessoa['salario']}, {pessoa['pensao']}\n")





