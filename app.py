from __future__ import annotations

import uuid
from threading import Lock

from flask import Flask, jsonify, render_template, request, session

import chatbot_financeiro as cf


app = Flask(__name__)
app.secret_key = "fashionflow-financeiro-web-local"

chat_lock = Lock()
SESSOES: dict[str, dict] = {}

WELCOME_MESSAGE = (
    "Olá! Sou o atendimento financeiro da FashionFlow. Posso ajudar com "
    "descontos, pagamentos, parcelamentos e recibos. O que vamos resolver hoje?"
)

EMPTY_MESSAGE = (
    "Opa, sua mensagem veio em branco. Me diga se deseja calcular desconto, "
    "confirmar pagamento ou consultar formas de pagamento."
)

GENERIC_ERROR = (
    "Oxente, tive uma instabilidade aqui na tela. Tente novamente em instantes."
)


def _load_base() -> None:
    if not cf.intencoes:
        cf.intencoes = cf.carregar_intencoes()


def _session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = str(uuid.uuid4())
        session["sid"] = sid
    return sid


def _get_state() -> dict:
    sid = _session_id()
    if sid not in SESSOES:
        SESSOES[sid] = cf.nova_sessao()
    return SESSOES[sid]


def _new_state() -> dict:
    sid = str(uuid.uuid4())
    session["sid"] = sid
    SESSOES[sid] = cf.nova_sessao()
    return SESSOES[sid]


def _as_messages(saida: list[str]) -> list[dict[str, str]]:
    return [{"sender": "bot", "text": texto} for texto in saida]


def _process_message(entrada: str) -> list[dict[str, str]]:
    state = _get_state()
    cf.estado = state
    cf.MODO_WEB = True
    state.setdefault("_saida", []).clear()

    cf.processar_mensagem(entrada)

    replies = list(state.get("_saida", []))
    state["_saida"].clear()

    if state.get("encerrar_sessao"):
        SESSOES[session["sid"]] = cf.nova_sessao()

    return _as_messages(replies)


@app.get("/")
def index():
    return render_template("index.html", welcome_message=WELCOME_MESSAGE)


@app.post("/api/message")
def api_message():
    data = request.get_json(silent=True) or {}
    entrada = str(data.get("message", "")).strip()
    if not entrada:
        return jsonify({"ok": True, "messages": [{"sender": "system", "text": EMPTY_MESSAGE}]})

    with chat_lock:
        try:
            _load_base()
            messages = _process_message(entrada)
            return jsonify({"ok": True, "messages": messages})
        except Exception:
            return jsonify({"ok": False, "messages": [{"sender": "system", "text": GENERIC_ERROR}]})


@app.post("/api/clear")
def api_clear():
    with chat_lock:
        _new_state()
    return jsonify({"ok": True, "messages": [{"sender": "bot", "text": WELCOME_MESSAGE}]})


if __name__ == "__main__":
    cf.MODO_WEB = True
    _load_base()
    app.run(host="127.0.0.1", port=5000, debug=False)
