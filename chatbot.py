import re
import time
import sys
import csv
import unicodedata
from datetime import datetime

# ─────────────────────────────────────────────────────────────
#  CARREGAMENTO E VALIDAÇÃO DO CSV (Tratamento do Aviso 1)
# ─────────────────────────────────────────────────────────────


def carregar_intencoes(caminho_csv="base_conhecimento.csv"):
    intencoes = []
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            palavras_lista = [p.strip() for p in row["palavras"].split(",")]

            # Regex compiladas na carga utilizando a nova normalização robusta
            regex_compiladas = [
                re.compile(r'(?<!\w)' + re.escape(normalizar(p)) + r'(?!\w)')
                for p in palavras_lista if p
            ]

            intencao = {
                "tag":           row["tag"],
                "prioridade":    int(row["prioridade"]),
                "regex_palavras": regex_compiladas,
                "resposta":      row["resposta"],
            }
            if row["pergunta_seguinte"]:
                intencao["pergunta_seguinte"] = row["pergunta_seguinte"]
            if row["encerrar"] == "True":
                intencao["encerrar"] = True

            intencoes.append(intencao)

    # Ordena estritamente por prioridade: menor número (0) verificado primeiro
    return sorted(intencoes, key=lambda x: x["prioridade"])


# ─────────────────────────────────────────────────────────────
#  NORMALIZAÇÃO DE TEXTO ROBUSTA (Melhoria 3)
# ─────────────────────────────────────────────────────────────

def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    # Decompõe caracteres acentuados em seus equivalentes sem acento
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


# ─────────────────────────────────────────────────────────────
#  LOG DE ATENDIMENTO & SESSÃO
# ─────────────────────────────────────────────────────────────

LOG_FILE = "log_atendimento.txt"


def registrar_log(quem, mensagem):
    hora = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{hora}] {quem}: {mensagem}\n")


# ─────────────────────────────────────────────────────────────
#  EXIBIÇÃO E HISTÓRICO (Melhoria 1)
# ─────────────────────────────────────────────────────────────

def bot_falar(texto, efeito_digitacao=True):
    time.sleep(0.6)
    registrar_log("Bot", texto)

    # Armazena no histórico estruturado global da sessão
    historico_conversa.append({"quem": "bot", "msg": texto})

    # Alimenta o buffer dinâmico da função nativa de repetição
    historico_recente.append(texto)

    if efeito_digitacao:
        sys.stdout.write("Bot: ")
        sys.stdout.flush()
        for caractere in texto:
            sys.stdout.write(caractere)
            sys.stdout.flush()
            time.sleep(0.01)
        print()
    else:
        print(f"Bot: {texto}")


# ─────────────────────────────────────────────────────────────
#  MECANISMO DE BUSCA DE INTENÇÕES
# ─────────────────────────────────────────────────────────────

def buscar_resposta(mensagem):
    mensagem_norm = normalizar(mensagem)

    for intencao in intencoes:
        for padrao in intencao["regex_palavras"]:
            if padrao.search(mensagem_norm):
                return intencao

    return {
        "tag": "fallback",
        "resposta": "Desculpe, não consegui compreender a sua dúvida. Pode tentar explicar de outra forma?",
        "encerrar": False
    }


FALLBACK_RESPOSTA = "Desculpe, não consegui compreender a sua dúvida. Pode tentar explicar de outra forma?"
RESPOSTAS_SIM = ["s", "sim", "ss", "aham", "claro", "quero", "pode", "bora"]
RESPOSTAS_NAO = ["n", "nao", "não", "negativo", "deixa", "cancelar", "cancela"]
MENU_FINANCEIRO = {
    "1": "cobranca incorreta",
    "cobranca": "cobranca incorreta",
    "cobrança": "cobranca incorreta",
    "cobranca incorreta": "cobranca incorreta",
    "cobrança incorreta": "cobranca incorreta",
    "2": "pagamento nao reconhecido",
    "fraude": "pagamento nao reconhecido",
    "contestacao": "pagamento nao reconhecido",
    "contestação": "pagamento nao reconhecido",
    "3": "paguei e nao constou",
    "conciliacao": "paguei e nao constou",
    "conciliação": "paguei e nao constou",
    "4": "reembolso",
    "estorno": "reembolso",
    "5": "nota fiscal",
    "nf": "nota fiscal",
    "6": "formas de pagamento",
    "formas": "formas de pagamento",
    "7": "extrato financeiro",
    "extrato": "extrato financeiro",
    "historico": "extrato financeiro",
    "histórico": "extrato financeiro",
    "8": "status do pagamento",
    "status": "status do pagamento",
    "9": "negociar divida",
    "acordo": "negociar divida",
    "negociacao": "negociar divida",
    "negociação": "negociar divida",
}
TAGS_QUE_PODEM_INTERROMPER_CONTEXTO = {
    "seguranca_bloqueio",
    "contestacao_fraude",
    "cobranca_duplicada_valor_incorreto",
    "conciliacao_pagamento",
    "reembolso",
    "nota_fiscal",
    "recusado_cartao_credito",
    "recusado_cartao_debito",
    "recusado_pix",
    "forma_pagamento",
    "pix",
    "boleto",
    "pagamento_misto",
    "status_pagamento",
    "link_pagamento",
    "extrato_historico",
    "isencao_juros_multas",
    "negociacao_divida",
    "alterar_vencimento",
    "atualizar_metodo_pagamento",
    "dados_bancarios_empresa",
    "atendimento_humano",
}


