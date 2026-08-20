from __future__ import annotations

from pathlib import Path

from config.settings import PipelineConfig
from reel.bgm_selector import compute_ducking_envelope, make_gain_function
from reel.models import BGMSelection, NarrationResult, PhraseSet

TELOP_FONT_SIZE = 64
TELOP_MARGIN_BOTTOM_RATIO = 0.22


def plan_background_segments(image_paths: list[str], total_duration: float) -> list[tuple[str, float]]:
    if not image_paths:
        raise ValueError("背景画像が1枚も指定されていません")
    if total_duration <= 0:
        raise ValueError("total_duration は正の値である必要があります")

    n = len(image_paths)
    base = total_duration / n
    segments = [(path, base) for path in image_paths]
    return segments


def output_file_path(output_dir: Path, date_str: str, phrase_id: str) -> Path:
    return Path(output_dir) / f"{date_str}_{phrase_id}.mp4"


def _load_font(font_path: str | None, size: int) -> "ImageFont.FreeTypeFont":
    from PIL import ImageFont

    if font_path:
        return ImageFont.truetype(font_path, size)
    for candidate in (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
    ):
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def render_text_image(
    text: str,
    canvas_size: tuple[int, int],
    font_path: str | None = None,
    font_size: int = TELOP_FONT_SIZE,
    fill: tuple[int, int, int, int] = (255, 255, 255, 255),
    stroke_fill: tuple[int, int, int, int] = (0, 0, 0, 255),
    stroke_width: int = 6,
) -> "Image.Image":
    from PIL import Image, ImageDraw

    width, height = canvas_size
    font = _load_font(font_path, font_size)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]

    x = (width - text_w) / 2 - bbox[0]
    y = height - int(height * TELOP_MARGIN_BOTTOM_RATIO) - text_h / 2 - bbox[1]

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_fill=stroke_fill,
        stroke_width=stroke_width,
    )
    return img


def build_ken_burns_clip(image_path: str, duration: float, size: tuple[int, int], zoom: float):
    from moviepy.editor import ImageClip

    width, height = size
    clip = ImageClip(image_path).set_duration(duration)

    scale_to_cover = max(width / clip.w, height / clip.h) * zoom
    clip = clip.resize(scale_to_cover)

    def zoom_factor(t: float) -> float:
        progress = t / duration if duration > 0 else 0
        return 1.0 + (zoom - 1.0) * 0.15 * progress

    clip = clip.resize(zoom_factor).set_position(("center", "center"))
    return clip


def build_telop_clip(text: str, start: float, end: float, size: tuple[int, int], config: PipelineConfig):
    import numpy as np
    from moviepy.editor import ImageClip
    from moviepy.video.fx.fadein import fadein
    from moviepy.video.fx.fadeout import fadeout

    duration = max(0.05, end - start)
    img = render_text_image(text, size, font_path=config.font_path)
    clip = (
        ImageClip(np.array(img))
        .set_start(start)
        .set_duration(duration)
        .fx(fadein, config.telop_fade_sec)
        .fx(fadeout, min(config.telop_fade_sec, duration / 2))
    )
    return clip


def build_ducked_bgm_clip(bgm: BGMSelection, narration_duration: float, config: PipelineConfig, narration_windows: list[tuple[float, float]]):
    import numpy as np
    from moviepy.editor import AudioFileClip, afx

    bgm_clip = AudioFileClip(bgm.path)
    target_duration = narration_duration + config.bgm_duck_fade_sec

    if bgm_clip.duration < target_duration:
        bgm_clip = bgm_clip.fx(afx.audio_loop, duration=target_duration)
    else:
        bgm_clip = bgm_clip.subclip(0, target_duration)

    envelope = compute_ducking_envelope(
        bgm_duration=target_duration,
        narration_windows=narration_windows,
        normal_gain=config.bgm_normal_gain,
        duck_gain=config.bgm_duck_gain,
        fade=config.bgm_duck_fade_sec,
    )
    gain_fn = make_gain_function(envelope)

    def apply_gain(get_frame, t):
        frame = get_frame(t)
        if np.isscalar(t):
            return frame * gain_fn(t)
        gains = np.array([gain_fn(tt) for tt in t])
        return (frame.T * gains).T

    return bgm_clip.fl(apply_gain)


def compose_reel(
    phrase_set: PhraseSet,
    narration: NarrationResult,
    bgm: BGMSelection,
    background_image_paths: list[str],
    config: PipelineConfig,
    date_str: str,
) -> Path:
    from moviepy.editor import CompositeAudioClip, CompositeVideoClip, AudioFileClip, concatenate_videoclips

    total_duration = narration.total_duration
    segments = plan_background_segments(background_image_paths, total_duration)

    bg_clips = [
        build_ken_burns_clip(path, seg_duration, config.video_size, config.ken_burns_zoom)
        for path, seg_duration in segments
    ]
    background = concatenate_videoclips(bg_clips, method="compose").set_duration(total_duration)

    telop_clips = [
        build_telop_clip(tp.phrase.text, tp.start, tp.end, config.video_size, config)
        for tp in narration.timed_phrases
    ]

    video = CompositeVideoClip([background, *telop_clips], size=config.video_size).set_duration(total_duration)

    narration_audio = AudioFileClip(narration.concatenated_audio_path)
    narration_windows = [(tp.start, tp.end) for tp in narration.timed_phrases]
    bgm_audio = build_ducked_bgm_clip(bgm, total_duration, config, narration_windows)

    final_audio = CompositeAudioClip([bgm_audio.set_start(0), narration_audio.set_start(0)]).set_duration(total_duration)
    video = video.set_audio(final_audio)

    out_path = output_file_path(config.output_dir, date_str, phrase_set.phrase_id)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    video.write_videofile(
        str(out_path),
        fps=config.fps,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium",
    )
    return out_path
