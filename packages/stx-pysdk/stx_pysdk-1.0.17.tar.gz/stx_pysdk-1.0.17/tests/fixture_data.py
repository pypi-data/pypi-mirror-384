from unittest.mock import MagicMock

import pytest

from stxsdk import Selection
from stxsdk.storage.user_storage import User


@pytest.fixture
def selection():
    return Selection


@pytest.fixture
def user():
    return User


@pytest.fixture
def client():
    class Client:
        def __init__(self):
            self.transport = MagicMock()
            self.transport.headers = None

    return Client


login_return_fields = {
    "currentLoginAt": "String",
    "deviceId": "String",
    "ipAddress": "String",
    "lastLoginAt": "String",
    "limitsNumber": {
        "accountLimits": {
            "accountId": "rID",
            "coolOffPeriod": "Int",
            "dailyDeposit": "Int",
            "hoursPerDay": "Int",
            "lifetimeDeposit": "Int",
            "lossLimit24Hours": "Int",
            "lossLimitMonthly": "Int",
            "lossLimitWeekly": "Int",
            "maxOrderLiabilityPerOrder": "Int",
            "monthlyDeposit": "Int",
            "orderLiability": "Int",
            "weeklyDeposit": "Int",
        },
        "adminLimits": {
            "coolOffPeriod": "Int",
            "dailyDeposit": "Int",
            "hoursPerDay": "Int",
            "lifetimeDeposit": "Int",
            "lossLimit24Hours": "Int",
            "lossLimitMonthly": "Int",
            "lossLimitWeekly": "Int",
            "maxOrderLiabilityPerOrder": "Int",
            "monthlyDeposit": "Int",
            "orderLiability": "Int",
            "weeklyDeposit": "Int",
        },
    },
    "promptTncAcceptance": "Boolean",
    "promptTwoFactorAuth": "Boolean",
    "refreshToken": "String",
    "sessionId": "String",
    "status": "Int",
    "tncId": "String",
    "token": "String",
    "userId": "rID",
    "userProfile": {
        "accountId": "rID",
        "address1": "String",
        "address2": "String",
        "city": "String",
        "country": "String",
        "dateOfBirth": "String",
        "firstName": "String!",
        "id": "rID!",
        "industry": "String",
        "jobTitle": "String",
        "lastName": "String!",
        "optInMarketing": "Boolean",
        "phoneNumber": "String",
        "ssn": "String",
        "state": "String",
        "twoFactorAuth": "Boolean",
        "twoFactorAuthPerDevice": "Boolean",
        "username": "String!",
        "zipCode": "String",
    },
    "userStatus": "String",
    "userUid": "String",
}

update_profile_return_fields = {"status": "Int!", "userProfile": "UserProfile!"}

cancel_order_return_fields = {"status": "String"}

confirm_order_return_fields = {
    "order": {
        "action": "String",
        "avgPrice": "Price",
        "clientOrderId": "String",
        "filled": "Int",
        "filledPercentage": "Int",
        "id": "rID",
        "insertedAt": "Int",
        "marketId": "rID",
        "orderType": "String",
        "price": "Price",
        "quantity": "Int",
        "status": "String",
        "time": "String",
        "totalValue": "Int",
    }
}

new_token_return_fields = {
    "currentLoginAt": "String",
    "deviceId": "String",
    "ipAddress": "String",
    "lastLoginAt": "String",
    "limitsNumber": {
        "accountLimits": {
            "accountId": "rID",
            "coolOffPeriod": "Int",
            "dailyDeposit": "Int",
            "hoursPerDay": "Int",
            "lifetimeDeposit": "Int",
            "lossLimit24Hours": "Int",
            "lossLimitMonthly": "Int",
            "lossLimitWeekly": "Int",
            "maxOrderLiabilityPerOrder": "Int",
            "monthlyDeposit": "Int",
            "orderLiability": "Int",
            "weeklyDeposit": "Int",
        },
        "adminLimits": {
            "coolOffPeriod": "Int",
            "dailyDeposit": "Int",
            "hoursPerDay": "Int",
            "lifetimeDeposit": "Int",
            "lossLimit24Hours": "Int",
            "lossLimitMonthly": "Int",
            "lossLimitWeekly": "Int",
            "maxOrderLiabilityPerOrder": "Int",
            "monthlyDeposit": "Int",
            "orderLiability": "Int",
            "weeklyDeposit": "Int",
        },
    },
    "promptTncAcceptance": "Boolean",
    "promptTwoFactorAuth": "Boolean",
    "refreshToken": "String",
    "sessionId": "String",
    "status": "Int",
    "tncId": "String",
    "token": "String",
    "userId": "rID",
    "userProfile": {
        "accountId": "rID",
        "address1": "String",
        "address2": "String",
        "city": "String",
        "country": "String",
        "dateOfBirth": "String",
        "firstName": "String!",
        "id": "rID!",
        "industry": "String",
        "jobTitle": "String",
        "lastName": "String!",
        "optInMarketing": "Boolean",
        "phoneNumber": "String",
        "ssn": "String",
        "state": "String",
        "twoFactorAuth": "Boolean",
        "twoFactorAuthPerDevice": "Boolean",
        "username": "String!",
        "zipCode": "String",
    },
    "userStatus": "String",
    "userUid": "String",
}

market_infos_return_fields = {
    "archived": "Boolean",
    "bids": {"price": "Int", "quantity": "Int"},
    "closedAt": "String",
    "competition": "String",
    "description": "String",
    "detailedEventBrief": "String",
    "eventBrief": "String",
    "eventId": "rID",
    "eventStart": "String",
    "eventStatus": "String",
    "eventType": "String",
    "filters": {
        "category": "String",
        "grouping": "String",
        "manual": "Boolean",
        "section": "String",
        "subcategory": "String",
    },
    "homeCategory": "String",
    "lastProbabilityAt": "DateTime",
    "lastTradedPrice": "Int",
    "manualProbability": "Boolean",
    "marketId": "rID",
    "maxPrice": "Int",
    "offers": {"price": "Int", "quantity": "Int"},
    "orderPriceRules": {"from": "Int", "inc": "Int", "to": "Int"},
    "participants": {"abbreviation": "String", "name": "String", "role": "String"},
    "position": "String",
    "price": "Float",
    "priceChange24h": "Int",
    "probability": "Float",
    "question": "String",
    "recentTrades": {
        "liquidityTaker": "String",
        "price": "Int",
        "quantity": "Int",
        "timestamp": "String",
        "timestampInt": "Int",
    },
    "result": "String",
    "rules": "String",
    "rulesSpecifier": "String",
    "shortTitle": "String",
    "specifier": "String",
    "sport": "String",
    "status": "String",
    "symbol": "String",
    "timestamp": "String",
    "timestampInt": "Int",
    "title": "String",
    "tradingFilters": {
        "category": "String",
        "grouping": "String",
        "manual": "Boolean",
        "section": "String",
        "subcategory": "String",
    },
    "volume24h": "Int",
}

user_profile_return_fields = {
    "accountId": "rID",
    "address1": "String",
    "address2": "String",
    "city": "String",
    "country": "String",
    "dateOfBirth": "String",
    "firstName": "String!",
    "id": "rID!",
    "industry": "String",
    "jobTitle": "String",
    "lastName": "String!",
    "optInMarketing": "Boolean",
    "phoneNumber": "String",
    "ssn": "String",
    "state": "String",
    "twoFactorAuth": "Boolean",
    "twoFactorAuthPerDevice": "Boolean",
    "username": "String!",
    "zipCode": "String",
}

geo_fencing_return_fields = {"expiresAt": "String", "license": "String"}
