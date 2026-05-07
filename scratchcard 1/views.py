from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
import uuid
from .models import ScratchCard, ScratchCardBatch, ScratchCardRedemption
from students.models import Student

@login_required
def scratch_card_list(request):
    batches = ScratchCardBatch.objects.all()
    cards = ScratchCard.objects.select_related('batch', 'redeemed_by').all()
    
    status_filter = request.GET.get('status')
    if status_filter:
        cards = cards.filter(status=status_filter)
    
    batch_filter = request.GET.get('batch')
    if batch_filter:
        cards = cards.filter(batch_id=batch_filter)
    
    context = {
        'batches': batches,
        'cards': cards,
        'status_filter': status_filter,
        'batch_filter': batch_filter,
    }
    return render(request, 'scratchcard/card_list.html', context)

@login_required
def create_scratch_batch(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        quantity = int(request.POST.get('quantity', 0))
        value_per_card = request.POST.get('value_per_card')
        purpose = request.POST.get('purpose')
        
        batch = ScratchCardBatch.objects.create(
            name=name,
            description=description,
            quantity=quantity,
            value_per_card=value_per_card,
            purpose=purpose,
            created_by=request.user.username
        )
        
        import random
        import string
        
        for _ in range(quantity):
            card_code = 'SC' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            pin = ''.join(random.choices(string.digits, k=8))
            
            ScratchCard.objects.create(
                batch=batch,
                card_code=card_code,
                pin=pin,
                value=value_per_card
            )
        
        messages.success(request, f'Scratch card batch "{name}" created with {quantity} cards!')
        return redirect('scratchcard:card_list')
    
    return render(request, 'scratchcard/create_batch.html')

@login_required
def redeem_scratch_card(request):
    if request.method == 'POST':
        card_code = request.POST.get('card_code', '').strip()
        pin = request.POST.get('pin', '').strip()
        
        card = get_object_or_404(ScratchCard, card_code=card_code)
        
        if not card.is_valid():
            messages.error(request, 'This card is no longer valid or has been redeemed.')
            return redirect('scratchcard:redeem')
        
        if card.pin != pin:
            messages.error(request, 'Invalid PIN. Please check and try again.')
            return redirect('scratchcard:redeem')
        
        try:
            student = request.user.student
        except Student.DoesNotExist:
            messages.error(request, 'Only students can redeem scratch cards.')
            return redirect('scratchcard:redeem')
        
        card.status = 'redeemed'
        card.redeemed_by = student
        card.redeemed_at = timezone.now()
        card.save()
        
        reference_number = 'REF' + str(uuid.uuid4())[:8].upper()
        ScratchCardRedemption.objects.create(
            card=card,
            student=student,
            amount_redeemed=card.value,
            reference_number=reference_number
        )
        
        messages.success(request, f'Scratch card redeemed successfully! Reference: {reference_number}')
        return redirect('scratchcard:redemption_receipt', ref_number=reference_number)
    
    return render(request, 'scratchcard/redeem.html')

@login_required
def redemption_receipt(request, ref_number):
    redemption = get_object_or_404(ScratchCardRedemption, reference_number=ref_number)
    context = {'redemption': redemption}
    return render(request, 'scratchcard/receipt.html', context)

@login_required
def batch_list(request):
    batches = ScratchCardBatch.objects.all()
    context = {'batches': batches}
    return render(request, 'scratchcard/batch_list.html', context)

@login_required
def batch_detail(request, batch_id):
    batch = get_object_or_404(ScratchCardBatch, id=batch_id)
    cards = batch.cards.all()
    
    stats = {
        'total': cards.count(),
        'active': cards.filter(status='active').count(),
        'redeemed': cards.filter(status='redeemed').count(),
        'expired': cards.filter(status='expired').count(),
    }
    
    context = {'batch': batch, 'cards': cards, 'stats': stats}
    return render(request, 'scratchcard/batch_detail.html', context)

@login_required
@require_POST
def export_cards_csv(request, batch_id):
    from django.http import HttpResponse
    import csv
    
    batch = get_object_or_404(ScratchCardBatch, id=batch_id)
    cards = batch.cards.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="scratch_cards_{batch.id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Card Code', 'PIN', 'Value', 'Status', 'Expiry Date'])
    
    for card in cards:
        writer.writerow([
            card.card_code,
            card.pin,
            card.value,
            card.status,
            card.expiry_date or 'N/A'
        ])
    
    return response
