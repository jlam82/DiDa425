import io
import sys
import datetime

import pygame
import pandas as pd
import yfinance as yf

from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib import font_manager

# ------------------ LOAD CSV DATA ------------------
csv_df = pd.read_csv(
    "Nintendo Annual CSV - Sheet1.csv",
    index_col=0,
    thousands=","
)
csv_df.columns = pd.to_datetime(csv_df.columns, format="%Y-%m-%d")

# ------------------ SETTINGS ------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FPS = 30

FONT_PATH  = "assets/font.ttf"
BG_IMAGE   = "assets/Background.png"
COMPANIES  = {"Nintendo": "NTDOY", "TakeTwo": "TTWO", "EA": "EA"}
START_YEAR = 2000
START_CASH = 10000

# ------------------ CHART FUNCTIONS ------------------
def create_chart(df_daily, years, idx, size, font_path):
    cutoff = datetime.datetime(years[idx], 12, 31)
    df_sub = df_daily[df_daily.index <= cutoff]

    prop = font_manager.FontProperties(fname=font_path)
    w, h = size
    dpi = 100
    fig = Figure(figsize=(w/dpi, h/dpi), dpi=dpi, facecolor="#121212")
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    fig.patch.set_facecolor("#121212")
    ax.set_facecolor("#121212")
    for spine in ax.spines.values():
        spine.set_color("#2f2f2f")
    ax.grid(color="#2f2f2f", linestyle="--", linewidth=0.5)
    ax.tick_params(colors="white", labelsize=10)
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.xaxis.label.set_fontproperties(prop)
    ax.yaxis.label.set_fontproperties(prop)

    for ticker in df_sub.columns:
        ax.plot(df_sub.index, df_sub[ticker], label=ticker, linewidth=1.5)

    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend(
        loc="upper left",
        facecolor="#121212",
        edgecolor="#2f2f2f",
        labelcolor="white",
        prop=prop
    )
    fig.tight_layout(rect=[0, 0, 0.95, 1])

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)
    return pygame.image.load(buf).convert()

def create_portfolio_chart(df_daily, shares, years, idx, size, font_path):
    import datetime, io, pygame
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib import font_manager

    # 1) restrict to dates up to end of current game-year
    cutoff = datetime.datetime(years[idx], 12, 31)
    df_sub = df_daily[df_daily.index <= cutoff]

    # 2) build a Series of total portfolio value at each date
    port_values = pd.Series(0.0, index=df_sub.index)

    # COMPANIES maps names → tickers; loop your shares by company name
    for company_name, num_shares in shares.items():
        ticker = COMPANIES[company_name]  # e.g. "Nintendo" → "NTDOY"
        if ticker in df_sub.columns:
            port_values += df_sub[ticker] * num_shares

    # 3) Now plot with your dark styling
    prop = font_manager.FontProperties(fname=font_path)
    w, h = size
    dpi = 100
    fig = Figure(figsize=(w/dpi, h/dpi), dpi=dpi, facecolor="#121212")
    FigureCanvas(fig)
    ax = fig.add_subplot(111)

    fig.patch.set_facecolor("#121212")
    ax.set_facecolor("#121212")
    for spine in ax.spines.values():
        spine.set_color("#2f2f2f")
    ax.grid(color="#2f2f2f", linestyle="--", linewidth=0.5)
    ax.tick_params(colors="white", labelsize=10)

    # 4) plot the summed portfolio line
    ax.plot(port_values.index, port_values.values, linewidth=1.5)

    # 5) labels in white using your pixel font
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.xaxis.label.set_fontproperties(prop)
    ax.yaxis.label.set_fontproperties(prop)
    ax.set_xlabel("Date")
    ax.set_ylabel("Portfolio Value (USD)")

    fig.tight_layout(rect=[0, 0, 0.95, 1])

    # 6) render to pygame.Surface
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)
    return pygame.image.load(buf).convert()




# ------------------ INIT & DATA ------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PixelInvest")
clock = pygame.time.Clock()

pixel_font = lambda sz: pygame.font.Font(FONT_PATH, sz)
bg = pygame.image.load(BG_IMAGE).convert()

start_dt = f"{START_YEAR}-03-01"
today = datetime.date.today().isoformat()

# yearly data for progression
df_yearly = yf.download(list(COMPANIES.values()), start=start_dt, end=today)["Close"]
df_yearly = df_yearly.resample("Y").last()
years = df_yearly.index.year.tolist()
price_vals = {n: df_yearly[t].to_numpy() for n, t in COMPANIES.items()}

# daily data for chart
df_daily = yf.download(list(COMPANIES.values()), start=start_dt, end=today)["Close"]
df_daily.index = pd.to_datetime(df_daily.index)

