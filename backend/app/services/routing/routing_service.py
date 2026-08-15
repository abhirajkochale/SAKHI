from abc import ABC, abstractmethod
from typing import Optional
from app.schemas.journey import JourneyRequest, JourneyResponse

class RoutingService(ABC):
    """
    Abstract base class for routing services.
    Ensures that SAKHI is not tightly coupled to any specific routing provider.
    """

    @abstractmethod
    async def get_journey(self, request: JourneyRequest) -> JourneyResponse:
        """
        Calculates a route and returns a JourneyResponse containing
        the total distance, duration, and ordered JourneySegments.
        """
        pass
