# Introduction

This package provides a simple message queue for commands and events. The queue is synchronous and lacks certain frills
you might expect from a more elaborate message queue.

The idea is to split your business logic in commands and events and write small function-based handlers which you can
register to either of them.

```python
import dataclasses

from queuebie.runner import handle_message
from queuebie.messages import Command, Event
from queuebie import message_registry


# Example command
@dataclasses.dataclass(kw_only=True)
class BuyProduct(Command):
    product_id: int
    customer_id: int
    price: float
    currency: str


# Example event
@dataclasses.dataclass(kw_only=True)
class ProductBought(Event):
    product_id: int
    customer_id: int


# Example handler
@message_registry.register_command(BuyProduct)
def handle_buy_product(context: BuyProduct) -> Event:
    # Here lives your business logic

    return ProductBought(
        product_id=context.product_id,
        customer_id=context.customer_id,
    )


# Start queue and process messages
handle_message(
    BuyProduct(
        product_id=product.id,
        customer_id=customer.id,
        price=12.99,
        currency="EUR",
    )
)
```