chart_size = (SCREEN_WIDTH - 400, 400)
year_idx = 0
chart_surf = create_chart(df_daily, years, year_idx, chart_size, FONT_PATH)

# game state
state = "MENU"
cash = START_CASH
shares = {n: 0.0 for n in COMPANIES}

active_action = None      # ("invest"|"sell", company_name)
input_str = ""
input_box = pygame.Rect(50, SCREEN_HEIGHT - 60, 200, 40)

# ------------------ BUTTONS ------------------
from button import Button

invest_btns = {}
sell_btns = {}
for i, name in enumerate(COMPANIES):
    x_off = 200 + i * 400
    invest_btns[name] = Button(None, (x_off, SCREEN_HEIGHT - 160),
                               f"Invest {name}", pixel_font(24), "White", "Green")
    sell_btns[name] = Button(None, (x_off, SCREEN_HEIGHT - 100),
                             f"Sell {name}", pixel_font(24), "White", "Green")

next_year_btn = Button(None, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 605),
                       "Next Year", pixel_font(24), "White", "Green")

# Menu buttons
play_btn = Button(pygame.image.load("assets/Play Rect.png"),
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50),
                  "PLAY", pixel_font(48), "#d7fcd4", "White")
quit_btn = Button(pygame.image.load("assets/Quit Rect.png"),
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100),
                  "QUIT", pixel_font(48), "#d7fcd4", "White")
back_btn = Button(None, (80, 30), "BACK", pixel_font(24), "White", "Green")

# Tab buttons
tab_price_btn = Button(None, (100, 80), "Prices", pixel_font(24), "#ffffff", "#444444")
tab_portfolio_btn = Button(None, (250, 80), "Portfolio", pixel_font(24), "#ffffff", "#444444")
active_tab = "prices"

# ------------------ DRAW FUNCTIONS ------------------
def draw_menu():
    screen.blit(bg, (0, 0))
    title = pixel_font(72).render("PixelInvest", True, "#b68f40")
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 150)))
    m = pygame.mouse.get_pos()
    play_btn.changeColor(m); play_btn.update(screen)
    quit_btn.changeColor(m); quit_btn.update(screen)

def draw_game():
    global chart_surf
    screen.fill((30, 30, 30))

    # -- Tab bar -------------------------------------------------------
    m = pygame.mouse.get_pos()
    tab_price_btn.bg_color     = "#888888" if active_tab == "prices"    else "#444444"
    tab_portfolio_btn.bg_color = "#888888" if active_tab == "portfolio" else "#444444"
    for btn in (tab_price_btn, tab_portfolio_btn):
        btn.changeColor(m)
        btn.update(screen)
    # -- End Tab bar ---------------------------------------------------

    # common header
    hf = pixel_font(25)
    screen.blit(hf.render(f"Year: {years[year_idx]}", True, "#b68f40"), (700, 30))
    screen.blit(hf.render(f"Cash: ${cash:,.0f}", True, "#ffffff"), (250, 30))

    if active_tab == "prices":
        # existing price chart + metrics + buttons
        screen.blit(chart_surf, (50, 120))

        # CSV metrics
        year = years[year_idx]
        matching = [c for c in csv_df.columns if c.year == year]
        if matching:
            col = matching[0]
            net_income     = csv_df.loc["Net Income/Net Profit\n(Losses)", col]
            revenue        = csv_df.loc["Revenue", col]
            dividends_paid = csv_df.loc["Dividends Paid", col]
            eps            = csv_df.loc["Basic Earnings per Share", col]
            lines = [
                f"Net Income:  ${net_income:,.2f}M",
                f"Revenue:     ${revenue:,.2f}M",
                f"Dividends:   ${dividends_paid:,.2f}M",
                f"EPS:         {eps:,.2f}"
            ]
            for i, text in enumerate(lines):
                surf = pixel_font(14).render(text, True, "#ffffff")
                screen.blit(surf, (940, 180 + i * 30))

        # share counts + invest/sell buttons
        base_x, y = SCREEN_WIDTH - 1250, 70
        pf = pixel_font(24)
        for i, name in enumerate(COMPANIES):
            txt = f"{name}: {shares[name]:.2f} sh"
            surf = pf.render(txt, True, "#ffffff")
            screen.blit(surf, (base_x + i * 450, y))
            invest_btns[name].changeColor(m); invest_btns[name].update(screen)
            if shares[name] > 0:
                sell_btns[name].changeColor(m); sell_btns[name].update(screen)

        next_year_btn.changeColor(m); next_year_btn.update(screen)
        back_btn.changeColor(m); back_btn.update(screen)

        if active_action:
            pygame.draw.rect(screen, (255, 255, 255), input_box, 2)
            txt_surf = pf.render(input_str, True, "#ffffff")
            screen.blit(txt_surf, (input_box.x + 5, input_box.y + 5))

    else:  # active_tab == "portfolio"
        # 1) restrict to dates up to end of current game‐year
        cutoff = datetime.datetime(years[year_idx], 12, 31)
        df_sub = df_daily[df_daily.index <= cutoff]

        # 2) build total portfolio value series
        port_values = pd.Series(0.0, index=df_sub.index)
        for comp_name, num_shares in shares.items():
            ticker = COMPANIES[comp_name]
            if ticker in df_sub.columns:
                port_values += df_sub[ticker] * num_shares

        # 3) get current and previous year‐end values
        current = port_values.iloc[-1]
        if year_idx > 0:
            prev_cutoff = datetime.datetime(years[year_idx - 1], 12, 31)
            prev_series = port_values[port_values.index <= prev_cutoff]
            prev = prev_series.iloc[-1] if len(prev_series) else port_values.iloc[0]
        else:
            prev = current

        change = current - prev
        pct    = (change / prev * 100) if prev else 0

        # 4) draw total value at top
        big_font = pixel_font(72)
        val_surf = big_font.render(f"${current:,.2f}", True, "#ffffff")
        screen.blit(val_surf, (50, 120))

        # 5) draw yearly change beneath it
        chg_font = pixel_font(24)
        sign     = "+" if change >= 0 else ""
        color    = "#00c853" if change >= 0 else "#d32f2f"
        chg_text = f"{sign}${change:,.2f} ({sign}{pct:.2f}%) YTD"
        chg_surf = chg_font.render(chg_text, True, color)
        screen.blit(chg_surf, (50, 120 + val_surf.get_height() + 5))

        # 6) draw the portfolio‐value chart below
        chart_y = 120 + val_surf.get_height() + chg_surf.get_height() + 20
        port_surf = create_portfolio_chart(
            df_daily, shares, years, year_idx, chart_size, FONT_PATH
        )
        screen.blit(port_surf, (50, chart_y))

        # 7) draw your navigation buttons
        m = pygame.mouse.get_pos()
        back_btn.changeColor(m);      back_btn.update(screen)
        next_year_btn.changeColor(m); next_year_btn.update(screen)



