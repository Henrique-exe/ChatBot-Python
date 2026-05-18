import re
import time
import sys

# =========================
# Lista de intenções
# =========================

intencoes = [
    {
        "tag": "saudacao",
        "prioridade": 1,
        "palavras": [
            "oi", "ola", "olá", "bom dia", "boa tarde", "boa noite",
            "tudo bem", "como vai", "eae", "salve", "fala", "hey",
            "hi", "hello", "oie", "oii", "oioi", "olaa", "oláa"
        ],
        "resposta": "Olá! Seja bem-vindo à FashionFlow 👋 Como posso te ajudar hoje?"
    },

    {
        "tag": "reembolso",
        "prioridade": 2,
        "palavras": [
            "reembolso", "devolução", "devolucao", "estornar",
            "estorno", "reembolsos", "devoluções", "devolucoes",
            "estornos", "estornar pagamento", "estornar compra"
        ],
        "resposta": (
            "A devolução no Pix virá em até 24 horas após a confirmação "
            "do estorno, e no cartão de crédito em até 48 horas, "
            "dependendo do banco."
        )
    },

    {
        "tag": "bandeiras",
        "prioridade": 2,
        "palavras": [
            "bandeira", "cartão", "cartao", "visa",
            "master", "mastercard"
        ],
        "resposta": "Aceitamos pagamentos via Visa e Mastercard! 💳✨"
    },

    {
        "tag": "prazo_entrega",
        "prioridade": 3,
        "palavras": [
            "prazo", "entrega", "quando chega", "frete",
            "tempo de entrega", "prazo de entrega",
            "cep", "calcular prazo"
        ],
        "resposta": (
            "O prazo de entrega varia conforme sua região "
            "e o tipo de frete escolhido."
        ),
        "pergunta_seguinte": (
            "Deseja calcular o prazo exato informando seu CEP? (s/n)"
        )
    },

    {
        "tag": "desconto",
        "prioridade": 4,
        "palavras": [
            "cupom", "desconto", "voucher", "promoção",
            "promocao", "codigo promocional", "descontos",
            "cupons", "vouchers"
        ],
        "resposta": (
            "🌟 Promoção ativa: 5% de desconto em compras via Pix! 🌟"
        ),
        "pergunta_seguinte": (
            "Deseja gerar a chave Pix agora? (s/n)"
        )
    },

    {
        "tag": "forma_pagamento",
        "prioridade": 5,
        "palavras": [
            "formas de pagamento",
            "formas de pagamentos",
            "formas de pagamento disponíveis",
            "quais formas de pagamento aceitam"
        ],
        "resposta": (
            "Aceitamos:\n\n"
            "- Pix (5% de desconto)\n"
            "- Cartão de Crédito/Débito "
            "(Visa e Mastercard em até 12x sem juros)"
        )
    },

    {
        "tag": "pix",
        "prioridade": 6,
        "palavras": [
            "pix", "pagar no pix", "pagamento pix",
            "chave pix", "pagar com pix"
        ],
        "resposta": (
            "Temos pagamento via Pix com aprovação imediata "
            "e 5% de desconto!"
        ),
        "pergunta_seguinte": (
            "Deseja gerar a chave Pix para o pedido? (s/n)"
        )
    },

    {
        "tag": "credito",
        "prioridade": 6,
        "palavras": [
            "crédito", "credito",
            "cartão de crédito", "cartao de credito",
            "pagar no crédito"
        ],
        "resposta": (
            "Pagamento no crédito disponível em até 12x sem juros."
        ),
        "pergunta_seguinte": (
            "Qual a bandeira do cartão e quantidade de parcelas?\n"
            "(Ex: Visa, 3x)"
        )
    },

    {
        "tag": "boleto",
        "prioridade": 7,
        "palavras": [
            "boleto", "boleto bancario",
            "pagar boleto"
        ],
        "resposta": (
            "Infelizmente, não aceitamos boleto bancário.\n"
            "Você pode pagar via Pix ou Cartão."
        )
    },

    {
        "tag": "pagamento_misto",
        "prioridade": 8,
        "palavras": [
            "pagamento misto",
            "pix e cartão",
            "pix e credito",
            "cartão e pix juntos"
        ],
        "resposta": (
            "Atualmente, nosso sistema não suporta pagamento misto."
        )
    },

    {
        "tag": "exit",
        "prioridade": 999,
        "palavras": [
            "sair", "encerrar", "finalizar",
            "tchau", "até mais", "falou"
        ],
        "resposta": "Até mais! 👋",
        "encerrar": True
    }
]

