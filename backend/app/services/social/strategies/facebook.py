from typing import Dict, Any, Optional
import httpx
from app.services.social.base import SocialMediaPoster


class FacebookPoster(SocialMediaPoster):
    """Facebook social media posting strategy"""
    
    @property
    def platform_name(self) -> str:
        return "facebook"
    
    async def post(
        self,
        access_token: str,
        content: str,
        page_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Post content to Facebook using the user's access token.
        
        Args:
            access_token: Facebook OAuth access token
            content: Post content text
            page_id: Optional page ID to post to (if None, posts to user's timeline)
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with post_id and other response data
        
        Raises:
            Exception if posting fails
        """
        # If no page_id, post to user's timeline
        endpoint = "me/feed" if not page_id else f"{page_id}/feed"
        
        post_data = {
            "message": content,
            "access_token": access_token,
        }
        
        async with httpx.AsyncClient() as client:
            post_response = await client.post(
                f"https://graph.facebook.com/v18.0/{endpoint}",
                data=post_data,
            )
        
        if post_response.status_code not in [200, 201]:
            error_text = post_response.text
            try:
                error_json = post_response.json()
                error_message = error_json.get("error", {}).get("message", error_text)
                raise Exception(f"Failed to post to Facebook: {error_message}")
            except:
                raise Exception(f"Failed to post to Facebook: {error_text}")
        
        post_result = post_response.json()
        
        # Extract post ID from response
        post_id = post_result.get("id", "")
        
        return {
            "post_id": post_id,
            "platform": "facebook",
            "success": True,
        }

