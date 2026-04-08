#!/usr/bin/env python3
"""Start Pi Agent Boss as a ready-to-use local assistant."""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Set UTF-8 for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "scripts" / "benchmark"))

from pi_agent_boss import PiAgentBoss, AgentMode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    print("="*70)
    print(" PI AGENT BOSS - LOCAL ASSISTANT (ACTIVE MODE)")
    print("="*70)
    print()
    print("Mode: ACTIVE (Auto-optimizing routing)")
    print("Pool Management: AUTO")
    print("External APIs: Enabled (NVIDIA)")
    print()

    agent = PiAgentBoss(
        ollama_base_url="http://localhost:11434",
        router_api_url="http://localhost:8000",
        mode=AgentMode.ACTIVE,  # ACTIVE mode - auto-optimize without heavy benchmarking
        state_dir="pi_agent_state",
        external_api_config="config/external_apis.yaml",
        discovery_interval=600,  # Check for new models every 10 min
        health_check_interval=60,  # Health check every minute
        auto_manage_pool=True,  # Automatically manage model pool
        max_disk_size_gb=50.0,  # Maximum disk size for models
        disk_cleanup_threshold=0.90,  # Cleanup at 90% of max (45GB)
    )

    try:
        await agent.start()
    except KeyboardInterrupt:
        print("\n\nShutting down Pi Agent...")
        agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
