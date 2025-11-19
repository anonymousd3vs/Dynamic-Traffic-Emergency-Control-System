"""
Indian Traffic Signal - Sequential Phase System

Phase-based sequential control:
- Phase 1: SOUTH GREEN (35s) - vehicles move from NORTH→SOUTH
- Phase 2: SOUTH YELLOW (5s) - warning
- Phase 3: WEST GREEN (35s) - vehicles move from EAST→WEST
- Phase 4: WEST YELLOW (5s) - warning
- Phase 5: NORTH GREEN (35s) - vehicles move from SOUTH→NORTH
- Phase 6: NORTH YELLOW (5s) - warning
- Phase 7: EAST GREEN (35s) - vehicles move from WEST→EAST
- Phase 8: EAST YELLOW (5s) - warning
- Phase 9: All RED (2s) - safety clearance
- Total cycle: ~168 seconds
"""

from enum import Enum
from typing import Dict, Optional, Callable
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SignalState(Enum):
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    ALL_RED = "ALL_RED"
    EMERGENCY = "EMERGENCY"


SIGNAL_COLORS = {
    SignalState.RED: (255, 0, 0),
    SignalState.YELLOW: (255, 255, 0),
    SignalState.GREEN: (0, 255, 0),
    SignalState.ALL_RED: (128, 0, 0),
    SignalState.EMERGENCY: (0, 255, 0),
}

STATE_DISPLAY_NAMES = {
    SignalState.RED: "STOP",
    SignalState.YELLOW: "SLOW",
    SignalState.GREEN: "GO",
    SignalState.ALL_RED: "ALL STOP",
    SignalState.EMERGENCY: "AMBULANCE",
}


class IndianTrafficSignal:
    """Single direction traffic signal"""

    def __init__(self, lane_id: str, direction: str = None):
        self.lane_id = lane_id
        self.direction = direction or lane_id.upper()
        self.current_state = SignalState.RED
        self.elapsed_time = 0.0
        self.ambulance_active = False
        self.ambulance_confidence = 0.0
        self.ambulance_start_time = None
        self.on_state_change: Optional[Callable] = None
        logger.info(f"Lane {self.lane_id} initialized")

    def set_state(self, state: SignalState, notify: bool = True):
        if state != self.current_state:
            old_state = self.current_state
            self.current_state = state
            self.elapsed_time = 0.0
            logger.debug(
                f"Lane {self.lane_id}: {old_state.value} -> {state.value}")
            if notify and self.on_state_change:
                self.on_state_change(self.lane_id, old_state, state)

    def update(self, delta_time: float = 0.1):
        self.elapsed_time += delta_time

        if self.ambulance_active:
            if self.current_state != SignalState.EMERGENCY:
                self.set_state(SignalState.EMERGENCY)

            if self.ambulance_start_time:
                duration = (datetime.now() -
                            self.ambulance_start_time).total_seconds()
                if duration > 45:
                    self.ambulance_active = False
                    logger.info(f"Lane {self.lane_id}: Ambulance cleared")

    def activate_ambulance(self, confidence: float = 0.95):
        if confidence >= 0.80:
            self.ambulance_active = True
            self.ambulance_confidence = confidence
            self.ambulance_start_time = datetime.now()
            logger.warning(f"Ambulance activated for {self.lane_id}")
            return True
        return False


class IntersectionPhase(Enum):
    PHASE_1 = 1   # SOUTH GREEN
    PHASE_2 = 2   # SOUTH YELLOW
    PHASE_3 = 3   # WEST GREEN
    PHASE_4 = 4   # WEST YELLOW
    PHASE_5 = 5   # NORTH GREEN
    PHASE_6 = 6   # NORTH YELLOW
    PHASE_7 = 7   # EAST GREEN
    PHASE_8 = 8   # EAST YELLOW
    PHASE_9 = 9   # All RED


