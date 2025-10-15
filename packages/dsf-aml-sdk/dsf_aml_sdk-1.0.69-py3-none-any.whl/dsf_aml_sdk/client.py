# ============================================
# dsf_aml_sdk/client.py (DROP-IN)
# ============================================

from . import __version__
from .models import Config, EvaluationResult, DistillationResult
from .exceptions import APIError, RateLimitError, LicenseError, ValidationError

import requests
from typing import Dict, List, Optional, Union, Any, Iterable, Tuple
from urllib.parse import urljoin
import time
from functools import wraps
import logging
import os
import math
import random

logger = logging.getLogger(__name__)

# --------- Límites tunables por ENV (con defaults seguros) ----------
MAX_N_SYNTHETIC = int(os.getenv("DSF_MAX_N_SYNTHETIC", "10000"))
MAX_PARTIAL_VARIANTS = int(os.getenv("DSF_MAX_PARTIAL_VARIANTS", "5000"))
MAX_DATASET_ITEMS = int(os.getenv("DSF_MAX_DATASET_ITEMS", "10000"))  # límite duro backend
MAX_BATCH_EVAL = int(os.getenv("DSF_MAX_BATCH_EVAL", "1000"))         # evaluate_batch
MAX_BATCH_PREDICT = int(os.getenv("DSF_MAX_BATCH_PREDICT", "2000"))   # translate_predict
DEFAULT_CHUNK = int(os.getenv("DSF_DEFAULT_CHUNK", "800"))            # tamaño chunk por defecto

# --------- Utilidades internas ----------
def _ensure_len(name: str, seq, max_len: int):
    if isinstance(seq, list) and len(seq) > max_len:
        raise ValidationError(f"{name} too large — max {max_len}")

