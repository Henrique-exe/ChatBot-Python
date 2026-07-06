"""
chatbot_financeiro.py — Chatbot do Módulo FINANCEIRO — FashionFlow
Escopo: exclusivamente o Grupo Financeiro (Projeto FashionFlow 2026 — UNIFAN).

Este módulo cuida de: cobrança, pagamento, reembolso, nota fiscal, Pix,
cartão, cálculo de desconto/parcelamento e atualização de status de
pagamento (CRUD - UPDATE) na tabela pedidos_vendas.csv.

Qualquer assunto de outro grupo (Vendas, Estoque, Produção, Logística,
Compras) é identificado e redirecionado com uma mensagem específica,
em vez de cair num "não entendi" genérico.
"""

import re
import os
import sys
import csv
import time
import difflib
import unicodedata
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# CORES DO TERMINAL (ANSI)
# Usadas para colorir o texto no terminal. RESET volta ao normal.
# ─────────────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
GREEN   = "\033[92m"
CYAN    = "\033[96m"
YELLOW  = "\033[93m"
RED     = "\033[91m"

# ─────────────────────────────────────────────────────────────
# CONFIGURAÇÕES GLOBAIS
# Altere aqui para mudar comportamentos do bot sem mexer no código.
# ─────────────────────────────────────────────────────────────
ARQUIVO_CSV         = "base_conhecimento.csv"
ARQUIVO_LOG         = "log_atendimento.txt"
ARQUIVO_PEDIDOS     = "pedidos_vendas.csv"   # Tabela compartilhada com o Vendas (CRUD - UPDATE)
PIX_DESCONTO        = Decimal("0.05")   # 5% de desconto no Pix
DESCONTO_VALOR_MINIMO = Decimal("350")
DESCONTO_VALOR_PERCENTUAL = Decimal("10")
MAX_PARCELAS        = 12                # Máximo de parcelas sem juros
CHAVE_PIX           = "12.345.678/0001-99 (FashionFlow Pagamentos Ltda)"
LIMITE_ANIMACAO     = 240               # Textos maiores que isso pulam o efeito de digitação

# Menu de atalhos financeiros (digitar número ou palavra)
MENU_FINANCEIRO = {
    "1":"cobranca incorreta","cobranca":"cobranca incorreta","cobrança":"cobranca incorreta",
    "2":"pagamento nao reconhecido","fraude":"pagamento nao reconhecido","contestacao":"pagamento nao reconhecido",
    "3":"paguei e nao constou","conciliacao":"paguei e nao constou",
    "4":"reembolso","estorno":"reembolso",
    "5":"nota fiscal","nf":"nota fiscal",
    "6":"formas de pagamento","formas":"formas de pagamento",
    "7":"extrato financeiro","extrato":"extrato financeiro",
    "8":"status do pagamento","status":"status do pagamento",
    "9":"negociar divida","acordo":"negociar divida",
}

# ─────────────────────────────────────────────────────────────
# ROTEAMENTO ENTRE SETORES (Semana 2 — "A Batalha dos Pesos")
# O Financeiro atende SOMENTE assuntos financeiros. Se a mensagem for
# claramente de outro grupo do FashionFlow, o Bot não tenta adivinhar:
# ele explica educadamente qual é o setor certo.
#
# Regra de ouro (combinação obrigatória / E lógico, igual à missão do
# Grupo 2 na dinâmica): se a frase também tiver uma palavra financeira
# forte (pix, pagamento, cartao, boleto, fatura, cobranca, reembolso...),
# o Financeiro sempre vence — mesmo que "prazo", "pedido" ou "conta"
# apareçam também. Isso resolve a ambiguidade descrita no slide da
# Semana 2 (ex: "prazo" pode ser de entrega OU de estorno).
# ─────────────────────────────────────────────────────────────
PALAVRAS_FINANCEIRO_FORTES = {
    "pix","pagamento","pagto","pgto","cartao","cartão","boleto","cobranca","cobrança",
    "fatura","reembolso","estorno","nota fiscal","parcela","parcelas","desconto",
    "conta","juros","divida","dívida","credito","crédito","debito","débito",
    "financeiro","fraude","clonado","clonaram",
}

DEPARTAMENTOS = {
    "vendas": {
        "palavras": [
            "comprar camisa","comprar produto","catalogo","catálogo","fechar pedido",
            "novo pedido","quero comprar","fazer pedido","escolher produto",
            "adicionar ao carrinho","tamanho p","tamanho m","tamanho g","quero levar",
            "carrinho","meu carrinho","ver carrinho",
            "valor de uma camisa","valor da camisa","preco da camisa","preço da camisa",
            "valor de um produto","valor do produto","preco do produto","preço do produto",
            "quanto custa a camisa","quanto custa o produto","valor de uma peca","valor de uma peça",
        ],
        "mensagem": (
            "Fechar pedidos e ver o catálogo de produtos é com o time de "
            "Vendas! 🛍️ Por aqui no Financeiro eu cuido de pagamento, cobrança, "
            "reembolso e nota fiscal. Posso ajudar com algo desses assuntos?"
        ),
    },
    "estoque": {
        "palavras": [
            "tem estoque","disponibilidade do produto","quantidade em estoque",
            "tem disponivel","tem disponível","produto disponivel","produto disponível",
            "tem no estoque","peca disponivel","peça disponível","disponivel","disponível",
            "em estoque",
        ],
        "mensagem": (
            "Consultar disponibilidade em estoque é com o time de Estoque. 📦 "
            "Aqui no Financeiro eu só cuido da parte de pagamento do seu pedido. "
            "Posso ajudar com isso?"
        ),
    },
    "producao": {
        "palavras": [
            "ordem de servico","ordem de serviço","numero da os","número da os",
            "status da producao","status da produção","etapa de producao",
            "etapa de produção","fila de corte","mandei pra estamparia",
            "minha os","da os","status da os","na costura","em producao","em produção",
        ],
        "mensagem": (
            "Acompanhar a produção (corte, costura, estamparia) é com o time de "
            "Produção. 🧵 Posso ajudar com o pagamento do seu pedido, se quiser."
        ),
    },
    "logistica": {
        "palavras": [
            "calcular frete","valor do frete","frete","cep","rastrear","rastreio",
            "codigo de rastreio","código de rastreio","transportadora",
            "prazo de entrega","onde esta minha encomenda","onde está minha encomenda",
            "quando chega","quando vai chegar","quando ira chegar","quando irá chegar",
            "vai chegar","ira chegar","irá chegar",
            "retirar na loja","loja fisica","loja física",
        ],
        "mensagem": (
            "Cálculo de frete, CEP e rastreio de entrega é com o time de "
            "Logística. 🚚 Aqui no Financeiro posso ajudar com pagamento, "
            "cobrança ou reembolso, se precisar."
        ),
    },
    "compras": {
        "palavras": [
            "fornecedor","fornecedores","materia prima","matéria-prima",
            "insumo","insumos","tecido de algodao","tecido de algodão",
            "ziper no estoque","zíper no estoque","pedido de fornecedor",
        ],
        "mensagem": (
            "Assuntos com fornecedores e matéria-prima são com o time de "
            "Compras. 📋 Posso ajudar você com o financeiro do seu pedido, "
            "se for o caso."
        ),
    },
}

# Contextos "formulário crítico": só saem com "sair"/"cancelar" explícito.
# Em todos os outros contextos, qualquer intenção forte (ou redirecionamento
# de setor) pode interromper automaticamente — resolve o caso do "usuário
# indeciso" sem depender de uma lista fixa de tags.
CONTEXTOS_CRITICOS = {"credito", "debito", "parcela"}