def emitir_resultado(resultado):
    global contexto_pergunta

    bot_falar(resultado["resposta"])

    if resultado.get("pergunta_seguinte"):
        time.sleep(0.4)
        bot_falar(resultado["pergunta_seguinte"])
        contexto_pergunta = resultado["tag"]
    else:
        contexto_pergunta = None

    return not resultado.get("encerrar")


def parece_dado_credito(entrada_lower):
    tem_bandeira = any(b in entrada_lower for b in [
                       "visa", "master", "mastercard"])
    tem_parcela = re.search(
        r'(?<!\w)\d{1,2}\s*(x|vez|vezes|parcela|parcelas)(?!\w)',
        entrada_lower
    )
    return bool(tem_bandeira and tem_parcela)


def parece_dado_debito(entrada_lower):
    return any(b in entrada_lower for b in ["visa", "master", "mastercard"])


def entrada_muda_de_assunto(entrada, contexto_atual):
    resultado = buscar_resposta(entrada)
    tag = resultado.get("tag")
    if tag in TAGS_QUE_PODEM_INTERROMPER_CONTEXTO and tag != contexto_atual:
        return resultado
    return None


# ─────────────────────────────────────────────────────────────
#  PROCESSAMENTO DE CONTEXTOS (Correções dos Bugs 2, 4 e Melhoria 2)
# ─────────────────────────────────────────────────────────────

