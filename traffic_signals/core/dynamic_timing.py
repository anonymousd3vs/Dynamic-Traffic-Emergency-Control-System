"""
Dynamic Traffic Signal Timing Controller
Adjusts signal timing based on real-time vehicle congestion levels
"""

import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CongestionLevel(Enum):
    """Traffic congestion levels"""
    NONE = "NONE"           # No vehicles
    LOW = "LOW"             # Few vehicles
    MODERATE = "MODERATE"   # Normal traffic
    HIGH = "HIGH"           # Heavy traffic
    CRITICAL = "CRITICAL"   # Very heavy traffic


@dataclass
class TimingConfig:
    """Signal timing configuration"""
    green_duration: int
    yellow_duration: int
    red_duration: int
    congestion_level: CongestionLevel
    vehicle_count: int
    timestamp: datetime


class DynamicTimingCalculator:
    """
    Calculates dynamic signal timing based on vehicle congestion.

    ✅ Simple Congestion-Based Timing for Single Zone

    Algorithm:
    - Monitors vehicle count in zone
    - Higher vehicles = Longer GREEN time
    - Lower vehicles = Shorter GREEN time
    - Automatically adjusts signal timing

    Example:
        >>> calculator = DynamicTimingCalculator(
        ...     base_cycle_time=90,  # Total cycle time
        ...     min_green=15,        # Minimum green duration
        ...     max_green=60         # Maximum green duration
        ... )
        >>> 
        >>> # Calculate timing for 12 vehicles
        >>> timing = calculator.calculate_timing(vehicle_count=12)
        >>> print(timing)
        {
            'green_duration': 35,
            'yellow_duration': 4,
            'red_duration': 51,
            'vehicle_count': 12,
            'congestion_level': 'MODERATE',
            'reason': '🟠 Moderate traffic - normal green'
        }
    """

    # Congestion thresholds for single zone
    VEHICLE_THRESHOLDS = {
        0: (CongestionLevel.NONE, 15),           # 0 vehicles: 15s green
        1: (CongestionLevel.LOW, 20),            # 1-5 vehicles: 20s green
        6: (CongestionLevel.MODERATE, 35),       # 6-15 vehicles: 35s green
        16: (CongestionLevel.HIGH, 50),          # 16-30 vehicles: 50s green
        # 31+ vehicles: 60s green (max)
        31: (CongestionLevel.CRITICAL, 60),
    }

    # Reason messages for each level
    REASON_MESSAGES = {
        CongestionLevel.NONE: "🟢 No traffic - minimum green",
        CongestionLevel.LOW: "🟡 Light traffic - short green",
        CongestionLevel.MODERATE: "🟠 Moderate traffic - normal green",
        CongestionLevel.HIGH: "🔴 Heavy traffic - extended green",
        CongestionLevel.CRITICAL: "🔴🔴 Very heavy traffic - maximum green",
    }

    def __init__(
        self,
        base_cycle_time: int = 90,
        min_green: int = 15,
        max_green: int = 60,
        yellow_duration: int = 4,
        smoothing_enabled: bool = True,
        smoothing_window: int = 5
    ):
        """
        Initialize dynamic timing calculator

        Args:
            base_cycle_time: Total cycle time in seconds (green + yellow + red)
            min_green: Minimum green duration in seconds
            max_green: Maximum green duration in seconds
            yellow_duration: Fixed yellow duration in seconds
            smoothing_enabled: Enable smoothing to prevent rapid timing changes
            smoothing_window: Number of samples to smooth over
        """
        self.base_cycle_time = base_cycle_time
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_duration = yellow_duration
        self.smoothing_enabled = smoothing_enabled
        self.smoothing_window = smoothing_window

        # Smoothing buffer to prevent rapid changes
        self.timing_history: list = []
        self.vehicle_count_history: list = []
        self.last_calculated_timing: Optional[TimingConfig] = None

        logger.info(
            f"DynamicTimingCalculator initialized: "
            f"cycle_time={base_cycle_time}s, "
            f"green={min_green}-{max_green}s"
        )

    def calculate_timing(self, vehicle_count: int) -> Dict:
        """
        Calculate signal timing based on vehicle count

        Args:
            vehicle_count: Number of vehicles in zone

        Returns:
            Dictionary with timing configuration:
            {
                'green_duration': 35,
                'yellow_duration': 4,
                'red_duration': 51,
                'vehicle_count': 12,
                'congestion_level': 'MODERATE',
                'reason': '🟠 Moderate traffic - normal green'
            }
        """
        # Determine congestion level and base green time
        congestion_level, suggested_green = self._get_congestion_level_and_timing(
            vehicle_count
        )

        # Apply smoothing if enabled
        if self.smoothing_enabled:
            final_green = self._apply_smoothing(suggested_green, vehicle_count)
        else:
            final_green = suggested_green

        # Ensure within bounds
        final_green = max(self.min_green, min(self.max_green, final_green))

        # Calculate red duration (remaining cycle time)
        red_duration = self.base_cycle_time - final_green - self.yellow_duration

        # Create timing config
        timing_config = TimingConfig(
            green_duration=final_green,
            yellow_duration=self.yellow_duration,
            red_duration=max(10, red_duration),  # Ensure minimum red time
            congestion_level=congestion_level,
            vehicle_count=vehicle_count,
            timestamp=datetime.now()
        )

        # Update history for smoothing
        self.timing_history.append(final_green)
        if len(self.timing_history) > self.smoothing_window * 2:
            self.timing_history = self.timing_history[-self.smoothing_window * 2:]

        self.vehicle_count_history.append(vehicle_count)
        if len(self.vehicle_count_history) > self.smoothing_window * 2:
            self.vehicle_count_history = self.vehicle_count_history[-self.smoothing_window * 2:]

        # Store last calculated timing
        self.last_calculated_timing = timing_config

        return {
            'green_duration': timing_config.green_duration,
            'yellow_duration': timing_config.yellow_duration,
            'red_duration': timing_config.red_duration,
            'vehicle_count': timing_config.vehicle_count,
            'congestion_level': timing_config.congestion_level.value,
            'reason': self.REASON_MESSAGES[congestion_level]
        }

    def _get_congestion_level_and_timing(
        self,
        vehicle_count: int
    ) -> Tuple[CongestionLevel, int]:
        """
        Determine congestion level and suggested green time

        Args:
            vehicle_count: Number of vehicles

        Returns:
            Tuple of (CongestionLevel, suggested_green_time)
        """
        # Find the appropriate threshold
        congestion_level = CongestionLevel.NONE
        suggested_green = self.min_green

        for threshold, (level, green_time) in sorted(
            self.VEHICLE_THRESHOLDS.items(),
            reverse=True
        ):
            if vehicle_count >= threshold:
                congestion_level = level
                suggested_green = green_time
                break

        return congestion_level, suggested_green

    def _apply_smoothing(self, suggested_green: int, vehicle_count: int) -> int:
        """
        Apply smoothing to prevent rapid timing changes

        Args:
            suggested_green: Newly calculated green time
            vehicle_count: Current vehicle count

        Returns:
            Smoothed green time
        """
        if not self.timing_history:
            return suggested_green

        # Get previous green time
        prev_green = self.timing_history[-1]

        # Maximum change allowed per update (seconds)
        max_change_per_step = 5

        # Don't jump too much from previous value
        if abs(suggested_green - prev_green) > max_change_per_step:
            # Gradually increase or decrease
            if suggested_green > prev_green:
                smoothed_green = prev_green + max_change_per_step
            else:
                smoothed_green = prev_green - max_change_per_step
        else:
            smoothed_green = suggested_green

        return smoothed_green

    def get_statistics(self) -> Dict:
        """
        Get statistics about timing adjustments

        Returns:
            Statistics dictionary
        """
        avg_vehicle_count = (
            sum(self.vehicle_count_history) / len(self.vehicle_count_history)
            if self.vehicle_count_history else 0
        )
        avg_green_time = (
            sum(self.timing_history) / len(self.timing_history)
            if self.timing_history else self.min_green
        )

        return {
            'average_vehicle_count': round(avg_vehicle_count, 2),
            'average_green_duration': round(avg_green_time, 2),
            'min_green_observed': min(self.timing_history) if self.timing_history else self.min_green,
            'max_green_observed': max(self.timing_history) if self.timing_history else self.max_green,
            'total_adjustments': len(self.timing_history),
            'history_samples': len(self.vehicle_count_history)
        }

    def reset_history(self):
        """Reset timing history and statistics"""
        self.timing_history.clear()
        self.vehicle_count_history.clear()
        self.last_calculated_timing = None
        logger.info("DynamicTimingCalculator history reset")

    def __repr__(self) -> str:
        """String representation"""
        stats = self.get_statistics()
        return (
            f"DynamicTimingCalculator(cycle={self.base_cycle_time}s, "
            f"green={self.min_green}-{self.max_green}s, "
            f"avg_vehicles={stats['average_vehicle_count']:.1f})"
        )


