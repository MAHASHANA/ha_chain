"""Factory-boy factories for all ha_chain models."""

import json
import uuid
from datetime import datetime, timedelta, timezone

import factory

from app.enums import (
    TransferStatus, DeliveryMethod, MobileMoneyProvider, KYCLevel,
    AgentStatus, EscrowStatus, ComplianceAction, CorridorStatus,
    InvestmentStatus,
)
from app.models.models import (
    User, Agent, Transfer, Corridor, TokenizedAsset, Investment,
    ComplianceCheck, Dispute, SanctionsList,
)


def generate_uuid():
    return str(uuid.uuid4())


class UserFactory(factory.Factory):
    """Factory for creating User instances."""

    class Meta:
        model = User

    id = factory.LazyFunction(generate_uuid)
    email = factory.Sequence(lambda n: f"user{n}@hachain.io")
    phone = factory.Sequence(lambda n: f"+1555000{n:04d}")
    hashed_password = "hashed_test_password_placeholder"
    full_name = factory.Sequence(lambda n: f"Test User {n}")
    country = "USA"
    kyc_level = KYCLevel.BASIC.value
    wallet_address = factory.LazyFunction(
        lambda: f"G{'A' * 55}"[:56]
    )
    wallet_balance_usdc = 10000.0
    is_active = True
    is_sanctioned = False
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class SenderFactory(UserFactory):
    """Sender user with funds."""
    country = "USA"
    kyc_level = KYCLevel.ENHANCED.value
    wallet_balance_usdc = 10000.0


class ReceiverUserFactory(UserFactory):
    """A receiver who is also a platform user."""
    country = "SOM"
    kyc_level = KYCLevel.BASIC.value
    wallet_balance_usdc = 0.0


class AgentFactory(factory.Factory):
    """Factory for creating Agent instances."""

    class Meta:
        model = Agent

    id = factory.LazyFunction(generate_uuid)
    user_id = factory.LazyFunction(generate_uuid)
    city = "Hargeisa"
    country = "SOM"
    status = AgentStatus.ACTIVE.value
    is_online = True
    delivery_methods = json.dumps([
        DeliveryMethod.CASH_PICKUP.value,
        DeliveryMethod.MOBILE_MONEY.value,
    ])
    supported_providers = json.dumps([
        MobileMoneyProvider.ZAAD.value,
        MobileMoneyProvider.EDAHAB.value,
    ])
    rating = 4.8
    total_transactions = 150
    successful_transactions = 147
    success_rate = 0.98
    avg_delivery_minutes = 25.0
    stake_amount_usdc = 5000.0
    daily_volume_usdc = 0.0
    daily_limit_usdc = 10000.0
    commission_rate = 0.005
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class HargeisaAgentFactory(AgentFactory):
    """Agent based in Hargeisa, Somalia."""
    city = "Hargeisa"
    country = "SOM"
    delivery_methods = json.dumps([
        DeliveryMethod.CASH_PICKUP.value,
        DeliveryMethod.MOBILE_MONEY.value,
    ])
    supported_providers = json.dumps([
        MobileMoneyProvider.ZAAD.value,
        MobileMoneyProvider.EDAHAB.value,
    ])


class MumbaiAgentFactory(AgentFactory):
    """Agent based in Mumbai, India."""
    city = "Mumbai"
    country = "IND"
    delivery_methods = json.dumps([
        DeliveryMethod.MOBILE_MONEY.value,
        DeliveryMethod.BANK_TRANSFER.value,
    ])
    supported_providers = json.dumps([
        MobileMoneyProvider.UPI.value,
    ])
    rating = 4.6
    avg_delivery_minutes = 15.0
    commission_rate = 0.004


class MexicoCityAgentFactory(AgentFactory):
    """Agent based in Mexico City, Mexico."""
    city = "Mexico City"
    country = "MEX"
    delivery_methods = json.dumps([
        DeliveryMethod.MOBILE_MONEY.value,
        DeliveryMethod.BANK_TRANSFER.value,
    ])
    supported_providers = json.dumps([
        MobileMoneyProvider.SPEI.value,
    ])
    rating = 4.7
    avg_delivery_minutes = 10.0
    commission_rate = 0.003