def processar_contexto(entrada, entrada_lower):
    global contexto_pergunta, tentativas_cep

    if entrada_lower in MENU_FINANCEIRO:
        emitir_resultado(buscar_resposta(MENU_FINANCEIRO[entrada_lower]))
        return True

    # ── CEP com limite de tentativas (Melhoria 2) ───────────
    if contexto_pergunta == "aguardando_cep":
        if entrada_lower in ["sair", "cancelar", "n", "nao", "não"]:
            bot_falar("Sem problemas! Cancelamos o cálculo do frete.")
            bot_falar("Posso ajudar com algum outro assunto financeiro?")
            contexto_pergunta = None
            tentativas_cep = 0
            return True

        cep_limpo = entrada.replace("-", "").replace(" ", "")
        if cep_limpo.isdigit() and len(cep_limpo) == 8:
            bot_falar(f"CEP {entrada} validado com sucesso! 📍")
            bot_falar(
                "O prazo estimado para a entrega na sua região é de 3 a 7 dias úteis.")
            bot_falar("Posso te ajudar com mais alguma coisa?")
            contexto_pergunta = None
            tentativas_cep = 0
        else:
            tentativas_cep += 1
            if tentativas_cep >= 3:
                bot_falar(
                    "Não consegui validar um formato de CEP válido após 3 tentativas.")
                bot_falar(
                    "Tudo bem! Vamos prosseguir. Como posso te ajudar agora?")
                contexto_pergunta = None
                tentativas_cep = 0
            else:
                bot_falar(
                    f"Formato inválido. Digite um CEP com 8 dígitos numéricos (Tentativa {tentativas_cep}/3):")
        return True

    # ── Validação robusta de Crédito (Correção do Bug 4) ────
    if contexto_pergunta == "credito":
        novo_assunto = entrada_muda_de_assunto(entrada, contexto_pergunta)
        if novo_assunto:
            emitir_resultado(novo_assunto)
            return True

        if not parece_dado_credito(entrada_lower):
            bot_falar(
                "Para seguir no crédito, informe bandeira e parcelas no mesmo texto (Ex: Visa, 3x). Se quiser mudar de assunto, diga Pix, boleto, reembolso ou cobrança.")
            return True
        bot_falar(f"Perfeito! Registrei a opção fornecida: '{entrada}'.")
        bot_falar(
            "Redirecionando para o ambiente de checkout seguro para digitação dos dados confidenciais... 💳")
        bot_falar("Posso te ajudar com mais alguma coisa?")
        contexto_pergunta = None
        return True

    # ── Validação robusta de Parcelas/Débito ─────────────────
    if contexto_pergunta in ["parcela", "debito"]:
        novo_assunto = entrada_muda_de_assunto(entrada, contexto_pergunta)
        if novo_assunto:
            emitir_resultado(novo_assunto)
            return True

        dado_valido = parece_dado_credito(
            entrada_lower) if contexto_pergunta == "parcela" else parece_dado_debito(entrada_lower)
        if not dado_valido:
            bot_falar(
                "Preciso de uma informação válida para continuar. Para débito, diga Visa ou Mastercard. Para parcelamento, diga bandeira e parcelas (Ex: Visa, 3x).")
            return True
        bot_falar(
            f"Registrado com sucesso: '{entrada}'. Redirecionando para o Gateway seguro.")
        contexto_pergunta = None
        return True

    # ── Validação de confirmações Sim/Não (Bug 2 corrigido) ──
    if contexto_pergunta and entrada_lower in RESPOSTAS_SIM + RESPOSTAS_NAO:
        respondeu_sim = entrada_lower in RESPOSTAS_SIM

        if respondeu_sim:
            # Bug 2: Agrupando estritamente quem segue o fluxo de dados Pix
            if contexto_pergunta in ["pix", "desconto"]:
                bot_falar(
                    "Aqui estão os dados para transferência rápida via Pix: 👇")
                bot_falar(
                    "Chave CNPJ: 12.345.678/0001-99 (FashionFlow Pagamentos Ltda)")
                bot_falar(
                    "A compensação ocorre instantaneamente de forma segura. Posso ajudar em algo mais?")
                contexto_pergunta = None

            elif contexto_pergunta in ["contestacao_fraude"]:
                bot_falar(
                    "Entendido. Estou gerando um token de prioridade financeira e transferindo você para o Setor de Segurança.")
                bot_falar(
                    "Um especialista humano assumirá a conversa em instantes... 🧑‍💻")
                contexto_pergunta = None

            elif contexto_pergunta == "reembolso":
                bot_falar(
                    "Certo! Para abrir a auditoria de devolução, acesse o link de autoatendimento:")
                bot_falar("financeiro.fashionflow.com/reembolsos")
                bot_falar("Posso te ajudar com mais alguma coisa?")
                contexto_pergunta = None

            elif contexto_pergunta == "cobranca_duplicada_valor_incorreto":
                bot_falar(
                    "Certo. Vou transferir seu caso para o Financeiro com prioridade de auditoria de cobrança.")
                bot_falar(
                    "Tenha em mãos pedido, data, valor cobrado e meio de pagamento. Um atendente humano assume em instantes.")
                contexto_pergunta = None

            elif contexto_pergunta in ["conciliacao_pagamento", "status_pagamento"]:
                bot_falar(
                    "Combinado. Vou direcionar para conciliação financeira para comparar o retorno do banco com o pedido.")
                bot_falar(
                    "Se tiver comprovante, informe apenas pelos canais seguros do atendimento humano.")
                contexto_pergunta = None

            elif contexto_pergunta == "isencao_juros_multas":
                bot_falar(
                    "Certo. Vou abrir uma solicitacao de analise para verificar se houve instabilidade do sistema no vencimento.")
                bot_falar(
                    "Guarde data da tentativa de pagamento, comprovante e mensagem de erro. O Financeiro avaliara a isencao de juros ou multa.")
                contexto_pergunta = None

            elif contexto_pergunta == "negociacao_divida":
                bot_falar(
                    "Combinado. Vou te direcionar para o setor de acordos e negociacao financeira.")
                bot_falar(
                    "Por seguranca, dados de CPF e valores detalhados devem ser tratados apenas no atendimento humano autenticado.")
                contexto_pergunta = None

            elif contexto_pergunta == "link_pagamento":
                bot_falar(
                    "Para gerar um novo pagamento, acesse Meus Pedidos, escolha o pedido pendente e selecione Pagar novamente.")
                bot_falar(
                    "Confira sempre se o endereço do checkout é oficial da FashionFlow antes de concluir.")
                contexto_pergunta = None

            elif contexto_pergunta == "dados_bancarios_empresa":
                resposta_pix = buscar_resposta("gerar novo pix")
                bot_falar(resposta_pix["resposta"])
                if resposta_pix.get("pergunta_seguinte"):
                    bot_falar(resposta_pix["pergunta_seguinte"])
                    contexto_pergunta = resposta_pix["tag"]
                else:
                    contexto_pergunta = None

            elif contexto_pergunta in ["recusado_cartao_credito", "recusado_cartao_debito", "recusado_pix"]:
                # Puxa dinamicamente a resposta de outra tag existente no CSV
                resposta_formas = buscar_resposta("formas de pagamento")
                bot_falar(resposta_formas["resposta"])
                contexto_pergunta = None

            elif contexto_pergunta in ["atendimento_humano", "ofensas"]:
                bot_falar("Conectando com o suporte humano agora mesmo... 👤")
                bot_falar("Por gentileza, aguarde um instante na linha.")
                contexto_pergunta = None
            else:
                bot_falar("Perfeito, como posso te ajudar?")
                contexto_pergunta = None
        else:
            bot_falar("Entendido. Operação cancelada. Como posso ser útil agora?")
            contexto_pergunta = None

        return True

    return False


