from typing import Any, Awaitable, Callable, Dict
from .models import ExtensionTrace

class UpstreamDeepResearchAdapter:
    """Single compatibility seam between the extension and upstream Deep Research."""
    def __init__(self, execute_deep_research: Callable[..., Awaitable[Any]]):
        self._execute_deep_research = execute_deep_research

    async def execute(self, *, trace: ExtensionTrace, upstream_kwargs: Dict[str, Any]) -> Any:
        result = await self._execute_deep_research(**upstream_kwargs)
        metadata = dict(getattr(result, "metadata", {}) or {})
        metadata["verified_research_extension"] = trace.model_dump()
        if hasattr(result, "model_copy"):
            return result.model_copy(update={"metadata": metadata})
        if hasattr(result, "copy"):
            try:
                return result.copy(update={"metadata": metadata})
            except TypeError:
                pass
        result.metadata = metadata
        return result
