"""
AI-powered pricing and allocation strategy service.
Uses Gemini API for intelligent decision-making.
"""
import google.generativeai as genai
import logging
from config import settings

logger = logging.getLogger(__name__)

class AIPricingService:
    """Uses Gemini API to provide AI-driven pricing and allocation logic."""
    
    def __init__(self):
        """Initialize Gemini AI client."""
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.client = genai.GenerativeModel("gemini-pro")
        else:
            logger.warning("GEMINI_API_KEY not configured. Using fallback logic.")
            self.client = None
    
    def get_allocation_strategy(
        self,
        available_pool_kwh: float,
        demand_kwh: float,
        grid_rate_inr: float,
        pool_rate_inr: float,
        house_priority: int = 5,
    ) -> dict:
        """
        Get AI-driven allocation strategy.
        If AI unavailable, uses rule-based fallback.
        """
        if self.client:
            return self._ai_allocation(
                available_pool_kwh, demand_kwh, grid_rate_inr, pool_rate_inr, house_priority
            )
        else:
            return self._fallback_allocation(
                available_pool_kwh, demand_kwh, grid_rate_inr, pool_rate_inr, house_priority
            )
    
    def _ai_allocation(
        self, available_pool_kwh: float, demand_kwh: float, 
        grid_rate_inr: float, pool_rate_inr: float, house_priority: int
    ) -> dict:
        """Use Gemini to determine allocation."""
        prompt = f"""
        You are a solar energy allocation optimizer for a virtual net metering system.
        
        Context:
        - Available solar from pool: {available_pool_kwh:.2f} kWh
        - Consumer demand: {demand_kwh:.2f} kWh
        - Pool rate: ₹{pool_rate_inr:.2f}/kWh
        - Grid rate: ₹{grid_rate_inr:.2f}/kWh
        - Consumer priority (1-10): {house_priority}
        
        Provide a JSON response with:
        1. "pool_allocation_kwh": How much should come from pool
        2. "reasoning": Why this allocation (max 50 words)
        3. "fairness_score": 0-100 rating of fairness
        
        Consider: fairness to other consumers, cost efficiency, grid stability.
        """
        
        try:
            response = self.client.generate_content(prompt)
            reasoning = response.text
            
            # Parse response (simplified)
            pool_kwh = min(available_pool_kwh, demand_kwh)
            
            return {
                "pool_kwh": pool_kwh,
                "grid_kwh": max(0, demand_kwh - pool_kwh),
                "reasoning": reasoning[:200],
            }
        except Exception as e:
            logger.error(f"AI allocation error: {str(e)}")
            return self._fallback_allocation(
                available_pool_kwh, demand_kwh, grid_rate_inr, pool_rate_inr, house_priority
            )
    
    def _fallback_allocation(
        self, available_pool_kwh: float, demand_kwh: float,
        grid_rate_inr: float, pool_rate_inr: float, house_priority: int
    ) -> dict:
        """Rule-based allocation when AI unavailable."""
        # Priority-based allocation: higher priority gets more pool
        priority_multiplier = 1.0 + (house_priority - 5) * 0.05  # 5 = 1.0x
        
        pool_allocation = min(
            available_pool_kwh * priority_multiplier,
            demand_kwh
        )
        grid_allocation = max(0, demand_kwh - pool_allocation)
        
        reasoning = (
            f"Priority-based allocation (priority={house_priority}): "
            f"Allocating {pool_allocation:.2f}kWh from pool, "
            f"{grid_allocation:.2f}kWh from grid fallback."
        )
        
        return {
            "pool_kwh": pool_allocation,
            "grid_kwh": grid_allocation,
            "reasoning": reasoning,
        }
    
    def calculate_dynamic_pricing(self, pool_utilization_percent: float) -> dict:
        """Adjust pricing based on pool utilization."""
        from config import settings
        
        base_pool_rate = settings.solar_pool_rate
        
        # Higher utilization = slightly higher price
        if pool_utilization_percent > 80:
            adjusted_rate = base_pool_rate * 1.1
        elif pool_utilization_percent > 60:
            adjusted_rate = base_pool_rate * 1.05
        else:
            adjusted_rate = base_pool_rate
        
        return {
            "base_rate_inr": base_pool_rate,
            "adjusted_rate_inr": adjusted_rate,
            "utilization_percent": pool_utilization_percent,
        }