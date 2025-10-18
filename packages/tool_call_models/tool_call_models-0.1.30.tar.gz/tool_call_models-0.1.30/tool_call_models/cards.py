from pydantic import BaseModel, Field, model_validator
from typing import List, Union, Optional, Dict

from .base import BaseToolCallModel
import json

# import override from typing_extensions or from typing package whichever is available
try:
    from typing_extensions import override
except ImportError:
    from typing import override


class CardDetails(BaseModel):
    cardDetailsId: int
    cardName: str
    cardColor: str
    cardIsPrimary: bool


class CardBalance(BaseModel):
    balance: Union[int, str] = Field(..., description="Balance in cents")
    status: int

    @model_validator(mode="before")
    def validate_balance(cls, values):
        if isinstance(values.get("balance"), str) and len(values["balance"]) == 0:
            print("balance is empty setting to 0")
            values["balance"] = 0
        if isinstance(values["balance"], str):
            print("balance is string setting to 0")
            values["balance"] = int(values["balance"])
        return values


class BankIcon(BaseModel):
    bankLogo: str
    bankLogoMini: str
    bankWhiteLogo: str
    bankWhiteLogoMini: str


class Card(BaseModel):
    panMask: str
    panToken: str
    requestId: str
    pan: str
    expiry: str
    bankIssuer: str
    uzcardToken: Optional[str] = None
    processingSystem: str
    salaryAmount: Union[int, str] = Field(..., description="Salary amount in cents")
    isVerified: bool
    createdAt: str
    cardDetails: CardDetails
    cardBalance: CardBalance
    isVirtual: bool
    bankIcon: BankIcon

    def __init__(self, **data):
        if isinstance(data.get("salaryAmount"), (str, int)):
            data["salaryAmount"] = int(data["salaryAmount"]) // 100
        super().__init__(**data)


class CardBalanceResponseBody(BaseToolCallModel, BaseModel):
    custNo: str
    phoneNumber: str
    firstname: str
    middlename: str
    lastname: str
    birthDate: str
    pinfl: str
    createdAt: str
    cardList: List[Card]

    @override
    def filter_for_llm(self):
        # print("Filter For LLM in CardBalanceResponseBody")
        return [
            {
                "pan": card.pan,
                "balance": int(card.cardBalance.balance) // 100,
                "bankIssuer": card.bankIssuer,
                "CardName": card.cardDetails.cardName,
            }
            for card in self.cardList
        ]


class CardsBalanceResponse(BaseToolCallModel, BaseModel):
    body: List[CardBalanceResponseBody] = Field(
        default_factory=[],  # pyright: ignore[reportArgumentType]
        description="List of card balance responses",
    )
    status: Optional[Union[int, str]] = Field(..., description="Status code")
    workflowId: Optional[str] = None

    @override
    def filter_for_llm(self):
        # print("Filter For LLM in CardsBalanceResponse")
        output = []
        for card in self.body:
            output.append(card.filter_for_llm())
        return json.dumps(output, ensure_ascii=False, indent=2)


class CardInfoByPhoneNumber(BaseModel):
    pan: str
    name: str
    processing: str
    mask: str


class CardsByPhoneNumberResponse(BaseToolCallModel, BaseModel):
    cards: List[CardInfoByPhoneNumber]

    @override
    def filter_for_llm(self):
        return json.dumps(
            [x.model_dump(by_alias=True) for x in self.cards],
            ensure_ascii=False,
            indent=2,
        )


class CardInfoByCard(BaseToolCallModel, BaseModel):
    processingSystem: Optional[str] = None
    iconMini: Optional[str] = None
    isFound: Optional[bool] = None
    maskedPan: Optional[str] = None
    errorMessage: Optional[str] = None
    icon: Optional[str] = None
    fullName: Optional[str] = None
    errorCode: Optional[str] = None
    token: Optional[str] = None

    @override
    def filter_for_llm(self):
        return {
            "processingSystem": self.processingSystem,
            "maskedPan": self.maskedPan,
            "fullName": self.fullName,
            "token": self.token,
        }


class CardInfoByCardNumberResponse(BaseToolCallModel, BaseModel):
    status: Optional[str] = None
    workflowId: Optional[str] = None
    body: Optional[List[CardInfoByCard]] = None

    @override
    def filter_for_llm(self):
        if self.body:
            return json.dumps(
                [card.filter_for_llm() for card in self.body],
                ensure_ascii=False,
                indent=2,
            )
        return json.dumps(
            {"status": self.status, "workflowId": self.workflowId},
            ensure_ascii=False,
            indent=2,
        )
