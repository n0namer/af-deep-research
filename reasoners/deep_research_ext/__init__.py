"""Upgrade-friendly verified Deep Research extension layer."""
from .bootstrap import install_verified_deep_research
from .methodology import select_methodology
from .task_contract import build_answer_contract
__all__ = ["build_answer_contract", "install_verified_deep_research", "select_methodology"]
