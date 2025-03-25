import requests
import pandas as pd
import time

API_KEY = "9C02THUB964TPA9"
BASE_URL = "https://www.alphavantage.co/query"

def get_monthly_adjusted_data(symbol):
    """
    Fetches monthly adjusted data from Alpha Vantage for the given symbol,
    filters for dates from 2000 onward, and resamples it to a semiannual frequency.
    """
    params = {
        "function": "TIME_SERIES_MONTHLY_ADJUSTED",
        "symbol": symbol,
        "apikey": API_KEY,
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    
    # Extract time series data from the JSON response.
    time_series = data.get("Monthly Adjusted Time Series", {})
    if not time_series:
        raise ValueError(f"No data found for symbol {symbol}. Check your API key and symbol.")
    
    # Create DataFrame and process dates.
    df = pd.DataFrame.from_dict(time_series, orient='index')
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    
    # Filter for data from 2000 onward and convert the adjusted close to float.
    df = df.loc[df.index >= pd.to_datetime("2000-01-01")]
    df = df[['5. adjusted close']].rename(columns={'5. adjusted close': 'adj_close'})
    df['adj_close'] = df['adj_close'].astype(float)
    
    # Resample to a semiannual frequency (using the last available price in each 6-month period).
    semiannual = df.resample('6M').last()
    return semiannual

def main():
    # Define the symbols and corresponding company names.
    # Note: For Nintendo, we're using its US-traded ADR (NTDOY).
    symbols = {
        'NTDOY': "Nintendo Co.",
        'EA': "Electronic Arts",
        'TTWO': "Take-Two Interactive"
    }
    
    # Fetch semiannual data for each company.
    data = {}
    for symbol in symbols:
        print(f"Fetching data for {symbols[symbol]} ({symbol})...")
        try:
            data[symbol] = get_monthly_adjusted_data(symbol)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return
        # Sleep to avoid API rate limits.
        time.sleep(12)
    
    # Combine the data from each symbol using the union of their indices.
    # This creates a DataFrame where the index is the union of all dates in the individual data sets.
    combined = pd.concat([data[symbol]['adj_close'].rename(symbol) for symbol in symbols], axis=1)
    combined.sort_index(inplace=True)
    # Ensure we are only considering data from 2000 onward.
    combined = combined.loc[combined.index >= pd.to_datetime("2000-01-01")]
    # Forward fill missing data and drop any remaining gaps.
    combined.fillna(method='ffill', inplace=True)
    combined.dropna(inplace=True)
    
    if combined.empty:
        print("No combined data available for simulation. Please check the data sources.")
        return
    
    # Initialize simulation parameters.
    cash = 100000.0  # Starting cash balance.
    portfolio = {symbol: 0 for symbol in symbols}
    
    print("\n=== Historical Investment Simulator ===")
    print("You start with a cash balance of ${:.2f}.\n".format(cash))
    
    # Loop over each semiannual period.
    for current_date, prices in combined.iterrows():
        print("\n----------------------------------------")
        print("Date: {}".format(current_date.strftime("%Y-%m-%d")))
        print("Current Stock Prices:")
        for symbol in symbols:
            print("  {}: ${:.2f}".format(symbol, prices[symbol]))
        
        # Display current portfolio status.
        print("\nPortfolio Status:")
        print("  Cash: ${:.2f}".format(cash))
        for symbol in symbols:
            print("  {} shares: {}".format(symbol, portfolio[symbol]))
        
        # For each stock, prompt the user for a trade decision.
        for symbol in symbols:
            try:
                trade = input(f"Enter number of shares to buy (positive) or sell (negative) for {symbol} (or press Enter to skip): ")
                if trade == "":
                    continue  # No trade for this symbol.
                trade = int(trade)
            except ValueError:
                print(f"Invalid input. Skipping trade for {symbol}.")
                continue
            
            trade_cost = trade * prices[symbol]
            if trade > 0:  # Buying shares.
                if cash >= trade_cost:
                    portfolio[symbol] += trade
                    cash -= trade_cost
                    print(f"Bought {trade} shares of {symbol} for ${trade_cost:.2f}.")
                else:
                    print(f"Not enough cash to buy {trade} shares of {symbol}.")
            elif trade < 0:  # Selling shares.
                if portfolio[symbol] >= abs(trade):
                    portfolio[symbol] += trade  # trade is negative so this subtracts shares.
                    cash -= trade_cost  # trade_cost is negative; subtracting a negative adds cash.
                    print(f"Sold {abs(trade)} shares of {symbol} for ${-trade_cost:.2f}.")
                else:
                    print(f"Not enough shares to sell {abs(trade)} of {symbol}.")
    
    # Use the last available date from the combined DataFrame for the final valuation.
    last_date = combined.index[-1]
    last_prices = combined.iloc[-1]
    
    final_value = cash
    print("\n========================================")
    print("Final Portfolio as of {}:".format(last_date.strftime("%Y-%m-%d")))
    print("Cash: ${:.2f}".format(cash))
    for symbol in symbols:
        stock_value = portfolio[symbol] * last_prices[symbol]
        final_value += stock_value
        print("  {} shares at ${:.2f} each: ${:.2f}".format(symbol, last_prices[symbol], stock_value))
    print("Total Portfolio Value: ${:.2f}".format(final_value))
    
if __name__ == '__main__':
    main()