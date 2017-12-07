import os
from PIL import Image

from mock import patch, Mock

from golem.core.common import is_linux
from golem.task.taskbase import Task
from golem.testutils import TempDirFixture, PEP8MixIn
from golem.tools.assertlogs import LogTestCase
from golem.verification.verificator import SubtaskVerificationState

from apps.rendering.task.verificator import RenderingVerificator, logger, FrameRenderingVerificator
from apps.rendering.task.renderingtaskstate import AdvanceRenderingVerificationOptions


class TestRenderingVerificator(TempDirFixture, LogTestCase, PEP8MixIn):
    PEP8_FILES = [
        'apps/rendering/task/verificator.py',
    ]
    last_verdict = None

    def test_get_part_size(self):
        rv = RenderingVerificator(lambda: None)
        subtask_info = {
            "res_x": 800,
            "res_y": 600}
        assert rv._get_part_size(subtask_info) == (800, 600)

    def verification_callback(self, subtask_id, verdict, result):
        print("Verfication callback")
        print("\t subtask_id %r" % subtask_id)
        print("\t verdict %r" % verdict)
        self.last_verdict = verdict

    def test_start_verification(self):
        self.last_verdict = None
        rv = RenderingVerificator(self.verification_callback)
        # Result us not a file
        subtask_info = {
            "res_x": 80,
            "res_y": 60,
            "subtask_id": "subtask1"
        }
        rv.start_verification(subtask_info=subtask_info,
                              results=["file1"],
                              resources=[],
                              reference_data=[])
        assert self.last_verdict == SubtaskVerificationState.WRONG_ANSWER

        subtask_info["total_tasks"] = 30
        subtask_info["start_task"] = 3
        # No data
        self.last_verdict = None
        rv.start_verification(subtask_info=subtask_info,
                              results=[],
                              reference_data=[],
                              resources=[])
        assert self.last_verdict == SubtaskVerificationState.WRONG_ANSWER

        # Result is not an image
        self.last_verdict = None
        rv.start_verification(subtask_info=subtask_info,
                              results=["file1"],
                              reference_data=[],
                              resources=[])
        assert self.last_verdict == SubtaskVerificationState.WRONG_ANSWER

        img_path = os.path.join(self.path, "img1.png")
        img = Image.new("RGB", (80, 60))
        img.save(img_path)

        img_path2 = os.path.join(self.path, "img2.png")
        img = Image.new("RGB", (80, 60))
        img.save(img_path2)

        ver_dir = os.path.join(self.path, "ver_img")
        os.makedirs(ver_dir)
        img_path3 = os.path.join(ver_dir, "img3.png")
        img.save(img_path3)

        # Proper simple verification - just check if images have proper sizes
        self.last_verdict = None
        rv.start_verification(subtask_info=subtask_info,
                              results=[img_path, img_path2],
                              reference_data=[],
                              resources=[])
        assert self.last_verdict == SubtaskVerificationState.VERIFIED


    def test_get_part_img_size(self):
        rv = RenderingVerificator(lambda: None)
        subtask_info = {
            "res_x": 800,
            "res_y": 600,
            "total_tasks": 30,
            "start_task": 3
        }
        assert rv._get_part_img_size(subtask_info) == (0, 40, 800, 60)

        subtask_info["total_tasks"] = 0
        with self.assertLogs(logger, level="WARNING"):
            assert rv._get_part_img_size(subtask_info) == (0, 0, 0, 0)

        subtask_info["total_tasks"] = 30
        subtask_info["start_task"] = 34
        with self.assertLogs(logger, level="WARNING"):
            assert rv._get_part_img_size(subtask_info) == (0, 0, 0, 0)

        subtask_info["total_tasks"] = 11
        subtask_info["res_y"] = 211
        subtask_info["start_task"] = 5
        assert rv._get_part_img_size(subtask_info) == (0, 76, 800, 95)


class TestFrameRenderingVerificator(TempDirFixture):
    def test_check_files(self):
        def callback(*args, **kwargs):
            pass

        frv = FrameRenderingVerificator(callback)
        subtask_info = {"frames": [3], "use_frames": False, "total_tasks": 20,
                        "all_frames": [3], "res_x": 800, "res_y": 600}
        frv._check_files(subtask_info, [])
        assert frv.state == SubtaskVerificationState.WRONG_ANSWER

        subtask_info["use_frames"] = True
        subtask_info["all_frames"] = [3, 4, 5, 6]
        frv._check_files(subtask_info, [])
        assert frv.state == SubtaskVerificationState.WRONG_ANSWER

        subtask_info["total_tasks"] = 2
        frv._check_files(subtask_info, [])
        assert frv.state == SubtaskVerificationState.WRONG_ANSWER

        subtask_info["frames"] = [3, 4]
        frv._check_files(subtask_info, ["file1"])
        assert frv.state == SubtaskVerificationState.WRONG_ANSWER

        subtask_info["start_task"] = 1
        frv._check_files(subtask_info, ["file1", "file2"])
        assert frv.state == SubtaskVerificationState.WRONG_ANSWER

    def test_get_part_img_size(self):
        frv = FrameRenderingVerificator(lambda: None)
        subtask_info = {
            "res_x": 600,
            "res_y": 800,
            "total_tasks": 20,
            "all_frames": [5, 6, 7, 8, 9],
            "start_task": 1,
            "parts": 4,
            "use_frames": True}
        assert frv._get_part_img_size(subtask_info) == (1, 1, 599, 199)
        subtask_info["use_frames"] = False
        assert frv._get_part_img_size(subtask_info) == (0, 0, 600, 40)

