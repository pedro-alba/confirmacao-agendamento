import pdfplumber
import re
from datetime import datetime, timedelta
from collections import defaultdict

def extrair_dados_pdf(caminho_pdf):
    clientes = []
    
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            # Divide o texto por linhas
            linhas = texto.split('\n')
            
            # Combina linhas que podem estar quebradas entre páginas
            linhas_combinadas = []
            for i in range(len(linhas)):
                if re.match(r'\d{2}:\d{2}', linhas[i]) and i + 1 < len(linhas):
                    # Se a próxima linha não começa com uma data, significa que é parte do mesmo agendamento
                    if not re.match(r'\d{2}/\d{2}/\d{4}', linhas[i + 1]):
                        linhas_combinadas.append(linhas[i] + ' ' + linhas[i + 1])
                        continue
                linhas_combinadas.append(linhas[i])

            # Extrai informações de cada agendamento
            for i in range(len(linhas_combinadas)):
                # Verifica se a linha contém um horário
                if re.match(r'\d{2}:\d{2}', linhas_combinadas[i]):
                    # Extraindo horário e nome do cliente
                    horario_e_cliente = linhas_combinadas[i].split(maxsplit=1)  # Divide em horário e resto da linha
                    horario = horario_e_cliente[0]
                    nome_cliente = horario_e_cliente[1].strip() if len(horario_e_cliente) > 1 else "Nome não encontrado"

                    # Informações do animal
                    info_animal = linhas_combinadas[i + 1].strip() if i + 1 < len(linhas_combinadas) else "Informações do animal não encontradas"
                    
                    # Extraindo nome do animal
                    match = re.search(r'(\w+)\s*-\s*.*', info_animal)
                    nome_animal = match.group(1).strip() if match else "Nome do animal não encontrado"
                    nome_animal = re.sub(r'[0-9/]', '', nome_animal)
                    
                    # Tipo de atendimento
                    tipo_atendimento = None
                    for linha in linhas_combinadas[i + 2:i + 7]:  # Procura nas próximas linhas
                        if "Tipo de atendimento:" in linha:
                            tipo_atendimento = linha.split(":")[-1].strip().lower()  # Armazenar como "banho"
                            break
                    
                    # Se tipo_atendimento não for encontrado, define um valor padrão
                    if tipo_atendimento is None:
                        tipo_atendimento = "desconhecido"

                    # Observações
                    observacoes = None
                    for linha in linhas_combinadas[i + 2:i + 7]:  # Procura nas próximas linhas
                        if "Observações:" in linha:
                            observacoes = linha.split(":")[-1].strip()
                            break
                    
                    # Busca o telefone no texto
                    telefone = re.search(r'\(\d{2}\) \d{4,5}-\d{4}', texto)
                    telefone = telefone.group(0) if telefone else "Telefone não encontrado"
                    
                    # Adiciona as informações extraídas à lista de clientes
                    clientes.append({
                        "nome_cliente": nome_cliente,
                        "nome_animal": nome_animal,
                        "horario": horario,
                        "tipo_atendimento": tipo_atendimento,
                        "observacoes": observacoes if observacoes else "Sem observações",
                        "telefone": telefone
                    })
    return clientes

def gerar_mensagens(clientes):
    mensagens = defaultdict(list)
    
    # Definindo a data para o dia seguinte
    dia_seguinte = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    
    for cliente in clientes:
        # Verifica se há horário nas observações
        if cliente['observacoes'] and "VEM" in cliente['observacoes']:
            match_horario = re.search(r'VEM (\d{2}:\d{2})', cliente['observacoes'])
            if match_horario:
                cliente['horario'] = match_horario.group(1)  # Substitui o horário

        # Adiciona a informação na mensagem para o cliente
        mensagens[cliente["nome_cliente"]].append((cliente["nome_animal"].capitalize(), cliente["tipo_atendimento"], cliente["horario"]))

    # Gerando mensagens únicas por cliente
    for nome_cliente, agendamentos in mensagens.items():
        # Construindo a mensagem
        if len(agendamentos) == 1:
            animal, tipo_atendimento, horario = agendamentos[0]
            mensagem = f"""
            Boa tarde, {nome_cliente.split()[0].capitalize()}, tudo bem? 👋
            Podemos confirmar seu agendamento de amanhã?
            - {animal}: {tipo_atendimento.capitalize()} - {horario}
            """
        else:
            animals_info = '\n'.join([f"- {animal}: {tipo.capitalize()} - {horario}" for animal, tipo, horario in agendamentos])
            mensagem = f"""
            Boa tarde, {nome_cliente.split()[0].capitalize()}, tudo bem? 👋
            Podemos confirmar seus agendamentos de amanhã?
            {animals_info}
            """
        
        print(mensagem)
        print("-" * 50)

# Nome do arquivo PDF (deve estar na mesma pasta que o script)
caminho_pdf = "doc.pdf"

# Extrai os dados do PDF
clientes = extrair_dados_pdf(caminho_pdf)

# Gerando mensagens para cada cliente
gerar_mensagens(clientes)

# Contando e imprimindo o número de mensagens enviadas
contador_mensagens = len(set(cliente["nome_cliente"] for cliente in clientes))  # Contar clientes únicos
print(f"Número de mensagens enviadas: {contador_mensagens}")