# Ordena por prioridade
intencoes = sorted(
    intencoes,
    key=lambda x: x["prioridade"],
    reverse=True
)

# =========================
# Busca de resposta
# =========================

def buscar_resposta(mensagem):
    mensagem = mensagem.lower()

    for intencao in intencoes:
        for palavra in intencao["palavras"]:

            padrao = r'(?<!\w)' + re.escape(palavra.lower()) + r'(?!\w)'

            if re.search(padrao, mensagem):
                return intencao

    return {
        "resposta": (
            "Desculpe, não entendi. "
            "Pode tentar explicar de outra forma?"
        ),
        "encerrar": False
    }

# =========================
# Função de fala do bot
# =========================

def bot_falar(texto, efeito_digitacao=True):

    time.sleep(0.8)

    if efeito_digitacao:

        sys.stdout.write("Bot: ")
        sys.stdout.flush()

        for caractere in texto:
            sys.stdout.write(caractere)
            sys.stdout.flush()
            time.sleep(0.02)

        print()

    else:
        print(f"Bot: {texto}")

# =========================
# Inicialização
# =========================

print("--- Chatbot FashionFlow Iniciado ---")

contexto_pergunta = None
cep_armazenado = None

# =========================
# Loop principal
# =========================

while True:

    entrada = input("Você: ").strip()
    entrada_lower = entrada.lower()

    # =====================
    # CEP
    # =====================

    if contexto_pergunta == "aguardando_cep":

        cep_limpo = entrada.replace("-", "").replace(" ", "")

        if cep_limpo.isdigit() and len(cep_limpo) == 8:

            cep_armazenado = cep_limpo

            bot_falar(
                f"CEP {entrada} validado e armazenado com sucesso! 📍"
            )

            bot_falar(
                "O prazo estimado é de 3 a 7 dias úteis."
            )

            contexto_pergunta = None
            continue

        else:

            bot_falar(
                "❌ CEP inválido.\n"
                "Digite um CEP válido com 8 números."
            )

            continue

    # =====================
    # Crédito
    # =====================

    if contexto_pergunta == "credito":

        bot_falar(
            f"Perfeito! Registrei a opção: '{entrada}'."
        )

        bot_falar(
            "Redirecionando para o ambiente seguro de pagamento 💳"
        )

        contexto_pergunta = None
        continue

    # =====================
    # Respostas Sim/Não
    # =====================

    if (
        contexto_pergunta and
        entrada_lower in ["s", "sim", "n", "nao", "não"]
    ):

        if entrada_lower in ["s", "sim"]:

            if contexto_pergunta in ["pix", "desconto"]:

                bot_falar(
                    "Aqui está sua chave Pix fictícia 👇"
                )

                bot_falar(
                    "00020101021126580014br.gov.bcb.pix0136fashionflow"
                )

                bot_falar(
                    "Pagamento aprovado instantaneamente! 💸"
                )

            elif contexto_pergunta == "prazo_entrega":

                bot_falar(
                    "Digite seu CEP para calcular o prazo:"
                )

                contexto_pergunta = "aguardando_cep"
                continue

        else:

            bot_falar(
                "Entendido! Posso ajudar em algo mais?"
            )

        contexto_pergunta = None
        continue

    # =====================
    # Busca resposta
    # =====================

    resultado = buscar_resposta(entrada)

    bot_falar(resultado["resposta"])

    # =====================
    # Próxima pergunta
    # =====================

    if "pergunta_seguinte" in resultado:

        time.sleep(0.5)

        bot_falar(resultado["pergunta_seguinte"])

        contexto_pergunta = resultado["tag"]

    else:
        contexto_pergunta = None

    # =====================
    # Encerrar
    # =====================

    if resultado.get("encerrar"):
        break
