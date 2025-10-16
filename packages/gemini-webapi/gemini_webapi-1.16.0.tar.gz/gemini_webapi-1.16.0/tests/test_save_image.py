import os
import unittest
import logging

from httpx import HTTPError

from gemini_webapi import GeminiClient, AuthError, set_log_level, logger

logging.getLogger("asyncio").setLevel(logging.ERROR)
set_log_level("DEBUG")


class TestGeminiClient(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.geminiclient = GeminiClient(
            os.getenv("SECURE_1PSID"), os.getenv("SECURE_1PSIDTS")
        )

        try:
            await self.geminiclient.init(auto_refresh=False)
        except AuthError:
            self.skipTest("Test was skipped due to invalid cookies")

    async def test_save_web_image(self):
        response = await self.geminiclient.generate_content(
            "Show me some pictures of random subjects"
        )
        self.assertTrue(response.images)
        for image in response.images:
            try:
                await image.save(verbose=True, skip_invalid_filename=True)
            except HTTPError as e:
                logger.warning(e)

    async def test_save_generated_image(self):
        response = await self.geminiclient.generate_content(
            "Generate a picture of random subjects"
        )
        self.assertTrue(response.images)
        for image in response.images:
            await image.save(verbose=True, full_size=True)

    async def test_save_image_to_image(self):
        response = await self.geminiclient.generate_content(
            "Design an application icon based on the provided image. Make it simple and modern.",
            files=["assets/banner.png"],
        )
        self.assertTrue(response.images)
        for image in response.images:
            await image.save(verbose=True, full_size=True)


if __name__ == "__main__":
    unittest.main()
