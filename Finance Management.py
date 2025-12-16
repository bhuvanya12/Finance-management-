import wx
import csv
import os
import random
import datetime
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

USERS_FILE = "users.csv"
DEDUCTIONS = {"80C": 150000, "80D": 25000, "80E": 50000}
STOCKS = {"AAPL": 120, "GOOGL": 140, "MSFT": 110, "TSLA": 180, "INFY": 75, "TCS": 95}

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["username", "password", "question", "answer"])

def old_regime_tax(t):
    tax = 0
    if t > 1000000:
        tax += (t - 1000000) * 0.30
        t = 1000000
    if t > 500000:
        tax += (t - 500000) * 0.20
        t = 500000
    if t > 250000:
        tax += (t - 250000) * 0.05
    return tax

def new_regime_tax(t):
    slabs = [(300000,0),(600000,0.05),(900000,0.10),(1200000,0.15),(1500000,0.20),(10**18,0.30)]
    tax = 0
    prev = 0
    for lim, rate in slabs:
        if t > lim:
            tax += (lim - prev) * rate
            prev = lim
        else:
            tax += (t - prev) * rate
            break
    return tax

class App(wx.App):
    def OnInit(self):
        self.user = None
        self.frame = MainFrame()
        self.frame.Show()
        return True

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Personal Finance Manager", size=(1200, 700))
        self.root = wx.Panel(self)
        self.root.SetBackgroundColour("#FFF6ED")
        s = wx.BoxSizer(wx.HORIZONTAL)
        self.sidebar = wx.Panel(self.root, size=(240, -1))
        self.sidebar.SetBackgroundColour("#2E2A27")
        self.side = wx.BoxSizer(wx.VERTICAL)
        self.content = wx.ScrolledWindow(self.root)
        self.content.SetScrollRate(10, 10)
        self.content.SetBackgroundColour("#FFF6ED")
        self.main = wx.BoxSizer(wx.VERTICAL)
        self.sidebar.SetSizer(self.side)
        self.content.SetSizer(self.main)
        s.Add(self.sidebar, 0, wx.EXPAND)
        s.Add(self.content, 1, wx.EXPAND)
        self.root.SetSizer(s)
        self.show_login()

    def clear_content(self):
        for c in self.content.GetChildren():
            c.Destroy()
        self.main.Clear()

    def clear_sidebar(self):
        for c in self.sidebar.GetChildren():
            c.Destroy()
        self.side.Clear()

    def sidebar_btn(self, label, handler):
        b = wx.Button(self.sidebar, label=label, size=(-1, 45))
        b.SetBackgroundColour("#3A3633")
        b.SetForegroundColour("white")
        b.Bind(wx.EVT_BUTTON, handler)
        self.side.Add(b, 0, wx.EXPAND | wx.ALL, 6)

    def build_sidebar(self):
        self.clear_sidebar()
        for l, f in [
            ("Dashboard", self.dashboard),
            ("Tax Calculator", self.tax),
            ("Tax History", self.tax_history),
            ("Stock Tracker", self.stock),
            ("Watchlist", self.watchlist),
            ("Account", self.account),
            ("Logout", self.logout)
        ]:
            self.sidebar_btn(l, f)
        self.sidebar.Layout()

    def card(self, title):
        p = wx.Panel(self.content)
        p.SetBackgroundColour("white")
        s = wx.BoxSizer(wx.VERTICAL)
        t = wx.StaticText(p, label=title)
        t.SetFont(wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        s.Add(t, 0, wx.ALL, 12)
        body = wx.BoxSizer(wx.VERTICAL)
        s.Add(body, 1, wx.EXPAND | wx.ALL, 10)
        p.SetSizer(s)
        return p, body

    def show_login(self):
        self.clear_sidebar()
        self.clear_content()
        card, body = self.card("Tax Calculator & Stock price tracker")
        card.SetMinSize((450, 400))
        u = wx.TextCtrl(card, size=(300, 30))
        p = wx.TextCtrl(card, style=wx.TE_PASSWORD, size=(300, 30))
        msg = wx.StaticText(card)
        def login(e):
            with open(USERS_FILE) as f:
                for r in csv.DictReader(f):
                    if r["username"] == u.GetValue() and r["password"] == p.GetValue():
                        app.user = u.GetValue()
                        self.build_sidebar()
                        self.dashboard(None)
                        return
            msg.SetLabel("Invalid credentials")
        for lbl, ctrl in [("Username", u), ("Password", p)]:
            body.Add(wx.StaticText(card, label=lbl), 0, wx.ALL, 5)
            body.Add(ctrl, 0, wx.EXPAND | wx.ALL, 5)
        for lbl, fn in [("Login", login), ("Register", self.register), ("Forgot Password", self.forgot)]:
            b = wx.Button(card, label=lbl)
            b.SetBackgroundColour("#E07A5F")
            b.SetForegroundColour("white")
            b.Bind(wx.EVT_BUTTON, fn)
            body.Add(b, 0, wx.ALL | wx.CENTER, 6)
        body.Add(msg, 0, wx.ALL | wx.CENTER, 6)
        self.main.AddStretchSpacer()
        self.main.Add(card, 0, wx.CENTER | wx.ALL, 20)
        self.main.AddStretchSpacer()
        self.content.Layout()

    def register(self, e):
        self.clear_content()
        card, body = self.card("Register")
        card.SetMinSize((450, 400))
        fields = [wx.TextCtrl(card, size=(300, 30)) for _ in range(4)]
        labels = ["Username", "Password", "Security Question", "Answer"]
        for l, w in zip(labels, fields):
            body.Add(wx.StaticText(card, label=l), 0, wx.ALL, 5)
            body.Add(w, 0, wx.EXPAND | wx.ALL, 5)
        def save(e):
            with open(USERS_FILE, "a", newline="") as f:
                csv.writer(f).writerow([w.GetValue() for w in fields])
            self.show_login()
        create_btn = wx.Button(card, label="Create Account")
        create_btn.SetBackgroundColour("#E07A5F")
        create_btn.SetForegroundColour("white")
        create_btn.Bind(wx.EVT_BUTTON, save)
        body.Add(create_btn, 0, wx.ALL | wx.CENTER, 10)
        back_btn = wx.Button(card, label="Back")
        back_btn.SetBackgroundColour("#E07A5F")
        back_btn.SetForegroundColour("white")
        back_btn.Bind(wx.EVT_BUTTON, lambda e: self.show_login())
        body.Add(back_btn, 0, wx.ALL | wx.CENTER, 6)
        self.main.Add(card, 1, wx.EXPAND | wx.ALL, 20)
        self.content.Layout()

    def forgot(self, e):
        self.clear_content()
        card, body = self.card("Recover Password")
        card.SetMinSize((450, 400))
        u = wx.TextCtrl(card, size=(300, 30))
        question_label = wx.StaticText(card, label="")
        a = wx.TextCtrl(card, size=(300, 30))
        msg = wx.StaticText(card)
        def fetch_question(e):
            question_label.SetLabel("")
            msg.SetLabel("")
            with open(USERS_FILE) as f:
                for r in csv.DictReader(f):
                    if r["username"] == u.GetValue():
                        question_label.SetLabel("Security Question: " + r["question"])
                        return
            question_label.SetLabel("Username not found")
        def recover(e):
            with open(USERS_FILE) as f:
                for r in csv.DictReader(f):
                    if r["username"] == u.GetValue() and r["answer"] == a.GetValue():
                        msg.SetLabel("Password: " + r["password"])
                        return
            msg.SetLabel("Incorrect answer")
        body.Add(wx.StaticText(card, label="Username"), 0, wx.ALL, 5)
        body.Add(u, 0, wx.EXPAND | wx.ALL, 5)
        fetch_btn = wx.Button(card, label="Show Security Question")
        fetch_btn.SetBackgroundColour("#E07A5F")
        fetch_btn.SetForegroundColour("white")
        fetch_btn.Bind(wx.EVT_BUTTON, fetch_question)
        body.Add(fetch_btn, 0, wx.ALL | wx.CENTER, 6)
        body.Add(question_label, 0, wx.ALL | wx.CENTER, 5)
        body.Add(wx.StaticText(card, label="Security Answer"), 0, wx.ALL, 5)
        body.Add(a, 0, wx.EXPAND | wx.ALL, 5)
        recover_btn = wx.Button(card, label="Recover Password")
        recover_btn.SetBackgroundColour("#E07A5F")
        recover_btn.SetForegroundColour("white")
        recover_btn.Bind(wx.EVT_BUTTON, recover)
        body.Add(recover_btn, 0, wx.ALL | wx.CENTER, 10)
        back_btn = wx.Button(card, label="Back")
        back_btn.SetBackgroundColour("#E07A5F")
        back_btn.SetForegroundColour("white")
        back_btn.Bind(wx.EVT_BUTTON, lambda e: self.show_login())
        body.Add(back_btn, 0, wx.ALL | wx.CENTER, 6)
        body.Add(msg, 0, wx.ALL | wx.CENTER, 6)
        self.main.Add(card, 1, wx.EXPAND | wx.ALL, 20)
        self.content.Layout()

    def dashboard(self, e):
        self.clear_content()
        card, body = self.card(f"Welcome, {app.user}")
        body.Add(wx.StaticText(card, label="Use the sidebar to access all features."), 0, wx.ALL, 10)
        self.main.Add(card, 1, wx.EXPAND | wx.ALL, 20)
        self.content.Layout()

    def tax(self, e):
        self.clear_content()
        card, body = self.card("Tax Calculator")
        income = wx.TextCtrl(card)
        regime = wx.RadioBox(card, label="Tax Regime", choices=["Old Regime", "New Regime"], majorDimension=1)
        checklist = wx.CheckListBox(card, choices=[f"{k} (₹{v})" for k, v in DEDUCTIONS.items()])
        out = wx.StaticText(card)
        def calc(e):
            try:
                inc = float(income.GetValue())
            except:
                out.SetLabel("Enter valid income")
                return
            selected = [list(DEDUCTIONS.keys())[i] for i in checklist.GetCheckedItems()]
            ded = sum(DEDUCTIONS[k] for k in selected)
            taxable = max(0, inc - ded) if regime.GetStringSelection() == "Old Regime" else inc
            base = old_regime_tax(taxable) if regime.GetStringSelection() == "Old Regime" else new_regime_tax(taxable)
            cess = base * 0.04
            total = base + cess
            out.SetLabel(f"Taxable Income: ₹{taxable}\nBase Tax: ₹{int(base)}\nCess (4%): ₹{int(cess)}\nFinal Tax: ₹{int(total)}")
            fn = f"tax_{app.user}.csv"
            write = not os.path.exists(fn)
            with open(fn, "a", newline="") as f:
                w = csv.writer(f)
                if write:
                    w.writerow(["Date", "Income", "Regime", "Deductions", "Taxable", "Base Tax", "Cess", "Final Tax"])
                w.writerow([datetime.date.today(), inc, regime.GetStringSelection(), "+".join(selected), taxable, int(base), int(cess), int(total)])
        for l, w in [("Annual Income", income)]:
            body.Add(wx.StaticText(card, label=l), 0, wx.ALL, 5)
            body.Add(w, 0, wx.EXPAND | wx.ALL, 5)
        body.Add(regime, 0, wx.ALL, 10)
        body.Add(wx.StaticText(card, label="Deductions (Old Regime only)"), 0, wx.ALL, 5)
        body.Add(checklist, 0, wx.EXPAND | wx.ALL, 5)
        b = wx.Button(card, label="Calculate Tax")
        b.SetBackgroundColour("#E07A5F")
        b.SetForegroundColour("white")
        b.Bind(wx.EVT_BUTTON, calc)
        body.Add(b, 0, wx.ALL, 10)
        body.Add(out, 0, wx.ALL, 10)
        self.main.Add(card, 1, wx.EXPAND | wx.ALL, 20)
        self.content.Layout()
    def export_tax_pdf(self):
        fn = f"tax_{app.user}.csv"
        if not os.path.exists(fn):
            wx.MessageBox("No tax data found")
            return
        pdf = f"{app.user}_tax_report.pdf"
        c = canvas.Canvas(pdf, pagesize=A4)
        w, h = A4
        y = h - 40
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, y, "Tax Report")
        y -= 30
        c.setFont("Helvetica", 10)
        with open(fn) as f:
            for r in csv.reader(f):
                c.drawString(40, y, " | ".join(r))
                y -= 14
                if y < 50:
                    c.showPage()
                    y = h - 40
        c.save()
        wx.MessageBox(f"PDF exported as {pdf}")

    def tax_history(self, e):
        self.clear_content()
        card, body = self.card("Tax History")
        grid = wx.ListCtrl(card, style=wx.LC_REPORT)
        headers = ["Date", "Income", "Regime", "Deductions", "Taxable", "Base Tax", "Cess", "Final Tax"]
        for i, h in enumerate(headers):
            grid.InsertColumn(i, h)
        fn = f"tax_{app.user}.csv"
        if os.path.exists(fn):
            with open(fn) as f:
                for r in list(csv.reader(f))[1:]:
                    i = grid.InsertItem(grid.GetItemCount(), r[0])
                    for j in range(1, len(r)):
                        grid.SetItem(i, j, r[j])
        b = wx.Button(card, label="Export as PDF")
        b.SetBackgroundColour("#E07A5F")
        b.SetForegroundColour("white")
        b.Bind(wx.EVT_BUTTON, lambda e: self.export_tax_pdf())
        body.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        body.Add(b, 0, wx.ALL | wx.CENTER, 8)
        self.main.Add(card, 1, wx.EXPAND | wx.ALL, 20)
        self.content.Layout()

    def stock(self, e):
        self.clear_content()
        card, body = self.card("Stock Tracker")
        choice = wx.Choice(card, choices=list(STOCKS.keys()))
        price = wx.StaticText(card)
        fig = Figure(figsize=(5, 3))
        ax = fig.add_subplot(111)
        canvas_plot = FigureCanvasWxAgg(card, -1, fig)
        def update(e):
            if choice.GetSelection() == wx.NOT_FOUND:
                return
            ax.clear()
            s = choice.GetString(choice.GetSelection())
            base = STOCKS[s]
            hist = [base + random.randint(-5, 5) for _ in range(10)]
            ax.plot(hist, marker="o")
            ax.set_title(s)
            canvas_plot.draw()
            price.SetLabel(f"Current Price: ₹{hist[-1]}")
        def add_watch(e):
            if choice.GetSelection() == wx.NOT_FOUND:
                return
            fn = f"watchlist_{app.user}.csv"
            s = choice.GetString(choice.GetSelection())
            rows = []
            if os.path.exists(fn):
                with open(fn) as f:
                    rows = [r[0] for r in csv.reader(f)]
            if s not in rows:
                with open(fn, "a", newline="") as f:
                    csv.writer(f).writerow([s])
        b = wx.Button(card, label="Add to Watchlist")
        b.SetBackgroundColour("#E07A5F")
        b.SetForegroundColour("white")
        b.Bind(wx.EVT_BUTTON, add_watch)
        choice.Bind(wx.EVT_CHOICE, update)
        body.Add(choice, 0, wx.EXPAND | wx.ALL, 5)
        body.Add(price, 0, wx.ALL, 5)
        body.Add(b, 0, wx.ALL, 6)
        body.Add(canvas_plot, 1, wx.EXPAND | wx.ALL, 5)
        self.main.Add(card, 1, wx.EXPAND | wx.ALL, 20)
        self.content.Layout()

    def watchlist(self, e):
        self.clear_content()
        card, body = self.card("Watchlist")
        grid = wx.ListCtrl(card, style=wx.LC_REPORT)
        grid.InsertColumn(0, "Stock")
        price = wx.StaticText(card)
        fig = Figure(figsize=(5, 3))
        ax = fig.add_subplot(111)
        canvas_plot = FigureCanvasWxAgg(card, -1, fig)
        fn = f"watchlist_{app.user}.csv"
        if os.path.exists(fn):
            with open(fn) as f:
                for r in csv.reader(f):
                    grid.InsertItem(grid.GetItemCount(), r[0])
        def select(e):
            i = grid.GetFirstSelected()
            if i == -1: return
            s = grid.GetItemText(i)
            ax.clear()
            base = STOCKS[s]
            hist = [base + random.randint(-5, 5) for _ in range(10)]
            ax.plot(hist, marker="o")
            ax.set_title(s)
            canvas_plot.draw()
            price.SetLabel(f"Current Price: ₹{hist[-1]}")
        def remove(e):
            i = grid.GetFirstSelected()
            if i == -1: return
            grid.DeleteItem(i)
            with open(fn, "w", newline="") as f:
                for j in range(grid.GetItemCount()):
                    csv.writer(f).writerow([grid.GetItemText(j)])
        grid.Bind(wx.EVT_LIST_ITEM_SELECTED, select)
        rb = wx.Button(card, label="Remove")
        rb.SetBackgroundColour("#E07A5F")
        rb.SetForegroundColour("white")
        rb.Bind(wx.EVT_BUTTON, remove)
        body.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        body.Add(price, 0, wx.ALL, 5)
        body.Add(rb, 0, wx.ALL | wx.CENTER, 5)
        body.Add(canvas_plot, 1, wx.EXPAND | wx.ALL, 5)
        self.main.Add(card, 1, wx.EXPAND | wx.ALL, 20)
        self.content.Layout()

    def account(self, e):
        self.clear_content()
        card, body = self.card("Account Management")
        body.Add(wx.StaticText(card, label=f"Username: {app.user}"), 0, wx.ALL, 5)
        name = wx.TextCtrl(card, value=app.user)
        pw = wx.TextCtrl(card, style=wx.TE_PASSWORD)
        body.Add(wx.StaticText(card, label="Change Username"), 0, wx.ALL, 5)
        body.Add(name, 0, wx.EXPAND | wx.ALL, 5)
        body.Add(wx.StaticText(card, label="Change Password"), 0, wx.ALL, 5)
        body.Add(pw, 0, wx.EXPAND | wx.ALL, 5)
        msg = wx.StaticText(card)
        def update_acc(e):
            rows = []
            with open(USERS_FILE) as f:
                rows = list(csv.DictReader(f))
            for r in rows:
                if r["username"] == app.user:
                    if name.GetValue(): r["username"] = name.GetValue()
                    if pw.GetValue(): r["password"] = pw.GetValue()
            with open(USERS_FILE, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=["username", "password", "question", "answer"]).writeheader()
                csv.DictWriter(f, fieldnames=["username", "password", "question", "answer"]).writerows(rows)
            app.user = name.GetValue() if name.GetValue() else app.user
            msg.SetLabel("Account updated successfully")
            self.build_sidebar()
        def delete_acc(e):
            if wx.MessageBox("Confirm Delete?", "Confirm", wx.YES_NO | wx.ICON_WARNING) == wx.YES:
                rows = []
                with open(USERS_FILE) as f:
                    rows = [r for r in csv.DictReader(f) if r["username"] != app.user]
                with open(USERS_FILE, "w", newline="") as f:
                    csv.DictWriter(f, fieldnames=["username", "password", "question", "answer"]).writeheader()
                    csv.DictWriter(f, fieldnames=["username", "password", "question", "answer"]).writerows(rows)
                fn = f"tax_{app.user}.csv"
                if os.path.exists(fn): os.remove(fn)
                fn = f"watchlist_{app.user}.csv"
                if os.path.exists(fn): os.remove(fn)
                app.user = None
                self.show_login()
        upb = wx.Button(card, label="Update Account")
        upb.SetBackgroundColour("#E07A5F")
        upb.SetForegroundColour("white")
        upb.Bind(wx.EVT_BUTTON, update_acc)
        delb = wx.Button(card, label="Delete Account")
        delb.SetBackgroundColour("#E07A5F")
        delb.SetForegroundColour("white")
        delb.Bind(wx.EVT_BUTTON, delete_acc)
        body.Add(upb, 0, wx.ALL | wx.CENTER, 6)
        body.Add(delb, 0, wx.ALL | wx.CENTER, 6)
        body.Add(msg, 0, wx.ALL | wx.CENTER, 6)
        self.main.Add(card, 1, wx.EXPAND | wx.ALL, 20)
        self.content.Layout()

    def logout(self, e):
        app.user = None
        self.show_login()

app = App()
app.MainLoop()