from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Callable

from config.settings import MOOD_CHOICES, PipelineConfig
from reel.models import Act, Phrase, PhraseSet

JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)

INSTRUCTION_TEMPLATE = """\
以下は中高生向けInstagram/TikTokリール動画のためのペルソナ・トーン定義です。
このペルソナに厳密に従い、指定されたお題について「共感フック→展開→着地」の
3幕構成のナレーション用フレーズを生成してください。

# ペルソナ定義
{persona}

# お題
{topic}

# 出力ルール
- 出力はJSONオブジェクト1つのみ。説明文・コードフェンス・前置きは一切含めない
- 動画の長さは30〜60秒のナレーションを想定し、フレーズ合計は6〜9個程度
- 各フレーズは短く（目安15〜25文字）、音声で聞き取りやすい口語文にする
- act は "hook" "develop" "landing" のいずれか。hookは1〜2個、developは2〜4個、
  landingは1〜2個とし、この順序で並べる
- mood は次のいずれか一つのみ: {moods}
- 以下のJSONスキーマに厳密に従うこと:

{{
  "theme": "動画のテーマを一言で",
  "mood": "{moods_pipe}",
  "cta": "着地で促す軽いアクション（任意, 20文字以内、不要ならnull）",
  "phrases": [
    {{"act": "hook", "text": "..."}},
    {{"act": "develop", "text": "..."}},
    {{"act": "landing", "text": "..."}}
  ]
}}
"""


class PhraseValidationError(ValueError):
    pass


def load_persona_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"ペルソナマスタープロンプトが見つかりません: {path}")
    return path.read_text(encoding="utf-8")


def build_instruction(persona: str, topic: str) -> str:
    return INSTRUCTION_TEMPLATE.format(
        persona=persona,
        topic=topic,
        moods=", ".join(MOOD_CHOICES),
        moods_pipe=" | ".join(MOOD_CHOICES),
    )


def extract_json_block(raw_text: str) -> dict[str, Any]:
    match = JSON_BLOCK_RE.search(raw_text)
    if not match:
        raise PhraseValidationError(f"レスポンスからJSONを抽出できません: {raw_text[:200]!r}")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise PhraseValidationError(f"JSONのパースに失敗しました: {exc}") from exc


def validate_phrase_payload(data: dict[str, Any]) -> dict[str, Any]:
    for key in ("theme", "mood", "phrases"):
        if key not in data:
            raise PhraseValidationError(f"必須キー '{key}' がレスポンスにありません")

    if data["mood"] not in MOOD_CHOICES:
        raise PhraseValidationError(
            f"mood '{data['mood']}' は許可された値ではありません（許可値: {MOOD_CHOICES}）"
        )

    phrases = data["phrases"]
    if not isinstance(phrases, list) or not phrases:
        raise PhraseValidationError("phrases は空でないリストである必要があります")

    valid_acts = {act.value for act in Act}
    seen_acts: list[str] = []
    for item in phrases:
        if "act" not in item or "text" not in item:
            raise PhraseValidationError(f"phrase要素に act/text が不足しています: {item}")
        if item["act"] not in valid_acts:
            raise PhraseValidationError(f"不正な act 値です: {item['act']}")
        if not str(item["text"]).strip():
            raise PhraseValidationError("空のフレーズtextが含まれています")
        seen_acts.append(item["act"])

    if seen_acts != sorted(seen_acts, key=lambda a: list(Act).index(Act(a))):
        raise PhraseValidationError(
            "phrases は hook -> develop -> landing の順序である必要があります"
        )
    if seen_acts[0] != Act.HOOK.value or seen_acts[-1] != Act.LANDING.value:
        raise PhraseValidationError("先頭はhook、末尾はlandingである必要があります")

    return data


def slugify_theme(theme: str) -> str:
    ascii_slug = re.sub(r"[^a-zA-Z0-9]+", "-", theme).strip("-").lower()
    return ascii_slug[:24] if ascii_slug else "reel"


def assign_phrase_id(theme: str) -> str:
    return f"{slugify_theme(theme)}-{uuid.uuid4().hex[:6]}"


def build_phrase_set(data: dict[str, Any]) -> PhraseSet:
    phrases = [
        Phrase(act=Act(item["act"]), text=str(item["text"]).strip(), order=i)
        for i, item in enumerate(data["phrases"])
    ]
    return PhraseSet(
        phrase_id=assign_phrase_id(data["theme"]),
        theme=data["theme"],
        mood=data["mood"],
        phrases=phrases,
        cta=data.get("cta") or None,
    )


ClaudeCallFn = Callable[[str, str, str], str]


def _default_claude_call(api_key: str, model: str, instruction: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": instruction}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def generate_phrases(
    config: PipelineConfig,
    topic: str,
    claude_call: ClaudeCallFn = _default_claude_call,
) -> PhraseSet:
    persona = load_persona_prompt(Path(config.persona_prompt_path))
    instruction = build_instruction(persona, topic)
    raw_text = claude_call(config.anthropic_api_key, config.anthropic_model, instruction)
    data = extract_json_block(raw_text)
    data = validate_phrase_payload(data)
    return build_phrase_set(data)