# ─────────────────────────────────────────────────────────────
#  PROCESSAMENTO DE INTENÇÕES (Correção do Bug 1 e Melhoria 4)
# ─────────────────────────────────────────────────────────────

def processar_intencao(entrada):
    global contexto_pergunta, sem_entender

    resultado = buscar_resposta(entrada)
    continuar = emitir_resultado(resultado)

    # Melhoria 4: Monitoria de loops de incompreensão do usuário
    if resultado.get("tag") != "fallback":
        sem_entender = 0
    else:
        sem_entender += 1
        if sem_entender >= 3:
            bot_falar(
                "Percebi que não estou conseguindo te fornecer a resposta exata de forma automática.")
            bot_falar(
                "Gostaria que eu realizasse o transbordo para um atendente humano analisar o seu caso? (s/n)")
            contexto_pergunta = "atendimento_humano"
            sem_entender = 0

    return continuar


# ─────────────────────────────────────────────────────────────
#  INICIALIZAÇÃO DO SISTEMA (Aviso 1 Tratado)
# ─────────────────────────────────────────────────────────────

try:
    intencoes = carregar_intencoes("base_conhecimento.csv")
except FileNotFoundError:
    print("\n❌ ERRO CRÍTICO: O arquivo de dados 'base_conhecimento.csv' não foi localizado.")
    print("Por favor, execute o script 'gerar_csv.py' primeiro para criar a base de conhecimento.\n")
    sys.exit(1)

# Estados globais
contexto_pergunta = None
tentativas_cep = 0
sem_entender = 0

# Estruturas de Memória e Repetição Nativa
historico_conversa = []  # Lista de dicionários contendo o histórico de toda a sessão
memoria_repeticao = []  # Armazena as respostas do turno anterior para comandos "repete"
historico_recente = []  # Coleta as respostas enviadas no turno ativo

registrar_log(
    "Sistema", f"=== Nova sessão iniciada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ===")

print("--- Chatbot Financeiro FashionFlow Iniciado ---")
print(f"✅ {len(intencoes)} intenções de gírias e transações mapeadas do CSV.\n")

# ─────────────────────────────────────────────────────────────
#  LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────

while True:
    try:
        entrada = input("Você: ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        bot_falar("Atendimento finalizado preventivamente. Até logo! 👋")
        break

    if not entrada:
        continue

    entrada_lower = normalizar(entrada)
    registrar_log("Você", entrada)

    # Registra a entrada do usuário no histórico estruturado
    historico_conversa.append({"quem": "usuario", "msg": entrada})

    # Interceptador dinâmico de gírias para comandos de repetição instantânea
    if entrada_lower in ["repete", "manda de novo", "fala de novo", "repete ai", "manda de novo ai"]:
        mensagens_para_repetir = historico_recente or memoria_repeticao
        if mensagens_para_repetir:
            for msg in mensagens_para_repetir:
                time.sleep(0.4)
                print(f"Bot (Repetindo): {msg}")
        else:
            print(
                "Bot: Ainda não há mensagens registradas no histórico recente para que eu possa repetir.")
        continue

    # Transfere as mensagens emitidas no último turno para a memória estática de repetição
    memoria_repeticao = list(historico_recente)
    historico_recente.clear()

    # 1. Avalia se o usuário está respondendo dentro de um fluxo de contexto ativo
    if processar_contexto(entrada, entrada_lower):
        continue

    # 2. Executa a busca regular por palavras-chave mapeadas no CSV
    continuar = processar_intencao(entrada)
    if not continuar:
        break

registrar_log("Sistema", "=== Sessão encerrada de forma limpa ===\n")
