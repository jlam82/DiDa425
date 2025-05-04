import io  # for in-memory byte buffers when saving Matplotlib figures
import sys  # to use sys.exit() for quitting the program
import datetime  # provides date and time functionality

import pygame  # game library for window, input, and rendering
import pandas as pd  # data analysis library for CSV reading and dataframes
import yfinance as yf  # library to fetch stock data from Yahoo Finance

from matplotlib.figure import Figure  # object to create figures in Matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas  # renderer to draw figures to a buffer
from matplotlib import font_manager  # utility to load TTF fonts into Matplotlib
from matplotlib.ticker import FuncFormatter, MaxNLocator  # utilities for axis tick formatting

# ------------------ LOAD CSV DATA ------------------
csv_dfs = {  # dictionary storing DataFrames for each company's annual data
    "Nintendo": pd.read_csv(
        "Nintendo Annual CSV - Sheet1.csv",  # path to CSV file for Nintendo
        index_col=0,  # use first column as the DataFrame index
        thousands=","  # treat commas as thousand separators
    ),
    "TakeTwo": pd.read_csv(
        "Take Two Annual Data - Sheet1.csv",  # path to CSV file for TakeTwo
        index_col=0,  # use first column as index
        thousands=","  # treat commas as thousand separators
    ),
    "EA": pd.read_csv(
        "EA Annual CSV - Sheet1.csv",  # path to CSV file for EA
        index_col=0,  # use first column as index
        thousands=","  # treat commas as thousand separators
    ),
}
# convert each DataFrame’s column labels (string dates) into pandas datetime objects
for df in csv_dfs.values():
    df.columns = pd.to_datetime(df.columns, format="%Y-%m-%d")  # parse dates in YYYY-MM-DD format

# ------------------ SETTINGS ------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720  # dimensions of the game window
FPS = 30  # target frames per second

FONT_PATH  = "assets/font.ttf"  # path to custom font file
BG_IMAGE   = "assets/Background.png"  # path to background image file
COMPANIES  = {"Nintendo": "NTDOY", "TakeTwo": "TTWO", "EA": "EA"}  # mapping of display names to tickers
START_YEAR = 2002  # first year of simulation
START_CASH = 10000  # initial cash balance in USD

# ------------------ CHART FUNCTIONS ------------------
def create_chart(df_daily, years, idx, size, font_path):
    # Determine the cutoff date as March 31 of the selected year
    cutoff = datetime.datetime(years[idx], 3, 31)
    # Calculate the start date 5 years before the cutoff
    start = cutoff - pd.DateOffset(years=5)
    # Slice the daily data to include only dates between start and cutoff
    df_sub = df_daily[(df_daily.index >= start) & (df_daily.index <= cutoff)]

    # Load the custom font for Matplotlib
    prop = font_manager.FontProperties(fname=font_path)
    # Unpack the desired chart size into width and height
    w, h = size
    # Set the dots-per-inch for the figure
    dpi = 100
    # Create a new Matplotlib Figure with the specified size, dpi, and background color
    fig = Figure(figsize=(w/dpi, h/dpi), dpi=dpi, facecolor="#121212")
    # Attach a canvas so we can render into a buffer later
    FigureCanvas(fig)
    # Add a single subplot (axes) to the figure
    ax = fig.add_subplot(111)

    # Set the figure background color
    fig.patch.set_facecolor("#121212")
    # Set the axes background color
    ax.set_facecolor("#121212")

    # Style each spine (border) of the plot
    for spine in ax.spines.values():
        spine.set_color("#2f2f2f")

    # Draw a grid with dashed lines
    ax.grid(color="#2f2f2f", linestyle="--", linewidth=0.5)

    # Style the tick marks and labels
    ax.tick_params(colors="white", labelsize=10)
    # Apply the custom font and white color to all tick labels
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(prop)
        label.set_color("white")

    # Adjust layout to respect the given rectangle (leaves space on the right)
    fig.tight_layout(rect=[0, 0, 0.95, 1])
    # Set the x-axis label
    ax.set_xlabel("Date", fontproperties=prop, color="white")
    # Set the y-axis label
    ax.set_ylabel("Price (USD)", fontproperties=prop, color="white")

    # Plot a line for each ticker in the subsetted data
    for ticker in df_sub.columns:
        ax.plot(
            df_sub.index,               # x-values (dates)
            df_sub[ticker],             # y-values (prices)
            label=ticker,               # legend label
            linewidth=1.5,              # line thickness
            color="#00fc17"             # bright green color
        )

    # Add a legend in the upper-left, styled to match the dark theme
    ax.legend(
        loc="upper left",
        facecolor="#121212",
        edgecolor="#2f2f2f",
        labelcolor="white",
        prop=prop
    )

    # Readjust layout now that the legend and labels are in place
    fig.tight_layout(rect=[0, 0, 0.95, 1])

    # Render the figure to an in-memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)
    # Load the buffer into a Pygame surface and return it
    return pygame.image.load(buf).convert()


