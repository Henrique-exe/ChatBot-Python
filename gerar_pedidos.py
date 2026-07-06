"""
gerar_pedidos.py — Gera a tabela pedidos_vendas.csv usada pelo módulo
Financeiro para confirmar pagamentos por CPF (CRUD - UPDATE).

Em produção, esta tabela seria criada pelo módulo de Vendas (CREATE).
Aqui geramos uma base de exemplo para testar o fluxo do Financeiro de
forma isolada, sem depender do código de outro grupo.
"""

import csv

FIELDNAMES = ["id", "cpf", "produto", "valor", "status"]

pedidos = [
    {"id": "001", "cpf": "123.456.789-00", "produto": "Jaqueta de couro M", "valor": "250.00", "status": "Aguardando Pagamento"},
    {"id": "002", "cpf": "987.654.321-00", "produto": "Calça sarja G",      "valor": "180.00", "status": "Pago"},
    {"id": "003", "cpf": "111.222.333-00", "produto": "Blusa P",           "valor": "90.00",  "status": "Cancelado"},
    {"id": "004", "cpf": "222.333.444-55", "produto": "Camisa social M",   "valor": "135.00", "status": "Aguardando Pagamento"},
]

with open("pedidos_vendas.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
    writer.writeheader()
    writer.writerows(pedidos)

print(f"Arquivo pedidos_vendas.csv gerado com {len(pedidos)} pedidos de exemplo.")