class ManilaAgentFactory(AgentFactory):
    """Agent based in Manila, Philippines."""
    city = "Manila"
    country = "PHL"
    delivery_methods = json.dumps([
        DeliveryMethod.MOBILE_MONEY.value,
        DeliveryMethod.CASH_PICKUP.value,
    ])
    supported_providers = json.dumps([
        MobileMoneyProvider.GCASH.value,
    ])
    rating = 4.5
    avg_delivery_minutes = 20.0
    commission_rate = 0.004


class CorridorFactory(factory.Factory):
    """Factory for creating Corridor instances."""

    class Meta:
        model = Corridor

    id = factory.LazyFunction(generate_uuid)
    source_country = "USA"
    destination_country = "SOM"
    source_currency = "USD"
    destination_currency = "SOS"
    base_fee_percent = 1.5
    flat_fee_usd = 0.50
    minimum_fee_usd = 2.0
    min_transfer_usd = 5.0
    max_transfer_usd = 10000.0
    exchange_rate = 571.50
    exchange_rate_markup = 0.01
    risk_score = 6
    status = CorridorStatus.ACTIVE.value
    supported_delivery_methods = json.dumps([
        DeliveryMethod.CASH_PICKUP.value,
        DeliveryMethod.MOBILE_MONEY.value,
    ])
    supported_providers = json.dumps([
        MobileMoneyProvider.ZAAD.value,
        MobileMoneyProvider.EDAHAB.value,
    ])
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class USAToSomaliaCorridorFactory(CorridorFactory):
    """USA to Somalia corridor."""
    source_country = "USA"
    destination_country = "SOM"
    source_currency = "USD"
    destination_currency = "SOS"
    base_fee_percent = 1.5
    flat_fee_usd = 0.50
    exchange_rate = 571.50
    risk_score = 6


class USAToIndiaCorridorFactory(CorridorFactory):
    """USA to India corridor (high volume = lower fee)."""
    source_country = "USA"
    destination_country = "IND"
    source_currency = "USD"
    destination_currency = "INR"
    base_fee_percent = 1.0
    flat_fee_usd = 0.0
    minimum_fee_usd = 1.50
    exchange_rate = 83.25
    risk_score = 3
    supported_delivery_methods = json.dumps([
        DeliveryMethod.MOBILE_MONEY.value,
        DeliveryMethod.BANK_TRANSFER.value,
    ])
    supported_providers = json.dumps([
        MobileMoneyProvider.UPI.value,
    ])


class USAToMexicoCorridorFactory(CorridorFactory):
    """USA to Mexico corridor (highest volume = lowest fee)."""
    source_country = "USA"
    destination_country = "MEX"
    source_currency = "USD"
    destination_currency = "MXN"
    base_fee_percent = 0.8
    flat_fee_usd = 0.0
    minimum_fee_usd = 1.00
    exchange_rate = 17.15
    risk_score = 2
    supported_delivery_methods = json.dumps([
        DeliveryMethod.MOBILE_MONEY.value,
        DeliveryMethod.BANK_TRANSFER.value,
    ])
    supported_providers = json.dumps([
        MobileMoneyProvider.SPEI.value,
    ])


class USAToPhilippinesCorridorFactory(CorridorFactory):
    """USA to Philippines corridor."""
    source_country = "USA"
    destination_country = "PHL"
    source_currency = "USD"
    destination_currency = "PHP"
    base_fee_percent = 1.2
    flat_fee_usd = 0.25
    minimum_fee_usd = 1.50
    exchange_rate = 56.20
    risk_score = 3
    supported_delivery_methods = json.dumps([
        DeliveryMethod.MOBILE_MONEY.value,
        DeliveryMethod.CASH_PICKUP.value,
    ])
    supported_providers = json.dumps([
        MobileMoneyProvider.GCASH.value,
    ])