def create_pchart(df_daily, years, idx, size, font_path):
    # Determine the cutoff date as March 31 of the selected year
    cutoff = datetime.datetime(years[idx], 3, 31)
    # Calculate the start date 5 years before the cutoff
    start = cutoff - pd.DateOffset(years=5)
    # Slice the daily data to include only dates between start and cutoff
    df_sub = df_daily[(df_daily.index >= start) & (df_daily.index <= cutoff)]

    # Load the custom font for Matplotlib
    prop = font_manager.FontProperties(fname=font_path)
    # Unpack the desired chart size into width and height
    w, h = size
    # Set the dots-per-inch for the figure
    dpi = 100
    # Create a new Matplotlib Figure with the specified size, dpi, and background color
    fig = Figure(figsize=(w/dpi, h/dpi), dpi=dpi, facecolor="#121212")
    # Attach a canvas so we can render into a buffer later
    FigureCanvas(fig)
    # Add a single subplot (axes) to the figure
    ax = fig.add_subplot(111)

    # Set the figure background color
    fig.patch.set_facecolor("#121212")
    # Set the axes background color
    ax.set_facecolor("#121212")

    # Style each spine (border) of the plot
    for spine in ax.spines.values():
        spine.set_color("#2f2f2f")

    # Draw a grid with dashed lines
    ax.grid(color="#2f2f2f", linestyle="--", linewidth=0.5)

    # Style the tick marks and labels
    ax.tick_params(colors="white", labelsize=10)
    # Apply the custom font and white color to all tick labels
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(prop)
        label.set_color("white")

    # Adjust layout to respect the given rectangle (leaves space on the right)
    fig.tight_layout(rect=[0, 0, 0.95, 1])
    # Set the x-axis label
    ax.set_xlabel("Date", fontproperties=prop, color="white")
    # Set the y-axis label
    ax.set_ylabel("Price (USD)", fontproperties=prop, color="white")

    # Plot a line for each ticker in the subsetted data
    for ticker in df_sub.columns:
        ax.plot(
            df_sub.index,   # x-values (dates)
            df_sub[ticker], # y-values (prices)
            label=ticker,   # legend label
            linewidth=1.5   # line thickness
            # default line color since none is specified
        )

    # Add a legend in the upper-left, styled to match the dark theme
    ax.legend(
        loc="upper left",
        facecolor="#121212",
        edgecolor="#2f2f2f",
        labelcolor="white",
        prop=prop
    )

    # Readjust layout now that the legend and labels are in place
    fig.tight_layout(rect=[0, 0, 0.95, 1])

    # Render the figure to an in-memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)
    # Load the buffer into a Pygame surface and return it
    return pygame.image.load(buf).convert()


