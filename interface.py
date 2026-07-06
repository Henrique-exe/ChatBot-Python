"""
chatbot_gui.py — Interface gráfica do Chatbot Financeiro FashionFlow
─────────────────────────────────────────────────────────────────────
Este arquivo NÃO altera chatbot_financeiro.py, gerar_pedidos.py nem
nenhum outro arquivo do projeto. Ele importa o módulo original e reusa
100% da lógica de atendimento já pronta:

    - roteamento entre setores (Vendas, Estoque, Produção, Logística, Compras)
    - cálculo de desconto / juros / parcelamento
    - consulta e confirmação de pagamento por CPF (READ / UPDATE no CSV)
    - contexto de conversa, atalhos do menu, comandos especiais, etc.

A única coisa que este arquivo faz de diferente é trocar a "camada de
saída": em vez de o bot escrever no terminal (print/input), a resposta
aparece como um balão de chat nesta janela. Isso é feito substituindo,
em tempo de execução, a função `bot_falar` do módulo importado — o
arquivo chatbot_financeiro.py em si permanece intocado no disco.

COMO USAR
─────────
1) Coloque este arquivo na MESMA pasta de:
       chatbot_financeiro.py
       base_conhecimento.csv   (renomeie o CSV enviado para este nome —
                                 o bot procura exatamente por
                                 "base_conhecimento.csv")
       pedidos_vendas.csv
2) Rode no terminal do VS Code:
       python chatbot_gui.py
   (Tkinter já vem instalado com o Python — nada a instalar.)
"""

import tkinter as tk
from tkinter import font as tkfont

import chatbot_financeiro as cf


# ─────────────────────────────────────────────────────────────
# TEMA VISUAL — paleta inspirada em "extrato financeiro" (fundo grafite,
# verde-cédula para o bot, azul-aço para o cliente, dourado para avisos).
# ─────────────────────────────────────────────────────────────
BG_APP        = "#0D141B"
BG_SIDEBAR    = "#121C26"
BG_HEADER     = "#111A23"
BG_INPUT      = "#182432"
BUBBLE_BOT    = "#14281F"
BORDER_BOT    = "#2ECC91"
BUBBLE_USER   = "#17263A"
BORDER_USER   = "#5B8CFF"
BUBBLE_SYS    = "#2A2112"
BORDER_SYS    = "#E8B94A"
TEXT_MAIN     = "#E9EDF2"
TEXT_MUTED    = "#9AA7B6"
ACCENT        = "#2ECC91"
ACCENT_GOLD   = "#E8B94A"
DIVIDER       = "#263342"
BTN_BG        = "#1B2A38"
BTN_BG_HOVER  = "#263B4D"

FONT_UI    = ("Segoe UI", 11)
FONT_UI_B  = ("Segoe UI", 11, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 19, "bold")
FONT_SUB   = ("Segoe UI", 10)
FONT_SIDE_TITLE = ("Segoe UI", 10, "bold")

MENSAGEM_INICIAL = (
    "Olá! Sou o atendimento financeiro da FashionFlow. Posso ajudar com "
    "descontos, pagamentos, parcelamentos e recibos. O que vamos resolver hoje?"
)

MENSAGEM_VAZIA = (
    "Opa, sua mensagem veio em branco. Me diga se deseja calcular desconto, "
    "confirmar pagamento ou consultar formas de pagamento."
)

ATALHOS_PRINCIPAIS = [
    ("Calcular desconto", "calcular desconto"),
    ("Confirmar pagamento", "paguei e nao constou"),
    ("Formas de pagamento", "formas de pagamento"),
    ("Parcelamento", "parcelamento"),
    ("Recibo", "comprovantes de pagamento"),
    ("Limpar conversa", "limpar conversa"),
]


# ─────────────────────────────────────────────────────────────
# CHAT ROLÁVEL COM BALÕES (Canvas + Frame interno)
# ─────────────────────────────────────────────────────────────
class ChatArea(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_APP)

        self.canvas = tk.Canvas(self, bg=BG_APP, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=BG_APP)

        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)       # Windows/Mac
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units"))  # Linux
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units"))

    def _on_inner_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.inner_id, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_bubble(self, texto: str, align: str, bg: str, border: str, label: str):
        row = tk.Frame(self.inner, bg=BG_APP)
        row.pack(fill="x", padx=20, pady=6)

        bubble = tk.Frame(row, bg=bg, highlightbackground=border, highlightcolor=border,
                           highlightthickness=1, bd=0)

        tk.Label(bubble, text=label, font=FONT_SMALL, bg=bg, fg=border
                 ).pack(anchor="w", padx=16, pady=(10, 0))
        tk.Label(bubble, text=texto, font=FONT_UI, bg=bg, fg=TEXT_MAIN,
                  justify="left", wraplength=560, anchor="w"
                 ).pack(anchor="w", padx=16, pady=(3, 12))

        bubble.pack(side="right" if align == "right" else "left", anchor="e" if align == "right" else "w")

        self.after(10, self._ir_para_o_fim)

    def _ir_para_o_fim(self):
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def limpar(self):
        for w in self.inner.winfo_children():
            w.destroy()


