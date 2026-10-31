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
                "engine_displacement_cc": 1591,
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
        self.assertEqual(result["record_type"], "current_listing")
        self.assertEqual(result["source"], "XAPI Korea")
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["model"], "Avante")
        self.assertEqual(result["results"][0]["currency"], "KRW")


    async def test_korea_applies_lot_and_engine_volume_filters(self):
        env = {key: value for key, value in os.environ.items() if key != "XAPIKOREA_API_KEY"}
        env["XAPIKOREA_API_KEY"] = "test-key"
        with patch.dict(os.environ, env, clear=True), patch("api.fetch_korea_monthly_stats", new_callable=AsyncMock) as monthly, patch("api.httpx.AsyncClient", FakeAsyncClient):
            result = await api.search_vehicles(
                country="south-korea", make="Hyundai", model="Avante",
                year_from=2020, year_to=2025, max_price=1500000,
                mileage_max=None, volume_min=1500, volume_max=1700,
                body="", grade="", lot_number="listing-123", limit=20,
            )
        monthly.assert_not_awaited()
        self.assertEqual(result["returned_count"], 1)
        self.assertEqual(result["results"][0]["volume_cc"], 1591)
        self.assertEqual(result["filters_applied"]["lot_number"], "listing-123")
        self.assertEqual(result["filters_applied"]["volume_min"], 1500)

    async def test_korea_excludes_unknown_engine_volume_when_volume_filter_is_requested(self):
        env = {key: value for key, value in os.environ.items() if key != "XAPIKOREA_API_KEY"}
        env["XAPIKOREA_API_KEY"] = "test-key"
        fake = FakeAsyncClient()
        fake.response._payload["results"][0].pop("engine_displacement_cc", None)
        with patch.dict(os.environ, env, clear=True), patch("api.fetch_korea_monthly_stats", new_callable=AsyncMock), patch("api.httpx.AsyncClient", return_value=fake):
            result = await api.search_vehicles(
                country="south-korea", make="Hyundai", model="Avante",
                year_from=2020, year_to=2025, max_price=0,
                mileage_max=None, volume_min=1500, volume_max=None,
                body="", grade="", lot_number="", limit=20,
            )
        self.assertEqual(result["returned_count"], 0)
        self.assertEqual(result["results"], [])

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
        self.assertIn("статистика", result["message"].lower())


class FakeGeminiResponse:
    status_code = 200

    def json(self):
        import json
        return {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "reply": "Нашёл параметры Toyota RAV4.",
                            "filters": {
                                "make": "Toyota", "model": "RAV4",
                                "year_from": 2020, "year_to": 2023,
                                "mileage_max": 80000, "volume_min": None,
                                "volume_max": None, "body": "SUV",
                                "grade": "", "lot_number": ""
                            },
                            "preferences_not_applied": ["полный привод", "не вариатор"]
                        }, ensure_ascii=False)
                    }]
                }
            }]
        }


class FakeGeminiClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        return FakeGeminiResponse()


class VehicleAssistantSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_natural_language_request_becomes_filters_and_calls_market_source(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False), \
             patch("api.httpx.AsyncClient", FakeGeminiClient), \
             patch("api.search_vehicles", new_callable=AsyncMock, return_value={
                 "ok": True, "country": "japan", "data_type": "external_search",
                 "search_links": [{"name": "Archive", "url": "https://example.org"}]
             }) as search:
            result = await api.assistant_search_vehicles(
                api.VehicleSearchAssistantInput(
                    message="Нужен Toyota RAV4 2020–2023, пробег до 80 тысяч, полный привод, не вариатор",
                    country="japan",
                    city="Новосибирск",
                )
            )

        self.assertEqual(result["filters"]["make"], "Toyota")
        self.assertEqual(result["filters"]["model"], "RAV4")
        self.assertEqual(result["filters"]["year_from"], 2020)
        self.assertEqual(result["filters"]["year_to"], 2023)
        self.assertEqual(result["filters"]["mileage_max"], 80000)
        self.assertEqual(result["preferences_not_applied"], ["полный привод", "не вариатор"])
        search.assert_awaited_once()
        self.assertEqual(search.await_args.kwargs["country"], "japan")

    async def test_natural_language_search_rejects_invalid_volume_range(self):
        class InvalidVolumeResponse(FakeGeminiResponse):
            def json(self):
                import json
                return {
                    "candidates": [{
                        "content": {
                            "parts": [{
                                "text": json.dumps({
                                    "reply": "Параметры распознаны.",
                                    "filters": {
                                        "make": "Toyota", "model": "RAV4",
                                        "year_from": 2020, "year_to": 2023,
                                        "volume_min": 2500, "volume_max": 1500
                                    },
                                    "preferences_not_applied": []
                                }, ensure_ascii=False)
                            }]
                        }
                    }]
                }

        class InvalidVolumeClient(FakeGeminiClient):
            async def post(self, *args, **kwargs):
                return InvalidVolumeResponse()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False), \
             patch("api.httpx.AsyncClient", InvalidVolumeClient), \
             patch("api.search_vehicles", new_callable=AsyncMock) as search:
            with self.assertRaises(api.HTTPException) as ctx:
                await api.assistant_search_vehicles(
                    api.VehicleSearchAssistantInput(message="Toyota RAV4", country="japan")
                )
        self.assertEqual(ctx.exception.status_code, 422)
        search.assert_not_awaited()


class JapanChassisSearchTests(unittest.IsolatedAsyncioTestCase):
    async def test_japan_chassis_search_normalizes_and_returns_free_match_summary(self):
        class JPResponse:
            status_code = 200
            def json(self):
                return {"ok": True, "found": True, "credits_left": 96, "matches": [{
                    "ref": "ref-123", "match": "exact", "make": "TOYOTA",
                    "model": "COROLLA AXIO", "year": "2008", "engine_cc": "1500",
                    "grade": "X", "transmission": "AT", "color": "SILVER",
                    "result": "sold", "start_price": "80,000 YEN", "photos": 6
                }]}
        class JPClient:
            def __init__(self, *args, **kwargs): pass
            async def __aenter__(self): return self
            async def __aexit__(self, *args): return False
            async def get(self, url, **kwargs): return JPResponse()
        with patch.dict(os.environ, {"JPSHEET_API_KEY": "jp-test-key"}, clear=False), \
             patch("api.httpx.AsyncClient", JPClient):
            result = await api.search_japan_auction_history(api.JapanChassisSearchInput(chassis="nze141-1234567"))
        self.assertEqual(result["chassis"], "NZE141-1234567")
        self.assertTrue(result["found"])
        self.assertEqual(result["matches"][0]["result"], "sold")
        self.assertEqual(result["matches"][0]["photos_count"], 6)
        self.assertEqual(result["credits_left"], 96)

    async def test_japan_chassis_search_requires_provider_key(self):
        env = {key: value for key, value in os.environ.items() if key != "JPSHEET_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(api.HTTPException) as ctx:
                await api.search_japan_auction_history(api.JapanChassisSearchInput(chassis="NZE141-1234567"))
        self.assertEqual(ctx.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
