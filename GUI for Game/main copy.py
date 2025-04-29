import io
import sys
import datetime

import pygame
import pandas as pd
import yfinance as yf

import matplotlib
matplotlib.use("Agg")  # render without a display
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib import font_manager

# ------------------ SETTINGS ------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FPS = 30

FONT_PATH = "assets/font.ttf"  # your pixel font file
BG_IMAGE = "assets/Background.png"

COMPANIES = {
    "Nintendo": "NTDOY",
    "TakeTwo": "TTWO",
    "EA": "EA"
}
START_YEAR = 2000
START_CAPITAL = 10000

# ------------------ CHART FUNCTION ------------------
def create_stock_chart_surface(df_daily, years, current_year_idx, size, font_path):
    """
    Given the full daily-Close DataFrame, the list of annual 'years',
    and the current_year_idx, plot only data up to that year and return
    a pygame.Surface of the chart in dark theme, using the pixel font.
    """
    # determine cutoff date (end of that calendar year)
    cutoff = datetime.datetime(years[current_year_idx], 12, 31)
    df_sub = df_daily[df_daily.index <= cutoff]

    # register pixel font for matplotlib
    prop = font_manager.FontProperties(fname=font_path)

    width, height = size
    dpi = 100
    fig = Figure(figsize=(width/dpi, height/dpi), dpi=dpi, facecolor="#121212")
    FigureCanvas(fig)  # bind canvas
    ax = fig.add_subplot(111)

    # styling
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
  

    # plot each ticker
    for ticker in df_sub.columns:
        ax.plot(df_sub.index, df_sub[ticker], label=ticker, linewidth=1.5)

    ax.set_xlabel("Date")
    ax.set_ylabel("Price (USD)")
    ax.legend(facecolor="#121212", edgecolor="#2f2f2f", labelcolor="white", loc="upper left", prop=prop)

    fig.tight_layout(pad=1)

    # render to pygame surface
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)
    surf = pygame.image.load(buf).convert()
    return surf

# ------------------ INIT & DATA ------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PixelInvest: Retro Stock Simulator")
clock = pygame.time.Clock()

pixel_font = lambda size: pygame.font.Font(FONT_PATH, size)
bg_image = pygame.image.load(BG_IMAGE).convert()

end_date = datetime.date.today().isoformat()
start_date = f"{START_YEAR}-01-01"

# for game-year progression
df_yearly = yf.download(list(COMPANIES.values()), start=start_date, end=end_date)["Close"]
df_yearly = df_yearly.resample('Y').last()
years = df_yearly.index.year.tolist()
price_vals = {
    name: df_yearly[ticker].to_numpy()
    for name, ticker in COMPANIES.items()
}
n_years = len(years)

# for chart
df_daily = yf.download(list(COMPANIES.values()), start=start_date, end=end_date)["Close"]
df_daily.index = pd.to_datetime(df_daily.index)

chart_size = (SCREEN_WIDTH - 400, 400)
current_year_idx = 0
chart_surface = create_stock_chart_surface(df_daily, years, current_year_idx, chart_size, FONT_PATH)

# game state
state = "MENU"
cash = START_CAPITAL
shares = {name: 0.0 for name in COMPANIES}

# buttons
from button import Button

invest_btns = {}
sell_btns = {}
for i, name in enumerate(COMPANIES):
    invest_btns[name] = Button(None, (200 + i*400, SCREEN_HEIGHT - 120),
                               f"Invest {name}", pixel_font(24), "White", "Green")
    sell_btns[name] = Button(None, (200 + i*400, SCREEN_HEIGHT - 70),
                             f"Sell {name}", pixel_font(24), "White", "Green")

play_btn = Button(pygame.image.load("assets/Play Rect.png"),
                  (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50),
                  "PLAY", pixel_font(48), "#d7fcd4", "White")
quit_btn = Button(pygame.image.load("assets/Quit Rect.png"),
                  (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100),
                  "QUIT", pixel_font(48), "#d7fcd4", "White")
back_btn = Button(None, (80, 30), "BACK", pixel_font(24), "White", "Green")

# ------------------ DRAW ------------------
def draw_menu():
    screen.blit(bg_image, (0, 0))
    title = pixel_font(72).render("PixelInvest", True, "#b68f40")
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 150)))
    m = pygame.mouse.get_pos()
    play_btn.changeColor(m); play_btn.update(screen)
    quit_btn.changeColor(m); quit_btn.update(screen)

def draw_game():
    global cash, current_year_idx, chart_surface
    screen.fill((30, 30, 30))

    hf = pixel_font(25)
    screen.blit(hf.render(f"Year: {years[current_year_idx]}", True, "#b68f40"), (700, 30))
    screen.blit(hf.render(f"Cash: ${cash:,.0f}", True, "#ffffff"), (250, 30))

    # chart
    chart_rect = pygame.Rect(50, 120, *chart_size)
    screen.blit(chart_surface, chart_rect.topleft)

    #ratios
    

    # Holdings (no background rectangle)
    panel_x = SCREEN_WIDTH - 1250
    panel_y = 70
    panel_font = pixel_font(20)
    spacing= 450
    for idx, name in enumerate(COMPANIES):
        text = f"{name}: {shares[name]:.2f} sh"
        surf = panel_font.render(text, True, "#ffffff")
        x = panel_x + idx * spacing
        # just blit text at an offset—no rect
        screen.blit(surf, (x + 10, panel_y + 10))

    m = pygame.mouse.get_pos()
    if current_year_idx < n_years - 1:
        for name in COMPANIES:
            invest_btns[name].changeColor(m); invest_btns[name].update(screen)
            if shares[name] > 0:
                sell_btns[name].changeColor(m); sell_btns[name].update(screen)
    else:
        over = hf.render(f"Game Over! Final Cash: ${cash:,.0f}", True, "#ffffff")
        screen.blit(over, over.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))

    back_btn.changeColor(m); back_btn.update(screen)

# ------------------ MAIN LOOP ------------------
while True:
    m = pygame.mouse.get_pos()
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        if e.type == pygame.MOUSEBUTTONDOWN:
            if state == "MENU":
                if play_btn.checkForInput(m): state = "GAME"
                if quit_btn.checkForInput(m): pygame.quit(); sys.exit()

            elif state == "GAME":
                if back_btn.checkForInput(m):
                    state = "MENU"
                    # reset chart to year 0
                    current_year_idx = 0
                    cash = START_CAPITAL
                    shares = {name: 0.0 for name in COMPANIES}
                    chart_surface = create_stock_chart_surface(
                        df_daily, years, current_year_idx, chart_size, FONT_PATH
                    )

                if current_year_idx < n_years - 1:
                    acted = False
                    for name in COMPANIES:
                        if invest_btns[name].checkForInput(m) and cash > 0:
                            price = price_vals[name][current_year_idx]
                            shares[name] = cash / price
                            cash = 0
                            acted = True
                        if sell_btns[name].checkForInput(m) and shares[name] > 0:
                            price = price_vals[name][current_year_idx]
                            cash = shares[name] * price
                            shares[name] = 0
                            acted = True
                    if acted:
                        current_year_idx += 1
                        chart_surface = create_stock_chart_surface(
                            df_daily, years, current_year_idx, chart_size, FONT_PATH
                        )

    if state == "MENU":
        draw_menu()
    else:
        draw_game()

    pygame.display.flip()
    clock.tick(FPS)
