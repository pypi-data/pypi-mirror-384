from typing import Any, Dict, List, Union
from ._http import HTTPClient

class TextNormalizer:
    """
    ProtonX TextNormalizer API wrapper
    Usage:
        client.text.correct(input = "Toi di hoc")
    """

    def __init__(self, http: HTTPClient):
        self._http = http

    def correct(self, 
                input: Union[str, List[str]], 
                top_k: int = 1,
                model: str = "protonx-text-correction-v1",
                **kwargs: Any
        ) -> Dict[str, Any]:
        """
        Vietnamese correction
        """
        
        # Validate input is not None
        if input is None:
            raise ValueError("Input cannot be None")
        
        # Convert to list
        if isinstance(input, str):
            texts = [input]
        elif isinstance(input, list):
            texts = input
        else:
            raise TypeError(f"Input must be str or list, got {type(input).__name__}")
        
        # Validate list is not empty
        if len(texts) == 0:
            raise ValueError("Input list cannot be empty")
        
        # Validate no empty strings in list
        if any(not text or not text.strip() for text in texts):
            raise ValueError("Input cannot contain empty or whitespace-only strings")

        payload = {
            "input": texts,
            "top_k": top_k,
            "model": model,
            **kwargs
        }

        return self._http.post("/v1/correction", payload)
        