"""Offline regression checks for the LM Studio v1 download-status endpoint."""
import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "lmstudio_admin", Path(__file__).resolve().parents[1] / "scripts/lmstudio_admin.py"
)
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)


class DownloadStatusTests(unittest.TestCase):
    def test_job_id_is_an_encoded_path_segment(self):
        for job_id, encoded in [("job_123", "job_123"),
                                ("job /?#%", "job%20%2F%3F%23%25")]:
            with self.subTest(job_id=job_id):
                result = {"job_id": job_id, "status": "completed"}
                output = io.StringIO()
                args = argparse.Namespace(base_url="http://localhost:1234/v1", job_id=job_id)
                with patch.object(admin, "http_request", return_value=result) as request:
                    with redirect_stdout(output):
                        self.assertEqual(admin.cmd_download_status(args), 0)
                request.assert_called_once_with(
                    "GET", "http://localhost:1234/api/v1/models/download/status/" + encoded
                )
                self.assertEqual(json.loads(output.getvalue()), result)

    def test_request_failure_is_not_reported_as_success(self):
        args = argparse.Namespace(base_url="http://localhost:1234", job_id="job_123")
        with patch.object(admin, "http_request", side_effect=admin.LMStudioError("offline")):
            with self.assertRaises(admin.LMStudioError):
                admin.cmd_download_status(args)


if __name__ == "__main__":
    unittest.main()
