import os
import unittest
from unittest.mock import AsyncMock, patch

import api


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self.response = FakeResponse({
            "total_count": 1,
            "partial": False,
            "source_errors": [],
            "results": [{
                "id": "listing-123",
                "source": "kbchachacha",
                "manufacturer": "Hyundai",
                "model": "Avante",
                "year": 2022,
                "mileage_km": 50000,
                "price_krw": 12345678,
                "listing_url": "https://www.kbchachacha.com/public/car/detail.kbc?carSeq=listing-123",
                "photos": ["https://images.example.org/car.jpg"],
            }],
        })

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *args, **kwargs):
        return self.response


class VehicleSearchRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_korea_key_prioritizes_live_listings_over_monthly_summary(self):
        env = {key: value for key, value in os.environ.items() if key != "XAPIKOREA_API_KEY"}
        env["XAPIKOREA_API_KEY"] = "test-key"
        with patch.dict(os.environ, env, clear=True), \
             patch("api.fetch_korea_monthly_stats", new_callable=AsyncMock) as monthly, \
             patch("api.httpx.AsyncClient", FakeAsyncClient):
            result = await api.search_vehicles(
                country="south-korea",
                make="Hyundai",
                model="Avante",
                year_from=2020,
                year_to=2025,
                max_price=0,
                mileage_max=None,
                volume_min=None,
                volume_max=None,
                body="",
                grade="",
                lot_number="",
                limit=20,
            )

        monthly.assert_not_awaited()
        self.assertEqual(result["data_type"], "current_listings")
        self.assertEqual(result["source"], "XAPI Korea")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["model"], "Avante")
        self.assertEqual(result["results"][0]["currency"], "KRW")

    async def test_korea_without_live_key_uses_official_monthly_summary(self):
        env = {key: value for key, value in os.environ.items() if key != "XAPIKOREA_API_KEY"}
        stats = {
            "ok": True,
            "source": "Korea Automobile Auction Association",
            "source_url": "https://www.aaa-korea.com/en/data",
            "history": [{
                "year": 2026,
                "month_number": 9,
                "month": "2026-09",
                "offered": 1000,
                "sold": 700,
                "completion_rate_percent": 70,
            }],
            "disclaimer": "Monthly aggregate statistics only.",
        }
        with patch.dict(os.environ, env, clear=True), \
             patch("api.fetch_korea_monthly_stats", new_callable=AsyncMock, return_value=stats):
            result = await api.search_vehicles(
                country="south-korea",
                make="Hyundai",
                model="Avante",
                year_from=2020,
                year_to=2025,
                max_price=0,
                mileage_max=None,
                volume_min=None,
                volume_max=None,
                body="",
                grade="",
                lot_number="",
                limit=20,
            )

        self.assertEqual(result["data_type"], "source_hub")
        self.assertEqual(result["source"], "Korea Automobile Auction Association")
        self.assertEqual(result["records"], [])
        self.assertIn("official", result["message"].lower())


if __name__ == "__main__":
    unittest.main()
