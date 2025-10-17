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
from itertools import islice

MAX_BATCH_EVAL = 1000

logger = logging.getLogger(__name__)

def _ensure_len(name: str, seq, max_len: int):
    """Asegura que una lista no exceda una longitud máxima."""
    if isinstance(seq, list) and len(seq) > max_len:
        raise ValidationError(f"{name} es demasiado grande — máximo {max_len}")

def _normalize_config_for_wire(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Ordena las claves del config para consistencia."""
    if not isinstance(cfg, dict):
        return {}
    return {k: cfg[k] for k in sorted(cfg.keys())}

def _sanitize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Limpia los datos para que sean serializables a JSON."""
    # Esta es una versión simplificada. Puedes añadir más lógica si es necesario.
    return records

def _chunked(seq, size):
    """Divide una secuencia en sublotes (chunks) más pequeños."""
    it = iter(seq)
    return iter(lambda: list(islice(it, size)), [])

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
       
    BASE_URL = 'https://label-bg0vkr1gi-api-dsfuptech.vercel.app/'
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

    
    @retry_on_failure(max_retries=3, delay=1.5)
    def _make_request(self, endpoint: str, data: dict) -> dict:
        # 1) Routing: evaluate/''/'/' => raíz
        base = (self.base_url or "").rstrip("/") + "/"
        ep = (endpoint or "").strip().lstrip("/")
        if ep in ("", "evaluate"):
            url = base
        else:
            url = urljoin(base, ep)

        try:
            resp = self.session.post(url, json=data, timeout=self.timeout, verify=self.verify_ssl)
        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

        # 2) 429: respetar Retry-After y no depender de JSON válido
        if resp.status_code == 429:
            try:
                err = resp.json()
            except ValueError:
                err = {}
            retry_after = err.get("retry_after") or resp.headers.get("Retry-After", "60")
            try:
                retry_after_int = int(retry_after)
            except (ValueError, TypeError):
                retry_after_int = 60
            # si tu RateLimitError acepta 'limit', pásalo también
            limit = err.get("limit")
            raise RateLimitError(err.get("error", "Rate limited by server"),
                                retry_after=retry_after_int,
                                limit=limit)

        # 3) Parseo seguro del resto de respuestas
        try:
            j = resp.json()
        except ValueError:
            j = {}

        if resp.status_code >= 400:
            msg = j.get("error", f"API returned HTTP {resp.status_code}")
            if resp.status_code == 403:
                raise LicenseError(msg)
            raise APIError(msg, status_code=resp.status_code)

        return j

    
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
        chunk_size: int = 25,
        max_retries: int = 3,
    ) -> List[EvaluationResult]:
        """
        Evalúa un lote de puntos de datos, dividiéndolo automáticamente en sublotes
        para evitar timeouts o errores 504 en entornos serverless (como Vercel).
        """
        if self.tier == "community":
            raise LicenseError("Batch evaluation requires professional or enterprise tier")

        if isinstance(config, Config):
            config = config.to_dict()
        config = config or {}

        _ensure_len("data_points", data_points, MAX_BATCH_EVAL * 10)

        if len(data_points) <= chunk_size:
            req = {
                "data_batch": _sanitize_records(data_points),
                "config": _normalize_config_for_wire(config),
                "tier": self.tier,
                "license_key": self.license_key,
            }
            # En tu API, la acción está implícita. Si tuvieras un router,
            # sería "action": "evaluate_batch". Lo dejamos como está.
            resp = self._make_request("evaluate", req) 
            return self._normalize_batch_response(resp, len(data_points))

        all_results: List[EvaluationResult] = []
        total_chunks = (len(data_points) + chunk_size - 1) // chunk_size

        for i, chunk in enumerate(_chunked(data_points, chunk_size), start=1):
            for attempt in range(max_retries):
                try:
                    req = {
                        "data_batch": _sanitize_records(chunk),
                        "config": _normalize_config_for_wire(config),
                        "tier": self.tier,
                        "license_key": self.license_key,
                    }
                    resp = self._make_request("evaluate", req)
                    chunk_results = self._normalize_batch_response(resp, len(chunk))
                    all_results.extend(chunk_results)
                    # Opcional: print(f"✅ Chunk {i}/{total_chunks} procesado.")
                    break
                except (APIError, requests.RequestException) as e:
                    logger.warning(f"⚠️ Error en chunk {i}/{total_chunks} (intento {attempt+1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    else:
                        logger.error(f"❌ Chunk {i}/{total_chunks} omitido tras {max_retries} intentos.")
                        all_results.extend([
                            EvaluationResult(score=0.0, tier=self.tier, confidence_level=0.0)
                            for _ in range(len(chunk))
                        ])
        return all_results

    def _normalize_batch_response(self, resp: dict, expected_len: int) -> List[EvaluationResult]:
        """Normaliza la respuesta de batch_evaluate de forma segura."""
        if isinstance(resp, dict):
            # Asumiendo que tu API devuelve {'scores': [0.1, 0.2, ...]}
            raw = resp.get("scores", {}).get("scores", []) 
        elif isinstance(resp, list):
            raw = resp
        else:
            raw = []

        if raw and isinstance(raw[0], dict):
            raw = [float(x.get("score", 0.0)) for x in raw]

        while len(raw) < expected_len:
            raw.append(0.0)

        # Asegura que la respuesta tenga al menos un score si se espera uno
        if expected_len > 0 and not raw:
            raw = [0.0] * expected_len

        return [
            EvaluationResult(
                score=float(raw[i]),
                tier=self.tier,
                confidence_level=resp.get("threshold", resp.get("confidence_level", 0.65)),
                metrics=resp.get("metrics"),
            )
            for i in range(expected_len)
        ]
    
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