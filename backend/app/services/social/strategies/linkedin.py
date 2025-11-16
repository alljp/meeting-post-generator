from typing import Dict, Any
import httpx
from app.services.social.base import SocialMediaPoster


class LinkedInPoster(SocialMediaPoster):
    """LinkedIn social media posting strategy"""
    
    @property
    def platform_name(self) -> str:
        return "linkedin"
    
    async def post(
        self,
        access_token: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Post content to LinkedIn using the user's access token.
        
        Args:
            access_token: LinkedIn OAuth access token
            content: Post content text
            **kwargs: Additional parameters (unused for LinkedIn)
        
        Returns:
            Dictionary with post_id and other response data
        
        Raises:
            Exception if posting fails
        """
        # First, get the user's LinkedIn URN (person identifier)
        async with httpx.AsyncClient() as client:
            profile_response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        
        if profile_response.status_code != 200:
            raise Exception(f"Failed to get LinkedIn profile: {profile_response.text}")
        
        profile_data = profile_response.json()
        person_urn = f"urn:li:person:{profile_data.get('sub')}"
        
        # Create a share on LinkedIn
        share_data = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": content
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
        
        async with httpx.AsyncClient() as client:
            post_response = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
                json=share_data,
            )
        
        if post_response.status_code not in [200, 201]:
            raise Exception(f"Failed to post to LinkedIn: {post_response.text}")
        
        post_data = post_response.json()
        
        # Extract post ID from response
        post_id = post_data.get("id", "")
        
        return {
            "post_id": post_id,
            "platform": "linkedin",
            "success": True,
        }

