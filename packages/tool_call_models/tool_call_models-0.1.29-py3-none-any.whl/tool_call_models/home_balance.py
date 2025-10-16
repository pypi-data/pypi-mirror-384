from pydantic import BaseModel, Field, model_validator
from typing import Dict, Union
from .base import BaseToolCallModel


class HomeBalanceDetails(BaseModel):
    balance: int
    details: Dict[Union[str, int], Union[int, float, str]] = Field(default_factory=dict)

    def __init__(self, **data):
        if "balance" in data and data["balance"] is not None:
            if isinstance(data["balance"], str):
                data["balance"] = int(data["balance"])
            data["balance"] = data["balance"] // 100
        else:
            data["balance"] = 0
        super().__init__(**data)

    def filter_for_llm(self):
        return {
            "balance": self.balance if self.balance else None,
        }


class HomeBalance(BaseToolCallModel, BaseModel):
    homeName: str
    services: Dict[str, HomeBalanceDetails] = Field(default_factory=dict)

    @model_validator(mode="before")
    def extract_services(cls, values):
        known_keys = {"homeName"}
        services = {k: v for k, v in values.items() if k not in known_keys}
        values["services"] = services
        return values

    def filter_for_llm(self):
        # no need for details
        return {
            "homeName": self.homeName,
            "services": {k: v.filter_for_llm() for k, v in self.services.items()},
        }
