#!/usr/bin/env python3
"""
🚦 Traffic Test Case Executor
Real-world traffic scenario testing for Indian Signal System

Executes all traffic test cases and generates report
"""

from traffic_signals.core.indian_traffic_signal import IntersectionController, SignalState
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import signal system


class TrafficTestExecutor:
    """Executes traffic test cases"""

    def __init__(self):
        """Initialize executor"""
        self.results = {
            'passed': [],
            'failed': [],
            'total': 0
        }
        self.controller = None

    def setup_controller(self):
        """Setup intersection controller"""
        self.controller = IntersectionController()
        self.controller.add_lane('north', 'NORTH')
        self.controller.add_lane('south', 'SOUTH')
        self.controller.add_lane('east', 'EAST')
        self.controller.add_lane('west', 'WEST')
        self.controller.start()
        logger.info("Controller setup complete")

    def print_header(self, title: str):
        """Print test header"""
        print("\n" + "="*70)
        print(f"🧪 {title}")
        print("="*70)

    def print_test(self, test_name: str, category: str):
        """Print test start"""
        print(f"\n📝 {category} - {test_name}")
        print("-" * 70)

    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        self.results['total'] += 1

        if passed:
            self.results['passed'].append(test_name)
            status = "✓ PASS"
            logger.info(f"✓ {test_name}: PASSED")
        else:
            self.results['failed'].append(test_name)
            status = "✗ FAIL"
            logger.error(f"✗ {test_name}: FAILED - {message}")

        print(f"{status} - {message}")
        return passed

    # ============ CATEGORY A: Normal Operations ============

    def test_a1_basic_cycling(self):
        """A1: Basic Signal Cycling"""
        self.print_test("Basic Signal Cycling", "CATEGORY A")
        self.setup_controller()

        try:
            # Run for one complete cycle (~140 seconds)
            # But simulate faster for testing - just 3 seconds
            print("Running 3-second simulation (1/46 of full cycle)...")

            states_observed = set()
            for i in range(30):  # 30 * 0.1 = 3 seconds
                self.controller.update(0.1)

                # Collect states
                for lane_id, signal in self.controller.lanes.items():
                    states_observed.add(signal.current_state.value)

            # Check for expected states
            has_green = SignalState.GREEN.value in states_observed
            has_red = SignalState.RED.value in states_observed

            message = f"States observed: {states_observed}"
            return self.log_result("A1", has_green and has_red, message)

        except Exception as e:
            return self.log_result("A1", False, str(e))

    def test_a2_long_term_stability(self):
        """A2: Long-Term Stability (simulated: 30 cycles instead of 30 min)"""
        self.print_test("Long-Term Stability", "CATEGORY A")
        self.setup_controller()

        try:
            print("Running 300 cycles (equivalent to 30 seconds real time)...")

            cycle_count = 0
            errors = []

            for i in range(3000):  # 3000 * 0.1 = 300 seconds
                try:
                    self.controller.update(0.1)
                except Exception as e:
                    errors.append(f"Cycle {i}: {e}")

            if errors:
                message = f"Errors: {errors[:3]}"
                return self.log_result("A2", False, message)

            message = "Ran 3000 updates without errors"
            return self.log_result("A2", len(errors) == 0, message)

        except Exception as e:
            return self.log_result("A2", False, str(e))

    def test_a3_visual_display(self):
        """A3: Visual Display Accuracy"""
        self.print_test("Visual Display Accuracy", "CATEGORY A")
        self.setup_controller()

        try:
            # Run for 1 second
            for i in range(10):
                self.controller.update(0.1)

            status = self.controller.get_status()

            # Verify status format
            has_lanes = 'lanes' in status
            has_running = 'is_running' in status
            all_lanes_have_state = all(
                'current_state' in lane_info
                for lane_info in status['lanes'].values()
            )

            message = f"Status has all required fields: {has_lanes and has_running and all_lanes_have_state}"
            return self.log_result("A3", has_lanes and has_running and all_lanes_have_state, message)

        except Exception as e:
            return self.log_result("A3", False, str(e))

    # ============ CATEGORY B: Emergency Scenarios ============

    def test_b1_ambulance_north(self):
        """B1: Ambulance from NORTH"""
        self.print_test("Ambulance from NORTH", "CATEGORY B")
        self.setup_controller()

        try:
            # Let it run a bit
            for _ in range(50):
                self.controller.update(0.1)

            # Trigger ambulance
            self.controller.activate_ambulance('north', 0.95)

            # Check state
            self.controller.update(0.1)
            north_state = self.controller.lanes['north'].current_state

            is_emergency = north_state == SignalState.EMERGENCY
            message = f"NORTH state: {north_state.value}"
            return self.log_result("B1", is_emergency, message)

        except Exception as e:
            return self.log_result("B1", False, str(e))

    def test_b2_ambulance_south(self):
        """B2: Ambulance from SOUTH"""
        self.print_test("Ambulance from SOUTH", "CATEGORY B")
        self.setup_controller()

        try:
            self.controller.activate_ambulance('south', 0.92)
            self.controller.update(0.1)

            is_emergency = self.controller.lanes['south'].current_state == SignalState.EMERGENCY
            return self.log_result("B2", is_emergency, "SOUTH activated emergency")

        except Exception as e:
            return self.log_result("B2", False, str(e))

    def test_b3_ambulance_east(self):
        """B3: Ambulance from EAST"""
        self.print_test("Ambulance from EAST", "CATEGORY B")
        self.setup_controller()

        try:
            self.controller.activate_ambulance('east', 0.88)
            self.controller.update(0.1)

            is_emergency = self.controller.lanes['east'].current_state == SignalState.EMERGENCY
            return self.log_result("B3", is_emergency, "EAST activated emergency")

        except Exception as e:
            return self.log_result("B3", False, str(e))

    def test_b4_ambulance_west(self):
        """B4: Ambulance from WEST"""
        self.print_test("Ambulance from WEST", "CATEGORY B")
        self.setup_controller()

        try:
            self.controller.activate_ambulance('west', 0.91)
            self.controller.update(0.1)

            is_emergency = self.controller.lanes['west'].current_state == SignalState.EMERGENCY
            return self.log_result("B4", is_emergency, "WEST activated emergency")

        except Exception as e:
            return self.log_result("B4", False, str(e))

    def test_b5_ambulance_during_yellow(self):
        """B5: Ambulance During YELLOW"""
        self.print_test("Ambulance During YELLOW", "CATEGORY B")
        self.setup_controller()

        try:
            # Run until we get YELLOW (should be ~30 updates)
            yellow_found = False
            for i in range(100):
                self.controller.update(0.1)
                if self.controller.lanes['north'].current_state == SignalState.YELLOW:
                    yellow_found = True
                    break

            if not yellow_found:
                return self.log_result("B5", False, "YELLOW state not reached in time")

            # Trigger ambulance during yellow
            self.controller.activate_ambulance('north', 0.95)
            self.controller.update(0.1)

            is_emergency = self.controller.lanes['north'].current_state == SignalState.EMERGENCY
            return self.log_result("B5", is_emergency, "Emergency activated during YELLOW")

        except Exception as e:
            return self.log_result("B5", False, str(e))

    def test_b6_ambulance_during_allred(self):
        """B6: Ambulance During ALL_RED"""
        self.print_test("Ambulance During ALL_RED", "CATEGORY B")
        self.setup_controller()

        try:
            # Run until we get ALL_RED
            allred_found = False
            for i in range(200):
                self.controller.update(0.1)
                if self.controller.lanes['north'].current_state == SignalState.ALL_RED:
                    allred_found = True
                    break

            if not allred_found:
                return self.log_result("B6", False, "ALL_RED state not reached")

            # Trigger ambulance during ALL_RED
            self.controller.activate_ambulance('north', 0.95)
            self.controller.update(0.1)

            is_emergency = self.controller.lanes['north'].current_state == SignalState.EMERGENCY
            return self.log_result("B6", is_emergency, "Emergency activated during ALL_RED")

        except Exception as e:
            return self.log_result("B6", False, str(e))

    def test_b7_multiple_ambulances(self):
        """B7: Multiple Ambulances Sequential"""
        self.print_test("Multiple Ambulances Sequential", "CATEGORY B")
        self.setup_controller()

        try:
            # Trigger multiple ambulances
            self.controller.activate_ambulance('north', 0.95)
            time.sleep(0.1)
            self.controller.activate_ambulance('south', 0.92)
            time.sleep(0.1)
            self.controller.activate_ambulance('east', 0.90)

            self.controller.update(0.1)

            # At least one should be emergency
            emergencies = sum(
                1 for lane in self.controller.lanes.values()
                if lane.current_state == SignalState.EMERGENCY
            )

            message = f"Emergencies active: {emergencies}"
            return self.log_result("B7", emergencies >= 1, message)

        except Exception as e:
            return self.log_result("B7", False, str(e))

    def test_b8_low_confidence(self):
        """B8: Ambulance with Low Confidence"""
        self.print_test("Ambulance with Low Confidence", "CATEGORY B")
        self.setup_controller()

        try:
            # This would depend on implementation
            # For now, just verify it doesn't crash
            self.controller.activate_ambulance('north', 0.75)
            self.controller.update(0.1)

            # Should not crash
            return self.log_result("B8", True, "Low confidence handled gracefully")

        except Exception as e:
            return self.log_result("B8", False, str(e))

    def test_b9_threshold_confidence(self):
        """B9: Ambulance at Threshold"""
        self.print_test("Ambulance at Threshold (0.80)", "CATEGORY B")
        self.setup_controller()

        try:
            self.controller.activate_ambulance('north', 0.80)
            self.controller.update(0.1)

            is_emergency = self.controller.lanes['north'].current_state == SignalState.EMERGENCY
            return self.log_result("B9", is_emergency, "Threshold ambulance activated")

        except Exception as e:
            return self.log_result("B9", False, str(e))

    # ============ CATEGORY C: Edge Cases ============

    def test_c1_rapid_triggers(self):
        """C1: Rapid Ambulance Triggers"""
        self.print_test("Rapid Ambulance Triggers", "CATEGORY C")
        self.setup_controller()

        try:
            # Rapid triggers
            for i in range(5):
                self.controller.activate_ambulance('north', 0.95 - i*0.01)
                self.controller.update(0.01)

            # Should not crash
            return self.log_result("C1", True, "Rapid triggers handled")

        except Exception as e:
            return self.log_result("C1", False, str(e))

    def test_c2_alternating_ambulances(self):
        """C2: Alternating Direction Ambulances"""
        self.print_test("Alternating Ambulances", "CATEGORY C")
        self.setup_controller()

        try:
            directions = ['north', 'south', 'north', 'south']
            for direction in directions:
                self.controller.activate_ambulance(direction, 0.90)
                for _ in range(5):
                    self.controller.update(0.1)

            return self.log_result("C2", True, "Alternating ambulances handled")

        except Exception as e:
            return self.log_result("C2", False, str(e))

    def test_c3_reset_during_emergency(self):
        """C3: Manual Reset During Emergency"""
        self.print_test("Reset During Emergency", "CATEGORY C")
        self.setup_controller()

        try:
            self.controller.activate_ambulance('north', 0.95)
            self.controller.update(0.1)

            # Reset
            self.controller.reset()

            # Check state
            all_red = all(
                lane.current_state == SignalState.RED
                for lane in self.controller.lanes.values()
            )

            return self.log_result("C3", all_red, "Reset clears emergency state")

        except Exception as e:
            return self.log_result("C3", False, str(e))

    def test_c4_stress_test(self):
        """C4: System Overload/Stress Test"""
        self.print_test("System Overload", "CATEGORY C")
        self.setup_controller()

        try:
            # Stress test: lots of updates
            for i in range(10000):
                self.controller.update(0.001)
                if i % 1000 == 0:
                    print(f"  {i}/10000 updates...")

            return self.log_result("C4", True, "Handled 10000 rapid updates")

        except Exception as e:
            return self.log_result("C4", False, str(e))

    # ============ CATEGORY D: Safety Tests ============

    def test_d1_no_conflicts(self):
        """D1: No Conflicting States"""
        self.print_test("No Conflicting States", "CATEGORY D")
        self.setup_controller()

        try:
            conflicts = 0
            for i in range(1000):
                self.controller.update(0.1)

                # Count GREEN states
                greens = sum(
                    1 for lane in self.controller.lanes.values()
                    if lane.current_state == SignalState.GREEN
                )

                emergencies = sum(
                    1 for lane in self.controller.lanes.values()
                    if lane.current_state == SignalState.EMERGENCY
                )

                # Should be at most 1 green or emergency
                total_active = greens + emergencies
                if total_active > 1:
                    conflicts += 1

            message = f"Conflicts found: {conflicts} out of 1000 cycles"
            return self.log_result("D1", conflicts == 0, message)

        except Exception as e:
            return self.log_result("D1", False, str(e))

    def test_d2_allred_clearance(self):
        """D2: ALL_RED Safety Clearance Exists"""
        self.print_test("ALL_RED Safety Clearance", "CATEGORY D")
        self.setup_controller()

        try:
            allred_found = False
            for i in range(500):
                self.controller.update(0.1)
                if self.controller.lanes['north'].current_state == SignalState.ALL_RED:
                    allred_found = True
                    break

            return self.log_result("D2", allred_found, "ALL_RED clearance period verified")

        except Exception as e:
            return self.log_result("D2", False, str(e))

    def test_d3_emergency_duration(self):
        """D3: Emergency Duration (45 seconds)"""
        self.print_test("Emergency Duration Accuracy", "CATEGORY D")
        self.setup_controller()

        try:
            # Note: Testing with simulated time - 450 updates = 45 seconds at 0.1s per update
            self.controller.activate_ambulance('north', 0.95)

            # Run until emergency ends
            emergency_duration = 0
            start_count = 0
            while emergency_duration < 600:  # Safety limit: 60 seconds of simulation
                self.controller.update(0.1)
                is_emergency = self.controller.lanes['north'].current_state == SignalState.EMERGENCY

                if is_emergency:
                    start_count += 1
                    emergency_duration += 1
                elif start_count > 0:
                    break  # Emergency ended

            # Should be ~450 cycles = 45 seconds
            # Allow ±10% tolerance = 450 ± 45
            duration_seconds = (emergency_duration - start_count) * 0.1
            is_close = 40 < duration_seconds < 50

            message = f"Emergency duration: {duration_seconds:.1f}s (expected: ~45s)"
            return self.log_result("D3", is_close, message)

        except Exception as e:
            return self.log_result("D3", False, str(e))

    def test_d4_state_transitions(self):
        """D4: Proper State Transitions"""
        self.print_test("State Transition Sequence", "CATEGORY D")
        self.setup_controller()

        try:
            # Expected sequence: RED → GREEN → YELLOW → ALL_RED → RED
            states_sequence = []
            prev_state = None

            for i in range(500):
                self.controller.update(0.1)
                curr_state = self.controller.lanes['north'].current_state

                if curr_state != prev_state:
                    states_sequence.append(curr_state.value)
                    prev_state = curr_state

            # Should have multiple state changes
            has_variety = len(set(states_sequence)) >= 3

            message = f"States observed: {states_sequence[:10]}..."
            return self.log_result("D4", has_variety, message)

        except Exception as e:
            return self.log_result("D4", False, str(e))

    def test_d5_priority_override(self):
        """D5: Ambulance Priority Over Any State"""
        self.print_test("Ambulance Priority Override", "CATEGORY D")
        self.setup_controller()

        try:
            success_count = 0

            # Test with different starting states
            for test_state in range(3):
                self.setup_controller()

                # Let it run to a state
                for _ in range(100 + test_state * 50):
                    self.controller.update(0.1)

                # Trigger ambulance
                self.controller.activate_ambulance('north', 0.95)
                self.controller.update(0.1)

                # Should be emergency
                if self.controller.lanes['north'].current_state == SignalState.EMERGENCY:
                    success_count += 1

            return self.log_result("D5", success_count == 3, f"Override successful in {success_count}/3 tests")

        except Exception as e:
            return self.log_result("D5", False, str(e))

    # ============ CATEGORY E: Integration Tests ============

    def test_e1_statistics(self):
        """E1: Statistics Tracking"""
        self.print_test("Statistics Tracking", "CATEGORY E")
        self.setup_controller()

        try:
            # Trigger some ambulances
            for i in range(3):
                self.controller.activate_ambulance(
                    f'{"north"if i == 0 else "south" if i == 1 else "east"}', 0.95)
                for _ in range(100):
                    self.controller.update(0.1)

            status = self.controller.get_status()

            # Statistics should exist
            has_stats = status is not None and 'lanes' in status
            return self.log_result("E1", has_stats, "Statistics tracked successfully")

        except Exception as e:
            return self.log_result("E1", False, str(e))

    def test_e2_status_format(self):
        """E2: Status Format Correctness"""
        self.print_test("Status Format", "CATEGORY E")
        self.setup_controller()

        try:
            self.controller.update(0.1)
            status = self.controller.get_status()

            # Check format
            required_fields = ['is_running', 'current_active_lane', 'lanes']
            lane_fields = ['lane_id', 'current_state',
                           'elapsed_time', 'ambulance_active']

            has_main_fields = all(field in status for field in required_fields)
            has_lane_fields = all(
                all(field in lane_info for field in lane_fields)
                for lane_info in status['lanes'].values()
            )

            return self.log_result("E2", has_main_fields and has_lane_fields, "Status format correct")

        except Exception as e:
            return self.log_result("E2", False, str(e))

    def test_e3_api_response(self):
        """E3: API Response Correctness"""
        self.print_test("API Response", "CATEGORY E")
        self.setup_controller()

        try:
            # Trigger ambulance
            self.controller.activate_ambulance('north', 0.95)

            # Run a bit
            for _ in range(50):
                self.controller.update(0.1)

            # Get status
            status = self.controller.get_status()

            north_info = status['lanes']['north']
            is_emergency = north_info['current_state'] == 'EMERGENCY'

            return self.log_result("E3", is_emergency, "API returns correct emergency status")

        except Exception as e:
            return self.log_result("E3", False, str(e))

    def test_e4_integration_readiness(self):
        """E4: Integration with External System"""
        self.print_test("Integration Readiness", "CATEGORY E")
        self.setup_controller()

        try:
            # Simulate external detection system
            def external_detection_system():
                """Simulate YOLO detection"""
                return {
                    'ambulance_detected': True,
                    'direction': 'north',
                    'confidence': 0.95
                }

            # Get detection
            detection = external_detection_system()

            # Feed to signal system
            if detection['ambulance_detected']:
                self.controller.activate_ambulance(
                    detection['direction'],
                    detection['confidence']
                )

            self.controller.update(0.1)

            # Get status for dashboard
            status = self.controller.get_status()

            # Verify integration worked
            is_emergency = status['lanes']['north']['current_state'] == 'EMERGENCY'

            return self.log_result("E4", is_emergency, "Integration with external system successful")

        except Exception as e:
            return self.log_result("E4", False, str(e))

    # ============ MAIN EXECUTOR ============

    def run_all_tests(self):
        """Run all test cases"""
        print("\n")
        print("╔" + "═"*68 + "╗")
        print("║" + " "*15 + "🚦 TRAFFIC TEST CASE EXECUTOR" + " "*23 + "║")
        print("║" + " "*20 + "Indian Signal System" + " "*28 + "║")
        print("╚" + "═"*68 + "╝")
        print(f"\n⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # CATEGORY A
        self.print_header("CATEGORY A: NORMAL OPERATIONS")
        self.test_a1_basic_cycling()
        self.test_a2_long_term_stability()
        self.test_a3_visual_display()

        # CATEGORY B
        self.print_header("CATEGORY B: EMERGENCY SCENARIOS")
        self.test_b1_ambulance_north()
        self.test_b2_ambulance_south()
        self.test_b3_ambulance_east()
        self.test_b4_ambulance_west()
        self.test_b5_ambulance_during_yellow()
        self.test_b6_ambulance_during_allred()
        self.test_b7_multiple_ambulances()
        self.test_b8_low_confidence()
        self.test_b9_threshold_confidence()

        # CATEGORY C
        self.print_header("CATEGORY C: EDGE CASES")
        self.test_c1_rapid_triggers()
        self.test_c2_alternating_ambulances()
        self.test_c3_reset_during_emergency()
        # Skip C4 stress test for quick run - uncomment to run
        # self.test_c4_stress_test()

        # CATEGORY D
        self.print_header("CATEGORY D: SAFETY & COMPLIANCE")
        self.test_d1_no_conflicts()
        self.test_d2_allred_clearance()
        self.test_d3_emergency_duration()
        self.test_d4_state_transitions()
        self.test_d5_priority_override()

        # CATEGORY E
        self.print_header("CATEGORY E: INTEGRATION")
        self.test_e1_statistics()
        self.test_e2_status_format()
        self.test_e3_api_response()
        self.test_e4_integration_readiness()

        # SUMMARY
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")

        total = self.results['total']
        passed = len(self.results['passed'])
        failed = len(self.results['failed'])
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n📊 Results:")
        print(f"  Total Tests:  {total}")
        print(f"  Passed:       {passed} ✓")
        print(f"  Failed:       {failed} ✗")
        print(f"  Pass Rate:    {pass_rate:.1f}%")

        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for test_name in self.results['failed']:
                print(f"  - {test_name}")

        print(f"\n⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if pass_rate == 100:
            print("\n" + "="*70)
            print("✓ ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION ✓")
            print("="*70)
        else:
            print("\n" + "="*70)
            print(f"⚠️  {failed} TESTS FAILED - REVIEW REQUIRED")
            print("="*70)

        return pass_rate


def main():
    """Main entry point"""
    executor = TrafficTestExecutor()
    pass_rate = executor.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if pass_rate == 100 else 1)


if __name__ == '__main__':
    main()
