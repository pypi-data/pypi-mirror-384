from pydantic import BaseModel

class PubSubMessage(BaseModel):
    """ Model for Pub/Sub message """
    message: dict
    subscription: str