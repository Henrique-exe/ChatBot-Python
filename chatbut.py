import re
import time
import sys

# ============================================================
#  CONFIGURAÇÕES VISUAIS DO TERMINAL
# ============================================================

class Cor:
    RESET      = "\033[0m"
    NEGRITO    = "\033[1m"
    CINZA      = "\033[90m"
    BRANCO     = "\033[97m"
    AZUL       = "\033[94m"
    VERDE      = "\033[92m"
    AMARELO    = "\033[93m"
    CIANO      = "\033[96m"
    VERMELHO   = "\033[91m"
    BG_AZUL    = "\033[44m"
    BG_ESCURO  = "\033[40m"


def digitar(texto, delay=0.018):
    """Efeito de digitação letra a letra."""
    for c in texto:
        print(c, end='', flush=True)
        time.sleep(delay)
    print()


def linha(char="─", tamanho=55, cor=Cor.CINZA):
    print(cor + char * tamanho + Cor.RESET)


def cabecalho():
    print()
    linha("═", 55, Cor.AZUL)
    print(Cor.AZUL + Cor.NEGRITO +
          "  💳  FashionFlow — Atendimento Financeiro" +
          Cor.RESET)
    linha("═", 55, Cor.AZUL)
    print()


def fala_bot(texto):
    """Exibe mensagem do bot com efeito de digitação."""
    prefixo = Cor.CIANO + Cor.NEGRITO + "  Bot › " + Cor.RESET
    print(prefixo, end='')
    digitar(texto)


def fala_sistema(texto):
    """Mensagem de sistema/informação."""
    print(Cor.AMARELO + "  ⚡ " + texto + Cor.RESET)


def fala_erro(texto):
    print(Cor.VERMELHO + "  ✖ " + texto + Cor.RESET)


def exibir_opcoes(opcoes):
    """Exibe opções numeradas para o usuário escolher."""
    print()
    linha("·", 55, Cor.CINZA)
    print(Cor.CINZA + "  Atalhos rápidos:" + Cor.RESET)
    for i, op in enumerate(opcoes, 1):
        print(f"  {Cor.AZUL}[{i}]{Cor.RESET} {op}")
    linha("·", 55, Cor.CINZA)
    print()


def aguardar_confirmacao(pergunta):
    """Pergunta s/n e retorna True se sim."""
    while True:
        resp = input(
            f"  {Cor.AMARELO}? {pergunta} (s/n): {Cor.RESET}"
        ).strip().lower()
        if resp in ('s', 'sim', 'yes', 'y'):
            return True
        if resp in ('n', 'nao', 'não', 'no'):
            return False
        print(Cor.VERMELHO + "  Digite s para sim ou n para não." + Cor.RESET)


def input_usuario():
    """Lê entrada do usuário com prompt estilizado."""
    return input(
        Cor.VERDE + Cor.NEGRITO + "\n  Você › " + Cor.RESET
    ).strip()


# ============================================================
#  FLUXOS DE PAGAMENTO (terminam em algum lugar)
# ============================================================

def fluxo_pix():
    """Fluxo completo de pagamento via Pix."""
    linha()
    print()
    fala_bot("Perfeito! Vou gerar os dados para pagamento via Pix.")
    time.sleep(0.5)

    print()
    linha("─", 55, Cor.VERDE)
    print(Cor.VERDE + Cor.NEGRITO + "  ✅ DADOS PARA PAGAMENTO VIA PIX" + Cor.RESET)
    linha("─", 55, Cor.VERDE)
    print(f"  {'Chave Pix:':<20} {Cor.BRANCO}fashionflow@pagamentos.com.br{Cor.RESET}")
    print(f"  {'Tipo:':<20} E-mail")
    print(f"  {'Favorecido:':<20} FashionFlow Ltda")
    print(f"  {'CNPJ:':<20} 00.000.000/0001-00")
    print(f"  {'Aprovação:':<20} {Cor.VERDE}Imediata{Cor.RESET}")
    linha("─", 55, Cor.VERDE)
    print()

    fala_sistema("Copie a chave acima e realize o pagamento no app do seu banco.")
    print()

    if aguardar_confirmacao("Já realizou o pagamento?"):
        print()
        fala_bot("Ótimo! Assim que identificarmos o pagamento, seu pedido será confirmado.")
        fala_sistema("Prazo de confirmação: até 5 minutos após o pagamento.")
        fala_sistema("Você receberá um e-mail de confirmação.")
        print()
        fala_bot("Posso te ajudar com mais alguma coisa?")
        return True
    else:
        print()
        fala_bot("Tudo bem! A chave fica disponível quando você precisar.")
        fala_bot("Se tiver dificuldades, entre em contato pelo e-mail suporte@fashionflow.com.br")
        return False


