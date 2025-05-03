import io
import sys
import datetime

import pygame
import pandas as pd
import yfinance as yf
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib import font_manager

# ------------------ CONSTANTS ------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FPS = 30
FONT_PATH = "assets/font.ttf"
BG_IMAGE = "assets/Background.png"
COMPANIES = {"Nintendo": "NTDOY", "TakeTwo": "TTWO", "EA": "EA"}
START_YEAR = 2000
START_CASH = 10000
HIST_START = "1995-03-01"

# ------------------ CHART HELPERS ------------------
class ChartHelper:
    @staticmethod
    def _setup_axes(size, font_path, xlabel, ylabel):
        w, h = size
        dpi = 100
        fig = Figure(figsize=(w / dpi, h / dpi), dpi=dpi, facecolor="#121212")
        FigureCanvas(fig)
        ax = fig.add_subplot(111)

        # styling
        fig.patch.set_facecolor("#121212")
        ax.set_facecolor("#121212")
        for spine in ax.spines.values():
            spine.set_color("#2f2f2f")
        ax.grid(color="#2f2f2f", linestyle="--", linewidth=0.5)
        ax.tick_params(colors="white", labelsize=10)

        prop = font_manager.FontProperties(fname=font_path)
        for label in ax.get_xticklabels() + ax.get_yticklabels():
            label.set_fontproperties(prop)
            label.set_color("white")

        ax.set_xlabel(xlabel, fontproperties=prop, color="white")
        ax.set_ylabel(ylabel, fontproperties=prop, color="white")
        fig.tight_layout(rect=[0, 0, 0.95, 1])
        return fig, ax

    @staticmethod
    def create_price_chart(df_daily, years, idx, size, font_path):
        cutoff = datetime.datetime(years[idx], 3, 31)
        start = cutoff - pd.DateOffset(years=5)
        df_sub = df_daily[(df_daily.index >= start) & (df_daily.index <= cutoff)]

        fig, ax = ChartHelper._setup_axes(size, font_path, "Date", "Price (USD)")
        for ticker in df_sub.columns:
            ax.plot(df_sub.index, df_sub[ticker], label=ticker, linewidth=1.5, color="#00fc17")
        ax.legend(loc="upper left", facecolor="#121212", edgecolor="#2f2f2f", labelcolor="white",
                  prop=font_manager.FontProperties(fname=font_path))
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=fig.dpi, facecolor=fig.get_facecolor())
        buf.seek(0)
        return pygame.image.load(buf).convert()

    @staticmethod
    def create_portfolio_chart(df_daily, shares, years, idx, size, font_path):
        cutoff = datetime.datetime(years[idx], 12, 31)
        df_sub = df_daily[df_daily.index <= cutoff]
        port = pd.Series(0.0, index=df_sub.index)
        for comp, num in shares.items():
            ticker = COMPANIES[comp]
            if ticker in df_sub.columns:
                port += df_sub[ticker] * num

        fig, ax = ChartHelper._setup_axes(size, font_path, "Date", "Portfolio Value (USD)")
        ax.plot(port.index, port.values, label="Portfolio", linewidth=1.5)
        ax.legend(loc="upper left", facecolor="#121212", edgecolor="#2f2f2f", labelcolor="white",
                  prop=font_manager.FontProperties(fname=font_path))
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=fig.dpi, facecolor=fig.get_facecolor())
        buf.seek(0)
        return pygame.image.load(buf).convert()

# ------------------ MAIN GAME CLASS ------------------
class PixelInvestGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("PixelInvest")
        self.clock = pygame.time.Clock()
        self.pixel_font = lambda sz: pygame.font.Font(FONT_PATH, sz)
        self.bg = pygame.image.load(BG_IMAGE).convert()
        self.state = "MENU"
        self.cash = START_CASH
        self.shares = {n: 0.0 for n in COMPANIES}
        self.active_tab = list(COMPANIES.keys())[0]
        self.active_action = None
        self.input_str = ""
        self.popup_msg = None
        self.popup_rect = None
        self.input_box = pygame.Rect(50, SCREEN_HEIGHT - 60, 200, 40)

        self._load_data()
        self._init_ui_elements()

    def _load_data(self):
        # CSV data
        self.csv_df = pd.read_csv("Nintendo Annual CSV - Sheet1.csv", index_col=0, thousands=",")
        self.csv_df.columns = pd.to_datetime(self.csv_df.columns, format="%Y-%m-%d")

        # yearly price
        start_dt = f"{START_YEAR}-03-01"
        today = datetime.date.today().isoformat()
        df_yearly = yf.download(list(COMPANIES.values()), start=start_dt, end=today)["Close"]
        df_yearly = df_yearly.resample("Y").last()
        self.years = df_yearly.index.year.tolist()
        self.price_vals = {n: df_yearly[t].to_numpy() for n, t in COMPANIES.items()}

        # daily price
        self.df_daily = yf.download(list(COMPANIES.values()), start=HIST_START, end=today)["Close"]
        self.df_daily.index = pd.to_datetime(self.df_daily.index)
        self.year_idx = 0

    def _init_ui_elements(self):
        # tabs
        from button import Button
        self.tab_buttons = {}
        all_tabs = list(COMPANIES.keys()) + ["Portfolio"]
        for i, name in enumerate(all_tabs):
            x = 100 + i * 300
            self.tab_buttons[name] = Button(None, (x, 80), name, self.pixel_font(24), "#ffffff", "#444444")

        # buy/sell buttons
        self.invest_btns = {}
        self.sell_btns = {}
        for name in COMPANIES:
            self.invest_btns[name] = Button(None, (400, SCREEN_HEIGHT - 70), "BUY", self.pixel_font(30), "White", "Green")
            self.sell_btns[name] = Button(None, (700, SCREEN_HEIGHT - 70), "SELL", self.pixel_font(30), "White", "Green")

        self.next_year_btn = Button(None, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 605),
                                    "Next Year", self.pixel_font(24), "White", "Green")
        self.play_btn = Button(pygame.image.load("assets/Play Rect.png"),
                               (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50), "PLAY", self.pixel_font(48), "#d7fcd4", "White")
        self.quit_btn = Button(pygame.image.load("assets/Quit Rect.png"),
                               (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100), "QUIT", self.pixel_font(48), "#d7fcd4", "White")
        self.back_btn = Button(None, (80, 30), "BACK", self.pixel_font(24), "White", "Green")

    def run(self):
        while True:
            self._handle_events()
            self._draw()
            pygame.display.flip()
            self.clock.tick(FPS)

    def _handle_events(self):
        m = pygame.mouse.get_pos()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if self.popup_msg:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    self.popup_msg = None
                continue

            if self.state == "MENU":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if self.play_btn.checkForInput(m):
                        self.state = "GAME"
                    elif self.quit_btn.checkForInput(m):
                        pygame.quit(); sys.exit()
            else:
                self._handle_game_input(e, m)

    def _handle_game_input(self, e, m):
        if self.active_action and e.type == pygame.KEYDOWN:
            self._process_text_input(e)
        elif e.type == pygame.MOUSEBUTTONDOWN and not self.active_action:
            self._process_mouse_click(m)

    # ... Additional methods _process_text_input, _process_mouse_click, _draw_menu, _draw_game go here ...

    def _draw(self):
        if self.state == "MENU":
            self._draw_menu()
        else:
            self._draw_game()

# ------------------ ENTRY POINT ------------------
def main():
    game = PixelInvestGame()
    game.run()

if __name__ == "__main__":
    main()
