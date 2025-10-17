"""
VLOEX SDK Client
Minimal, Stripe-style API
"""

from typing import Dict, Optional, List
import requests
from .exceptions import VloexError


DEFAULT_BASE_URL = 'https://api.vloex.com'


class VideoResource:
    """Videos resource - core primitive"""

    def __init__(self, client: 'Vloex'):
        self._client = client

    def create(self, script: str, webhook_url: str = None, webhook_secret: str = None, idempotency_key: str = None, **options) -> Dict:
        """
        Create a video from text (async - returns immediately)

        Args:
            script: The text script for your video
            webhook_url: Webhook URL to receive completion notification (recommended)
            webhook_secret: Secret for webhook HMAC signature
            idempotency_key: Optional UUID to prevent duplicate charges on retry (e.g., str(uuid.uuid4()))
            **options: Optional settings (avatar, voice, background - coming soon)

        Returns:
            dict: Job object with id and status='queued'

        Example:
            import uuid
            video = vloex.videos.create(
                script='Version 2.0 is live!',
                webhook_url='https://your-app.com/webhook',
                idempotency_key=str(uuid.uuid4())  # Optional: prevents duplicate charges
            )
        """
        payload = {
            'input': script,
            'options': options
        }

        if webhook_url:
            payload['webhook_url'] = webhook_url

        if webhook_secret:
            payload['webhook_secret'] = webhook_secret

        return self._client._request('POST', '/v1/generate', payload, idempotency_key=idempotency_key)

    def retrieve(self, id: str) -> Dict:
        """
        Get video status and URL

        Args:
            id: Video job ID

        Returns:
            dict: Video object with current status

        Example:
            status = vloex.videos.retrieve('job_abc123')
            print(status['url'])
        """
        return self._client._request('GET', f'/v1/jobs/{id}/status')

    def from_journey(
        self,
        screenshots: Optional[List[str]] = None,
        descriptions: Optional[List[str]] = None,
        product_url: Optional[str] = None,
        pages: Optional[List[str]] = None,
        product_context: str = None,
        step_duration: int = 15,
        avatar_position: str = 'bottom-right',
        tone: str = 'professional',
        webhook_url: str = None,
        webhook_secret: str = None,
        **options
    ) -> Dict:
        """
        Create product demo videos from screenshots or URLs (ASYNC - returns immediately)

        ⚠️  This endpoint is ASYNC - it returns a job_id immediately.
        Video generation takes 8-12 minutes in the background.

        Use webhooks (recommended) or poll /v1/jobs/{job_id}/status to get the final video URL.

        **3 Modes Available:**

        Mode 1A - Screenshots + Manual Descriptions:
            video = vloex.videos.from_journey(
                screenshots=['base64img1...', 'base64img2...'],
                descriptions=['Login page walkthrough', 'Dashboard overview'],
                product_context='My Product Demo',
                webhook_url='https://your-app.com/webhook'
            )

        Mode 1B - Screenshots Only (AI auto-generates narrations):
            video = vloex.videos.from_journey(
                screenshots=['base64img1...', 'base64img2...'],
                product_context='My Product Demo',  # Omit descriptions for AI auto-narration
                webhook_url='https://your-app.com/webhook'
            )

        Mode 2 - URL + Pages (Auto-capture + AI narration):
            video = vloex.videos.from_journey(
                product_url='https://myapp.com',
                pages=['/', '/features', '/pricing'],
                product_context='MyApp Website Tour',
                webhook_url='https://your-app.com/webhook'
            )

        Args:
            screenshots: List of base64-encoded images (Mode 1A/1B)
            descriptions: Narration for each screenshot (Mode 1A). If omitted, AI auto-generates narrations (Mode 1B)
            product_url: Public URL to capture (Mode 2)
            pages: List of page paths like ['/dashboard', '/pricing'] (Mode 2)
            product_context: Brief description of what you're demoing (e.g., "MyApp Dashboard", "ACME CRM Platform")
            step_duration: Seconds per screenshot (default: 15)
            avatar_position: Avatar placement - 'bottom-right', 'bottom-left', 'top-right', 'top-left'
            tone: Narration style - 'professional', 'casual', 'technical'
            webhook_url: Your webhook URL to receive completion notification (recommended)
            webhook_secret: Secret for HMAC signature verification
            **options: Additional settings

        Returns:
            dict: Job object with id and status='queued'
                  {
                      'id': 'job_abc123',
                      'status': 'queued',
                      'created_at': '2024-01-15T10:30:00Z'
                  }

        Webhook Payload (when complete):
            {
                "event": "video.completed",
                "job_id": "job_abc123",
                "status": "completed",
                "video_url": "https://...",
                "cost": 1.25,
                "timestamp": "2024-01-15T10:42:00Z"
            }
        """
        if not product_context:
            raise ValueError('product_context is required')

        payload = {
            'product_context': product_context,
            'step_duration': step_duration,
            'avatar_position': avatar_position,
            'tone': tone,
            **options
        }

        # Level 1: Screenshots + descriptions
        if screenshots:
            payload['screenshots'] = screenshots
            if descriptions:
                payload['descriptions'] = descriptions

        # Level 2: URL + pages
        if product_url:
            payload['product_url'] = product_url
            if pages:
                payload['pages'] = pages

        # Webhook support
        if webhook_url:
            payload['webhook_url'] = webhook_url
        if webhook_secret:
            payload['webhook_secret'] = webhook_secret

        return self._client._request('POST', '/v1/videos/from-journey', payload)


class Vloex:
    """VLOEX SDK Client"""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL):
        """
        Initialize VLOEX SDK

        Args:
            api_key: Your VLOEX API key (get one at https://vloex.com/api-keys)
            base_url: Optional custom base URL
        """
        if not api_key:
            raise ValueError('VLOEX API key required. Get one at https://vloex.com/api-keys')

        self.api_key = api_key
        self.base_url = base_url
        self.videos = VideoResource(self)

    def _request(self, method: str, path: str, body: Optional[Dict] = None, idempotency_key: str = None) -> Dict:
        """Internal: Make HTTP request"""
        url = f'{self.base_url}{path}'

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

        # Add idempotency key if provided
        if idempotency_key:
            headers['Idempotency-Key'] = idempotency_key

        # Set timeout - all endpoints now return immediately (async)
        timeout = 60

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=body,
            timeout=timeout
        )

        try:
            data = response.json()
        except ValueError:
            data = {}

        if not response.ok:
            error_message = data.get('detail') or data.get('message') or 'API request failed'
            raise VloexError(error_message, response.status_code)

        # Transform API response to SDK format
        if '/generate' in path:
            return {
                'id': data.get('job_id') or data.get('id'),
                'status': data.get('status'),
                'url': data.get('url'),
                'error': data.get('error')
            }

        if '/status' in path:
            return {
                'id': data.get('id'),
                'status': data.get('status'),
                'url': data.get('video_url') or data.get('url'),
                'error': data.get('error_message') or data.get('error')
            }

        if '/from-journey' in path:
            # Now returns job status (async endpoint)
            return {
                'id': data.get('id'),
                'status': data.get('status'),
                'created_at': data.get('created_at'),
                'updated_at': data.get('updated_at')
            }

        return data
