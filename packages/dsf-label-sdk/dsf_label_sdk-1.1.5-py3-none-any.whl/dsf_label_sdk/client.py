# dsf_label_sdk/client.py
"""Main SDK Client"""

import requests
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin
import time
from functools import wraps
import logging

from . import __version__
from .exceptions import ValidationError, LicenseError, APIError, RateLimitError
from .models import Field, Config, EvaluationResult



logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    # Respetar retry_after del servidor
                    if attempt < max_retries - 1:
                        sleep_time = e.retry_after
                        logger.warning(f"Rate limited. Retrying after {sleep_time}s...")
                        time.sleep(sleep_time)
                    last_exception = e
                except (requests.RequestException, APIError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
            raise last_exception
        return wrapper
    return decorator


class LabelSDK:
       
    BASE_URL = 'https://label-i0ccmc37a-api-dsfuptech.vercel.app/'
    TIERS = {'community', 'professional', 'enterprise'}
    
    def __init__(
        self,
        license_key: Optional[str] = None,
        tier: str = 'community',
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True
    ):
       
        if tier not in self.TIERS:
            raise ValidationError(f"Invalid tier. Must be one of: {self.TIERS}")
        
        self.license_key = license_key
        self.tier = tier
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        
        # Configure session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': f'DSF-Label-SDK-Python/{__version__}'
        })
        
        # Validate license on initialization for premium tiers
        if tier != 'community' and license_key:
            self._validate_license()
    
    def _validate_license(self) -> None:
        """Valida la licencia contra la API con un ping inofensivo."""
        # 1) Evitar trabajo innecesario
        if self.tier == 'community' or not self.license_key:
            return

        # 2) Ping “neutro” (no afecta métricas ni costos)
        dummy_cfg = {'_ping': {'default': 0, 'weight': 0.0, 'criticality': 0.0}}
        dummy_data = {'_ping': 0}

        try:
            resp = self._make_request('evaluate', {
                'data': dummy_data,
                'config': dummy_cfg,
                'tier': self.tier,
                'license_key': self.license_key,
            })

            # 3) Sanidad de respuesta
            api_tier = resp.get('tier')
            if not api_tier:
                raise LicenseError("License validation failed: missing 'tier' in response")
            # Si quieres ser más estricto, exige match exacto con self.tier:
            if api_tier != self.tier:
                raise LicenseError(f"Tier mismatch: expected {self.tier}, got {api_tier}")

        except RateLimitError:
            # Deja que el decorador de reintentos maneje el Retry-After.
            # Si se agotan los reintentos, la excepción sube tal cual.
            raise

        except APIError as e:
            # Traducir 403 a LicenseError; el resto se propaga como APIError
            if getattr(e, "status_code", None) == 403:
                raise LicenseError(f"Invalid license: {e.message}")
            raise

    
    @retry_on_failure(max_retries=3)
    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self.session.post(
                url,
                json=data,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            # Manejar 429 ANTES de otros errores
            if response.status_code == 429:
                error_data = response.json()
                raise RateLimitError(
                    error_data.get('error', 'Rate limited'),
                    retry_after=error_data.get('retry_after', 60),
                    limit=error_data.get('limit')
                )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 403:
                error_data = response.json()
                raise LicenseError(error_data.get('error', 'License error'))
            elif response.status_code >= 400:
                error_data = response.json()
                raise APIError(
                    error_data.get('error', 'API error'),
                    status_code=response.status_code
                )
                
        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    def evaluate(
        self,
        data: Dict[str, Any],
        config: Optional[Union[Dict, Config]] = None,
        custom_confidence: Optional[float] = None
    ) -> EvaluationResult:
     
        # Convert Config object to dict if needed
        if isinstance(config, Config):
            config = config.to_dict()
        
        # Validate inputs
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        if config and not isinstance(config, dict):
            raise ValidationError("Config must be a dictionary or Config object")
        
        # Build request
        request_data = {
            'data': data,
            'config': config or {},
            'tier': self.tier
        }
        
        if self.license_key:
            request_data['license_key'] = self.license_key
        
        if custom_confidence is not None:
            if not 0.0 <= custom_confidence <= 1.0:
                raise ValidationError("Confidence must be between 0.0 and 1.0")
            request_data['confidence_level'] = custom_confidence
        
        # Make request
        response = self._make_request('evaluate', request_data)
        
        # Return structured result
        return EvaluationResult.from_response(response)
    
    def batch_evaluate(
        self,
        data_points: List[Dict[str, Any]],
        config: Optional[Union[Dict, Config]] = None,
        parallel: bool = True
    ) -> List[EvaluationResult]:

        if self.tier == 'community':
            raise LicenseError("Batch evaluation requires professional or enterprise tier")

        if isinstance(config, Config):
            config = config.to_dict()

        if parallel and len(data_points) > 1:
            request_data = {
                'data_batch': data_points,
                'config': config or {},
                'tier': self.tier,
                'license_key': self.license_key
            }

            response = self._make_request('evaluate', request_data)
            scores = response.get('scores', [])  # nuevo formato esperado: list
            conf = (response.get('threshold', None) 
                    if 'threshold' in response 
                    else response.get('confidence_level', 0.65))  # ← (3)

            results: List[EvaluationResult] = []

            if isinstance(scores, list):
                # ← (1) normalizar longitud y tipos
                vals: List[float] = []
                for x in scores:
                    try:
                        vals.append(float(x))
                    except (TypeError, ValueError):
                        vals.append(0.0)

                if len(vals) < len(data_points):
                    vals.extend([0.0] * (len(data_points) - len(vals)))
                elif len(vals) > len(data_points):
                    vals = vals[:len(data_points)]

                for sv in vals:
                    results.append(EvaluationResult(
                        score=sv,
                        tier=response.get('tier', self.tier),
                        confidence_level=conf,
                        metrics=response.get('metrics')
                    ))

            elif isinstance(scores, dict):
                # ← (2) aceptar int y str como llave
                for i in range(len(data_points)):
                    raw = scores.get(i, scores.get(str(i), 0.0))
                    try:
                        sv = float(raw)
                    except (TypeError, ValueError):
                        sv = 0.0
                    results.append(EvaluationResult(
                        score=sv,
                        tier=response.get('tier', self.tier),
                        confidence_level=conf,
                        metrics=response.get('metrics')
                    ))
            else:
                # forma inesperada: devuelve todo 0.0 pero mantiene longitud
                for _ in range(len(data_points)):
                    results.append(EvaluationResult(
                        score=0.0,
                        tier=response.get('tier', self.tier),
                        confidence_level=conf,
                        metrics=response.get('metrics')
                    ))

            return results

        return [self.evaluate(d, config) for d in data_points]

    
    def create_config(self) -> Config:
        """
        Create a new configuration builder.
        
        Returns:
            Config object for building configurations fluently
            
        Example:
            >>> config = sdk.create_config()
            ...     .add_field('temperature', default=20, weight=1.0)
            ...     .add_field('pressure', default=1.0, weight=0.8)
        """
        return Config()
    
    def get_metrics(self) -> Optional[Dict]:
        """
        Get performance metrics (Premium feature).
        
        Returns:
            Dictionary with metrics or None for community tier
        """
        if self.tier == 'community':
            logger.warning("Metrics not available for community tier")
            return None
        
        response = self._make_request('evaluate', {
            'data': {},
            'config': {},
            'tier': self.tier,
            'license_key': self.license_key,
            'get_metrics': True
        })
        
        return response.get('metrics')
    
    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self):
        return f"LabelSDK(tier='{self.tier}', url='{self.base_url}')"