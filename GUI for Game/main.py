import pygame
import sys
import pandas as pd
import yfinance as yf
import datetime

# ------------------ SETTINGS ------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FPS = 30
FONT_PATH = "assets/font.ttf"  # Pixel font for retro aesthetic
BG_IMAGE = "assets/Background.png"

# Companies to invest in and their tickers
COMPANIES = {
    "Nintendo": "NTDOY",
    "TakeTwo": "TTWO",
    "EA": "EA"
}
START_YEAR = 2000
START_CAPITAL = 10000

# ------------------ INITIALIZATION ------------------
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PixelInvest: Retro Stock Simulator")
clock = pygame.time.Clock()

# Load font and background
pixel_font = lambda size: pygame.font.Font(FONT_PATH, size)
bg_image = pygame.image.load(BG_IMAGE).convert()

# Button helper
from button import Button

def draw_button(btn, mouse_pos):
    btn.changeColor(mouse_pos)
    btn.update(screen)

# ------------------ DATA FETCH ------------------
end_date = datetime.date.today().isoformat()
start_date = f"{START_YEAR}-01-01"
df_raw = yf.download(list(COMPANIES.values()), start=start_date, end=end_date)["Close"]
# Resample to yearly close (last trading day of year)
price_yearly = df_raw.resample('Y').last()
years = price_yearly.index.year.tolist()

# Prepare price arrays
price_vals = {name: price_yearly[ticker].to_numpy() for name, ticker in COMPANIES.items()}
n_years = len(years)

# ------------------ GAME STATES ------------------
state = "MENU"
cash = START_CAPITAL
current_year_idx = 0
# Track shares held per company
shares = {name: 0.0 for name in COMPANIES}

# Buttons: Invest / Sell per company
invest_btns = {}
sell_btns = {}
for i, name in enumerate(COMPANIES):
    invest_btns[name] = Button(
        image=None,
        pos=(200 + i*300, SCREEN_HEIGHT - 120),
        text_input=f"Invest {name}",
        font=pixel_font(28),
        base_color="White",
        hovering_color="Green"
    )
    sell_btns[name] = Button(
        image=None,
        pos=(200 + i*300, SCREEN_HEIGHT - 70),
        text_input=f"Sell {name}",
        font=pixel_font(28),
        base_color="White",
        hovering_color="Green"
    )

# Main menu buttons
play_btn = Button(
    image=pygame.image.load("assets/Play Rect.png"),
    pos=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50),
    text_input="PLAY",
    font=pixel_font(48),
    base_color="#d7fcd4",
    hovering_color="White"
)
quit_btn = Button(
    image=pygame.image.load("assets/Quit Rect.png"),
    pos=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 100),
    text_input="QUIT",
    font=pixel_font(48),
    base_color="#d7fcd4",
    hovering_color="White"
)

# Back button for game screen
back_btn = Button(
    image=None,
    pos=(80, 50),
    text_input="BACK",
    font=pixel_font(24),
    base_color="White",
    hovering_color="Green"
)

# ------------------ DRAW FUNCTIONS ------------------
def draw_menu():
    screen.blit(bg_image, (0, 0))
    title = pixel_font(72).render("PixelInvest", True, "#b68f40")
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 150)))
    mpos = pygame.mouse.get_pos()
    draw_button(play_btn, mpos)
    draw_button(quit_btn, mpos)


def draw_game():
    global cash, current_year_idx
    screen.fill((30, 30, 30))

    # Header: Year & Cash
    header_font = pixel_font(36)
    year_surf = header_font.render(f"Year: {years[current_year_idx]}", True, "#b68f40")
    cash_surf = header_font.render(f"Cash: ${cash:,.0f}", True, "#ffffff")
    screen.blit(year_surf, (50, 30))
    screen.blit(cash_surf, (50, 70))

    # Chart area
    chart_rect = pygame.Rect(100, 120, SCREEN_WIDTH - 400, 400)
    pygame.draw.rect(screen, (20, 20, 20), chart_rect)

    # Prepare scale
    all_vals = []
    for v in price_vals.values():
        all_vals.extend(v[:current_year_idx+1])
    mn, mx = min(all_vals), max(all_vals)
    def x_of(i): return int(chart_rect.left + i * chart_rect.width / (n_years - 1))
    def y_of(p): return int(chart_rect.bottom - (p - mn) / (mx - mn) * chart_rect.height)

    colors = {"Nintendo": (255, 100, 100), "TakeTwo": (100, 255, 100), "EA": (100, 100, 255)}
    for name, vals in price_vals.items():
        pts = [(x_of(i), y_of(vals[i])) for i in range(current_year_idx+1)]
        if len(pts) > 1:
            pygame.draw.lines(screen, colors[name], False, pts, 3)

    # Holdings panel
    panel_rect = pygame.Rect(SCREEN_WIDTH - 280, 120, 240, 200)
    pygame.draw.rect(screen, (20, 20, 20), panel_rect)
    panel_font = pixel_font(24)
    for idx, name in enumerate(COMPANIES):
        text = f"{name}: {shares[name]:.2f} sh"
        surf = panel_font.render(text, True, "#ffffff")
        screen.blit(surf, (panel_rect.left + 10, panel_rect.top + 10 + idx * 40))

    # Action buttons
    mpos = pygame.mouse.get_pos()
    if current_year_idx < n_years - 1:
        for name in COMPANIES:
            draw_button(invest_btns[name], mpos)
            if shares[name] > 0:
                draw_button(sell_btns[name], mpos)
    else:
        end_surf = header_font.render(f"Game Over! Final Cash: ${cash:,.0f}", True, "#ffdd00")
        screen.blit(end_surf, end_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))

    # Back button
    draw_button(back_btn, mpos)

# ------------------ MAIN LOOP ------------------
while True:
    mpos = pygame.mouse.get_pos()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if state == "MENU":
                if play_btn.checkForInput(mpos):
                    state = "GAME"
                if quit_btn.checkForInput(mpos):
                    pygame.quit()
                    sys.exit()
            elif state == "GAME":
                if back_btn.checkForInput(mpos):
                    state = "MENU"
                # Handle invest/sell
                if current_year_idx < n_years - 1:
                    action_taken = False
                    for name in COMPANIES:
                        if invest_btns[name].checkForInput(mpos) and cash > 0:
                            price = price_vals[name][current_year_idx]
                            shares[name] = cash / price
                            cash = 0
                            action_taken = True
                        if sell_btns[name].checkForInput(mpos) and shares[name] > 0:
                            price = price_vals[name][current_year_idx]
                            cash = shares[name] * price
                            shares[name] = 0
                            action_taken = True
                    if action_taken:
                        current_year_idx += 1

    if state == "MENU":
        draw_menu()
    elif state == "GAME":
        draw_game()

    pygame.display.update()
    clock.tick(FPS)