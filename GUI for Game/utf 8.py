import io
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

from button import Button

# ------------------ Load CSV data ------------------
csv_dfs = {
    "Nintendo": pd.read_csv("Nintendo Annual CSV - Sheet1.csv", index_col=0, thousands=","),
    "TakeTwo":  pd.read_csv("Take Two Annual Data - Sheet1.csv", index_col=0, thousands=","),
    "EA":       pd.read_csv("EA Annual CSV - Sheet1.csv", index_col=0, thousands=",")
}
for df in csv_dfs.values():
    df.columns = pd.to_datetime(df.columns, format="%Y-%m-%d")

# ------------------ Load news data ------------------
with open("news.json", encoding="utf-8") as f:
    news_data = json.load(f)

# ------------------ Settings & Globals ------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FPS            = 30
FONT_PATH      = "assets/font.ttf"
BG_IMAGE       = "assets/Background.png"
COMPANIES      = {"Nintendo": "NTDOY", "TakeTwo": "TTWO", "EA": "EA"}
START_YEAR     = 2002
START_CASH     = 10000

# Dynamic state
year_idx       = 0
state          = "MENU"
cash           = START_CASH
shares         = {n: 0.0 for n in COMPANIES}
invested       = {n: 0.0 for n in COMPANIES}
totalinvested  = invested.copy()
sold           = invested.copy()
active_action  = None
input_str      = ""
input_box      = pygame.Rect(800, 600, 200, 40)
popup_surf     = None
popup_rect     = None
news_headline  = ""
news_body      = ""

# Tutorial state
tutorial_slides = [
    "Welcome to PixelInvest!\n\nIn this tutorial you'll learn how to buy and sell.",
    "Use the TAB buttons to switch between companies or see your portfolio.",
    "On a company page you can BUY or SELL shares.\n\nOn Portfolio you see your combined holdings.",
    "That’s it! Let’s get started."
]
tutorial_idx    = 0

# ------------------ Chart functions ------------------
def create_chart(df_daily, years, idx, size, font_path):
    cutoff = datetime.datetime(years[idx], 3, 31)
    start  = cutoff - pd.DateOffset(years=5)
    df_sub = df_daily[(df_daily.index >= start) & (df_daily.index <= cutoff)]
    prop = font_manager.FontProperties(fname=font_path)
    w, h, dpi = size[0], size[1], 100
    fig = Figure(figsize=(w/dpi, h/dpi), dpi=dpi, facecolor="#121212")
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
    fig.tight_layout(rect=[0,0,0.95,1])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)
    return pygame.image.load(buf).convert()

def create_pchart(df_daily, years, idx, size, font_path):
    cutoff = datetime.datetime(years[idx], 3, 31)
    start  = cutoff - pd.DateOffset(years=5)
    df_sub = df_daily[(df_daily.index >= start) & (df_daily.index <= cutoff)]
    prop = font_manager.FontProperties(fname=font_path)
    w, h, dpi = size[0], size[1], 100
    fig = Figure(figsize=(w/dpi, h/dpi), dpi=dpi, facecolor="#121212")
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
    fig.tight_layout(rect=[0,0,0.95,1])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)
    return pygame.image.load(buf).convert()

def create_portfolio_chart(df_daily, shares, years, idx, size, font_path):
    cutoff = datetime.datetime(years[idx], 3, 31)
    start  = cutoff - pd.DateOffset(years=5)
    df_sub = df_daily[(df_daily.index >= start) & (df_daily.index <= cutoff)]
    port_values = pd.Series(0.0, index=df_sub.index)
    for comp_name, num in shares.items():
        ticker = COMPANIES[comp_name]
        if ticker in df_sub.columns:
            port_values += df_sub[ticker] * num
    prop = font_manager.FontProperties(fname=font_path)
    w, h, dpi = size[0], size[1], 100
    fig = Figure(figsize=(w/dpi, h/dpi), dpi=dpi, facecolor="#121212")
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
    fig.tight_layout(rect=[0,0,0.95,1])
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)
    return pygame.image.load(buf).convert()

# ------------------ Initialize Pygame & Data ------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PixelInvest")
clock = pygame.time.Clock()
pixel_font = lambda sz: pygame.font.Font(FONT_PATH, sz)
bg = pygame.image.load(BG_IMAGE).convert()

