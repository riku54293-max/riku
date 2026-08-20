import random
import tempfile
import unittest
from pathlib import Path

from reel import bgm_selector as bs


class ListBgmCandidatesTest(unittest.TestCase):
    def test_lists_only_audio_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            mood_dir = Path(tmp) / "energetic"
            mood_dir.mkdir()
            (mood_dir / "a.mp3").touch()
            (mood_dir / "b.wav").touch()
            (mood_dir / "readme.txt").touch()

            candidates = bs.list_bgm_candidates(Path(tmp), "energetic")
            names = sorted(p.name for p in candidates)
            self.assertEqual(names, ["a.mp3", "b.wav"])

    def test_missing_mood_dir_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                bs.list_bgm_candidates(Path(tmp), "energetic")

    def test_empty_mood_dir_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "calm").mkdir()
            with self.assertRaises(FileNotFoundError):
                bs.list_bgm_candidates(Path(tmp), "calm")


class SelectBgmTest(unittest.TestCase):
    def test_selects_deterministically_with_seeded_rng(self):
        with tempfile.TemporaryDirectory() as tmp:
            mood_dir = Path(tmp) / "calm"
            mood_dir.mkdir()
            for name in ("a.mp3", "b.mp3", "c.mp3"):
                (mood_dir / name).touch()

            selection = bs.select_bgm(
                Path(tmp),
                "calm",
                duration_fn=lambda p: 42.0,
                rng=random.Random(1),
            )
            self.assertEqual(selection.mood, "calm")
            self.assertEqual(selection.duration, 42.0)
            self.assertTrue(selection.path.endswith(".mp3"))

    def test_excludes_given_paths_when_alternatives_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            mood_dir = Path(tmp) / "calm"
            mood_dir.mkdir()
            (mood_dir / "a.mp3").touch()
            (mood_dir / "b.mp3").touch()

            excluded_path = str(mood_dir / "a.mp3")
            for _ in range(10):
                selection = bs.select_bgm(
                    Path(tmp),
                    "calm",
                    exclude={excluded_path},
                    duration_fn=lambda p: 10.0,
                    rng=random.Random(),
                )
                self.assertNotEqual(selection.path, excluded_path)


class DuckingEnvelopeTest(unittest.TestCase):
    def test_envelope_ducks_during_narration_and_recovers(self):
        envelope = bs.compute_ducking_envelope(
            bgm_duration=10.0,
            narration_windows=[(2.0, 4.0)],
            normal_gain=1.0,
            duck_gain=0.2,
            fade=0.5,
        )
        gain_fn = bs.make_gain_function(envelope)

        self.assertAlmostEqual(gain_fn(0.0), 1.0, places=2)
        self.assertAlmostEqual(gain_fn(3.0), 0.2, places=2)
        self.assertAlmostEqual(gain_fn(9.0), 1.0, places=2)

    def test_rejects_non_positive_duration(self):
        with self.assertRaises(ValueError):
            bs.compute_ducking_envelope(0.0, [], 1.0, 0.2, 0.3)


class MakeGainFunctionTest(unittest.TestCase):
    def test_linear_interpolation_between_breakpoints(self):
        gain_fn = bs.make_gain_function([(0.0, 0.0), (10.0, 1.0)])
        self.assertAlmostEqual(gain_fn(5.0), 0.5, places=5)
        self.assertAlmostEqual(gain_fn(-1.0), 0.0, places=5)
        self.assertAlmostEqual(gain_fn(20.0), 1.0, places=5)


if __name__ == "__main__":
    unittest.main()
