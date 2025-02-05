import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

# Download NVDA's historical data for the past year
ticker = "NVDA" 
data = yf.download(ticker, period="1y", interval="1d")

# Compute the 20-day simple moving average (MA20)
data['MA20'] = data['Close'].rolling(window=20).mean()

# Compute the standard deviation with a 20-day window
data['stddev'] = data['Close'].rolling(window=20).std()

# Compute Bollinger Bands: the middle band is MA20, and the upper/lower bands are MA20 ± 2× standard deviation
data['UpperBand'] = data['MA20'] + (data['stddev'] * 2)
data['LowerBand'] = data['MA20'] - (data['stddev'] * 2)

# Initialize cash, position, and record of buy timestamps
initial_cash = 2000
cash = initial_cash
position = 0  # Accumulated number of shares held
# Use last_buy_index to record the last buy transaction index, used as a reference when selling
last_buy_index = None

# Record daily portfolio value and trading signals
portfolio_values = []
buy_info = []   # Format: (date, shares bought, buy price)
sell_info = []  # Format: (date, shares sold, sell price)

# Backtesting loop: Iterate from the second trading day onward (i from 1 to len(data)-1)
for i in range(1, len(data)):
    # Get the closing price of the day
    price = data['Close'].iloc[i].item()
    
    # Retrieve MA20, LowerBand, and UpperBand (convert to float if not NaN)
    ma20 = data['MA20'].iloc[i]
    if pd.notna(ma20):
        ma20 = float(ma20)
    
    lower_band = data['LowerBand'].iloc[i]
    if pd.notna(lower_band):
        lower_band = float(lower_band)
    
    upper_band = data['UpperBand'].iloc[i]
    if pd.notna(upper_band):
        upper_band = float(upper_band)


    # ----------- Abnormal value detection -------------
    # if data.index[i].strftime("%Y-%m-%d") == "2023-12-05":
    #     print("2023-12-05 debug:")
    #     print("Price:", price)
    #     print("MA20:", ma20)
    #     print("LowerBand:", lower_band)
    #     print("Price - LowerBand:", price - lower_band)
    #     print("0.2*(MA20 - LowerBand):", 0.2 * (ma20 - lower_band))
    #     print("Last buy index:", last_buy_index)

    
    # -------------------- Buy Logic --------------------
    # Buy when the closing price breaks below the lower Bollinger Band, ensuring at least a 2-day gap between buys
    if pd.notna(lower_band) and pd.notna(ma20) and ((price - lower_band) <= 0.15 * (ma20 - lower_band)):

        if last_buy_index is None or (i - last_buy_index >= 2):
            # Allocate 2/5 of available cash for each purchase
            allocation = cash * (2/5)
            shares_to_buy = int(allocation // price)
            if shares_to_buy > 0:
                cash -= shares_to_buy * price
                position += shares_to_buy
                buy_info.append((data.index[i], shares_to_buy, price))
                # Update the last buy date
                last_buy_index = i

    # -------------------- Sell Logic --------------------
    if position > 0 and last_buy_index is not None:
        # Calculate holding period in trading days
        holding_days = i - last_buy_index
        
        # Sell conditions:
        # ① If holding for more than 20 trading days and price breaks above MA20, sell.
        # ② If holding ≤ 20 days, ignore MA20 and sell only if the price breaks above the upper Bollinger Band.
        if holding_days > 20:
            if pd.notna(ma20) and price > ma20:
                sell_info.append((data.index[i], position, price))
                cash += position * price
                position = 0
                last_buy_index = None
        else:
            if pd.notna(upper_band) and price > upper_band:
                sell_info.append((data.index[i], position, price))
                cash += position * price
                position = 0
                last_buy_index = None

    # Record daily portfolio value (cash + stock holdings value)
    portfolio_value = cash + position * price
    portfolio_values.append(portfolio_value)

# Align data as backtesting started from index 1
data = data.iloc[1:].copy()
data['PortfolioValue'] = portfolio_values

# -------------------- Plot Results --------------------
plt.figure(figsize=(14, 7))

# Subplot 1: Stock price, MA20, and Bollinger Bands
plt.subplot(2, 1, 1)
plt.plot(data.index, data['Close'], label='Close Price', color='blue')
plt.plot(data.index, data['MA20'], label='MA 20', color='orange')
plt.plot(data.index, data['UpperBand'], label='Upper Band', color='green')
plt.plot(data.index, data['LowerBand'], label='Lower Band', color='red')
plt.fill_between(data.index, data['UpperBand'], data['LowerBand'], color='grey', alpha=0.1)

# Mark buy signals and annotate buy quantity
for date, shares, price in buy_info:
    plt.scatter(date, price, marker='^', color='green', s=100, label='Buy Signal')
    plt.annotate(
        f"{shares}",
        (date, price),
        textcoords="offset points",
        xytext=(0, 10),
        ha='center',
        color='black',
        fontsize=12,
        fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8)
    )

# Mark sell signals and annotate sell quantity
for date, shares, price in sell_info:
    plt.scatter(date, price, marker='v', color='red', s=100, label='Sell Signal')
    plt.annotate(
        f"{shares}",
        (date, price),
        textcoords="offset points",
        xytext=(0, -15),
        ha='center',
        color='black',
        fontsize=12,
        fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8)
    )

# Avoid duplicate legends
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys())
plt.title(f'{ticker} Stock Price and Trading Signals')

# Subplot 2: Portfolio value trend
plt.subplot(2, 1, 2)
plt.plot(data.index, data['PortfolioValue'], label='Portfolio Value', color='purple')
plt.title('Portfolio Value Over Time')
plt.legend()

plt.tight_layout()
plt.show()

# Print final portfolio value and net profit
final_value = data['PortfolioValue'].iloc[-1] if not data.empty else cash
print(f"Initial Cash: ${initial_cash:.2f}")
print(f"Final Portfolio Value: ${final_value:.2f}")
print(f"Net Profit: ${final_value - initial_cash:.2f}")
print(f"Profit Rate: {(final_value - initial_cash) * 100 / initial_cash:.2f}%")
