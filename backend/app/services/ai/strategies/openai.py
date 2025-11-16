from typing import Optional
import httpx
from app.core.config import settings
from app.services.ai.base import AIGenerator


class OpenAIGenerator(AIGenerator):
    """OpenAI AI content generation strategy"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-3.5-turbo')
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    def _extract_content(self, result) -> Optional[str]:
        """Extract content from various OpenAI response formats"""
        content = None
        
        # Check if result is a list (Responses API format)
        if isinstance(result, list) and len(result) > 0:
            first_item = result[0]
            if isinstance(first_item, dict):
                content = first_item.get("text")
        
        # Check for nested content structures
        if not content and isinstance(result, dict) and "output" in result:
            output = result["output"]
            if isinstance(output, str):
                content = output
            elif isinstance(output, dict) and "content" in output:
                content = output["content"]
            elif isinstance(output, list) and len(output) > 0:
                item = output[0]
                if isinstance(item, dict):
                    content = item.get("text") or item.get("content")
        
        # Check for direct content/text fields
        if not content and isinstance(result, dict):
            if "content" in result:
                content = result["content"]
            elif "text" in result:
                content = result["text"]
            elif "response" in result:
                content = result["response"]
        
        # Check for choices structure (Chat Completions format)
        if not content and isinstance(result, dict) and "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if isinstance(choice, dict):
                if "message" in choice and isinstance(choice["message"], dict):
                    content = choice["message"].get("content")
                elif "content" in choice:
                    content = choice["content"]
                elif "text" in choice:
                    content = choice["text"]
        
        # Process content if found
        if content is not None:
            if isinstance(content, str):
                return content.strip()
            elif isinstance(content, dict):
                return str(content.get("text", content.get("content", content))).strip()
            else:
                return str(content).strip()
        
        # Fallback: return string representation of entire result
        return str(result).strip() if result else None
    
    async def generate_follow_up_email(
        self,
        transcript: str,
        meeting_title: str,
        attendees: list,
        meeting_date: str
    ) -> str:
        """Generate a follow-up email from meeting transcript"""
        if not self.api_key:
            return "OpenAI API key not configured. Please set OPENAI_API_KEY in your environment."
        
        attendees_list = ", ".join([a.get("name", "Unknown") for a in attendees]) if attendees else "Team members"
        
        prompt = f"""You are a professional assistant helping to write a follow-up email after a meeting.

Meeting Details:
- Title: {meeting_title}
- Date: {meeting_date}
- Attendees: {attendees_list}

Meeting Transcript:
{transcript}

Please generate a professional, concise follow-up email that:
1. Thanks attendees for their participation
2. Summarizes key discussion points and decisions
3. Lists action items (if any)
4. Mentions next steps or follow-up meetings (if applicable)
5. Has a friendly, professional tone

Format the email as plain text with:
- Subject line
- Greeting
- Body paragraphs
- Closing

Do not include email headers (From, To, etc.), just the email content."""

        try:
            full_prompt = f"""You are a professional email writing assistant. Generate clear, concise, and professional follow-up emails.

{prompt}"""
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/responses",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "input": full_prompt,
                        "temperature": 0.7,
                        "max_output_tokens": 1000,
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                content = self._extract_content(result)
                return content if content else "Error generating email: No content returned"
                
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", error_detail)
            except:
                error_detail = e.response.text or error_detail
            return f"Error generating email: {error_detail}"
        except Exception as e:
            return f"Error generating email: {str(e)}"
    
    async def generate_social_media_post(
        self,
        transcript: str,
        meeting_title: str,
        platform: str,
        custom_prompt: Optional[str] = None
    ) -> str:
        """Generate a social media post from meeting transcript"""
        if not self.api_key:
            return "OpenAI API key not configured. Please set OPENAI_API_KEY in your environment."
        
        # Platform-specific guidelines
        platform_guidelines = {
            "linkedin": "professional, business-focused, industry insights, networking",
            "facebook": "engaging, conversational, community-focused, relatable"
        }
        
        guidelines = platform_guidelines.get(platform.lower(), "engaging and professional")
        
        if custom_prompt:
            # Use custom prompt template, replacing placeholders
            prompt = custom_prompt.replace("{transcript}", transcript).replace("{meeting_title}", meeting_title)
        else:
            # Default prompt
            prompt = f"""You are a social media content creator helping to create a {platform} post based on a meeting.

Meeting Title: {meeting_title}

Meeting Transcript:
{transcript}

Please generate a {platform} post that:
1. Is {guidelines} in tone
2. Highlights key insights or takeaways from the meeting
3. Is engaging and encourages interaction
4. Is appropriate for {platform} (consider platform character limits and style)
5. Uses relevant hashtags if appropriate for {platform}

For LinkedIn: Keep it professional, focus on business value, use 1-3 relevant hashtags
For Facebook: Keep it conversational, focus on community, use 1-2 relevant hashtags

Generate only the post content, no additional formatting or explanations."""

        try:
            full_prompt = f"""You are a social media content creator specializing in {platform} posts. Create engaging, platform-appropriate content.

{prompt}"""
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/responses",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "input": full_prompt,
                        "temperature": 0.8,
                        "max_output_tokens": 500,
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                content = self._extract_content(result)
                return content if content else "Error generating post: No content returned"
                
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", error_detail)
            except:
                error_detail = e.response.text or error_detail
            return f"Error generating post: {error_detail}"
        except Exception as e:
            return f"Error generating post: {str(e)}"

