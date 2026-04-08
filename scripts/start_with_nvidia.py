#!/usr/bin/env python3
"""Start Pi Agent Boss with external NVIDIA model support."""

import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Set UTF-8 for Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set environment variable
os.environ["NVIDIA_API_KEY"] = "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"

print("="*70)
print(" STARTING PI AGENT BOSS WITH EXTERNAL NVIDIA MODEL")
print("="*70)
print()
print(f"API Key: {os.environ['NVIDIA_API_KEY'][:20]}...")
print(f"Config: config/external_apis.yaml")
print(f"Mode: BOSS")
print()

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Also add scripts directory
sys.path.insert(0, str(project_root / "scripts"))

# Import and run
from benchmark.pi_agent_boss import PiAgentBoss, AgentMode
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    agent = PiAgentBoss(
        ollama_base_url="http://localhost:11434",
        router_api_url="http://localhost:8000",
        mode=AgentMode.BOSS,
        state_dir="pi_agent_state",
        external_api_config="config/external_apis.yaml",
        discovery_interval=600,
        health_check_interval=60,
    )

    try:
        await agent.start()
    except KeyboardInterrupt:
        print("\nShutting down Pi Agent...")
        agent.stop()

if __name__ == "__main__":
    asyncio.run(main())
