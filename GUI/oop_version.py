import io
import os
import sys
import datetime
import json
import textwrap

import pygame
import pandas as pd
import yfinance as yf

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
import csv

from button import Button

abspath = os.path.abspath(__file__)
dirname = os.path.dirname(abspath)

high_scores = pd.read_csv("scores.csv")

class Game:
    def __init__(self):
        # ------------------ Settings & Globals ------------------
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 1280, 720
        self.FPS = 30
        self.FONT_PATH = "assets/font.ttf"
        self.BG_IMAGE = "assets/Background.png"
        self.COMPANIES = {"Nintendo": "NTDOY", "TakeTwo": "TTWO", "EA": "EA"}
        self.START_YEAR = 2002
        self.START_CASH = 10000

        # Dynamic state
        self.year_idx = 0
        self.state = "MENU"
        self.cash = self.START_CASH # first amount for score calculation
        self.current = 0 # second amount
        self.player_name = "Diddy"
        self.shares = {n: 0.0 for n in self.COMPANIES}
        self.invested = {n: 0.0 for n in self.COMPANIES}
        self.totalinvested = self.invested.copy()
        self.sold = self.invested.copy()
        self.active_action = None
        self.input_str = ""
        self.input_box = pygame.Rect(800, 600, 200, 40)
        self.popup_surf = None
        self.popup_rect = None
        self.news_headline = ""
        self.news_body = ""

        # Tutorial state
        self.tutorial_slides = [
"""Welcome to Pixel Invest! You are an investor

looking to make it big. It's 2002 and it's

been one year since the dot-com bubble crisis.

You've taken an interest in the video game

industry and believe that this is where the

money is at. After hours of research you've

concluded that Nintendo, TakeTwo, and EA will

make you rich.""",
"""Use buttons to switch between companies

you want to invest in and manage your port-

folio of investments. You can buy and sell

shares of stock in these companies the va-

lue of which fluctuates with market events,

expectations, and finances of the firm.""",
"""Company Button: Navigate to the company you

want to invest in (also tells you important

data)

Buy button: Enter the amount of shares you

would like to purchase at a set price.

Sell button: Enter the amount of shares you

would like to sell at a set price.""",
"""News: Each firm has important news to help

you decide when to buy and when to sell.

Next Year: Goes to the next fiscal year and

you can see how your portfolio changed.""",
"""Provided company informations:

Net income - Tells how much income firm made

net of expenses determined from revenue.

Revenue - How much the firm made in sales

and profits.""",
"""Total equity - Financial value of firm,

how much would be left if firm sold all

assets and paid off all debts.

PM (Profit Margin) - Amount by which revenue

from sales exceeds costs in a business. Higher

is better.

EPS (Earnings per share) - How much profit

the company makes on each share of stock."""
        ]
        self.tutorial_idx = 0

        self.shift = False # for multi-key entry

        # ------------------ Load CSV data ------------------
        self.csv_dfs = {
            "Nintendo": pd.read_csv("Nintendo Annual CSV - Sheet1.csv", index_col=0, thousands=","),
            "TakeTwo":  pd.read_csv("Take Two Annual Data - Sheet1.csv", index_col=0, thousands=","),
            "EA":       pd.read_csv("EA Annual CSV - Sheet1.csv", index_col=0, thousands=",")
        }
        for df in self.csv_dfs.values():
            df.columns = pd.to_datetime(df.columns, format="%Y-%m-%d")

        # ------------------ Load news data ------------------
        with open("news.json", encoding="utf-8") as f:
            self.news_data = json.load(f)

        # ------------------ Initialize Pygame & Data ------------------
        pygame.init()
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("PixelInvest")
        self.clock = pygame.time.Clock()
        self.pixel_font = lambda sz: pygame.font.Font(self.FONT_PATH, sz)
        self.bg = pygame.image.load(self.BG_IMAGE).convert()

        # Fetch stock data
        start_dt = f"{self.START_YEAR}-03-01"
        HIST_START = "1995-03-01"
        today = datetime.date.today().isoformat()

        df_yearly = yf.download(list(self.COMPANIES.values()), start=start_dt, end=today)["Close"]
        df_yearly = df_yearly.resample("Y").last()
        self.years = df_yearly.index.year.tolist()
        self.price_vals = {n: df_yearly[t].to_numpy() for n, t in self.COMPANIES.items()}

        df_daily = yf.download(list(self.COMPANIES.values()), start=HIST_START, end=today)["Close"]
        df_daily.index = pd.to_datetime(df_daily.index)
        self.df_daily = df_daily

        # ------------------ Buttons ------------------
        self.tab_buttons = {}
        for i, name in enumerate(list(self.COMPANIES.keys()) + ["Portfolio"]):
            self.tab_buttons[name] = Button(
                None, (100 + i * 200 + 30, 80),
                name, self.pixel_font(24),
                "#ffffff", "#444444"
            )
        self.active_tab = list(self.tab_buttons.keys())[0]

        self.invest_btns = {
            n: Button(None, (850, 500), "BUY",
                      self.pixel_font(30), "White", "Green")
            for n in self.COMPANIES
        }
        self.sell_btns = {
            n: Button(None, (1150, 500), "SELL",
                      self.pixel_font(30), "White", "RED")
            for n in self.COMPANIES
        }

        self.next_year_btn = Button(None, (self.SCREEN_WIDTH - 180, 40), "Next Year",
                                   self.pixel_font(25), "White", "Green")
        self.play_btn = Button(pygame.image.load("assets/Play Rect.png"),
                               (self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 - 50),
                               "PLAY", self.pixel_font(48), "#d7fcd4", "White")
        self.quit_btn = Button(pygame.image.load("assets/Quit Rect.png"),
                               (self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2 + 100),
                               "QUIT", self.pixel_font(48), "#d7fcd4", "White")
        self.back_btn = Button(None, (80, 30), "BACK", self.pixel_font(24), "White", "Green")
        self.news_btn = Button(None, (1000, 400), "News", self.pixel_font(40), "#ffffff", "#444444")
        self.next_tut_btn = Button(None, (self.SCREEN_WIDTH - 180, self.SCREEN_HEIGHT - 80),
                                   "Next", self.pixel_font(30), "White", "Green")
        self.help_btn = Button(None, (self.SCREEN_WIDTH - 180, 600),
                               "Help", self.pixel_font(24), "#ffffff", "#444444")
        self.play_again_btn = Button(None, (self.SCREEN_WIDTH //2, 650), "Play again?", self.pixel_font(24), "#ffffff", "#444444")

    def restart_game(self):
        print("Hello world") # keeping this here
        print(self.cash, self.current)

        csv_file = open("scores.csv", "a", newline="", encoding="utf-8")
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([self.player_name, self.cash+self.current])
        csv_file.close()
        
        print("Goodbye World!")

        python = sys.executable # get Python's interpreter's executable path
        script = os.path.join(dirname, os.path.basename(abspath))  # Absolute path to the script
    
        os.execl(python, python, script, *sys.argv[1:]) # restart the script

    def create_chart(self, df, years, idx, size):
        cutoff = datetime.datetime(years[idx], 3, 31)
        start = cutoff - pd.DateOffset(years=5)
        df_sub = df[(df.index >= start) & (df.index <= cutoff)]
        prop = font_manager.FontProperties(fname=self.FONT_PATH)
        w, h, dpi = size[0], size[1], 100
        fig = Figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor="#121212")
        FigureCanvas(fig)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor("#121212"); ax.set_facecolor("#121212")
        for spine in ax.spines.values():
            spine.set_color("#2f2f2f")
        ax.grid(color="#2f2f2f", linestyle="--", linewidth=0.5)
        ax.tick_params(colors="white", labelsize=10)
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_fontproperties(prop); lbl.set_color("white")
        ax.set_xlabel("Date", fontproperties=prop, color="white")
        ax.set_ylabel("Price (USD)", fontproperties=prop, color="white")
        for ticker in df_sub.columns:
            ax.plot(df_sub.index, df_sub[ticker], linewidth=1.5, color="#00fc17", label=ticker)
        ax.legend(loc="upper left", facecolor="#121212", edgecolor="#2f2f2f", labelcolor="white", prop=prop)
        fig.tight_layout(rect=[0, 0, 0.95, 1])
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
        buf.seek(0)
        return pygame.image.load(buf).convert()

    def create_pchart(self, df, years, idx, size):
        cutoff = datetime.datetime(years[idx], 3, 31)
        start = cutoff - pd.DateOffset(years=5)
        df_sub = df[(df.index >= start) & (df.index <= cutoff)]
        prop = font_manager.FontProperties(fname=self.FONT_PATH)
        w, h, dpi = size[0], size[1], 100
        fig = Figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor="#121212")
        FigureCanvas(fig)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor("#121212"); ax.set_facecolor("#121212")
        for spine in ax.spines.values():
            spine.set_color("#2f2f2f")
        ax.grid(color="#2f2f2f", linestyle="--", linewidth=0.5)
        ax.tick_params(colors="white", labelsize=10)
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_fontproperties(prop); lbl.set_color("white")
        ax.set_xlabel("Date", fontproperties=prop, color="white")
        ax.set_ylabel("Price (USD)", fontproperties=prop, color="white")
        for ticker in df_sub.columns:
            ax.plot(df_sub.index, df_sub[ticker], linewidth=1.5, label=ticker)
        ax.legend(loc="upper left", facecolor="#121212", edgecolor="#2f2f2f", labelcolor="white", prop=prop)
        fig.tight_layout(rect=[0, 0, 0.95, 1])
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
        buf.seek(0)
        return pygame.image.load(buf).convert()

    def create_portfolio_chart(self, df, shares, years, idx, size):
        cutoff = datetime.datetime(years[idx], 3, 31)
        start = cutoff - pd.DateOffset(years=5)
        df_sub = df[(df.index >= start) & (df.index <= cutoff)]
        port_values = pd.Series(0.0, index=df_sub.index)
        for comp_name, num in shares.items():
            ticker = self.COMPANIES[comp_name]
            if ticker in df_sub.columns:
                port_values += df_sub[ticker] * num
        prop = font_manager.FontProperties(fname=self.FONT_PATH)
        w, h, dpi = size[0], size[1], 100
        fig = Figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor="#121212")
        FigureCanvas(fig)
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor("#121212"); ax.set_facecolor("#121212")
        for spine in ax.spines.values():
            spine.set_color("#2f2f2f")
        ax.grid(color="#2f2f2f", linestyle="--", linewidth=0.5)
        ax.tick_params(colors="white", labelsize=10)
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_fontproperties(prop); lbl.set_color("white")
        def y_fmt(x, pos):
            x = int(x)
            return f"{x//1000}k" if abs(x) >= 1000 else str(x)
        ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))
        ax.set_xlabel("Date", fontproperties=prop, color="white")
        ax.set_ylabel("Portfolio Value (USD)", fontproperties=prop, color="white")
        ax.plot(port_values.index, port_values.values, linewidth=1.5, color="#00fc17", label="Portfolio")
        ax.legend(loc="upper left", facecolor="#121212", edgecolor="#2f2f2f", labelcolor="white", prop=prop)
        fig.tight_layout(rect=[0, 0, 0.95, 1])
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
        buf.seek(0)
        return pygame.image.load(buf).convert()

    def draw_menu(self):
        self.screen.blit(self.bg, (0, 0))
        title = self.pixel_font(72).render("PixelInvest", True, "#b68f40")
        self.screen.blit(title, title.get_rect(center=(self.SCREEN_WIDTH // 2, 150)))
        m = pygame.mouse.get_pos()
        self.play_btn.changeColor(m); self.play_btn.update(self.screen)
        self.quit_btn.changeColor(m); self.quit_btn.update(self.screen)

    def draw_tutorial(self):
        self.screen.fill((20, 20, 20))
        lines = self.tutorial_slides[self.tutorial_idx].split("\n")
        font = pygame.font.Font(self.FONT_PATH, 28)
        block_h = font.get_linesize() * len(lines)
        y0 = (self.SCREEN_HEIGHT - block_h) // 2
        for i, ln in enumerate(lines):
            txt = font.render(ln, True, "#ffffff")
            x = (self.SCREEN_WIDTH - txt.get_width()) // 2
            self.screen.blit(txt, (x, y0 + i * font.get_linesize()))
        m = pygame.mouse.get_pos()
        self.next_tut_btn.changeColor(m); self.next_tut_btn.update(self.screen)

    def draw_endgame(self):
        global high_scores
        print(high_scores)

        self.screen.fill((20, 20, 20)) # fill the screen with a darker color
        m = pygame.mouse.get_pos()

        msg = "Game over!"
        font = pygame.font.Font(self.FONT_PATH, 28)
        txt = font.render(msg, True, "#ffffff")

        block_h = font.get_linesize() * len(msg)
        x, y = (self.SCREEN_WIDTH - txt.get_width()) // 2, (self.SCREEN_HEIGHT - block_h) // 2
        self.screen.blit(txt, (x, y))

        self.play_again_btn.changeColor(m); self.play_again_btn.update(self.screen)

    def draw_game(self):
        self.screen.fill((30, 30, 30))
        m = pygame.mouse.get_pos()

        # draw tabs
        for name, btn in self.tab_buttons.items():
            btn.bg_color = "#888888" if name == self.active_tab else "#444444"
            btn.changeColor(m); btn.update(self.screen)

        # header
        self.screen.blit(self.pixel_font(25).render(f"Year: {self.years[self.year_idx]}", True, "#b68f40"), (700, 30))
        self.screen.blit(self.pixel_font(25).render(f"Cash: ${self.cash:,.0f}", True, "#ffffff"),  (250, 30))

        if self.active_tab in self.COMPANIES:
            comp   = self.active_tab
            ticker = self.COMPANIES[comp]

            # -- Price & YTD change ----------------------------------------
            cutoff = datetime.datetime(self.years[self.year_idx],12,31)
            df_sub = self.df_daily[self.df_daily.index <= cutoff]
            current_price = float(df_sub[ticker].iloc[-1])
            if self.year_idx > 0:
                prev_cutoff = datetime.datetime(self.years[self.year_idx-1],12,31)
                prev_df     = df_sub[df_sub.index <= prev_cutoff]
                prev_raw    = prev_df[ticker].iloc[-1] if not prev_df.empty else current_price
            else:
                prev_raw    = current_price
            prev_price = float(prev_raw)
            change     = current_price - prev_price
            pct        = (change/prev_price*100) if prev_price != 0 else 0

            price_surf = self.pixel_font(48).render(f"${current_price:,.2f}", True, "#ffffff")
            self.screen.blit(price_surf, (50,120))
            sign = "+" if change >= 0 else ""
            self.screen.blit(self.pixel_font(24).render(
                f"{sign}${change:,.2f} ({sign}{pct:.2f}%) YTD",
                True, "#00c853" if change >= 0 else "#d32f2f"
            ), (50,120 + price_surf.get_height() + 5))

            # -- Total Return -----------------------------------------------
            cost_basis     = self.totalinvested[comp]
            total_sold     = self.sold[comp]
            position_value = self.shares[comp] * current_price
            total_ret      = (total_sold + position_value) - cost_basis
            pct_ret        = (total_ret / cost_basis * 100) if cost_basis != 0 else 0
            tr_font = pygame.font.Font(self.FONT_PATH,16)
            self.screen.blit(tr_font.render("Total Return:", True, "#ffffff"), (180,self.SCREEN_HEIGHT-100))
            sign2 = "+" if total_ret >= 0 else ""
            self.screen.blit(tr_font.render(
                f"{sign2}${total_ret:,.2f} ({sign2}{pct_ret:.2f}%)",
                True, "#00c853" if total_ret >= 0 else "#d32f2f"
            ), (180 + tr_font.size("Total Return: ")[0] + 20, self.SCREEN_HEIGHT-100))

            # -- Price Chart ------------------------------------------------
            chart = self.create_chart(self.df_daily[[ticker]], self.years, self.year_idx, (700,400))
            y_off_chart = 120 + price_surf.get_height() + self.pixel_font(24).get_linesize() + 20
            self.screen.blit(chart, (50, y_off_chart))

            # -- CSV Metrics -----------------------------------------------
            df_cur = self.csv_dfs[comp]
            cols   = [c for c in df_cur.columns if c.year == self.years[self.year_idx]]
            lines  = []
            if cols:
                col = cols[0]
                profit_label = "Net Income/Net Profit\n(Losses)"
                lines = [
                    f"Net Income:  ${df_cur.loc[profit_label,col]:,.2f}M",
                    f"Revenue:     ${df_cur.loc['Revenue',col]:,.2f}M",
                    f"Tot. Equity: ${df_cur.loc['Total Equity',col]:,.2f}M",
                    f"PM:          {df_cur.loc['Profit Margin',col]:.2f}%",
                    f"EPS:         {df_cur.loc['Basic Earnings per Share',col]:.2f}"
                ]
                for i, text in enumerate(lines):
                    surf = self.pixel_font(20).render(text, True, "#ffffff")
                    self.screen.blit(surf, (780, 220 + i*30))

            # -- News Button with Hover -------------------------------------
            comp_news = self.news_data.get(comp, [])
            item = next((it for it in comp_news if it.get("year") == self.years[self.year_idx]), None)
            if item:
                self.news_headline = item["headline"]
                self.news_body     = item["body"]
                text_color    = "#ffffff"
            else:
                self.news_headline, self.news_body, text_color = "No news available", "", "#888888"

            news_x = 780
            news_y = 220 + len(lines)*30 + 20
            self.news_btn.pos = (news_x, news_y)
            if self.news_btn.checkForInput(m):
                self.news_btn.bg_color = "#888888"
            else:
                self.news_btn.bg_color = "#444444"
            self.news_btn.text_color = text_color
            self.news_btn.changeColor(m); self.news_btn.update(self.screen)

            # -- Shares & Value ---------------------------------------------
            self.screen.blit(self.pixel_font(20).render(f"Shares: {self.shares[comp]:.2f}", True, "#ffffff"), (400,140))
            self.screen.blit(self.pixel_font(20).render(
                f"Total Value: ${self.shares[comp]*current_price:,.2f}", True, "#ffffff"
            ), (700,140))

            # -- Invest/Sell/Next/Back --------------------------------------
            self.invest_btns[comp].changeColor(m); self.invest_btns[comp].update(self.screen)
            self.sell_btns[comp].bg_color = "#555555" if self.shares[comp]==0 else "Green"
            self.sell_btns[comp].changeColor(m); self.sell_btns[comp].update(self.screen)
            self.next_year_btn.changeColor(m); self.next_year_btn.update(self.screen)
            self.back_btn.changeColor(m); self.back_btn.update(self.screen)

            if self.active_action and self.active_action[1] == comp:
                pygame.draw.rect(self.screen, (255,255,255), self.input_box, 2)
                self.screen.blit(self.pixel_font(20).render(self.input_str, True, "#ffffff"),
                                 (self.input_box.x+5, self.input_box.y+5))

        else:
            # -- Portfolio View ---------------------------------------------
            cutoff = datetime.datetime(self.years[self.year_idx],12,31)
            df_sub = self.df_daily[self.df_daily.index <= cutoff]
            port_values = pd.Series(0.0, index=df_sub.index)
            for name, num in self.shares.items():
                tt = self.COMPANIES[name]
                if tt in df_sub.columns:
                    port_values += df_sub[tt] * num

            current = port_values.iloc[-1]
            self.current = current
            if self.year_idx > 0:
                prev_cutoff  = datetime.datetime(self.years[self.year_idx-1],12,31)
                prev_series  = port_values[port_values.index <= prev_cutoff]
                prev = prev_series.iloc[-1] if not prev_series.empty else port_values.iloc[0]
            else:
                prev = current

            change = current - prev
            pct    = (change/prev*100) if prev != 0 else 0

            self.screen.blit(self.pixel_font(72).render(f"${current:,.2f}", True, "#ffffff"), (50,120))
            sign    = "+" if change >= 0 else ""
            self.screen.blit(self.pixel_font(24).render(
                f"{sign}${change:,.2f} ({sign}{pct:.2f}%) YTD",
                True, "#00c853" if change >= 0 else "#d32f2f"
            ), (50, 120 + self.pixel_font(72).get_linesize() + 5))

            # -- Two charts side by side ------------------------------------
            w, h = (self.SCREEN_WIDTH - 400)//2, 400
            y0   = 120 + self.pixel_font(72).get_linesize() + self.pixel_font(24).get_linesize() + 20

            port_surf  = self.create_portfolio_chart(self.df_daily, self.shares, self.years, self.year_idx, (w,h))
            price_surf = self.create_pchart(self.df_daily, self.years, self.year_idx, (w,h))
            self.screen.blit(port_surf,  (50, y0))
            self.screen.blit(price_surf, (50 + w + 50, y0))

            # -- Company list ----------------------------------------------
            pf = self.pixel_font(24)
            for i, name in enumerate(self.COMPANIES):
                tt = self.COMPANIES[name]
                ns = self.shares[name]
                lp = df_sub[tt].iloc[-1] if tt in df_sub.columns else 0
                y1 = y0 + i * 60
                self.screen.blit(pf.render(name, True, "#ffffff"),        (50 + w*2 + 100, y1))
                self.screen.blit(pf.render(f"{ns:.2f} shares", True, "#aaaaaa"),
                                (50 + w*2 + 250, y1))
                self.screen.blit(pf.render(f"${lp:,.2f}", True, "#ffffff"),
                                (50 + w*2 + 100, y1 + 24))

            # Draw help button
            self.help_btn.changeColor(m); self.help_btn.update(self.screen)
            self.next_year_btn.changeColor(m); self.next_year_btn.update(self.screen)
            self.back_btn.changeColor(m);    self.back_btn.update(self.screen)

        # -- Pop‑up Overlay ---------------------------------------------
        if self.popup_surf is not None and isinstance(self.popup_rect, pygame.Rect):
            overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,180))
            self.screen.blit(overlay, (0,0))
            self.screen.blit(self.popup_surf, self.popup_rect)

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.popup_surf is not None:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.popup_surf = None
                        self.popup_rect = None
                    continue

                mpos = pygame.mouse.get_pos()

                # -- MENU Input ------------------------------------------------
                if self.state == "MENU":
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.play_btn.checkForInput(mpos):
                            self.tutorial_idx = 0
                            self.state = "TUTORIAL"
                        elif self.quit_btn.checkForInput(mpos):
                            pygame.quit()
                            sys.exit()

                # -- TUTORIAL Input --------------------------------------------
                elif self.state == "TUTORIAL":
                    if event.type == pygame.MOUSEBUTTONDOWN and self.next_tut_btn.checkForInput(mpos):
                        self.tutorial_idx += 1
                        if self.tutorial_idx >= len(self.tutorial_slides):
                            self.active_tab = "Portfolio"
                            self.state = "GAME"
                    continue

                elif self.state == "ENDGAME":
                    if event.type == pygame.MOUSEBUTTONDOWN and self.play_again_btn.checkForInput(mpos):
                        pygame.quit()
                        self.restart_game()

                # -- GAME Input ------------------------------------------------
                else:
                    # -- News Button Click ------------------------------------
                    if event.type == pygame.MOUSEBUTTONDOWN and self.active_tab in self.COMPANIES:
                        if self.news_btn.checkForInput(mpos):
                            all_lines = [self.news_headline] + textwrap.wrap(self.news_body or "", width=40)
                            headline_font = pygame.font.Font(self.FONT_PATH, 24)
                            headline_font.set_underline(True)
                            body_font     = pygame.font.Font(self.FONT_PATH, 24)
                            lh = headline_font.get_linesize()
                            if len(all_lines) > 1:
                                widths = [headline_font.size(all_lines[0])[0]] + \
                                         [body_font.size(ln)[0] for ln in all_lines[1:]]
                                w_popup = max(widths) + 20
                            else:
                                w_popup = headline_font.size(all_lines[0])[0] + 20
                            h_popup = lh * len(all_lines) + 20
                            self.popup_surf = pygame.Surface((w_popup, h_popup), pygame.SRCALPHA)
                            self.popup_surf.fill((47,47,47,230))
                            for i, ln in enumerate(all_lines):
                                if i == 0:
                                    txt = headline_font.render(ln, True, (255,165,0))
                                    x = (w_popup - txt.get_width()) // 2
                                else:
                                    txt = body_font.render(ln, True, "#ffffff")
                                    x = 10
                                self.popup_surf.blit(txt, (x, 10 + i * lh))
                            self.popup_rect = self.popup_surf.get_rect(center=(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2))
                            continue

                    # -- Typing input for BUY/SELL -----------------------------
                    if self.active_action and event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_BACKSPACE:
                            self.input_str = self.input_str[:-1]
                        elif event.key == pygame.K_RETURN:
                            mode, comp = self.active_action
                            price = self.price_vals[comp][self.year_idx]
                            try:
                                num = int(self.input_str)
                            except:
                                num = 0
                            msg = ""
                            if mode == "invest":
                                cost = num * price
                                if num <= 0:
                                    msg = "Enter at least 1 share to buy."
                                elif cost > self.cash:
                                    msg = f"Not enough cash: need ${cost:,.2f}."
                                else:
                                    self.shares[comp]        += num
                                    self.invested[comp]      += cost
                                    self.totalinvested[comp] += cost
                                    self.cash                -= cost
                                    msg = f"Bought {num} share(s) for ${cost:,.2f}!"
                            else:
                                to_sell = min(num, int(self.shares[comp]))
                                if to_sell <= 0:
                                    msg = "No shares to sell."
                                else:
                                    proceeds = to_sell * price
                                    self.shares[comp]     -= to_sell
                                    self.sold[comp]       += proceeds
                                    self.invested[comp]   -= proceeds
                                    self.cash             += proceeds
                                    msg = f"Sold {to_sell} share(s) for ${proceeds:,.2f}!"
                            lines = textwrap.wrap(msg, width=60)
                            font  = pygame.font.Font(self.FONT_PATH,24)
                            lh    = font.get_linesize()
                            w_p   = max(font.size(ln)[0] for ln in lines) + 20
                            h_p   = lh * len(lines) + 20
                            self.popup_surf = pygame.Surface((w_p,h_p), pygame.SRCALPHA)
                            self.popup_surf.fill((47,47,47,230))
                            for i, ln in enumerate(lines):
                                self.popup_surf.blit(font.render(ln,True,"#ffffff"), (10,10+i*lh))
                            self.popup_rect = pygame.Rect(
                                (self.SCREEN_WIDTH//2 - w_p//2, self.SCREEN_HEIGHT//2 - h_p//2),
                                (w_p,h_p)
                            )
                            self.active_action = None
                            self.input_str     = ""
                        elif event.unicode.isdigit() or event.unicode == ".":
                            self.input_str += event.unicode

                    # -- Other button clicks ---------------------------------
                    if event.type == pygame.MOUSEBUTTONDOWN and not self.active_action:
                        # BACK
                        if self.back_btn.checkForInput(mpos):
                            self.state    = "MENU"
                            self.year_idx = 0
                            self.cash     = self.START_CASH
                            self.shares   = {n:0.0 for n in self.COMPANIES}
                            self.invested = {n:0.0 for n in self.COMPANIES}
                            self.totalinvested = self.invested.copy()
                            self.sold     = self.invested.copy()

                        # TAB SWITCH
                        for name, btn in self.tab_buttons.items():
                            if btn.checkForInput(mpos):
                                self.active_tab = name

                        # BUY/SELL
                        if self.active_tab in self.COMPANIES:
                            if self.invest_btns[self.active_tab].checkForInput(mpos):
                                self.active_action = ("invest", self.active_tab)
                                self.input_str = ""
                            elif self.sell_btns[self.active_tab].checkForInput(mpos) and self.shares[self.active_tab] > 0:
                                self.active_action = ("sell", self.active_tab)
                                self.input_str = ""

                        # NEXT YEAR
                        if self.next_year_btn.checkForInput(mpos) and self.year_idx < len(self.years)-1:
                            self.year_idx += 1

                        # HELP in Portfolio
                        if self.active_tab == "Portfolio" and self.help_btn.checkForInput(mpos):
                            self.tutorial_idx = 0
                            self.state = "TUTORIAL"

                    # -- multi-key input -------------------------------
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_LSHIFT:
                            self.shift = True
                        if event.key == pygame.K_DELETE and self.shift:
                            self.state = "ENDGAME"
                    if event.type == pygame.KEYUP:
                        if event.type == pygame.K_LSHIFT:
                            self.shift = False

            # -- RENDER -------------------------------------------------
            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "TUTORIAL":
                self.draw_tutorial()
            elif self.state == "ENDGAME":
                self.draw_endgame()
            else:
                self.draw_game()

            pygame.display.flip()
            self.clock.tick(self.FPS)

if __name__ == "__main__":
    Game().run()
