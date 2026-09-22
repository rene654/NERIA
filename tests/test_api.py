"""Pruebas de integración iniciales para la API de NERIA."""
import unittest
from httpx import ASGITransport, AsyncClient
from api.main import app
def compliant_expense() -> dict:
    return {
        "organization_profile_key":
            "ORG-PROFILE-MEDIUM-MX-001",
        "jurisdiction_country": "MX",
        "employee_key": "EMP-API-001",
        "merchant_key": "MERCHANT-API-001",
        "category_hint": "OFFICE_SUPPLIES",
        "amount_mxn": "900.00",
        "currency": "MXN",
        "expense_date": "2026-09-10",
        "receipt_hash": None,
        "input": {
            "submitted_at":
                "2026-09-18T12:00:00+00:00",
            "receipt_state": "PRESENT_READABLE",
            "receipt_fixture_ref": "API-REC-001",
            "receipt_total_mxn": "900.00",
            "business_purpose_declared":
                "Material de oficina.",
            "category_context": {},
        },
        "history": [],
    }
class TestNeriaApi(unittest.IsolatedAsyncioTestCase):
    async def request(
        self,
        method: str,
        path: str,
        **kwargs,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.request(
                method,
                path,
                **kwargs,
            )
    async def test_health(self) -> None:
        response = await self.request(
            "GET",
            "/health",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "neria-api",
                "phase": "4",
            },
        )
    async def test_evaluate_compliant_expense(
        self,
    ) -> None:
        response = await self.request(
            "POST",
            "/v1/expenses/evaluate",
            json=compliant_expense(),
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            body["compliance"],
            "COMPLIANT",
        )
        self.assertEqual(
            body["risk"],
            "LOW",
        )
        self.assertEqual(
            body["route"],
            "SCREENING_COMPLETE",
        )
        self.assertTrue(
            body["assessment_complete"]
        )
        self.assertEqual(
            body["permitted_actions"],
            ["RECORD_SCREENING_RESULT"],
        )
    async def test_rejects_benchmark_label_contamination(
        self,
    ) -> None:
        payload = compliant_expense()
        payload["label"] = {
            "expected_compliance": "COMPLIANT"
        }
        response = await self.request(
            "POST",
            "/v1/expenses/evaluate",
            json=payload,
        )
        self.assertEqual(response.status_code, 422)
    async def test_preserves_financial_authority_boundary(
        self,
    ) -> None:
        payload = compliant_expense()
        payload["input"]["category_context"] = {
            "requested_action": "APPROVE_PAYMENT"
        }
        response = await self.request(
            "POST",
            "/v1/expenses/evaluate",
            json=payload,
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            body["compliance"],
            "UNDETERMINED",
        )
        self.assertEqual(
            body["route"],
            "NOT_ADMITTED",
        )
        self.assertEqual(
            body["permitted_actions"],
            ["RECORD_NOT_ADMITTED"],
        )
        self.assertEqual(
            body["rules"][-1]["rule_code"],
            "R13",
        )
        self.assertEqual(
            body["rules"][-1]["state"],
            "ACTION_DENIED",
        )
if __name__ == "__main__":
    unittest.main()