def fluxo_credito():
    """Fluxo de pagamento no crédito com escolha de parcelas."""
    linha()
    print()
    fala_bot("Ótima escolha! Vamos configurar seu pagamento no crédito.")
    time.sleep(0.4)

    print()
    linha("─", 55, Cor.AZUL)
    print(Cor.AZUL + Cor.NEGRITO + "  💳 TABELA DE PARCELAMENTO" + Cor.RESET)
    linha("─", 55, Cor.AZUL)

    parcelas = [
        (1,  "Sem juros",          "valor total"),
        (2,  "Sem juros",          "em 2x"),
        (3,  "Sem juros",          "em 3x"),
        (6,  "Sem juros",          "em 6x"),
        (9,  "0,99% ao mês",       "em 9x"),
        (12, "Sem juros*",         "em 12x (cartão parceiro)"),
    ]

    for n, juros, desc in parcelas:
        cor_juros = Cor.VERDE if "Sem juros" in juros else Cor.AMARELO
        print(f"  {Cor.NEGRITO}{n:>2}x{Cor.RESET}  {cor_juros}{juros:<18}{Cor.RESET}  {Cor.CINZA}{desc}{Cor.RESET}")

    linha("─", 55, Cor.AZUL)
    print(Cor.CINZA + "  * Consulte as bandeiras parceiras." + Cor.RESET)
    print()

    while True:
        try:
            escolha = input(
                f"  {Cor.AMARELO}? Em quantas parcelas deseja pagar? (1/2/3/6/9/12): {Cor.RESET}"
            ).strip()
            qtd = int(escolha)
            if qtd in [1, 2, 3, 6, 9, 12]:
                break
            print(Cor.VERMELHO + "  Escolha uma das opções listadas." + Cor.RESET)
        except ValueError:
            print(Cor.VERMELHO + "  Digite apenas o número de parcelas." + Cor.RESET)

    print()
    fala_bot(f"Perfeito! Pagamento em {qtd}x selecionado.")
    fala_sistema("Redirecionando para o checkout seguro...")
    time.sleep(0.8)

    print()
    linha("─", 55, Cor.AZUL)
    print(Cor.AZUL + Cor.NEGRITO + "  🔒 CHECKOUT SEGURO" + Cor.RESET)
    linha("─", 55, Cor.AZUL)
    print(f"  {'Link:':<12} {Cor.CIANO}https://checkout.fashionflow.com.br/credito{Cor.RESET}")
    print(f"  {'Parcelas:':<12} {qtd}x")
    print(f"  {'Sessão:':<12} {Cor.AMARELO}Expira em 15 minutos{Cor.RESET}")
    print(f"  {'Bandeiras:':<12} Visa · Master · Elo · Amex · Hipercard")
    linha("─", 55, Cor.AZUL)
    print()

    fala_sistema("Acesse o link acima no navegador para concluir o pagamento.")
    print()
    fala_bot("Posso te ajudar com mais alguma coisa?")
    return True


def fluxo_debito():
    """Fluxo de pagamento no débito."""
    linha()
    print()
    fala_bot("Vou verificar as opções de débito disponíveis para você.")
    time.sleep(0.4)

    print()
    linha("─", 55, Cor.CIANO)
    print(Cor.CIANO + Cor.NEGRITO + "  💳 PAGAMENTO NO DÉBITO" + Cor.RESET)
    linha("─", 55, Cor.CIANO)
    print(f"  {'Bandeiras aceitas:'}")
    bandeiras = ["Visa Electron", "Maestro", "Elo Débito"]
    for b in bandeiras:
        print(f"    {Cor.VERDE}✓{Cor.RESET} {b}")
    print()
    print(f"  {'Link:':<12} {Cor.CIANO}https://checkout.fashionflow.com.br/debito{Cor.RESET}")
    print(f"  {'Sessão:':<12} {Cor.AMARELO}Expira em 15 minutos{Cor.RESET}")
    linha("─", 55, Cor.CIANO)
    print()

    fala_sistema("Acesse o link acima no navegador para concluir o pagamento.")

    if aguardar_confirmacao("Seu cartão é de uma das bandeiras listadas?"):
        print()
        fala_bot("Ótimo! Basta acessar o link e inserir os dados do seu cartão.")
        fala_bot("O débito é processado na hora, sem aprovação posterior.")
    else:
        print()
        fala_bot("Sem problemas! Temos outras formas de pagamento disponíveis.")
        fala_bot("Quer tentar pagar com Pix ou crédito?")

    print()
    fala_bot("Posso te ajudar com mais alguma coisa?")
    return True


