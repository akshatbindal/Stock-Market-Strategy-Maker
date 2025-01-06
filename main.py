import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go

# Step 1: Fetch Stock Data
def fetch_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    return data

# Step 2: Calculate All Indicators Using ta Library
def calculate_all_indicators(data):
    data = ta.add_all_ta_features(
        data,
        open="Open",
        high="High",
        low="Low",
        close="Close",
        volume="Volume",
        fillna=True
    )
    return data

# Step 3: Build Conditions
def generate_signals(data, buy_conditions, sell_conditions):
    buy_condition1 = eval_condition(data, *buy_conditions[0]).fillna(False)
    buy_condition2 = eval_condition(data, *buy_conditions[1]).fillna(False)
    buy_condition3 = eval_condition(data, *buy_conditions[2]).fillna(False)

    sell_condition1 = eval_condition(data, *sell_conditions[0]).fillna(False)
    sell_condition2 = eval_condition(data, *sell_conditions[1]).fillna(False)
    sell_condition3 = eval_condition(data, *sell_conditions[2]).fillna(False)

    buy_condition1.index = data.index
    buy_condition2.index = data.index
    buy_condition3.index = data.index

    sell_condition1.index = data.index
    sell_condition2.index = data.index
    sell_condition3.index = data.index

    data['Buy_Signal'] = buy_condition1 & buy_condition2 & buy_condition3
    data['Sell_Signal'] = sell_condition1 & sell_condition2 & sell_condition3
    return data

def eval_condition(data, left, operator, right):
    try:
        if operator == '>':
            return left > right
        elif operator == '<':
            return left < right
        elif operator == '=':
            return left == right
    except (KeyError, ValueError) as e:
        st.error(f"Error in condition evaluation: {left} {operator} {right} - {e}")
    return pd.Series([False] * len(data))

# Step 4: Plot Results with Selected Indicators
def plot_signals(data, ticker, selected_indicators):
    fig = go.Figure()

    # Add Candlestick
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Candlestick'
    ))

    # Add Buy Signals
    buy_signals = data[data['Buy_Signal']]
    fig.add_trace(go.Scatter(
        x=buy_signals.index,
        y=buy_signals['Close'],
        mode='markers',
        name='Buy Signal',
        marker=dict(color='green', size=10, symbol='triangle-up')
    ))

    # Add Sell Signals
    sell_signals = data[data['Sell_Signal']]
    fig.add_trace(go.Scatter(
        x=sell_signals.index,
        y=sell_signals['Close'],
        mode='markers',
        name='Sell Signal',
        marker=dict(color='red', size=10, symbol='triangle-down')
    ))

    # Add Selected Indicators
    for indicator in selected_indicators:
        if indicator in data.columns:
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data[indicator],
                mode='lines',
                name=indicator
            ))

    # Layout
    fig.update_layout(
        title=f"Trading Signals and Indicators for {ticker}",
        xaxis_title="Date",
        yaxis_title="Price",
        template="plotly_dark"
    )
    st.plotly_chart(fig)

# Streamlit App
def main():
    st.title("Stock Market Strategy Builder")
    
    # Initialize session state
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'buy_conditions' not in st.session_state:
        st.session_state.buy_conditions = []
    if 'sell_conditions' not in st.session_state:
        st.session_state.sell_conditions = []

    # Step 1: Input Ticker and Date Range
    st.header("Step 1: Enter Stock Details")
    ticker = st.text_input("Enter the stock ticker (e.g., TCS.NS):", value="TCS.NS")
    start_date = st.date_input("Start Date", value=pd.to_datetime("2020-01-01"))
    end_date = st.date_input("End Date", value=pd.to_datetime("2025-01-01"))
    
    if st.button("Fetch Data"):
        st.session_state.data = fetch_data(ticker, start_date, end_date)
        st.session_state.data = calculate_all_indicators(st.session_state.data)
        st.success("Data fetched and indicators calculated successfully!")
        st.dataframe(st.session_state.data.tail())

    # Step 2: Select Indicators to Plot
    if st.session_state.data is not None:
        st.header("Step 2: Select Indicators to Plot")
        all_indicators = list(st.session_state.data.columns)
        selected_indicators = st.multiselect("Choose Indicators to Plot:", all_indicators, default=['Close'])
        st.dataframe(st.session_state.data[selected_indicators].tail())

    # Step 3: Build Buy and Sell Conditions
    if st.session_state.data is not None:
        st.header("Step 3: Create Buy and Sell Conditions")
        options = ["User Input"] + list(st.session_state.data.columns)
        
        # Buy Conditions
        st.subheader("Buy Conditions")
        buy_conditions = []
        for i in range(1, 4):
            cols = st.columns([3, 1, 3])
            with cols[0]:
                left = st.selectbox(f"Left Operand {i}", options, key=f"buy_left_{i}")
                left_value = None
                if left == "User Input":
                    left_value = st.number_input(f"Enter Value {i}", min_value=0, max_value=1000, step=1, key=f"buy_left_value_{i}")
            with cols[1]:
                operator = st.selectbox(f"Operator {i}", ['>', '<', '='], key=f"buy_operator_{i}")
            with cols[2]:
                right = st.selectbox(f"Right Operand {i}", options, key=f"buy_right_{i}")
                right_value = None
                if right == "User Input":
                    right_value = st.number_input(f"Enter Value {i}", min_value=0, max_value=1000, step=1, key=f"buy_right_value_{i}")
            
            left_operand = pd.Series([left_value] * len(st.session_state.data), index=st.session_state.data.index) if left == "User Input" else st.session_state.data[left]
            right_operand = pd.Series([right_value] * len(st.session_state.data), index=st.session_state.data.index) if right == "User Input" else st.session_state.data[right]
            buy_conditions.append((left_operand, operator, right_operand))
        
        # Sell Conditions
        st.subheader("Sell Conditions")
        sell_conditions = []
        for i in range(1, 4):
            cols = st.columns([3, 1, 3])
            with cols[0]:
                left = st.selectbox(f"Left Operand {i}", options, key=f"sell_left_{i}")
                left_value = None
                if left == "User Input":
                    left_value = st.number_input(f"Enter Value {i}", min_value=0, max_value=1000, step=1, key=f"sell_left_value_{i}")
            with cols[1]:
                operator = st.selectbox(f"Operator {i}", ['>', '<', '='], key=f"sell_operator_{i}")
            with cols[2]:
                right = st.selectbox(f"Right Operand {i}", options, key=f"sell_right_{i}")
                right_value = None
                if right == "User Input":
                    right_value = st.number_input(f"Enter Value {i}", min_value=0, max_value=1000, step=1, key=f"sell_right_value_{i}")
            
            left_operand = pd.Series([left_value] * len(st.session_state.data), index=st.session_state.data.index) if left == "User Input" else st.session_state.data[left]
            right_operand = pd.Series([right_value] * len(st.session_state.data), index=st.session_state.data.index) if right == "User Input" else st.session_state.data[right]
            sell_conditions.append((left_operand, operator, right_operand))

        if st.button("Generate Signals"):
            st.session_state.buy_conditions = buy_conditions
            st.session_state.sell_conditions = sell_conditions
            st.session_state.data = generate_signals(st.session_state.data, st.session_state.buy_conditions, st.session_state.sell_conditions)
            st.success("Signals generated successfully!")
            st.dataframe(st.session_state.data[['Close', 'Buy_Signal', 'Sell_Signal']].tail())

            # Step 4: Plot Results
            st.header("Step 4: Visualize Results")
            plot_signals(st.session_state.data, ticker, selected_indicators)

if __name__ == "__main__":
    main()
