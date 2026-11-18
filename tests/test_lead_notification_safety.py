"""Regression checks for saved PapAuto leads when Telegram delivery is uncertain.

These tests are entirely offline; no leads or Telegram messages are created.
"""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import api


class LeadNotificationSafetyTests(unittest.TestCase):
    def test_saved_lead_with_telegram_failure_is_accepted_not_reposted(self):
        message = "Заявка сохранена, но Telegram не подтвердил доставку."
        with patch("api._record_telegram_failure") as mark:
            response = api._accepted_without_telegram(
                "postgresql://not-used", "test-lead-uuid", "telegram_network_unconfirmed", message
            )
        self.assertEqual(response.status_code, 202)
        body = json.loads(response.body)
        self.assertTrue(body["ok"])
        self.assertTrue(body["stored"])
        self.assertFalse(body["notified"])
        self.assertEqual(body["message"], message)
        mark.assert_called_once_with(
            "postgresql://not-used", "test-lead-uuid", "telegram_network_unconfirmed"
        )

    def test_survey_phone_validation_disallows_telegram_username(self):
        for phone in ("+7 913 123-45-67", "89131234567", "9131234567"):
            self.assertTrue(api._survey_contact_is_phone(phone), phone)
        for bad_contact in ("@username", "telegram_user", "12345",
                            "+7 abc 9131234567", "call me"):
            self.assertFalse(api._survey_contact_is_phone(bad_contact), bad_contact)

    def test_invalid_survey_contact_is_rejected_before_neon(self):
        import asyncio
        invalid = api.Lead(
            contact="@username",
            request="Подбор автомобиля через PapAuto (SurveyJS)\\nМодель: Honda Fit",
            consent=True,
        )
        with patch("api.psycopg.connect") as connect:
            with self.assertRaises(api.HTTPException) as error:
                asyncio.run(api.create_lead(invalid))
            self.assertEqual(error.exception.status_code, 422)
            connect.assert_not_called()

    def test_form_does_not_offer_duplicate_submit_after_confirmed_storage(self):
        app_js = (Path(__file__).resolve().parents[1] / "app.js").read_text(encoding="utf-8")
        self.assertIn('send.textContent=data.notified===false?"Заявка сохранена":"Заявка отправлена"', app_js)
        self.assertIn('if(data.notified===false)', app_js)
        self.assertIn('return;}window.dispatchEvent', app_js)


if __name__ == "__main__":
    unittest.main()
