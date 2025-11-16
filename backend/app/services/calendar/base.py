from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime


class CalendarProvider(ABC):
    """Abstract base class for calendar provider strategies"""
    
    @abstractmethod
    async def fetch_events(
        self,
        account,
        max_results: int = 50,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch events from the calendar provider.
        
        Args:
            account: Calendar account object (provider-specific)
            max_results: Maximum number of events to fetch
            time_min: Start time for event range
            time_max: End time for event range
            
        Returns:
            List of event dictionaries
        """
        pass
    
    @abstractmethod
    def extract_meeting_link(self, event: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract meeting link and platform from calendar event.
        
        Args:
            event: Calendar event dictionary (provider-specific format)
            
        Returns:
            Tuple of (platform, link) where platform is 'zoom', 'teams', 'meet', etc.
        """
        pass
    
    @abstractmethod
    def refresh_credentials(self, account) -> Optional[Any]:
        """
        Refresh OAuth credentials if needed.
        
        Args:
            account: Calendar account object (provider-specific)
            
        Returns:
            Refreshed credentials object or None if refresh failed
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the calendar provider name (e.g., 'google', 'outlook', 'apple')"""
        pass