# Fetch stock data
start_dt   = f"{START_YEAR}-03-01"
HIST_START = "1995-03-01"
today      = datetime.date.today().isoformat()

df_yearly  = yf.download(list(COMPANIES.values()), start=start_dt, end=today)["Close"]
df_yearly  = df_yearly.resample("Y").last()
years      = df_yearly.index.year.tolist()
price_vals = {n: df_yearly[t].to_numpy() for n,t in COMPANIES.items()}

df_daily   = yf.download(list(COMPANIES.values()), start=HIST_START, end=today)["Close"]
df_daily.index = pd.to_datetime(df_daily.index)

# ------------------ Buttons ------------------
tab_buttons = {}
for i, name in enumerate(list(COMPANIES.keys()) + ["Portfolio"]):
    tab_buttons[name] = Button(None, (100 + i*300, 80), name,
                               pixel_font(24), "#ffffff", "#444444")
active_tab = list(tab_buttons.keys())[0]

invest_btns = {
    n: Button(None, (850, 500), "BUY",
              pixel_font(30), "White", "Green")
    for n in COMPANIES
}
sell_btns = {
    n: Button(None, (1150, 500), "SELL",
              pixel_font(30), "White", "RED")
    for n in COMPANIES
}

next_year_btn = Button(None, (SCREEN_WIDTH-180, 40), "Next Year",
                       pixel_font(25), "White", "Green")
play_btn      = Button(pygame.image.load("assets/Play Rect.png"),
                       (SCREEN_WIDTH//2, SCREEN_HEIGHT//2-50),
                       "PLAY", pixel_font(48), "#d7fcd4", "White")
quit_btn      = Button(pygame.image.load("assets/Quit Rect.png"),
                       (SCREEN_WIDTH//2, SCREEN_HEIGHT//2+100),
                       "QUIT", pixel_font(48), "#d7fcd4", "White")
back_btn      = Button(None, (80, 30), "BACK", pixel_font(24), "White", "Green")

# instantiate News button once (position will be overwritten each frame)
news_btn = Button(None, (1000, 400), "News", pixel_font(40), "#ffffff", "#444444")

# Tutorial navigation buttons
next_tut_btn = Button(None, (SCREEN_WIDTH-180, SCREEN_HEIGHT-80),
                      "Next", pixel_font(30), "White", "Green")
help_btn     = Button(None, (SCREEN_WIDTH-180, 30),
                      "Help", pixel_font(24), "#ffffff", "#444444")

# ------------------ Draw functions ------------------
def draw_menu():
    screen.blit(bg, (0, 0))
    title = pixel_font(72).render("PixelInvest", True, "#b68f40")
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 150)))
    m = pygame.mouse.get_pos()
    play_btn.changeColor(m); play_btn.update(screen)
    quit_btn.changeColor(m); quit_btn.update(screen)

