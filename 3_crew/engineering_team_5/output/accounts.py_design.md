```markdown
# Design Document: `accounts.py` - Account Management System

## Overview

This document details the design for a `accounts.py` Python module, which implements a simple account management system for a trading simulation platform. The system allows users to create an account, manage funds (deposit, withdraw), trade shares (buy, sell), and track their portfolio's value, profit/loss, and transaction history. Robust validation is included to prevent invalid operations such as over-withdrawing or selling unowned shares. The module is entirely self-contained within a single Python file.

## Module Structure

The `accounts.py` module will consist of custom exception classes, a default share price lookup function, and the main `Account` class.

### Custom Exceptions

To provide clear error handling, the following custom exceptions will be defined:

*   **`InsufficientFundsError(Exception)`**: Raised when an operation (e.g., withdrawal, share purchase) cannot be completed due to insufficient cash balance.
*   **`InsufficientSharesError(Exception)`**: Raised when a share selling operation attempts to sell more shares than are currently held for a given symbol.
*   **`InvalidQuantityError(Exception)`**: Raised when a share trading operation receives a non-positive quantity of shares.
*   **`InvalidAmountError(Exception)`**: Raised when a fund management operation receives a non-positive amount.

### External Dependency / Test Helper Function

```python
# accounts.py

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
```

## Class: `Account`

This class encapsulates all functionalities related to a single user's trading simulation account.

**Attributes:**

*   `_account_id` (str): A unique identifier for the account, set at initialization. This attribute is read-only after creation.
*   `_balance` (float): The current cash balance available in the account. Initialized to `0.0` or `initial_deposit`.
*   `_holdings` (Dict[str, int]): A dictionary representing the shares currently held by the account. Keys are stock symbols (e.g., "AAPL"), and values are the integer quantities of shares held.
*   `_transactions` (List[Dict]): A chronological list of all financial and trading activities performed on the account. Each entry in the list is a dictionary describing a single transaction. The structure of these transaction dictionaries is as follows:
    *   `"timestamp"` (str): An ISO formatted datetime string indicating when the transaction occurred.
    *   `"type"` (str): The type of transaction, e.g., "DEPOSIT", "WITHDRAWAL", "BUY", "SELL".
    *   `"amount"` (float, optional): The cash amount involved in DEPOSIT or WITHDRAWAL transactions.
    *   `"symbol"` (str, optional): The stock symbol for BUY or SELL transactions.
    *   `"quantity"` (int, optional): The number of shares involved in BUY or SELL transactions.
    *   `"price_per_share"` (float, optional): The price per share at which BUY or SELL transactions were executed.
    *   `"total_cost_or_proceeds"` (float, optional): The calculated total cost (for BUY) or total proceeds (for SELL) for the transaction.
*   `_get_share_price_func` (Callable[[str], float]): A callable function responsible for fetching the current market price of a given stock symbol. This allows for dependency injection, making the `Account` class testable with mocked prices or adaptable to different real-time data sources. It defaults to `_default_get_share_price`.

**Methods:**

1.  ### `__init__(self, account_id: str, initial_deposit: float = 0.0, get_share_price_func: Callable[[str], float] = None)`
    *   **Description**: Initializes a new trading account with a unique identifier and an optional initial cash deposit.
    *   **Parameters**:
        *   `account_id` (str): A unique string identifier for this account.
        *   `initial_deposit` (float, optional): An initial amount of funds to be deposited into the account upon creation. Defaults to `0.0`. Must be non-negative.
        *   `get_share_price_func` (Callable[[str], float], optional): A function to retrieve share prices. If `None`, `_default_get_share_price` is used.
    *   **Raises**:
        *   `InvalidAmountError`: If `initial_deposit` is a negative value.
    *   **Behavior**:
        *   Sets the `_account_id`.
        *   Initializes `_balance` to `0.0`.
        *   Initializes `_holdings` as an empty dictionary.
        *   Initializes `_transactions` as an empty list.
        *   Sets `_get_share_price_func`.
        *   If `initial_deposit` is greater than `0.0`, calls `self.deposit(initial_deposit)` to process and record the initial deposit.

2.  ### `deposit(self, amount: float)`
    *   **Description**: Adds the specified `amount` of funds to the account's cash balance.
    *   **Parameters**:
        *   `amount` (float): The amount of money to deposit. Must be a positive value.
    *   **Raises**:
        *   `InvalidAmountError`: If `amount` is not positive.
    *   **Behavior**:
        *   Increases `_balance` by `amount`.
        *   Records a 'DEPOSIT' transaction including timestamp and amount.

3.  ### `withdraw(self, amount: float)`
    *   **Description**: Removes the specified `amount` of funds from the account's cash balance.
    *   **Parameters**:
        *   `amount` (float): The amount of money to withdraw. Must be a positive value.
    *   **Raises**:
        *   `InvalidAmountError`: If `amount` is not positive.
        *   `InsufficientFundsError`: If the withdrawal would result in a negative cash balance.
    *   **Behavior**:
        *   Decreases `_balance` by `amount`.
        *   Records a 'WITHDRAWAL' transaction including timestamp and amount.

4.  ### `buy_shares(self, symbol: str, quantity: int)`
    *   **Description**: Purchases a specified `quantity` of shares for a given `symbol`.
    *   **Parameters**:
        *   `symbol` (str): The stock symbol (e.g., "AAPL") to buy.
        *   `quantity` (int): The number of shares to purchase. Must be a positive integer.
    *   **Raises**:
        *   `InvalidQuantityError`: If `quantity` is not positive.
        *   `ValueError`: If `_get_share_price_func` returns `0.0` or a negative value for the `symbol`, indicating an invalid or unsupported symbol.
        *   `InsufficientFundsError`: If the account's `_balance` is insufficient to cover the total cost of the purchase.
    *   **Behavior**:
        *   Retrieves the current `price_per_share` using `_get_share_price_func`.
        *   Calculates `total_cost = price_per_share * quantity`.
        *   Decreases `_balance` by `total_cost`.
        *   Updates `_holdings`: increments the `quantity` for the `symbol` (or initializes it if this is the first purchase of that symbol).
        *   Records a 'BUY' transaction including timestamp, symbol, quantity, price per share, and total cost.

5.  ### `sell_shares(self, symbol: str, quantity: int)`
    *   **Description**: Sells a specified `quantity` of shares for a given `symbol`.
    *   **Parameters**:
        *   `symbol` (str): The stock symbol (e.g., "AAPL") to sell.
        *   `quantity` (int): The number of shares to sell. Must be a positive integer.
    *   **Raises**:
        *   `InvalidQuantityError`: If `quantity` is not positive.
        *   `InsufficientSharesError`: If the account does not hold the specified `quantity` of `symbol`.
        *   `ValueError`: If `_get_share_price_func` returns `0.0` or a negative value for the `symbol`, indicating an invalid or unsupported symbol.
    *   **Behavior**:
        *   Retrieves the current `price_per_share` using `_get_share_price_func`.
        *   Calculates `total_proceeds = price_per_share * quantity`.
        *   Increases `_balance` by `total_proceeds`.
        *   Updates `_holdings`: decrements the `quantity` for the `symbol`. If the quantity for that `symbol` becomes `0` or less, the `symbol` is removed from `_holdings`.
        *   Records a 'SELL' transaction including timestamp, symbol, quantity, price per share, and total proceeds.

6.  ### `get_account_id(self) -> str`
    *   **Description**: Returns the unique identifier of the account.
    *   **Returns**:
        *   `str`: The `_account_id` of the account.

7.  ### `get_balance(self) -> float`
    *   **Description**: Returns the current cash balance in the account.
    *   **Returns**:
        *   `float`: The current `_balance`.

8.  ### `get_holdings(self) -> Dict[str, int]`
    *   **Description**: Returns a copy of the current stock holdings of the account.
    *   **Returns**:
        *   `Dict[str, int]`: A dictionary mapping stock symbols to the quantity of shares held. A copy is returned to prevent external modification of the internal state.

9.  ### `get_portfolio_value(self) -> float`
    *   **Description**: Calculates the total value of the account's portfolio, which includes the current cash balance plus the current market value of all held shares.
    *   **Returns**:
        *   `float`: The total portfolio value.
    *   **Behavior**:
        *   Iterates through `_holdings`, retrieves the current price for each symbol using `_get_share_price_func`, and sums `price * quantity` to get the total market value of shares. Symbols for which `_get_share_price_func` returns `0.0` will contribute `0.0` to the market value.
        *   Adds the `_balance` to this total market value to get the final portfolio value.

10. ### `get_profit_loss(self) -> float`
    *   **Description**: Calculates the overall profit or loss for the account. This is defined as the difference between the `current total portfolio value` and the `net capital injected` into the account (total deposits minus total withdrawals).
    *   **Returns**:
        *   `float`: The calculated profit or loss.
    *   **Behavior**:
        *   Sums all `amount`s from 'DEPOSIT' transactions to get `total_deposits`.
        *   Sums all `amount`s from 'WITHDRAWAL' transactions to get `total_withdrawals`.
        *   Calculates `net_capital_injected = total_deposits - total_withdrawals`.
        *   Retrieves `current_total_value` by calling `self.get_portfolio_value()`.
        *   Calculates `profit_loss = current_total_value - net_capital_injected`.

11. ### `get_transactions(self) -> List[Dict]`
    *   **Description**: Returns a chronological list of all transactions that have occurred in the account.
    *   **Returns**:
        *   `List[Dict]`: A shallow copy of the internal `_transactions` list, ensuring the original list cannot be modified externally.

## Complete `accounts.py` Module Content

```python
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
```
```