"""
Traffic Signal Priority Manager
Manages emergency priority for ambulances across multiple signals
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from .signal_state_machine import SignalStateMachine

logger = logging.getLogger(__name__)


class PriorityManager:
    """
    Manages emergency priority for ambulances across traffic signals

    Features:
    - Register multiple signals at an intersection
    - Detect ambulance and activate emergency on relevant signals
    - Coordinate multi-signal priority
    - Automatic reset after ambulance passes
    - Conflict detection and resolution

    Example:
        >>> manager = PriorityManager()
        >>> manager.register_signal('signal_ns', 'north-south')
        >>> manager.register_signal('signal_ew', 'east-west')
        >>> 
        >>> # When ambulance detected
        >>> manager.activate_emergency(
        ...     direction='north',
        ...     confidence=0.95
        ... )
        >>> 
        >>> # Update signals periodically
        >>> while True:
        ...     manager.update()
        ...     time.sleep(0.1)
    """

    def __init__(self):
        """Initialize priority manager"""
        self.signals: Dict[str, SignalStateMachine] = {}
        self.active_emergencies: List[Dict] = []
        self.emergency_history: List[Dict] = []

        logger.info("Priority Manager initialized")

    def register_signal(
        self,
        signal_id: str,
        direction: str,
        green_duration: int = 30,
        yellow_duration: int = 4,
        red_duration: int = 34,
        emergency_duration: int = 45
    ) -> SignalStateMachine:
        """
        Register a traffic signal

        Args:
            signal_id: Unique identifier for signal
            direction: Direction (north, south, east, west, north-south, east-west)
            green_duration: Green light duration in seconds
            yellow_duration: Yellow light duration in seconds
            red_duration: Red light duration in seconds
            emergency_duration: Emergency mode duration in seconds

        Returns:
            SignalStateMachine instance
        """
        signal = SignalStateMachine(
            signal_id=signal_id,
            green_duration=green_duration,
            yellow_duration=yellow_duration,
            red_duration=red_duration,
            emergency_duration=emergency_duration,
            on_state_change=self._on_signal_state_change
        )

        self.signals[signal_id] = signal
        logger.info(f"Signal registered: {signal_id} ({direction})")

        return signal

    def start_all_signals(self):
        """Start all registered signals"""
        for signal in self.signals.values():
            signal.start()
        logger.info(f"Started {len(self.signals)} signals")

    def stop_all_signals(self):
        """Stop all registered signals"""
        for signal in self.signals.values():
            signal.stop()
        logger.info(f"Stopped {len(self.signals)} signals")

    def activate_emergency(
        self,
        ambulance_id: str,
        direction: Optional[str] = None,
        confidence: float = 0.9,
        location: str = "intersection",
        activate_signals: Optional[List[str]] = None
    ) -> bool:
        """
        Activate emergency mode for ambulance

        Args:
            ambulance_id: Unique ambulance identifier
            direction: Direction ambulance is coming from (north, south, east, west)
            confidence: Detection confidence (0.0 - 1.0)
            location: Location description
            activate_signals: Specific signals to activate (if None, activates all)

        Returns:
            True if emergency activated successfully
        """
        # Check if already in emergency
        for emergency in self.active_emergencies:
            if emergency['ambulance_id'] == ambulance_id:
                logger.warning(
                    f"Ambulance {ambulance_id} already in emergency mode")
                return False

        # Determine which signals to activate
        signals_to_activate = activate_signals or list(self.signals.keys())

        # Activate emergency on specified signals
        activated_count = 0
        for signal_id in signals_to_activate:
            if signal_id in self.signals:
                if self.signals[signal_id].activate_emergency(
                    reason=f"Ambulance {ambulance_id} detected"
                ):
                    activated_count += 1

        # Record emergency
        emergency_record = {
            'ambulance_id': ambulance_id,
            'direction': direction,
            'confidence': confidence,
            'location': location,
            'activation_time': datetime.now(),
            'signals_activated': signals_to_activate,
            'status': 'active'
        }

        self.active_emergencies.append(emergency_record)
        self.emergency_history.append(emergency_record)

        logger.warning(
            f"🚨 EMERGENCY ACTIVATED - Ambulance {ambulance_id} "
            f"({confidence:.0%} confidence) in {direction} direction. "
            f"Activated {activated_count} signals"
        )

        return activated_count > 0

    def deactivate_emergency(self, ambulance_id: str) -> bool:
        """
        Deactivate emergency for ambulance

        Args:
            ambulance_id: Ambulance to deactivate

        Returns:
            True if deactivated successfully
        """
        # Find and remove emergency record
        for emergency in self.active_emergencies[:]:
            if emergency['ambulance_id'] == ambulance_id:
                # Reset signals to normal
                for signal_id in emergency['signals_activated']:
                    if signal_id in self.signals:
                        self.signals[signal_id].reset_to_normal()

                emergency['status'] = 'deactivated'
                emergency['deactivation_time'] = datetime.now()
                self.active_emergencies.remove(emergency)

                logger.info(
                    f"🚑 Emergency deactivated for ambulance {ambulance_id}")
                return True

        return False

    def update(self):
        """
        Update all signals and manage emergency durations
        Should be called frequently (every 100-500ms)
        """
        # Update all signals
        for signal in self.signals.values():
            signal.update()

        # Check for expired emergencies
        now = datetime.now()
        for emergency in self.active_emergencies[:]:
            elapsed = (now - emergency['activation_time']).total_seconds()

            # Emergency duration (typically 45 seconds)
            # Signals handle their own reset, but we track it here
            if elapsed > 50:  # 5 second buffer
                emergency['status'] = 'expired'
                self.active_emergencies.remove(emergency)
                logger.info(
                    f"Emergency expired for {emergency['ambulance_id']}")

    def get_signal_status(self, signal_id: str) -> Optional[Dict]:
        """
        Get status of a specific signal

        Args:
            signal_id: Signal to query

        Returns:
            Signal status dictionary or None if not found
        """
        if signal_id in self.signals:
            return self.signals[signal_id].get_state_info()
        return None

    def get_all_signals_status(self) -> Dict[str, Dict]:
        """Get status of all signals"""
        return {
            signal_id: signal.get_state_info()
            for signal_id, signal in self.signals.items()
        }

    def get_active_emergencies(self) -> List[Dict]:
        """Get list of active emergencies"""
        result = []
        for emergency in self.active_emergencies:
            result.append({
                'ambulance_id': emergency['ambulance_id'],
                'direction': emergency['direction'],
                'confidence': emergency['confidence'],
                'location': emergency['location'],
                'activation_time': emergency['activation_time'].isoformat(),
                'elapsed_seconds': (
                    datetime.now() - emergency['activation_time']
                ).total_seconds(),
                'signals_affected': emergency['signals_activated']
            })
        return result

    def get_emergency_history(self, limit: int = 50) -> List[Dict]:
        """Get emergency history"""
        result = []
        for emergency in self.emergency_history[-limit:]:
            record = {
                'ambulance_id': emergency['ambulance_id'],
                'direction': emergency['direction'],
                'confidence': emergency['confidence'],
                'location': emergency['location'],
                'activation_time': emergency['activation_time'].isoformat(),
                'status': emergency['status'],
                'signals_affected': emergency['signals_activated']
            }

            if 'deactivation_time' in emergency:
                record['deactivation_time'] = emergency['deactivation_time'].isoformat()
                record['duration_seconds'] = (
                    emergency['deactivation_time'] -
                    emergency['activation_time']
                ).total_seconds()

            result.append(record)

        return result

    def get_statistics(self) -> Dict:
        """Get emergency statistics"""
        completed = [
            e for e in self.emergency_history
            if e['status'] in ['deactivated', 'expired']
        ]

        total_duration = sum(
            (e.get('deactivation_time', datetime.now()) -
             e['activation_time']).total_seconds()
            for e in completed
        )

        return {
            'total_emergencies': len(self.emergency_history),
            'active_emergencies': len(self.active_emergencies),
            'completed_emergencies': len(completed),
            'total_emergency_duration_seconds': round(total_duration, 2),
            'average_emergency_duration_seconds': (
                round(total_duration / len(completed), 2) if completed else 0
            ),
            'signal_count': len(self.signals)
        }

    def _on_signal_state_change(self, signal_id: str, new_state):
        """Callback when signal state changes"""
        logger.debug(f"Signal {signal_id} changed to {new_state.value}")

    def __repr__(self) -> str:
        """String representation"""
        return (
            f"PriorityManager(signals={len(self.signals)}, "
            f"active_emergencies={len(self.active_emergencies)})"
        )
