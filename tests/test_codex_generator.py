import unittest
from unittest.mock import patch

import ai_generator as generator_module
from codex_prompt import build_batch_user_prompt


class CodexPromptTests(unittest.TestCase):
    def setUp(self):
        generator_module.RECENT_LLM_SECONDARIES.clear()
        generator_module.RECENT_LLM_BLUE_SNIPPETS.clear()

    def test_batch_prompt_requires_secondary_then_blue(self):
        prompt = build_batch_user_prompt(
            [
                {
                    "index": 0,
                    "level1": "加点能量",
                    "source_hint": "先洗手，再坐下来吃点心。",
                    "secondary_char_range": "6-20字，20字以内优先",
                    "blue_char_range": "30-45字",
                    "needs_response_care": False,
                }
            ]
        )

        self.assertIn("先根据 `level1` 和 `source_hint` 提炼 `secondary`", prompt)
        self.assertIn("再根据 `secondary` 展开 `blue`", prompt)

    def test_prepare_request_uses_source_hint_by_default(self):
        generator = generator_module.CodexActivityGenerator()
        request = generator._prepare_request(
            0,
            "加点能量",
            "加点能量：吃点心前先去洗手。阳阳咬了一口后说“不吃了”。",
        )

        self.assertEqual(request["clean_level1"], "加点能量")
        self.assertIn("吃点心前先去洗手", request["source_hint"])
        self.assertTrue(request["allowed_names"])

    def test_batch_generate_uses_batch_path(self):
        generator = generator_module.CodexActivityGenerator()

        def fake_generate_chunk(chunk):
            results = []
            for request in chunk:
                results.append(
                    (
                        "愿意自己拿好点心",
                        f"{request['allowed_names'][0]}拿起{request['material']['items'][0]}，又坐下来接着吃。",
                    )
                )
            return results

        with patch.object(generator, "_generate_chunk", side_effect=fake_generate_chunk):
            result = generator.batch_generate(
                [{"level1": "加点能量", "source_text": "加点能量：先洗手再吃点心。"}]
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "愿意自己拿好点心")
        self.assertIn("接着吃", result[0][1])


if __name__ == "__main__":
    unittest.main()
