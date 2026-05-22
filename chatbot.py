import re
import time
import sys
import csv


def carregar_intencoes(caminho_csv="base_conhecimento.csv"):
    intencoes = []

    with open(caminho_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            palavras_lista = [p.strip() for p in row["palavras"].split(",")]

            regex_compiladas = [
                re.compile(r'(?<!\w)' + re.escape(p.lower()) + r'(?!\w)')
                for p in palavras_lista if p
            ]

            intencao = {
                "tag": row["tag"],
                "prioridade": int(row["prioridade"]),
                "regex_palavras": regex_compiladas,
                "resposta": row["resposta"],
            }
            if row["pergunta_seguinte"]:
                intencao["pergunta_seguinte"] = row["pergunta_seguinte"]
            if row["encerrar"] == "True":
                intencao["encerrar"] = True

            intencoes.append(intencao)

    return sorted(intencoes, key=lambda x: x["prioridade"])


intencoes = carregar_intencoes("base_conhecimento.csv")


def buscar_resposta(mensagem):
    mensagem = mensagem.lower()

    for intencao in intencoes:
        for padrao in intencao["regex_palavras"]:
            if padrao.search(mensagem):
                return intencao

    return {
        "resposta": "Desculpe, não entendi. Pode tentar explicar de outra forma?",
        "encerrar": False
    }


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


print("--- Chatbot FashionFlow Iniciado ---")
print(f"✅ {len(intencoes)} intenções carregadas do CSV.\n")

contexto_pergunta = None
cep_armazenado = None

while True:
    entrada = input("Você: ").strip()
    if not entrada:
        continue

    entrada_lower = entrada.lower()

    if contexto_pergunta == "aguardando_cep":
        cep_limpo = entrada.replace("-", "").replace(" ", "")
        if cep_limpo.isdigit() and len(cep_limpo) == 8:
            cep_armazenado = cep_limpo
            bot_falar(f"CEP {entrada} validado e armazenado com sucesso! 📍")
            bot_falar("O prazo estimado é de 3 a 7 dias úteis.")
            contexto_pergunta = None
            continue
        else:
            bot_falar("❌ CEP inválido.\nDigite um CEP válido com 8 números.")
            continue

    if contexto_pergunta == "credito":
        bot_falar(f"Perfeito! Registrei a opção: '{entrada}'.")
        bot_falar("Redirecionando para o ambiente seguro de pagamento 💳")
        contexto_pergunta = None
        continue

    if contexto_pergunta and entrada_lower in ["s", "sim", "n", "nao", "não"]:
        if entrada_lower in ["s", "sim"]:
            if contexto_pergunta in ["pix", "desconto", "pagamento_recusado"]:
                bot_falar("Aqui está sua chave Pix👇")
                bot_falar("00020101021126580014br.gov.bcb.pix0136fashionflow")
                bot_falar("Pagamento aprovado instantaneamente! 💸")
                contexto_pergunta = None
                continue

            elif contexto_pergunta == "prazo_entrega":
                bot_falar("Digite seu CEP para calcular o prazo:")
                contexto_pergunta = "aguardando_cep"
                continue

            elif contexto_pergunta in ["cobranca_duplicada", "contestacao_fraude"]:
                bot_falar(
                    "Perfeito. Estou transferindo você para um especialista do nosso Setor Financeiro. Aguarde um instante... 🧑‍💻")
                contexto_pergunta = None
                continue

            elif contexto_pergunta == "alterar_pagamento":
                bot_falar(
                    "Solicitação recebida! Estamos processando o cancelamento do seu pedido atual para que você possa refazê-lo. ❌")
                contexto_pergunta = None
                continue

            elif contexto_pergunta in ["recusado_cartao_credito", "recusado_cartao_debito", "recusado_pix"]:
                resposta_formas = buscar_resposta("formas de pagamento")
                bot_falar(resposta_formas["resposta"])
                continue

            else:
                bot_falar("Entendido! Posso ajudar em algo mais?")
                contexto_pergunta = None
                continue

        elif entrada_lower in ["n", "nao", "não"]:
            bot_falar("Sem problemas! Como posso te ajudar agora?")
            contexto_pergunta = None
            continue

    resultado = buscar_resposta(entrada)
    bot_falar(resultado["resposta"])

    if "pergunta_seguinte" in {k: v for k, v in resultado.items() if v}:
        time.sleep(0.5)
        bot_falar(resultado["pergunta_seguinte"])
        contexto_pergunta = resultado["tag"]
    else:
        contexto_pergunta = None

    if resultado.get("encerrar"):
        break