def create_portfolio_chart(df_daily, shares, years, idx, size, font_path):
    # Determine the cutoff date as March 31 of the selected year
    cutoff = datetime.datetime(years[idx], 3, 31)
    # Calculate the start date 5 years before the cutoff
    start = cutoff - pd.DateOffset(years=5)
    # Slice the daily data to include only dates between start and cutoff
    df_sub = df_daily[(df_daily.index >= start) & (df_daily.index <= cutoff)]

    # Build the portfolio value time series by summing each holding’s value
    port_values = pd.Series(0.0, index=df_sub.index)  # initialize series at zero
    for comp_name, num_shares in shares.items():
        # Map the company name to its ticker symbol
        ticker = COMPANIES[comp_name]
        # Only add if we have data for that ticker in df_sub
        if ticker in df_sub.columns:
            # Increment the portfolio value by price * shares for this company
            port_values += df_sub[ticker] * num_shares

    # Load the custom font for axis labels and ticks
    prop = font_manager.FontProperties(fname=font_path)
    # Unpack the desired chart size into width and height
    w, h = size
    # Set the resolution for the figure
    dpi = 100
    # Create a new Matplotlib Figure with dark background
    fig = Figure(figsize=(w/dpi, h/dpi), dpi=dpi, facecolor="#121212")
    # Attach a canvas so we can render into a buffer
    FigureCanvas(fig)
    # Add a single subplot (axes) to the figure
    ax = fig.add_subplot(111)

    # Set the figure background color
    fig.patch.set_facecolor("#121212")
    # Set the axes background color
    ax.set_facecolor("#121212")

    # Style each spine (border) of the plot
    for spine in ax.spines.values():
        spine.set_color("#2f2f2f")

    # Draw a dashed grid
    ax.grid(color="#2f2f2f", linestyle="--", linewidth=0.5)

    # Style the tick marks and labels
    ax.tick_params(colors="white", labelsize=10)
    # Apply the custom font and white color to all tick labels
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontproperties(prop)
        label.set_color("white")

    # Define a formatter that converts large values to 'k'
    def y_fmt(x, pos):
        x = int(x)
        if abs(x) >= 1000:
            return f"{x//1000}k"
        return str(x)
    # Apply the formatter to the y-axis
    ax.yaxis.set_major_formatter(FuncFormatter(y_fmt))

    # Set the x-axis label
    ax.set_xlabel("Date", fontproperties=prop, color="white")
    # Set the y-axis label
    ax.set_ylabel("Portfolio Value (USD)", fontproperties=prop, color="white")

    # Plot the portfolio value line
    ax.plot(
        port_values.index,
        port_values.values,
        label="Portfolio",
        linewidth=1.5,
        color="#00fc17"
    )

    # Add a legend styled for dark theme
    ax.legend(
        loc="upper left",
        facecolor="#121212",
        edgecolor="#2f2f2f",
        labelcolor="white",
        prop=prop
    )

    # Adjust layout to ensure nothing is clipped
    fig.tight_layout(rect=[0, 0, 0.95, 1])

    # Render the figure to an in-memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=fig.get_facecolor())
    buf.seek(0)
    # Load the buffer into a Pygame Surface and return it
    return pygame.image.load(buf).convert()


# ------------------ INIT & DATA ------------------
pygame.init()  # initialize Pygame modules
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # create window
pygame.display.set_caption("PixelInvest")  # set window title
clock = pygame.time.Clock()  # clock for controlling FPS

pixel_font = lambda sz: pygame.font.Font(FONT_PATH, sz)  # helper to load pixel font
bg = pygame.image.load(BG_IMAGE).convert()  # load and convert background image

start_dt = f"{START_YEAR}-03-01"  # start date for yearly data fetch
HIST_START = "1995-03-01"   # start date for daily data fetch

today = datetime.date.today().isoformat()  # current date for data fetch

# yearly data for buttons (not used in tabs directly but for price_vals)
df_yearly = yf.download(list(COMPANIES.values()), start=start_dt, end=today)["Close"]  # fetch yearly close prices
df_yearly = df_yearly.resample("Y").last()  # take last trading day per year
years = df_yearly.index.year.tolist()  # list of years for navigation
price_vals = {n: df_yearly[t].to_numpy() for n, t in COMPANIES.items()}  # store yearly prices

# daily data for charts
df_daily = yf.download(
    list(COMPANIES.values()),
    start=HIST_START,
    end=today,
)["Close"]  # fetch daily close prices
df_daily.index = pd.to_datetime(df_daily.index)  # ensure datetime index
chart_size = (700, 400)  # chart dimensions
year_idx = 0  # start at first year

# ------------------ GAME STATE ------------------
state         = "MENU"  # current screen: MENU or GAME
cash          = START_CASH  # player cash balance
shares        = {n: 0.0 for n in COMPANIES}  # shares held per company
# net cash you’ve put into each stock (buys add, sells subtract)
invested = {name: 0.0 for name in COMPANIES}  # track cash invested per company
totalinvested = {name: 0.0 for name in COMPANIES}  # alias for invested
sold = {name: 0.0 for name in COMPANIES}  # track cash from sells per company

