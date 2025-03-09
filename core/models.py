from django.db import models
from django.contrib.auth.models import User


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    on_hold = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    def __str__(self):
        return f"{self.user.username}'s Wallet"


class AIResponse(models.Model):
    question = models.TextField()
    answer = models.TextField()
    model = models.CharField(max_length=250, null=True, blank=False)
    stake_amount = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # "open", "resolved", or "debate_ongoing"
    status = models.CharField(
        max_length=20,
        default='open',
        choices=(
            ('open', 'Open'),
            ('reviewing', 'Reviewing'),
            ('debate_ongoing', 'Debate Ongoing'),
            ('resolved', 'Resolved')
        )
    )

    @property
    def get_first_share(self):
        return int(self.stake_amount / 2)

    @property
    def get_confirm_share(self):
        return int(self.stake_amount / 6)

    def __str__(self):
        return f"AIResponse #{self.id} by {self.model}"


class Review(models.Model):
    ai_response = models.ForeignKey(AIResponse, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    justification = models.TextField()
    is_hallucination = models.BooleanField()
    correction = models.TextField()
    confirmed_by = models.ManyToManyField(User, related_name='confirmed_reviews')
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        default='active',
        choices=(
            ('active', 'Active'),
            ('challenged', 'Challenged'),
            ('resolved', 'Resolved')
        )
    )

    def get_current_pot(self):
        confirmed_by_plus_self = self.confirmed_by.all().count() + 1
        return int(self.ai_response.get_first_share + self.ai_response.stake_amount / 6 * confirmed_by_plus_self)

    def get_current_pot(self):
        confirmed_by = self.confirmed_by.all().count()
        return int(self.ai_response.get_first_share + self.ai_response.stake_amount / 6 * confirmed_by)
    
    def settle(self):
        reviewer_wallet = Wallet.objects.get(user=self.reviewer)
        reviewer_wallet.on_hold -= self.ai_response.get_first_share
        reviewer_wallet.balance += 2 * self.ai_response.get_first_share
        reviewer_wallet.save()
        for confirmed_user in self.confirmed_by.all():
            wallet = Wallet.objects.get(user=confirmed_user)
            wallet.on_hold -= self.ai_response.get_confirm_share
            wallet.balance += 2 * self.ai_response.get_confirm_share
            wallet.save()

        self.status = 'resolved'
        self.save()

        self.ai_response.status = 'resolved'
        self.ai_response.save()

    def __str__(self):
        return f"Review #{self.id} by {self.reviewer.username}"


class Debate(models.Model):
    ai_response = models.ForeignKey(AIResponse, on_delete=models.CASCADE, related_name='debates')
    challenged_review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='debates')
    challenger = models.ForeignKey(User, on_delete=models.CASCADE)
    justification = models.TextField()
    is_hallucination = models.BooleanField(null=False, default=False)
    correction = models.TextField()

    challenger_vote = models.ManyToManyField(User, related_name='challenger_vote')
    reviewer_vote = models.ManyToManyField(User, related_name='reviewer_vote')
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def challenger_vote_count(self):
        return self.challenger_vote.all().count()

    def reviewer_vote_count(self):
        return self.reviewer_vote.all().count()

    def settle(self):
        if self.challenger_vote_count() > self.reviewer_vote_count():
            # Challenger Win.
            challenger_wallet = Wallet.objects.get(user=self.challenger)
            challenger_wallet.on_hold -= self.challenged_review.get_current_pot()
            challenger_wallet.balance += 2 * self.challenged_review.get_current_pot()
            challenger_wallet.save()

            reviewer_wallet = Wallet.objects.get(user=self.challenged_review.reviewer)
            reviewer_wallet.on_hold -= self.ai_response.get_first_share
            reviewer_wallet.save()

            for user in self.challenged_review.confirmed_by.all():
                wallet = Wallet.objects.get(user=user)
                wallet.on_hold -= self.ai_response.get_confirm_share
                wallet.save()

            self.ai_response.status = 'open'
            self.ai_response.save()

            self.challenged_review.status = 'resolved'
            self.challenged_review.save()
        else:
            # Reviewer Win.
            challenger_wallet = Wallet.objects.get(user=self.challenger)
            challenger_wallet.on_hold -= self.challenged_review.get_current_pot()
            challenger_wallet.save()

            reviewer_wallet = Wallet.objects.get(user=self.challenged_review.reviewer)
            reviewer_wallet.balance += self.ai_response.get_first_share
            reviewer_wallet.save()
            for user in self.challenged_review.confirmed_by.all():
                wallet = Wallet.objects.get(user=user)
                wallet.balance += self.ai_response.get_confirm_share
                wallet.save()

            self.challenged_review.status = 'active'
            self.challenged_review.save()

            self.ai_response.status = 'reviewing'
            self.ai_response.save()

        self.resolved = True
        self.save()


    def __str__(self):
        return f"Debate #{self.id} on Review #{self.challenged_review.id}"