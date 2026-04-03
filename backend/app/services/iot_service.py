"""
IoT Device Service - manages real-time IoT device data
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class IoTService:
    """Service for managing IoT device status data."""

    def __init__(self):
        self.device_status: Dict[str, Dict[str, Any]] = {}
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

    def get_device_status(self, house_id: str) -> Dict[str, Any]:
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

    def reset_cumulative(self, house_id: str):
        """Reset cumulative generation for a house (for testing)."""
        self.cumulative_generation[house_id] = 0.0
        logger.info(f"Reset cumulative generation for {house_id}")

# Global IoT service instance
iot_service = IoTService()