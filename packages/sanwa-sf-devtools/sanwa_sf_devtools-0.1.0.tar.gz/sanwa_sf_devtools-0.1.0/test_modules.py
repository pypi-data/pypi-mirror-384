#!/usr/bin/env python3
"""
Simple test script to verify module functionality
"""

import sys
from pathlib import Path

# Add the sf_devtools package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sf_devtools.core.common import logger, config
from sf_devtools.modules.core_package import core_package_manager
from sf_devtools.modules.scratch_org import scratch_org_manager
from sf_devtools.modules.mes_package import mes_package_manager

def test_imports():
    """Test that all modules import correctly."""
    logger.info("Testing module imports...")
    
    # Test config
    logger.info(f"Project root: {config.project_root}")
    logger.info(f"Config dir: {config.config_dir}")
    
    # Test module instances
    logger.info(f"Core package manager: {core_package_manager}")
    logger.info(f"Scratch org manager: {scratch_org_manager}")
    logger.info(f"MES package manager: {mes_package_manager}")
    
    logger.success("All modules imported successfully!")

if __name__ == "__main__":
    test_imports()