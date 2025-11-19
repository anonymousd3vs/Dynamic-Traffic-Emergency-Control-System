"""
Traffic Signal State Machine
Manages traffic light states with emergency override capability
"""

from enum import Enum
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional, Callable

logger = logging.getLogger(__name__)


class SignalState(Enum):
    """Traffic signal states"""
    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    EMERGENCY = "EMERGENCY"  # Special mode for ambulances


class SignalStateMachine:
    """
    Traffic signal state machine with emergency priority

    Normal Cycle: RED -> GREEN -> YELLOW -> RED
    Emergency: Any State -> EMERGENCY -> Resume normal cycle

    Example:
        >>> signal = SignalStateMachine(
        ...     signal_id="signal_north",
        ...     green_duration=30,
        ...     yellow_duration=4,
        ...     red_duration=34
        ... )
        >>> signal.start()
        >>> signal.activate_emergency()
        >>> # ... 45 seconds later ...
        >>> signal.reset_to_normal()
    """

    def __init__(
        self,
        signal_id: str,
        green_duration: int = 30,
        yellow_duration: int = 4,
        red_duration: int = 34,
        all_red_clearance: int = 3,
        emergency_duration: int = 45,
        on_state_change: Optional[Callable] = None
    ):
        """
        Initialize signal state machine

        Args:
            signal_id: Unique identifier for this signal
            green_duration: Green light duration in seconds
            yellow_duration: Yellow light duration in seconds
            red_duration: Red light duration in seconds
            all_red_clearance: All-red clearance time in seconds
            emergency_duration: Duration to stay in emergency mode (seconds)
            on_state_change: Callback function when state changes
        """
        self.signal_id = signal_id
        self.green_duration = green_duration
        self.yellow_duration = yellow_duration
        self.red_duration = red_duration
        self.all_red_clearance = all_red_clearance
        self.emergency_duration = emergency_duration
        self.on_state_change = on_state_change

        # Current state
        self.current_state = SignalState.RED
        self.state_start_time = None
        self.is_running = False

        # Emergency mode tracking
        self.emergency_active = False
        self.emergency_start_time = None
        self.emergency_reason = ""

        # State history for debugging
        self.state_history = []

        logger.info(f"Signal {signal_id} initialized")
        logger.info(
            f"  Green: {green_duration}s, Yellow: {yellow_duration}s, Red: {red_duration}s")

    def start(self):
        """Start the signal from RED state"""
        if not self.is_running:
            self.is_running = True
            self.current_state = SignalState.RED
            self.state_start_time = datetime.now()
            self._log_state_change("START")
            if self.on_state_change:
                self.on_state_change(self.signal_id, self.current_state)
            logger.info(f"Signal {self.signal_id} started")

    def stop(self):
        """Stop the signal"""
        if self.is_running:
            self.is_running = False
            self._log_state_change("STOP")
            logger.info(f"Signal {self.signal_id} stopped")

    def activate_emergency(self, reason: str = "Ambulance detected"):
        """
        Activate emergency mode (green light for ambulance)

        Args:
            reason: Reason for emergency activation
        """
        if not self.is_running:
            logger.warning(
                f"Cannot activate emergency on stopped signal {self.signal_id}")
            return False

        if not self.emergency_active:
            self.emergency_active = True
            self.emergency_reason = reason
            self.emergency_start_time = datetime.now()

            # Save previous state in case we need it
            self.previous_state = self.current_state
            self.previous_state_time = self.state_start_time

            # Switch to emergency (green light for ambulance)
            self.current_state = SignalState.EMERGENCY
            self.state_start_time = datetime.now()

            self._log_state_change(f"EMERGENCY ({reason})")
            if self.on_state_change:
                self.on_state_change(self.signal_id, self.current_state)

            logger.warning(
                f"🚨 Signal {self.signal_id} EMERGENCY MODE activated: {reason}")
            return True

        return False

    def reset_to_normal(self):
        """Reset from emergency to normal operation"""
        if self.emergency_active:
            self.emergency_active = False

            # Resume normal cycle from RED state
            self.current_state = SignalState.RED
            self.state_start_time = datetime.now()

            self._log_state_change("RESET_TO_NORMAL")
            if self.on_state_change:
                self.on_state_change(self.signal_id, self.current_state)

            logger.info(f"Signal {self.signal_id} reset to normal operation")
            return True

        return False

    def update(self) -> SignalState:
        """
        Update signal state based on elapsed time
        Should be called periodically (every 100-500ms)

        Returns:
            Current signal state
        """
        if not self.is_running or not self.state_start_time:
            return self.current_state

        elapsed = (datetime.now() - self.state_start_time).total_seconds()
        new_state = self.current_state

        # Emergency mode handling
        if self.emergency_active:
            if elapsed >= self.emergency_duration:
                # Emergency duration expired, reset to normal
                self.reset_to_normal()
                new_state = SignalState.RED
            else:
                # Stay in emergency (green light)
                new_state = SignalState.EMERGENCY

        # Normal cycle handling
        else:
            if self.current_state == SignalState.RED:
                if elapsed >= self.red_duration:
                    new_state = SignalState.GREEN

            elif self.current_state == SignalState.GREEN:
                if elapsed >= self.green_duration:
                    new_state = SignalState.YELLOW

            elif self.current_state == SignalState.YELLOW:
                if elapsed >= self.yellow_duration:
                    new_state = SignalState.RED

        # State changed
        if new_state != self.current_state:
            self.current_state = new_state
            self.state_start_time = datetime.now()
            self._log_state_change()
            if self.on_state_change:
                self.on_state_change(self.signal_id, self.current_state)

        return self.current_state

    def get_state_info(self) -> Dict:
        """
        Get detailed state information

        Returns:
            Dictionary with signal state details
        """
        elapsed = 0
        if self.state_start_time:
            elapsed = (datetime.now() - self.state_start_time).total_seconds()

        # Get time remaining for current state
        time_remaining = 0
        if self.current_state == SignalState.GREEN:
            time_remaining = max(0, self.green_duration - elapsed)
        elif self.current_state == SignalState.YELLOW:
            time_remaining = max(0, self.yellow_duration - elapsed)
        elif self.current_state == SignalState.RED:
            time_remaining = max(0, self.red_duration - elapsed)
        elif self.current_state == SignalState.EMERGENCY:
            time_remaining = max(0, self.emergency_duration - elapsed)

        # Emergency info
        emergency_remaining = 0
        if self.emergency_active and self.emergency_start_time:
            emergency_remaining = max(
                0,
                self.emergency_duration -
                (datetime.now() - self.emergency_start_time).total_seconds()
            )

        return {
            'signal_id': self.signal_id,
            'current_state': self.current_state.value,
            'is_running': self.is_running,
            'elapsed_seconds': round(elapsed, 2),
            'time_remaining': round(time_remaining, 2),
            'emergency_active': self.emergency_active,
            'emergency_reason': self.emergency_reason if self.emergency_active else "",
            'emergency_remaining': round(emergency_remaining, 2),
            'timestamp': datetime.now().isoformat()
        }

    def _log_state_change(self, context: str = ""):
        """Log state change to history"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'state': self.current_state.value,
            'context': context
        }
        self.state_history.append(entry)

        # Keep only last 1000 entries
        if len(self.state_history) > 1000:
            self.state_history = self.state_history[-1000:]

    def get_state_history(self, limit: int = 20) -> list:
        """Get recent state change history"""
        return self.state_history[-limit:]

    def __str__(self) -> str:
        """String representation"""
        info = self.get_state_info()
        return (
            f"Signal({self.signal_id}): {info['current_state']} "
            f"({info['time_remaining']:.1f}s remaining)"
        )


# Color mapping for signal visualization
SIGNAL_COLORS = {
    SignalState.RED: (255, 0, 0),          # Red
    SignalState.YELLOW: (255, 255, 0),    # Yellow
    SignalState.GREEN: (0, 255, 0),       # Green
    SignalState.EMERGENCY: (0, 255, 0),   # Green (ambulance gets green light)
}

# State display names
STATE_DISPLAY_NAMES = {
    SignalState.RED: "🔴 RED",
    SignalState.YELLOW: "🟡 YELLOW",
    SignalState.GREEN: "🟢 GREEN",
    SignalState.EMERGENCY: "🚨 EMERGENCY (GREEN)",
}