RESPOSTAS_SIM = {"s","sim","ss","aham","claro","quero","pode","bora","agora","vamos","confirmado"}
RESPOSTAS_NAO = {"n","nao","não","negativo","deixa","cancelar","cancela","nao quero","desisto"}
COMANDOS_REPETIR = {"repete","manda de novo","fala de novo","repete ai","manda de novo ai"}
COMANDOS_LIMPAR = {
    "limpar conversa","limpar o chat","limpar chat","/clear","clear",
    "resetar conversa","reiniciar conversa","reiniciar atendimento","recomecar",
    "recomeçar","novo atendimento","limpar historico","limpar histórico",
}
COMANDOS_AJUDA = {
    "ajuda","help","menu","comandos","o que voce faz","o que você faz",
    "quais suas funcoes","quais são suas funções","o que voce sabe fazer",
    "o que você sabe fazer","como voce funciona","como você funciona",
    "quais comandos","lista de comandos","opcoes","opções",
}

# ─────────────────────────────────────────────────────────────
# ESTADO GLOBAL DA CONVERSA
# Tudo que precisa ser lembrado entre mensagens fica aqui.
# ─────────────────────────────────────────────────────────────
MODO_WEB = False

estado = {
    "contexto":          None,  # Aguardando resposta de alguma pergunta?
    "tentativas_valor":  0,     # Quantas vezes o valor digitado foi inválido
    "percentual_pendente": None, # % de desconto combinado, aguardando o valor
    "pagamento_pendente_pix": False,
    "cpf_pendente":      None,  # CPF em confirmação de pagamento
    "sem_entender":      0,     # Quantas msgs seguidas o bot não entendeu
    "historico":         [],    # Todo o histórico (usuário + bot)
    "historico_recente": [],    # Últimas respostas do bot (para "repete")
    "mem_repeticao":     [],    # Backup das últimas respostas antes de limpar
    "encerrar_sessao":   False, # Sinaliza para o loop principal que deve parar
    "conectado_humano":  False, # True enquanto o cliente está "na fila" com um humano
    "_saida":            [],
}

def nova_sessao() -> dict:
    """Cria um estado de conversa novo e isolado para terminal ou web."""
    return {
        "contexto": None,
        "tentativas_valor": 0,
        "percentual_pendente": None,
        "pagamento_pendente_pix": False,
        "cpf_pendente": None,
        "sem_entender": 0,
        "historico": [],
        "historico_recente": [],
        "mem_repeticao": [],
        "encerrar_sessao": False,
        "conectado_humano": False,
        "_saida": [],
    }

# Comandos para o cliente retomar a conversa com o bot enquanto aguarda humano
COMANDOS_VOLTAR_BOT = {
    "voltar","voltar ao bot","continuar com o bot","falar com o bot",
    "cancelar humano","voltar a falar com o bot","quero voltar",
}

intencoes = []   # Preenchido ao carregar o CSV

# ─────────────────────────────────────────────────────────────
# UTILITÁRIOS DE TEXTO
# ─────────────────────────────────────────────────────────────

def normalizar(texto: str) -> str:
    """Remove acentos e deixa tudo em minúsculo. Ex: 'Ação' → 'acao'"""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")

def expandir_girias(texto: str) -> str:
    """Substitui gírias/abreviações financeiras brasileiras pelo termo padrão."""
    substituicoes = {
        r'\bvlr\b': 'valor', r'\bpgto\b': 'pagamento', r'\bpagmto\b': 'pagamento',
        r'\bparc\b': 'parcela', r'\bjrs\b': 'juros', r'\bbol\b': 'boleto',
        r'\bgrana\b': 'dinheiro', r'\bdindin\b': 'dinheiro', r'\bdimdim\b': 'dinheiro',
        r'\bta caro\b': 'limite de orcamento', r'\bmudei de ideia\b': 'formas de pagamento',
    }
    for padrao, substituto in substituicoes.items():
        texto = re.sub(padrao, substituto, texto)
    return texto

def classificar_sim_nao(texto: str) -> str | None:
    """
    Classifica a resposta como 'sim', 'nao' ou None. Além da checagem exata,
    tolera pequenos erros de digitação (ex: 'siom' -> 'sim') via distância
    aproximada, mas só para respostas curtas — evita confundir frases
    maiores que apenas contenham letras parecidas por coincidência.
    """
    if texto in RESPOSTAS_SIM:
        return "sim"
    if texto in RESPOSTAS_NAO:
        return "nao"
    if texto and len(texto) <= 6:
        if difflib.get_close_matches(texto, RESPOSTAS_SIM, n=1, cutoff=0.8):
            return "sim"
        if difflib.get_close_matches(texto, RESPOSTAS_NAO, n=1, cutoff=0.8):
            return "nao"
    return None

def eh_numero(texto: str) -> bool:
    """
    É_NUMERO() do pseudocódigo da Semana 4 (Módulo Financeiro).
    Confirma se o texto é só um número (com opcional R$, vírgula ou ponto)
    antes de qualquer cálculo, evitando o TypeError de multiplicar texto.
    Ex: '150.30' -> True | 'cento e cinquenta reais' -> False
    """
    limpo = texto.strip().lower().replace("r$", "").strip()
    limpo = re.sub(r'\s+', '', limpo)
    return bool(re.fullmatch(
        r'(?:'
        r'\d+'
        r'|\d+[.,]\d{1,2}'
        r'|\d{1,3}(?:\.\d{3})+'
        r'|\d{1,3}(?:\.\d{3})+,\d{1,2}'
        r')',
        limpo,
    ))

def checar_redirecionamento(texto: str) -> dict | None:
    """
    Roteamento entre setores (Semana 2 — Batalha dos Pesos).
    Se a mensagem for claramente de outro grupo do FashionFlow, retorna
    a resposta de redirecionamento. Se tiver palavra financeira forte
    junto, o Financeiro sempre vence (combinação obrigatória / E lógico).
    """
    if any(p in texto for p in PALAVRAS_FINANCEIRO_FORTES):
        return None
    for setor, dados in DEPARTAMENTOS.items():
        if any(p in texto for p in dados["palavras"]):
            return {"tag": f"redirecionar_{setor}", "resposta": dados["mensagem"]}
    return None

def detectar_recibo_comprovante(texto: str) -> dict | None:
    """Prioriza pedidos claros de recibo/comprovante sem confundir com pagamento pendente."""
    termos_documento = ("recibo", "comprovante", "comprovantes")
    termos_pedido = ("quero", "preciso", "manda", "mandar", "me passa", "paguei")
    if any(t in texto for t in termos_documento) and any(t in texto for t in termos_pedido):
        for intencao in intencoes:
            if intencao.get("tag") == "extrato_historico":
                return intencao
    return None

# ─────────────────────────────────────────────────────────────
# LOG E EXIBIÇÃO
# ─────────────────────────────────────────────────────────────

def registrar_log(quem: str, mensagem: str):
    """Salva a mensagem no arquivo de log com horário."""
    hora = datetime.now().strftime("%H:%M:%S")
    with open(ARQUIVO_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{hora}] {quem}: {mensagem}\n")