def fluxo_misto():
    """Pagamento combinado Pix + crédito."""
    linha()
    print()
    fala_bot("Você pode dividir o pagamento entre Pix e cartão de crédito!")
    time.sleep(0.4)

    print()
    linha("─", 55, Cor.AMARELO)
    print(Cor.AMARELO + Cor.NEGRITO + "  ⚡ PAGAMENTO MISTO — PIX + CRÉDITO" + Cor.RESET)
    linha("─", 55, Cor.AMARELO)
    print("  Como funciona:")
    print(f"   {Cor.VERDE}1.{Cor.RESET} Escolha o valor que quer pagar via Pix")
    print(f"   {Cor.VERDE}2.{Cor.RESET} O restante vai automaticamente para o crédito")
    print(f"   {Cor.VERDE}3.{Cor.RESET} Finalize no checkout em uma só tela")
    print()
    print(f"  {'Link:':<12} {Cor.CIANO}https://checkout.fashionflow.com.br/misto{Cor.RESET}")
    linha("─", 55, Cor.AMARELO)
    print()

    fala_sistema("Acesse o link para configurar os valores e finalizar.")
    print()
    fala_bot("Posso te ajudar com mais alguma coisa?")
    return True


def fluxo_reembolso():
    """Fluxo de solicitação de reembolso."""
    linha()
    print()
    fala_bot("Vou te ajudar com o reembolso. Preciso de alguns dados.")
    time.sleep(0.4)

    print()
    numero = input(
        f"  {Cor.AMARELO}? Número do pedido: {Cor.RESET}"
    ).strip()

    email = input(
        f"  {Cor.AMARELO}? E-mail cadastrado: {Cor.RESET}"
    ).strip()

    motivo_opcoes = {
        '1': 'Produto com defeito',
        '2': 'Produto errado / diferente do pedido',
        '3': 'Arrependimento de compra',
        '4': 'Cobrado duas vezes',
        '5': 'Outro'
    }
    print()
    print("  Motivo do reembolso:")
    for k, v in motivo_opcoes.items():
        print(f"   {Cor.AZUL}[{k}]{Cor.RESET} {v}")

    while True:
        mot = input(
            f"\n  {Cor.AMARELO}? Escolha o motivo (1-5): {Cor.RESET}"
        ).strip()
        if mot in motivo_opcoes:
            break
        print(Cor.VERMELHO + "  Digite um número entre 1 e 5." + Cor.RESET)

    print()
    fala_sistema("Processando sua solicitação...")
    time.sleep(1.0)

    # Gera número de protocolo fictício
    import random
    protocolo = f"FF-{random.randint(100000, 999999)}"

    print()
    linha("─", 55, Cor.VERDE)
    print(Cor.VERDE + Cor.NEGRITO + "  ✅ SOLICITAÇÃO REGISTRADA" + Cor.RESET)
    linha("─", 55, Cor.VERDE)
    print(f"  {'Protocolo:':<16} {Cor.NEGRITO}{protocolo}{Cor.RESET}")
    print(f"  {'Pedido:':<16} {numero}")
    print(f"  {'E-mail:':<16} {email}")
    print(f"  {'Motivo:':<16} {motivo_opcoes[mot]}")
    print(f"  {'Prazo Pix:':<16} {Cor.VERDE}até 24h{Cor.RESET}")
    print(f"  {'Prazo Cartão:':<16} {Cor.AMARELO}até 48h úteis{Cor.RESET}")
    linha("─", 55, Cor.VERDE)
    print()

    fala_bot(f"Solicitação registrada com protocolo {protocolo}.")
    fala_sistema("Você receberá uma confirmação no e-mail informado.")
    print()
    fala_bot("Posso te ajudar com mais alguma coisa?")
    return True


