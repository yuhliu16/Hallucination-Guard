from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import AIResponse, Review, Wallet, Debate

from django.contrib.auth.forms import UserCreationForm


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Wallet.objects.create(user=user)
            login(request, user)
            return redirect('airesponse_list')
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})


@login_required
def airesponse_list(request):
    ai_responses = AIResponse.objects.filter(status='open')
    return render(request, 'core/airesponse_list.html', {'ai_responses': ai_responses})

@login_required
def review_list(request):
    reviews = Review.objects.filter(status='active').exclude(reviewer=request.user).exclude(confirmed_by=request.user)
    return render(request, 'core/review_list.html', {'reviews': reviews})

@login_required
def debate_list(request):
    debates = Debate.objects.filter(resolved=False).exclude(challenger=request.user).exclude(challenged_review__reviewer=request.user)
    return render(request, 'core/debate_list.html', {'debates': debates})


@login_required
def airesponse_detail(request, pk):
    ai_response = get_object_or_404(AIResponse, pk=pk)
    return render(request, 'core/airesponse_detail.html', {'ai_response': ai_response})


@login_required
def submit_review(request, pk):
    ai_response = get_object_or_404(AIResponse, pk=pk)
    if request.method == 'POST':
        justification = request.POST['justification']
        is_hallucination = (request.POST['is_hallucination'] == 'true')
        correction = request.POST['correction']

        stake_amount = ai_response.get_first_share
        # Check wallet balance
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # Add onhold balance
        if wallet.balance < stake_amount:
            messages.error(request, 'Sorry, you do not have enough balance in your wallet to submit this review.')
            return redirect('airesponse_detail', pk)
        wallet.on_hold += stake_amount
        wallet.balance -= stake_amount
        wallet.save()

        # Create Review
        review = Review.objects.create(
            ai_response=ai_response,
            reviewer=request.user,
            justification=justification,
            correction=correction,
            is_hallucination=is_hallucination,
        )

        ai_response.status = 'reviewing'
        ai_response.save()

        messages.success(request, 'Your review has been submitted.')
        return redirect('airesponse_list')


@login_required
def review_detail(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    ai_response = review.ai_response
    if request.method == 'POST':
        is_confirmed = (request.POST['is_confirmed'] == 'true')
        wallet = Wallet.objects.get(user=request.user)
        if is_confirmed:
            review.confirmed_by.add(request.user)
            review.save()
            if wallet.balance < review.ai_response.get_confirm_share:
                messages.error(request, 'Sorry, you do not have enough balance to confirm this review.')
                return redirect('review_detail', review_id)
            wallet.on_hold += review.ai_response.get_confirm_share
            wallet.balance -= review.ai_response.get_confirm_share
            wallet.save()
            if review.confirmed_by.all().count() >= 3:
                review.settle()
        else:
            is_hallucination = (request.POST.get('is_hallucination') == 'true')
            justification = request.POST.get('justification')
            correction = request.POST['correction']
            if wallet.balance < review.get_current_pot():
                messages.error(request, 'Sorry, you do not have enough balance to confirm this review.')
                return redirect('review_detail', review_id)
            wallet.on_hold += review.get_current_pot()
            wallet.balance -= review.get_current_pot()
            wallet.save()
            debate = Debate.objects.create(
                ai_response=ai_response,
                challenged_review=review,
                challenger=request.user,
                justification=justification,
                correction=correction,
                is_hallucination=is_hallucination
            )
            review.status = 'challenged'
            review.save()

            # Mark the AIResponse as debate ongoing
            ai_response.status = 'debate_ongoing'
            ai_response.save()

        return redirect('review_list')

    return render(request, 'core/review_detail.html', {'review': review})


@login_required
def debate_detail(request, debate_id):
    debate = get_object_or_404(Debate, pk=debate_id)
    if request.method == 'POST':
        vote_reviewer = (request.POST['vote'] == '1')
        if vote_reviewer:
            debate.reviewer_vote.add(request.user)
        else:
            debate.challenger_vote.add(request.user)
        if debate.reviewer_vote.all().count() + debate.challenger_vote.all().count() >= 10:
            debate.settle()

        messages.success(request, 'Your vote has been submitted.')
        return redirect('debate_list')
    return render(request, 'core/debate_detail.html', {'debate': debate})


@login_required
def profile_view(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user)
    if request.method == 'POST':
        balance = request.POST.get('balance', 0)
        wallet.balance += int(balance)
        wallet.save()
    my_reviews = Review.objects.filter(reviewer=user).order_by('-created_at')
    my_confirmed_reviews = Review.objects.filter(confirmed_by=user).order_by('-created_at')
    my_challenged_debates = Debate.objects.filter(challenger=user).order_by('-created_at')
    my_defended_debates = Debate.objects.filter(challenged_review__reviewer=user).order_by('-created_at')

    context = {
        'wallet': wallet,
        'my_reviews': my_reviews,
        'my_confirmed_reviews': my_confirmed_reviews,
        'my_challenged_debates': my_challenged_debates,
        'my_defended_debates': my_defended_debates,
    }
    return render(request, 'core/profile.html', context)