# ------------------ MAIN LOOP ------------------
while True:
    m = pygame.mouse.get_pos()
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if state == "MENU":
            if e.type == pygame.MOUSEBUTTONDOWN:
                if play_btn.checkForInput(m):
                    state = "GAME"
                if quit_btn.checkForInput(m):
                    pygame.quit(); sys.exit()

        else:  # GAME state
            # handle typing
            if active_action and e.type == pygame.KEYDOWN:
                if e.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                elif e.key == pygame.K_RETURN:
                    mode, comp = active_action
                    try:
                        amt = float(input_str)
                    except:
                        amt = 0.0
                    price = price_vals[comp][year_idx]
                    if mode == "invest" and amt > 0 and cash >= amt:
                        bought = amt / price
                        shares[comp] += bought
                        cash -= amt
                    if mode == "sell" and amt > 0:
                        max_sell     = shares[comp] * price
                        sell_amt     = min(amt, max_sell)
                        sold_shares  = sell_amt / price
                        shares[comp] -= sold_shares
                        cash        += sell_amt
                    active_action = None
                    input_str     = ""
                elif e.unicode.isdigit() or e.unicode == ".":
                    input_str += e.unicode

            # handle clicks (including tab switching)
            if e.type == pygame.MOUSEBUTTONDOWN and not active_action:
                if back_btn.checkForInput(m):
                    state = "MENU"
                    year_idx = 0
                    cash = START_CASH
                    shares = {n: 0.0 for n in COMPANIES}
                    chart_surf = create_chart(df_daily, years, year_idx, chart_size, FONT_PATH)

                if tab_price_btn.checkForInput(m):
                    active_tab = "prices"
                if tab_portfolio_btn.checkForInput(m):
                    active_tab = "portfolio"

                for name in COMPANIES:
                    if invest_btns[name].checkForInput(m):
                        active_action = ("invest", name)
                        input_str = ""
                    if sell_btns[name].checkForInput(m) and shares[name] > 0:
                        active_action = ("sell", name)
                        input_str = ""

                if next_year_btn.checkForInput(m) and year_idx < len(years) - 1:
                    year_idx += 1
                    chart_surf = create_chart(df_daily, years, year_idx, chart_size, FONT_PATH)

    # draw
    if state == "MENU":
        draw_menu()
    else:
        draw_game()

    pygame.display.flip()
    clock.tick(FPS)
