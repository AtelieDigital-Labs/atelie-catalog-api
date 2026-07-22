from dataclasses import dataclass

@dataclass
class StoreCreatedEvent:
    artisan_id: str
    store_id: str
    pix_key: str