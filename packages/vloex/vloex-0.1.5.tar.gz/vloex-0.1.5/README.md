# VLOEX Python SDK

Official Python SDK for VLOEX - Turn text into professional videos with AI.

[![PyPI version](https://badge.fury.io/py/vloex.svg)](https://pypi.org/project/vloex/)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📦 Installation

```bash
pip install vloex
```

**Requirements:** Python 3.7 or higher

---

## 🚀 Quick Start

### Step 1: Get Your API Key

1. Sign up at [vloex.com](https://vloex.com)
2. Go to **Dashboard** → **API Keys**
3. Click **Create New Key**
4. Copy your key (starts with `vs_live_...`)

### Step 2: Create Your First Video

```python
from vloex import Vloex

# Initialize with your API key
vloex = Vloex('vs_live_your_key_here')

# Create a video
video = vloex.videos.create(
    script="Hello! This is my first AI-generated video."
)

print(f"✅ Video created: {video['id']}")
print(f"📊 Status: {video['status']}")
```

### Step 3: Get Your Video

```python
import time

# Wait for video to complete
while True:
    status = vloex.videos.retrieve(video['id'])

    if status['status'] == 'completed':
        print(f"🎉 Video ready: {status['url']}")
        break

    if status['status'] == 'failed':
        print(f"❌ Failed: {status.get('error')}")
        break

    time.sleep(5)  # Check again in 5 seconds
```

**That's it!** Your video is ready to share.

---

## 📖 Usage

### Basic Video Generation

```python
from vloex import Vloex

vloex = Vloex('vs_live_your_key_here')

# Simple text to video
video = vloex.videos.create(
    script="We just launched version 2.0 with dark mode!"
)
```

### With Custom Options (Coming Soon)

```python
video = vloex.videos.create(
    script="Welcome to our product demo!",
    options={
        'avatar': 'lily',              # Only supported avatar
        'voice': 'enthusiastic',       # Only supported voice
        'background': 'modern_office'  # Only supported background
    }
)

# More avatars, voices, and backgrounds coming soon!
```

### Using Environment Variables

```python
import os
from vloex import Vloex

# Set environment variable
# export VLOEX_API_KEY='vs_live_...'

vloex = Vloex(os.getenv('VLOEX_API_KEY'))
video = vloex.videos.create(script="...")
```

### With Webhooks (Get Notified When Ready)

```python
video = vloex.videos.create(
    script="Your video content here",
    webhook_url="https://your-app.com/webhook"
)

# Your code continues immediately
# We'll POST to your webhook when the video is ready
```

### Journey Videos (Product Demos)

Create videos from screenshots or URLs:

**Mode 1: Screenshots with Descriptions (Fastest)**
```python
video = vloex.videos.from_journey(
    screenshots=['base64img1...', 'base64img2...'],
    descriptions=['Login page', 'Dashboard overview'],
    product_context='MyApp Demo'
)
```

**Mode 2: URL + Page Paths (Public Pages)**
```python
video = vloex.videos.from_journey(
    product_url='https://myapp.com',
    pages=['/', '/features', '/pricing'],
    product_context='MyApp Website Tour'
)
```

---

## 📚 API Reference

### `vloex.videos.create()`

Create a new video.

**Parameters:**
- `script` (str, required) - The text script for your video
- `webhook_url` (str, optional) - URL to receive completion notification
- `webhook_secret` (str, optional) - Secret for webhook HMAC signature
- `options` (dict, optional) - Customize avatar, voice, background (coming soon)
  - `avatar`: `'lily'` (only supported option)
  - `voice`: `'enthusiastic'` (only supported option)
  - `background`: `'modern_office'` (only supported option)

**Returns:**
```python
{
    'id': 'abc-123-def-456',
    'status': 'pending',
    'created_at': '2025-01-04T12:00:00Z',
    'estimated_completion': '2025-01-04T12:05:00Z'
}
```

### `vloex.videos.retrieve(id)`

Get video status and URL.

**Parameters:**
- `id` (str, required) - Video job ID

**Returns:**
```python
{
    'id': 'abc-123-def-456',
    'status': 'completed',  # or 'pending', 'processing', 'failed'
    'url': 'https://...',   # Video URL when completed
    'duration': 12.5,       # Video length in seconds
    'created_at': '...',
    'updated_at': '...'
}
```

---

## 💡 Examples

### Example 1: Simple Video

```python
from vloex import Vloex

vloex = Vloex('vs_live_your_key_here')

video = vloex.videos.create(
    script="Check out our new features!"
)

print(f"Video ID: {video['id']}")
```

### Example 2: GitHub Release Announcement

```python
from vloex import Vloex
import requests

# Fetch latest release
release = requests.get(
    'https://api.github.com/repos/vercel/next.js/releases/latest'
).json()

# Create announcement video
vloex = Vloex('vs_live_your_key_here')

video = vloex.videos.create(
    script=f"Next.js {release['tag_name']} is here! {release['body'][:200]}"
)

print(f"Release video: {video['id']}")
```

**See more examples:** [examples/](./examples)

---

## ⚠️ Error Handling

```python
from vloex import Vloex, VloexError

vloex = Vloex('vs_live_...')

try:
    video = vloex.videos.create(script="Hello!")

except VloexError as e:
    if e.status_code == 401:
        print("Invalid API key")
    elif e.status_code == 429:
        print("Rate limit exceeded - wait a moment")
    elif e.status_code == 402:
        print("Quota exceeded - upgrade your plan")
    else:
        print(f"Error: {e.message}")
```

**Common Errors:**

| Code | Meaning | What to Do |
|------|---------|------------|
| 401 | Invalid API key | Check your key at vloex.com/dashboard |
| 429 | Too many requests | Wait 60 seconds and try again |
| 402 | Quota exceeded | Upgrade your plan |
| 400 | Bad request | Check your script/parameters |
| 500 | Server error | Retry in a few seconds |

---

## 🔧 Advanced

### Custom Timeout

```python
vloex = Vloex(
    api_key='vs_live_...',
    timeout=60  # seconds
)
```

### Custom API Endpoint

```python
vloex = Vloex(
    api_key='vs_live_...',
    base_url='https://custom-api.example.com'
)
```

### Debug Mode

```python
import logging

logging.basicConfig(level=logging.DEBUG)
vloex = Vloex('vs_live_...')
# Prints all API requests
```

---

## 📚 Resources

- **Documentation:** https://docs.vloex.com
- **API Docs:** https://api.vloex.com/docs
- **Examples:** [examples/](./examples)
- **GitHub:** https://github.com/vloex/vloex-python
- **npm Package:** https://pypi.org/project/vloex/

---

## 🆘 Support

- **Email:** support@vloex.com
- **Issues:** https://github.com/vloex/vloex-python/issues

---

## 📄 License

MIT License