active_action = None      # ("invest"|"sell", company_name) for input mode
input_str     = ""        # buffer for user-typed numbers
input_box     = pygame.Rect(800, 600, 200, 40)  # rectangle defining input box region

popup_msg   = None  # current pop-up message string
popup_rect  = None  # rectangle for pop-up text

# ------------------ TAB BUTTONS ------------------
from button import Button  # import custom Button helper

tab_buttons = {}
x_start = 100  # starting x position for tabs
spacing = 300  # spacing between tabs
all_tabs = list(COMPANIES.keys()) + ["Portfolio"]  # list of all tab names
for i, name in enumerate(all_tabs):
    x = x_start + i * spacing  # x coordinate for this tab
    tab_buttons[name] = Button(
        None,  # no image background
        (x, 80),  # position
        name,  # label text
        pixel_font(24),  # font for label
        "#ffffff",  # text color
        "#444444"  # background color
    )
active_tab = all_tabs[0]  # start on the first tab

# ------------------ OTHER BUTTONS ------------------
invest_btns = {}  # dict for BUY buttons
sell_btns   = {}  # dict for SELL buttons
for i, name in enumerate(COMPANIES):
    x_off = 200  # base x offset for buttons
    invest_btns[name] = Button(None, (x_off, SCREEN_HEIGHT - 70),
                               f"BUY", pixel_font(30), "White", "Green")  # BUY button
    sell_btns[name] = Button(None, (x_off+300, SCREEN_HEIGHT - 70),
                             f"SELL", pixel_font(30), "White", "Green")  # SELL button

next_year_btn = Button(None, (SCREEN_WIDTH - 180, 40),
                       "Next Year", pixel_font(25), "White", "Green")  # advance year
play_btn = Button(pygame.image.load("assets/Play Rect.png"),
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50),
                  "PLAY", pixel_font(48), "#d7fcd4", "White")  # play button
quit_btn = Button(pygame.image.load("assets/Quit Rect.png"),
                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100),
                  "QUIT", pixel_font(48), "#d7fcd4", "White")  # quit button
back_btn = Button(None, (80, 30), "BACK", pixel_font(24), "White", "Green")  # back button

# ------------------ DRAW FUNCTIONS ------------------
def draw_menu():
    screen.blit(bg, (0, 0))  # draw background image
    title = pixel_font(72).render("PixelInvest", True, "#b68f40")  # render title text
    screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 150)))  # center title
    m = pygame.mouse.get_pos()  # get mouse position
    play_btn.changeColor(m);  play_btn.update(screen)  # draw PLAY button
    quit_btn.changeColor(m);  quit_btn.update(screen)  # draw QUIT button