def bot_falar(texto: str, digitar=True):
    """
    Exibe a resposta do bot com efeito de digitação e salva no log/histórico.

    Resiliência (Item E):
    - Textos muito longos (> LIMITE_ANIMACAO) pulam a animação direto.
    - Se o usuário apertar Ctrl+C durante a digitação, o bot só exibe o
      restante do texto imediatamente — nunca fecha o programa por isso.
    """
    registrar_log("Bot", texto)
    estado["historico"].append({"quem": "bot", "msg": texto})
    estado["historico_recente"].append(texto)

    if MODO_WEB:
        estado.setdefault("_saida", []).append(texto)
        return

    try:
        time.sleep(0.4)
    except KeyboardInterrupt:
        pass  # pula a pausa inicial sem encerrar o chatbot

    # Destaca valores em R$ com cor verde
    colorido = texto.replace("R$", f"{GREEN}{BOLD}R${RESET}{GREEN}")
    sys.stdout.write(f"{GREEN}{BOLD}Bot: {RESET}{GREEN}")
    sys.stdout.flush()

    texto_longo = len(texto) > LIMITE_ANIMACAO
    if digitar and not texto_longo:
        idx = -1
        try:
            for idx, char in enumerate(colorido):
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(0.008)
        except KeyboardInterrupt:
            # Pula direto para o texto completo em vez de fechar o bot
            sys.stdout.write(colorido[idx + 1:])
            sys.stdout.flush()
        print(RESET)
    else:
        print(f"{colorido}{RESET}")

# ─────────────────────────────────────────────────────────────
# CARREGAMENTO DA BASE DE CONHECIMENTO (CSV)
# O CSV define todas as perguntas que o bot sabe responder.
# ─────────────────────────────────────────────────────────────

def carregar_intencoes(caminho=ARQUIVO_CSV) -> list:
    """
    Lê o CSV e transforma cada linha em uma intenção com regex pré-compiladas.
    As intenções são ordenadas por prioridade (menor número = maior prioridade).
    """
    resultado = []
    with open(caminho, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            palavras = [p.strip() for p in row["palavras"].split(",") if p.strip()]

            # Para frases com 2+ palavras, guarda também os termos separados
            # (cada um como regex de palavra inteira). Usado num 2º passe de
            # busca (ver buscar_resposta) que aceita a frase mesmo com outras
            # palavras intercaladas — ex: "status do pagamento" também deve
            # bater em "status ATUAL DO MEU pagamento".
            frases_multipalavra = []
            for p in palavras:
                termos = normalizar(p).split()
                if len(termos) >= 2:
                    frases_multipalavra.append([
                        re.compile(r'(?<!\w)' + re.escape(t) + r'(?!\w)')
                        for t in termos
                    ])

            intencao = {
                "tag":      row["tag"],
                "prioridade": int(row["prioridade"]),
                "resposta": row["resposta"],
                # Compila regex de cada palavra-chave para busca eficiente
                "regex_palavras": [
                    re.compile(r'(?<!\w)' + re.escape(normalizar(p)) + r'(?!\w)')
                    for p in palavras
                ],
                "frases_multipalavra": frases_multipalavra,
            }
            if row["pergunta_seguinte"]:
                intencao["pergunta_seguinte"] = row["pergunta_seguinte"]
            if row["encerrar"] == "True":
                intencao["encerrar"] = True
            resultado.append(intencao)
    return sorted(resultado, key=lambda x: x["prioridade"])

# ─────────────────────────────────────────────────────────────
# PERSISTÊNCIA — CRUD (READ e UPDATE)
# Semana 3 / "O Guardião da Memória" — Missão Grupo 2 (Financeiro):
# buscar o pedido pelo CPF em pedidos_vendas.csv, conferir o status e,
# somente quando for de fato uma confirmação de pagamento, alterar para
# "Pago" e SALVAR. Uma simples consulta de status/saldo NUNCA deve
# alterar o dado — por isso READ e UPDATE são funções separadas.
# ─────────────────────────────────────────────────────────────

CAMPOS_PEDIDOS = ["id", "cpf", "produto", "valor", "status"]
CPF_INVALIDO_MSG = "Esse CPF não parece válido. Digite os 11 números ou use o formato 123.456.789-00."

def cpf_basico_valido(cpf: str) -> bool:
    """Valida tamanho e rejeita CPFs formados por um único dígito repetido."""
    return len(cpf) == 11 and len(set(cpf)) > 1

def _buscar_pedido_por_cpf(cpf: str):
    """
    READ puro: retorna (linhas_completas, linha_do_cpf, erro).
    Nunca deixa o Bot travar se o arquivo não existir (defesa do
    'arquivo fantasma' — Semana 4, aplicada à nossa própria tabela).
    """
    try:
        with open(ARQUIVO_PEDIDOS, newline="", encoding="utf-8") as f:
            linhas = list(csv.DictReader(f))
    except FileNotFoundError:
        return None, None, (
            "Sistema interno: tabela de pedidos indisponível no momento. "
            "Por favor, avise o suporte técnico."
        )

    for linha in linhas:
        if re.sub(r'\D', '', linha.get("cpf", "")) == cpf:
            return linhas, linha, None

    return linhas, None, (
        "Não encontrei nenhum pedido com esse CPF. Poderia conferir "
        "o número e tentar novamente?"
    )

def consultar_pedido_por_cpf(cpf: str) -> str:
    """
    READ — usado por 'status do pagamento' e 'quanto eu devo'.
    Só informa a situação atual; NUNCA altera o status do pedido.
    """
    if not cpf_basico_valido(cpf):
        return CPF_INVALIDO_MSG

    _, linha, erro = _buscar_pedido_por_cpf(cpf)
    if erro:
        return erro

    if linha["status"] == "Pago":
        return f"O pedido #{linha['id']} está com o pagamento em dia (Pago). Não há pendências."

    if linha["status"] == "Aguardando Pagamento":
        return (
            f"O pedido #{linha['id']} ({linha['produto']}) está com pagamento "
            f"pendente, no valor de {dinheiro(Decimal(linha['valor']))}. Deseja "
            "confirmar o pagamento agora?"
        )

    return f"O pedido #{linha['id']} está com status '{linha['status']}'."

def confirmar_pagamento_por_cpf(cpf: str) -> str:
    """
    UPDATE real na tabela pedidos_vendas.csv.
    Sempre segue o padrão: READ -> validação -> altera coluna -> SALVAR.
    Só deve ser chamada quando o cliente está de fato confirmando um
    pagamento (ex: aviso do banco de PIX recebido) — nunca em uma
    simples consulta de status.
    """
    if not cpf_basico_valido(cpf):
        return CPF_INVALIDO_MSG

    linhas, linha_encontrada, erro = _buscar_pedido_por_cpf(cpf)
    if erro:
        return erro

    if linha_encontrada["status"] == "Pago":
        return (
            f"O pedido #{linha_encontrada['id']} já está com o pagamento "
            f"confirmado como Pago. Posso ajudar com mais alguma coisa?"
        )

    if linha_encontrada["status"] != "Aguardando Pagamento":
        return (
            f"O pedido #{linha_encontrada['id']} está com status "
            f"'{linha_encontrada['status']}', então não é possível confirmar "
            "o pagamento agora. Deseja sinalizar que este caso precisa de análise humana do Financeiro?"
        )

    # UPDATE: altera a coluna de status e SALVA a tabela inteira
    linha_encontrada["status"] = "Pago"
    with open(ARQUIVO_PEDIDOS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS_PEDIDOS)
        writer.writeheader()
        writer.writerows(linhas)

    return (
        f"Oba! Pagamento do pedido #{linha_encontrada['id']} confirmado com "
        f"sucesso ({dinheiro(Decimal(linha_encontrada['valor']))}). Nossa equipe "
        "já está preparando o próximo passo! 🎉"
    )

# ─────────────────────────────────────────────────────────────
# FUNÇÕES DE EXTRAÇÃO DE DADOS DO TEXTO
# Usadas para identificar números, produtos, cores etc. nas mensagens.
# ─────────────────────────────────────────────────────────────

def dinheiro(valor) -> str:
    """Formata um Decimal como moeda brasileira. Ex: 55.5 → 'R$ 55,50'"""
    v = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"R$ {v:.2f}".replace(".", ",")

def para_decimal(texto: str) -> Decimal:
    """Converte string com R$, vírgulas etc. em Decimal."""
    texto = texto.strip().lower().replace("r$", "").strip()
    texto = re.sub(r'\s+', '', texto)
    if re.fullmatch(r'\d{1,3}(?:\.\d{3})+,\d{1,2}', texto):
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r'\d{1,3}(?:\.\d{3})+', texto):
        texto = texto.replace(".", "")
    elif "," in texto:
        texto = texto.replace(",", ".")
    return Decimal(texto)