def _normalize_config_for_wire(cfg: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(cfg, dict):
        return {}
    return {k: cfg[k] for k in sorted(cfg.keys())}

# --- [AÑADIR] Helpers de métricas para pipeline_generate_critical ---

def _pg_extract_scalar(resp: dict, key: str, default=0.0):
    try:
        v = resp.get(key, default)
        return float(v) if isinstance(v, (int, float)) else default
    except Exception:
        return default

def _pg_metrics_from_gen_list(gen_list: list) -> dict:
    """Agrega métricas desde partial_metrics.gen_metrics_list (si existen)."""
    if not isinstance(gen_list, list) or not gen_list:
        return {}
    acc_rate_vals = []
    for it in gen_list:
        if isinstance(it, dict):
            # aceptación por iteración (si viene)
            if "acceptance_rate" in it and isinstance(it["acceptance_rate"], (int, float)):
                acc_rate_vals.append(float(it["acceptance_rate"]))
    out = {}
    if acc_rate_vals:
        out["acceptance_rate"] = float(sum(acc_rate_vals) / len(acc_rate_vals))
    return out

def _pg_normalize_result(resp: dict, acc_gen_list: list = None) -> dict:
    """
    Normaliza la salida de pipeline_generate_critical:
      - NO depende de 'quality_metrics'
      - Construye 'metrics' con claves estables
    """
    if not isinstance(resp, dict):
        return {"status": "error", "error": "Malformed response"}

    # 1) Conteos base
    total_generated   = int(resp.get("total_generated", resp.get("critical_generated", 0)) or 0)
    non_critical      = int(resp.get("non_critical_added", 0) or 0)

    # 2) critical_samples puede ser lista o número (contratos previos)
    crit_count_raw = resp.get("critical_samples")
    crit_list = None

    if isinstance(crit_count_raw, list):
        # backend ya trajo la lista
        crit_list = crit_count_raw
        critical_count = len([x for x in crit_list if isinstance(x, dict)])
    elif isinstance(crit_count_raw, (int, float)):
        # backend dio solo conteo → busca la lista en previews
        critical_count = int(crit_count_raw)
        crit_list = resp.get("dataset_preview") or resp.get("critical_preview")
    else:
        # ni lista ni número → intenta previews
        critical_count = 0
        crit_list = resp.get("dataset_preview") or resp.get("critical_preview")

    critical_samples = [x for x in (crit_list or []) if isinstance(x, dict)]

    # 3) Métricas directas del backend (si vienen)
    metrics = {
        "generated": total_generated,
        "critical_count": critical_count,
        "non_critical": non_critical,
    }
    acc_rate = _pg_extract_scalar(resp, "avg_acceptance_rate", None)
    if acc_rate is not None and acc_rate != 0.0:
        metrics["acceptance_rate"] = acc_rate

    bal = _pg_extract_scalar(resp, "balance_ratio", None)
    if bal is not None and bal != 0.0:
        metrics["balance_ratio"] = bal

    # 4) Métricas desde parciales acumulados (opcional)
    gen_list = []
    if isinstance(acc_gen_list, list):
        gen_list.extend(acc_gen_list)
    pm = resp.get("partial_metrics") or {}
    if isinstance(pm, dict) and isinstance(pm.get("gen_metrics_list"), list):
        gen_list.extend(pm["gen_metrics_list"])

    extra = _pg_metrics_from_gen_list(gen_list)
    metrics.update({k: v for k, v in extra.items() if k not in metrics})

    out = {
        "status": resp.get("status", "complete"),
        "total_generated": total_generated,
        "non_critical_added": non_critical,
        "metrics": metrics
    }
    if critical_samples is not None:
        out["critical_samples"] = critical_samples

    # Si es parcial, preserva campos necesarios para el loop de reintento
    if out["status"] == "partial":
        out.update({
            "cursor": resp.get("cursor", 0),
            "retry_after": resp.get("retry_after", 2),
            "partial_results": resp.get("partial_results", []),
            "partial_metrics": resp.get("partial_metrics", {}),
        })
    return out


def _chunked(seq: List[Any], chunk: int) -> Iterable[List[Any]]:
    for i in range(0, len(seq), chunk):
        yield seq[i:i + chunk]

def _to_serializable(v: Any) -> Any:
    try:
        import numpy as np
        if isinstance(v, (np.generic,)):
            return v.item()
        if isinstance(v, (np.ndarray,)):
            return v.tolist()
    except Exception:
        pass
    if isinstance(v, (float, int, str, bool)) or v is None:
        return v
    if isinstance(v, (complex,)):
        return float(v)
    # fallback seguro:
    return str(v)  # 👈 antes devolvías v; mejor serializar a str


def _sanitize_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    return {str(k): _to_serializable(v) for k, v in rec.items()}

def _sanitize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [_sanitize_record(r) for r in records]

def _global_near_threshold(scores: List[float], top_k_percent: float) -> List[int]:
    # Selección por distancia a la mediana global
    if not scores:
        return []
    thr = float(_median(scores))
    distances = [abs(s - thr) for s in scores]
    k = max(1, int(len(scores) * float(top_k_percent)))
    return sorted(range(len(scores)), key=lambda i: distances[i])[:k]

def _median(a: List[float]) -> float:
    b = sorted(a)
    n = len(b)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 0:
        return (b[mid - 1] + b[mid]) / 2.0
    return b[mid]

def _cap_list(lst: List[Any], cap: int, seed: int = 42) -> List[Any]:
    if len(lst) <= cap:
        return lst
    random.Random(seed).shuffle(lst)
    return lst[:cap]

# --------- Decorador de reintentos ----------
def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, APIError) as e:
                    last_exception = e
                    # Respeta Retry-After si viene (429/503); aplica jitter y cap
                    ra = getattr(e, "retry_after", None)
                    if ra is not None and getattr(e, "status_code", None) in (429, 503):
                        sleep_s = max(1, min(int(ra), 120)) + random.random()
                    else:
                        # backoff exponencial (previo comportamiento)
                        sleep_s = delay * (2 ** attempt)
                    if attempt < max_retries - 1:
                        time.sleep(sleep_s)
            raise last_exception
        return wrapper
    return decorator