def draw_game():
    screen.fill((30, 30, 30))  # clear screen with dark gray
    m = pygame.mouse.get_pos()  # get mouse position

    # draw all tabs
    for name, btn in tab_buttons.items():
        btn.bg_color = "#888888" if name == active_tab else "#444444"  # highlight active tab
        btn.changeColor(m)
        btn.update(screen)

    # header info: Year & Cash
    hf = pixel_font(25)
    screen.blit(hf.render(f"Year: {years[year_idx]}", True, "#b68f40"), (700, 30))  # draw year text
    screen.blit(hf.render(f"Cash: ${cash:,.0f}", True, "#ffffff"), (250, 30))  # draw cash text

    if active_tab in COMPANIES:
        comp   = active_tab  # current company tab
        ticker = COMPANIES[comp]  # stock ticker

        # ── Compute prices ──────────────────────────────────────────
        cutoff       = datetime.datetime(years[year_idx], 12, 31)  # cutoff date for subset
        df_sub       = df_daily[df_daily.index <= cutoff]  # filter daily data
        current_price = df_sub[ticker].iloc[-1]  # latest price

        if year_idx > 0:
            prev_cutoff = datetime.datetime(years[year_idx-1], 12, 31)  # prev year cutoff
            prev_df     = df_sub[df_sub.index <= prev_cutoff]  # filter prev year
            prev_price  = prev_df[ticker].iloc[-1] if not prev_df.empty else current_price  # prev price
        else:
            prev_price = current_price  # same for first year

        change = current_price - prev_price  # absolute change
        pct    = (change / prev_price * 100) if prev_price else 0  # percent change

        # ── Draw price & YTD change ───────────────────────────────────
        big_font    = pixel_font(48)
        price_surf  = big_font.render(f"${current_price:,.2f}", True, "#ffffff")  # price text
        screen.blit(price_surf, (50, 120))  # draw price

        sign        = "+" if change >= 0 else ""  # plus sign if positive
        color       = "#00c853" if change >= 0 else "#d32f2f"  # green/red color
        change_text = f"{sign}${change:,.2f} ({sign}{pct:.2f}%) YTD"  # change display
        small_surf  = pixel_font(24).render(change_text, True, color)  # render change
        screen.blit(small_surf, (50, 120 + price_surf.get_height() + 5))  # draw change

        # ── Combined Total Return ─────────────────────────────────────
        cost_basis     = totalinvested[comp]  # invested cash
        total_sold     = sold[comp]  # cash from sales
        position_value = shares[comp] * current_price  # current holding value
        total_ret      =(total_sold+position_value) - cost_basis  # total return
        pct_ret        = (total_ret / cost_basis * 100) if cost_basis else 0  # percent return

        tr_font = pixel_font(16)
        tr_text = f"Total Return: "  # label text
        tr_surf = tr_font.render(tr_text, True, "#ffffff")  # render label

        tx, ty = 440, 700  # position below YTD line
        screen.blit(tr_surf, (tx, ty))  # draw label

        pr_sign  = "+" if pct_ret >= 0 else ""  # sign
        pr_text  = f"{pr_sign}${total_ret:,.2f} ({pr_sign}{pct_ret:.2f}% )"  # return text
        pr_color = "#00c853" if pct_ret >= 0 else "#d32f2f"  # color
        pr_surf  = tr_font.render(pr_text, True, pr_color)  # render text
        screen.blit(pr_surf, (tx + tr_surf.get_width() + 20, ty))  # draw text

        # ── Draw chart ───────────────────────────────────────────────────
        chart_y = 120 + price_surf.get_height() + small_surf.get_height() + 20  # y pos
        chart   = create_chart(df_daily[[ticker]], years, year_idx, chart_size, FONT_PATH)  # get surface
        screen.blit(chart, (50, chart_y))  # draw chart

        # ── CSV metrics ──────────────────────────────────────────────────
        df = csv_dfs[comp]  # select correct DataFrame
        year = years[year_idx]  # current year
        matching = [c for c in df.columns if c.year == year]  # find matching col
        if matching:
            col = matching[0]  # use first match
            net_income     = df.loc["Net Income/Net Profit\n(Losses)", col]  # net income
            revenue        = df.loc["Revenue", col]  # revenue
            TotalEquity    = df.loc["Total Equity", col]  # total equity
            ProfitMargin   = df.loc["Profit Margin", col]  # profit margin
            eps            = df.loc["Basic Earnings per Share", col]  # EPS
            lines = [
                f"Net Income:  ${net_income:,.2f}M",
                f"Revenue:     ${revenue:,.2f}M",
                f"Tot. Equity: ${TotalEquity:,.2f}M",
                f"PM:          {ProfitMargin:,.2f}%",
                f"EPS:         {eps:.2f}"
            ]
            for i, text in enumerate(lines):
                surf = pixel_font(20).render(text, True, "#ffffff")  # render each line
                screen.blit(surf, (780, 220 + i*30))  # position lines

        # ── Shares & Value display ──────────────────────────────────────
        pf = pixel_font(20)  # small font
        y  = 140  # y position
        shares_txt = pf.render(f"Shares: {shares[comp]:.2f}", True, "#ffffff")  # share count
        screen.blit(shares_txt, (300, y))  # draw share count

        current_price = df_sub[ticker].iloc[-1]  # reuse price
        total_value   = shares[comp] * current_price  # holding value
        value_txt     = pf.render(f"Total Value: ${total_value:,.2f}", True, "#ffffff")  # format value
        screen.blit(value_txt, (600, y))  # draw value

        # ── BUY/SELL buttons ─────────────────────────────────────────────
        invest_btns[comp].changeColor(m); invest_btns[comp].update(screen)  # buy button
        if shares[comp] == 0:
            sell_btns[comp].bg_color = "#555555"  # grey if no shares
        else:
            sell_btns[comp].bg_color = "Green"  # green if can sell
        sell_btns[comp].changeColor(m); sell_btns[comp].update(screen)  # sell button

        # ── Navigation ────────────────────────────────────────────────────
        next_year_btn.changeColor(m); next_year_btn.update(screen)  # next year button
        back_btn.changeColor(m);    back_btn.update(screen)  # back button

        # ── Input box rendering ───────────────────────────────────────────
        if active_action and active_action[1] == comp:
            pygame.draw.rect(screen, (255,255,255), input_box, 2)  # draw input box border
            txt_surf = pf.render(input_str, True, "#ffffff")  # render typed input
            screen.blit(txt_surf, (input_box.x + 5, input_box.y + 5))  # draw input

    else:
        # ── Portfolio view ─────────────────────────────────────────────────
        cutoff = datetime.datetime(years[year_idx], 12, 31)  # cutoff date
        df_sub = df_daily[df_daily.index <= cutoff]  # filter data

        port_values = pd.Series(0.0, index=df_sub.index)  # init series
        for comp_name, num_shares in shares.items():
            ticker = COMPANIES[comp_name]  # ticker symbol
            if ticker in df_sub.columns:
                port_values += df_sub[ticker] * num_shares  # accumulate

        current = port_values.iloc[-1]  # latest value
        if year_idx > 0:
            prev_cutoff = datetime.datetime(years[year_idx-1], 12, 31)  # prev cutoff
            prev_series = port_values[port_values.index <= prev_cutoff]  # prev series
            prev = prev_series.iloc[-1] if len(prev_series) else port_values.iloc[0]  # prev value
        else:
            prev = current  # same if first year

        change = current - prev  # dollar change
        pct    = (change / prev * 100) if prev else 0  # percent change

        big_font = pixel_font(72)  # large font
        val_surf = big_font.render(f"${current:,.2f}", True, "#ffffff")  # render total
        screen.blit(val_surf, (50, 120))  # draw total

        chg_font = pixel_font(24)  # small font for change
        sign     = "+" if change >= 0 else ""  # plus if positive
        color    = "#00c853" if change >= 0 else "#d32f2f"  # green/red
        chg_text = f"{sign}${change:,.2f} ({sign}{pct:.2f}%) YTD"  # change text
        chg_surf = chg_font.render(chg_text, True, color)  # render change
        screen.blit(chg_surf, (50, 120 + val_surf.get_height() + 5))  # draw change

        # ── Two charts side by side ──────────────────────────────────────
        chart_w, chart_h = (SCREEN_WIDTH - 400) // 2, 400  # dims
        chart_y = 120 + val_surf.get_height() + chg_surf.get_height() + 20  # y pos

        port_surf  = create_portfolio_chart(df_daily, shares, years, year_idx, (chart_w, chart_h), FONT_PATH)  # portfolio chart
        price_surf = create_pchart(df_daily, years, year_idx, (chart_w, chart_h), FONT_PATH)  # price chart
        screen.blit(port_surf,  (50, chart_y))  # draw portfolio chart
        screen.blit(price_surf, (50 + chart_w + 50, chart_y))  # draw price chart

        # ── Company list ─────────────────────────────────────────────────
        list_x = 50 + chart_w * 2 + 100  # x pos for list
        pf = pixel_font(24)  # font
        for i, comp_name in enumerate(COMPANIES):
            ticker     = COMPANIES[comp_name]  # ticker
            num_shares = shares[comp_name]  # shares held
            last_price = df_sub[ticker].iloc[-1] if ticker in df_sub.columns else 0  # latest price
            y_off      = chart_y + i * 60  # y offset

            screen.blit(pf.render(comp_name, True, "#ffffff"),      (list_x, y_off))  # draw name
            screen.blit(pf.render(f"{num_shares:.2f} shares", True, "#aaaaaa"),  (list_x + 150, y_off))  # draw shares
            screen.blit(pf.render(f"${last_price:,.2f}", True, "#ffffff"),       (list_x, y_off + 24))  # draw price

        next_year_btn.changeColor(m); next_year_btn.update(screen)  # draw next year
        back_btn.changeColor(m);    back_btn.update(screen)  # draw back

    # ── Pop‑up overlay ─────────────────────────────────────────────────
    if popup_msg:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)  # transparent overlay
        overlay.fill((0, 0, 0, 180))  # darken
        screen.blit(overlay, (0, 0))  # draw overlay

        popup_font = pygame.font.Font(FONT_PATH, 24)  # font for pop-up
        text_surf  = popup_font.render(popup_msg, True, "#ffffff")  # render message
        box_rect   = popup_rect.inflate(20, 20)  # enlarge rect
        pygame.draw.rect(screen, "#2f2f2f", box_rect, border_radius=8)  # draw background box
        screen.blit(text_surf, popup_rect)  # draw text

