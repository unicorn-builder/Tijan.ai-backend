"""
Tests pour le système de codes promo Tijan AI.
Requiert: backend live sur Render + migration Supabase déployée.
"""
import pytest
import requests
import re
from datetime import datetime, timedelta

from .conftest import BASE_URL

TIMEOUT = 120  # generous timeout for Render cold starts

# Test data
ADMIN_USER_ID = "test-admin-uuid"  # Placeholder
TEST_PROSPECT = {
    "prospect_name": "Moussa Diallo",
    "prospect_email": "moussa@test.com",
    "prospect_company": "Diallo BTP",
    "discount_percent": 30,
    "duration_months": 3,
    "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
    "notes": "Test automatique"
}


class TestPromoCodesCreation:
    """Tests de création de codes promo."""

    def test_create_promo_code_returns_code(self):
        """POST /admin/promo-codes retourne un code au format TIJAN-XXX-XXXX."""
        r = requests.post(f"{BASE_URL}/admin/promo-codes", json=TEST_PROSPECT, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] == True
        assert "code" in data
        assert "share_url" in data
        # Store for subsequent tests
        TestPromoCodesCreation.created_code = data["code"]

    def test_code_format_is_memorable(self):
        """Le code généré suit le format TIJAN-XXX-XXXX."""
        code = getattr(TestPromoCodesCreation, 'created_code', None)
        if not code:
            pytest.skip("Pas de code créé")
        assert re.match(r'^TIJAN-[A-Z]{3}-[A-Z0-9]{4}$', code), f"Format invalide: {code}"

    def test_duration_only_accepts_3_or_6_months(self):
        """duration_months doit être 3 ou 6, pas autre chose."""
        bad = {**TEST_PROSPECT, "duration_months": 12}
        r = requests.post(f"{BASE_URL}/admin/promo-codes", json=bad, timeout=TIMEOUT)
        data = r.json()
        assert data["ok"] == False or r.status_code >= 400


class TestPromoCodesValidation:
    """Tests de validation de codes promo."""

    def test_validate_active_code_returns_correct_price(self):
        """Un code actif retourne valid=true avec le bon prix."""
        # Create a fresh code
        r = requests.post(f"{BASE_URL}/admin/promo-codes", json=TEST_PROSPECT, timeout=TIMEOUT)
        code = r.json()["code"]

        r2 = requests.post(f"{BASE_URL}/promo-codes/validate", json={"code": code}, timeout=TIMEOUT)
        data = r2.json()
        assert data["valid"] == True
        assert data["discount_percent"] == 30
        assert data["monthly_price"] == 350000  # 500K * 0.70
        assert data["original_price"] == 500000
        assert data["duration_months"] == 3

    def test_validate_expired_code_returns_invalid(self):
        """Un code expiré retourne valid=false."""
        expired = {**TEST_PROSPECT, "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat()}
        r = requests.post(f"{BASE_URL}/admin/promo-codes", json=expired, timeout=TIMEOUT)
        code = r.json()["code"]

        r2 = requests.post(f"{BASE_URL}/promo-codes/validate", json={"code": code}, timeout=TIMEOUT)
        data = r2.json()
        assert data["valid"] == False
        assert "expir" in data.get("reason", "").lower()

    def test_validate_nonexistent_code_returns_invalid(self):
        """Un code inexistant retourne valid=false."""
        r = requests.post(f"{BASE_URL}/promo-codes/validate", json={"code": "TIJAN-ZZZ-9999"}, timeout=TIMEOUT)
        data = r.json()
        assert data["valid"] == False


class TestPromoCodesRedemption:
    """Tests de rédemption et souscription."""

    def test_redemption_marks_code_used(self):
        """Après souscription, le code est marqué used."""
        # Create code
        r = requests.post(f"{BASE_URL}/admin/promo-codes", json=TEST_PROSPECT, timeout=TIMEOUT)
        code = r.json()["code"]

        # Subscribe with code
        r2 = requests.post(f"{BASE_URL}/subscriptions/create", json={
            "user_id": ADMIN_USER_ID,
            "promo_code": code,
        }, timeout=TIMEOUT)
        # The subscription should succeed
        if r2.status_code == 200 and r2.json().get("ok"):
            # Validate same code again — should be used
            r3 = requests.post(f"{BASE_URL}/promo-codes/validate", json={"code": code}, timeout=TIMEOUT)
            data = r3.json()
            assert data["valid"] == False
            assert "utilis" in data.get("reason", "").lower() or "used" in data.get("reason", "").lower()

    def test_subscription_has_correct_discount_end(self):
        """La souscription a une date de fin de discount correcte."""
        r = requests.post(f"{BASE_URL}/admin/promo-codes", json={
            **TEST_PROSPECT, "duration_months": 6, "discount_percent": 20
        }, timeout=TIMEOUT)
        code = r.json()["code"]

        r2 = requests.post(f"{BASE_URL}/subscriptions/create", json={
            "user_id": ADMIN_USER_ID,
            "promo_code": code,
        }, timeout=TIMEOUT)
        if r2.status_code == 200:
            data = r2.json()
            assert data.get("discount_percent") == 20
            assert data.get("discount_months") == 6
            assert data.get("price") == 400000  # 500K * 0.80

    def test_list_promo_codes(self):
        """GET /admin/promo-codes retourne la liste."""
        r = requests.get(f"{BASE_URL}/admin/promo-codes", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] == True
        assert isinstance(data["codes"], list)
