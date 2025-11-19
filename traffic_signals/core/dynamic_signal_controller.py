"""
Dynamic Signal Controller
Integrates dynamic timing calculator with traffic signal state machine
"""

import logging
from typing import Dict, Optional, Callable
from datetime import datetime
from .signal_state_machine import SignalStateMachine
from .dynamic_timing import DynamicTimingCalculator

logger = logging.getLogger(__name__)


class DynamicSignalController:
    """
    Bridges dynamic timing calculator and signal state machine.

    Automatically adjusts signal timing based on vehicle congestion.

    Workflow:
    1. Monitor vehicle count in zone (from detection system)
    2. Calculate optimal signal timing (DynamicTimingCalculator)
    3. Apply timing to signal state machine (SignalStateMachine)
    4. Signal automatically transitions with new timing

    Example:
        >>> # Create controller
        >>> controller = DynamicSignalController(
        ...     signal_id="signal_north",
        ...     base_cycle_time=90
        ... )
        >>> 
        >>> # Start the signal
        >>> controller.start()
        >>> 
        >>> # Monitor zone, get vehicle count from detection
        >>> vehicle_count = 12  # From detection system
        >>> 
        >>> # Update signal with new vehicle count
        >>> controller.update_vehicle_count(vehicle_count)
        >>> 
        >>> # Periodically call update() to apply timing changes
        >>> controller.update()
        >>> 
        >>> # Check status
        >>> status = controller.get_status()
    """

    def __init__(
        self,
        signal_id: str,
        base_cycle_time: int = 90,
        min_green: int = 15,
        max_green: int = 60,
        yellow_duration: int = 4,
        smoothing_enabled: bool = True,
        on_timing_change: Optional[Callable] = None
    ):
        """
        Initialize dynamic signal controller

        Args:
            signal_id: Unique signal identifier
            base_cycle_time: Total cycle time in seconds
            min_green: Minimum green duration in seconds
            max_green: Maximum green duration in seconds
            yellow_duration: Fixed yellow duration in seconds
            smoothing_enabled: Enable smoothing to prevent rapid changes
            on_timing_change: Callback when timing changes (receives timing dict)
        """
        self.signal_id = signal_id
        self.on_timing_change = on_timing_change

        # Create timing calculator
        self.timing_calculator = DynamicTimingCalculator(
            base_cycle_time=base_cycle_time,
            min_green=min_green,
            max_green=max_green,
            yellow_duration=yellow_duration,
            smoothing_enabled=smoothing_enabled
        )

        # Create signal state machine with initial timing
        initial_timing = self.timing_calculator.calculate_timing(0)
        self.signal = SignalStateMachine(
            signal_id=signal_id,
            green_duration=initial_timing['green_duration'],
            yellow_duration=initial_timing['yellow_duration'],
            red_duration=initial_timing['red_duration'],
            on_state_change=self._on_signal_state_change
        )

        # Vehicle count tracking
        self.current_vehicle_count = 0
        self.last_update_time = None
        self.last_timing_update_time = None
        self.timing_updates_count = 0

        # Timing change history
        self.timing_change_history: list = []

        logger.info(f"DynamicSignalController initialized for {signal_id}")

    def start(self):
        """Start the signal"""
        self.signal.start()
        self.last_update_time = datetime.now()
        logger.info(f"Dynamic signal {self.signal_id} started")

    def stop(self):
        """Stop the signal"""
        self.signal.stop()
        logger.info(f"Dynamic signal {self.signal_id} stopped")

    def update_vehicle_count(self, vehicle_count: int) -> bool:
        """
        Update vehicle count in monitored zone

        Args:
            vehicle_count: Number of vehicles detected in zone

        Returns:
            True if timing was updated, False otherwise
        """
        self.current_vehicle_count = vehicle_count

        # Calculate new timing based on vehicle count
        new_timing = self.timing_calculator.calculate_timing(vehicle_count)

        # Check if timing changed significantly
        if self._should_update_timing(new_timing):
            self._apply_new_timing(new_timing)
            return True

        return False

    def _should_update_timing(self, new_timing: Dict) -> bool:
        """
        Determine if timing should be updated

        Args:
            new_timing: New timing configuration

        Returns:
            True if significant change, False otherwise
        """
        if not self.signal.state_start_time:
            return False

        # Don't update if in emergency mode
        if self.signal.emergency_active:
            return False

        # Update if green duration changed
        current_green = self.signal.green_duration
        new_green = new_timing['green_duration']

        return current_green != new_green

    def _apply_new_timing(self, new_timing: Dict):
        """
        Apply new timing to signal state machine

        Args:
            new_timing: New timing configuration
        """
        old_green = self.signal.green_duration

        # Update signal timing
        self.signal.green_duration = new_timing['green_duration']
        self.signal.yellow_duration = new_timing['yellow_duration']
        self.signal.red_duration = new_timing['red_duration']

        self.last_timing_update_time = datetime.now()
        self.timing_updates_count += 1

        # Record change
        timing_record = {
            'timestamp': datetime.now().isoformat(),
            'old_green_duration': old_green,
            'new_green_duration': new_timing['green_duration'],
            'vehicle_count': new_timing['vehicle_count'],
            'congestion_level': new_timing['congestion_level'],
            'reason': new_timing['reason']
        }
        self.timing_change_history.append(timing_record)

        # Keep only last 100 changes
        if len(self.timing_change_history) > 100:
            self.timing_change_history = self.timing_change_history[-100:]

        logger.info(
            f"Signal {self.signal_id} timing updated: "
            f"{old_green}s → {new_timing['green_duration']}s green "
            f"({new_timing['vehicle_count']} vehicles, {new_timing['congestion_level']})"
        )

        # Callback
        if self.on_timing_change:
            self.on_timing_change(new_timing)

    def update(self) -> Dict:
        """
        Update signal state

        Should be called periodically (every 100-500ms)

        Returns:
            Current signal status
        """
        # Update signal state
        self.signal.update()
        self.last_update_time = datetime.now()

        return self.get_status()

    def activate_emergency(self, reason: str = "Ambulance detected") -> bool:
        """
        Activate emergency mode (ambulance priority)

        Args:
            reason: Reason for emergency

        Returns:
            True if activated
        """
        success = self.signal.activate_emergency(reason)
        if success:
            logger.warning(
                f"Signal {self.signal_id} emergency mode activated: {reason}")
        return success

    def reset_to_normal(self) -> bool:
        """
        Reset from emergency to normal operation

        Returns:
            True if reset
        """
        success = self.signal.reset_to_normal()
        if success:
            logger.info(f"Signal {self.signal_id} reset to normal operation")
        return success

    def get_status(self) -> Dict:
        """
        Get complete status including dynamic timing info

        Returns:
            Dictionary with status information
        """
        signal_info = self.signal.get_state_info()
        calculator_stats = self.timing_calculator.get_statistics()

        return {
            'signal_id': self.signal_id,
            'signal_state': signal_info['current_state'],
            'is_running': signal_info['is_running'],
            'time_remaining': signal_info['time_remaining'],
            'green_duration': self.signal.green_duration,
            'yellow_duration': self.signal.yellow_duration,
            'red_duration': self.signal.red_duration,
            'current_vehicle_count': self.current_vehicle_count,
            'timing_updates_count': self.timing_updates_count,
            'calculator_stats': calculator_stats,
            'emergency_active': signal_info['emergency_active'],
            'emergency_reason': signal_info['emergency_reason'],
            'last_timing_update': (
                self.last_timing_update_time.isoformat()
                if self.last_timing_update_time else None
            ),
            'timestamp': datetime.now().isoformat()
        }

    def get_timing_change_history(self, limit: int = 20) -> list:
        """
        Get history of timing changes

        Args:
            limit: Maximum number of records to return

        Returns:
            List of timing change records
        """
        return self.timing_change_history[-limit:]

    def _on_signal_state_change(self, signal_id: str, new_state):
        """Callback when signal state changes"""
        logger.debug(f"Signal {signal_id} state changed to {new_state.value}")

    def __str__(self) -> str:
        """String representation"""
        status = self.get_status()
        return (
            f"DynamicSignal({self.signal_id}): "
            f"{status['signal_state']} "
            f"({status['current_vehicle_count']} vehicles)"
        )


