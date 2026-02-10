import flet as ft
import asyncio, json, websockets, pandas as pd

class RickAlgo:
    def __init__(self):
        self.prices = []
        self.token = "4CTmLVCQFl5lZIw"
        self.last_macd = 0

    def compute_indicators(self):
        df = pd.Series(self.prices)
        # RSI 14
        delta = df.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        # MACD
        ema12 = df.ewm(span=12).mean()
        ema26 = df.ewm(span=26).mean()
        macd = ema12 - ema26
        return rsi.iloc[-1], macd.iloc[-1]

    async def run(self, update_ui, page):
        uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"authorize": self.token}))
            await ws.send(json.dumps({"ticks": "R_75"}))
            async for msg in ws:
                data = json.loads(msg)
                if "tick" in data:
                    p = float(data["tick"]["quote"])
                    self.prices.append(p)
                    if len(self.prices) > 30:
                        rsi, macd = self.compute_indicators()
                        alert = ""
                        if self.last_macd <= 0 and macd > 0: alert = "MACD: CROISEMENT HAUSSIER ↑"
                        elif self.last_macd >= 0 and macd < 0: alert = "MACD: CROISEMENT BAISSIER ↓"
                        elif rsi >= 70: alert = "RSI: SUR-ACHAT (VENTE !)"
                        elif rsi <= 30: alert = "RSI: SUR-VENTE (ACHAT !)"
                        
                        if alert:
                            page.run_method("vibrate")
                            page.show_snack_bar(ft.SnackBar(ft.Text(alert), open=True))
                        self.last_macd = macd
                        update_ui(p, rsi, macd, alert)

def main(page: ft.Page):
    page.title = "RICK ALGO VIP"
    page.bgcolor = "black"
    algo = RickAlgo()
    p_display = ft.Text("CONNEXION...", size=50, color="yellow")
    i_display = ft.Text("", size=20)

    def update_ui(p, r, m, alert):
        p_display.value = f"{p:.2f}"
        i_display.value = f"RSI: {r:.2f} | MACD: {m:.4f}\n{alert}"
        page.update()

    def start_app(e):
        if pwd.value == "Rick":
            page.clean()
            page.add(ft.Column([p_display, i_display], horizontal_alignment="center"))
            asyncio.run(algo.run(update_ui, page))

    pwd = ft.TextField(label="Code VIP", password=True)
    page.add(ft.Column([ft.Text("RICK ALGO V75", size=30), pwd, ft.ElevatedButton("ENTRER", on_click=start_app)]))

ft.app(target=main)
