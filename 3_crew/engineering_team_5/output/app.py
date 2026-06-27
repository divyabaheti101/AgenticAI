import gradio as gr
import pandas as pd
from accounts import Account, InsufficientFundsError, InsufficientSharesError, InvalidQuantityError, InvalidAmountError, _default_get_share_price

# --- Backend Initialization (Single Account for Demo) ---
# For a simple demo, we'll instantiate one account globally.
# In a real application, this would be managed by a session or user login.
user_account = Account("demo_user_1", initial_deposit=10000.0)

# --- Helper function to refresh all UI outputs ---
def refresh_account_data(status_message_text: str = ""):
    """Fetches and formats all relevant account data for UI display."""
    balance = user_account.get_balance()
    portfolio_value = user_account.get_portfolio_value()
    profit_loss = user_account.get_profit_loss()

    holdings_dict = user_account.get_holdings()
    holdings_data = [[symbol, quantity, round(quantity * _default_get_share_price(symbol), 2)]
                     for symbol, quantity in holdings_dict.items()]
    holdings_df = pd.DataFrame(holdings_data, columns=["Symbol", "Quantity", "Current Value"])
    if holdings_df.empty:
        holdings_df = pd.DataFrame(columns=["Symbol", "Quantity", "Current Value"]) # Ensure headers are visible for empty state

    transactions = user_account.get_transactions()
    transactions_df = pd.DataFrame(transactions)
    if transactions_df.empty:
        # Define columns explicitly for empty dataframe to match headers used in gr.DataFrame
        transactions_df = pd.DataFrame(columns=["timestamp", "type", "amount", "symbol", "quantity", "price_per_share", "total_cost_or_proceeds"])

    return (
        status_message_text,
        f"Account ID: {user_account.get_account_id()}",
        round(balance, 2),
        round(portfolio_value, 2),
        round(profit_loss, 2),
        holdings_df,
        transactions_df
    )

# --- Gradio Wrapper Functions for Account Operations ---
# These functions call the backend and then trigger a full UI refresh.
def deposit_funds(amount: float):
    try:
        user_account.deposit(amount)
        return refresh_account_data("Deposit successful!")
    except (InvalidAmountError, Exception) as e:
        return refresh_account_data(f"Error: {e}")

def withdraw_funds(amount: float):
    try:
        user_account.withdraw(amount)
        return refresh_account_data("Withdrawal successful!")
    except (InvalidAmountError, InsufficientFundsError, Exception) as e:
        return refresh_account_data(f"Error: {e}")

def buy_shares(symbol: str, quantity: int):
    try:
        user_account.buy_shares(symbol, quantity)
        return refresh_account_data(f"Successfully bought {quantity} shares of {symbol}!")
    except (InvalidQuantityError, InsufficientFundsError, ValueError, Exception) as e:
        return refresh_account_data(f"Error: {e}")

def sell_shares(symbol: str, quantity: int):
    try:
        user_account.sell_shares(symbol, quantity)
        return refresh_account_data(f"Successfully sold {quantity} shares of {symbol}!")
    except (InvalidQuantityError, InsufficientSharesError, ValueError, Exception) as e:
        return refresh_account_data(f"Error: {e}")

# --- Gradio UI Definition ---
with gr.Blocks(title="Trading Account Simulator") as demo:
    gr.Markdown("# Simple Trading Account Simulator")
    gr.Markdown("Demonstrates the `Account` backend class functionalities for a single user.")

    # Shared output components for account status
    status_message = gr.Textbox(label="Status/Message", interactive=False, container=False, value="Welcome! Account loaded.")
    account_id_output = gr.Textbox(label="Account ID", interactive=False)
    
    with gr.Row():
        balance_output = gr.Number(label="Cash Balance", interactive=False, precision=2)
        portfolio_value_output = gr.Number(label="Total Portfolio Value", interactive=False, precision=2)
        profit_loss_output = gr.Number(label="Profit/Loss (vs Net Injected)", interactive=False, precision=2)

    # List of all output components to refresh after any action
    all_outputs = [
        status_message, 
        account_id_output, 
        balance_output, 
        portfolio_value_output, 
        profit_loss_output, 
        # These are placeholders for the dataframes that will be updated in the 'Reports' tab
        # We need to explicitly reference the actual dataframe components for updates to work.
        # They will be defined below in the Reports tab.
        # For now, let's keep them in the list and ensure they are defined globally
        # or accessible correctly. The current design requires them to be global outputs.
        # Let's define the DataFrames upfront.
    ]

    # Define DataFrames outside the tabs so they are global outputs
    holdings_output = gr.DataFrame(label="Share Holdings", headers=["Symbol", "Quantity", "Current Value"], row_count=(1, "dynamic"), col_count=(3, "fixed"))
    transactions_output = gr.DataFrame(label="All Transactions", headers=["timestamp", "type", "amount", "symbol", "quantity", "price_per_share", "total_cost_or_proceeds"], row_count=(5, "dynamic"), col_count=(7, "fixed"))

    all_outputs_with_dataframes = all_outputs + [holdings_output, transactions_output]

    with gr.Tab("Funds Management"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Deposit Funds")
                deposit_amount_input = gr.Number(label="Amount to Deposit", value=100.0, minimum=0.01)
                deposit_btn = gr.Button("Deposit")
            with gr.Column():
                gr.Markdown("### Withdraw Funds")
                withdraw_amount_input = gr.Number(label="Amount to Withdraw", value=50.0, minimum=0.01)
                withdraw_btn = gr.Button("Withdraw")
        
        deposit_btn.click(
            deposit_funds,
            inputs=[deposit_amount_input],
            outputs=all_outputs_with_dataframes
        )
        withdraw_btn.click(
            withdraw_funds,
            inputs=[withdraw_amount_input],
            outputs=all_outputs_with_dataframes
        )

    with gr.Tab("Share Trading"):
        gr.Markdown("## Buy/Sell Shares")
        supported_symbols = ["AAPL", "TSLA", "GOOGL"]
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Buy Shares")
                buy_symbol_input = gr.Dropdown(label="Stock Symbol", choices=supported_symbols, value="AAPL")
                buy_quantity_input = gr.Number(label="Quantity", value=1, minimum=1, step=1)
                buy_btn = gr.Button("Buy Shares")
            with gr.Column():
                gr.Markdown("### Sell Shares")
                sell_symbol_input = gr.Dropdown(label="Stock Symbol", choices=supported_symbols, value="AAPL")
                sell_quantity_input = gr.Number(label="Quantity", value=1, minimum=1, step=1)
                sell_btn = gr.Button("Sell Shares")
        
        buy_btn.click(
            buy_shares,
            inputs=[buy_symbol_input, buy_quantity_input],
            outputs=all_outputs_with_dataframes
        )
        sell_btn.click(
            sell_shares,
            inputs=[sell_symbol_input, sell_quantity_input],
            outputs=all_outputs_with_dataframes
        )

    with gr.Tab("Reports"):
        gr.Markdown("## Account Reports")
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Current Holdings")
                # holdings_output is already defined globally
            with gr.Column():
                gr.Markdown("### Transaction History")
                # transactions_output is already defined globally
        
        refresh_btn = gr.Button("Refresh All Data")
        refresh_btn.click(
            lambda: refresh_account_data("Data refreshed."), # Pass a default status message
            outputs=all_outputs_with_dataframes
        )

    # Initial data load when UI starts
    demo.load(
        lambda: refresh_account_data("Welcome! Account loaded."), # Initial message
        outputs=all_outputs_with_dataframes
    )

demo.launch()