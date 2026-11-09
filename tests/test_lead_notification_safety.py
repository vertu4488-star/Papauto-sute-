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

    def test_form_does_not_offer_duplicate_submit_after_confirmed_storage(self):
        app_js = (Path(__file__).resolve().parents[1] / "app.js").read_text(encoding="utf-8")
        self.assertIn('send.textContent=data.notified===false?"Заявка сохранена":"Заявка отправлена"', app_js)
        self.assertIn('if(data.notified===false)', app_js)
        self.assertIn('return;}window.dispatchEvent', app_js)


if __name__ == "__main__":
    unittest.main()