def extrair_percentual(texto: str, palavras: list) -> Decimal:
    """Extrai um percentual do texto próximo a certas palavras. Ex: 'desconto de 10%' → 10"""
    w = "|".join(re.escape(p) for p in palavras)
    m = re.search(rf'(?:{w})\s*(?:de|do|da)?\s*(\d+(?:[.,]\d+)?)\s*%', texto)
    if not m:
        m = re.search(rf'(\d+(?:[.,]\d+)?)\s*%\s*(?:de\s*)?(?:{w})', texto)
    return para_decimal(m.group(1)) if m else Decimal("0")

def validar_percentual_desconto(texto: str, percentual: Decimal) -> str | None:
    """Valida percentuais de desconto antes de calcular."""
    if not any(p in texto for p in ("desconto", "cupom", "promocao", "promoção")):
        return None
    if re.search(r'-\s*\d+(?:[.,]\d+)?\s*%', texto):
        return "Opa, desconto negativo não é válido. Informe um percentual positivo, como 10%."
    if re.search(r'\d+(?:[.,]\d+)?\s*%', texto) and not (Decimal("1") <= percentual <= Decimal("100")):
        return "Opa, esse percentual de desconto não parece válido. Use um valor entre 1% e 100%."
    return None

def extrair_parcelas(texto: str) -> int | None:
    """Extrai número de parcelas do texto. Ex: '3x', 'em 3 vezes' → 3"""
    m = re.search(r'(?<!\w)(\d{1,2})\s*(?:x|vezes|parcelas?)(?!\w)', texto)
    if not m:
        m = re.search(r'em\s+(\d{1,2})\s*(?:x|vezes|parcelas?)', texto)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 24 else None
    return None

def extrair_valores_soltos(texto: str) -> list:
    """
    Extrai valores numéricos genéricos do texto.
    Usado para somar valores avulsos como 'quanto fica 100 + 250?'
    """
    padrao = re.compile(
        r'(?<![\w%])(?:r\$\s*)?(\d+(?:\.\d{3})*(?:[,.]\d{1,2})?|\d+)'
        r'(?!\s*(?:x|vezes|parcelas?|%))(?!\w)'
    )
    valores = []
    for m in padrao.finditer(texto):
        ant = texto[max(0, m.start()-18):m.start()]
        depois = texto[m.end():m.end()+12]
        parece_percentual = re.search(r'(desconto|juros|taxa de juros|parcelas?|vezes)\s*(de)?\s*$', ant)
        parece_valor_monetario = re.match(r'\s*(reais|real|conto|contos|pila|pilas|r\$)', depois)
        if parece_percentual and not parece_valor_monetario:
            continue
        valores.append(para_decimal(m.group(1)))
    return valores

# ─────────────────────────────────────────────────────────────
# MONTAGEM DE RESPOSTAS DE CÁLCULO
# ─────────────────────────────────────────────────────────────

