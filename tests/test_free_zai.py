import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import api

class FreeZaiTests(unittest.IsolatedAsyncioTestCase):
    async def test_paid_model_setting_uses_free_model(self):
        response = MagicMock(status_code=200)
        response.json.return_value = {'choices': [{'message': {'content': '{"recommendations":[{"make":"Toyota","model":"Prius"}]}'}}]}
        client = AsyncMock()
        client.post.return_value = response
        with patch.dict(os.environ, {'ZAI_API_KEY': 'test-only', 'ZAI_MODEL': 'glm-4.6'}), patch('api.httpx.AsyncClient') as factory:
            factory.return_value.__aenter__.return_value = client
            result = await api.assistant_select(api.VehicleSelectionInput(message='Toyota Prius для города'))
        self.assertEqual(client.post.call_args.kwargs['json']['model'], 'glm-4.5-flash')
        self.assertEqual(result['processing_mode'], 'zai_glm')

    async def test_no_key_never_calls_provider(self):
        with patch.dict(os.environ, {'ZAI_API_KEY': '', 'ZAI_API_TOKEN': ''}), patch('api.httpx.AsyncClient') as factory:
            result = await api.assistant_select(api.VehicleSelectionInput(message='Toyota Prius для города'))
        factory.assert_not_called()
        self.assertEqual(result['processing_mode'], 'local_free')
