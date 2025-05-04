import tkinter as tk
from tkinter import Scrollbar
import re

class BIOESLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("中文 BIOES 标注工具 （南理工）")
        self.root.configure(bg="#f5f5f5")
        self.root.geometry("1280x850")
        self.root.resizable(False, False)

        self.bioes_types = ['B', 'I', 'E', 'S', 'O']
        self.entity_types = ["FM", "Pd", "Po", "Pr", "Eq", "Co", "Sy", "Te", "Ti"]

        self.sentences = []
        self.current_index = 0
        self.tokens = []
        self.labels = []
        self.token_labels = []
        self.popup_menu = None

        self.assist_var = tk.BooleanVar()
        self.split_var = tk.BooleanVar()

        self._setup_ui()

    def _setup_ui(self):
        font = ("微软雅黑", 11)

        # 输入区
        tk.Label(self.root, text="请输入长文本：", bg="#f5f5f5", font=("微软雅黑", 12, "bold"))\
          .pack(anchor="w", padx=10)
        self.text_entry = tk.Text(self.root, height=5, width=110,
                                  font=font, wrap='word')
        self.text_entry.pack(padx=10, pady=5)

        # 控制区
        ctrl = tk.Frame(self.root, bg="#f5f5f5"); ctrl.pack(pady=5)
        tk.Checkbutton(ctrl, text="启用自动分句", variable=self.split_var,
                       font=font, bg="#f5f5f5").pack(side=tk.LEFT, padx=8)
        tk.Button(ctrl, text="加载下一句", command=self.load_next_sentence,
                  bg="#99c2ff", font=font).pack(side=tk.LEFT, padx=8)
        tk.Button(ctrl, text="重置", command=self.reset,
                  bg="#ffcccc", font=font).pack(side=tk.LEFT, padx=8)
        tk.Button(ctrl, text="生成 BIOES 标注", command=self.generate_output,
                  bg="#c1e1c1", font=font).pack(side=tk.LEFT, padx=8)

        # 实体管理
        mgr = tk.Frame(self.root, bg="#f5f5f5"); mgr.pack(pady=5)
        tk.Label(mgr, text="实体类型：", bg="#f5f5f5", font=font)\
          .pack(side=tk.LEFT)
        self.entity_entry = tk.Entry(mgr, width=10, font=font)
        self.entity_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(mgr, text="添加实体类型", command=self.add_entity_type,
                  bg="#ddeeff", font=font).pack(side=tk.LEFT, padx=5)
        tk.Button(mgr, text="删除实体类型", command=self.remove_entity_type,
                  bg="#ffe4b5", font=font).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(self.root, text="开启标注辅助（严格按照BIOES标准）", variable=self.assist_var,
                       bg="#f5f5f5", font=font).pack(pady=5)

        # Token 区（垂直滚动 + 自动换行）
        tok_sf = tk.Frame(self.root); tok_sf.pack(pady=10)
        self.token_canvas = tk.Canvas(tok_sf, width=1220, height=200,
                                      bg="#fff", highlightthickness=1,
                                      highlightbackground="#ccc")
        self.token_canvas.pack(side=tk.LEFT, fill="both", expand=True)
        vsb = Scrollbar(tok_sf, orient="vertical",
                        command=self.token_canvas.yview)
        vsb.pack(side=tk.RIGHT, fill="y")
        self.token_canvas.configure(yscrollcommand=vsb.set)
        self.token_frame = tk.Frame(self.token_canvas, bg="#fff")
        self.token_canvas.create_window((0, 0), window=self.token_frame, anchor="nw")
        self.token_frame.bind(
            "<Configure>",
            lambda e: self.token_canvas.configure(
                scrollregion=self.token_canvas.bbox("all")
            )
        )

        # 输出区
        tk.Label(self.root, text="输出结果（Token|||BIOES）：",
                 bg="#f5f5f5", font=("微软雅黑", 12, "bold"))\
          .pack(anchor="w", padx=10)
        out_f = tk.Frame(self.root); out_f.pack()
        self.output_text = tk.Text(out_f, height=10, width=110,
                                   font=font, wrap='word')
        self.output_text.pack(side=tk.LEFT)
        out_sb = Scrollbar(out_f, command=self.output_text.yview)
        out_sb.pack(side=tk.RIGHT, fill="y")
        self.output_text.config(yscrollcommand=out_sb.set)

    def reset(self):
        self.text_entry.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.sentences.clear(); self.current_index = 0
        self.tokens.clear(); self.labels.clear(); self.token_labels.clear()
        for w in self.token_frame.winfo_children():
            w.destroy()

    def split_sentences(self, text):
        t = re.sub(r'([。；;！!？?])', r'\1\n', text)
        t = re.sub(r'\)\s*', r')\n', t)
        return [s.strip() for s in t.split('\n') if s.strip()]

    def load_next_sentence(self):
        if not self.sentences:
            txt = self.text_entry.get("1.0", tk.END).strip()
            self.sentences = (self.split_sentences(txt)
                              if self.split_var.get() else [txt])
        if self.current_index < len(self.sentences):
            self.display_sentence(self.sentences[self.current_index])
            self.current_index += 1

    def display_sentence(self, sentence):
        for w in self.token_frame.winfo_children():
            w.destroy()
        self.tokens = list(sentence)
        self.labels = ["O"] * len(self.tokens)
        self.token_labels = []

        max_per_line = 20  # 每行不超过20个token，保证自动换行
        for i, ch in enumerate(self.tokens):
            row, col = divmod(i, max_per_line)
            lbl = tk.Label(self.token_frame,
                           text=ch,
                           relief="raised",
                           width=6, height=2,
                           font=("微软雅黑", 10),
                           bg="#eef7ff",
                           borderwidth=1)
            lbl.grid(row=row, column=col, padx=1, pady=1)
            lbl.bind("<Enter>", lambda e, idx=i: self.show_menu(e, idx))
            lbl.bind("<Button-1>", lambda e, idx=i: self.show_menu(e, idx))
            self.token_labels.append(lbl)

    def get_allowed_labels(self, idx):
        if not self.assist_var.get():
            return ["O"] + [f"{p}-{e}"
                            for p in ['B', 'I', 'E', 'S']
                            for e in self.entity_types]
        open_ent = None
        for j in range(idx):
            tag = self.labels[j]
            if tag.startswith("B-"):
                open_ent = tag[2:]
            elif tag == f"E-{open_ent}" or tag == "O":
                open_ent = None
        if open_ent:
            return [f"I-{open_ent}", f"E-{open_ent}"]
        else:
            return ["O"] + [f"{p}-{e}"
                            for p in ['B', 'I', 'E', 'S']
                            for e in self.entity_types]

    def show_menu(self, event, idx):
        if self.popup_menu:
            self.popup_menu.unpost()
        self.popup_menu = tk.Menu(self.root, tearoff=0)
        allowed = self.get_allowed_labels(idx)
        grouped = {}
        for lab in allowed:
            if lab == "O":
                self.popup_menu.add_command(
                    label="O",
                    command=lambda i=idx: self.set_label(i, "O")
                )
            else:
                pre, ent = lab.split("-")
                grouped.setdefault(pre, []).append(ent)
        for pre, ents in grouped.items():
            sub = tk.Menu(self.popup_menu, tearoff=0)
            for ent in ents:
                full = f"{pre}-{ent}"
                sub.add_command(
                    label=ent,
                    command=lambda i=idx, l=full: self.set_label(i, l)
                )
            self.popup_menu.add_cascade(label=pre, menu=sub)
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty() + event.widget.winfo_height()
        self.popup_menu.post(x, y)

    def set_label(self, idx, label):
        self.labels[idx] = label
        self.token_labels[idx].config(text=f"{self.tokens[idx]}\n{label}")
        if self.popup_menu:
            self.popup_menu.unpost()

    def generate_output(self):
        toks = ' '.join(self.tokens)
        labs = ' '.join(self.labels)
        self.output_text.insert(tk.END, f"{toks}|||{labs}\n")

    def add_entity_type(self):
        new = self.entity_entry.get().strip()
        if new and new not in self.entity_types:
            self.entity_types.append(new)
            self.entity_entry.delete(0, tk.END)

    def remove_entity_type(self):
        rm = self.entity_entry.get().strip()
        if rm in self.entity_types:
            self.entity_types.remove(rm)
            self.entity_entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = BIOESLabeler(root)
    root.mainloop()
