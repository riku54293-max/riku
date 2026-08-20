import json
import unittest
from pathlib import Path

from config.settings import PipelineConfig
from reel import phrase_generator as pg
from reel.models import Act


VALID_PAYLOAD = {
    "theme": "テスト前の焦り",
    "mood": "energetic",
    "cta": "保存してね",
    "phrases": [
        {"act": "hook", "text": "テスト前、焦ってない？"},
        {"act": "develop", "text": "一夜漬けより朝5分見直しが効く"},
        {"act": "develop", "text": "完璧よりまず1問解こう"},
        {"act": "landing", "text": "今日からできること、一つだけ"},
    ],
}


class ExtractJsonBlockTest(unittest.TestCase):
    def test_extracts_json_from_surrounding_text(self):
        raw = "はい、こちらです:\n" + json.dumps(VALID_PAYLOAD, ensure_ascii=False) + "\nよろしくお願いします"
        data = pg.extract_json_block(raw)
        self.assertEqual(data["theme"], VALID_PAYLOAD["theme"])

    def test_raises_when_no_json_present(self):
        with self.assertRaises(pg.PhraseValidationError):
            pg.extract_json_block("no json here")


class ValidatePhrasePayloadTest(unittest.TestCase):
    def test_valid_payload_passes(self):
        pg.validate_phrase_payload(VALID_PAYLOAD)

    def test_missing_key_rejected(self):
        bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "phrases"}
        with self.assertRaises(pg.PhraseValidationError):
            pg.validate_phrase_payload(bad)

    def test_invalid_mood_rejected(self):
        bad = dict(VALID_PAYLOAD, mood="angry")
        with self.assertRaises(pg.PhraseValidationError):
            pg.validate_phrase_payload(bad)

    def test_wrong_order_rejected(self):
        bad = dict(VALID_PAYLOAD, phrases=list(reversed(VALID_PAYLOAD["phrases"])))
        with self.assertRaises(pg.PhraseValidationError):
            pg.validate_phrase_payload(bad)

    def test_must_start_with_hook_end_with_landing(self):
        bad = dict(VALID_PAYLOAD, phrases=VALID_PAYLOAD["phrases"][1:])
        with self.assertRaises(pg.PhraseValidationError):
            pg.validate_phrase_payload(bad)

    def test_empty_text_rejected(self):
        phrases = [dict(p) for p in VALID_PAYLOAD["phrases"]]
        phrases[0]["text"] = "   "
        bad = dict(VALID_PAYLOAD, phrases=phrases)
        with self.assertRaises(pg.PhraseValidationError):
            pg.validate_phrase_payload(bad)


class SlugAndIdTest(unittest.TestCase):
    def test_slugify_ascii(self):
        self.assertEqual(pg.slugify_theme("Exam Stress!!"), "exam-stress")

    def test_slugify_japanese_falls_back(self):
        self.assertEqual(pg.slugify_theme("テスト前の焦り"), "reel")

    def test_phrase_id_has_expected_shape(self):
        pid = pg.assign_phrase_id("Exam Stress")
        prefix, _, suffix = pid.rpartition("-")
        self.assertEqual(prefix, "exam-stress")
        self.assertEqual(len(suffix), 6)


class BuildPhraseSetTest(unittest.TestCase):
    def test_builds_ordered_phrases(self):
        phrase_set = pg.build_phrase_set(VALID_PAYLOAD)
        self.assertEqual(phrase_set.mood, "energetic")
        self.assertEqual([p.order for p in phrase_set.phrases], [0, 1, 2, 3])
        self.assertEqual(phrase_set.phrases[0].act, Act.HOOK)
        self.assertEqual(phrase_set.phrases[-1].act, Act.LANDING)
        self.assertEqual(phrase_set.cta, "保存してね")


class GeneratePhrasesTest(unittest.TestCase):
    def test_generate_phrases_uses_injected_claude_call(self):
        config = PipelineConfig(
            persona_prompt_path=Path("config/SNS運用マスタープロンプト.md"),
            anthropic_api_key="dummy",
        )
        captured = {}

        def fake_claude_call(api_key, model, instruction):
            captured["api_key"] = api_key
            captured["model"] = model
            captured["instruction"] = instruction
            return json.dumps(VALID_PAYLOAD, ensure_ascii=False)

        phrase_set = pg.generate_phrases(config, "テスト前の焦り", claude_call=fake_claude_call)
        self.assertEqual(phrase_set.theme, VALID_PAYLOAD["theme"])
        self.assertEqual(captured["api_key"], "dummy")
        self.assertIn("テスト前の焦り", captured["instruction"])
        self.assertIn("energetic", captured["instruction"])


if __name__ == "__main__":
    unittest.main()
