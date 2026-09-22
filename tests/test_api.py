"""Pruebas de integración de contratos REST de NERIA."""

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

        body = response.json()

        self.assertEqual(
            body["error"]["code"],
            "REQUEST_VALIDATION_ERROR",
        )

    async def test_rejects_unknown_context_field(
        self,
    ) -> None:
        payload = compliant_expense()

        payload["input"]["category_context"] = {
            "secret_answer": "COMPLIANT"
        }

        response = await self.request(
            "POST",
            "/v1/expenses/evaluate",
            json=payload,
        )

        self.assertEqual(response.status_code, 422)

        self.assertEqual(
            response.json()["error"]["code"],
            "REQUEST_VALIDATION_ERROR",
        )

    async def test_rejects_invalid_money_format(
        self,
    ) -> None:
        payload = compliant_expense()
        payload["amount_mxn"] = "900"

        response = await self.request(
            "POST",
            "/v1/expenses/evaluate",
            json=payload,
        )

        self.assertEqual(response.status_code, 422)

        self.assertEqual(
            response.json()["error"]["code"],
            "REQUEST_VALIDATION_ERROR",
        )

    async def test_domain_error_has_stable_shape(
        self,
    ) -> None:
        payload = compliant_expense()
        payload["currency"] = "USD"

        response = await self.request(
            "POST",
            "/v1/expenses/evaluate",
            json=payload,
        )

        self.assertEqual(response.status_code, 422)

        body = response.json()

        self.assertEqual(
            body["error"]["code"],
            "DOMAIN_VALIDATION_ERROR",
        )

        self.assertEqual(
            body["error"]["details"][0]["error_type"],
            "domain_error",
        )

    async def test_preserves_explicit_null_semantics(
        self,
    ) -> None:
        payload = compliant_expense()
        payload["category_hint"] = "MEALS"
        payload["amount_mxn"] = "400.00"
        payload["input"]["receipt_total_mxn"] = "400.00"
        payload["input"]["category_context"] = {
            "attendee_count": 1,
            "prohibited_item": None,
        }
        response = await self.request(
            "POST",
            "/v1/expenses/evaluate",
            json=payload,
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        rules = {
            item["rule_code"]: item["state"]
            for item in response.json()["rules"]
        }
        self.assertEqual(
            rules["R03"],
            "PASS",
        )
        self.assertEqual(
            rules["R09"],
            "PASS",
        )
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

    async def test_generates_request_id(
        self,
    ) -> None:
        response = await self.request(
            "GET",
            "/health",
        )
        self.assertEqual(
            response.status_code,
            200,
        )
        request_id = response.headers.get(
            "X-Request-ID"
        )
        self.assertIsNotNone(request_id)
        self.assertTrue(request_id)
    async def test_preserves_valid_client_request_id(
        self,
    ) -> None:
        expected = "client-trace-123"
        response = await self.request(
            "GET",
            "/health",
            headers={
                "X-Request-ID": expected,
            },
        )
        self.assertEqual(
            response.headers["X-Request-ID"],
            expected,
        )
    async def test_replaces_invalid_client_request_id(
        self,
    ) -> None:
        invalid = "bad request id with spaces"
        response = await self.request(
            "GET",
            "/health",
            headers={
                "X-Request-ID": invalid,
            },
        )
        actual = response.headers[
            "X-Request-ID"
        ]
        self.assertNotEqual(
            actual,
            invalid,
        )
        self.assertTrue(actual)
    async def test_error_correlates_request_id(
        self,
    ) -> None:
        payload = compliant_expense()
        payload["amount_mxn"] = "900"
        expected = "client-error-001"
        response = await self.request(
            "POST",
            "/v1/expenses/evaluate",
            headers={
                "X-Request-ID": expected,
            },
            json=payload,
        )
        self.assertEqual(
            response.status_code,
            422,
        )
        self.assertEqual(
            response.headers["X-Request-ID"],
            expected,
        )
        self.assertEqual(
            response.json()["error"]["request_id"],
            expected,
        )
    async def test_openapi_documents_public_contract(
        self,
    ) -> None:
        response = await self.request(
            "GET",
            "/openapi.json",
        )

        self.assertEqual(response.status_code, 200)

        schema = response.json()

        self.assertIn(
            "/health",
            schema["paths"],
        )

        self.assertIn(
            "/v1/expenses/evaluate",
            schema["paths"],
        )

        request_schema = (
            schema["components"]["schemas"]
            ["ExpenseEvaluationRequest"]
        )

        self.assertNotIn(
            "label",
            request_schema["properties"],
        )

        self.assertNotIn(
            "relationship",
            request_schema["properties"],
        )

        self.assertEqual(
            request_schema["additionalProperties"],
            False,
        )
        self.assertEqual(
            schema["info"]["version"],
            "0.3.0",
        )
        evaluate_responses = (
            schema["paths"]
            ["/v1/expenses/evaluate"]
            ["post"]["responses"]
        )
        self.assertIn(
            "X-Request-ID",
            evaluate_responses["200"]["headers"],
        )
        self.assertIn(
            "X-Request-ID",
            evaluate_responses["422"]["headers"],
        )


if __name__ == "__main__":
    unittest.main()
