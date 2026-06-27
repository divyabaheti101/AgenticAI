import unittest
import datetime
from unittest.mock import patch, MagicMock

# Assuming accounts.py is in the same directory
from accounts import (
    Account,
    InsufficientFundsError,
    InsufficientSharesError,
    InvalidQuantityError,
    InvalidAmountError,
    _default_get_share_price
)

# Custom mock for _get_share_price_func to control test prices
def mock_get_share_price(symbol: str) -> float:
    """
    A mock function for fetching share prices during tests.
    Returns fixed prices for specific symbols and 0.0 for others.
    """
    prices = {
        "TESTA": 100.00,
        "TESTB": 50.00,
        "TESTC": 200.00,
        "ZERO_PRICE": 0.0,
        "NEGATIVE_PRICE": -10.0,
    }
    return prices.get(symbol, 0.0)

class TestAccount(unittest.TestCase):

    def setUp(self):
        # Patch datetime.datetime.now() to ensure consistent timestamps for testing transactions
        self.mock_now = datetime.datetime(2023, 1, 1, 10, 0, 0)
        self.patcher = patch('datetime.datetime')
        self.mock_datetime = self.patcher.start()
        self.mock_datetime.now.return_value = self.mock_now

    def tearDown(self):
        self.patcher.stop()

    # --- Test _default_get_share_price helper function ---
    def test_default_get_share_price_helper(self):
        self.assertAlmostEqual(_default_get_share_price("AAPL"), 170.50)
        self.assertAlmostEqual(_default_get_share_price("TSLA"), 250.75)
        self.assertAlmostEqual(_default_get_share_price("GOOGL"), 140.20)
        self.assertAlmostEqual(_default_get_share_price("UNKNOWN_SYMBOL"), 0.0)
        self.assertAlmostEqual(_default_get_share_price(""), 0.0)

    # --- Test __init__ ---
    def test_init_default_deposit(self):
        account = Account("acc1")
        self.assertEqual(account.get_account_id(), "acc1")
        self.assertAlmostEqual(account.get_balance(), 0.0)
        self.assertEqual(account.get_holdings(), {})
        self.assertEqual(len(account.get_transactions()), 0) # No initial deposit means no transaction

    def test_init_with_initial_deposit(self):
        account = Account("acc2", initial_deposit=1000.0)
        self.assertEqual(account.get_account_id(), "acc2")
        self.assertAlmostEqual(account.get_balance(), 1000.0)
        self.assertEqual(account.get_holdings(), {})
        self.assertEqual(len(account.get_transactions()), 1)
        self.assertEqual(account.get_transactions()[0]["type"], "DEPOSIT")
        self.assertAlmostEqual(account.get_transactions()[0]["amount"], 1000.0)
        self.assertEqual(account.get_transactions()[0]["timestamp"], self.mock_now.isoformat())


    def test_init_with_negative_initial_deposit_raises_error(self):
        with self.assertRaises(InvalidAmountError):
            Account("acc3", initial_deposit=-100.0)

    def test_init_with_custom_get_share_price_func(self):
        mock_price_func = MagicMock(return_value=150.0)
        account = Account("acc4", get_share_price_func=mock_price_func)
        # Verify it uses the custom function by calling a method that would invoke it
        account.buy_shares("ANY_SYMBOL", 1, initial_deposit=200) # Buy to trigger price lookup
        mock_price_func.assert_called_with("ANY_SYMBOL")

    def test_init_with_default_get_share_price_func_if_not_provided(self):
        # Create account without providing custom function, it should use _default_get_share_price
        account = Account("acc_default", initial_deposit=500.0)
        
        # Test buying a stock known by _default_get_share_price (AAPL=170.50)
        account.buy_shares("AAPL", 1) 
        self.assertEqual(account.get_holdings()["AAPL"], 1)
        self.assertAlmostEqual(account.get_balance(), 500.0 - 170.50)
        self.assertEqual(len(account.get_transactions()), 2) # Initial deposit + buy

    # --- Test deposit ---
    def test_deposit_positive_amount(self):
        account = Account("acc1")
        initial_balance = account.get_balance()
        account.deposit(500.0)
        self.assertAlmostEqual(account.get_balance(), initial_balance + 500.0)
        self.assertEqual(len(account.get_transactions()), 1)
        self.assertEqual(account.get_transactions()[0]["type"], "DEPOSIT")
        self.assertAlmostEqual(account.get_transactions()[0]["amount"], 500.0)
        self.assertEqual(account.get_transactions()[0]["timestamp"], self.mock_now.isoformat())

    def test_deposit_zero_amount_raises_error(self):
        account = Account("acc1")
        with self.assertRaises(InvalidAmountError):
            account.deposit(0.0)
        self.assertAlmostEqual(account.get_balance(), 0.0)
        self.assertEqual(len(account.get_transactions()), 0) # No transaction for invalid deposit

    def test_deposit_negative_amount_raises_error(self):
        account = Account("acc1")
        with self.assertRaises(InvalidAmountError):
            account.deposit(-100.0)
        self.assertAlmostEqual(account.get_balance(), 0.0)
        self.assertEqual(len(account.get_transactions()), 0) # No transaction for invalid deposit

    # --- Test withdraw ---
    def test_withdraw_positive_amount_sufficient_funds(self):
        account = Account("acc1", initial_deposit=1000.0)
        initial_balance = account.get_balance()
        account.withdraw(500.0)
        self.assertAlmostEqual(account.get_balance(), initial_balance - 500.0)
        self.assertEqual(len(account.get_transactions()), 2) # Initial deposit + withdrawal
        self.assertEqual(account.get_transactions()[1]["type"], "WITHDRAWAL")
        self.assertAlmostEqual(account.get_transactions()[1]["amount"], 500.0)
        self.assertEqual(account.get_transactions()[1]["timestamp"], self.mock_now.isoformat())


    def test_withdraw_zero_amount_raises_error(self):
        account = Account("acc1", initial_deposit=1000.0)
        with self.assertRaises(InvalidAmountError):
            account.withdraw(0.0)
        self.assertAlmostEqual(account.get_balance(), 1000.0)
        self.assertEqual(len(account.get_transactions()), 1) # Only initial deposit transaction

    def test_withdraw_negative_amount_raises_error(self):
        account = Account("acc1", initial_deposit=1000.0)
        with self.assertRaises(InvalidAmountError):
            account.withdraw(-100.0)
        self.assertAlmostEqual(account.get_balance(), 1000.0)
        self.assertEqual(len(account.get_transactions()), 1) # Only initial deposit transaction

    def test_withdraw_insufficient_funds_raises_error(self):
        account = Account("acc1", initial_deposit=100.0)
        with self.assertRaises(InsufficientFundsError):
            account.withdraw(200.0)
        self.assertAlmostEqual(account.get_balance(), 100.0) # Balance should not change
        self.assertEqual(len(account.get_transactions()), 1) # Only initial deposit transaction

    # --- Test buy_shares ---
    def test_buy_shares_successful(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        account.buy_shares("TESTA", 10) # Price is 100.0, cost = 1000.0
        self.assertAlmostEqual(account.get_balance(), 1000.0)
        self.assertEqual(account.get_holdings(), {"TESTA": 10})
        self.assertEqual(len(account.get_transactions()), 2) # Initial deposit + buy
        transaction = account.get_transactions()[1]
        self.assertEqual(transaction["type"], "BUY")
        self.assertEqual(transaction["symbol"], "TESTA")
        self.assertEqual(transaction["quantity"], 10)
        self.assertAlmostEqual(transaction["price_per_share"], 100.0)
        self.assertAlmostEqual(transaction["total_cost_or_proceeds"], 1000.0)
        self.assertEqual(transaction["timestamp"], self.mock_now.isoformat())

    def test_buy_shares_invalid_quantity_zero_raises_error(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        with self.assertRaises(InvalidQuantityError):
            account.buy_shares("TESTA", 0)
        self.assertEqual(account.get_holdings(), {})
        self.assertAlmostEqual(account.get_balance(), 2000.0)

    def test_buy_shares_invalid_quantity_negative_raises_error(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        with self.assertRaises(InvalidQuantityError):
            account.buy_shares("TESTA", -5)
        self.assertEqual(account.get_holdings(), {})
        self.assertAlmostEqual(account.get_balance(), 2000.0)

    def test_buy_shares_insufficient_funds_raises_error(self):
        account = Account("acc1", initial_deposit=500.0, get_share_price_func=mock_get_share_price)
        with self.assertRaises(InsufficientFundsError):
            account.buy_shares("TESTA", 10) # Cost 1000.0
        self.assertAlmostEqual(account.get_balance(), 500.0)
        self.assertEqual(account.get_holdings(), {})

    def test_buy_shares_invalid_price_zero_raises_error(self):
        account = Account("acc1", initial_deposit=1000.0, get_share_price_func=mock_get_share_price)
        with self.assertRaises(ValueError):
            account.buy_shares("ZERO_PRICE", 5) # Price 0.0 from mock
        self.assertAlmostEqual(account.get_balance(), 1000.0)
        self.assertEqual(account.get_holdings(), {})

    def test_buy_shares_invalid_price_negative_raises_error(self):
        account = Account("acc1", initial_deposit=1000.0, get_share_price_func=mock_get_share_price)
        with self.assertRaises(ValueError):
            account.buy_shares("NEGATIVE_PRICE", 5) # Price -10.0 from mock
        self.assertAlmostEqual(account.get_balance(), 1000.0)
        self.assertEqual(account.get_holdings(), {})

    def test_buy_shares_add_to_existing_holdings(self):
        account = Account("acc1", initial_deposit=3000.0, get_share_price_func=mock_get_share_price)
        account.buy_shares("TESTA", 10) # Cost 1000, balance 2000, holdings {"TESTA": 10}
        account.buy_shares("TESTA", 5)  # Cost 500, balance 1500, holdings {"TESTA": 15}
        self.assertAlmostEqual(account.get_balance(), 1500.0)
        self.assertEqual(account.get_holdings(), {"TESTA": 15})
        self.assertEqual(len(account.get_transactions()), 3) # Initial deposit + 2 buys

    # --- Test sell_shares ---
    def test_sell_shares_successful(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        account.buy_shares("TESTA", 10) # Price 100, cost 1000, balance 1000, holdings {"TESTA": 10}
        account.sell_shares("TESTA", 5) # Price 100, proceeds 500, balance 1500, holdings {"TESTA": 5}
        self.assertAlmostEqual(account.get_balance(), 1500.0)
        self.assertEqual(account.get_holdings(), {"TESTA": 5})
        self.assertEqual(len(account.get_transactions()), 3) # Initial deposit + buy + sell
        transaction = account.get_transactions()[2]
        self.assertEqual(transaction["type"], "SELL")
        self.assertEqual(transaction["symbol"], "TESTA")
        self.assertEqual(transaction["quantity"], 5)
        self.assertAlmostEqual(transaction["price_per_share"], 100.0)
        self.assertAlmostEqual(transaction["total_cost_or_proceeds"], 500.0)
        self.assertEqual(transaction["timestamp"], self.mock_now.isoformat())


    def test_sell_shares_invalid_quantity_zero_raises_error(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        account.buy_shares("TESTA", 10)
        with self.assertRaises(InvalidQuantityError):
            account.sell_shares("TESTA", 0)
        self.assertEqual(account.get_holdings(), {"TESTA": 10}) # Holdings unchanged

    def test_sell_shares_invalid_quantity_negative_raises_error(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        account.buy_shares("TESTA", 10)
        with self.assertRaises(InvalidQuantityError):
            account.sell_shares("TESTA", -5)
        self.assertEqual(account.get_holdings(), {"TESTA": 10}) # Holdings unchanged

    def test_sell_shares_insufficient_shares_raises_error(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        account.buy_shares("TESTA", 10)
        with self.assertRaises(InsufficientSharesError):
            account.sell_shares("TESTA", 15)
        self.assertEqual(account.get_holdings(), {"TESTA": 10}) # Holdings unchanged
        self.assertAlmostEqual(account.get_balance(), 1000.0) # Balance unchanged

    def test_sell_shares_symbol_not_held_raises_error(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        with self.assertRaises(InsufficientSharesError):
            account.sell_shares("TESTA", 5) # TESTA not in holdings
        self.assertEqual(account.get_holdings(), {})
        self.assertAlmostEqual(account.get_balance(), 2000.0)

    def test_sell_shares_removes_symbol_when_quantity_zero(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        account.buy_shares("TESTA", 10) # Holdings {"TESTA": 10}, balance 1000
        account.sell_shares("TESTA", 10) # Sell all, holdings {}
        self.assertEqual(account.get_holdings(), {})
        self.assertAlmostEqual(account.get_balance(), 2000.0) # 2000 (initial) - 1000 (buy) + 1000 (sell) = 2000

    def test_sell_shares_invalid_price_zero_raises_error(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        account.buy_shares("TESTA", 10) # Balance 1000, Holdings {"TESTA": 10}
        with self.assertRaises(ValueError):
            account.sell_shares("ZERO_PRICE", 5) # This symbol has zero price in mock
        self.assertEqual(account.get_holdings(), {"TESTA": 10})
        self.assertAlmostEqual(account.get_balance(), 1000.0)

    def test_sell_shares_invalid_price_negative_raises_error(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        account.buy_shares("TESTA", 10) # Balance 1000, Holdings {"TESTA": 10}
        with self.assertRaises(ValueError):
            account.sell_shares("NEGATIVE_PRICE", 5) # This symbol has negative price in mock
        self.assertEqual(account.get_holdings(), {"TESTA": 10})
        self.assertAlmostEqual(account.get_balance(), 1000.0)

    # --- Test getters ---
    def test_get_account_id(self):
        account = Account("unique_id_123")
        self.assertEqual(account.get_account_id(), "unique_id_123")

    def test_get_balance(self):
        account = Account("acc1", initial_deposit=500.0)
        self.assertAlmostEqual(account.get_balance(), 500.0)
        account.deposit(200.0)
        self.assertAlmostEqual(account.get_balance(), 700.0)
        account.withdraw(100.0)
        self.assertAlmostEqual(account.get_balance(), 600.0)

    def test_get_holdings(self):
        account = Account("acc1", initial_deposit=2000.0, get_share_price_func=mock_get_share_price)
        self.assertEqual(account.get_holdings(), {})
        account.buy_shares("TESTA", 10)
        self.assertEqual(account.get_holdings(), {"TESTA": 10})
        account.buy_shares("TESTB", 5)
        self.assertEqual(account.get_holdings(), {"TESTA": 10, "TESTB": 5})
        account.sell_shares("TESTA", 5)
        self.assertEqual(account.get_holdings(), {"TESTA": 5, "TESTB": 5})
        account.sell_shares("TESTA", 5)
        self.assertEqual(account.get_holdings(), {"TESTB": 5})
        
        # Test that it returns a copy, not the internal dictionary reference
        holdings_copy = account.get_holdings()
        holdings_copy["NEW_STOCK"] = 1
        self.assertNotEqual(account.get_holdings(), holdings_copy)
        self.assertNotIn("NEW_STOCK", account.get_holdings())


    def test_get_portfolio_value(self):
        account = Account("acc1", initial_deposit=1000.0, get_share_price_func=mock_get_share_price)
        # Initial: balance 1000, holdings {} -> value 1000
        self.assertAlmostEqual(account.get_portfolio_value(), 1000.0)

        account.buy_shares("TESTA", 5) # Price 100.0, cost 500.0
        # Balance 500, holdings {"TESTA": 5} (market value 5 * 100 = 500) -> total value 500 + 500 = 1000
        self.assertAlmostEqual(account.get_portfolio_value(), 1000.0)

        account.buy_shares("TESTB", 10) # Price 50.0, cost 500.0
        # Balance 0, holdings {"TESTA": 5, "TESTB": 10} (market value 5*100 + 10*50 = 500 + 500 = 1000) -> total value 0 + 1000 = 1000
        self.assertAlmostEqual(account.get_portfolio_value(), 1000.0)
        
        # Manually add a stock that mock_get_share_price returns 0.0 for (should not add to portfolio value)
        account._holdings["UNKNOWN_STOCK_ZERO_PRICE"] = 10 
        self.assertAlmostEqual(account.get_portfolio_value(), 1000.0) # Still 1000, as UNKNOWN_STOCK has 0 price

        # Manually add a stock that mock_get_share_price returns negative for (should not add to portfolio value)
        account._holdings["NEGATIVE_PRICE"] = 5
        self.assertAlmostEqual(account.get_portfolio_value(), 1000.0) # Still 1000, as NEGATIVE_PRICE stock has negative price

    def test_get_profit_loss(self):
        account = Account("acc1", get_share_price_func=mock_get_share_price)
        self.assertAlmostEqual(account.get_profit_loss(), 0.0) # No activity: current_value 0, injected 0 -> P/L 0

        account.deposit(1000.0) # Injected: 1000 (deposit 1000)
        # Current total value: 1000 (balance) + 0 (holdings) = 1000
        # P/L = 1000 - 1000 = 0
        self.assertAlmostEqual(account.get_profit_loss(), 0.0) 

        account.buy_shares("TESTA", 5) # Price 100.0, cost 500.0
        # Balance 500, holdings {"TESTA": 5} (market value 500)
        # Current total value: 500 (balance) + 500 (holdings) = 1000
        # Injected: 1000
        # P/L = 1000 - 1000 = 0
        self.assertAlmostEqual(account.get_profit_loss(), 0.0)

        account.withdraw(200.0) # Injected: 1000 (deposit) - 200 (withdrawal) = 800
        # Balance 300, holdings {"TESTA": 5} (market value 500)
        # Current total value: 300 (balance) + 500 (holdings) = 800
        # P/L = 800 - 800 = 0
        self.assertAlmostEqual(account.get_profit_loss(), 0.0)

        # Simulate price increase for TESTA
        def mock_price_increase_for_pl(symbol: str) -> float:
            if symbol == "TESTA":
                return 120.0 # Price increased
            return mock_get_share_price(symbol) # Use default mock for others
        
        # Temporarily change the price function for P/L calculation test
        original_price_func = account._get_share_price_func
        account._get_share_price_func = mock_price_increase_for_pl
        
        # Current value with new price: Balance 300 + (5 * 120.0) = 300 + 600 = 900
        # Net capital injected: 800
        # P/L = 900 - 800 = 100
        self.assertAlmostEqual(account.get_profit_loss(), 100.0)

        # Simulate price decrease
        def mock_price_decrease_for_pl(symbol: str) -> float:
            if symbol == "TESTA":
                return 80.0 # Price decreased
            return mock_get_share_price(symbol) # Use default mock for others
        
        account._get_share_price_func = mock_price_decrease_for_pl
        # Current value with new price: Balance 300 + (5 * 80.0) = 300 + 400 = 700
        # Net capital injected: 800
        # P/L = 700 - 800 = -100
        self.assertAlmostEqual(account.get_profit_loss(), -100.0)

        # Restore original price func for other potential tests if this wasn't the last P/L test
        account._get_share_price_func = original_price_func

    def test_get_transactions(self):
        account = Account("acc1", initial_deposit=100.0, get_share_price_func=mock_get_share_price)
        account.deposit(50.0)
        account.withdraw(20.0)
        account.buy_shares("TESTA", 1) # Cost 100.0, balance 30.0 (100+50-20-100)
        account.sell_shares("TESTA", 1) # Proceeds 100.0, balance 130.0 (30+100)

        transactions = account.get_transactions()
        self.assertEqual(len(transactions), 5)
        self.assertEqual(transactions[0]["type"], "DEPOSIT")
        self.assertEqual(transactions[1]["type"], "DEPOSIT")
        self.assertEqual(transactions[2]["type"], "WITHDRAWAL")
        self.assertEqual(transactions[3]["type"], "BUY")
        self.assertEqual(transactions[4]["type"], "SELL")
        
        # Verify timestamps are mocked correctly for all transactions
        for t in transactions:
            self.assertEqual(t["timestamp"], self.mock_now.isoformat())

        # Test that it returns a copy, not the internal list reference
        transactions_copy = account.get_transactions()
        transactions_copy.append({"type": "FAKE"})
        self.assertNotEqual(len(account.get_transactions()), len(transactions_copy))
        self.assertEqual(len(account.get_transactions()), 5) # Original list should be unchanged

if __name__ == '__main__':
    unittest.main()