def fluxo_parcelas():
    """Exibe tabela de parcelamento sem fluxo de pagamento."""
    linha()
    print()
    fala_bot("Veja as condições de parcelamento disponíveis:")
    print()
    linha("─", 55, Cor.AZUL)
    print(Cor.AZUL + Cor.NEGRITO + "  💳 PARCELAMENTO — CARTÃO DE CRÉDITO" + Cor.RESET)
    linha("─", 55, Cor.AZUL)

    parcelas = [
        (1,  "Sem juros"),
        (2,  "Sem juros"),
        (3,  "Sem juros"),
        (6,  "Sem juros"),
        (9,  "0,99% ao mês"),
        (12, "Sem juros (cartão parceiro)"),
    ]
    for n, juros in parcelas:
        cor = Cor.VERDE if "Sem juros" in juros else Cor.AMARELO
        print(f"  {Cor.NEGRITO}{n:>2}x{Cor.RESET}  {cor}{juros}{Cor.RESET}")

    linha("─", 55, Cor.AZUL)
    print()

    if aguardar_confirmacao("Deseja prosseguir com o pagamento no crédito?"):
        return fluxo_credito()
    return False


# ============================================================
#  INTENÇÕES
# ============================================================

intencoes = [
    {
        "tag": "saudacao",
        "palavras": ["oi", "ola", "olá", "bom dia", "boa tarde", "boa noite",
                     "tudo bem", "como vai", "e ai", "hey", "hello", "hi",
                     "salve", "oie", "fala", "opa"],
        "resposta": "Olá! Seja bem-vindo ao atendimento financeiro da FashionFlow 👋",
        "opcoes": ["Formas de pagamento", "Pagar com Pix", "Pagar no crédito",
                   "Pagar no débito", "Parcelamento", "Reembolso",
                   "Pix + Crédito (misto)", "Encerrar atendimento"]
    },
    {
        "tag": "formas_pagamento",
        "palavras": ["formas de pagamento", "como pagar", "aceita cartão", "aceita pix",
                     "métodos de pagamento", "formas de pagar", "quais pagamentos",
                     "métodos", "meios de pagamento"],
        "resposta": "Aceitamos: Pix (imediato), cartão de crédito (até 12x sem juros), débito e pagamento misto Pix + crédito.",
        "opcoes": ["Pagar com Pix", "Pagar no crédito", "Pagar no débito",
                   "Pix + Crédito (misto)", "Encerrar atendimento"]
    },
    {
        "tag": "pix",
        "palavras": ["pix", "pagar com pix", "pagar no pix", "chave pix",
                     "qr code", "pagamento pix", "quero pagar com pix"],
        "fluxo": fluxo_pix
    },
    {
        "tag": "credito",
        "palavras": ["crédito", "credito", "cartão de crédito", "pagar no crédito",
                     "pagar com crédito", "cartao de credito", "pagamento crédito",
                     "cartão crédito"],
        "fluxo": fluxo_credito
    },
    {
        "tag": "debito",
        "palavras": ["débito", "debito", "cartão de débito", "pagar no débito",
                     "pagar com débito", "debito em conta", "débito em conta",
                     "cartão débito", "cartao de debito"],
        "fluxo": fluxo_debito
    },
    {
        "tag": "parcelamento",
        "palavras": ["parcelar", "parcelas", "parcelamento", "sem juros", "dividir",
                     "quantas parcelas", "posso parcelar", "12x", "6x", "3x",
                     "quero parcelar", "parcelado"],
        "fluxo": fluxo_parcelas
    },
    {
        "tag": "pagamento_misto",
        "palavras": ["pagamento misto", "pix e crédito", "dividir pagamento",
                     "metade pix", "pix e credito", "dois cartões", "cartão e pix",
                     "misto", "pix mais crédito", "pix + crédito"],
        "fluxo": fluxo_misto
    },
    {
        "tag": "reembolso",
        "palavras": ["reembolso", "estorno", "devolução do dinheiro", "quero meu dinheiro",
                     "ressarcimento", "devolver dinheiro", "receber meu dinheiro",
                     "estornar", "quero devolver"],
        "fluxo": fluxo_reembolso
    },
    {
        "tag": "bandeiras",
        "palavras": ["bandeiras", "cartões", "bandeira", "marcas de cartão", "aceitamos cartões"],
        "fluxo": lambda: fala_bot("Aceitamos as seguintes bandeiras:\n- Crédito: Visa, MasterCard, Elo, Amex, Hipercard\n- Débito: Visa Electron, Maestro, Elo Débito")
    },
    {
        "tag": "desconto",
        "palavras": ["cupom", "desconto", "voucher", "promoção", "codigo promocional",
                     "cupom de desconto", "tem desconto", "black friday", "código desconto"],
        "resposta": "Você pode aplicar seu cupom na última etapa antes de finalizar o pagamento.",
        "opcoes": ["Pagar com Pix", "Pagar no crédito", "Encerrar atendimento"]
    },
    {
        "tag": "consultar_pedido",
        "palavras": ["status do pedido", "meu pedido", "acompanhar pedido", "rastrear",
                     "rastreamento", "onde está meu pedido", "previsão de entrega",
                     "codigo de rastreio", "pedido atrasado", "quando chega"],
        "resposta": "Para consultar seu pedido, acesse: https://app.fashionflow.com.br/meus-pedidos\nInforme o número do pedido e o e-mail cadastrado.",
        "opcoes": ["Reembolso", "Encerrar atendimento"]
    },
    {
        "tag": "exit",
        "palavras": ["sair", "encerrar", "finalizar", "fechar", "tchau", "bye",
                     "adeus", "até mais", "até logo", "valeu", "vlw", "flw",
                     "obrigado", "obrigada", "falou", "encerrar atendimento"],
        "encerrar": True
    }
]