def retry_on_failure(max_retries: int = 3, base_backoff: float = 1.5):
    """Decorator to retry failed requests with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None
            
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                    
                except RateLimitError as e:
                    last_exception = e
                    sleep_time = max(1, e.retry_after)
                    print(f"⚠️ Rate limited. Retrying after {sleep_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(sleep_time)
                    attempt += 1
                    
                except (requests.RequestException, APIError) as e:
                    last_exception = e
                    attempt += 1
                    if attempt >= max_retries:
                        raise
                    sleep_time = base_backoff ** attempt
                    print(f"⚠️ Request failed. Retrying in {sleep_time:.1f}s (attempt {attempt}/{max_retries})")
                    time.sleep(sleep_time)
                    
            raise last_exception
            
        return wrapper
    return decorator

class AMLSDK:
    BASE_URL = os.environ.get(
        "DSF_AML_BASE_URL",
        "https://dsf-4rgd1gbv0-api-dsfuptech.vercel.app/"
    )
    TIERS = {"community", "professional", "enterprise"}

    def __init__(
        self,
        license_key: Optional[str] = None,
        tier: str = "community",
        base_url: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True,
        validate_on_init: bool = False
    ):
        if tier not in self.TIERS:
            raise ValidationError(f"Invalid tier. Allowed: {self.TIERS}")

        self.license_key = license_key
        self.tier = tier
        self.base_url = base_url or os.getenv("DSF_AML_BASE_URL", self.BASE_URL)
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": f"DSF-AML-SDK-Python/{__version__}"
        })

        if validate_on_init and self.tier != "community" and self.license_key:
            self._validate_license()

        # última config usada (para get_metrics())
        self._last_config: Optional[Dict[str, Any]] = None

    # ---------- Helpers de licencia ----------
    def _validate_license(self):
        req = {
            "data": {},
            "config": {"__probe__": {"default": 0, "weight": 1.0, "criticality": 1.0}},
            "license_key": self.license_key,
        }
        resp = self._make_request("", req)
        if not isinstance(resp, dict):
            raise LicenseError("License validation failed (unexpected response)")

    def _ensure_license_if_needed(self):
        if self.tier != "community" and self.license_key:
            try:
                self._validate_license()
            except Exception:
                logger.warning("License pre-check failed; relying on server-side enforcement")

    # ---------- HTTP ----------
    @retry_on_failure(max_retries=3, base_backoff=1.5)
    def _make_request(self, endpoint: str, data: dict) -> dict:
        """
        Make HTTP POST request to the API endpoint.
        Handles 429 rate limiting with Retry-After header.
        
        Args:
            endpoint: API endpoint path
            data: Request payload
            
        Returns:
            dict: JSON response from API
            
        Raises:
            RateLimitError: When rate limited (429)
            LicenseError: When license invalid (403)
            APIError: When API returns other error statuses
            requests.RequestException: For network errors
        """
        url = (self.base_url or "").rstrip("/") + "/" + endpoint.lstrip("/")
        
        # Timeout seguro
        timeout = getattr(self, "timeout", 30)
        
        try:
            resp = self.session.post(url, json=data, timeout=timeout, verify=self.verify_ssl)  # ← ESTA LÍNEA
        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
        
        # Manejar 429 ANTES de parsear JSON
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After", "60")
            try:
                retry_after_int = int(retry_after)
            except (ValueError, TypeError):
                retry_after_int = 60
            raise RateLimitError(
                "Rate limited by server", 
                retry_after=retry_after_int, 
                status_code=429
            )
        
        # Parsear JSON de forma segura
        try:
            j = resp.json()
        except ValueError:
            j = {}
        
        # Manejar otros errores con mensajes más útiles
        if resp.status_code >= 400:
            try:
                txt = resp.text[:200]
            except Exception:
                txt = ""
            error_msg = j.get("error") or f"HTTP {resp.status_code}: {txt}"
            context = j.get("context")
            if context:
                error_msg = f"{error_msg} | context={context}"
            
            # Reutiliza las excepciones específicas si aplican
            if resp.status_code == 403:
                raise LicenseError(error_msg)
            
            raise APIError(error_msg, status_code=resp.status_code)
        
        return j


    # ---------- Core ----------
    def get_version_info(self) -> Dict:
        return self._make_request("", {"action": "__version__"})

    def evaluate(self, data: Dict[str, Any], config: Optional[Union[Dict, Config]] = None) -> EvaluationResult:
        if isinstance(config, Config):
            config = config.to_dict()
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")

        config = _normalize_config_for_wire(config or {})
        self._last_config = config

        req = {"data": _sanitize_record(data), "config": config, "tier": self.tier}
        if self.license_key:
            req["license_key"] = self.license_key

        resp = self._make_request("", req)
        return EvaluationResult.from_response(resp)

    def batch_evaluate(self, data_points: List[Dict], config: Optional[Union[Dict, Config]] = None) -> List[EvaluationResult]:
        if self.tier == "community":
            raise LicenseError("Batch evaluation requires premium tier")
        _ensure_len("data_points", data_points, MAX_BATCH_EVAL)

        if config:
            self._last_config = config.to_dict() if isinstance(config, Config) else config
        use_config = self._last_config or {}
        if isinstance(use_config, Config):
            use_config = use_config.to_dict()
        use_config = _normalize_config_for_wire(use_config)

        req = {
            "action": "evaluate_batch",
            "tier": self.tier,
            "license_key": self.license_key,
            "config": use_config,
            "data_points": _sanitize_records(data_points),
        }

        try:
            resp = self._make_request("", req)
            # Normalización
            if isinstance(resp, list):
                raw = resp
            elif isinstance(resp, dict):
                raw = resp.get("scores")
                if raw is None:
                    raw = [resp.get(i, resp.get(str(i), 0.0)) for i in range(len(data_points))]
            else:
                raw = []

            if raw and isinstance(raw[0], dict):
                raw = [float(x.get("score", 0.0)) for x in raw]

            return [
                EvaluationResult(score=float(raw[i]) if i < len(raw) else 0.0, tier=self.tier)
                for i in range(len(data_points))
            ]
        except APIError:
            # Fallback: secuencial (mantiene contrato)
            return [self.evaluate(dp, use_config) for dp in data_points]

    def bootstrap_config(self, config: Union[Dict, Config]) -> Dict:
        if isinstance(config, Config):
            config = config.to_dict()
        config = _normalize_config_for_wire(config)
        req = {
            "action": "bootstrap_config",
            "config": config,
            "license_key": self.license_key,
        }
        return self._make_request("", req)

    # ---------- Pipelines ----------
    def pipeline_identify_seeds(self, dataset: List[Dict], config: Union[Dict, Config],
                                top_k_percent: float = 0.1, **kwargs) -> Dict:
        cfg = config.to_dict() if hasattr(config, "to_dict") else config
        cfg = _normalize_config_for_wire(cfg)
        req = {
            "action": "pipeline_identify_seeds",
            "dataset": _sanitize_records(dataset),
            "config": cfg,
            "top_k_percent": top_k_percent,
            "license_key": self.license_key,
            **kwargs
        }
        return self._make_request("", req)

    def pipeline_identify_seeds_safe(
        self,
        dataset: List[Dict],
        config: Union[Dict, Config],
        top_k_percent: float = 0.3,
        chunk_size: int = DEFAULT_CHUNK
    ) -> Dict:
        """
        Selecciona seeds localmente:
        1) batch_evaluate en chunks (≤MAX_BATCH_EVAL)
        2) near-threshold global por distancia a la mediana
        3) devuelve contrato parecido a pipeline_identify_seeds
        """
        if self.tier == "community":
            raise LicenseError("Seeds selection in batch requires premium tier")

        chunk = max(1, min(int(chunk_size), MAX_BATCH_EVAL))
        ds = _sanitize_records(list(dataset))
        # scoring local
        scores: List[float] = []
        for part in _chunked(ds, chunk):
            part_scores = self.batch_evaluate(part, config)
            scores.extend([r.score for r in part_scores])

        idx = _global_near_threshold(scores, top_k_percent)
        seeds = [{"data": ds[i], "uncertainty": abs(scores[i] - float(_median(scores)))} for i in idx]
        return {
            "pipeline": "client_near_threshold",
            "seeds_count": len(seeds),
            "seeds": seeds,
            "scores_summary": {
                "median": float(_median(scores)),
                "avg": float(sum(scores) / max(1, len(scores))),
                "min": float(min(scores)) if scores else 0.0,
                "max": float(max(scores)) if scores else 0.0,
            }
        }

    def pipeline_generate_critical(self, config, seeds=None, advanced=None, **kwargs):
        if self.tier == 'community':
            raise LicenseError("Pipeline requires premium tier")

        cfg = config.to_dict() if hasattr(config, "to_dict") else config
        cfg = _normalize_config_for_wire(cfg)

        req = {
            'action': 'pipeline_generate_critical',
            'config': cfg,
            'license_key': self.license_key,
        }

        # Auto-seeds si no las pasan pero sí hay dataset original
        original_ds = kwargs.get('original_dataset')
        if seeds is None and original_ds:
            tkp = kwargs.get('top_k_percent', 0.1)
            sresp = self.pipeline_identify_seeds_safe(dataset=original_ds, config=cfg, top_k_percent=tkp)
            seeds = [s.get('data', s) for s in (sresp.get('seeds') or [])]

        # Cap y saneo de seeds (solo variantes/muestras)
        if seeds:
            max_seeds = min(300, max(100, int(0.1 * len(original_ds or [])) if original_ds else 300))
            seeds = [_sanitize_record(s.get('data', s) if isinstance(s, dict) else s) for s in seeds][:max_seeds]
            req['seeds'] = seeds

        # Hyperparámetros por defecto prudentes
        adv = dict(advanced or {})
        adv.setdefault('epsilon', 0.08)
        adv.setdefault('diversity_threshold', 0.92)
        adv.setdefault('non_critical_ratio', 0.15)
        adv.setdefault('max_seeds_to_process', 8)
        adv.setdefault('max_retries', 5)
        adv.setdefault('require_middle', False)
        req['advanced'] = adv

        if original_ds:
            req['original_dataset'] = _sanitize_records(original_ds)
        if 'k_variants' in kwargs:
            req['k_variants'] = kwargs['k_variants']
        if 'vectors_for_dedup' in kwargs:
            req['vectors_for_dedup'] = kwargs['vectors_for_dedup']

        resp = self._make_request('', req)
        return _pg_normalize_result(resp)

    
    def pipeline_generate_critical_safe(
        self,
        config,
        original_dataset,
        seeds=None,
        top_k_percent: float = 0.1,
        k_variants: int = 6,
        advanced: Optional[Dict[str, Any]] = None,
        max_chunk: int = 2000,
        max_413_retries: int = 3,
    ) -> Dict[str, Any]:
        if not isinstance(original_dataset, list):
            raise ValidationError("original_dataset must be a list of dicts")

        norm_seeds = []
        if seeds:
            norm_seeds = [_sanitize_record(s.get('data', s) if isinstance(s, dict) else s) for s in seeds]

        total_generated = 0
        critical_samples_acc: List[Dict[str, Any]] = []
        non_critical_acc = 0
        
        acc_gen_metrics_list: List[dict] = []

        original_dataset = _sanitize_records(list(original_dataset))
        for start in range(0, len(original_dataset), max_chunk):
            ds_chunk = original_dataset[start:start + max_chunk]
            curr_k = int(k_variants)
            curr_seeds = list(norm_seeds) if norm_seeds else None

            for retry in range(max_413_retries):
                try:
                    # La llamada inicial no necesita 'cursor' ni 'partial_*'
                    res = self.pipeline_generate_critical(
                        config=config,
                        seeds=curr_seeds,
                        advanced=advanced,
                        original_dataset=ds_chunk,
                        top_k_percent=float(top_k_percent),
                        k_variants=int(curr_k),
                    )
                    
                    # --- [INICIO] AJUSTE DE DEBUG ---
                    print(f"DEBUG initial call chunk {start}: keys={list(res.keys() if isinstance(res, dict) else [])}")
                    print(f"  dataset_preview: {len(res.get('dataset_preview', []) if isinstance(res, dict) else [])}")
                    print(f"  critical_samples: {len(res.get('critical_samples', []) if isinstance(res, dict) else [])}")
                    # --- [FIN] AJUSTE DE DEBUG ---

                    acc_variants: List[dict] = [] 
                    
                    while isinstance(res, dict) and res.get('status') == 'partial':
                        cursor = res.get('cursor')
                        retry_after = int(res.get('retry_after', 2))
                        time.sleep(max(1, retry_after))

                        part_vars = res.get('partial_results') or []
                        if isinstance(part_vars, list):
                            acc_variants.extend(part_vars)

                        pm = res.get('partial_metrics') or {}
                        if isinstance(pm, dict) and isinstance(pm.get('gen_metrics_list'), list):
                            acc_gen_metrics_list.extend(pm['gen_metrics_list'])

                        res = self.pipeline_generate_critical(
                            config=config,
                            seeds=curr_seeds,
                            advanced=advanced,
                            original_dataset=ds_chunk,
                            top_k_percent=float(top_k_percent),
                            k_variants=int(curr_k),
                            cursor=cursor,
                            partial_results=acc_variants,
                            partial_metrics={"gen_metrics_list": acc_gen_metrics_list},
                        )

                        # --- [INICIO] AJUSTE DE DEBUG ---
                        print(f"DEBUG partial call chunk {start} cursor {cursor}: keys={list(res.keys() if isinstance(res, dict) else [])}")
                        print(f"  dataset_preview: {len(res.get('dataset_preview', []) if isinstance(res, dict) else [])}")
                        print(f"  critical_samples: {len(res.get('critical_samples', []) if isinstance(res, dict) else [])}")
                        # --- [FIN] AJUSTE DE DEBUG ---

                    # Al llegar a "complete", consolida los resultados del chunk
                    if isinstance(res, dict):
                        total_generated += int(res.get('total_generated', 0))
                        non_critical_acc += int(res.get('non_critical_added', 0))

                        # Usa la lógica robusta para extraer las muestras
                        crit_items = res.get("critical_samples") or res.get("dataset_preview")
                        if isinstance(crit_items, list):
                            critical_samples_acc.extend([x for x in crit_items if isinstance(x, dict)])

                    break  # El chunk se procesó correctamente

                except APIError as e:
                    if getattr(e, 'status_code', None) == 413 and retry < max_413_retries - 1:
                        if curr_seeds:
                            keep = max(50, len(curr_seeds) // 2)
                            curr_seeds = curr_seeds[:keep]
                        curr_k = max(2, curr_k - 1)
                        time.sleep(1 + retry)
                        continue
                    raise

        # Consolidación final de métricas
        final_metrics = _pg_metrics_from_gen_list(acc_gen_metrics_list)
        final_metrics.update({
            "generated": total_generated,
            "critical_count": len(critical_samples_acc),
            "non_critical": non_critical_acc,
        })

        return {
            "status": "ok",
            "total_generated": total_generated,
            "critical_samples": critical_samples_acc,
            "non_critical_added": non_critical_acc,
            "metrics": final_metrics,
        }



    def pipeline_full_cycle(self, dataset: List[Dict], config: Union[Dict, Config], max_iterations: int = 5, **kwargs) -> Dict:
        if self.tier != "enterprise":
            raise LicenseError("Full cycle requires enterprise tier")

        self._ensure_license_if_needed()
        _ensure_len("dataset", dataset, MAX_DATASET_ITEMS)

        cfg = config.to_dict() if isinstance(config, Config) else config
        cfg = _normalize_config_for_wire(cfg)

        req = {
            "action": "pipeline_full_cycle",
            "dataset": _sanitize_records(dataset),
            "config": cfg,
            "max_iterations": int(max_iterations),
            "license_key": self.license_key,
            **kwargs
        }
        return self._make_request("", req)

    def pipeline_full_cycle_auto(
        self,
        big_dataset: List[Dict],
        config: Union[Dict, Config],
        top_k_percent: float = 0.5,
        target_cap: int = MAX_DATASET_ITEMS,
        chunk_size: int = DEFAULT_CHUNK,
        max_iterations: int = 3,
        **kwargs
    ) -> Dict:
        """
        1) batch_evaluate en chunks sobre big_dataset
        2) selección near-threshold global
        3) cap a ≤ target_cap (≤10K)
        4) llama pipeline_full_cycle con subset
        5) si 413, reduce target_cap y reintenta (e.g., 10K→8K→6K)
        """
        if self.tier != "enterprise":
            raise LicenseError("Full cycle requires enterprise tier")

        ds = _sanitize_records(list(big_dataset))
        chunk = max(1, min(int(chunk_size), MAX_BATCH_EVAL))

        # 1) scoring
        scores: List[float] = []
        for part in _chunked(ds, chunk):
            part_scores = self.batch_evaluate(part, config)
            scores.extend([r.score for r in part_scores])

        # 2) near-threshold indices
        idx = _global_near_threshold(scores, top_k_percent)
        subset = [ds[i] for i in idx]

        # 3) cap duro
        if len(subset) > target_cap:
            subset = _cap_list(subset, cap=target_cap)

        # 4) intento + 5) retroceso si 413
        sizes_try = [target_cap]
        if target_cap >= 10000:
            sizes_try += [8000, 6000]
        for cap in sizes_try:
            sub = subset if len(subset) <= cap else _cap_list(subset, cap=cap)
            try:
                return self.pipeline_full_cycle(sub, config, max_iterations=max_iterations, **kwargs)
            except APIError as e:
                if getattr(e, "status_code", None) == 413 and cap > 2000:
                    logger.warning(f"[SDK] 413 on full_cycle with {len(sub)} rows. Retrying with next smaller cap…")
                    continue
                raise e


        # Si todos fallan (muy raro)
        raise APIError("Unable to run full_cycle without 413 after backoff")

    # ---------- Curriculum (Enterprise) ----------
    def curriculum_init(self, dataset: List[Dict], config: Union[Dict, Config], **params) -> Dict:
        if self.tier != "enterprise":
            raise LicenseError("Curriculum requires enterprise tier")
        cfg = config.to_dict() if isinstance(config, Config) else config
        cfg = _normalize_config_for_wire(cfg)
        req = {
            "action": "curriculum_init",
            "dataset": _sanitize_records(dataset),
            "config": cfg,
            "license_key": self.license_key,
            **params
        }
        return self._make_request("", req)

    def curriculum_step(self, dataset: List[Dict], config: Union[Dict, Config],
                        precomputed_metrics: Optional[Dict] = None) -> Dict:
        if self.tier != "enterprise":
            raise LicenseError("Curriculum requires enterprise tier")
        cfg = config.to_dict() if isinstance(config, Config) else config
        cfg = _normalize_config_for_wire(cfg)
        req = {
            "action": "curriculum_step",
            "dataset": _sanitize_records(dataset),
            "config": cfg,
            "license_key": self.license_key
        }
        if precomputed_metrics:
            req["precomputed_metrics"] = precomputed_metrics
        return self._make_request("", req)

    def curriculum_status(self) -> Dict:
        if self.tier != "enterprise":
            raise LicenseError("Curriculum requires enterprise tier")
        req = {"action": "curriculum_status", "license_key": self.license_key}
        return self._make_request("", req)

    # ---------- Fórmula no lineal ----------
    def evaluate_nonlinear(self, data: Dict, config: Union[Dict, Config],
                           adjustments: Dict[str, float], adjustment_values: Dict = None) -> EvaluationResult:
        if self.tier == "community":
            raise LicenseError("Nonlinear evaluation requires premium tier")
        if not self.license_key:
            raise LicenseError("license_key required for nonlinear evaluation")

        cfg = config.to_dict() if isinstance(config, Config) else config
        cfg = _normalize_config_for_wire(cfg)

        req = {
            "data": _sanitize_record(data),
            "config": cfg,
            "formula_mode": "nonlinear",
            "adjustments": adjustments,
            "tier": self.tier,
            "license_key": self.license_key,
        }
        if adjustment_values is not None:
            req["data"]["adjustments_values"] = adjustment_values

        resp = self._make_request("", req)
        return EvaluationResult.from_response(resp)

    # ---------- Distillation (Professional+) ----------
    def distill_train(self, config: Union[Dict, Config], samples: int = 1000, seed: int = 42,
                      batch_size: Optional[int] = None, adjustments: Optional[Dict] = None) -> DistillationResult:
        if self.tier == 'community':
            raise LicenseError("Distillation requires premium tier")
        if int(samples) > MAX_N_SYNTHETIC:
            raise ValidationError(f"samples too large — max {MAX_N_SYNTHETIC}")

        cfg = config.to_dict() if hasattr(config, "to_dict") else config
        cfg = _normalize_config_for_wire(cfg)
        req = {
            "action": "translate_train",
            "config": cfg,
            "tier": self.tier,
            "license_key": self.license_key,
            "n_synthetic": int(samples),
            "seed": int(seed),
        }
        if batch_size is not None:
            req["batch_size"] = int(batch_size)
        if adjustments:
            req["adjustments"] = adjustments

        resp = self._make_request("", req)
        return DistillationResult.from_train_response(resp)

    def distill_export(self) -> Dict:
        if self.tier != "enterprise":
            raise LicenseError("Export requires enterprise tier")
        req = {
            "action": "translate_export",
            "tier": self.tier,
            "license_key": self.license_key
        }
        return self._make_request("", req)

    def distill_predict(self, data: Dict[str, Any], config: Union[Dict, Config]) -> float:
        if self.tier == 'community':
            raise LicenseError("Surrogate prediction requires premium tier")

        cfg = config.to_dict() if hasattr(config, "to_dict") else config
        cfg = _normalize_config_for_wire(cfg)
        req = {
            "action": "translate_predict",
            "data": _sanitize_record(data),
            "config": cfg,
            "tier": self.tier,
            "license_key": self.license_key
        }
        resp = self._make_request("", req)
        return float(resp.get("score", 0.0))

    def distill_predict_batch(self, data_batch: List[Dict[str, Any]], config: Union[Dict, Config]) -> List[float]:
        if self.tier == 'community':
            raise LicenseError("Surrogate prediction requires premium tier")
        _ensure_len("data_batch", data_batch, MAX_BATCH_PREDICT)

        cfg = config.to_dict() if hasattr(config, "to_dict") else config
        cfg = _normalize_config_for_wire(cfg)
        req = {
            "action": "translate_predict",
            "data_batch": _sanitize_records(data_batch),
            "config": cfg,
            "tier": self.tier,
            "license_key": self.license_key
        }
        resp = self._make_request("", req)
        return [float(x) for x in resp.get("scores", [])]

    # ---------- Utilidades ----------
    def create_config(self) -> Config:
        return Config()

    def get_metrics(self) -> Optional[Dict]:
        if self.tier == "community":
            return None
        use_config = getattr(self, "_last_config", None)
        if not isinstance(use_config, dict) or not use_config:
            use_config = {"__probe__": {"default": 0, "weight": 1.0, "criticality": 1.0}}

        req = {"data": {}, "config": use_config, "tier": self.tier, "license_key": self.license_key}
        resp = self._make_request("", req)
        return resp.get("metrics")

    def close(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