# ------------------ MAIN LOOP ------------------
while True:
    m = pygame.mouse.get_pos()  # get current mouse position

    for e in pygame.event.get():  # poll events
        if e.type == pygame.QUIT:
            pygame.quit(); sys.exit()  # quit on window close

        if popup_msg:  # if pop‑up active
            if e.type == pygame.MOUSEBUTTONDOWN:
                popup_msg = None  # dismiss on click
            continue  # skip further input

        if state == "MENU":
            if e.type == pygame.MOUSEBUTTONDOWN:
                if play_btn.checkForInput(m):
                    state = "GAME"  # switch to game
                elif quit_btn.checkForInput(m):
                    pygame.quit(); sys.exit()  # quit

        else:
            # ── typing input handling ─────────────────────────────────
            if active_action and e.type == pygame.KEYDOWN:
                if e.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]  # remove last char
                elif e.key == pygame.K_RETURN:
                    mode, comp = active_action  # unpack action
                    price = price_vals[comp][year_idx]  # current price
                    try:
                        desired_shares = int(input_str)  # parse input
                    except:
                        desired_shares = 0  # default on error
                    cost = desired_shares * price  # total cost

                    if mode == "invest":
                        if desired_shares <= 0:
                            popup_msg = "Enter at least 1 share to buy."  # error message
                        elif cost > cash:
                            popup_msg = f"Not enough cash: need ${cost:,.2f}."  # error message
                        else:
                            shares[comp] += desired_shares  # update shares
                            totalinvested[comp] += cost  # track invested
                            invested[comp] += cost  # alias update
                            cash      -= cost  # deduct cash
                            popup_msg = f"Bought {desired_shares} share(s) of {comp} for ${cost:,.2f}!"  # success message
                    else:  # sell mode
                        sell_shares = min(desired_shares, int(shares[comp]))  # cap at shares owned
                        if sell_shares <= 0:
                            popup_msg = "No shares to sell."  # error message
                        else:
                            proceeds      = sell_shares * price  # calculate proceeds
                            shares[comp] -= sell_shares  # update shares
                            invested[comp] -= proceeds  # adjust basis
                            sold[comp]   += proceeds  # track sold cash
                            cash         += proceeds  # add cash
                            popup_msg   = f"Sold {sell_shares} share(s) of {comp} for ${proceeds:,.2f}!"  # success message

                    active_action = None  # exit input mode
                    input_str     = ""  # clear buffer
                    surf = pygame.font.Font(FONT_PATH, 24).render(popup_msg, True, "#ffffff")  # render pop‑up text
                    popup_rect = surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))  # center pop‑up

                elif e.unicode.isdigit() or e.unicode == ".":
                    input_str += e.unicode  # append typed char

            # ── mouse click handling ─────────────────────────────────
            if e.type == pygame.MOUSEBUTTONDOWN and not active_action:
                if back_btn.checkForInput(m):
                    state = "MENU"  # back to menu
                    year_idx = 0  # reset year
                    cash = START_CASH  # reset cash
                    shares = {n: 0.0 for n in COMPANIES}  # reset shares

                for name, btn in tab_buttons.items():
                    if btn.checkForInput(m):
                        active_tab = name  # switch tab

                if active_tab in COMPANIES:
                    comp = active_tab
                    if invest_btns[comp].checkForInput(m):
                        active_action = ("invest", comp); input_str = ""  # buy mode
                    elif sell_btns[comp].checkForInput(m) and shares[comp] > 0:
                        active_action = ("sell", comp); input_str = ""  # sell mode

                if next_year_btn.checkForInput(m) and year_idx < len(years) - 1:
                    year_idx += 1  # advance year

    # draw screens
    if state == "MENU":
        draw_menu()  # render menu screen
    else:
        draw_game()  # render game screen

    pygame.display.flip()  # update the display
    clock.tick(FPS)  # enforce frame rate