def calcular_desconto_resposta(valor: Decimal, percentual: Decimal) -> str:
    """
    DEFESA — Módulo Financeiro (Semana 4 / Dinâmica do Caos, Grupo 1).
    Só é chamada depois que eh_numero() confirmou que o valor é válido.
    Calcula o desconto de X% sobre o valor informado e mostra o valor final.
    """
    d = (valor * percentual / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
    final = (valor - d).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return (
        f"Sobre {dinheiro(valor)}, o desconto de {percentual}% é de {dinheiro(d)}.\n"
        f"Valor final: {dinheiro(final)}"
    )

def calcular_descontos_aplicaveis(valor: Decimal, pagar_no_pix: bool) -> dict:
    """Calcula descontos financeiros automáticos sem alterar nenhum pedido."""
    valor_intermediario = valor
    detalhes = []

    if valor >= DESCONTO_VALOR_MINIMO:
        desconto_valor = (valor * DESCONTO_VALOR_PERCENTUAL / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
        valor_intermediario = (valor - desconto_valor).quantize(Decimal("0.01"), ROUND_HALF_UP)
        detalhes.append(
            f"Desconto automático para compras a partir de {dinheiro(DESCONTO_VALOR_MINIMO)} "
            f"({DESCONTO_VALOR_PERCENTUAL}%): -{dinheiro(desconto_valor)}"
        )

    valor_final = valor_intermediario
    if pagar_no_pix:
        desconto_pix = (valor_intermediario * PIX_DESCONTO).quantize(Decimal("0.01"), ROUND_HALF_UP)
        valor_final = (valor_intermediario - desconto_pix).quantize(Decimal("0.01"), ROUND_HALF_UP)
        detalhes.append(f"Desconto adicional no Pix (5%): -{dinheiro(desconto_pix)}")

    return {"valor_original": valor, "valor_final": valor_final, "detalhes": detalhes}

def resposta_desconto_completa(valor: Decimal, pagar_no_pix: bool) -> str:
    """Monta uma simulação financeira com desconto automático e opção Pix."""
    sem_pix = calcular_descontos_aplicaveis(valor, pagar_no_pix=False)
    com_pix = calcular_descontos_aplicaveis(valor, pagar_no_pix=True)

    linhas = [f"Valor da compra: {dinheiro(valor)}"]
    if sem_pix["detalhes"]:
        linhas.extend(sem_pix["detalhes"])
        linhas.append(f"Valor com desconto: {dinheiro(sem_pix['valor_final'])}")
    else:
        linhas.append(
            f"Essa compra ainda não atinge o desconto automático por valor "
            f"(vale a partir de {dinheiro(DESCONTO_VALOR_MINIMO)})."
        )

    if pagar_no_pix:
        linhas.append(f"Pagando no Pix, valor final: {dinheiro(com_pix['valor_final'])}.")
    else:
        economia_extra = (sem_pix["valor_final"] - com_pix["valor_final"]).quantize(Decimal("0.01"), ROUND_HALF_UP)
        linhas.append(
            f"No Pix, com 5% adicional, ficaria {dinheiro(com_pix['valor_final'])} "
            f"(economia extra de {dinheiro(economia_extra)})."
        )
    return "\n".join(linhas)

def montar_resposta_calculo(valores_soltos: list, desconto, parcelas, juros) -> str | None:
    """Gera resposta para cálculos financeiros gerais (com desconto, juros e parcelamento)."""
    cabecalho = "Resumo do cálculo financeiro FashionFlow:"
    if not MODO_WEB:
        cabecalho = f"\n{CYAN}{cabecalho}{RESET}"
    linhas = [cabecalho]
    total = Decimal("0")

    if valores_soltos:
        linhas.append("Valores informados:")
        for n, v in enumerate(valores_soltos, 1):
            total += v
            linhas.append(f"- Valor {n}: {dinheiro(v)}")

    if total <= 0:
        return None

    linhas.append(f"\nSubtotal: {dinheiro(total)}")

    base = total
    if desconto <= 0 and total >= DESCONTO_VALOR_MINIMO:
        desconto = DESCONTO_VALOR_PERCENTUAL
        linhas.append(f"Desconto automático aplicado para compras a partir de {dinheiro(DESCONTO_VALOR_MINIMO)}.")
    if desconto > 0:
        d = (total * desconto / 100).quantize(Decimal("0.01"), ROUND_HALF_UP)
        base -= d
        linhas.append(f"Desconto aplicado ({desconto}%): -{dinheiro(d)}")
        linhas.append(f"Valor com desconto: {dinheiro(base)}")

    pix = (base * (1 - PIX_DESCONTO)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    linhas.append(f"Pix com 5% de desconto adicional: {dinheiro(pix)}")

    if parcelas:
        if juros > 0:
            total_j = (base * ((1 + juros/100) ** parcelas)).quantize(Decimal("0.01"), ROUND_HALF_UP)
            p = (total_j / parcelas).quantize(Decimal("0.01"), ROUND_HALF_UP)
            linhas.append(f"Crédito em {parcelas}x com juros de {juros}% ao mês: {parcelas}x de {dinheiro(p)}")
            linhas.append(f"Total no crédito: {dinheiro(total_j)}")
        else:
            p = (base / parcelas).quantize(Decimal("0.01"), ROUND_HALF_UP)
            linhas.append(f"Crédito em {parcelas}x sem juros: {parcelas}x de {dinheiro(p)}")
    else:
        p12 = (base / Decimal(MAX_PARCELAS)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        linhas.append(f"Crédito: até {MAX_PARCELAS}x sem juros de {dinheiro(p12)}")

    return "\n".join(linhas)

# ─────────────────────────────────────────────────────────────
# PROCESSADOR PRINCIPAL DE CÁLCULOS
# Chamado antes de qualquer outra lógica — tem prioridade máxima.
# ─────────────────────────────────────────────────────────────

PALAVRAS_CALCULO = {
    "quanto fica","qual valor total","quanto vou pagar","total somando","somar","soma",
    "calcular","calcula","orcamento","orçamento","custa","valor total","preco","preço",
    "desconto","parcelar","parcelas","juros",
}
# Subconjunto que realmente indica um PEDIDO DE CÁLCULO (não apenas uma
# pergunta sobre forma de pagamento/parcelamento). Só esse grupo aciona a
# defesa "digite apenas números" quando não há dígito na mensagem — evita
# atropelar intenções do CSV como 'credito' ou 'parcela'.
PALAVRAS_CALCULO_FORTE = {
    "quanto fica","qual valor total","quanto vou pagar","total somando","somar","soma",
    "calcular","calcula","orcamento","orçamento",
}

def processar_calculo(entrada: str, texto: str) -> dict | None:
    """
    Interpreta cálculos financeiros (desconto, juros, parcelamento, soma de
    valores). Segue a defesa da Semana 4 (Módulo Financeiro): sempre valida
    se o texto é um número antes de calcular, para nunca travar com
    TypeError ao tentar multiplicar texto por número.
    """
    # Cliente pede para calcular desconto mas ainda não informou o valor
    # (replica o diálogo real da Dinâmica do Caos — Grupo 1, Financeiro).
    # Importante: um "10%" no pedido tem dígito, mas não é um VALOR de
    # compra — por isso removemos percentuais antes de checar se falta valor.
    texto_sem_percentual = re.sub(r'\d+(?:[.,]\d+)?\s*%', '', texto)
    tem_valor_informado = any(ch.isdigit() for ch in texto_sem_percentual)
    pede_desconto_sem_valor = (
        "desconto" in texto
        and re.search(r'\b(?:quero saber|quero calcular|calcular|calcula|qual)\b', texto)
        and not tem_valor_informado
    )
    if pede_desconto_sem_valor:
        percentual = extrair_percentual(texto, ["desconto", "cupom", "promocao", "promoção"])
        erro_percentual = validar_percentual_desconto(texto, percentual)
        if erro_percentual:
            return _resultado(erro_percentual, "calculo_invalido")
        estado["percentual_pendente"] = percentual if percentual > 0 else Decimal("10")
        estado["pagamento_pendente_pix"] = "pix" in texto
        estado["tentativas_valor"] = 0
        return _resultado("Qual o valor da sua compra?", "aguardando_valor_desconto", contexto_manual=True)

    if not any(k in texto for k in PALAVRAS_CALCULO):
        return None

    # DEFESA: se pediu cálculo mas não digitou nenhum número, orienta o
    # cliente em vez de travar (ex: "cento e cinquenta reais e trinta centavos").
    # Só dispara para verbos claros de cálculo — não para menções soltas a
    # 'crédito' ou 'parcelas', que devem seguir para as intenções do CSV.
    if not any(ch.isdigit() for ch in texto):
        if any(k in texto for k in PALAVRAS_CALCULO_FORTE):
            # Mesmo contexto usado por 'pede_desconto_sem_valor' acima, para que
            # a próxima mensagem do usuário (o número) seja de fato capturada
            # em vez de cair em fallback (bug real observado no log de produção).
            percentual = extrair_percentual(texto, ["desconto", "cupom", "promocao", "promoção"])
            erro_percentual = validar_percentual_desconto(texto, percentual)
            if erro_percentual:
                return _resultado(erro_percentual, "calculo_invalido")
            estado["percentual_pendente"] = percentual if percentual > 0 else Decimal("10")
            estado["pagamento_pendente_pix"] = "pix" in texto
            estado["tentativas_valor"] = 0
            return _resultado(
                "Para calcular, digite apenas números. Ex: 150.30",
                "aguardando_valor_desconto",
                contexto_manual=True,
            )
        return None

    desconto = extrair_percentual(texto, ["desconto", "cupom", "promocao", "promoção"])
    erro_percentual = validar_percentual_desconto(texto, desconto)
    if erro_percentual:
        return _resultado(erro_percentual, "calculo_invalido")
    juros    = extrair_percentual(texto, ["juros", "taxa"])
    parcelas = extrair_parcelas(texto)
    valores  = extrair_valores_soltos(texto)
    if not valores:
        return None
    if any(v <= 0 for v in valores):
        return _resultado("O valor da compra precisa ser maior que zero para eu calcular o desconto.", "calculo_invalido")

    resp = montar_resposta_calculo(valores, desconto, parcelas, juros)
    return _resultado(resp, "calculo_concluido", "Deseja seguir com Pix ou Cartão? (s/n)") if resp else None

def _resultado(resposta: str, tag: str, pergunta: str = "", contexto_manual: bool = False) -> dict:
    """Atalho para criar dicionário de resultado padronizado."""
    return {
        "resposta": resposta,
        "tag": tag,
        "pergunta_seguinte": pergunta,
        "contexto_manual": contexto_manual,
    }

# ─────────────────────────────────────────────────────────────
# BUSCA NA BASE DE CONHECIMENTO (CSV)
# Procura a intenção que melhor corresponde à mensagem.
# ─────────────────────────────────────────────────────────────

def buscar_resposta(mensagem: str) -> dict:
    """
    Normaliza a mensagem e percorre as intenções do CSV em ordem de prioridade.
    Retorna a primeira intenção cujas palavras-chave aparecem na mensagem.
    """
    texto = expandir_girias(normalizar(mensagem))
    if texto in ("cancelar atendimento", "cancelar o atendimento"):
        return {"tag":"exit","resposta":"Atendimento finalizado. Obrigado por falar com o Financeiro da FashionFlow.","encerrar":True}
    recibo = detectar_recibo_comprovante(texto)
    if recibo:
        return recibo
    for intencao in intencoes:
        if any(r.search(texto) for r in intencao["regex_palavras"]):
            return intencao

    # 2º passe (mais tolerante): aceita uma frase-chave de 2+ palavras mesmo
    # que o cliente tenha intercalado outras palavras no meio dela, desde
    # que todos os termos apareçam na mensagem (ex: "quero saber quando meu
    # pedido ira chegar" ainda deve reconhecer "quando" + "chega"-like termos
    # cadastrados). Só roda se a busca exata (mais precisa) não encontrou nada.
    for intencao in intencoes:
        for termos in intencao.get("frases_multipalavra", []):
            if all(t.search(texto) for t in termos):
                return intencao

    return {"tag":"fallback","resposta":"Desculpe, não consegui compreender. Pode tentar explicar de outra forma?"}

# ─────────────────────────────────────────────────────────────
# GESTÃO DE CONTEXTO
# O "contexto" guarda o que o bot estava esperando do usuário.
# Ex: bot perguntou "Pix ou Cartão?" → contexto = "calculo_concluido"
# ─────────────────────────────────────────────────────────────

def processar_contexto(entrada: str, texto: str) -> bool:
    """
    Verifica se o bot estava aguardando alguma resposta específica (contexto ativo).
    Retorna True se o contexto tratou a mensagem, False caso contrário.
    """
    ctx = estado["contexto"]

    # Atalhos do menu financeiro têm prioridade sempre
    if texto in MENU_FINANCEIRO:
        emitir_resultado(buscar_resposta(MENU_FINANCEIRO[texto]))
        return True

    # Aguardando o valor da compra para calcular o desconto
    # (DEFESA — Semana 4 / Dinâmica do Caos, Grupo 1 Financeiro)
    if ctx == "aguardando_valor_desconto":
        if texto in {"sair","cancelar","n","nao","não"}:
            bot_falar("Sem problemas, cálculo cancelado.")
            estado["contexto"] = None; estado["tentativas_valor"] = 0; estado["percentual_pendente"] = None; estado["pagamento_pendente_pix"] = False
            return True
        novo = _checar_mudanca_assunto(entrada, ctx)
        if novo:
            estado["tentativas_valor"] = 0; estado["percentual_pendente"] = None; estado["pagamento_pendente_pix"] = False
            emitir_resultado(novo)
            return True
        if eh_numero(entrada):
            valor = para_decimal(entrada)
            if valor <= 0:
                bot_falar("O valor da compra precisa ser maior que zero para eu calcular o desconto.")
                return True
            percentual = estado["percentual_pendente"] or Decimal("10")
            bot_falar(calcular_desconto_resposta(valor, percentual))
            estado["contexto"] = None; estado["tentativas_valor"] = 0; estado["percentual_pendente"] = None; estado["pagamento_pendente_pix"] = False
        else:
            estado["tentativas_valor"] += 1
            if estado["tentativas_valor"] >= 3:
                bot_falar("Não consegui validar o valor digitado. Vamos tentar novamente mais tarde.")
                estado["contexto"] = None; estado["tentativas_valor"] = 0; estado["percentual_pendente"] = None; estado["pagamento_pendente_pix"] = False
            else:
                bot_falar(f"Para calcular, digite apenas números. Ex: 150.30 (tentativa {estado['tentativas_valor']}/3)")
        return True

    # Aguardando o CPF para confirmar pagamento
    # (CRUD - UPDATE — Semana 3 / O Guardião da Memória, Grupo 2 Financeiro)
    if ctx == "aguardando_cpf_pagamento":
        if texto in {"sair","cancelar","n","nao","não"}:
            bot_falar("Sem problemas, cancelei a confirmação de pagamento.")
            estado["contexto"] = None
            return True
        novo = _checar_mudanca_assunto(entrada, ctx)
        if novo:
            emitir_resultado(novo)
            return True
        cpf_limpo = re.sub(r'\D', '', entrada)
        if not cpf_basico_valido(cpf_limpo):
            bot_falar(CPF_INVALIDO_MSG)
            return True
        bot_falar(confirmar_pagamento_por_cpf(cpf_limpo))
        estado["contexto"] = None
        return True

    # Aguardando o CPF apenas para CONSULTAR status/saldo (CRUD - READ).
    # Nunca altera o pedido — usado por 'status do pagamento' e 'quanto devo'.
    if ctx == "aguardando_cpf_consulta":
        if texto in {"sair","cancelar","n","nao","não"}:
            bot_falar("Sem problemas, cancelei a consulta.")
            estado["contexto"] = None
            return True
        novo = _checar_mudanca_assunto(entrada, ctx)
        if novo:
            emitir_resultado(novo)
            return True
        cpf_limpo = re.sub(r'\D', '', entrada)
        if not cpf_basico_valido(cpf_limpo):
            bot_falar(CPF_INVALIDO_MSG)
            return True
        bot_falar(consultar_pedido_por_cpf(cpf_limpo))
        estado["contexto"] = None
        return True

    # Aguardando dados de cartão de crédito
    # (Formulário crítico: só sai com 'sair'/'cancelar' explícito — ver
    # CONTEXTOS_CRITICOS — para não perder o fluxo de pagamento no meio.)
    if ctx == "credito":
        if texto in {"sair","cancelar","n","nao","não"}:
            bot_falar("Sem problemas, cancelei o pagamento no crédito.")
            estado["contexto"] = None
            return True
        novo = _checar_mudanca_assunto(entrada, ctx)
        if novo: emitir_resultado(novo); return True
        tem_bandeira = any(b in texto for b in ["visa","master","mastercard"])
        tem_parcela  = re.search(r'(?<!\w)\d{1,2}\s*(x|vez|vezes|parcela)(?!\w)', texto)
        if not (tem_bandeira and tem_parcela):
            bot_falar("Informe a bandeira e as parcelas. Ex: Visa, 3x.")
            return True
        bot_falar("Dados recebidos para simulação. Em um sistema real, o próximo passo seria o checkout seguro.")
        estado["contexto"] = None
        return True

    # Aguardando dados de débito/parcelamento (também formulário crítico)
    if ctx in {"parcela","debito"}:
        if texto in {"sair","cancelar","n","nao","não"}:
            bot_falar("Sem problemas, cancelei essa forma de pagamento.")
            estado["contexto"] = None
            return True
        novo = _checar_mudanca_assunto(entrada, ctx)
        if novo: emitir_resultado(novo); return True
        valido = any(b in texto for b in ["visa","master","mastercard"])
        if not valido:
            bot_falar("Preciso de bandeira válida (Visa/Master) e parcelas se aplicável.")
            return True
        bot_falar("Dados recebidos para simulação. Em um sistema real, o próximo passo seria a confirmação segura do pagamento.")
        estado["contexto"] = None
        return True

    # Aguardando confirmação de encerramento do atendimento
    if ctx == "confirmando_saida":
        classe = classificar_sim_nao(texto)
        if classe == "sim":
            bot_falar("Atendimento finalizado. Obrigado por falar com o Financeiro da FashionFlow.")
            estado["contexto"] = None
            estado["encerrar_sessao"] = True
            return True
        if classe == "nao":
            bot_falar("Ótimo, seguimos por aqui! Como posso ajudar?")
            estado["contexto"] = None
            return True
        novo = _checar_mudanca_assunto(entrada, ctx)
        if novo:
            emitir_resultado(novo)
            return True
        bot_falar("Só para confirmar: deseja mesmo encerrar o atendimento? (s/n)")
        return True

    # Aguardando sim/não para alguma pergunta anterior
    classe_sim_nao = classificar_sim_nao(texto)
    if ctx and classe_sim_nao:
        if classe_sim_nao == "sim":
            if ctx == "conciliacao_pagamento":
                # O cliente já pagou (banco confirmou) -> CRUD real (UPDATE).
                bot_falar("Perfeito, vou verificar o pagamento do seu pedido.")
                bot_falar("Pode me informar o CPF usado na compra?")
                estado["contexto"] = "aguardando_cpf_pagamento"
                return True
            if ctx in {"status_pagamento", "saldo_devedor"}:
                # Apenas consulta -> CRUD READ, nunca altera o status.
                bot_falar("Pode me informar o CPF usado na compra?")
                estado["contexto"] = "aguardando_cpf_consulta"
                return True
            _responder_sim(ctx)
        else:
            bot_falar("Entendido. Operação cancelada. Como posso ajudar?")
        estado["contexto"] = None
        return True

    return False

def _checar_mudanca_assunto(entrada: str, ctx_atual: str) -> dict | None:
    """
    Verifica se o usuário mudou de assunto durante um contexto ativo.
    Regra universal: qualquer intenção forte (a busca no CSV encontrou algo
    além do fallback) ou um redirecionamento de setor pode interromper o
    contexto atual — EXCETO em formulários críticos (CONTEXTOS_CRITICOS),
    onde só uma saída explícita ('sair'/'cancelar') interrompe o fluxo.
    """
    if ctx_atual in CONTEXTOS_CRITICOS:
        return None
    texto_norm = expandir_girias(normalizar(entrada))
    redirecionamento = checar_redirecionamento(texto_norm)
    if redirecionamento:
        return redirecionamento
    r = buscar_resposta(entrada)
    tag = r.get("tag")
    if tag not in (None, "fallback", ctx_atual):
        return r
    return None

def _responder_sim(ctx: str):
    """Define a resposta do bot quando o usuário diz 'sim' em diferentes contextos."""
    dados_pix_demo = [
        "Dados de demonstração para Pix:",
        f"Chave CNPJ de demonstração: {CHAVE_PIX}",
        "Não realize pagamento real por estes dados nesta interface. Posso ajudar em algo mais?",
    ]
    respostas = {
        "pix":                 dados_pix_demo,
        "desconto":            dados_pix_demo,
        "calculo_concluido":   dados_pix_demo,
        "contestacao_fraude":  ["Esse caso precisa de análise humana do Financeiro. Não compartilhe dados completos do cartão por aqui."],
        "reembolso":           ["Ainda não emito relatório ou portal de auditoria nesta interface. Posso orientar sobre prazos e procedimento de reembolso."],
        "atendimento_humano":  ["Esse caso precisa de análise humana do Financeiro. Nesta interface, vou apenas sinalizar essa necessidade."],
        "reclamacoes":         ["Sinto muito de novo. Esse caso precisa de atenção humana do Financeiro, e vou apenas sinalizar essa necessidade por aqui."],
    }
    for msg in respostas.get(ctx, ["Perfeito! Como posso te ajudar agora?"]):
        bot_falar(msg)
    if ctx in {"atendimento_humano", "reclamacoes"}:
        estado["conectado_humano"] = True
        bot_falar("Necessidade de atendimento humano sinalizada. Se quiser, posso continuar te ajudando por aqui — é só digitar 'voltar'.")

def limpar_conversa():
    """
    Equivalente a um '/clear': reinicia o estado da conversa (contexto,
    contadores e histórico) sem encerrar o programa nem apagar o log
    salvo em disco — só a memória local da sessão atual é resetada.
    """
    estado["contexto"] = None
    estado["tentativas_valor"] = 0
    estado["percentual_pendente"] = None
    estado["pagamento_pendente_pix"] = False
    estado["cpf_pendente"] = None
    estado["sem_entender"] = 0
    estado["conectado_humano"] = False
    estado["historico"].clear()
    estado["historico_recente"].clear()
    estado["mem_repeticao"].clear()
    if not MODO_WEB:
        os.system("cls" if os.name == "nt" else "clear")
        print(f"{CYAN}{'─'*60}{RESET}")
        print(f"{CYAN}     {BOLD}🌟 CHATBOT FINANCEIRO FASHIONFLOW 🌟{RESET}")
        print(f"{CYAN}{'─'*60}{RESET}\n")
    bot_falar("Conversa limpa! Vamos começar de novo. Como posso te ajudar com o financeiro?", digitar=False)

def mostrar_ajuda():
    """Guia rápido do que o Bot Financeiro sabe fazer e quais comandos existem."""
    linhas = [
        "",
        "Sou o assistente do Financeiro da FashionFlow. Cuido de:",
        "- Pagamento (Pix, cartão de crédito/débito, boleto)",
        "- Cobrança duplicada ou valor incorreto",
        "- Reembolso, estorno e nota fiscal",
        "- Cálculo de desconto, juros e parcelamento",
        "- Status de pagamento e confirmação por CPF",
        "- Negociação de dívida",
        "",
        "Atalhos do menu (digite o número ou a palavra):",
    ]
    vistos = set()
    for chave, destino in MENU_FINANCEIRO.items():
        if destino not in vistos:
            vistos.add(destino)
            linhas.append(f"  {chave} — {destino}")
    linhas += [
        "",
        "Comandos especiais:",
        "  'repete' — repete a última resposta",
        "  'limpar conversa' — reinicia o atendimento do zero",
        "  'atendente' — fala com um humano a qualquer momento",
        "  'sair' — encerra o atendimento (com confirmação)",
    ]
    bot_falar("\n".join(linhas), digitar=False)

def emitir_resultado(resultado: dict) -> bool:
    """
    Exibe a resposta e, se houver pergunta_seguinte (ou contexto_manual),
    ativa o contexto correspondente.

    Confirmação de encerramento (Item 2): isso é centralizado AQUI —
    e não em processar_intencao — porque o resultado de 'sair' também
    pode chegar por outros caminhos, como uma quebra de contexto no meio
    de uma conversa (_checar_mudanca_assunto). Se qualquer um desses
    caminhos deixasse o encerrar=True passar direto, o bot diria
    'Atendimento finalizado' sem realmente encerrar a sessão.
    """
    if resultado.get("encerrar"):
        bot_falar("Tem certeza que deseja encerrar o atendimento? (s/n)")
        estado["contexto"] = "confirmando_saida"
        estado["sem_entender"] = 0
        return True

    bot_falar(resultado["resposta"])
    if resultado.get("pergunta_seguinte"):
        if not MODO_WEB:
            time.sleep(0.2)
        bot_falar(resultado["pergunta_seguinte"])
        estado["contexto"] = resultado["tag"]
    elif resultado.get("contexto_manual"):
        estado["contexto"] = resultado["tag"]
    else:
        estado["contexto"] = None
    return True

def processar_intencao(entrada: str) -> bool:
    """
    Busca a intenção no CSV e responde. Conta erros de compreensão e oferece
    transferência para atendente humano após 3 falhas seguidas.
    """
    resultado = buscar_resposta(entrada)
    continuar = emitir_resultado(resultado)

    if resultado["tag"] != "fallback":
        estado["sem_entender"] = 0
    else:
        estado["sem_entender"] += 1
        if estado["sem_entender"] >= 3:
            bot_falar("Percebi que suas dúvidas demandam atenção personalizada.")
            bot_falar("Gostaria que eu sinalizasse a necessidade de atendimento humano do Financeiro? (s/n)")
            estado["contexto"] = "atendimento_humano"
            estado["sem_entender"] = 0
    return continuar

def processar_mensagem(entrada: str) -> None:
    """Processa uma mensagem usando o estado ativo, para terminal ou web."""
    if not entrada:
        return

    texto = expandir_girias(normalizar(entrada))
    registrar_log("Você", entrada)
    estado["historico"].append({"quem": "usuario", "msg": entrada})

    if texto in COMANDOS_REPETIR:
        msgs = estado["historico_recente"] or estado["mem_repeticao"]
        if msgs:
            for msg in msgs:
                if MODO_WEB:
                    estado.setdefault("_saida", []).append(msg)
                else:
                    time.sleep(0.2)
                    print(f"{GREEN}Bot (Repetindo): {msg}{RESET}")
        else:
            if MODO_WEB:
                estado.setdefault("_saida", []).append("Não há mensagens para repetir.")
            else:
                print(f"{YELLOW}Bot: Não há mensagens para repetir.{RESET}")
        return

    if texto in COMANDOS_LIMPAR:
        limpar_conversa()
        return

    if texto in COMANDOS_AJUDA:
        mostrar_ajuda()
        return

    if texto in {"confirmar pagamento", "confirmar pagamento por cpf", "paguei e nao constou", "paguei e não constou"}:
        bot_falar("Perfeito, vou verificar o pagamento do seu pedido.")
        bot_falar("Pode me informar o CPF usado na compra?")
        estado["contexto"] = "aguardando_cpf_pagamento"
        estado["sem_entender"] = 0
        return

    estado["mem_repeticao"] = list(estado["historico_recente"])
    estado["historico_recente"].clear()

    if estado["conectado_humano"]:
        if texto in COMANDOS_VOLTAR_BOT:
            estado["conectado_humano"] = False
            bot_falar("Ok, voltei! Como posso te ajudar com o financeiro?")
        else:
            bot_falar(
                "A necessidade de atendimento humano já foi sinalizada. "
                "Se quiser voltar a falar comigo por aqui, digite 'voltar'."
            )
        return

    if estado["contexto"] is None:
        redirecionamento = checar_redirecionamento(texto)
        if redirecionamento:
            emitir_resultado(redirecionamento)
            return

    if estado["contexto"] not in CONTEXTOS_CRITICOS:
        resultado_calc = processar_calculo(entrada, texto)
        if resultado_calc:
            emitir_resultado(resultado_calc)
            return

    if processar_contexto(entrada, texto):
        return

    processar_intencao(entrada)

# ─────────────────────────────────────────────────────────────
# INICIALIZAÇÃO E LOOP PRINCIPAL
# ─────────────────────────────────────────────────────────────

def run_chatbot():
    """Ponto de entrada do Chatbot Financeiro FashionFlow."""
    global intencoes

    try:
        intencoes = carregar_intencoes()
    except FileNotFoundError:
        print(f"{RED}❌ ERRO: Arquivo '{ARQUIVO_CSV}' não encontrado.{RESET}")
        sys.exit(1)

    registrar_log("Sistema", f"=== Nova sessão: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ===")

    print(f"{CYAN}{'─'*60}{RESET}")
    print(f"{CYAN}     {BOLD}🌟 CHATBOT FINANCEIRO FASHIONFLOW 🌟{RESET}")
    print(f"{CYAN}{'─'*60}{RESET}")
    print(f"Loading: {YELLOW}Mapeando {len(intencoes)} intenções do CSV... {GREEN}Pronto!{RESET}\n")
    print(f"{GREEN}Bot: Olá! Como posso te ajudar com o financeiro hoje?{RESET}\n")

    while True:
        try:
            entrada = input(f"{BOLD}Você: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            bot_falar("Atendimento finalizado preventivamente. Até logo! 👋")
            break

        if not entrada:
            continue

        texto = expandir_girias(normalizar(entrada))
        registrar_log("Você", entrada)
        estado["historico"].append({"quem": "usuario", "msg": entrada})

        # Comando para repetir a última resposta
        if texto in COMANDOS_REPETIR:
            msgs = estado["historico_recente"] or estado["mem_repeticao"]
            if msgs:
                for m in msgs: time.sleep(0.2); print(f"{GREEN}Bot (Repetindo): {m}{RESET}")
            else:
                print(f"{YELLOW}Bot: Não há mensagens para repetir.{RESET}")
            continue

        # Comando para limpar a conversa (equivalente a um '/clear')
        if texto in COMANDOS_LIMPAR:
            limpar_conversa()
            continue

        # Comando de ajuda: guia rápido do que o bot faz
        if texto in COMANDOS_AJUDA:
            mostrar_ajuda()
            continue

        estado["mem_repeticao"] = list(estado["historico_recente"])
        estado["historico_recente"].clear()

        # 0. Handoff para humano (Bug corrigido): enquanto o cliente está
        #    "na fila" com um atendente, o bot não finge que está tudo
        #    normal — ele avisa a situação e só volta a atender se o
        #    cliente pedir explicitamente.
        if estado["conectado_humano"]:
            if texto in COMANDOS_VOLTAR_BOT:
                estado["conectado_humano"] = False
                bot_falar("Ok, voltei! Como posso te ajudar com o financeiro?")
            else:
                bot_falar(
                    "A necessidade de atendimento humano já foi sinalizada. "
                    "Se quiser voltar a falar comigo por aqui, digite 'voltar'."
                )
            continue

        # 1. Roteamento entre setores: se o assunto for de outro grupo do
        #    FashionFlow (Vendas, Estoque, Produção, Logística, Compras),
        #    o Financeiro nunca tenta adivinhar — sempre orienta o setor certo.
        if estado["contexto"] is None:
            redirecionamento = checar_redirecionamento(texto)
            if redirecionamento:
                emitir_resultado(redirecionamento)
                continue

        # 2. Prioridade máxima: intercepta cálculos financeiros — mas nunca
        #    durante um contexto crítico (ex: preenchendo bandeira/parcelas
        #    do cartão), para não deixar o cálculo "furar" o formulário.
        if estado["contexto"] not in CONTEXTOS_CRITICOS:
            resultado_calc = processar_calculo(entrada, texto)
            if resultado_calc:
                emitir_resultado(resultado_calc)
                continue

        # 3. Verifica se há um contexto ativo aguardando resposta
        if processar_contexto(entrada, texto):
            if estado["encerrar_sessao"]:
                break
            continue

        # 4. Busca normal na base de conhecimento do CSV
        processar_intencao(entrada)
        if estado["encerrar_sessao"]:
            break

    registrar_log("Sistema", "=== Sessão encerrada de forma limpa ===")


if __name__ == "__main__":
    run_chatbot()
