"""
LEGACY Payment Processor
========================
Dit bestand ziet eruit als oude, ongebruikte code maar wordt
WEL actief gebruikt via een import in book_manager.py (_initiate_payment_hold).

Oorspronkelijk geschreven door de eerste developer voor een prototype
betaalsysteem. Nu gebruikt als payment hold mechanisme.

DO NOT DELETE - still in use! (maar deze comment is ergens in het verleden
verwijderd en later weer toegevoegd door een andere freelancer)
"""
import os
import hashlib
from datetime import datetime


# Payment status tracking - module level state
_payment_holds = {}
_processed_payments = []


class PaymentError(Exception):
    """Custom exception voor payment errors"""
    pass


def _get_api_key():
    """Haal payment API key op uit environment"""
    key = os.environ.get('PAYMENT_API_KEY', '')
    if not key:
        # Fallback voor development
        return 'pk_test_dummy123'
    return key


def _generate_reference(reservation_id, amount):
    """Genereer unieke payment reference"""
    data = f"{reservation_id}-{amount}-{datetime.now().isoformat()}"
    return f"PAY-{hashlib.md5(data.encode()).hexdigest()[:12].upper()}"


def process_hold(reservation_id, amount):
    """
    Plaats een payment hold voor een reservering.
    In productie zou dit een externe payment provider aanroepen.
    Voor development simuleert dit het proces.

    Returns:
        dict met reference en status, of None bij falen
    """
    if amount <= 0:
        return None

    api_key = _get_api_key()
    if not api_key:
        return None

    reference = _generate_reference(reservation_id, amount)

    # Simuleer payment hold
    hold = {
        'reference': reference,
        'reservation_id': reservation_id,
        'amount': amount,
        'status': 'held',
        'created_at': datetime.now(),
        'api_key_prefix': api_key[:7]  # Log alleen prefix voor debugging
    }

    _payment_holds[reference] = hold

    return {
        'reference': reference,
        'status': 'held',
        'amount': amount
    }


def release_hold(reference):
    """Geef een payment hold vrij (bij annulering)"""
    if reference not in _payment_holds:
        return False

    hold = _payment_holds[reference]
    hold['status'] = 'released'
    hold['released_at'] = datetime.now()

    return True


def capture_payment(reference):
    """
    Capture een eerder geplaatste hold (bij bevestiging).
    Maakt de betaling definitief.
    """
    if reference not in _payment_holds:
        raise PaymentError(f"Hold not found: {reference}")

    hold = _payment_holds[reference]
    if hold['status'] != 'held':
        raise PaymentError(f"Hold is not in held status: {hold['status']}")

    hold['status'] = 'captured'
    hold['captured_at'] = datetime.now()

    _processed_payments.append({
        'reference': reference,
        'amount': hold['amount'],
        'reservation_id': hold['reservation_id'],
        'captured_at': hold['captured_at']
    })

    return True


def get_hold_status(reference):
    """Check de status van een payment hold"""
    hold = _payment_holds.get(reference)
    if not hold:
        return None
    return {
        'reference': hold['reference'],
        'status': hold['status'],
        'amount': hold['amount']
    }


def get_payment_summary():
    """Overzicht van alle betalingen - voor admin dashboard"""
    total_held = sum(h['amount'] for h in _payment_holds.values()
                     if h['status'] == 'held')
    total_captured = sum(p['amount'] for p in _processed_payments)

    return {
        'active_holds': len([h for h in _payment_holds.values()
                            if h['status'] == 'held']),
        'total_held_amount': total_held,
        'total_captured': len(_processed_payments),
        'total_captured_amount': total_captured
    }
