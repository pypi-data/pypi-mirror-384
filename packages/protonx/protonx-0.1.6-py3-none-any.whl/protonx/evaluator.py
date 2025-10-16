from typing import Any, Dict, List, Union, Optional
from ._http import HTTPClient

class Evaluator:
    """
    ProtonX Evaluator API wrapper
    Usage:
        client.evals().eval_llm_answer(
            metrics=['f1'],
            questions=['What is AI?'],
            response_llms=['AI is artificial intelligence'],
            ground_truths=['AI stands for artificial intelligence'],
            contexts=['AI context']
        )
    """
    def __init__(self, http: HTTPClient):
        self._http = http
    
    def eval_llm_answer(self, 
             metrics: Optional[Union[str, List[str]]] = None,
             questions: Optional[Union[str, List[str]]] = None,
             response_llms: Optional[Union[str, List[str]]] = None,
             ground_truths: Optional[Union[str, List[str]]] = None,
             contexts: Optional[Union[str, List[str]]] = None,
             **kwargs: Any
        ) -> List:

        payload = self._build_payload(
            metrics=metrics,
            questions=questions,
            response_llms=response_llms,
            ground_truths=ground_truths,
            contexts=contexts,
            **kwargs
        )
        
        return self._http.post("/eval_llm_answer/", payload)
    
    def _build_payload(self, **fields: Any) -> Dict[str, Any]:
        payload = {}

        for key, value in fields.items():
            if value is not None:
                payload[key] = [value] if isinstance(value, str) else value
        
        return payload