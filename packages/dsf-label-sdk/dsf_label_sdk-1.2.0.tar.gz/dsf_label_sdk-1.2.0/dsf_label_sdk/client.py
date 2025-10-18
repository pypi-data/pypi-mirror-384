# dsf_label_sdk/client.py
"""Main SDK Client with Async Support"""

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
            logger.error(f"Request failed after {max_retries} attempts: {last_exception}")
            raise last_exception
        return wrapper
    return decorator

class LabelSDK:
    """
    SDK cliente para DSF Label API.
    Soporta evaluaciones síncronas y asíncronas.
    """
    
    # CAMBIO: Base URL ahora apunta a Vercel (no Cloud Run)
    BASE_URL = 'https://label-5b3yk5c9e-api-dsfuptech.vercel.app/api/evaluate'
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
        """
        Inicializa el cliente SDK.
        
        Args:
            license_key: Clave de licencia para tiers premium
            tier: Tier de servicio (community, professional, enterprise)
            base_url: URL base de la API (default: Vercel)
            timeout: Timeout para requests HTTP
            max_retries: Número máximo de reintentos
            verify_ssl: Verificar certificados SSL
        """
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
        if self.tier == 'community' or not self.license_key:
            return

        dummy_cfg = {'_ping': {'default': 0, 'weight': 0.0, 'criticality': 0.0}}
        dummy_data = {'_ping': 0}

        try:
            resp = self._make_request('', {
                'data': dummy_data,
                'config': dummy_cfg,
                'tier': self.tier,
                'license_key': self.license_key,
            })

            api_tier = resp.get('tier')
            if not api_tier:
                raise LicenseError("License validation failed: missing 'tier' in response")
            if api_tier != self.tier:
                raise LicenseError(f"Tier mismatch: expected {self.tier}, got {api_tier}")

        except RateLimitError:
            raise
        except APIError as e:
            if getattr(e, "status_code", None) == 403:
                raise LicenseError(f"Invalid license: {e.message}")
            raise
    
    @retry_on_failure(max_retries=3, delay=1.5)
    def _make_request(self, endpoint: str, data: dict) -> dict:
        """Realiza request HTTP con reintentos."""
        base = (self.base_url or "").rstrip("/") + "/"
        ep = (endpoint or "").strip().lstrip("/")
        
        if ep in ("", "evaluate"):
            url = base.rstrip("/")
        else:
            url = urljoin(base, ep)

        try:
            resp = self.session.post(url, json=data, timeout=self.timeout, verify=self.verify_ssl)
        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

        # Handle 429 rate limiting
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
            limit = err.get("limit")
            raise RateLimitError(
                err.get("error", "Rate limited by server"),
                retry_after=retry_after_int,
                limit=limit
            )

        # Parse response
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
        """
        Evaluación síncrona simple.
        
        Args:
            data: Datos a evaluar
            config: Configuración de campos
            custom_confidence: Nivel de confianza personalizado
            
        Returns:
            EvaluationResult con el score
        """
        if isinstance(config, Config):
            config = config.to_dict()
        
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")
        
        if config and not isinstance(config, dict):
            raise ValidationError("Config must be a dictionary or Config object")
        
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
        
        response = self._make_request('', request_data)
        
        return EvaluationResult.from_response(response)
    
    def batch_evaluate(
        self,
        data_points: List[Dict[str, Any]],
        config: Optional[Union[Dict, Config]] = None,
        chunk_size: int = 5,
        max_retries: int = 3,
    ) -> List[EvaluationResult]:
        """
        Evaluación batch síncrona (legacy, no recomendado).
        Para batches grandes usar submit_batch_async().
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
            resp = self._make_request("", req)
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
                    resp = self._make_request("", req)
                    chunk_results = self._normalize_batch_response(resp, len(chunk))
                    all_results.extend(chunk_results)
                    break
                except (APIError, requests.RequestException) as e:
                    logger.warning(f"[batch_evaluate] Error chunk {i}/{total_chunks} (attempt {attempt+1}/{max_retries}): {e}")
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
            raw = resp.get("scores", {}).get("scores", [])
        elif isinstance(resp, list):
            raw = resp
        else:
            raw = []

        if raw and isinstance(raw[0], dict):
            raw = [float(x.get("score", 0.0)) for x in raw]

        while len(raw) < expected_len:
            raw.append(0.0)

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
    
    # ----------------------------------
    # NUEVOS MÉTODOS ASYNC
    # ----------------------------------
    
    def submit_batch_async(
        self,
        data_points: List[Dict[str, Any]],
        config: Optional[Union[Dict, Config]] = None
    ) -> str:
        """
        Envía batch a cola asíncrona (recomendado para >50 items).
        
        Args:
            data_points: Lista de datos a evaluar
            config: Configuración de campos
            
        Returns:
            job_id para consultar estado
            
        Example:
            >>> job_id = sdk.submit_batch_async(data, config)
            >>> result = sdk.wait_for_result(job_id)
        """
        if self.tier == "community":
            raise LicenseError("Async batch evaluation requires professional or enterprise tier")
        
        if isinstance(config, Config):
            config = config.to_dict()
        
        _ensure_len("data_points", data_points, MAX_BATCH_EVAL * 10)
        
        request_data = {
            'data_batch': _sanitize_records(data_points),
            'config': _normalize_config_for_wire(config or {}),
            'tier': self.tier,
            'license_key': self.license_key
        }
        
        response = self._make_request('enqueue', request_data)
        job_id = response.get('job_id')
        
        if not job_id:
            raise APIError("Server did not return job_id")
        
        logger.info(f"Async job submitted: {job_id} ({len(data_points)} records)")
        return job_id
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Consulta el estado de un job asíncrono.
        
        Args:
            job_id: ID del job a consultar
            
        Returns:
            Dict con 'status' y opcionalmente 'result' si completado
            
        Status posibles:
            - 'queued': En cola esperando procesamiento
            - 'running': Siendo procesado
            - 'completed': Finalizado exitosamente
            - 'failed': Error en procesamiento
        """
        # Intenta GET primero (más eficiente)
        base = self.base_url.rstrip("/")
        url = f"{base}/status/{job_id}"
        
        try:
            resp = self.session.get(url, timeout=self.timeout, verify=self.verify_ssl)
            if resp.status_code == 200:
                result = resp.json()
                logger.debug(f"Fetched status for job {job_id}: {result.get('status')}")
                return result
        except:
            pass
        
        # Fallback a POST
        request_data = {'job_id': job_id}
        return self._make_request('status', request_data)
    
    def wait_for_result(
        self,
        job_id: str,
        poll_interval: int = 5,
        timeout: int = 300
    ) -> List[EvaluationResult]:
        """
        Espera a que un job se complete con polling.
        
        Args:
            job_id: ID del job a esperar
            poll_interval: Segundos entre consultas de estado
            timeout: Timeout máximo en segundos
            
        Returns:
            Lista de EvaluationResult
            
        Raises:
            TimeoutError: Si excede timeout
            APIError: Si el job falla
        """
        start = time.time()
        
        while True:
            status_resp = self.get_job_status(job_id)
            status = status_resp.get('status')
            
            if status == 'completed':
                result = status_resp.get('result', {})
                scores = result.get('scores', [])
                
                if not scores:
                    raise APIError("Job completed but no scores returned")
                
                return [
                    EvaluationResult(
                        score=float(s),
                        tier=result.get('tier', self.tier),
                        confidence_level=result.get('confidence_level', 0.65),
                        metrics=result.get('metrics')
                    )
                    for s in scores
                ]
            
            elif status == 'failed':
                error_msg = status_resp.get('error', 'Unknown error')
                raise APIError(f"Job failed: {error_msg}")
            
            elif status in ('queued', 'running'):
                elapsed = time.time() - start
                if elapsed > timeout:
                    raise TimeoutError(f"Job {job_id} timed out after {timeout}s")
                
                # Warning si se acerca al timeout
                if elapsed > timeout * 0.8:
                    logger.warning(f"Job {job_id} running >{int((elapsed/timeout)*100)}% of timeout ({elapsed:.1f}s/{timeout}s)")
                
                logger.info(f"Job {job_id} status: {status}, waiting {poll_interval}s...")
                time.sleep(poll_interval)
            
            else:
                raise APIError(f"Unknown job status: {status}")
    
    def batch_evaluate_async(
        self,
        data_points: List[Dict[str, Any]],
        config: Optional[Union[Dict, Config]] = None,
        poll_interval: int = 5,
        timeout: int = 300
    ) -> List[EvaluationResult]:
        """
        Método conveniente: submit + wait en una sola llamada.
        
        Args:
            data_points: Lista de datos a evaluar
            config: Configuración de campos
            poll_interval: Segundos entre consultas
            timeout: Timeout máximo
            
        Returns:
            Lista de EvaluationResult
        """
        job_id = self.submit_batch_async(data_points, config)
        logger.info(f"Batch job submitted: {job_id}")
        return self.wait_for_result(job_id, poll_interval, timeout)
    
    # ----------------------------------
    # MÉTODOS LEGACY
    # ----------------------------------
    
    def create_config(self) -> Config:
        """Crea un builder de configuración."""
        return Config()
    
    def get_metrics(self) -> Optional[Dict]:
        """Obtiene métricas de performance (Premium feature)."""
        if self.tier == 'community':
            logger.warning("Metrics not available for community tier")
            return None
        
        response = self._make_request('', {
            'data': {},
            'config': {},
            'tier': self.tier,
            'license_key': self.license_key,
            'get_metrics': True
        })
        
        return response.get('metrics')
    
    def close(self):
        """Cierra la sesión HTTP."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self):
        return f"LabelSDK(tier='{self.tier}', url='{self.base_url}')"