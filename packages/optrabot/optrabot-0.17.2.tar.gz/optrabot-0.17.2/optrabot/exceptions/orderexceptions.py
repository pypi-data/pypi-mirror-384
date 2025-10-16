"""
This module contains custom exceptions related to order operations
"""

from optrabot.broker.order import Order


class OrderException(Exception):
    """
    Base class for all order-related exceptions
    """
    def __init__(self, reason: str, order: Order, operation: str = "Unspecific operation", *args):
        """
        Initialize the exception with a message

        Args:
            reason: Reason why the order operation failed
            order: The order that failed to be placed
            args: Additional arguments to pass to the base Exception class
        """
        super().__init__(reason, *args)
        self.reason = reason
        self.operation = operation
        self.order = order

    def __str__(self):
        """
        Return a string representation of the exception
        """
        return f"{self.operation} of order failed: {self.reason}"

class PlaceOrderException(OrderException):
    """
    Exception raised when an order placement fails
    """
    def __init__(self, reason: str, order: Order, *args):
        """
        Initialize the exception with a reason for the failure

        Args:
            reason: The reason why the order placement failed
            order: The order that failed to be placed
            args: Additional arguments to pass to the base Exception class
        """
        super().__init__(reason, order, operation="Place order", *args)

class PrepareOrderException(OrderException):
    """
    Exception raised when preparing an order fails
    """
    def __init__(self, reason: str, order: Order, *args):
        """
        Initialize the exception with a reason for the failure

        Args:
            reason: The reason why the order preparation failed
            order: The order that failed to be prepared
            args: Additional arguments to pass to the base Exception class
        """
        super().__init__(reason, order, operation="Prepare order", *args)