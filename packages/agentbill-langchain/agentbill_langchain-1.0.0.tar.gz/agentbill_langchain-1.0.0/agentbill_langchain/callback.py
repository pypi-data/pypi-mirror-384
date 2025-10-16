"""AgentBill LangChain Callback Handler"""

import time
import hashlib
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    from langchain.callbacks.base import BaseCallbackHandler
    from langchain.schema import LLMResult
except ImportError:
    raise ImportError(
        "langchain is not installed. Install with: pip install langchain"
    )

import requests


class AgentBillCallback(BaseCallbackHandler):
    """LangChain callback handler that sends usage data to AgentBill.
    
    Example:
        callback = AgentBillCallback(
            api_key="agb_your_key",
            base_url="https://your-instance.supabase.co",
            customer_id="customer-123"
        )
        
        llm = ChatOpenAI(callbacks=[callback])
        result = llm.invoke("Hello!")
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        customer_id: Optional[str] = None,
        account_id: Optional[str] = None,
        debug: bool = False,
        batch_size: int = 10,
        flush_interval: float = 5.0
    ):
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.customer_id = customer_id
        self.account_id = account_id
        self.debug = debug
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self._active_runs: Dict[str, Dict[str, Any]] = {}
        self._signal_queue: List[Dict[str, Any]] = []
        self._last_flush = time.time()
    
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """Called when LLM starts."""
        run_id = kwargs.get("run_id") or str(UUID(int=0))
        self._active_runs[str(run_id)] = {
            "start_time": time.time(),
            "prompts": prompts,
        }
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM ends."""
        run_id = str(kwargs.get("run_id", ""))
        run_info = self._active_runs.pop(run_id, None)
        
        if not run_info:
            return
        
        latency_ms = int((time.time() - run_info["start_time"]) * 1000)
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage", {})
        
        signal = {
            "event_name": "langchain_llm_call",
            "metrics": {
                "prompt_tokens": token_usage.get("prompt_tokens", 0),
                "completion_tokens": token_usage.get("completion_tokens", 0),
                "total_tokens": token_usage.get("total_tokens", 0),
            },
            "latency_ms": latency_ms,
            "data_source": "langchain",
        }
        
        if self.customer_id:
            signal["account_external_id"] = self.customer_id
        if self.account_id:
            signal["account_id"] = self.account_id
        
        self._queue_signal(signal)
    
    def _queue_signal(self, signal: Dict[str, Any]) -> None:
        self._signal_queue.append(signal)
        if len(self._signal_queue) >= self.batch_size:
            self.flush()
    
    def flush(self) -> None:
        """Flush queued signals to AgentBill."""
        if not self._signal_queue:
            return
        
        try:
            url = f"{self.base_url}/functions/v1/record-signals"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            response = requests.post(
                url,
                json=self._signal_queue,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self._signal_queue.clear()
                self._last_flush = time.time()
        except Exception as e:
            if self.debug:
                print(f"[AgentBill] Flush error: {e}")
    
    def track_revenue(
        self,
        event_name: str,
        revenue: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track revenue for profitability analysis.
        
        Args:
            event_name: Name of the revenue event
            revenue: Revenue amount in dollars
            metadata: Optional metadata dict
        """
        signal = {
            "event_name": event_name,
            "revenue": revenue,
            "data_source": "langchain",
            "data": metadata or {}
        }
        
        if self.customer_id:
            signal["account_external_id"] = self.customer_id
        if self.account_id:
            signal["account_id"] = self.account_id
        
        self._queue_signal(signal)
    
    def __del__(self):
        """Flush on cleanup."""
        self.flush()