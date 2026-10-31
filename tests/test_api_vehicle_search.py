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
    async def test_korea_uses_only_public_monthly_summary_even_when_paid_key_exists(self):
        stats = {
            "ok": True,
            "source": "Korea Automobile Auction Association",
            "source_url": "https://www.aaa-korea.com/en/data",
            "history": [{"month": "2026-09", "offered": 1000, "sold": 700, "completion_rate_percent": 70}],
            "disclaimer": "Monthly aggregate statistics only.",
        }
        with patch.dict(os.environ, {"XAPIKOREA_API_KEY": "unused-test-key"}, clear=False), \
             patch("api.fetch_korea_monthly_stats", new_callable=AsyncMock, return_value=stats) as monthly, \
             patch("api.httpx.AsyncClient") as client:
            result = await api.search_vehicles(country="south-korea", make="Hyundai", model="Avante")
        monthly.assert_awaited_once()
        client.assert_not_called()
        self.assertEqual(result["data_type"], "source_hub")
        self.assertEqual(result["records"], [])
        self.assertIn("статистика", result["message"].lower())

    async def test_korea_falls_back_to_free_encar_source_without_paid_api(self):
        with patch.dict(os.environ, {"XAPIKOREA_API_KEY": "unused-test-key"}, clear=False), \
             patch("api.fetch_korea_monthly_stats", new_callable=AsyncMock, return_value={"ok": False, "message": "offline"}), \
             patch("api.httpx.AsyncClient") as client:
            result = await api.search_vehicles(country="south-korea", make="Hyundai", model="Avante")
        client.assert_not_called()
        self.assertEqual(result["data_type"], "source_hub")
        self.assertTrue(any("Encar" in item["name"] for item in result["sources"]))

    async def test_china_search_does_not_call_metered_ttpai_api(self):
        with patch("api.fetch_ttpai_model_stats", new_callable=AsyncMock) as ttpai:
            result = await api.search_vehicles(country="china", make="BYD", model="Song")
        ttpai.assert_not_awaited()
        self.assertEqual(result["data_type"], "source_hub")
        self.assertTrue(result["sources"])

    async def test_china_auction_statistics_does_not_call_metered_ttpai_api(self):
        with patch("api.fetch_ttpai_model_stats", new_callable=AsyncMock) as ttpai:
            result = await api.auction_statistics(country="china", make="BYD", model="Song")
        ttpai.assert_not_awaited()
        self.assertEqual(result["data_type"], "source_hub")
        self.assertTrue(result["sources"])


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
    async def test_natural_language_request_is_parsed_locally_without_gemini(self):
        with patch("api.search_vehicles", new_callable=AsyncMock, return_value={
            "ok": True, "country": "japan", "data_type": "external_search",
            "search_links": [{"name": "Archive", "url": "https://example.org"}]
        }) as search, patch("api.httpx.AsyncClient") as client:
            result = await api.assistant_search_vehicles(
                api.VehicleSearchAssistantInput(
                    message="Нужен Toyota RAV4 2020–2023, пробег до 80 тысяч, кроссовер, полный привод, не вариатор",
                    country="japan", city="Новосибирск",
                )
            )
        client.assert_not_called()
        self.assertEqual(result["processing_mode"], "local_free")
        self.assertEqual(result["filters"]["make"], "Toyota")
        self.assertEqual(result["filters"]["model"], "RAV4")
        self.assertEqual(result["filters"]["year_from"], 2020)
        self.assertEqual(result["filters"]["year_to"], 2023)
        self.assertEqual(result["filters"]["mileage_max"], 80000)
        self.assertEqual(result["filters"]["body"], "SUV")
        self.assertIn("полный привод", result["preferences_not_applied"])
        self.assertIn("не вариатор", result["preferences_not_applied"])
        search.assert_awaited_once()

    async def test_natural_language_search_rejects_invalid_volume_range(self):
        with patch("api.search_vehicles", new_callable=AsyncMock) as search, patch("api.httpx.AsyncClient") as client:
            with self.assertRaises(api.HTTPException) as ctx:
                await api.assistant_search_vehicles(
                    api.VehicleSearchAssistantInput(message="Toyota RAV4 объём от 2.5 до 1.5 литра", country="japan")
                )
        self.assertEqual(ctx.exception.status_code, 422)
        client.assert_not_called()
        search.assert_not_awaited()


class FreeModeSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_customs_calculator_never_calls_tks_even_if_old_key_exists(self):
        payload = api.CustomsRequest(
            cost=1500000, volume=1800, power=120, currency="392",
            engine_type="petrol", age="35", face="nat"
        )
        with patch.dict(os.environ, {"TKS_AUTO_API_KEY": "a" * 32}, clear=False), \\
             patch("api.httpx.AsyncClient") as client:
            with self.assertRaises(api.HTTPException) as ctx:
                await api.calculate_customs(payload)
        self.assertEqual(ctx.exception.status_code, 503)
        client.assert_not_called()


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
