import tempfile
import unittest
import wave
from pathlib import Path

from config.settings import PipelineConfig
from reel import voice_synth as vs
from reel.models import Act, Phrase, PhraseSet

FRAMERATE = 16000


def write_silent_wav(path: Path, duration_sec: float) -> None:
    n_frames = int(duration_sec * FRAMERATE)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(FRAMERATE)
        wf.writeframes(b"\x00\x00" * n_frames)


class ComputeTimingTest(unittest.TestCase):
    def test_cumulative_with_gap(self):
        timings = vs.compute_timing([1.0, 2.0, 0.5], gap=0.2)
        expected = [(0.0, 1.0), (1.2, 3.2), (3.4, 3.9)]
        for (start, end), (exp_start, exp_end) in zip(timings, expected):
            self.assertAlmostEqual(start, exp_start, places=6)
            self.assertAlmostEqual(end, exp_end, places=6)

    def test_empty_durations(self):
        self.assertEqual(vs.compute_timing([], gap=0.3), [])


class WaveDurationTest(unittest.TestCase):
    def test_reads_duration_within_tolerance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.wav"
            write_silent_wav(path, 1.5)
            self.assertAlmostEqual(vs.wave_duration_sec(path), 1.5, places=2)


class ConcatWavsWithGapsTest(unittest.TestCase):
    def test_concatenates_and_inserts_silence(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = []
            for i, dur in enumerate([1.0, 1.0]):
                p = tmp_path / f"seg{i}.wav"
                write_silent_wav(p, dur)
                paths.append(p)

            out_path = tmp_path / "out.wav"
            total = vs.concat_wavs_with_gaps(paths, gap=0.5, out_path=out_path)
            self.assertAlmostEqual(total, 2.5, places=2)

    def test_rejects_empty_list(self):
        with self.assertRaises(ValueError):
            vs.concat_wavs_with_gaps([], gap=0.3, out_path=Path("/tmp/x.wav"))


class SynthesizeNarrationTest(unittest.TestCase):
    def test_builds_timed_phrases_with_fake_synth(self):
        phrase_set = PhraseSet(
            phrase_id="test-abc123",
            theme="テスト",
            mood="calm",
            phrases=[
                Phrase(act=Act.HOOK, text="つかみ", order=0),
                Phrase(act=Act.DEVELOP, text="展開", order=1),
                Phrase(act=Act.LANDING, text="着地", order=2),
            ],
        )
        config = PipelineConfig(phrase_gap_sec=0.3)

        durations = {"つかみ": 1.0, "展開": 1.5, "着地": 0.8}

        def fake_synth_fn(text, out_path, cfg):
            write_silent_wav(out_path, durations[text])

        with tempfile.TemporaryDirectory() as tmp:
            result = vs.synthesize_narration(
                phrase_set, config, Path(tmp), synth_fn=fake_synth_fn
            )

            self.assertEqual(len(result.timed_phrases), 3)
            self.assertAlmostEqual(result.timed_phrases[0].start, 0.0, places=2)
            self.assertAlmostEqual(result.timed_phrases[0].end, 1.0, places=2)
            self.assertAlmostEqual(result.timed_phrases[1].start, 1.3, places=2)
            self.assertAlmostEqual(result.timed_phrases[2].start, 3.1, places=2)
            self.assertTrue(Path(result.concatenated_audio_path).exists())
            self.assertAlmostEqual(result.total_duration, 3.9, places=2)


if __name__ == "__main__":
    unittest.main()