# ─────────────────────────────────────────────────────────────
# APLICAÇÃO PRINCIPAL
# ─────────────────────────────────────────────────────────────
class ChatbotFinanceiroApp:
    # Atalhos exibidos na barra lateral (reaproveita o MENU_FINANCEIRO
    # já definido em chatbot_financeiro.py — nada digitado à mão aqui)
    def __init__(self, root: tk.Tk):
        self.root = root
        self.sessao_encerrada = False

        root.title("FashionFlow — Módulo Financeiro")
        root.geometry("1040x700")
        root.minsize(880, 580)
        root.configure(bg=BG_APP)

        self.base_ok = self._carregar_base_conhecimento()
        self._montar_layout()
        self._substituir_bot_falar()

        if self.base_ok:
            self._iniciar_sessao()

    # ---------- carregamento da base (READ, sem alterar arquivos) ----------
    def _carregar_base_conhecimento(self) -> bool:
        try:
            cf.intencoes = cf.carregar_intencoes()
            return True
        except FileNotFoundError:
            return False

    # ---------- troca a "saída" do bot: terminal -> balão de chat ----------
    def _substituir_bot_falar(self):
        def bot_falar_gui(texto, digitar=True):
            # Mesmo comportamento de log/histórico do original,
            # só sem a animação de digitação no terminal.
            cf.registrar_log("Bot", texto)
            cf.estado["historico"].append({"quem": "bot", "msg": texto})
            cf.estado["historico_recente"].append(texto)
            self.chat.add_bubble(texto, "left", BUBBLE_BOT, BORDER_BOT, "FINANCEIRO")

        cf.bot_falar = bot_falar_gui  # só reatribui o atributo do módulo em memória

    # ---------- layout ----------
    def _montar_layout(self):
        # Cabeçalho
        header = tk.Frame(self.root, bg=BG_HEADER, height=82)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        title_box = tk.Frame(header, bg=BG_HEADER)
        title_box.pack(side="left", padx=24, pady=12)

        tk.Label(title_box, text="FashionFlow — Módulo Financeiro",
                 font=FONT_TITLE, bg=BG_HEADER, fg=TEXT_MAIN
                 ).pack(anchor="w")
        tk.Label(title_box,
                 text="Atendimento de descontos, pagamentos, parcelamentos e recibos",
                 font=FONT_SUB, bg=BG_HEADER, fg=TEXT_MUTED
                 ).pack(anchor="w", pady=(3, 0))

        self.status_lbl = tk.Label(header, text="", font=FONT_SMALL, bg=BG_HEADER, fg=ACCENT)
        self.status_lbl.pack(side="right", padx=24)

        tk.Frame(self.root, bg=DIVIDER, height=1).pack(fill="x")

        # Corpo: sidebar + chat
        body = tk.Frame(self.root, bg=BG_APP)
        body.pack(fill="both", expand=True)

        self._montar_sidebar(body)

        chat_col = tk.Frame(body, bg=BG_APP)
        chat_col.pack(side="left", fill="both", expand=True)

        self.chat = ChatArea(chat_col)
        self.chat.pack(fill="both", expand=True)

        self._montar_barra_input(chat_col)

        if not self.base_ok:
            self._mostrar_erro_base()

    def _montar_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=BG_SIDEBAR, width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="AÇÕES FINANCEIRAS", font=FONT_SIDE_TITLE,
                 bg=BG_SIDEBAR, fg=ACCENT
                 ).pack(anchor="w", padx=20, pady=(22, 4))
        tk.Label(sidebar, text="Escolha um fluxo para apresentar",
                 font=FONT_SMALL, bg=BG_SIDEBAR, fg=TEXT_MUTED,
                 wraplength=210, justify="left"
                 ).pack(anchor="w", padx=20, pady=(0, 12))

        for texto_botao, mensagem in ATALHOS_PRINCIPAIS:
            self._botao_atalho(
                sidebar,
                texto_botao,
                mensagem,
                destrutivo=(texto_botao == "Limpar conversa"),
                principal=True,
            )

        tk.Frame(sidebar, bg=DIVIDER, height=1).pack(fill="x", padx=20, pady=18)

        tk.Label(sidebar, text="APOIO", font=FONT_SIDE_TITLE, bg=BG_SIDEBAR, fg=TEXT_MUTED
                 ).pack(anchor="w", padx=20, pady=(0, 8))

        self._botao_atalho(sidebar, "Ajuda", "ajuda")
        self._botao_atalho(sidebar, "Repetir última resposta", "repete")
        self._botao_atalho(sidebar, "Encerrar atendimento", "sair", destrutivo=True)

        self.reiniciar_btn = None  # criado sob demanda quando a sessão terminar

    def _botao_atalho(self, parent, texto_botao, mensagem_enviada, destrutivo=False, principal=False):
        btn = tk.Button(
            parent, text=texto_botao, font=(FONT_UI_B if principal else FONT_UI), anchor="w",
            bg=BTN_BG, fg=(ACCENT_GOLD if destrutivo else TEXT_MAIN),
            activebackground=BTN_BG_HOVER, activeforeground=TEXT_MAIN,
            relief="flat", bd=0, padx=16, pady=(11 if principal else 8), cursor="hand2",
            command=lambda m=mensagem_enviada: self._enviar(texto_forcado=m),
        )
        btn.pack(fill="x", padx=16, pady=(4 if principal else 2))
        btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=BTN_BG_HOVER))
        btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=BTN_BG))
        return btn

    def _montar_barra_input(self, parent):
        tk.Frame(parent, bg=DIVIDER, height=1).pack(fill="x")
        barra = tk.Frame(parent, bg=BG_INPUT)
        barra.pack(fill="x")

        self.entry = tk.Entry(
            barra, font=FONT_UI, bg=BG_INPUT, fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN, relief="flat",
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(20, 10), pady=16, ipady=8)
        self.entry.bind("<Return>", lambda e: self._enviar())
        self.entry.focus_set()

        self.btn_enviar = tk.Button(
            barra, text="Enviar", font=FONT_UI_B, bg=ACCENT, fg="#0B1410",
            activebackground="#27b881", activeforeground="#0B1410",
            relief="flat", bd=0, padx=18, cursor="hand2",
            command=lambda: self._enviar(),
        )
        self.btn_enviar.pack(side="right", padx=(0, 20), pady=16, ipady=2)

    def _mostrar_erro_base(self):
        self.entry.configure(state="disabled")
        self.btn_enviar.configure(state="disabled")
        self.chat.add_bubble(
            "Não encontrei o arquivo 'base_conhecimento.csv' na pasta deste "
            "programa. Confirme se ele está na mesma pasta de chatbot_gui.py "
            "e chatbot_financeiro.py (o arquivo que você enviou está com o "
            "nome 'base_conhecimento__1_.csv' — renomeie para "
            "'base_conhecimento.csv') e abra o programa novamente.",
            "left", BUBBLE_SYS, BORDER_SYS, "SISTEMA",
        )
        self.status_lbl.configure(text="● base indisponível", fg=BORDER_SYS)

    # ---------- ciclo de vida da sessão ----------
    def _iniciar_sessao(self):
        cf.registrar_log("Sistema", f"=== Nova sessão (GUI): "
                          f"{cf.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ===")
        self.status_lbl.configure(text=f"● {len(cf.intencoes)} intenções carregadas")
        self.chat.add_bubble(
            MENSAGEM_INICIAL,
            "left", BUBBLE_BOT, BORDER_BOT, "FINANCEIRO",
        )

    def _reiniciar_sessao(self):
        cf.registrar_log("Sistema", "=== Sessão encerrada de forma limpa (GUI) ===")
        # Restaura o estado global do chatbot para os valores iniciais,
        # exatamente como no dicionário original do módulo.
        cf.estado.update({
            "contexto": None,
            "tentativas_valor": 0,
            "percentual_pendente": None,
            "cpf_pendente": None,
            "sem_entender": 0,
            "historico": [],
            "historico_recente": [],
            "mem_repeticao": [],
            "encerrar_sessao": False,
            "conectado_humano": False,
        })
        self.sessao_encerrada = False
        self.chat.limpar()
        self.entry.configure(state="normal")
        self.btn_enviar.configure(state="normal")
        if self.reiniciar_btn is not None:
            self.reiniciar_btn.destroy()
            self.reiniciar_btn = None
        self._iniciar_sessao()
        self.entry.focus_set()

    def _encerrar_sessao_ui(self):
        cf.registrar_log("Sistema", "=== Sessão encerrada de forma limpa ===")
        self.sessao_encerrada = True
        self.entry.configure(state="disabled")
        self.btn_enviar.configure(state="disabled")
        self.status_lbl.configure(text="● atendimento encerrado", fg=TEXT_MUTED)
        self.reiniciar_btn = tk.Button(
            self.root, text="Iniciar novo atendimento", font=FONT_UI_B,
            bg=ACCENT, fg="#0B1410", activebackground="#27b881",
            relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
            command=self._reiniciar_sessao,
        )
        self.reiniciar_btn.place(relx=0.5, rely=0.965, anchor="s")

    # ---------- envio de mensagem: espelha o loop de run_chatbot() ----------
    def _enviar(self, texto_forcado: str = None):
        if self.sessao_encerrada or not self.base_ok:
            return

        entrada = texto_forcado if texto_forcado is not None else self.entry.get().strip()
        if not entrada:
            self.chat.add_bubble(MENSAGEM_VAZIA, "left", BUBBLE_SYS, BORDER_SYS, "SISTEMA")
            return
        if texto_forcado is None:
            self.entry.delete(0, tk.END)

        self.chat.add_bubble(entrada, "right", BUBBLE_USER, BORDER_USER, "VOCÊ")

        try:
            self._processar_entrada(entrada)
        except Exception:
            self.chat.add_bubble(
                "Oxente, tive uma instabilidade aqui na tela. Tente de novo em instantes.",
                "left", BUBBLE_SYS, BORDER_SYS, "SISTEMA",
            )

    def _processar_entrada(self, entrada: str):
        texto = cf.expandir_girias(cf.normalizar(entrada))
        cf.registrar_log("Você", entrada)
        cf.estado["historico"].append({"quem": "usuario", "msg": entrada})

        # Comando para repetir a última resposta
        if texto in cf.COMANDOS_REPETIR:
            msgs = cf.estado["historico_recente"] or cf.estado["mem_repeticao"]
            if msgs:
                for m in msgs:
                    self.chat.add_bubble(m, "left", BUBBLE_BOT, BORDER_BOT, "FINANCEIRO (repetindo)")
            else:
                self.chat.add_bubble("Não há mensagens para repetir.", "left", BUBBLE_SYS, BORDER_SYS, "SISTEMA")
            return

        # Comando para limpar a conversa
        if texto in cf.COMANDOS_LIMPAR:
            cf.limpar_conversa()
            self.chat.limpar()
            self.chat.add_bubble(MENSAGEM_INICIAL, "left", BUBBLE_BOT, BORDER_BOT, "FINANCEIRO")
            return

        # Comando de ajuda
        if texto in cf.COMANDOS_AJUDA:
            cf.mostrar_ajuda()
            return

        cf.estado["mem_repeticao"] = list(cf.estado["historico_recente"])
        cf.estado["historico_recente"].clear()

        # Handoff para humano
        if cf.estado["conectado_humano"]:
            if texto in cf.COMANDOS_VOLTAR_BOT:
                cf.estado["conectado_humano"] = False
                cf.bot_falar("Ok, voltei! Como posso te ajudar com o financeiro?")
            else:
                cf.bot_falar(
                    "Você já foi encaminhado para um atendente humano e "
                    "está na fila de espera. Se quiser voltar a falar "
                    "comigo enquanto aguarda, digite 'voltar'."
                )
            return

        # Roteamento entre setores
        if cf.estado["contexto"] is None:
            redirecionamento = cf.checar_redirecionamento(texto)
            if redirecionamento:
                cf.emitir_resultado(redirecionamento)
                return

        # Cálculos financeiros (prioridade máxima, exceto em contexto crítico)
        if cf.estado["contexto"] not in cf.CONTEXTOS_CRITICOS:
            resultado_calc = cf.processar_calculo(entrada, texto)
            if resultado_calc:
                cf.emitir_resultado(resultado_calc)
                return

        # Contexto ativo aguardando resposta
        if cf.processar_contexto(entrada, texto):
            if cf.estado["encerrar_sessao"]:
                self._encerrar_sessao_ui()
            return

        # Busca normal na base de conhecimento
        cf.processar_intencao(entrada)
        if cf.estado["encerrar_sessao"]:
            self._encerrar_sessao_ui()


def main():
    root = tk.Tk()
    try:
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10)
    except tk.TclError:
        pass
    ChatbotFinanceiroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
