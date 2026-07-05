from app.core.logger import setup_trigger_logger
from sqlalchemy import event, inspect
from sqlalchemy.orm import Mapper
from sqlalchemy.engine import Connection
from app.models.product import ProductVariation
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm.attributes import get_history
from app.core.context import current_user_id
from app.models.outbox import LogOutbox
from app.models.store import Address

logger = setup_trigger_logger()


@event.listens_for(ProductVariation, 'before_update')
def generate_log_update_stock_product(mapper: Mapper, connection: Connection, target: ProductVariation):
    actor = str(current_user_id.get())

    stock_history = get_history(target, 'stock')

    if not stock_history.has_changes():
        return

    old_price = stock_history.deleted[0] if stock_history.deleted else None

    new_price = stock_history.added[0] if stock_history.added else None

    old_value_str = old_price.value if hasattr(old_price, 'value') else str(old_price)
    new_value_str = new_price.value if hasattr(new_price, 'value') else str(new_price)

    log_payload = {
        "log_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "microservice": "Catalog",
        "actor": {
            "user_id": actor
        },
        "action": "UPDATE",
        "resource": "ProductVariation",
        "resource_id": target.id,
        "changes": {
            "stock": {
                "old_value": old_value_str,
                "new_value": new_value_str
            }
        },
        "reason": "Alteração de estoque do produto variante"
    }

    print(log_payload)

    connection.execute(
        LogOutbox.__table__.insert().values(
            log_id = log_payload["log_id"],
            aggregate_type = "ProductVariant",
            aggregate_id = str(target.id), 
            payload = log_payload,
            processed = False
        )
    )

    logger.info(f"[UPDATE] Gatilho acionado com sucesso. Estoque alterado de {old_value_str} para {new_value_str} no produto variante {target.id}.")


@event.listens_for(ProductVariation, 'before_update')
def generate_log_update_price_product(mapper: Mapper, connection: Connection, target: ProductVariation):
    actor = str(current_user_id.get())

    price_history = get_history(target, 'price')

    if not price_history.has_changes():
        return

    old_price = price_history.deleted[0] if price_history.deleted else None
    print(old_price)

    new_price = price_history.added[0] if price_history.added else None

    old_value_str = old_price.value if hasattr(old_price, 'value') else str(old_price)
    new_value_str = new_price.value if hasattr(new_price, 'value') else str(new_price)

    log_payload = {
        "log_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "microservice": "Catalog",
        "actor": {
            "user_id": actor
        },
        "action": "UPDATE",
        "resource": "ProductVariation",
        "resource_id": target.id,
        "changes": {
            "price": {
                "old_value": old_value_str,
                "new_value": new_value_str
            }
        },
        "reason": "Alteração de preço do produto variante"
    }
    
    print(log_payload)


    connection.execute(
        LogOutbox.__table__.insert().values(
            log_id = log_payload["log_id"],
            aggregate_type = "ProductVariant",
            aggregate_id = str(target.id), 
            payload = log_payload,
            processed = False
        )
    )

    logger.info(f"[UPDATE] Gatilho acionado com sucesso. Preço alterado de {old_value_str} para {new_value_str} no produto variante {target.id}.")

@event.listens_for(Address, 'before_update')
def generate_log_update_store(mapper: Mapper, connection: Connection, target: Address):
    actor = str(current_user_id.get())

    st = inspect(target)

    alters = {}

    for attr in st.attrs:
        hist = attr.history

        if hist.has_changes():
            alters[attr.key] = {
                "old_value": list(hist.deleted) if hist.deleted else None,
                "new_value": list(hist.added) if hist.added else None
            }

    log_payload = {
        "log_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "microservice": "Catalog",
        "actor": {
            "user_id": actor
        },
        "action": "UPDATE",
        "resource": "Address Store",
        "resource_id": target.id,
        "changes": alters,
        "reason": "Alteração de dados do endereço da loja"
    }

    print(log_payload)


    connection.execute(
        LogOutbox.__table__.insert().values(
            log_id = log_payload["log_id"],
            aggregate_type = "Address",
            aggregate_id = str(target.id), 
            payload = log_payload,
            processed = False
        )
    )

    logger.info(f"[UPDATE] Gatilho acionado com sucesso. Endereço da loja {target.store_id} alterado.")