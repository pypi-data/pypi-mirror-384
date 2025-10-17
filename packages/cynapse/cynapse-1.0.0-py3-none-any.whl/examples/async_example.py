"""Example using async monitor with asyncio."""

import asyncio
from cynapse import AsyncMonitor, protect_function

@protect_function
async def fetch_data(source: str) -> dict:
    """Simulate async data fetching."""
    print(f"Fetching data from {source}...")
    await asyncio.sleep(1)
    return {'source': source, 'data': 'sample data'}

@protect_function
async def process_data(data: dict) -> dict:
    """Simulate async data processing."""
    print(f"Processing data from {data['source']}...")
    await asyncio.sleep(0.5)
    data['processed'] = True
    return data

async def main():
    """Main async function with monitoring."""
    print("Starting async monitor...\n")
    
    # use async context manager
    async with AsyncMonitor(interval=2.0) as monitor:
        print("Monitor active\n")
        
        # run async operations
        tasks = [
            fetch_data("api-1"),
            fetch_data("api-2"),
            fetch_data("api-3"),
        ]
        
        results = await asyncio.gather(*tasks)
        print(f"\nFetched {len(results)} items\n")
        
        # process results
        processed = []
        for result in results:
            proc = await process_data(result)
            processed.append(proc)
        
        print(f"Processed {len(processed)} items\n")
        
        # check monitor status
        status = monitor.get_status()
        print(f"Monitor performed {status.checks_performed} checks")
        print(f"Detected {status.tamper_events} tamper events")
    
    print("\nMonitor stopped automatically")

if __name__ == "__main__":
    asyncio.run(main())