class MultiDynamicSignalController:
    """
    Manages multiple dynamic signals at an intersection.

    Coordinates timing for multiple directions while maintaining
    emergency priority capability.

    Example:
        >>> controller = MultiDynamicSignalController()
        >>> 
        >>> # Register signals for each direction
        >>> controller.register_signal('signal_ns', 'north-south')
        >>> controller.register_signal('signal_ew', 'east-west')
        >>> 
        >>> # Update vehicle counts for each direction
        >>> controller.update_vehicle_count('signal_ns', 12)
        >>> controller.update_vehicle_count('signal_ew', 5)
        >>> 
        >>> # Periodically update
        >>> controller.update()
        >>> 
        >>> # Get all signals status
        >>> status = controller.get_all_signals_status()
    """

    def __init__(self):
        """Initialize multi-signal controller"""
        self.signals: Dict[str, DynamicSignalController] = {}
        logger.info("MultiDynamicSignalController initialized")

    def register_signal(
        self,
        signal_id: str,
        direction: str,
        base_cycle_time: int = 90,
        min_green: int = 15,
        max_green: int = 60
    ) -> DynamicSignalController:
        """
        Register a dynamic signal

        Args:
            signal_id: Unique signal identifier
            direction: Direction name (e.g., 'north-south', 'east-west')
            base_cycle_time: Total cycle time
            min_green: Minimum green duration
            max_green: Maximum green duration

        Returns:
            DynamicSignalController instance
        """
        controller = DynamicSignalController(
            signal_id=signal_id,
            base_cycle_time=base_cycle_time,
            min_green=min_green,
            max_green=max_green
        )
        self.signals[signal_id] = controller
        logger.info(f"Dynamic signal registered: {signal_id} ({direction})")
        return controller

    def start_all_signals(self):
        """Start all signals"""
        for signal in self.signals.values():
            signal.start()
        logger.info(f"Started {len(self.signals)} dynamic signals")

    def stop_all_signals(self):
        """Stop all signals"""
        for signal in self.signals.values():
            signal.stop()
        logger.info(f"Stopped {len(self.signals)} dynamic signals")

    def update_vehicle_count(self, signal_id: str, vehicle_count: int) -> bool:
        """
        Update vehicle count for a signal

        Args:
            signal_id: Signal identifier
            vehicle_count: Vehicle count in zone

        Returns:
            True if timing was updated
        """
        if signal_id not in self.signals:
            logger.warning(f"Signal {signal_id} not found")
            return False

        return self.signals[signal_id].update_vehicle_count(vehicle_count)

    def update(self):
        """Update all signals"""
        for signal in self.signals.values():
            signal.update()

    def get_signal_status(self, signal_id: str) -> Optional[Dict]:
        """Get status of specific signal"""
        if signal_id not in self.signals:
            return None
        return self.signals[signal_id].get_status()

    def get_all_signals_status(self) -> Dict[str, Dict]:
        """Get status of all signals"""
        return {
            signal_id: signal.get_status()
            for signal_id, signal in self.signals.items()
        }

    def activate_emergency(self, signal_id: str, reason: str = "Ambulance detected") -> bool:
        """Activate emergency for specific signal"""
        if signal_id not in self.signals:
            return False
        return self.signals[signal_id].activate_emergency(reason)

    def reset_emergency(self, signal_id: str) -> bool:
        """Reset emergency for specific signal"""
        if signal_id not in self.signals:
            return False
        return self.signals[signal_id].reset_to_normal()
