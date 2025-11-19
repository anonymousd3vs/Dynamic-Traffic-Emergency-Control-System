"""
Test Dynamic Timing Integration
Simulates real vehicle detection and dynamic timing adjustments
"""

import asyncio
import aiohttp
import logging
from datetime import datetime
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DynamicTimingTest')


class DynamicTimingSimulator:
    """Simulates vehicle detection and sends to dynamic timing API."""

    def __init__(self, base_url='http://localhost:8765'):
        self.base_url = base_url
        self.running = False

    async def send_vehicle_count(self, session, lane: str, count: int):
        """Send vehicle count to server."""
        url = f"{self.base_url}/api/signals/vehicle-count"
        payload = {
            'lane': lane,
            'count': count
        }

        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'timing' in data:
                        timing = data['timing']
                        logger.info(
                            f"✅ {lane.upper()}: {count} vehicles → "
                            f"GREEN: {timing['green_duration']}s "
                            f"({timing['congestion_level']}) - {timing['reason']}"
                        )
                    else:
                        logger.warning(f"No timing in response: {data}")
                else:
                    logger.error(f"Error: {response.status}")
        except Exception as e:
            logger.error(f"Failed to send vehicle count: {e}")

    async def simulate_scenario_1_light_traffic(self, session):
        """Scenario 1: Light traffic on all lanes."""
        logger.info("\n" + "="*70)
        logger.info("🚗 SCENARIO 1: Light Traffic (Few vehicles)")
        logger.info("="*70)

        # Light traffic: 2-4 vehicles per lane
        for i in range(5):
            logger.info(f"\n--- Cycle {i+1} ---")
            await self.send_vehicle_count(session, 'north', 2)
            await self.send_vehicle_count(session, 'south', 3)
            await self.send_vehicle_count(session, 'east', 2)
            await self.send_vehicle_count(session, 'west', 4)
            await asyncio.sleep(3)

    async def simulate_scenario_2_heavy_traffic(self, session):
        """Scenario 2: Heavy traffic on specific lanes."""
        logger.info("\n" + "="*70)
        logger.info("🚗🚗🚗 SCENARIO 2: Heavy Traffic (Rush Hour)")
        logger.info("="*70)

        # Heavy traffic: varies from 5-25 vehicles
        scenarios = [
            {'north': 8, 'south': 12, 'east': 25, 'west': 3},
            {'north': 15, 'south': 8, 'east': 20, 'west': 10},
            {'north': 20, 'south': 18, 'east': 5, 'west': 22},
        ]

        for cycle, scenario in enumerate(scenarios):
            logger.info(f"\n--- Cycle {cycle+1} ---")
            for lane, count in scenario.items():
                await self.send_vehicle_count(session, lane, count)
            await asyncio.sleep(3)

    async def simulate_scenario_3_ambulance_with_traffic(self, session):
        """Scenario 3: Ambulance approach (needs full timing)."""
        logger.info("\n" + "="*70)
        logger.info("🚑 SCENARIO 3: Ambulance Incoming + Traffic")
        logger.info("="*70)

        # Before ambulance
        logger.info("\nBefore Ambulance:")
        for lane, count in {'north': 10, 'south': 5, 'east': 8, 'west': 12}.items():
            await self.send_vehicle_count(session, lane, count)
        await asyncio.sleep(2)

        # Ambulance triggered (would be separate API call)
        logger.info("\n🚑 Ambulance triggered on WEST lane!")
        await asyncio.sleep(2)

        # During ambulance (still receiving vehicle counts)
        logger.info("\nDuring Ambulance:")
        for lane, count in {'north': 8, 'south': 3, 'east': 6, 'west': 20}.items():
            await self.send_vehicle_count(session, lane, count)
        await asyncio.sleep(2)

    async def simulate_scenario_4_congestion_increase(self, session):
        """Scenario 4: Gradual congestion increase (realistic)."""
        logger.info("\n" + "="*70)
        logger.info("📈 SCENARIO 4: Gradual Traffic Build-up")
        logger.info("="*70)

        # Gradually increase traffic
        congestion_levels = [
            (1, 1, 1, 1),   # Empty
            (3, 2, 4, 3),   # Light
            (7, 8, 6, 9),   # Moderate
            (15, 12, 18, 16),  # Heavy
            (22, 25, 20, 24),  # Very heavy
        ]

        for cycle, (n, s, e, w) in enumerate(congestion_levels):
            logger.info(
                f"\n--- Cycle {cycle+1} ({['Empty', 'Light', 'Moderate', 'Heavy', 'Critical'][cycle]}) ---")
            await self.send_vehicle_count(session, 'north', n)
            await self.send_vehicle_count(session, 'south', s)
            await self.send_vehicle_count(session, 'east', e)
            await self.send_vehicle_count(session, 'west', w)
            await asyncio.sleep(2)

    async def get_timing_status(self, session):
        """Get current timing status."""
        url = f"{self.base_url}/api/signals/dynamic-timing/status"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("\n" + "="*70)
                    logger.info("📊 DYNAMIC TIMING STATUS")
                    logger.info("="*70)
                    logger.info(f"Timestamp: {data['timestamp']}")
                    logger.info(f"Current Phase: {data['signal_phase']}")
                    logger.info(f"Vehicle Counts: {data['vehicle_counts']}")
                    logger.info("\nCurrent Timings:")
                    for lane, timing in data['timings'].items():
                        if timing:
                            logger.info(
                                f"  {lane.upper()}: {timing['green']}s GREEN "
                                f"({timing['congestion']})"
                            )
        except Exception as e:
            logger.error(f"Failed to get status: {e}")

    async def get_timing_stats(self, session):
        """Get detailed statistics."""
        url = f"{self.base_url}/api/signals/dynamic-timing/stats"
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("\n" + "="*70)
                    logger.info("📈 DYNAMIC TIMING STATISTICS")
                    logger.info("="*70)
                    logger.info(
                        f"Total Updates: {data['total_timing_updates']}")
                    logger.info("\nPer-Lane Statistics:")
                    for lane, stats in data['lanes'].items():
                        logger.info(f"\n  {lane.upper()}:")
                        logger.info(
                            f"    Average Vehicles: {stats['average_vehicle_count']:.1f}")
                        logger.info(
                            f"    Average Green Time: {stats['average_green_duration']:.1f}s")
                        logger.info(
                            f"    Green Range: {stats['min_green_observed']}-{stats['max_green_observed']}s"
                        )
                        logger.info(
                            f"    Total Adjustments: {stats['total_adjustments']}")
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")

    async def run_all_scenarios(self):
        """Run all test scenarios."""
        async with aiohttp.ClientSession() as session:
            try:
                # Scenario 1
                await self.simulate_scenario_1_light_traffic(session)
                await asyncio.sleep(2)

                # Scenario 2
                await self.simulate_scenario_2_heavy_traffic(session)
                await asyncio.sleep(2)

                # Scenario 3
                await self.simulate_scenario_3_ambulance_with_traffic(session)
                await asyncio.sleep(2)

                # Scenario 4
                await self.simulate_scenario_4_congestion_increase(session)
                await asyncio.sleep(2)

                # Get final status
                await self.get_timing_status(session)
                await self.get_timing_stats(session)

            except Exception as e:
                logger.error(f"Error running scenarios: {e}")

    async def run_continuous(self):
        """Run continuous simulation (useful for live testing)."""
        async with aiohttp.ClientSession() as session:
            logger.info(
                "🔄 Starting continuous simulation (press Ctrl+C to stop)")

            try:
                cycle = 0
                while True:
                    cycle += 1
                    logger.info(f"\n=== LIVE UPDATE CYCLE {cycle} ===")

                    # Simulate realistic vehicle counts
                    import random
                    base = random.randint(2, 15)

                    counts = {
                        'north': base + random.randint(-2, 5),
                        'south': base + random.randint(-2, 5),
                        'east': base + random.randint(-2, 5),
                        'west': base + random.randint(-2, 5),
                    }

                    for lane, count in counts.items():
                        await self.send_vehicle_count(session, lane, max(0, count))

                    await self.get_timing_status(session)
                    await asyncio.sleep(5)  # Update every 5 seconds

            except KeyboardInterrupt:
                logger.info("\n⏹️  Continuous simulation stopped")


async def main():
    """Main entry point."""
    import sys

    simulator = DynamicTimingSimulator()

    if len(sys.argv) > 1 and sys.argv[1] == 'continuous':
        await simulator.run_continuous()
    else:
        logger.info("🚀 Starting Dynamic Timing Integration Tests...")
        logger.info("   This will simulate real vehicle detection and show")
        logger.info("   how signal timings adjust automatically.\n")
        await simulator.run_all_scenarios()
        logger.info("\n✅ All scenarios completed!")


if __name__ == '__main__':
    asyncio.run(main())
