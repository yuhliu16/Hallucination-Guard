from django.contrib import admin
from .models import Wallet, AIResponse, Review, Debate


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance', 'on_hold')


@admin.register(AIResponse)
class AIResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'model', 'stake_amount', 'status', 'created_at')
    list_filter = ('status', 'model')
    search_fields = ('question', 'answer')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'ai_response', 'reviewer', 'is_hallucination', 'status', 'created_at')
    list_filter = ('status', 'is_hallucination')
    search_fields = ('ai_response__question', 'justification')


@admin.register(Debate)
class DebateAdmin(admin.ModelAdmin):
    list_display = ('id', 'ai_response', 'challenged_review', 'challenger', 'resolved', 'created_at')
    list_filter = ('resolved', 'created_at')