# ============================================================
#  MOTOR DE BUSCA DE INTENÇÃO
# ============================================================

def normalizar(texto):
    import unicodedata
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto


def buscar_intencao(mensagem):
    msg = normalizar(mensagem)
    melhor = None
    max_peso = 0

    for intencao in intencoes:
        peso = 0
        for palavra in intencao["palavras"]:
            p_norm = normalizar(palavra)
            if re.search(r'\b' + re.escape(p_norm) + r'\b', msg):
                peso += len(palavra.split())  # frases valem mais que palavras soltas
        if peso > max_peso:
            max_peso = peso
            melhor = intencao

    return melhor if melhor else None


def resolver_atalho(entrada, opcoes):
    """Permite digitar o número do atalho em vez do texto."""
    try:
        idx = int(entrada.strip()) - 1
        if 0 <= idx < len(opcoes):
            return opcoes[idx]
    except ValueError:
        pass
    return entrada


# ============================================================
#  LOOP PRINCIPAL
# ============================================================

def iniciar_chatbot():
    cabecalho()
    time.sleep(0.3)
    fala_bot("Olá! Seja bem-vindo ao atendimento financeiro da FashionFlow.")
    time.sleep(0.2)
    fala_bot("Como posso te ajudar hoje?")

    opcoes_iniciais = [
        "Formas de pagamento", "Pagar com Pix", "Pagar no crédito",
        "Pagar no débito", "Parcelamento", "Reembolso",
        "Pix + Crédito (misto)", "Encerrar atendimento"
    ]
    exibir_opcoes(opcoes_iniciais)
    opcoes_ativas = opcoes_iniciais[:]

    while True:
        try:
            entrada = input_usuario()
        except (KeyboardInterrupt, EOFError):
            print()
            fala_bot("Até mais! 👋")
            break

        if not entrada:
            fala_erro("Por favor, digite sua mensagem ou escolha uma opção acima.")
            continue

        # Resolve atalhos numéricos
        entrada = resolver_atalho(entrada, opcoes_ativas)

        intencao = buscar_intencao(entrada)

        if intencao is None:
            print()
            fala_bot("Não entendi muito bem. Pode tentar de outra forma?")
            fala_sistema("Ou escolha uma das opções numeradas acima.")
            continue

        # Encerramento
        if intencao.get("encerrar"):
            print()
            fala_bot("Foi um prazer te atender! Se precisar de algo mais, estamos à disposição.")
            fala_bot("Até logo! 👋")
            print()
            linha("═", 55, Cor.AZUL)
            print(Cor.AZUL + "  Atendimento encerrado." + Cor.RESET)
            linha("═", 55, Cor.AZUL)
            print()
            break

        # Tem fluxo interativo (pagamentos, reembolso)
        if "fluxo" in intencao:
            continuou = intencao["fluxo"]()
            if continuou:
                print()
                exibir_opcoes(opcoes_iniciais)
                opcoes_ativas = opcoes_iniciais[:]
            else:
                # Fluxo não continuado → pergunta se encerra
                print()
                if aguardar_confirmacao("Deseja continuar o atendimento?"):
                    exibir_opcoes(opcoes_iniciais)
                    opcoes_ativas = opcoes_iniciais[:]
                else:
                    fala_bot("Tudo bem! Até logo! 👋")
                    break
            continue

        # Resposta simples
        print()
        fala_bot(intencao["resposta"])

        # Exibe novas opções contextuais se disponíveis
        if "opcoes" in intencao:
            opcoes_ativas = intencao["opcoes"]
            exibir_opcoes(opcoes_ativas)
        else:
            opcoes_ativas = opcoes_iniciais[:]
            exibir_opcoes(opcoes_ativas)


# ============================================================
#  PONTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    # Garante que o terminal suporta UTF-8
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
    iniciar_chatbot()