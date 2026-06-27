import datetime
from typing import Dict, List, Callable, Union

# --- Custom Exceptions ---
class InsufficientFundsError(Exception):
    """Raised when there are insufficient funds for an operation."""
    pass

class InsufficientSharesError(Exception):
    """Raised when there are insufficient shares to sell."""
    pass

class InvalidQuantityError(Exception):
    """Raised when an invalid quantity (e.g., non-positive) is provided."""
    pass

class InvalidAmountError(Exception):
    """Raised when an invalid amount (e.g., non-positive) is provided."""
    pass

# --- External Dependency / Test Helper ---
def _default_get_share_price(symbol: str) -> float:
    """
    Default implementation for fetching the current market price for a given share symbol.
    This function serves as a test helper and can be overridden.
    It returns fixed prices for specific symbols and 0.0 for others.
    
    Parameters:
        symbol (str): The stock symbol (e.g., "AAPL").

    Returns:
        float: The fixed share price for known symbols, or 0.0 if the symbol is not found.
    """
    prices = {
        "AAPL": 170.50,
        "TSLA": 250.75,
        "GOOGL": 140.20,
    }
    return prices.get(symbol, 0.0)

# --- Main Account Class ---
class Account:
    """
    A simple account management system for a trading simulation platform.

    Allows users to:
    - Create an account with an optional initial deposit.
    - Deposit and withdraw funds.
    - Buy and sell shares, with validation for sufficient funds/holdings.
    - Report current cash balance, share holdings, and total portfolio value.
    - Calculate profit or loss from net capital injected.
    - List all historical transactions.
    """

    def __init__(self, account_id: str, initial_deposit: float = 0.0,
                 get_share_price_func: Callable[[str], float] = None):
        """
        Initializes a new trading account.

        Args:
            account_id (str): A unique identifier for the account.
            initial_deposit (float, optional): An initial amount of funds to deposit. 
                                               Must be non-negative. Defaults to 0.0.
            get_share_price_func (Callable[[str], float], optional): A function to override 
                                                                    the default share price lookup.
        
        Raises:
            InvalidAmountError: If initial_deposit is negative.
        """
        if initial_deposit < 0:
            raise InvalidAmountError("Initial deposit cannot be negative.")

        self._account_id = account_id
        self._balance = 0.0
        self._holdings: Dict[str, int] = {}
        self._transactions: List[Dict] = []
        self._get_share_price_func = get_share_price_func if get_share_price_func else _default_get_share_price

        if initial_deposit > 0:
            self.deposit(initial_deposit)

    def deposit(self, amount: float):
        """
        Adds funds to the account balance.

        Args:
            amount (float): The amount of money to deposit. Must be positive.

        Raises:
            InvalidAmountError: If amount is not positive.
        """
        if amount <= 0:
            raise InvalidAmountError("Deposit amount must be positive.")
        self._balance += amount
        self._transactions.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "DEPOSIT",
            "amount": amount,
        })

    def withdraw(self, amount: float):
        """
        Removes funds from the account balance.

        Args:
            amount (float): The amount of money to withdraw. Must be positive.

        Raises:
            InvalidAmountError: If amount is not positive.
            InsufficientFundsError: If the withdrawal would result in a negative balance.
        """
        if amount <= 0:
            raise InvalidAmountError("Withdrawal amount must be positive.")
        if self._balance - amount < 0:
            raise InsufficientFundsError(
                f"Insufficient funds. Attempted to withdraw {amount:.2f}, "
                f"but current balance is {self._balance:.2f}."
            )
        self._balance -= amount
        self._transactions.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "WITHDRAWAL",
            "amount": amount,
        })

    def buy_shares(self, symbol: str, quantity: int):
        """
        Purchases shares of a specified stock.

        Args:
            symbol (str): The stock symbol (e.g., "AAPL").
            quantity (int): The number of shares to buy. Must be positive.

        Raises:
            InvalidQuantityError: If quantity is not positive.
            ValueError: If a valid price cannot be obtained for the symbol 
                        (i.e., _get_share_price_func returns 0.0 or negative).
            InsufficientFundsError: If the account balance is not sufficient for the purchase.
        """
        if quantity <= 0:
            raise InvalidQuantityError("Quantity to buy must be positive.")
        
        price_per_share = self._get_share_price_func(symbol)
        if price_per_share <= 0:
             raise ValueError(f"Could not get a valid price for symbol '{symbol}'. Price returned: {price_per_share:.2f}")

        total_cost = price_per_share * quantity
        if self._balance < total_cost:
            raise InsufficientFundsError(
                f"Insufficient funds. Need {total_cost:.2f} to buy {quantity} of {symbol} "
                f"at {price_per_share:.2f} each. Current balance is {self._balance:.2f}."
            )
        
        self._balance -= total_cost
        self._holdings[symbol] = self._holdings.get(symbol, 0) + quantity
        self._transactions.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "price_per_share": price_per_share,
            "total_cost_or_proceeds": total_cost,
        })

    def sell_shares(self, symbol: str, quantity: int):
        """
        Sells shares of a specified stock.

        Args:
            symbol (str): The stock symbol (e.g., "AAPL").
            quantity (int): The number of shares to sell. Must be positive.

        Raises:
            InvalidQuantityError: If quantity is not positive.
            InsufficientSharesError: If the user does not own enough shares of the specified symbol.
            ValueError: If a valid price cannot be obtained for the symbol 
                        (i.e., _get_share_price_func returns 0.0 or negative).
        """
        if quantity <= 0:
            raise InvalidQuantityError("Quantity to sell must be positive.")
        if self._holdings.get(symbol, 0) < quantity:
            raise InsufficientSharesError(
                f"Insufficient shares. Attempted to sell {quantity} of {symbol}, "
                f"but only hold {self._holdings.get(symbol, 0)}."
            )
        
        price_per_share = self._get_share_price_func(symbol)
        if price_per_share <= 0:
             raise ValueError(f"Could not get a valid price for symbol '{symbol}'. Price returned: {price_per_share:.2f}")

        total_proceeds = price_per_share * quantity
        self._balance += total_proceeds
        self._holdings[symbol] -= quantity
        if self._holdings[symbol] == 0:
            del self._holdings[symbol]
        
        self._transactions.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "SELL",
            "symbol": symbol,
            "quantity": quantity,
            "price_per_share": price_per_share,
            "total_cost_or_proceeds": total_proceeds,
        })

    def get_account_id(self) -> str:
        """
        Returns the unique ID of the account.

        Returns:
            str: The account ID.
        """
        return self._account_id

    def get_balance(self) -> float:
        """
        Returns the current cash balance in the account.

        Returns:
            float: The current cash balance.
        """
        return self._balance

    def get_holdings(self) -> Dict[str, int]:
        """
        Returns a copy of the current stock holdings.

        Returns:
            Dict[str, int]: A dictionary where keys are stock symbols and values are quantities held.
        """
        return self._holdings.copy()

    def get_portfolio_value(self) -> float:
        """
        Calculates the total value of the portfolio, including cash balance 
        and the current market value of all held shares.

        Returns:
            float: The total portfolio value.
        """
        total_market_value = 0.0
        for symbol, quantity in self._holdings.items():
            price = self._get_share_price_func(symbol)
            if price > 0:  # Only add to value if a valid (positive) price is found
                total_market_value += price * quantity
        return self._balance + total_market_value

    def get_profit_loss(self) -> float:
        """
        Calculates the overall profit or loss of the account.
        This is determined by the (current total portfolio value) 
        minus the (net capital injected: total deposits - total withdrawals).

        Returns:
            float: The calculated profit or loss.
        """
        total_deposits = sum(t["amount"] for t in self._transactions if t["type"] == "DEPOSIT")
        total_withdrawals = sum(t["amount"] for t in self._transactions if t["type"] == "WITHDRAWAL")
        
        net_capital_injected = total_deposits - total_withdrawals
        current_total_value = self.get_portfolio_value()
        
        return current_total_value - net_capital_injected

    def get_transactions(self) -> List[Dict]:
        """
        Returns a chronological list of all transactions made in the account.

        Returns:
            List[Dict]: A list of transaction dictionaries.
        """
        return self._transactions[:] # Return a shallow copy