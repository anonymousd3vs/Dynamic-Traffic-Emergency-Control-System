"""
Dynamic Timing Integration Layer
SINGLE-LANE MODE: Dynamic timing only for selected lane.
Other lanes use DEFAULT 35 seconds.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from traffic_signals.core.dynamic_timing import DynamicTimingCalculator, CongestionLevel
from traffic_signals.core.indian_traffic_signal import IntersectionController

logger = logging.getLogger(__name__)


class DynamicTimingIntegration:
    """
    Bridges vehicle detection and traffic signal timing.
    SINGLE-LANE MODE: Only the selected lane gets dynamic timing.

    Real-time Operation:
    1. User selects lane (e.g., EAST) in Automatic Mode
    2. Detection counts vehicles in selected lane
    3. Calculate optimal timing for that lane
    4. Apply dynamic timing to that lane's phase
    5. Other directions use DEFAULT 35 seconds
    6. Frontend shows adjusted timing in real-time
    """

    # Mapping: Selected Lane → Signal Phase
    LANE_MAPPING = {
        'north': {
            'detection_zone': 'NORTH',
            'signal_phase': 'PHASE_5',  # NORTH GREEN
        },
        'south': {
            'detection_zone': 'SOUTH',
            'signal_phase': 'PHASE_1',  # SOUTH GREEN
        },
        'east': {
            'detection_zone': 'EAST',
            'signal_phase': 'PHASE_7',  # EAST GREEN
        },
        'west': {
            'detection_zone': 'WEST',
            'signal_phase': 'PHASE_3',  # WEST GREEN
        },
    }

    def __init__(self, signal_controller: IntersectionController):
        """Initialize dynamic timing integration."""
        self.signal_controller = signal_controller
        self.selected_lane: Optional[str] = None
        self.dynamic_timing_enabled = False
        self.timing_calculator: Optional[DynamicTimingCalculator] = None
        self.vehicle_count_selected_lane = 0
        self.timing_updates = 0
        self.last_update_timestamp = None
        self.vehicle_count_history = []

        logger.info("✅ Dynamic Timing Integration initialized")
        logger.info("   SINGLE-LANE MODE: Waiting for lane selection")

    def select_lane(self, lane: str) -> Dict:
        """Select a lane for dynamic timing."""
        if lane not in self.LANE_MAPPING:
            return {
                'status': 'error',
                'message': f'Invalid lane: {lane}'
            }

        self.selected_lane = lane
        self.dynamic_timing_enabled = True
        self.vehicle_count_selected_lane = 0
        self.timing_calculator = DynamicTimingCalculator(
            base_cycle_time=90,
            min_green=15,
            max_green=60,
            yellow_duration=4,
            smoothing_enabled=True,
            smoothing_window=5
        )

        mapping = self.LANE_MAPPING[lane]
        logger.info(f"\n🎯 LANE SELECTED: {lane.upper()}")
        logger.info(f"  Detection Zone: {mapping['detection_zone']}")
        logger.info(f"  Signal Phase: {mapping['signal_phase']}")
        logger.info(f"  Other directions: DEFAULT 35 seconds\n")

        return {
            'status': 'success',
            'selected_lane': lane,
            'detection_zone': mapping['detection_zone'],
            'signal_phase': mapping['signal_phase']
        }

    def update_vehicle_count(self, vehicle_count: int) -> Dict:
        """Update vehicle count for selected lane and adjust timing."""
        if not self.selected_lane or not self.dynamic_timing_enabled:
            return {
                'status': 'error',
                'message': 'No lane selected'
            }

        old_count = self.vehicle_count_selected_lane
        self.vehicle_count_selected_lane = max(0, vehicle_count)

        self.vehicle_count_history.append({
            'timestamp': datetime.now(),
            'count': vehicle_count
        })

        if abs(vehicle_count - old_count) > 1:
            logger.info(
                f"🚗 {self.selected_lane.upper()}: {old_count} → {vehicle_count} vehicles")

        timing = self._calculate_and_apply_timing(vehicle_count)

        return {
            'status': 'success',
            'selected_lane': self.selected_lane,
            'vehicle_count': vehicle_count,
            'timing': timing,
        }

    def _calculate_and_apply_timing(self, vehicle_count: int) -> Dict:
        """Calculate optimal timing and apply to signal controller."""
        if not self.timing_calculator:
            return {}

        timing_config = self.timing_calculator.calculate_timing(vehicle_count)
        green_time = timing_config['green_duration']
        congestion = timing_config['congestion_level']

        self._apply_timing_to_controller(green_time)

        logger.info(
            f"✅ {self.selected_lane.upper()}: {vehicle_count} vehicles → "
            f"GREEN: {green_time}s ({congestion})"
        )

        self.timing_updates += 1
        self.last_update_timestamp = datetime.now()

        return {
            'green_duration': green_time,
            'yellow_duration': timing_config['yellow_duration'],
            'congestion_level': congestion,
        }

    def _apply_timing_to_controller(self, green_time: int) -> None:
        """Apply timing to signal controller."""
        if not self.selected_lane:
            return

        try:
            if not hasattr(self.signal_controller, 'phase_timings'):
                return

            mapping = self.LANE_MAPPING[self.selected_lane]
            phase_key = mapping['signal_phase']

            if phase_key in self.signal_controller.phase_timings:
                old_timing = self.signal_controller.phase_timings[phase_key]
                self.signal_controller.phase_timings[phase_key] = green_time

                if old_timing != green_time:
                    logger.debug(
                        f"📡 {self.selected_lane.upper()} GREEN: {old_timing}s → {green_time}s"
                    )

        except Exception as e:
            logger.error(f"Error applying timing: {e}")

    def get_current_status(self) -> Dict:
        """Get current status."""
        if not self.selected_lane:
            return {'selected_lane': None, 'vehicle_count': 0}

        status = {
            'timestamp': datetime.now().isoformat(),
            'selected_lane': self.selected_lane,
            'vehicle_count': self.vehicle_count_selected_lane,
            'total_updates': self.timing_updates,
            'phase_timings': dict(self.signal_controller.phase_timings),
        }

        if self.timing_calculator and self.timing_calculator.last_calculated_timing:
            status['timing'] = {
                'green': self.timing_calculator.last_calculated_timing.green_duration,
                'congestion': self.timing_calculator.last_calculated_timing.congestion_level.value,
            }

        return status

    def get_statistics(self) -> Dict:
        """Get statistics."""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'selected_lane': self.selected_lane,
            'total_timing_updates': self.timing_updates,
            'vehicle_count_history': [
                {'timestamp': h['timestamp'].isoformat(), 'count': h['count']}
                for h in self.vehicle_count_history[-20:]
            ]
        }

        if self.timing_calculator:
            calc_stats = self.timing_calculator.get_statistics()
            stats['lane_statistics'] = calc_stats

        return stats

    def reset_selection(self) -> None:
        """Reset selection."""
        self.selected_lane = None
        self.dynamic_timing_enabled = False
        self.timing_calculator = None
        self.vehicle_count_selected_lane = 0
        self.timing_updates = 0
        self.vehicle_count_history = []
        logger.info("🔄 Dynamic timing reset")

    def __repr__(self) -> str:
        """String representation."""
        if not self.selected_lane:
            return "DynamicTimingIntegration(not_selected)"
        return f"DynamicTimingIntegration(selected={self.selected_lane}, vehicles={self.vehicle_count_selected_lane})"
