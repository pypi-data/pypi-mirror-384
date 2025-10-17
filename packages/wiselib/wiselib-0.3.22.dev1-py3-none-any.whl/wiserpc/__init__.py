"""
WiseRPC - Python gRPC client library for Wisedomise services.

This package provides gRPC client stubs and message types for various Wisedomise services:
- Common: Shared types and utilities
- Delphinus: Core trading and market data service
- Network Radar: Network monitoring and analysis service  
- Wealth Manager: Portfolio and wealth management service
"""

__version__ = "0.1.0"
__author__ = "Wisedomise"
__email__ = "info@wisedomise.com"

# Import all the generated protobuf modules to make them available
try:
    from . import common_pb2
    from . import common_pb2_grpc
    from . import delphinus_pb2
    from . import delphinus_pb2_grpc
    from . import network_radar_pb2
    from . import network_radar_pb2_grpc
    from . import wealth_manager_pb2
    from . import wealth_manager_pb2_grpc
except ImportError as e:
    # Handle case where protobuf modules are not available
    import warnings
    warnings.warn(f"Could not import protobuf modules: {e}", ImportWarning)

# Export the main modules for easy access
__all__ = [
    "common_pb2",
    "common_pb2_grpc", 
    "delphinus_pb2",
    "delphinus_pb2_grpc",
    "network_radar_pb2",
    "network_radar_pb2_grpc",
    "wealth_manager_pb2",
    "wealth_manager_pb2_grpc",
]