class MultiZoneDynamicTiming:
    """
    Advanced: Manage dynamic timing for multiple zones/lanes

    Future enhancement for multi-zone coordination.
    """

    def __init__(self):
        """Initialize multi-zone timing manager"""
        self.zones: Dict[str, DynamicTimingCalculator] = {}
        logger.info("MultiZoneDynamicTiming initialized")

    def add_zone(
        self,
        zone_id: str,
        base_cycle_time: int = 90,
        min_green: int = 15,
        max_green: int = 60
    ) -> DynamicTimingCalculator:
        """
        Add a new zone for dynamic control

        Args:
            zone_id: Unique zone identifier
            base_cycle_time: Total cycle time for this zone
            min_green: Minimum green duration
            max_green: Maximum green duration

        Returns:
            DynamicTimingCalculator for this zone
        """
        calculator = DynamicTimingCalculator(
            base_cycle_time=base_cycle_time,
            min_green=min_green,
            max_green=max_green
        )
        self.zones[zone_id] = calculator
        logger.info(f"Zone {zone_id} added to dynamic timing manager")
        return calculator

    def calculate_timing_for_zone(self, zone_id: str, vehicle_count: int) -> Optional[Dict]:
        """
        Calculate timing for specific zone

        Args:
            zone_id: Zone identifier
            vehicle_count: Vehicle count in zone

        Returns:
            Timing configuration or None if zone not found
        """
        if zone_id not in self.zones:
            logger.warning(f"Zone {zone_id} not found")
            return None

        return self.zones[zone_id].calculate_timing(vehicle_count)

    def get_all_zones_status(self) -> Dict[str, Dict]:
        """Get status of all zones"""
        return {
            zone_id: calculator.get_statistics()
            for zone_id, calculator in self.zones.items()
        }
