import unittest
from unittest.mock import patch

import ai_generator as generator_module
from codex_prompt import (
    DOUBAO_SYSTEM_PROMPT,
    build_batch_user_prompt,
    build_doubao_batch_user_prompt,
)


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

    def test_doubao_prompt_uses_good_case_style_and_json_contract(self):
        prompt = build_doubao_batch_user_prompt(
            [
                {
                    "index": 0,
                    "level1": "★户外自主游戏",
                    "source_hint": "几个幼儿在户外玩小车。",
                    "allowed_names": ["糕糕", "阳阳"],
                    "blue_char_range": "90-120字",
                    "needs_response_care": True,
                }
            ]
        )

        self.assertIn('{"items":[{"index":0,"secondary":"...","blue":"..."}]}', prompt)
        self.assertIn("像老师记录真实发生过的小事", prompt)
        self.assertIn("通过……支持/帮助/引导婴幼儿", prompt)
        self.assertIn("不要使用“重点观察”“观察记录”“生活观察”“教学”", prompt)
        self.assertIn("不要输出“把东西放好后", prompt)
        self.assertIn("★户外自主游戏", prompt)
        self.assertIn("自主游戏时能愿意和其他小朋友尝试合作", DOUBAO_SYSTEM_PROMPT)
        self.assertIn("跟随节奏摆动身体", DOUBAO_SYSTEM_PROMPT)

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

    def test_name_pool_uses_requested_names(self):
        self.assertEqual(
            generator_module.NAMES,
            [
                "糕糕",
                "阳阳",
                "叮当",
                "圆圆",
                "诞诞",
                "又又",
                "樾樾",
                "登登",
                "加加",
                "喜悦",
                "乐诚",
                "君严",
                "汤圆",
                "yoyo",
                "期期",
                "小天",
                "大宝",
                "小宝",
            ],
        )

    def test_rejects_legacy_child_names(self):
        with patch.dict(
            generator_module.os.environ,
            {"DOCX_ARK_API_KEY": "test-key"},
            clear=False,
        ):
            generator = generator_module.ArkActivityGenerator()

        request = generator._prepare_request(
            0,
            "生活活动",
            "生活活动：幼儿喝水。",
        )

        with self.assertRaisesRegex(ValueError, "旧名字池"):
            generator._normalize_result(
                request,
                {
                    "secondary": "愿意自己拿杯喝水",
                    "blue": "贝贝拿起水杯喝了一口，又把杯子放回桌边。",
                },
            )

    def test_does_not_treat_natural_dian_dian_tou_as_child_name(self):
        with patch.dict(
            generator_module.os.environ,
            {"DOCX_ARK_API_KEY": "test-key"},
            clear=False,
        ):
            generator = generator_module.ArkActivityGenerator()

        request = generator._prepare_request(
            0,
            "生活活动",
            "生活活动：幼儿喝水。",
        )
        name = request["allowed_names"][0]
        _, blue = generator._normalize_result(
            request,
            {
                "secondary": "愿意自己拿杯喝水",
                "blue": f"{name}拿起水杯喝了一口，又把杯子放回桌边，老师点点头说放好了。",
            },
        )

        self.assertIn("点点头", blue)

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

    def test_build_ai_generator_defaults_to_ark(self):
        with patch.dict(
            generator_module.os.environ,
            {"DOCX_LLM_PROVIDER": "ark", "DOCX_LLM_FALLBACK_PROVIDER": ""},
            clear=False,
        ):
            generator = generator_module.build_ai_generator()

        self.assertIsInstance(generator, generator_module.ArkActivityGenerator)

    def test_build_ai_generator_can_switch_to_codex(self):
        with patch.dict(generator_module.os.environ, {"DOCX_LLM_PROVIDER": "codex"}, clear=False):
            generator = generator_module.build_ai_generator()

        self.assertIsInstance(generator, generator_module.CodexActivityGenerator)

    def test_build_ai_generator_can_wrap_fallback_provider(self):
        with patch.dict(
            generator_module.os.environ,
            {
                "DOCX_LLM_PROVIDER": "ark",
                "DOCX_LLM_FALLBACK_PROVIDER": "codex",
                "DOCX_ARK_API_KEY": "test-key",
            },
            clear=False,
        ):
            generator = generator_module.build_ai_generator()

        self.assertIsInstance(generator, generator_module.FallbackActivityGenerator)
        self.assertIsInstance(generator.primary, generator_module.ArkActivityGenerator)
        self.assertIsInstance(generator.fallback, generator_module.CodexActivityGenerator)

    def test_ark_batch_generate_parses_json_payload(self):
        with patch.dict(
            generator_module.os.environ,
            {
                "DOCX_ARK_API_KEY": "test-key",
                "DOCX_ARK_MODEL": "doubao-seed-2-0-lite-260215",
            },
            clear=False,
        ):
            generator = generator_module.ArkActivityGenerator()

        material = "饼干"
        name = "糕糕"

        with patch.object(generator, "_request_completion") as mocked_request:
            mocked_request.return_value = {
                "items": [
                    {
                        "index": 0,
                        "secondary": "愿意拿起点心坐下吃",
                        "blue": f"{name}洗好手后拿起{material}咬了一口，又坐回小椅子上接着吃。",
                    }
                ]
            }
            with patch.object(generator_module, "_pick_names", return_value=["糕糕", "阳阳"]):
                result = generator.batch_generate(
                    [{"level1": "加点能量", "source_text": "加点能量：先洗手，再拿起饼干坐下来吃。"}]
                )

        self.assertEqual(result[0][0], "愿意拿起点心坐下吃")
        self.assertIn("接着吃", result[0][1])

    def test_ark_preserves_natural_style_words(self):
        with patch.dict(
            generator_module.os.environ,
            {"DOCX_ARK_API_KEY": "test-key"},
            clear=False,
        ):
            generator = generator_module.ArkActivityGenerator()

        request = generator._prepare_request(
            0,
            "早操律动",
            "早操律动：幼儿跟着老师做动作。",
        )
        name = request["allowed_names"][0]
        secondary, blue = generator._normalize_result(
            request,
            {
                "secondary": "感受集体活动的快乐",
                "blue": f"{name}跟着音乐拍手、转圈，动作认真，结束后开心地给自己鼓了鼓掌。",
            },
        )

        self.assertEqual(secondary, "感受集体活动的快乐")
        self.assertIn("认真", blue)
        self.assertIn("开心", blue)

    def test_ark_rejects_template_style_output(self):
        with patch.dict(
            generator_module.os.environ,
            {"DOCX_ARK_API_KEY": "test-key"},
            clear=False,
        ):
            generator = generator_module.ArkActivityGenerator()

        request = generator._prepare_request(
            0,
            "生活活动",
            "生活活动：幼儿喝水。",
        )

        with self.assertRaisesRegex(ValueError, "模板"):
            generator._normalize_result(
                request,
                {
                    "secondary": "生活观察",
                    "blue": "糕糕把东西放好后，拿起水杯喝了一口，再继续完成接下来的动作。",
                },
            )

    def test_ark_request_completion_extracts_openai_style_content(self):
        with patch.dict(
            generator_module.os.environ,
            {"DOCX_ARK_API_KEY": "test-key"},
            clear=False,
        ):
            generator = generator_module.ArkActivityGenerator()

        response_payload = {
            "choices": [
                {
                    "message": {
                        "content": [
                            {
                                "type": "text",
                                "text": "{\"items\":[{\"index\":0,\"secondary\":\"愿意把杯子放回桌边\",\"blue\":\"乐诚拿起杯子喝了一口，又把杯子放回桌边。\"}]}",
                            }
                        ]
                    }
                }
            ]
        }

        content = generator._extract_message_content(response_payload)
        parsed = generator._parse_model_json(content)

        self.assertEqual(parsed["items"][0]["index"], 0)
        self.assertEqual(parsed["items"][0]["secondary"], "愿意把杯子放回桌边")

    def test_ark_request_uses_doubao_prompt(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return generator_module.json.dumps(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": "{\"items\":[{\"index\":0,\"secondary\":\"吃点心前能自己洗手\",\"blue\":\"糕糕洗好手后拿起饼干咬了一口，又把杯子放回桌边。\"}]}"
                                }
                            }
                        ],
                        "usage": {"total_tokens": 1},
                    },
                    ensure_ascii=False,
                ).encode("utf-8")

        captured = {}

        def fake_urlopen(req, timeout):
            captured["body"] = generator_module.json.loads(req.data.decode("utf-8"))
            return FakeResponse()

        with patch.dict(
            generator_module.os.environ,
            {"DOCX_ARK_API_KEY": "test-key"},
            clear=False,
        ):
            generator = generator_module.ArkActivityGenerator()

        prompt = build_doubao_batch_user_prompt(
            [
                {
                    "index": 0,
                    "level1": "加点能量",
                    "allowed_names": ["糕糕", "阳阳"],
                    "needs_response_care": False,
                }
            ]
        )
        with patch.object(generator_module.urllib_request, "urlopen", side_effect=fake_urlopen):
            generator._request_completion(prompt)

        self.assertEqual(captured["body"]["messages"][0]["content"], DOUBAO_SYSTEM_PROMPT)
        self.assertIn("good case", captured["body"]["messages"][0]["content"])
        self.assertIn("像老师记录真实发生过的小事", captured["body"]["messages"][1]["content"])


if __name__ == "__main__":
    unittest.main()