def draw_game():
    global news_headline, news_body
    screen.fill((30, 30, 30))
    m = pygame.mouse.get_pos()

    # draw tabs
    for name, btn in tab_buttons.items():
        btn.bg_color = "#888888" if name == active_tab else "#444444"
        btn.changeColor(m); btn.update(screen)

    # header
    screen.blit(pixel_font(25).render(f"Year: {years[year_idx]}", True, "#b68f40"), (700,       30))
    screen.blit(pixel_font(25).render(f"Cash: ${cash:,.0f}", True, "#ffffff"),  (250, 30))

    if active_tab in COMPANIES:
        comp   = active_tab
        ticker = COMPANIES[comp]

        # ── Price & YTD change ────────────────────────────────────────
        cutoff = datetime.datetime(years[year_idx],12,31)
        df_sub = df_daily[df_daily.index <= cutoff]
        current_price = float(df_sub[ticker].iloc[-1])
        if year_idx > 0:
            prev_cutoff = datetime.datetime(years[year_idx-1],12,31)
            prev_df     = df_sub[df_sub.index <= prev_cutoff]
            prev_raw    = prev_df[ticker].iloc[-1] if not prev_df.empty else current_price
        else:
            prev_raw    = current_price
        prev_price = float(prev_raw)
        change     = current_price - prev_price
        pct        = (change/prev_price*100) if prev_price != 0 else 0

        price_surf = pixel_font(48).render(f"${current_price:,.2f}", True, "#ffffff")
        screen.blit(price_surf, (50,120))
        sign = "+" if change >= 0 else ""
        screen.blit(pixel_font(24).render(
            f"{sign}${change:,.2f} ({sign}{pct:.2f}%) YTD",
            True, "#00c853" if change >= 0 else "#d32f2f"
        ), (50,120 + price_surf.get_height() + 5))

        # ── Total Return ───────────────────────────────────────────────
        cost_basis     = totalinvested[comp]
        total_sold     = sold[comp]
        position_value = shares[comp] * current_price
        total_ret      = (total_sold + position_value) - cost_basis
        pct_ret        = (total_ret / cost_basis * 100) if cost_basis != 0 else 0
        tr_font = pygame.font.Font(FONT_PATH,16)
        screen.blit(tr_font.render("Total Return:", True, "#ffffff"), (180,SCREEN_HEIGHT-100))
        sign2 = "+" if total_ret >= 0 else ""
        screen.blit(tr_font.render(
            f"{sign2}${total_ret:,.2f} ({sign2}{pct_ret:.2f}%)",
            True, "#00c853" if total_ret >= 0 else "#d32f2f"
        ), (180 + tr_font.size("Total Return: ")[0] + 20, SCREEN_HEIGHT-100))

        # ── Price Chart ────────────────────────────────────────────────
        chart = create_chart(df_daily[[ticker]], years, year_idx, (700,400), FONT_PATH)
        y_off_chart = 120 + price_surf.get_height() + pixel_font(24).get_linesize() + 20
        screen.blit(chart, (50, y_off_chart))

        # ── CSV Metrics ───────────────────────────────────────────────
        df_cur = csv_dfs[comp]
        cols   = [c for c in df_cur.columns if c.year == years[year_idx]]
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
                surf = pixel_font(20).render(text, True, "#ffffff")
                screen.blit(surf, (780, 220 + i*30))

        # ── News Button with Hover ─────────────────────────────────────
        comp_news = news_data.get(comp, [])
        item = next((it for it in comp_news if it.get("year") == years[year_idx]), None)
        if item:
            news_headline = item["headline"]
            news_body     = item["body"]
            text_color    = "#ffffff"
        else:
            news_headline, news_body, text_color = "No news available", "", "#888888"

        news_x = 780
        news_y = 220 + len(lines)*30 + 20
        news_btn.pos = (news_x, news_y)
        if news_btn.checkForInput(m):
            news_btn.bg_color = "#888888"
        else:
            news_btn.bg_color = "#444444"
        news_btn.text_color = text_color
        news_btn.changeColor(m)
        news_btn.update(screen)

        # ── Shares & Value ─────────────────────────────────────────────
        screen.blit(pixel_font(20).render(f"Shares: {shares[comp]:.2f}", True, "#ffffff"), (300,140))
        screen.blit(pixel_font(20).render(
            f"Total Value: ${shares[comp]*current_price:,.2f}", True, "#ffffff"
        ), (600,140))

        # ── Invest/Sell/Next/Back ──────────────────────────────────────
        invest_btns[comp].changeColor(m); invest_btns[comp].update(screen)
        sell_btns[comp].bg_color = "#555555" if shares[comp]==0 else "Green"
        sell_btns[comp].changeColor(m); sell_btns[comp].update(screen)
        next_year_btn.changeColor(m); next_year_btn.update(screen)
        back_btn.changeColor(m); back_btn.update(screen)

        if active_action and active_action[1] == comp:
            pygame.draw.rect(screen, (255,255,255), input_box, 2)
            screen.blit(pixel_font(20).render(input_str, True, "#ffffff"),
                        (input_box.x+5, input_box.y+5))

    else:
        # ── Portfolio View ─────────────────────────────────────────────
        cutoff = datetime.datetime(years[year_idx],12,31)
        df_sub = df_daily[df_daily.index <= cutoff]
        port_values = pd.Series(0.0, index=df_sub.index)
        for name, num in shares.items():
            tt = COMPANIES[name]
            if tt in df_sub.columns:
                port_values += df_sub[tt] * num

        current = port_values.iloc[-1]
        if year_idx > 0:
            prev_cutoff  = datetime.datetime(years[year_idx-1],12,31)
            prev_series  = port_values[port_values.index <= prev_cutoff]
            prev = prev_series.iloc[-1] if not prev_series.empty else port_values.iloc[0]
        else:
            prev = current

        change = current - prev
        pct    = (change/prev*100) if prev != 0 else 0

        screen.blit(pixel_font(72).render(f"${current:,.2f}", True, "#ffffff"), (50,120))
        sign    = "+" if change >= 0 else ""
        screen.blit(pixel_font(24).render(
            f"{sign}${change:,.2f} ({sign}{pct:.2f}%) YTD",
            True, "#00c853" if change >= 0 else "#d32f2f"
        ), (50, 120 + pixel_font(72).get_linesize() + 5))

        # ── Two charts side by side ────────────────────────────────────
        w, h = (SCREEN_WIDTH - 400)//2, 400
        y0   = 120 + pixel_font(72).get_linesize() + pixel_font(24).get_linesize() + 20

        port_surf  = create_portfolio_chart(df_daily, shares, years, year_idx, (w,h), FONT_PATH)
        price_surf = create_pchart(df_daily, years, year_idx, (w,h), FONT_PATH)
        screen.blit(port_surf,  (50, y0))
        screen.blit(price_surf, (50 + w + 50, y0))

        # ── Company list ──────────────────────────────────────────────
        pf = pixel_font(24)
        for i, name in enumerate(COMPANIES):
            tt = COMPANIES[name]
            ns = shares[name]
            lp = df_sub[tt].iloc[-1] if tt in df_sub.columns else 0
            y1 = y0 + i * 60
            screen.blit(pf.render(name, True, "#ffffff"),        (50 + w*2 + 100, y1))
            screen.blit(pf.render(f"{ns:.2f} shares", True, "#aaaaaa"),
                        (50 + w*2 + 250, y1))
            screen.blit(pf.render(f"${lp:,.2f}", True, "#ffffff"),
                        (50 + w*2 + 100, y1 + 24))

        # Draw help button
        help_btn.changeColor(m); help_btn.update(screen)

        next_year_btn.changeColor(m); next_year_btn.update(screen)
        back_btn.changeColor(m);    back_btn.update(screen)

    # ── Pop‑up Overlay ─────────────────────────────────────────────
    if popup_surf is not None and isinstance(popup_rect, pygame.Rect):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        screen.blit(overlay, (0,0))
        screen.blit(popup_surf, popup_rect)

