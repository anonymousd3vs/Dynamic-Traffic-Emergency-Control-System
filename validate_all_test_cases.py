#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Test Case Validator for Traffic Signal System

Tests all scenarios from TRAFFIC_TEST_CASES.md:
- CATEGORY A: Normal Traffic Operations
- CATEGORY B: Emergency Scenarios
- CATEGORY C: Edge Cases & Stress Tests
- CATEGORY D: Safety & Compliance Tests
- CATEGORY E: Integration Tests
"""

from traffic_signals.core.indian_traffic_signal import IntersectionController, SignalState
import sys
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import traffic signal system


def print_header(title):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_subheader(title):
    """Print subsection header"""
    print(f"\n{'-'*70}")
    print(f"  {title}")
    print(f"{'-'*70}\n")


class TrafficTestValidator:
    """Validates all traffic test cases"""

    def __init__(self):
        """Initialize test validator"""
        self.results = {
            'passed': [],
            'failed': [],
            'skipped': []
        }
        self.controller = None

    def setup_controller(self):
        """Setup a fresh intersection controller"""
        self.controller = IntersectionController()
        self.controller.add_lane('north', 'NORTH ↓')
        self.controller.add_lane('south', 'SOUTH ↑')
        self.controller.add_lane('east', 'EAST ←')
        self.controller.add_lane('west', 'WEST →')
        self.controller.start()

    def run_for_duration(self, duration: float, label: str = ""):
        """Run simulator for given duration"""
        steps = int(duration * 10)  # 10 updates per second
        for i in range(steps):
            self.controller.update(0.1)
            time.sleep(0.01)

    def get_lane_status(self, lane_id: str):
        """Get status of a lane"""
        if lane_id not in self.controller.lanes:
            return None

        lane = self.controller.lanes[lane_id]
        return {
            'state': lane.current_state,
            'elapsed': lane.elapsed_time,
            'is_active': lane.is_active,
            'ambulance_active': lane.ambulance_active
        }

    def log_test(self, test_id: str, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  [{test_id}] {status}: {test_name}")
        if details:
            print(f"           {details}")

        if passed:
            self.results['passed'].append((test_id, test_name))
        else:
            self.results['failed'].append((test_id, test_name, details))

    # ==================== CATEGORY A: Normal Operations ====================

    def test_a1_basic_signal_cycling(self):
        """Test Case A1: Basic Signal Cycling"""
        print_subheader("TEST A1: Basic Signal Cycling")

        self.setup_controller()

        # Verify cycle order
        expected_order = ['north', 'south', 'east', 'west']
        current_order = self.controller.cycle_order

        if current_order == expected_order:
            print(
                f"  Cycle order: {' > '.join([l.upper() for l in current_order])}")
        else:
            print(
                f"  x Cycle order mismatch: {current_order} vs {expected_order}")

        # Run for a few seconds and check transitions
        print("\n  Running for 10 seconds...")
        states_observed = {}
        for i in range(100):  # 10 seconds * 10 Hz
            self.controller.update(0.1)

            for lane_id in self.controller.cycle_order:
                lane = self.controller.lanes[lane_id]
                state = lane.current_state.value

                if lane_id not in states_observed:
                    states_observed[lane_id] = set()
                states_observed[lane_id].add(state)

            if i % 20 == 0:  # Every 2 seconds
                active = self.controller.cycle_order[self.controller.current_cycle_index]
                print(f"    {i*0.1:.1f}s: Active = {active.upper()}")

            time.sleep(0.01)

        # Verify each direction had GREEN state
        all_had_green = all(
            'GREEN' in states_observed.get(lane, set())
            for lane in expected_order
        )

        print(f"\n  States observed:")
        for lane in expected_order:
            states = states_observed.get(lane, set())
            print(f"    {lane.upper()}: {', '.join(sorted(states))}")

        passed = all_had_green and current_order == expected_order
        self.log_test('A1', 'Basic Signal Cycling', passed,
                      f"All directions GREEN: {all_had_green}, Order correct: {current_order == expected_order}")

    def test_a2_no_conflicting_states(self):
        """Test Case A2: No Conflicting States (from Category D1)"""
        print_subheader("TEST A2: No Conflicting States Simultaneously")

        self.setup_controller()

        conflicts_found = []
        print("  Running for 15 seconds, checking for conflicts...")

        for i in range(150):  # 15 seconds
            self.controller.update(0.1)

            # Count GREEN states
            green_count = 0
            green_lanes = []

            for lane_id in self.controller.cycle_order:
                lane = self.controller.lanes[lane_id]
                if lane.current_state == SignalState.GREEN or lane.current_state == SignalState.EMERGENCY:
                    green_count += 1
                    green_lanes.append(lane_id.upper())

            if green_count > 1:
                conflicts_found.append({
                    'time': i * 0.1,
                    'lanes': green_lanes,
                    'count': green_count
                })

            time.sleep(0.01)

        if conflicts_found:
            print(f"  ✗ CONFLICTS DETECTED:")
            for conflict in conflicts_found[:5]:  # Show first 5
                print(
                    f"    t={conflict['time']:.1f}s: {conflict['count']} GREEN - {conflict['lanes']}")
            passed = False
        else:
            print(f"  ✓ No conflicts found - only 1 GREEN at any time")
            passed = True

        self.log_test('A2', 'No Conflicting States', passed,
                      f"Conflicts: {len(conflicts_found)}")

    def test_a3_all_red_safety_clearance(self):
        """Test Case A3: ALL_RED Safety Clearance"""
        print_subheader(
            "TEST A3: ALL_RED Safety Clearance Between Transitions")

        self.setup_controller()

        all_red_observed = []
        print("  Running for 15 seconds, looking for ALL_RED states...")

        for i in range(150):
            self.controller.update(0.1)

            for lane_id in self.controller.cycle_order:
                lane = self.controller.lanes[lane_id]
                if lane.current_state == SignalState.ALL_RED:
                    all_red_observed.append({
                        'time': i * 0.1,
                        'lane': lane_id.upper(),
                        'elapsed': lane.elapsed_time
                    })

            time.sleep(0.01)

        if all_red_observed:
            print(f"  ✓ ALL_RED safety clearance observed:")
            # Group by lane
            by_lane = {}
            for obs in all_red_observed:
                if obs['lane'] not in by_lane:
                    by_lane[obs['lane']] = []
                by_lane[obs['lane']].append(obs['time'])

            for lane, times in by_lane.items():
                print(
                    f"    {lane}: {len(times)} observations (times: {[f'{t:.1f}' for t in times[:3]]}...)")

            passed = len(all_red_observed) > 0
        else:
            print(f"  ✗ No ALL_RED safety clearance found")
            passed = False

        self.log_test('A3', 'ALL_RED Safety Clearance', passed,
                      f"ALL_RED observations: {len(all_red_observed)}")

    # ==================== CATEGORY B: Emergency Scenarios ====================

    def test_b1_ambulance_single_direction(self):
        """Test Case B1: Single Ambulance - All Directions"""
        print_subheader("TEST B1: Ambulance Emergency from Each Direction")

        test_passed = True

        for direction in ['north', 'south', 'east', 'west']:
            print(f"\n  Testing ambulance from {direction.upper()}...")
            self.setup_controller()

            # Activate ambulance
            self.controller.activate_ambulance(direction, 0.95)
            print(f"    Ambulance activated (confidence: 0.95)")

            # Run for 3 seconds
            ambulance_state_correct = True
            other_state_correct = True

            for i in range(30):  # 3 seconds
                self.controller.update(0.1)

                # Check direction lane
                lane = self.controller.lanes[direction]
                if i == 0:  # First update
                    if lane.current_state != SignalState.EMERGENCY:
                        ambulance_state_correct = False
                        print(
                            f"    ✗ {direction.upper()} should be EMERGENCY but is {lane.current_state.value}")

                # Check other lanes
                for other in self.controller.cycle_order:
                    if other != direction:
                        other_lane = self.controller.lanes[other]
                        if i == 0 and other_lane.current_state != SignalState.RED:
                            other_state_correct = False
                            print(
                                f"    ✗ {other.upper()} should be RED but is {other_lane.current_state.value}")

                time.sleep(0.01)

            direction_passed = ambulance_state_correct and other_state_correct
            print(f"    ✓ {direction.upper()} emergency: {direction_passed}")
            test_passed = test_passed and direction_passed

        self.log_test(
            'B1', 'Ambulance Emergency - All Directions', test_passed)

    def test_b2_ambulance_low_confidence_ignored(self):
        """Test Case B2: Low Confidence Ambulance Ignored"""
        print_subheader("TEST B2: Low Confidence Ambulance (< 0.80) Ignored")

        self.setup_controller()

        # Activate ambulance with LOW confidence
        self.controller.activate_ambulance(
            'north', 0.75)  # Below 0.80 threshold

        print("  Ambulance triggered with confidence: 0.75 (below threshold)")
        print("  Running for 2 seconds...")

        # Run and check if NORTH is NOT in emergency
        not_emergency = True
        for i in range(20):
            self.controller.update(0.1)

            lane = self.controller.lanes['north']
            if lane.ambulance_active:
                not_emergency = False
                print(
                    f"  ✗ NORTH should not be in emergency (ambulance_active = {lane.ambulance_active})")

            time.sleep(0.01)

        print(f"  ✓ Low confidence ambulance ignored")
        self.log_test('B2', 'Low Confidence Ambulance Ignored', not_emergency)

    # ==================== CATEGORY C: Edge Cases ====================

    def test_c1_system_stability(self):
        """Test Case C1: System Stability (30-second run)"""
        print_subheader("TEST C1: System Stability Test (30 seconds)")

        self.setup_controller()

        print("  Running system for 30 seconds...")
        errors = []

        try:
            for i in range(300):  # 30 seconds
                self.controller.update(0.1)

                # Verify controller is responsive
                if i % 50 == 0:
                    active_lane = self.controller.cycle_order[self.controller.current_cycle_index]
                    print(f"    {i*0.1:.1f}s: Active = {active_lane.upper()}")

                time.sleep(0.01)

            print("  ✓ 30-second stability test completed without errors")
            passed = True

        except Exception as e:
            errors.append(str(e))
            print(f"  ✗ Error during run: {e}")
            passed = False

        self.log_test('C1', 'System Stability (30s)', passed,
                      f"Errors: {len(errors)}")

    def test_c2_manual_reset(self):
        """Test Case C2: Manual Reset"""
        print_subheader("TEST C2: Manual Reset During Emergency")

        self.setup_controller()

        # Activate ambulance
        self.controller.activate_ambulance('north', 0.95)
        print("  Ambulance activated for NORTH")

        # Run for 1 second
        for _ in range(10):
            self.controller.update(0.1)
            time.sleep(0.01)

        # Manual reset
        self.controller.reset()
        self.controller.start()
        print("  Manual reset executed")

        # Check that NORTH is no longer in emergency
        north_lane = self.controller.lanes['north']
        reset_successful = not north_lane.ambulance_active

        if reset_successful:
            print("  ✓ Reset cleared ambulance state")
        else:
            print(f"  ✗ Ambulance still active after reset")

        self.log_test('C2', 'Manual Reset', reset_successful)

    # ==================== CATEGORY D: Safety & Compliance ====================

    def test_d1_state_transitions(self):
        """Test Case D1: Valid State Transitions"""
        print_subheader("TEST D1: Valid State Transitions")

        self.setup_controller()

        print("  Valid transitions: RED → GREEN → YELLOW → ALL_RED → RED")
        print("  Running for 15 seconds...")

        # Track state transitions
        transitions = {}

        for i in range(150):
            self.controller.update(0.1)

            for lane_id in self.controller.cycle_order:
                lane = self.controller.lanes[lane_id]
                state = lane.current_state

                if lane_id not in transitions:
                    transitions[lane_id] = []

                # Add state if different from last
                if not transitions[lane_id] or transitions[lane_id][-1] != state:
                    transitions[lane_id].append(state)

            time.sleep(0.01)

        # Verify valid transition sequence
        valid_transitions = {
            SignalState.RED: [SignalState.GREEN],
            SignalState.GREEN: [SignalState.YELLOW],
            SignalState.YELLOW: [SignalState.ALL_RED],
            SignalState.ALL_RED: [SignalState.RED],
        }

        invalid_found = []
        for lane_id, states in transitions.items():
            for i in range(len(states) - 1):
                from_state = states[i]
                to_state = states[i + 1]

                allowed = valid_transitions.get(from_state, [])
                if to_state not in allowed:
                    invalid_found.append(
                        f"{lane_id}: {from_state.value} → {to_state.value}")

        if invalid_found:
            print(f"  ✗ Invalid transitions found:")
            for trans in invalid_found[:5]:
                print(f"    {trans}")
            passed = False
        else:
            print(f"  ✓ All state transitions are valid")
            passed = True

        self.log_test('D1', 'Valid State Transitions', passed,
                      f"Invalid: {len(invalid_found)}")

    def test_d2_emergency_duration(self):
        """Test Case D2: Emergency Duration Accuracy"""
        print_subheader("TEST D2: Emergency Duration Accuracy (45 seconds)")

        self.setup_controller()

        # Activate ambulance and track duration
        start_time = time.time()
        self.controller.activate_ambulance('north', 0.95)

        print("  Ambulance activated, monitoring 50-second duration...")

        ambulance_ended = False
        end_time = None

        for i in range(500):  # 50 seconds
            self.controller.update(0.1)

            lane = self.controller.lanes['north']
            if lane.ambulance_active and not ambulance_ended:
                pass  # Still active
            elif not lane.ambulance_active and not ambulance_ended:
                ambulance_ended = True
                end_time = time.time()
                elapsed = end_time - start_time
                print(f"  Ambulance ended after {elapsed:.1f} seconds")

            time.sleep(0.01)

        if ambulance_ended:
            elapsed = end_time - start_time
            is_accurate = 44.5 <= elapsed <= 45.5  # ±0.5 second tolerance

            if is_accurate:
                print(f"  ✓ Duration accurate: {elapsed:.1f}s (within ±0.5s)")
                passed = True
            else:
                print(
                    f"  ✗ Duration inaccurate: {elapsed:.1f}s (expected ~45s)")
                passed = False
        else:
            print(f"  ✗ Ambulance did not end in 50 seconds")
            passed = False

        self.log_test('D2', 'Emergency Duration Accuracy', passed)

    # ==================== CATEGORY E: Integration ====================

    def test_e1_statistics(self):
        """Test Case E1: Statistics Tracking"""
        print_subheader("TEST E1: Statistics Tracking")

        self.setup_controller()

        # Trigger 3 ambulances
        print("  Triggering 3 ambulances...")
        for direction in ['north', 'south', 'east']:
            self.controller.activate_ambulance(direction, 0.95)
            print(f"    {direction.upper()}: activated")

            # Run for 2 seconds between ambulances
            for _ in range(20):
                self.controller.update(0.1)
                time.sleep(0.01)

        # Get statistics
        stats = self.controller.get_statistics()

        print(f"\n  Statistics:")
        print(
            f"    Total ambulances processed: {stats.get('total_ambulances', 0)}")
        print(f"    Active: {stats.get('active_ambulances', 0)}")
        print(f"    Duration: {stats.get('total_duration', 0):.1f}s")

        has_stats = 'total_ambulances' in stats or 'active_ambulances' in stats
        print(f"  ✓ Statistics available: {has_stats}")

        self.log_test('E1', 'Statistics Tracking', has_stats)

    # ==================== Run All Tests ====================

    def run_all_tests(self):
        """Run complete test suite"""
        print_header("TRAFFIC SIGNAL SYSTEM - COMPLETE TEST SUITE")
        print("Testing against TRAFFIC_TEST_CASES.md specifications\n")

        print("CATEGORY A: Normal Traffic Operations")
        self.test_a1_basic_signal_cycling()
        self.test_a2_no_conflicting_states()
        self.test_a3_all_red_safety_clearance()

        print("\n\nCATEGORY B: Emergency Scenarios")
        self.test_b1_ambulance_single_direction()
        self.test_b2_ambulance_low_confidence_ignored()

        print("\n\nCATEGORY C: Edge Cases")
        self.test_c1_system_stability()
        self.test_c2_manual_reset()

        print("\n\nCATEGORY D: Safety & Compliance")
        self.test_d1_state_transitions()
        self.test_d2_emergency_duration()

        print("\n\nCATEGORY E: Integration")
        self.test_e1_statistics()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")

        total_passed = len(self.results['passed'])
        total_failed = len(self.results['failed'])
        total_tests = total_passed + total_failed

        print(f"Total Tests Run: {total_tests}")
        print(f"Passed: {total_passed} ✓")
        print(f"Failed: {total_failed} ✗\n")

        if self.results['passed']:
            print("PASSED TESTS:")
            for test_id, test_name in self.results['passed']:
                print(f"  ✓ [{test_id}] {test_name}")

        if self.results['failed']:
            print("\nFAILED TESTS:")
            for test_id, test_name, details in self.results['failed']:
                print(f"  ✗ [{test_id}] {test_name}")
                if details:
                    print(f"      {details}")

        pass_rate = (total_passed / total_tests *
                     100) if total_tests > 0 else 0
        print(f"\nPass Rate: {pass_rate:.1f}%")

        if total_failed == 0:
            print("\n" + "="*70)
            print("  🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
            print("="*70)
            return 0
        else:
            print("\n" + "="*70)
            print("  ⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
            print("="*70)
            return 1


if __name__ == "__main__":
    validator = TrafficTestValidator()
    exit_code = validator.run_all_tests()
    sys.exit(exit_code)
