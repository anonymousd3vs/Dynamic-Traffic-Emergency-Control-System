#!/usr/bin/env python3
"""
Test Dynamic Timing Integration - Single Lane Mode
Simulates real vehicle detection for selected lane
"""

import asyncio
import aiohttp
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DynamicTimingTest')


class SingleLaneDynamicTimingSimulator:
    """Simulates vehicle detection for single selected lane."""

    def __init__(self, base_url='http://localhost:8765'):
        self.base_url = base_url
        self.selected_lane = None

    async def select_lane(self, session, lane: str):
        """Select lane for dynamic timing."""
        url = f"{self.base_url}/api/signals/dynamic-timing/select-lane"
        payload = {'lane': lane}

        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.selected_lane = lane
                    logger.info(f"\n✅ Selected Lane: {lane.upper()}")
                    logger.info(f"   Phase: {data.get('phase')}")
                    logger.info(f"   Direction: {data.get('direction')}")
                    return True
                else:
                    logger.error(f"Failed to select lane: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error selecting lane: {e}")
            return False

    async def send_vehicle_count(self, session, count: int):
        """Send vehicle count for selected lane."""
        if not self.selected_lane:
            logger.error("No lane selected!")
            return

        url = f"{self.base_url}/api/signals/dynamic-timing/update-count"
        payload = {'count': count}

        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        f"\n🚗 {self.selected_lane.upper()}: {count} vehicles"
                    )
                    logger.info(
                        f"   Congestion: {data.get('congestion_level')}"
                    )
                    logger.info(
                        f"   ✅ GREEN TIME: {data.get('new_green_time')}s "
                        f"(was {data.get('old_green_time')}s)"
                    )
                else:
                    logger.error(f"Error: {response.status}")
                    return

        except Exception as e:
            logger.error(f"Failed to send vehicle count: {e}")

    async def get_status(self, session):
        """Get current timing status."""
        url = f"{self.base_url}/api/signals/dynamic-timing/status"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("\n" + "="*70)
                    logger.info("📊 CURRENT STATUS")
                    logger.info("="*70)
                    logger.info(
                        f"Selected Lane: {data.get('selected_lane', 'NONE').upper()}")
                    logger.info(f"Vehicle Count: {data.get('vehicle_count')}")
                    logger.info(
                        f"Current Green Time: {data.get('current_green_time')}s")
                    logger.info(
                        f"Congestion Level: {data.get('congestion_level')}")

                    # Show all phase timings
                    logger.info("\nAll Phase Timings:")
                    phases = data.get('phase_timings', {})
                    for phase, timing in phases.items():
                        logger.info(f"  {phase}: {timing}s")
        except Exception as e:
            logger.error(f"Failed to get status: {e}")

    async def test_scenario_1_light_traffic(self, session):
        """Test Scenario 1: Light traffic on EAST lane."""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: Light Traffic on EAST Lane")
        logger.info("="*70)

        await self.select_lane(session, 'east')

        # Light traffic: 2-4 vehicles
        for cycle in range(3):
            count = 2 + cycle
            logger.info(f"\n--- Cycle {cycle+1} ---")
            await self.send_vehicle_count(session, count)
            await asyncio.sleep(2)

    async def test_scenario_2_medium_traffic(self, session):
        """Test Scenario 2: Medium traffic on WEST lane."""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: Medium Traffic on WEST Lane")
        logger.info("="*70)

        await self.select_lane(session, 'west')

        # Medium traffic: 8-12 vehicles
        for cycle in range(3):
            count = 8 + (cycle * 2)
            logger.info(f"\n--- Cycle {cycle+1} ---")
            await self.send_vehicle_count(session, count)
            await asyncio.sleep(2)

    async def test_scenario_3_heavy_traffic(self, session):
        """Test Scenario 3: Heavy traffic on NORTH lane."""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: Heavy Traffic on NORTH Lane")
        logger.info("="*70)

        await self.select_lane(session, 'north')

        # Heavy traffic: 20-35 vehicles
        for cycle in range(3):
            count = 20 + (cycle * 5)
            logger.info(f"\n--- Cycle {cycle+1} ---")
            await self.send_vehicle_count(session, count)
            await asyncio.sleep(2)

    async def test_scenario_4_dynamic_change(self, session):
        """Test Scenario 4: Dynamic change in SOUTH lane."""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: Dynamic Traffic Change on SOUTH Lane")
        logger.info("="*70)

        await self.select_lane(session, 'south')

        # Simulate traffic building up and reducing
        traffic_pattern = [2, 5, 10, 18, 25, 20, 12, 5, 2]

        for cycle, count in enumerate(traffic_pattern):
            logger.info(
                f"\n--- Cycle {cycle+1} ({['Empty', 'Light', 'Light-Med', 'Medium', 'Heavy', 'Heavy', 'Medium', 'Light', 'Empty'][cycle]}) ---")
            await self.send_vehicle_count(session, count)
            await asyncio.sleep(1.5)

    async def test_all_lanes_sequential(self, session):
        """Test Scenario 5: Test all lanes one by one."""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: All Lanes Sequential Testing")
        logger.info("="*70)

        lanes_data = {
            'north': [3, 8, 15, 25],
            'south': [2, 10, 20, 30],
            'east': [4, 6, 12, 28],
            'west': [5, 9, 18, 22]
        }

        for lane, counts in lanes_data.items():
            logger.info(f"\n{'='*70}")
            logger.info(f"Testing Lane: {lane.upper()}")
            logger.info(f"{'='*70}")

            await self.select_lane(session, lane)

            for cycle, count in enumerate(counts):
                logger.info(f"\n--- Cycle {cycle+1} ---")
                await self.send_vehicle_count(session, count)
                await asyncio.sleep(1)

            await asyncio.sleep(1)

    async def run_all_tests(self):
        """Run all test scenarios."""
        async with aiohttp.ClientSession() as session:
            try:
                await self.test_scenario_1_light_traffic(session)
                await asyncio.sleep(2)

                await self.test_scenario_2_medium_traffic(session)
                await asyncio.sleep(2)

                await self.test_scenario_3_heavy_traffic(session)
                await asyncio.sleep(2)

                await self.test_scenario_4_dynamic_change(session)
                await asyncio.sleep(2)

                await self.test_all_lanes_sequential(session)
                await asyncio.sleep(2)

                # Final status
                await self.get_status(session)

            except Exception as e:
                logger.error(f"Error running tests: {e}")

    async def run_continuous(self, lane: str = 'east'):
        """Run continuous simulation for a specific lane."""
        async with aiohttp.ClientSession() as session:
            await self.select_lane(session, lane)
            logger.info(
                f"\n🔄 Running continuous simulation for {lane.upper()}")
            logger.info("   (press Ctrl+C to stop)\n")

            try:
                cycle = 0
                while True:
                    cycle += 1

                    # Simulate realistic vehicle counts
                    import random
                    count = random.randint(0, 35)

                    logger.info(f"Cycle {cycle}: ", end='')
                    await self.send_vehicle_count(session, count)
                    await asyncio.sleep(3)

            except KeyboardInterrupt:
                logger.info("\n⏹️  Continuous simulation stopped")


async def main():
    """Main entry point."""
    import sys

    simulator = SingleLaneDynamicTimingSimulator()

    if len(sys.argv) > 1:
        if sys.argv[1] == 'continuous':
            # Continuous mode: python test_dynamic_timing_live.py continuous [lane]
            lane = sys.argv[2] if len(sys.argv) > 2 else 'east'
            await simulator.run_continuous(lane)
        else:
            # Single lane test: python test_dynamic_timing_live.py [lane]
            lane = sys.argv[1]
            simulator.selected_lane = lane
            logger.info(f"Testing {lane.upper()} lane...\n")
    else:
        # Run all tests
        logger.info("🚀 Starting Dynamic Timing Tests (Single Lane Mode)...")
        logger.info("   Testing how vehicle counts adjust signal timings\n")
        await simulator.run_all_tests()
        logger.info("\n✅ All tests completed!")


if __name__ == '__main__':
    asyncio.run(main())
