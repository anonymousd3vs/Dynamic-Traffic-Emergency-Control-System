"""
Traffic Signal REST API
Provides HTTP endpoints for signal control and monitoring
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SignalAPIHandler:
    """
    REST API handler for traffic signals

    Endpoints:
    - GET  /signals/status           - Get all signal states
    - GET  /signals/{id}/status      - Get specific signal state
    - POST /signals/{id}/emergency   - Activate emergency mode
    - POST /signals/{id}/reset       - Reset to normal
    - GET  /signals/emergencies      - Get active emergencies
    - GET  /signals/statistics       - Get statistics

    Example:
        >>> handler = SignalAPIHandler(priority_manager)
        >>> status = handler.get_all_signals_status()
        >>> handler.activate_emergency('amb_001', 'north')
    """

    def __init__(self, priority_manager):
        """
        Initialize API handler

        Args:
            priority_manager: PriorityManager instance
        """
        self.manager = priority_manager
        logger.info("Signal API handler initialized")

    # ==================== GET Endpoints ====================

    def get_all_signals_status(self) -> Dict:
        """
        Get status of all signals

        Returns:
            {
                'status': 'success',
                'timestamp': '2025-10-24T10:30:45.123456',
                'signals': {
                    'north': {'current_state': 'GREEN', 'time_remaining': 15.3, ...},
                    'south': {...}
                }
            }
        """
        try:
            signals = self.manager.get_all_signals_status()
            return {
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'signal_count': len(signals),
                'signals': signals
            }
        except Exception as e:
            logger.error(f"Error getting signals status: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_signal_status(self, signal_id: str) -> Dict:
        """
        Get status of specific signal

        Args:
            signal_id: Signal identifier

        Returns:
            {
                'status': 'success',
                'signal': {...signal data...}
            }
        """
        try:
            signal_status = self.manager.get_signal_status(signal_id)

            if not signal_status:
                return {
                    'status': 'error',
                    'message': f'Signal {signal_id} not found'
                }

            return {
                'status': 'success',
                'signal': signal_status
            }
        except Exception as e:
            logger.error(f"Error getting signal status: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_active_emergencies(self) -> Dict:
        """
        Get list of active emergencies

        Returns:
            {
                'status': 'success',
                'count': 1,
                'emergencies': [
                    {
                        'ambulance_id': 'amb_001',
                        'direction': 'NORTH',
                        'confidence': 0.95,
                        'location': 'intersection',
                        'activation_time': '2025-10-24T10:30:00',
                        'elapsed_seconds': 45.3,
                        'signals_affected': ['north', 'south']
                    }
                ]
            }
        """
        try:
            emergencies = self.manager.get_active_emergencies()
            return {
                'status': 'success',
                'count': len(emergencies),
                'emergencies': emergencies,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting active emergencies: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_emergency_history(self, limit: int = 50) -> Dict:
        """
        Get emergency history

        Args:
            limit: Maximum number of records to return

        Returns:
            {
                'status': 'success',
                'count': 5,
                'history': [...]
            }
        """
        try:
            history = self.manager.get_emergency_history(limit)
            return {
                'status': 'success',
                'count': len(history),
                'history': history,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting emergency history: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_statistics(self) -> Dict:
        """
        Get signal and emergency statistics

        Returns:
            {
                'status': 'success',
                'statistics': {
                    'total_emergencies': 5,
                    'active_emergencies': 1,
                    'completed_emergencies': 4,
                    'total_emergency_duration_seconds': 210.5,
                    'average_emergency_duration_seconds': 52.6,
                    'signal_count': 4
                }
            }
        """
        try:
            stats = self.manager.get_statistics()
            return {
                'status': 'success',
                'statistics': stats,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    # ==================== POST Endpoints ====================

    def activate_emergency(
        self,
        ambulance_id: str,
        direction: Optional[str] = None,
        confidence: float = 0.9,
        location: str = "intersection",
        signal_ids: Optional[list] = None
    ) -> Dict:
        """
        Activate emergency mode for ambulance

        Args:
            ambulance_id: Unique ambulance ID
            direction: Direction (north, south, east, west)
            confidence: Detection confidence (0.0-1.0)
            location: Location description
            signal_ids: Specific signals to activate (None = all)

        Returns:
            {'status': 'success|error', 'message': '...'}
        """
        try:
            success = self.manager.activate_emergency(
                ambulance_id=ambulance_id,
                direction=direction,
                confidence=confidence,
                location=location,
                activate_signals=signal_ids
            )

            if success:
                return {
                    'status': 'success',
                    'message': f'Emergency activated for ambulance {ambulance_id}',
                    'ambulance_id': ambulance_id,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to activate emergency for {ambulance_id}'
                }
        except Exception as e:
            logger.error(f"Error activating emergency: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def deactivate_emergency(self, ambulance_id: str) -> Dict:
        """
        Deactivate emergency for ambulance

        Args:
            ambulance_id: Ambulance ID to deactivate

        Returns:
            {'status': 'success|error', 'message': '...'}
        """
        try:
            success = self.manager.deactivate_emergency(ambulance_id)

            if success:
                return {
                    'status': 'success',
                    'message': f'Emergency deactivated for ambulance {ambulance_id}',
                    'ambulance_id': ambulance_id,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Emergency not found for {ambulance_id}'
                }
        except Exception as e:
            logger.error(f"Error deactivating emergency: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def reset_all_signals(self) -> Dict:
        """
        Reset all signals to normal operation

        Returns:
            {'status': 'success|error', 'message': '...'}
        """
        try:
            emergencies = self.manager.get_active_emergencies()
            reset_count = 0

            for emergency in emergencies:
                if self.manager.deactivate_emergency(emergency['ambulance_id']):
                    reset_count += 1

            return {
                'status': 'success',
                'message': f'Reset {reset_count} emergencies',
                'reset_count': reset_count,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error resetting signals: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }

    def get_signal_config(self, signal_id: str) -> Dict:
        """
        Get configuration of specific signal

        Args:
            signal_id: Signal identifier

        Returns:
            Signal configuration or error
        """
        try:
            if signal_id not in self.manager.signals:
                return {
                    'status': 'error',
                    'message': f'Signal {signal_id} not found'
                }

            signal = self.manager.signals[signal_id]

            return {
                'status': 'success',
                'signal_id': signal_id,
                'configuration': {
                    'green_duration': signal.green_duration,
                    'yellow_duration': signal.yellow_duration,
                    'red_duration': signal.red_duration,
                    'emergency_duration': signal.emergency_duration
                }
            }
        except Exception as e:
            logger.error(f"Error getting signal config: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }


# Example API response formats
API_RESPONSE_EXAMPLES = {
    'signal_status': {
        'status': 'success',
        'timestamp': '2025-10-24T10:30:45.123456',
        'signals': {
            'north': {
                'signal_id': 'north',
                'current_state': 'GREEN',
                'is_running': True,
                'elapsed_seconds': 12.5,
                'time_remaining': 17.5,
                'emergency_active': False,
                'emergency_reason': '',
                'emergency_remaining': 0.0,
                'timestamp': '2025-10-24T10:30:45.123456'
            }
        }
    },
    'active_emergencies': {
        'status': 'success',
        'count': 1,
        'emergencies': [
            {
                'ambulance_id': 'ambulance_north_1729759845',
                'direction': 'NORTH',
                'confidence': 0.95,
                'location': 'intersection',
                'activation_time': '2025-10-24T10:30:00',
                'elapsed_seconds': 45.3,
                'signals_affected': ['north', 'south']
            }
        ]
    },
    'statistics': {
        'status': 'success',
        'statistics': {
            'total_emergencies': 5,
            'active_emergencies': 1,
            'completed_emergencies': 4,
            'total_emergency_duration_seconds': 210.5,
            'average_emergency_duration_seconds': 52.6,
            'signal_count': 4
        }
    }
}
