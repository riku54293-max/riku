import unittest
from pathlib import Path

from reel import video_composer as vc


class PlanBackgroundSegmentsTest(unittest.TestCase):
    def test_splits_duration_evenly(self):
        segments = vc.plan_background_segments(["a.jpg", "b.jpg"], 10.0)
        self.assertEqual(segments, [("a.jpg", 5.0), ("b.jpg", 5.0)])

    def test_single_image_gets_full_duration(self):
        segments = vc.plan_background_segments(["a.jpg"], 7.5)
        self.assertEqual(segments, [("a.jpg", 7.5)])

    def test_rejects_empty_images(self):
        with self.assertRaises(ValueError):
            vc.plan_background_segments([], 10.0)

    def test_rejects_non_positive_duration(self):
        with self.assertRaises(ValueError):
            vc.plan_background_segments(["a.jpg"], 0.0)


class OutputFilePathTest(unittest.TestCase):
    def test_builds_expected_filename(self):
        path = vc.output_file_path(Path("output/reels"), "20260820", "exam-stress-ab12cd")
        self.assertEqual(path, Path("output/reels/20260820_exam-stress-ab12cd.mp4"))


if __name__ == "__main__":
    unittest.main()
