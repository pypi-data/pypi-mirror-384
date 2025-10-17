from django.contrib import admin
from django.contrib.admin import ModelAdmin

from wise_market.models import (
    ExchangeMarketPairBinding,
    NetworkSymbolBinding,
    Symbol,
    Network,
)


@admin.register(Network)
class NetworkAdmin(admin.ModelAdmin):
    search_fields = ["slug"]
    list_display = ["slug", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    search_fields = ["slug"]
    list_display = ["slug", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(NetworkSymbolBinding)
class NetworkSymbolBindingAdmin(admin.ModelAdmin):
    search_fields = ["network__slug", "symbol__slug", "contract_address"]
    list_display = [
        "network",
        "symbol",
        "contract_address",
        "updated_at",
        "type",
        "is_active",
    ]
    list_filter = ["type", "is_active", "network"]
    readonly_fields = ["created_at", "updated_at", "symbol"]


@admin.register(ExchangeMarketPairBinding)
class ExchangeMarketPairBindingAdmin(ModelAdmin):
    list_display = [
        "exchange_market",
        "pair",
        "min_notional",
        "quantity_step_size",
        "updated_at",
    ]
