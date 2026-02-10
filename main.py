import flet as ft
import asyncio, json, websockets, pandas as pd

class RickAlgoEngine:
    def __init__(self):
        self.prices = []
        self.token = "4CTmLVCQFl5lZIw"
        self.last_macd = 0

    def calculate_indicators(self):
        if len(self.prices) < 30: return None, None
        df = pd.Series(self.prices)
        
        # RSI (14 periods)
        delta = df.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD (12, 26, 9)
        exp1 = df.ewm(span=12, adjust=False).mean()
        exp2 = df.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        
        return rsi.iloc[-1], macd.iloc[-1]

    async def connect_v75(self, update_ui, page):
        uri = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"authorize": self.token}))
            await ws.send(json.dumps({"ticks": "R_75"}))
            async for msg in ws:
                res = json.loads(msg)
                if "tick" in res:
                    price = float(res["tick"]["quote"])
                    self.prices.append(price)
                    if len(self.prices) > 50: self.prices.pop(0) # Garde la mémoire propre

                    rsi, macd = self.calculate_indicators()
                    alert_msg = ""

                    if rsi and macd:
                        # Logique MACD : Croisement de la ligne 0
                        if self.last_macd <= 0 and macd > 0:
                            alert_msg = "🔥 SIGNAL ACHAT (MACD 0+)"
                        elif self.last_macd >= 0 and macd < 0:
                            alert_msg = "❄️ SIGNAL VENTE (MACD 0-)"
                        
                        # Logique RSI
                        elif rsi >= 70: alert_msg = "⚠️ RSI SUR-ACHAT (70)"
                        elif rsi <= 30: alert_msg = "⚠️ RSI SUR-VENTE (30)"

                        if alert_msg:
                            page.run_method("vibrate") # Fait vibrer le téléphone
                            page.show_snack_bar(ft.SnackBar(ft.Text(alert_msg), open=True))
                        
                        self.last_macd = macd
                    update_ui(price, rsi, macd, alert_msg)

def main(page: ft.Page):
    page.title = "RICK ALGO VIP"
    page.theme_mode = "dark"
    page.vertical_alignment = "center"
    engine = RickAlgoEngine()

    price_text = ft.Text("---", size=50, color="yellow", weight="bold")
    indicator_text = ft.Text("Analyse en cours...", size=16)

    def update_display(p, r, m, a):
        price_text.value = f"{p:.2f}"
        if r and m:
            indicator_text.value = f"RSI: {r:.2f} | MACD: {m:.4f}"
        page.update()

    def start_app(e):
        if pwd.value == "Rick":
            page.clean()
            page.add(ft.Column([
                ft.Text("V75 LIVE MONITOR", size=20, color="white"),
                price_text,
                indicator_text
            ], horizontal_alignment="center"))
            asyncio.run(engine.connect_v75(update_display, page))

    pwd = ft.TextField(label="Mot de Passe VIP", password=True, text_align="center")
    page.add(ft.Column([
        ft.Text("RICK ALGO VIP", size=32, weight="bold"),
        pwd,
        ft.ElevatedButton("LANCER L'ALGO", on_click=start_app)
    ], horizontal_alignment="center"))

ft.app(target=main)
