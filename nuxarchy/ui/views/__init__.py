"""
NUXARCHY Views Package
"""

from nuxarchy.ui.views.dashboard_view import DashboardView
from nuxarchy.ui.views.performance_view import PerformanceView
from nuxarchy.ui.views.thermal_view import ThermalView
from nuxarchy.ui.views.gpu_view import GpuView
from nuxarchy.ui.views.lighting_view import LightingView
from nuxarchy.ui.views.network_booster_view import NetworkBoosterView
from nuxarchy.ui.views.optimizer_view import OptimizerView

__all__ = [
    "DashboardView",
    "PerformanceView",
    "ThermalView",
    "GpuView",
    "LightingView",
    "NetworkBoosterView",
    "OptimizerView",
]