class IntersectionController:
    """Sequential 4-way intersection controller"""

    def __init__(self):
        self.lanes: Dict[str, IndianTrafficSignal] = {}
        self.is_running = False
        self.current_phase = IntersectionPhase.PHASE_1
        self.phase_elapsed_time = 0.0

        # Phase timings (seconds)
        self.phase_timings = {
            IntersectionPhase.PHASE_1: 35,
            IntersectionPhase.PHASE_2: 5,
            IntersectionPhase.PHASE_3: 35,
            IntersectionPhase.PHASE_4: 5,
            IntersectionPhase.PHASE_5: 35,
            IntersectionPhase.PHASE_6: 5,
            IntersectionPhase.PHASE_7: 35,
            IntersectionPhase.PHASE_8: 5,
            IntersectionPhase.PHASE_9: 2,
        }

        # Phase to direction mapping
        self.phase_directions = {
            IntersectionPhase.PHASE_1: {'state': SignalState.GREEN, 'direction': 'south'},
            IntersectionPhase.PHASE_2: {'state': SignalState.YELLOW, 'direction': 'south'},
            IntersectionPhase.PHASE_3: {'state': SignalState.GREEN, 'direction': 'west'},
            IntersectionPhase.PHASE_4: {'state': SignalState.YELLOW, 'direction': 'west'},
            IntersectionPhase.PHASE_5: {'state': SignalState.GREEN, 'direction': 'north'},
            IntersectionPhase.PHASE_6: {'state': SignalState.YELLOW, 'direction': 'north'},
            IntersectionPhase.PHASE_7: {'state': SignalState.GREEN, 'direction': 'east'},
            IntersectionPhase.PHASE_8: {'state': SignalState.YELLOW, 'direction': 'east'},
            IntersectionPhase.PHASE_9: {'state': SignalState.ALL_RED, 'direction': 'all'},
        }

        self.emergency_active = False
        self.emergency_direction = None
        self.emergency_start_time = None
        # Store phase time when emergency starts
        self.phase_elapsed_before_emergency = 0.0
        self.ambulance_count = 0
        self.completed_ambulances = 0

        logger.info("Intersection controller initialized")

    def add_lane(self, lane_id: str, direction_name: str = None):
        if lane_id not in self.lanes:
            self.lanes[lane_id] = IndianTrafficSignal(lane_id, direction_name)
            logger.info(f"Lane added: {lane_id}")

    def start(self):
        self.is_running = True
        self.current_phase = IntersectionPhase.PHASE_1
        self.phase_elapsed_time = 0.0
        self._update_phase_states()
        logger.info("Intersection controller started")

    def stop(self):
        self.is_running = False
        logger.info("Intersection controller stopped")

    def reset(self):
        self.current_phase = IntersectionPhase.PHASE_1
        self.phase_elapsed_time = 0.0
        self.phase_elapsed_before_emergency = 0.0
        self.emergency_active = False
        self.emergency_direction = None
        self.emergency_start_time = None
        for lane in self.lanes.values():
            lane.ambulance_active = False
        logger.info("Intersection reset")

    def _get_perpendicular_lane(self, lane_id: str) -> str:
        """Get perpendicular lane for given direction"""
        perpendicular_map = {
            'north': 'south',
            'south': 'north',
            'east': 'west',
            'west': 'east'
        }
        return perpendicular_map.get(lane_id, 'south')

    def activate_ambulance(self, direction: str, confidence: float = 0.95):
        if direction not in self.lanes:
            return False

        lane = self.lanes[direction]
        if lane.activate_ambulance(confidence):
            self.ambulance_count += 1
            self.emergency_active = True
            self.emergency_direction = direction
            self.emergency_start_time = datetime.now()
            self.phase_elapsed_before_emergency = self.phase_elapsed_time  # Save current phase time
            self.phase_elapsed_time = 0.0  # Reset timer for emergency countdown
            logger.warning(f"Ambulance priority activated for {direction}")
            return True
        return False

    def _update_phase_states(self):
        """Update all lane states based on current phase"""
        for lane_id, lane in self.lanes.items():
            if lane.ambulance_active:
                # Ambulance lane gets EMERGENCY
                lane.set_state(SignalState.EMERGENCY, notify=False)
            elif self.emergency_active and self.emergency_direction:
                # During emergency: perpendicular lane gets GREEN to clear ambulance
                perpendicular = self._get_perpendicular_lane(
                    self.emergency_direction)
                if lane_id == perpendicular:
                    lane.set_state(SignalState.GREEN, notify=False)
                else:
                    lane.set_state(SignalState.RED, notify=False)
            else:
                # Normal phase operation
                phase_config = self.phase_directions[self.current_phase]
                target_direction = phase_config['direction']
                state = phase_config['state']

                if target_direction == 'all':
                    lane.set_state(SignalState.ALL_RED, notify=False)
                elif lane_id == target_direction:
                    lane.set_state(state, notify=False)
                else:
                    lane.set_state(SignalState.RED, notify=False)

    def update(self, delta_time: float = 0.1):
        if not self.is_running:
            return

        for lane in self.lanes.values():
            lane.update(delta_time)

        if self.emergency_active and self.emergency_start_time:
            duration = (datetime.now() -
                        self.emergency_start_time).total_seconds()
            if duration > 45:
                self.emergency_active = False
                self.emergency_direction = None
                self.completed_ambulances += 1
                # Resume phase from saved time instead of resetting to 0
                self.phase_elapsed_time = self.phase_elapsed_before_emergency
                logger.info("Emergency cleared - phase resumed")

        # Only advance phases if no emergency is active
        if not self.emergency_active:
            self.phase_elapsed_time += delta_time
            phase_duration = self.phase_timings[self.current_phase]

            if self.phase_elapsed_time >= phase_duration:
                self.phase_elapsed_time = 0.0
                phases = list(IntersectionPhase)
                current_index = phases.index(self.current_phase)
                next_index = (current_index + 1) % len(phases)
                self.current_phase = phases[next_index]

        self._update_phase_states()

    def get_statistics(self) -> Dict:
        return {
            'total_ambulances': self.ambulance_count,
            'completed_ambulances': self.completed_ambulances,
            'current_phase': self.current_phase.name,
            'is_running': self.is_running,
        }

    def get_status(self) -> Dict:
        status = {}
        for lane_id, lane in self.lanes.items():
            status[lane_id] = {
                'state': lane.current_state.value,
                'elapsed': lane.elapsed_time,
                'ambulance': lane.ambulance_active,
            }
        return status