class TransferFactory(factory.Factory):
    """Factory for creating Transfer instances."""

    class Meta:
        model = Transfer

    id = factory.LazyFunction(generate_uuid)
    sender_id = factory.LazyFunction(generate_uuid)
    agent_id = None
    corridor_id = factory.LazyFunction(generate_uuid)
    status = TransferStatus.QUOTED.value
    send_amount_usd = 500.0
    fee_usd = 8.0
    total_debit_usd = 508.0
    exchange_rate = 565.785
    receive_amount_local = 282892.5
    agent_commission_usd = 0.0
    receiver_name = "Abdi Mohamed"
    receiver_phone = "+252634001234"
    receiver_city = "Hargeisa"
    receiver_country = "SOM"
    delivery_method = DeliveryMethod.CASH_PICKUP.value
    mobile_money_provider = None
    pickup_code = "ABC123"
    escrow_tx_hash = None
    escrow_status = EscrowStatus.PENDING.value
    release_tx_hash = None
    compliance_status = ComplianceAction.APPROVED.value
    compliance_notes = None
    sender_rating = None
    agent_rating = None
    quote_expires_at = factory.LazyFunction(
        lambda: datetime.now(timezone.utc) + timedelta(minutes=15)
    )
    initiated_at = None
    matched_at = None
    accepted_at = None
    delivered_at = None
    completed_at = None
    cancelled_at = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
    updated_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class TokenizedAssetFactory(factory.Factory):
    """Factory for creating TokenizedAsset instances."""

    class Meta:
        model = TokenizedAsset

    id = factory.LazyFunction(generate_uuid)
    name = "Somali Sukuk Bond"
    symbol = factory.Sequence(lambda n: f"SSB{n}")
    asset_type = "sukuk"
    total_supply = 1000000.0
    price_per_token_usd = 100.0
    annual_yield_percent = 5.0
    issuer = "Somali Development Fund"
    stellar_asset_code = factory.Sequence(lambda n: f"SSB{n}")
    stellar_issuer = "GBBD47IF6LWK7P7MDEVSCWR7DPUWV3NY3DTQEVFL4NAT4AQH3ZLLFLA5"
    is_active = True
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class InvestmentFactory(factory.Factory):
    """Factory for creating Investment instances."""

    class Meta:
        model = Investment

    id = factory.LazyFunction(generate_uuid)
    user_id = factory.LazyFunction(generate_uuid)
    asset_id = factory.LazyFunction(generate_uuid)
    quantity = 10.0
    purchase_price_usd = 1000.0
    current_value_usd = 1000.0
    status = InvestmentStatus.ACTIVE.value
    purchase_tx_hash = None
    sale_tx_hash = None
    sold_at = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class ComplianceCheckFactory(factory.Factory):
    """Factory for creating ComplianceCheck instances."""

    class Meta:
        model = ComplianceCheck

    id = factory.LazyFunction(generate_uuid)
    transfer_id = factory.LazyFunction(generate_uuid)
    check_type = "sanctions"
    result = ComplianceAction.APPROVED.value
    details = "No matches found"
    risk_score = 0
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class SanctionsListFactory(factory.Factory):
    """Factory for creating SanctionsList entries."""

    class Meta:
        model = SanctionsList

    id = factory.LazyFunction(generate_uuid)
    full_name = "BLOCKED PERSON"
    aliases = "alias1;alias2"
    country = "IRN"
    source = "OFAC"
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))


class DisputeFactory(factory.Factory):
    """Factory for creating Dispute instances."""

    class Meta:
        model = Dispute

    id = factory.LazyFunction(generate_uuid)
    transfer_id = factory.LazyFunction(generate_uuid)
    opened_by = factory.LazyFunction(generate_uuid)
    reason = "Receiver claims money was not delivered"
    status = "open"
    resolution_notes = None
    resolved_at = None
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc))
