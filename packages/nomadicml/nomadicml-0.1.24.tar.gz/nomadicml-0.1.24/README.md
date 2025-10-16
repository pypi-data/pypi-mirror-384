# NomadicML Python SDK

A Python client library for the NomadicML DriveMonitor API, allowing you to upload and analyze driving videos programmatically.

## Installation

### From PyPI (for users)

```bash
pip install nomadicml
```

### For Development (from source)

To install the package in development mode, where changes to the code will be immediately reflected without reinstallation:

```bash
# Clone the repository
git clone https://github.com/nomadic-ml/drivemonitor.git
cd sdk

# For development: Install in editable mode
pip install -e .
```

With this installation, any changes you make to the code will be immediately available when you import the package.

## Quick Start

```python
from nomadicml import NomadicML

# Initialize the client with your API key
client = NomadicML(api_key="your_api_key")

# Upload a video and analyze it in one step
result = client.video.upload_and_analyze("path/to/your/video.mp4")

# Print the detected events
for event in result["events"]:
    print(f"Event: {event['type']} at {event['time']}s - {event['description']}")
#For a batch upload

videos_list = [.....]#list of video paths
batch_results = client.video.upload_and_analyze_videos(videos_list, wait_for_completion=False)

    
video_ids = [
    res.get("video_id")
    for res in batch_results
    if res                                         # safety for None
    ]

    
full_results = client.video.wait_for_analyses(video_ids)

```

## Authentication

You need an API key to use the NomadicML API. You can get one by:

1. Log in to your DriveMonitor account
2. Go to Profile > API Key
3. Generate a new API key

Then use this key when initializing the client:

```python
client = NomadicML(api_key="your_api_key")
```

## Video Upload and Analysis

### Upload a video

```python
# Upload a local video file
result = client.video.upload_video(
    source="file",
    file_path="path/to/video.mp4"
)

# Or upload from YouTube
result = client.video.upload_video(
    source="youtube",
    youtube_url="https://www.youtube.com/watch?v=VIDEO_ID"
)

# Get the video ID from the response
video_id = result["video_id"]
```

### Analyze a video

```python
# Start analysis
client.video.analyze_video(video_id)

# Wait for analysis to complete
status = client.video.wait_for_analysis(video_id)

# Get analysis results
analysis = client.video.get_video_analysis(video_id)

# Get detected events
events = client.video.get_video_events(video_id)
```

### Upload and analyze in one step

```python
# Upload and analyze a video, waiting for results
analysis = client.video.upload_and_analyze("path/to/video.mp4")

# Or just start the process without waiting
result = client.video.upload_and_analyze("path/to/video.mp4", wait_for_completion=False)
```

## Advanced Usage

### Filter events by severity or type

```python
# Get only high severity events
high_severity_events = client.video.get_video_events(
    video_id=video_id,
    severity="high"
)

# Get only traffic violation events
traffic_violations = client.video.get_video_events(
    video_id=video_id,
    event_type="Traffic Violation"
)
```

### Custom timeout and polling interval

```python
# Wait for analysis with a custom timeout and polling interval
client.video.wait_for_analysis(
    video_id=video_id,
    timeout=1200,  # 20 minutes
    poll_interval=10  # Check every 10 seconds
)
```

### Batch analyses across many videos

When you provide a list of video IDs to `client.video.analyze(...)`, the SDK now
creates a backend batch automatically (for both Asking Agent and Edge Agent
pipelines) and keeps polling the `/batch/{batch_id}/status` endpoint until the
orchestrator finishes. The return value is a dictionary with two keys:

* `batch_metadata` — contains the `batch_id`, a fully-qualified
  `batch_viewer_url` pointing at the Batch Results Viewer, and a
  `batch_type` flag (`"ask"` or `"agent"`).
* `results` — the list of per-video analysis dictionaries (exactly the same
  schema you would get from calling `analyze()` on a single video).

## BEFORE DEPLOYIN RUN THIS: Running SDK integration tests locally

The integration suite is tagged with `calls_api` and exercises the live backend
endpoints. Make sure you have a valid API key and a backend domain reachable
from your environment, then run:

```bash
cd sdk
export NOMADICML_API_KEY=YOUR_API_KEY
export VITE_BACKEND_DOMAIN=http://127.0.0.1:8099
python -u -m pytest -m calls_api -vvs -rPfE --durations=0 --capture=no tests/test_integration.py
```

The command disables pytest's output capture so you can follow streaming logs
while the long-running tests execute.

```python
from nomadicml.video import AnalysisType, CustomCategory

batch = client.video.analyze(
    ["video_1", "video_2", "video_3"],
    analysis_type=AnalysisType.ASK,
    custom_event="Did the driver stop before the crosswalk?",
    custom_category=CustomCategory.DRIVING,
)

print(batch["batch_metadata"])
for item in batch["results"]:
    print(item["video_id"], item["analysis_id"], len(item.get("events", [])))
```

### Custom API endpoint

If you're using a custom deployment of the DriveMonitor backend:

```python
# Connect to a local or custom deployment
client = NomadicML(
    api_key="your_api_key",
    base_url="http://localhost:8099"
)
```

### Search across videos

Run a semantic search on several of your videos at once:

```python
results = client.video.search(
    "red pickup truck overtaking",
    ["vid123", "vid456"]
)
for match in results["matches"]:
    print(match["videoId"], match["eventIndex"], match["similarity"])
```

## Error Handling

The SDK provides specific exceptions for different error types:

```python
from nomadicml import NomadicMLError, AuthenticationError, VideoUploadError

try:
    client.video.upload_and_analyze("path/to/video.mp4")
except AuthenticationError:
    print("API key is invalid or expired")
except VideoUploadError as e:
    print(f"Failed to upload video: {e}")
except NomadicMLError as e:
    print(f"An error occurred: {e}")
```

## Development

### Setup

Clone the repository and install development dependencies:

```bash
git clone https://github.com/nomadicml/nomadicml-python.git
cd nomadicml-python
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

## License

MIT License. See LICENSE file for details.
