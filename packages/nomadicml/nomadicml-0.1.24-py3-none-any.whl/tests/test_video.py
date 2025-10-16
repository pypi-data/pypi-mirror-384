"""
Tests for the NomadicML video client.
"""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from nomadicml import NomadicML
from nomadicml.types import VideoSource
from nomadicml.video import AnalysisType, CustomCategory
from nomadicml.exceptions import ValidationError
import time

class TestVideoClient:
    """Test cases for the NomadicML video client."""

    @pytest.fixture
    def client(self):
        """Create a NomadicML client for testing."""
        return NomadicML(api_key="test_api_key")

    def test_upload_video_with_missing_path(self, client):
        """Test upload_video with missing file_path."""
        with pytest.raises(ValidationError):
            client.video._upload_video("")

    # Override the actual validate_file_path in the module namespace
    @patch("nomadicml.video.validate_file_path")
    @patch("nomadicml.video.VideoClient.get_user_id")
    @patch("nomadicml.utils.get_filename_from_path")
    @patch("nomadicml.utils.get_file_mime_type")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake video data")
    @patch("nomadicml.client.NomadicML._make_request")
    def test_upload_video_file_success(self, mock_make_request, mock_open_file,
                                   mock_get_mime_type, mock_get_filename,
                                   mock_get_user_id, mock_validate_path, client):
        """Test successful video file upload."""
        # Setup mocks
        mock_validate_path.return_value = None  # Just ensure it doesn't raise an exception
        mock_get_filename.return_value = "test_video.mp4"
        mock_get_mime_type.return_value = "video/mp4"
        mock_get_user_id.return_value = "test_user"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "video_id": "test_video_id"}
        mock_make_request.return_value = mock_response
        
        # Call the method
        result = client.video._upload_video(file_path="/path/to/test_video.mp4")
        
        # Assertions
        assert result == {"status": "success", "video_id": "test_video_id"}
        mock_validate_path.assert_called_once_with("/path/to/test_video.mp4")
        mock_make_request.assert_called_once()

        # Verify SDK headers were included
        call_args = mock_make_request.call_args
        # Headers should be passed through kwargs or in the actual request call
        called_kwargs = call_args.kwargs
        assert called_kwargs["data"]["scope"] == "user"

    @patch("nomadicml.video.validate_file_path")
    @patch("nomadicml.video.VideoClient.get_user_id")
    @patch("nomadicml.utils.get_filename_from_path")
    @patch("nomadicml.utils.get_file_mime_type")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake video data")
    @patch("nomadicml.client.NomadicML._make_request")
    def test_upload_video_file_with_org_scope(self, mock_make_request, mock_open_file,
                                         mock_get_mime_type, mock_get_filename,
                                         mock_get_user_id, mock_validate_path, client):
        mock_validate_path.return_value = None
        mock_get_filename.return_value = "test_video.mp4"
        mock_get_mime_type.return_value = "video/mp4"
        mock_get_user_id.return_value = "test_user"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "video_id": "test_video_id"}
        mock_make_request.return_value = mock_response

        client.video._upload_video(
            file_path="/path/to/test_video.mp4",
            folder="Marketing",
            scope="org",
        )

        called_kwargs = mock_make_request.call_args.kwargs
        assert called_kwargs["data"]["scope"] == "org"

    @patch("nomadicml.client.requests.request")
    def test_sdk_headers_included(self, mock_request, client):
        """Test that SDK identification headers are included in requests."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_request.return_value = mock_response
        
        # Make a request
        client._make_request("GET", "/test")
        
        # Verify headers were included
        call_args = mock_request.call_args
        headers = call_args[1]["headers"]
        assert headers["X-Client-Type"] == "SDK"
        assert "X-Client-Version" in headers
        assert "NomadicML-Python-SDK" in headers["User-Agent"]

    @patch("nomadicml.client.NomadicML._make_request")
    def test_analyze_video_success(self, mock_make_request, client):
        """Test successful video analysis."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "analysis_id": "test_analysis_id"}
        mock_make_request.return_value = mock_response
        
        # Call the method
        result = client.video.analyze_video("test_video_id")
        
        # Assertions
        assert result == {"status": "success", "analysis_id": "test_analysis_id"}
        mock_make_request.assert_called_once_with(
            method="POST",
            endpoint="/api/analyze-video/test_video_id",
            data={
                "firebase_collection_name": client.collection_name,
                "model_id": "Nomadic-VL-XLarge",
            },
        )

    @patch("nomadicml.client.NomadicML._make_request")
    def test_get_video_status_success(self, mock_make_request, client):
        """Test successful video status retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "completed", "progress": 100}
        mock_make_request.return_value = mock_response
        
        # Call the method
        result = client.video.get_video_status("test_video_id")
        
        # Assertions
        assert result == {"status": "completed", "progress": 100}
        mock_make_request.assert_called_once_with(
            "GET",
            "/api/video/test_video_id/status",
            params={"firebase_collection_name": client.collection_name}
        )

    @patch("nomadicml.client.NomadicML._make_request")
    def test_get_video_analysis_success(self, mock_make_request, client):
        """Test successful video analysis retrieval.""" 
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"events": [], "summary": "No events detected"}
        mock_make_request.return_value = mock_response
        
        # Call the method
        result = client.video.get_video_analysis("test_video_id")
        
        # Assertions
        assert result == {"events": [], "summary": "No events detected"}
        mock_make_request.assert_called_once_with(
            "GET",
            "/api/video/test_video_id/analysis",
            params={"firebase_collection_name": client.collection_name}
        )

    @patch("nomadicml.client.NomadicML._make_request")
    def test_delete_video_success(self, mock_make_request, client):
        """Test successful video deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "deleted"}
        mock_make_request.return_value = mock_response
        
        # Call the method
        result = client.video.delete_video("test_video_id")
        
        # Assertions
        assert result == {"status": "deleted"}
        mock_make_request.assert_called_once_with(
            "DELETE",
            "/api/video/test_video_id",
            params={"firebase_collection_name": client.collection_name}
        )

    @patch("nomadicml.client.NomadicML._make_request")
    def test_my_videos_success(self, mock_make_request, client):
        """Test successful video list retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"video_id": "test_video_1"}, {"video_id": "test_video_2"}]
        mock_make_request.return_value = mock_response

        # Call the method
        result = client.video.my_videos()

        # Assertions
        assert result == [{"video_id": "test_video_1"}, {"video_id": "test_video_2"}]
        mock_make_request.assert_called_once_with(
            "GET",
            "/api/videos",
            params={"firebase_collection_name": client.collection_name}
        )

    @patch("nomadicml.video.VideoClient._submit_batch")
    def test_analyze_many_returns_batch_links_on_start(self, mock_submit, client):
        mock_submit.return_value = {"batch_id": "batch123"}

        response = client.video._analyze_many(
            ["vid1", "vid2"],
            analysis_type=AnalysisType.ASK,
            model_id="Nomadic-VL-XLarge",
            timeout=30,
            wait_for_completion=False,
            search_query=None,
            custom_event="Did the driver stop?",
            custom_category=CustomCategory.DRIVING,
            concept_ids=None,
            return_subset=False,
            is_thumbnail=False,
            use_enhanced_motion_analysis=False,
        )

        assert set(response.keys()) == {"batch_metadata", "results"}
        metadata = response["batch_metadata"]
        assert metadata["batch_id"] == "batch123"
        assert metadata["batch_viewer_url"].endswith("/use-cases/rapid-review/batch-view/batch123")
        assert metadata["batch_viewer_url"].startswith("http")
        assert metadata["batch_type"] == "ask"

        results = response["results"]
        assert len(results) == 2
        for entry in results:
            assert entry["video_id"] in {"vid1", "vid2"}
            assert entry["analysis_id"] is None
            assert entry["mode"] == "rapid_review"
            assert entry["status"] == "started"
        mock_submit.assert_called_once()

    @patch("nomadicml.video.VideoClient._extract_summary", side_effect=["summary-one", "summary-two"])
    @patch("nomadicml.video.VideoClient._parse_api_events", side_effect=[[{"id": 1}], [{"id": 2}]])
    @patch("nomadicml.video.VideoClient.get_video_analysis")
    @patch("nomadicml.video.VideoClient._poll_batch_status")
    @patch("nomadicml.video.VideoClient._submit_batch")
    def test_analyze_many_waits_for_completion(
        self,
        mock_submit,
        mock_poll,
        mock_get_analysis,
        mock_parse,
        mock_summary,
        client,
    ):
        mock_submit.return_value = {"batch_id": "batchXYZ"}
        mock_poll.return_value = {
            "status": "completed",
            "aggregated_progress": {"total": 2, "completed": 2},
            "videos": [
                {"video_id": "vid1", "status": "completed", "analysis_id": "analysis-1"},
                {"video_id": "vid2", "status": "completed", "analysis_id": "analysis-2"},
            ],
        }
        mock_get_analysis.side_effect = [
            {
                "analysis": {"analysis_id": "analysis-1", "status": "COMPLETED"},
                "metadata": {"visual_analysis": {"status": {"status": "COMPLETED"}}},
            },
            {
                "analysis": {"analysis_id": "analysis-2", "status": "COMPLETED"},
                "metadata": {"visual_analysis": {"status": {"status": "COMPLETED"}}},
            },
        ]

        response = client.video._analyze_many(
            ["vid1", "vid2"],
            analysis_type=AnalysisType.ASK,
            model_id="Nomadic-VL-XLarge",
            timeout=30,
            wait_for_completion=True,
            search_query=None,
            custom_event="Check intersections",
            custom_category=CustomCategory.DRIVING,
            concept_ids=None,
            return_subset=False,
            is_thumbnail=False,
            use_enhanced_motion_analysis=False,
        )

        assert set(response.keys()) == {"batch_metadata", "results"}
        metadata = response["batch_metadata"]
        assert metadata["batch_id"] == "batchXYZ"
        assert metadata["batch_viewer_url"].endswith("/use-cases/rapid-review/batch-view/batchXYZ")
        assert metadata["batch_viewer_url"].startswith("http")
        assert metadata["batch_type"] == "ask"

        results = response["results"]
        assert [entry["analysis_id"] for entry in results] == ["analysis-1", "analysis-2"]
        assert all(entry["mode"] == "rapid_review" for entry in results)
        assert all(entry["status"] == "completed" for entry in results)
        assert results[0]["events"] == [{"id": 1}]
        assert results[1]["events"] == [{"id": 2}]
        assert results[0]["summary"] == "summary-one"
        assert results[1]["summary"] == "summary-two"
        mock_submit.assert_called_once()
        mock_poll.assert_called_once()
        assert mock_get_analysis.call_count == 2
        assert mock_parse.call_count == 2

    @patch("nomadicml.video.VideoClient.get_video_analysis")
    @patch("nomadicml.video.VideoClient._poll_batch_status")
    @patch("nomadicml.video.VideoClient._submit_batch")
    def test_analyze_many_missing_pointer_failure(
        self,
        mock_submit,
        mock_poll,
        mock_get_analysis,
        client,
    ):
        mock_submit.return_value = {"batch_id": "batchNoPtr"}
        mock_poll.return_value = {
            "status": "completed",
            "videos": [
                {"video_id": "vid-missing", "status": "completed"},
            ],
        }

        response = client.video._analyze_many(
            ["vid-missing"],
            analysis_type=AnalysisType.ASK,
            model_id="Nomadic-VL-XLarge",
            timeout=30,
            wait_for_completion=True,
            search_query=None,
            custom_event="Check intersections",
            custom_category=CustomCategory.DRIVING,
            concept_ids=None,
            return_subset=False,
            is_thumbnail=False,
            use_enhanced_motion_analysis=False,
        )

        result = response["results"][0]
        assert result["video_id"] == "vid-missing"
        assert result["status"] == "failed"
        assert result["analysis_id"] is None
        assert "analysis pointer" in result["error"]
        mock_get_analysis.assert_not_called()

    def test_wait_for_analysis_timeout(self, client):
        """Test that wait_for_analysis raises TimeoutError when analysis doesn't complete."""
        with patch.object(client.video, 'get_video_status') as mock_get_status:
            mock_get_status.return_value = {"status": "processing"}
            
            with pytest.raises(TimeoutError):
                client.video.wait_for_analysis("test_video_id", timeout=1, poll_interval=0.1)

    @patch("nomadicml.video.VideoClient.get_video_status")
    def test_wait_for_analysis_success(self, mock_get_status, client):
        """Test successful wait_for_analysis."""
        # First call returns processing, second call returns completed
        mock_get_status.side_effect = [
            {"status": "processing"},
            {"status": "completed", "analysis": {"events": []}}
        ]
        
        result = client.video.wait_for_analysis("test_video_id", timeout=10, poll_interval=0.1)
        
        assert result["status"] == "completed"
        assert mock_get_status.call_count == 2

    @patch("nomadicml.client.NomadicML._make_request")
    def test_create_or_get_folder_success(self, mock_make_request, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "folder1", "name": "Marketing", "scope": "org"}
        mock_make_request.return_value = mock_response

        data = client.video.create_or_get_folder("Marketing", scope="org")

        assert data == {"id": "folder1", "name": "Marketing", "scope": "org"}
        mock_make_request.assert_called_once_with(
            method="POST",
            endpoint="/api/folders/create-or-get",
            json_data={"name": "Marketing", "scope": "org"},
        )

    def test_create_or_get_folder_invalid_scope(self, client):
        with pytest.raises(ValidationError):
            client.video.create_or_get_folder("Marketing", scope="invalid")

    def test_create_or_get_folder_empty_name(self, client):
        with pytest.raises(ValidationError):
            client.video.create_or_get_folder(" ")
