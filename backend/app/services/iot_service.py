"""
IoT Device Service - manages real-time IoT device data
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IoTService:
    """Service for managing IoT device status data."""

    def __init__(self):
        self.device_status: Dict[str, Dict[str, Any]] = {}
        self.buyer_demand: Dict[str, Dict[str, Any]] = {}  # Track buyer demand from IoT
        self.cumulative_generation: Dict[str, float] = {}  # Track total kWh per house
        self.last_generation_time: Dict[str, datetime] = {}  # Track last update time

    def update_device_status(self, house_id: str, device_id: str, generation_kwh: float, signal_strength: int):
        """Update IoT device status and accumulate generation."""
        current_time = datetime.utcnow()

        # Initialize cumulative generation if not exists
        if house_id not in self.cumulative_generation:
            self.cumulative_generation[house_id] = 0.0

        # Calculate energy generated since last update (simple approximation)
        # Assuming updates come every ~5 seconds, we can accumulate based on current generation
        if house_id in self.last_generation_time:
            time_diff = (current_time - self.last_generation_time[house_id]).total_seconds()
            # Accumulate energy: generation_kwh is current power, so energy = power * time
            # But since generation_kwh from ESP32 is already in kWh (instantaneous?), 
            # let's accumulate the reported values directly for now
            # In a real system, we'd calculate: energy += (current_power_kW * time_diff_hours)
            pass  # For now, we'll accumulate the reported generation values

        # For simplicity, accumulate the generation_kwh values sent by ESP32
        # This assumes ESP32 sends cumulative kWh, but actually it sends current generation
        # Let's modify this to accumulate properly
        if house_id in self.device_status:
            previous_generation = self.device_status[house_id].get('generation_kwh', 0)
            # If generation increased, add the difference to cumulative
            if generation_kwh > previous_generation:
                energy_generated = generation_kwh - previous_generation
                self.cumulative_generation[house_id] += energy_generated
                logger.info(f"Accumulated {energy_generated:.3f} kWh for {house_id}, total: {self.cumulative_generation[house_id]:.3f} kWh")

        self.last_generation_time[house_id] = current_time

        current_time_str = current_time.isoformat() + "Z"
        self.device_status[house_id] = {
            "device_id": device_id,
            "generation_kwh": generation_kwh,
            "signal_strength": signal_strength,
            "last_update": current_time_str,
            "status": "online",
            "cumulative_kwh": self.cumulative_generation[house_id]
        }

        logger.info(f"Updated IoT status for {house_id}: {generation_kwh} kW (cumulative: {self.cumulative_generation[house_id]:.3f} kWh)")

    def update_buyer_demand(self, house_id: str, demand_kwh: float, device_id: str):
        """Update buyer demand from IoT device (potentiometer-based)."""
        current_time = datetime.utcnow()
        current_time_str = current_time.isoformat() + "Z"
        
        self.buyer_demand[house_id] = {
            "device_id": device_id,
            "demand_kwh": demand_kwh,
            "last_update": current_time_str,
            "status": "active" if demand_kwh > 0.1 else "idle",
        }
        
        logger.info(f"[IoTService] ✓ Stored buyer_demand: house={house_id}, demand={demand_kwh}kWh, update_time={current_time_str}")
        logger.debug(f"[IoTService] Full buyer_demand dict: {self.buyer_demand}")

    def get_buyer_demand(self, house_id: str) -> Optional[Dict[str, Any]]:
        """Get current buyer demand for a house."""
        result = self.buyer_demand.get(house_id)
        logger.debug(f"[IoTService] get_buyer_demand({house_id}): found={result is not None}")
        if result:
            logger.debug(f"[IoTService]   Data: {result}")
        return result

    def get_active_buyer_demand(self, house_id: str, max_age_seconds: int = 30) -> float:
        """Get buyer demand if the latest update is recent enough."""
        status = self.buyer_demand.get(house_id)
        if not status:
            return 0.0

        try:
            last_update = datetime.fromisoformat(status.get("last_update", "").replace("Z", "+00:00"))
            age_seconds = (datetime.utcnow() - last_update.replace(tzinfo=None)).total_seconds()
            if age_seconds <= max_age_seconds:
                return float(status.get("demand_kwh", 0.0) or 0.0)
        except Exception:
            return 0.0

        return 0.0

    def get_device_status(self, house_id: str) -> Optional[Dict[str, Any]]:
        """Get IoT device status for a house."""
        return self.device_status.get(house_id)

    def get_generation(self, house_id: str) -> float:
        """Get current generation for a house."""
        status = self.get_device_status(house_id)
        if status and status.get('status') == 'online':
            return status.get('generation_kwh', 0)
        return 0

    def get_cumulative_generation(self, house_id: str) -> float:
        """Get cumulative generation for a house."""
        return self.cumulative_generation.get(house_id, 0)

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get all device statuses (for debugging)."""
        return self.device_status

    def get_all_buyer_demand(self) -> Dict[str, Dict[str, Any]]:
        """Get all buyer demand states (for debugging and pool sync)."""
        return self.buyer_demand

    def reset_cumulative(self, house_id: str):
        """Reset cumulative generation for a house (for testing)."""
        self.cumulative_generation[house_id] = 0.0
        logger.info(f"Reset cumulative generation for {house_id}")

# Global IoT service instance
iot_service = IoTService()