def draw_tutorial():
    screen.fill((20,20,20))
    lines = tutorial_slides[tutorial_idx].split("\n")
    font = pygame.font.Font(FONT_PATH, 28)
    block_h = font.get_linesize() * len(lines)
    y0 = (SCREEN_HEIGHT - block_h)//2
    for i, ln in enumerate(lines):
        txt = font.render(ln, True, "#ffffff")
        x = (SCREEN_WIDTH - txt.get_width())//2
        screen.blit(txt, (x, y0 + i*font.get_linesize()))
    m = pygame.mouse.get_pos()
    next_tut_btn.changeColor(m); next_tut_btn.update(screen)

# ------------------ Main Loop ------------------
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if popup_surf is not None:
            if e.type == pygame.MOUSEBUTTONDOWN:
                popup_surf = None
                popup_rect = None
            continue

        mpos = pygame.mouse.get_pos()

        # ── MENU Input ────────────────────────────────────────────────
        if state == "MENU":
            if e.type == pygame.MOUSEBUTTONDOWN:
                if play_btn.checkForInput(mpos):
                    tutorial_idx = 0
                    state = "TUTORIAL"
                elif quit_btn.checkForInput(mpos):
                    pygame.quit()
                    sys.exit()

        # ── TUTORIAL Input ────────────────────────────────────────────
        elif state == "TUTORIAL":
            if e.type == pygame.MOUSEBUTTONDOWN and next_tut_btn.checkForInput(mpos):
                tutorial_idx += 1
                if tutorial_idx >= len(tutorial_slides):
                    active_tab = "Portfolio"
                    state = "GAME"
            continue

        # ── GAME Input & other clicks ───────────────────────────────
        else:
            # ── News Button Click ─────────────────────────────────────────
            if e.type == pygame.MOUSEBUTTONDOWN and active_tab in COMPANIES:
                if news_btn.checkForInput(mpos):
                    all_lines = [news_headline] + textwrap.wrap(news_body or "", width=40)
                    headline_font = pygame.font.Font(FONT_PATH, 24)
                    headline_font.set_underline(True)
                    body_font     = pygame.font.Font(FONT_PATH, 24)
                    lh = headline_font.get_linesize()
                    if len(all_lines) > 1:
                        widths = [headline_font.size(all_lines[0])[0]] + \
                                 [body_font.size(ln)[0] for ln in all_lines[1:]]
                        w_popup = max(widths) + 20
                    else:
                        w_popup = headline_font.size(all_lines[0])[0] + 20
                    h_popup = lh * len(all_lines) + 20
                    popup_surf = pygame.Surface((w_popup, h_popup), pygame.SRCALPHA)
                    popup_surf.fill((47,47,47,230))
                    for i, ln in enumerate(all_lines):
                        if i == 0:
                            txt = headline_font.render(ln, True, (255,165,0))
                            x = (w_popup - txt.get_width()) // 2
                        else:
                            txt = body_font.render(ln, True, "#ffffff")
                            x = 10
                        popup_surf.blit(txt, (x, 10 + i * lh))
                    popup_rect = popup_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                    continue

            # ── Typing input for BUY/SELL ────────────────────────────────
            if active_action and e.type == pygame.KEYDOWN:
                if e.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                elif e.key == pygame.K_RETURN:
                    mode, comp = active_action
                    price      = price_vals[comp][year_idx]
                    try:
                        num = int(input_str)
                    except:
                        num = 0
                    msg = ""
                    if mode == "invest":
                        cost = num * price
                        if num <= 0:
                            msg = "Enter at least 1 share to buy."
                        elif cost > cash:
                            msg = f"Not enough cash: need ${cost:,.2f}."
                        else:
                            shares[comp]        += num
                            invested[comp]      += cost
                            totalinvested[comp] += cost
                            cash                -= cost
                            msg = f"Bought {num} share(s) for ${cost:,.2f}!"
                    else:
                        to_sell = min(num, int(shares[comp]))
                        if to_sell <= 0:
                            msg = "No shares to sell."
                        else:
                            proceeds = to_sell * price
                            shares[comp]     -= to_sell
                            sold[comp]       += proceeds
                            invested[comp]   -= proceeds
                            cash             += proceeds
                            msg = f"Sold {to_sell} share(s) for ${proceeds:,.2f}!"
                    lines = textwrap.wrap(msg, width=60)
                    font  = pygame.font.Font(FONT_PATH,24)
                    lh    = font.get_linesize()
                    w_p   = max(font.size(ln)[0] for ln in lines) + 20
                    h_p   = lh * len(lines) + 20
                    popup_surf = pygame.Surface((w_p,h_p), pygame.SRCALPHA)
                    popup_surf.fill((47,47,47,230))
                    for i, ln in enumerate(lines):
                        popup_surf.blit(font.render(ln,True,"#ffffff"), (10,10+i*lh))
                    popup_rect = pygame.Rect((SCREEN_WIDTH//2 - w_p//2, SCREEN_HEIGHT//2 - h_p//2), (w_p,h_p))
                    active_action = None
                    input_str     = ""
                elif e.unicode.isdigit() or e.unicode == ".":
                    input_str += e.unicode

            # ── Other button clicks ─────────────────────────────────────
            if e.type == pygame.MOUSEBUTTONDOWN and not active_action:
                # BACK
                if back_btn.checkForInput(mpos):
                    state    = "MENU"
                    year_idx = 0
                    cash     = START_CASH
                    shares   = {n:0.0 for n in COMPANIES}

                # TAB SWITCH
                for name, btn in tab_buttons.items():
                    if btn.checkForInput(mpos):
                        active_tab = name

                # BUY/SELL
                if active_tab in COMPANIES:
                    if invest_btns[active_tab].checkForInput(mpos):
                        active_action = ("invest", active_tab); input_str = ""
                    elif sell_btns[active_tab].checkForInput(mpos) and shares[active_tab] > 0:
                        active_action = ("sell", active_tab); input_str = ""

                # NEXT YEAR
                if next_year_btn.checkForInput(mpos) and year_idx < len(years)-1:
                    year_idx += 1

                # HELP in Portfolio
                if active_tab == "Portfolio" and help_btn.checkForInput(mpos):
                    tutorial_idx = 0
                    state = "TUTORIAL"

    # ── RENDER ───────────────────────────────────────────────────────
    if state == "MENU":
        draw_menu()
    elif state == "TUTORIAL":
        draw_tutorial()
    else:
        draw_game()

    pygame.display.flip()
    clock.tick(FPS)
