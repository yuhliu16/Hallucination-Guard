import os
import django
import random
from decimal import Decimal

# Point to your Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hallucination_guard.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import AIResponse, Wallet, Debate, Review

User.objects.all().exclude(username='admin').delete()
AIResponse.objects.all().delete()
Review.objects.all().delete()
Debate.objects.all().delete()

def run():
    # 1) Create 20 users with wallets
    for i in range(1, 21):
        username = f"user{i}"
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password("Nit014316")  # or any default password
            user.save()
            print(f"Created user: {username}")
        # Create or get the wallet
        wallet, w_created = Wallet.objects.get_or_create(user=user)
        if w_created:
            # Give them some random balance
            wallet.balance = Decimal(random.randint(10, 100))
            wallet.save()
            print(f"  -> Added wallet with balance {wallet.balance}")

    # 2) Create some fake AI responses
    #    We'll define some sample questions and answers; feel free to expand
    sample_questions = [
        "What is the best programming language?",
        "Explain quantum computing in simple terms.",
        "What year was the Magna Carta signed?",
        "How do I bake a chocolate cake?",
        "What is the capital of France?",
        "Who wrote 'To Kill a Mockingbird'?"
    ]
    sample_answers = [
        "The best programming language is subjective, but many prefer Python.",
        "Quantum computing uses qubits that can be in superpositions.",
        "The Magna Carta was signed in 1215, but let's say 1220 for confusion.",
        "Chocolate cake can be baked by mixing flour, sugar, eggs, cocoa powder, and baking at 350F.",
        "Paris is the capital of France, or so they say.",
        "Harper Lee wrote 'To Kill a Mockingbird'."
    ]
    sample_models = [
        "OpenAI GPT-4", "Google Bard", "Meta LLaMA", "Anthropic Claude", "Microsoft Bing"
    ]

    # We'll create e.g. 30 AI responses with random staker, random question, answer, stake
    for _ in range(30):
        question = random.choice(sample_questions)
        answer = random.choice(sample_answers)
        model_name = random.choice(sample_models)
        stake_amount = Decimal(random.randint(10, 50))

        ai_response = AIResponse.objects.create(
            question=question,
            answer=answer,
            model=model_name,
            stake_amount=stake_amount,
            status='open'  # default
        )
        print(f"Created AIResponse #{ai_response.id}: {model_name} / {question} (stake {stake_amount})")




if __name__ == '__main__':
    run()
