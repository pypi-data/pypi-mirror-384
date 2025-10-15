# DSF AML SDK

Reduce ML training data by **70–90%** via adaptive evaluation and knowledge distillation.  
Distill a surrogate and run inference **typically ~10× faster** with tiny footprints.

---

## 🚀 Why DSF AML?

Traditional ML needs thousands of labels and long training cycles. DSF AML encodes **domain rules** in a lightweight formula and (Pro/Ent) distills them into a **fast surrogate**, letting you ship accurate models with **minimal data** and **lower infrastructure costs**.

---

## 📚 Core Concepts

- **Config-as-rules**: Per-field `default`, `importance`, `sensitivity`, optional `string_floor`
- **Adaptive evaluation**: Compute a normalized score for any item
- **Decision-boundary focus**: Generate/collect data near the threshold
- **Knowledge distillation** (Pro/Ent): Train a linear surrogate for sub-ms inference

> **Non-linear mode (Pro/Ent):** The backend expects  
> `adjustments_values = { field_name: { adjustment_name: value[-1..1] } }` at top-level.  
> SDK wiring: you pass `adjustments_values` to `evaluate_nonlinear`; the SDK handles backend format.

---

## 📦 Installation

```bash
pip install dsf-aml-sdk
```

Optionally point the SDK to your backend:

```python
import os
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK(
    base_url=os.getenv("DSF_AML_BASE_URL"),  # e.g. https://your-vercel-app.vercel.app
    tier="community"
)
```

---

## 🎯 Quick Start

### Community

```python
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK()  # defaults to community tier

config = (sdk.create_config()
    .add_field('model_accuracy',  0.95, 2.5, 2.0)
    .add_field('training_epochs', 100,  1.8, 1.5)
    .add_field('validation_loss', 0.05, 2.2, 2.5)
    .add_field('model_name', 'baseline', 1.0, string_floor=0.1)
)

item = {'model_accuracy': 0.96, 'training_epochs': 105, 'validation_loss': 0.048}
res = sdk.evaluate(item, config)
print(f"Score: {res.score:.3f}")

# Active Learning: identify priority samples (100/day limit)
pool = [
    {'model_accuracy': 0.92, 'training_epochs': 50,  'validation_loss': 0.08},
    {'model_accuracy': 0.95, 'training_epochs': 100, 'validation_loss': 0.05},
    # ... up to 500 evaluations/day (identify_seeds capped at 100/day)
]
seeds = sdk.pipeline_identify_seeds(dataset=pool, config=config, top_k_percent=0.1)
print(f"Priority samples: {seeds.get('seeds_count', 0)}")
```

### Professional

```python
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK(license_key='PRO-2026-12-31-XXXX', tier='professional')

cfg = (sdk.create_config()
    .add_field('model_accuracy', 0.9, 2.0, 2.0)
    .add_field('training_epochs', 100, 1.8, 1.5)
    .add_field('validation_loss', 0.05, 2.2, 2.5)
)

# Batch evaluation (up to 1000 items/batch)
experiments = [
    {'model_accuracy': 0.92, 'training_epochs': 50,  'validation_loss': 0.08},
    {'model_accuracy': 0.95, 'training_epochs': 100, 'validation_loss': 0.05},
]
scores = sdk.batch_evaluate(experiments, cfg)

# Non-linear evaluation
res = sdk.evaluate_nonlinear(
    data={'model_accuracy': 0.92, 'training_epochs': 50, 'validation_loss': 0.08},
    config=cfg,
    adjustments={'model_accuracy': +0.03, 'validation_loss': -0.01},
    adjustments_values={'model_accuracy': {'boost': 0.5}, 'validation_loss': {'penalty': -0.3}}
)
print(f"Adjusted score: {res.score:.3f}")

# Note: adjustments is optional; if omitted, only adjustments_values applies (when provided)

# Metrics (after at least one evaluate/batch)
metrics = sdk.get_metrics()
```

### Enterprise: Pipeline + Distillation

```python
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK(license_key='ENT-2026-12-31-XXXX', tier='enterprise')

training_data = [
    {'model_accuracy': 0.92, 'training_epochs': 120, 'validation_loss': 0.06},
    {'model_accuracy': 0.88, 'training_epochs':  80, 'validation_loss': 0.07},
    # ...
]

cfg = (sdk.create_config()
    .add_field('model_accuracy', 0.9, 2.0, 2.0)
    .add_field('training_epochs', 100, 1.8, 1.5)
    .add_field('validation_loss', 0.05, 2.2, 2.5)
)

# 1) Identify seeds
seeds = sdk.pipeline_identify_seeds(dataset=training_data, config=cfg, top_k_percent=0.1)

# 2) Generate critical variants
gen = sdk.pipeline_generate_critical(
    config=cfg,
    original_dataset=training_data,
    k_variants=5,
    epsilon=0.05,
    diversity_threshold=0.95,
    non_critical_ratio=0.15,
    advanced={"require_middle": False, "max_retries": 20}
)
print(f"Generated: {gen.get('total_generated', 0)} variants")

# 3) Full cycle
full = sdk.pipeline_full_cycle(dataset=training_data, config=cfg, max_iterations=3)

# 4) Distillation
sdk.distill_train(cfg, samples=1000, batch_size=100, seed=42)
fast_score = sdk.distill_predict(training_data[0], cfg)

# Batch prediction (chunking recommended)
batch = training_data[:1000]
scores = []
for i in range(0, len(batch), 200):
    scores.extend(sdk.distill_predict_batch(batch[i:i+200], cfg))

artifact = sdk.distill_export()  # Enterprise only
```

---

## 🔧 Fine-Tuned Calibrations (Recipes)

> Use **positional** calls in `add_field(name, default, importance, sensitivity)`.  
> Where knobs are specified (e.g., `epsilon`, `diversity_threshold`), respect tier limits.

### A) Community — Fast Active Learning (wide top-k)

```python
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK()  # community
config = (sdk.create_config()
    .add_field('feature_1', 0.5, 2.0, 1.5)
    .add_field('feature_2', 0.5, 1.5, 2.0)
    .add_field('feature_3', 0.5, 1.0, 1.0)
    .add_field('metric_score', 0.75, 2.5, 2.0)
)

# Top 50% to see seeds (daily limit applies)
seeds = sdk.pipeline_identify_seeds(dataset=pool[:100], config=config, top_k_percent=0.50)
print("Seeds:", seeds.get("seeds_count", 0))
```

### B) Enterprise — Relaxed Critical Generation (more useful data)

```python
sdk = AMLSDK(license_key='ENT-XXXX', tier='enterprise')
cfg = (sdk.create_config()
    .add_field('f1', 0.5, 2.0, 1.5)
    .add_field('f2', 0.5, 1.8, 1.5)
    .add_field('f3', 0.5, 1.2, 1.2)
    .add_field('score', 0.75, 2.5, 2.0)
)

gen = sdk.pipeline_generate_critical(
    config=cfg,
    original_dataset=pool[:80],
    k_variants=14,                 # ↑ variants/seed
    epsilon=0.22,                  # wider band
    diversity_threshold=0.82,      # less strict dedup
    non_critical_ratio=0.50,       # 50/50 mix
    advanced={
        "require_middle": False,   # key to not slow acceptance
        "max_seeds_to_process": 50,
        "step_scale": 0.50,
        "min_step": 0.02,
        "max_retries": 25,
    },
    vectors_for_dedup=[]           # exact dedup (no cosine)
)
print("Total generated:", gen.get("total_generated", 0))
```

### C) Enterprise — Full Cycle with Knobs (larger final dataset)

```python
full = sdk.pipeline_full_cycle(
    dataset=pool[:80],
    config=cfg,
    max_iterations=3,
    top_k_percent=0.50,
    k_variants=16,
    epsilon=0.25,
    diversity_threshold=0.80,
    non_critical_ratio=0.40,
    advanced={
        "require_middle": False,
        "max_seeds_to_process": 50,
        "step_scale": 0.60,
        "min_step": 0.01,
        "max_retries": 30,
    },
    vectors_for_dedup=[]
)
print("Final size:", full.get("final_size"))
```

### D) Realistic Z-score Matching (map to original dataset)

```python
import numpy as np

def map_by_zscore(reduced_samples, df_numeric, cols, max_rows, z_threshold=2.0):
    stds = {c: float(df_numeric[c].std() or 1.0) for c in cols}
    def z_dist(a, b): return np.sqrt(sum(((a.get(k,0)-b.get(k,0))/stds[k])**2 for k in cols))
    base = df_numeric[cols].to_dict("records")

    idxs, dists = [], []
    for s in reduced_samples:
        best = min(range(min(max_rows, len(base))), key=lambda i: z_dist(s, base[i]))
        d = z_dist(s, base[best])
        if d < z_threshold and best not in idxs:
            idxs.append(best); dists.append(d)
    print(f"Mapped (z<{z_threshold}): {len(idxs)}",
          f"| avg z-dist: {np.mean(dists):.2f}" if dists else "")
    return idxs
```

### E) Distillation — Training + Batch Prediction (avoid 429)

```python
# Train surrogate
sdk.distill_train(cfg, samples=500, batch_size=100)

# Batch prediction with chunking
def batched(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

all_scores, CHUNK = [], 200
for chunk in batched(pool[:1000], CHUNK):
    all_scores.extend(sdk.distill_predict_batch(chunk, cfg))
print("Batch scores:", len(all_scores))
```

### F) Non-linear Mode (Pro/Ent) — Correct Top-level Signature

```python
adjustments = {"f1": 0.2, "f2": -0.1}  # extra weights in formula
adjustments_values = {"f1": {"delta": 0.2}, "f2": {"delta": -0.1}}  # values per field

res = sdk.evaluate_nonlinear(
    data=sample,
    config=cfg,
    adjustments=adjustments,
    adjustments_values=adjustments_values
)
print("Score:", res.score)
```

---

## ⚡ Performance Tips (High-Volume Scoring)

* Avoid `evaluate()` loops for hundreds/thousands of rows: request latency accumulates.
* Use batch (`batch_evaluate`) or, better, distillation + `distill_predict_batch`.
* For curation, don't score everything: use `pipeline_identify_seeds(top_k_percent)` and work only with that subset.
* If a long operation returns `status: "partial"`, resume with the `cursor` (serverless-friendly).

### A) Batch Scoring (fast, no distillation)

```python
BATCH = 200
scores = []
for i in range(0, len(dataset), BATCH):
    chunk = dataset[i:i+BATCH]
    scores.extend(sdk.batch_evaluate(chunk, config))
```

### B) Distillation (faster and cheaper at volume)

```python
# 1) Train surrogate once
sdk.distill_train(config, samples=1000, batch_size=100)

# 2) Predict in batch (chunking recommended)
CHUNK = 200
scores = []
for i in range(0, len(dataset), CHUNK):
    scores.extend(sdk.distill_predict_batch(dataset[i:i+CHUNK], config))
```

### C) Efficient Curation (Active Learning)

```python
# Select only the 30–50% most informative
seeds = sdk.pipeline_identify_seeds(dataset=dataset, config=config, top_k_percent=0.5)
print("Priority samples:", seeds.get("seeds_count", 0))
```

### D) Resuming Partial Operations

```python
resp = sdk.pipeline_generate_critical(config, original_dataset=dataset, k_variants=3)
while isinstance(resp, dict) and resp.get("status") == "partial":
    resp = sdk.pipeline_generate_critical(
        config=config,
        original_dataset=dataset,
        cursor=resp.get("cursor"),
        partial_results=resp.get("partial_results", []),
        k_variants=3
    )
```

**Tip:** If you don't need non-linear mode, don't send `adjustments/adjustments_values`; reduces cost and latency.

---

## 💡 Use Cases

### 1. Data Curation: Keep Only What Matters
Retain the **10–30% most informative samples** near decision boundaries, discard duplicates and easy cases.

```python
# Start with 10,000 samples
result = sdk.pipeline_full_cycle(dataset=full_training_data, config=config, max_iterations=3)
print(f"Reduced: {len(full_training_data)} → {result['final_size']} samples")
# Typical output: "Reduced: 10000 → 1500 samples" (85% reduction)
```

### 2. Policy Stress Testing: Generate Edge Cases
Create boundary scenarios for testing ML policies (e.g., accuracy vs latency trade-offs).

```python
# Generate critical variants around decision threshold
seeds = sdk.pipeline_identify_seeds(production_data, config, top_k_percent=0.1)
edge_cases = sdk.pipeline_generate_critical(
    config=config,
    original_dataset=production_data,
    epsilon=0.05  # tight band around threshold
)
# Use edge_cases for stress testing your models
```

### 3. Edge Deployment: Sub-millisecond Inference
Deploy a linear surrogate for **typically <1ms CPU inference** without GPUs.

```python
# Train surrogate from your complex model
sdk.distill_train(config, samples=1000)

# Deploy with minimal footprint
def inference_edge(sample):
    return sdk.distill_predict(sample, config)  # typically <1ms on CPU

# Benchmark: typically 10-50× faster than original model
```

### 4. Cost Control: 70–90% Less Training Data
Evaluate → Reduce → Train pipeline cuts cloud costs dramatically.

```python
# Traditional approach: train on all 100K samples
original_size = 100_000

# DSF approach: focus on critical samples
reduced_data = sdk.pipeline_full_cycle(dataset, config)
new_size = len(reduced_data['final_samples'])

reduction = (1 - new_size/original_size) * 100
print(f"Data reduction: {reduction:.0f}%")
print(f"Proportional cost savings: ~{reduction:.0f}%")
# Typical output: "Data reduction: 87%"
```

### Summary
**DSF AML delivers:**
- **Less data**: 70–90% reduction while preserving decision boundaries
- **Faster training**: Focus on critical samples only  
- **Synthesis capability**: Generate edge cases from minimal seed data
- **Production-ready**: Partial results handling for serverless environments

---

## 🔄 Data Optimization Capabilities

### Active Learning (Community+)
Prioritize samples close to the decision boundary (formula threshold or surrogate prediction if trained and active for mass pre-scoring).

```python
seeds = sdk.pipeline_identify_seeds(dataset=training_data, config=config, top_k_percent=0.1)
print("Priority samples:", seeds.get("seeds_count", 0))
```

### Curriculum Learning (Enterprise)
Iteratively refine datasets by focusing on hard examples. May return `status: "partial"` with `cursor` for serverless-friendly continuation.

```python
result = sdk.pipeline_full_cycle(dataset, config, max_iterations=5)
```

### Data Augmentation (Enterprise)
Generate synthetic variants near decision boundaries for stress testing and data augmentation.

```python
gen = sdk.pipeline_generate_critical(
    config=config,
    original_dataset=training_data,
    k_variants=5,
    epsilon=0.05,
    diversity_threshold=0.95,
    non_critical_ratio=0.15,
    advanced={"require_middle": False, "max_retries": 20}
)
print("New examples:", gen.get("total_generated", 0))
```

---

## ⏱️ Handling Partial Results (Serverless-friendly)

Long operations may return `status: "partial"` with a cursor for continuation. The API handles timeouts automatically—simply re-submit with the provided cursor to continue.

### Critical Generation (Enterprise)

```python
import time

resp = sdk.pipeline_generate_critical(cfg, original_dataset=training_data, k_variants=3)

while isinstance(resp, dict) and resp.get("status") == "partial":
    time.sleep(resp.get("retry_after", 1))  # Respect retry_after if provided
    resp = sdk.pipeline_generate_critical(
        config=cfg,
        original_dataset=training_data,
        cursor=resp.get("cursor", 0),
        partial_results=resp.get("partial_results", []),
        k_variants=3
    )

print(f"Total generated: {resp.get('total_generated', 0)}")
```

---

## 📊 Rate Limits

| Tier         | Evaluations/Day | Batch Size | Seeds/Day | Seeds Preview |
|--------------|------------------|------------|-----------|---------------|
| Community    | 500              | ❌         | 100       | up to 100     |
| Professional | unlimited        | ✅ ≤1000   | unlimited | unlimited     |
| Enterprise   | unlimited        | ✅ ≤1000   | unlimited | unlimited     |

*Limits may vary by account. Contact sales for details.*  
*Seeds Preview = number of samples returned by `pipeline_identify_seeds`.*

---

## 🆚 Tier Comparison

| Feature                      | Community              | Professional | Enterprise         |
|------------------------------|------------------------|--------------|-------------------|
| Single evaluation            | ✅ (500/day)           | ✅           | ✅                |
| Batch evaluation             | ❌                     | ✅           | ✅                |
| Metrics                      | ❌                     | ✅           | ✅ (enhanced)     |
| Identify seeds               | ✅ (daily limit)       | ✅           | ✅                |
| Generate critical variants   | ❌                     | ❌           | ✅ (full)         |
| Full cycle pipeline          | ❌                     | ❌           | ✅                |
| Curriculum learning          | ❌                     | ❌           | ✅                |
| Non-linear evaluation        | ❌                     | ✅           | ✅                |
| Distillation                 | ❌                     | ✅           | ✅                |
| Surrogate export             | ❌                     | ❌           | ✅                |

---

## 📖 API Reference

### Initialization
```python
AMLSDK(
    tier='community'|'professional'|'enterprise',
    license_key=None,
    base_url=None,
    timeout=30
)
```

### Configuration
```python
# Method signature
create_config() -> ConfigBuilder
ConfigBuilder.add_field(
    name: str,
    default: Any,
    importance: float,
    sensitivity: float,
    *,
    string_floor: float | None = None
) -> ConfigBuilder

# Example
config = (sdk.create_config()
    .add_field('field1', 0.5, 2.0, 1.5)
    .add_field('field2', 100, 1.8, 2.0)
    .add_field('text_field', 'default', 1.0, string_floor=0.1)
)

# As dict (alternative)
config = {
    "field1": {"default": 0.5, "importance": 2.0, "sensitivity": 1.5},
    "field2": {"default": 100, "importance": 1.8, "sensitivity": 2.0}
}
```

### Core Methods
- `evaluate(data: dict, config) -> EvaluationResult` - Single evaluation
- `evaluate_nonlinear(data: dict, config, adjustments: dict, adjustments_values: dict)` - Non-linear (Pro/Ent)
- `batch_evaluate(data_points: list[dict], config) -> list[float]` - Batch processing (Pro/Ent)
- `get_metrics() -> dict` - Performance metrics (Pro/Ent)

### Pipeline Methods
- `pipeline_identify_seeds(dataset: list[dict], config, top_k_percent=0.1) -> dict`
- `pipeline_generate_critical(config, original_dataset: list[dict], **kwargs) -> dict` (Enterprise)
- `pipeline_full_cycle(dataset: list[dict], config, max_iterations=5) -> dict` (Enterprise)

### Distillation Methods (Pro/Ent)
- `distill_train(config, samples=1000, batch_size=100, seed=42) -> dict`
- `distill_predict(data: dict, config) -> float`
- `distill_predict_batch(data_points: list[dict], config) -> list[float]`
- `distill_export() -> dict` (Enterprise only)

---

## ⚠️ Common Errors

### 422 Model Not Trained
**Cause**: Surrogate not trained or config mismatch  
**Solution**: Run `sdk.distill_train(config, ...)` with the same config

### 429 Rate Limited
**Cause**: Exceeded tier limits  
**Solution**: Use batch operations, chunk large requests, respect `Retry-After` header

### 413 Payload Too Large
**Cause**: Dataset or payload exceeds size limits  
**Solution**: Split dataset into smaller chunks or reduce generation parameters (Enterprise only)

### 400 Invalid Config
**Cause**: Missing required fields or invalid parameter values  
**Solution**: Ensure config has `default`, `importance`, `sensitivity` for each field

---



## 📞 Support

- **Documentation**: https://docs.dsf-aml.ai
- **Issues**: https://github.com/dsf-aml/sdk/issues
- **Enterprise**: contacto@softwarefinanzas.com.co

---

## 📄 License

MIT for Community tier. Professional/Enterprise under commercial terms.

© 2025 DSF AML SDK — Adaptive ML powered by Knowledge Distillation

---

# DSF AML SDK (Español)

Reduce los datos de entrenamiento ML en **70–90%** mediante evaluación adaptativa y destilación de conocimiento.  
Destila un modelo sustituto y ejecuta inferencias **típicamente ~10× más rápido** con huella mínima.

---

## 🚀 ¿Por qué DSF AML?

El ML tradicional necesita miles de etiquetas y largos ciclos de entrenamiento. DSF AML codifica **reglas del dominio** en una fórmula ligera y (Pro/Ent) las destila en un **sustituto rápido**, permitiendo entregar modelos precisos con **mínimos datos** y **menores costos de infraestructura**.

---

## 📚 Conceptos Clave

- **Configuración como reglas**: Por campo `default`, `importance`, `sensitivity`, opcional `string_floor`
- **Evaluación adaptativa**: Calcula un score normalizado para cualquier elemento
- **Foco en fronteras de decisión**: Genera/recolecta datos cerca del umbral
- **Destilación de conocimiento** (Pro/Ent): Entrena un sustituto lineal para inferencia sub-milisegundo

> **Modo no lineal (Pro/Ent):** El backend espera  
> `adjustments_values = { field_name: { adjustment_name: value[-1..1] } }` en nivel superior.  
> Cableado SDK: pasas `adjustments_values` a `evaluate_nonlinear`; el SDK maneja el formato del backend.

---

## 📦 Instalación

```bash
pip install dsf-aml-sdk
```

Opcionalmente apunta el SDK a tu backend:

```python
import os
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK(
    base_url=os.getenv("DSF_AML_BASE_URL"),  # ej: https://tu-app-vercel.vercel.app
    tier="community"
)
```

---

## 🎯 Inicio Rápido

### Community

```python
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK()  # por defecto tier community

config = (sdk.create_config()
    .add_field('model_accuracy',  0.95, 2.5, 2.0)
    .add_field('training_epochs', 100,  1.8, 1.5)
    .add_field('validation_loss', 0.05, 2.2, 2.5)
    .add_field('model_name', 'baseline', 1.0, string_floor=0.1)
)

item = {'model_accuracy': 0.96, 'training_epochs': 105, 'validation_loss': 0.048}
res = sdk.evaluate(item, config)
print(f"Score: {res.score:.3f}")

# Active Learning: identificar muestras prioritarias (límite 100/día)
pool = [
    {'model_accuracy': 0.92, 'training_epochs': 50,  'validation_loss': 0.08},
    {'model_accuracy': 0.95, 'training_epochs': 100, 'validation_loss': 0.05},
    # ... hasta 500 evaluaciones/día (identify_seeds limitado a 100/día)
]
seeds = sdk.pipeline_identify_seeds(dataset=pool, config=config, top_k_percent=0.1)
print(f"Muestras prioritarias: {seeds.get('seeds_count', 0)}")
```

### Professional

```python
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK(license_key='PRO-2026-12-31-XXXX', tier='professional')

cfg = (sdk.create_config()
    .add_field('model_accuracy', 0.9, 2.0, 2.0)
    .add_field('training_epochs', 100, 1.8, 1.5)
    .add_field('validation_loss', 0.05, 2.2, 2.5)
)

# Evaluación batch (hasta 1000 items/batch)
experimentos = [
    {'model_accuracy': 0.92, 'training_epochs': 50,  'validation_loss': 0.08},
    {'model_accuracy': 0.95, 'training_epochs': 100, 'validation_loss': 0.05},
]
scores = sdk.batch_evaluate(experimentos, cfg)

# Evaluación no lineal
res = sdk.evaluate_nonlinear(
    data={'model_accuracy': 0.92, 'training_epochs': 50, 'validation_loss': 0.08},
    config=cfg,
    adjustments={'model_accuracy': +0.03, 'validation_loss': -0.01},
    adjustments_values={'model_accuracy': {'boost': 0.5}, 'validation_loss': {'penalty': -0.3}}
)
print(f"Score ajustado: {res.score:.3f}")

# Nota: adjustments es opcional; si se omite, solo se aplica adjustments_values (cuando se proporciona)

# Métricas (después de al menos una evaluación)
metrics = sdk.get_metrics()
```

### Enterprise: Pipeline + Destilación

```python
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK(license_key='ENT-2026-12-31-XXXX', tier='enterprise')

datos_entrenamiento = [
    {'model_accuracy': 0.92, 'training_epochs': 120, 'validation_loss': 0.06},
    {'model_accuracy': 0.88, 'training_epochs':  80, 'validation_loss': 0.07},
    # ...
]

cfg = (sdk.create_config()
    .add_field('model_accuracy', 0.9, 2.0, 2.0)
    .add_field('training_epochs', 100, 1.8, 1.5)
    .add_field('validation_loss', 0.05, 2.2, 2.5)
)

# 1) Identificar semillas
seeds = sdk.pipeline_identify_seeds(dataset=datos_entrenamiento, config=cfg, top_k_percent=0.1)

# 2) Generar variantes críticas
gen = sdk.pipeline_generate_critical(
    config=cfg,
    original_dataset=datos_entrenamiento,
    k_variants=5,
    epsilon=0.05,
    diversity_threshold=0.95,
    non_critical_ratio=0.15,
    advanced={"require_middle": False, "max_retries": 20}
)
print(f"Generadas: {gen.get('total_generated', 0)} variantes")

# 3) Ciclo completo
full = sdk.pipeline_full_cycle(dataset=datos_entrenamiento, config=cfg, max_iterations=3)

# 4) Destilación
sdk.distill_train(cfg, samples=1000, batch_size=100, seed=42)
score_rapido = sdk.distill_predict(datos_entrenamiento[0], cfg)

# Predicción batch (chunking recomendado)
batch = datos_entrenamiento[:1000]
scores = []
for i in range(0, len(batch), 200):
    scores.extend(sdk.distill_predict_batch(batch[i:i+200], cfg))

artifact = sdk.distill_export()  # Solo Enterprise
```

---

## 🔧 Calibraciones Finas (Recetas)

> Usa llamadas **posicionales** en `add_field(name, default, importance, sensitivity)`.  
> Donde se indiquen knobs (p. ej., `epsilon`, `diversity_threshold`), respeta los límites por tier.

### A) Community — Active Learning "rápido" (top-k amplio)

```python
from dsf_aml_sdk import AMLSDK

sdk = AMLSDK()  # community
config = (sdk.create_config()
    .add_field('feature_1', 0.5, 2.0, 1.5)
    .add_field('feature_2', 0.5, 1.5, 2.0)
    .add_field('feature_3', 0.5, 1.0, 1.0)
    .add_field('metric_score', 0.75, 2.5, 2.0)
)

# Top 50% para ver semillas (límite diario aplica)
seeds = sdk.pipeline_identify_seeds(dataset=pool[:100], config=config, top_k_percent=0.50)
print("Seeds:", seeds.get("seeds_count", 0))
```

### B) Enterprise — Generación crítica "relajada" (más datos útiles)

```python
sdk = AMLSDK(license_key='ENT-XXXX', tier='enterprise')
cfg = (sdk.create_config()
    .add_field('f1', 0.5, 2.0, 1.5)
    .add_field('f2', 0.5, 1.8, 1.5)
    .add_field('f3', 0.5, 1.2, 1.2)
    .add_field('score', 0.75, 2.5, 2.0)
)

gen = sdk.pipeline_generate_critical(
    config=cfg,
    original_dataset=pool[:80],
    k_variants=14,                 # ↑ variantes/seed
    epsilon=0.22,                  # banda más ancha
    diversity_threshold=0.82,      # dedup menos estricto
    non_critical_ratio=0.50,       # mezcla 50/50
    advanced={
        "require_middle": False,   # clave para no frenar la aceptación
        "max_seeds_to_process": 50,
        "step_scale": 0.50,
        "min_step": 0.02,
        "max_retries": 25,
    },
    vectors_for_dedup=[]           # dedup exacto (sin coseno)
)
print("Total generado:", gen.get("total_generated", 0))
```

### C) Enterprise — Full Cycle con knobs (dataset final más grande)

```python
full = sdk.pipeline_full_cycle(
    dataset=pool[:80],
    config=cfg,
    max_iterations=3,
    top_k_percent=0.50,
    k_variants=16,
    epsilon=0.25,
    diversity_threshold=0.80,
    non_critical_ratio=0.40,
    advanced={
        "require_middle": False,
        "max_seeds_to_process": 50,
        "step_scale": 0.60,
        "min_step": 0.01,
        "max_retries": 30,
    },
    vectors_for_dedup=[]
)
print("Final size:", full.get("final_size"))
```

### D) Matching "realista" por z-score (para mapear al dataset original)

```python
import numpy as np

def map_by_zscore(reduced_samples, df_numeric, cols, max_rows, z_threshold=2.0):
    stds = {c: float(df_numeric[c].std() or 1.0) for c in cols}
    def z_dist(a, b): return np.sqrt(sum(((a.get(k,0)-b.get(k,0))/stds[k])**2 for k in cols))
    base = df_numeric[cols].to_dict("records")

    idxs, dists = [], []
    for s in reduced_samples:
        best = min(range(min(max_rows, len(base))), key=lambda i: z_dist(s, base[i]))
        d = z_dist(s, base[best])
        if d < z_threshold and best not in idxs:
            idxs.append(best); dists.append(d)
    print(f"Mapeados (z<{z_threshold}): {len(idxs)}",
          f"| z-dist media: {np.mean(dists):.2f}" if dists else "")
    return idxs
```

### E) Distillation — entrenamiento + predicción batch (sin 429)

```python
# Entrena surrogate
sdk.distill_train(cfg, samples=500, batch_size=100)

# Predicción batch con chunking
def batched(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

all_scores, CHUNK = [], 200
for chunk in batched(pool[:1000], CHUNK):
    all_scores.extend(sdk.distill_predict_batch(chunk, cfg))
print("Batch scores:", len(all_scores))
```

### F) Modo no lineal (Pro/Ent) — firma correcta en top-level

```python
adjustments = {"f1": 0.2, "f2": -0.1}  # pesos extra en la fórmula
adjustments_values = {"f1": {"delta": 0.2}, "f2": {"delta": -0.1}}  # valores por campo

res = sdk.evaluate_nonlinear(
    data=sample,
    config=cfg,
    adjustments=adjustments,
    adjustments_values=adjustments_values
)
print("Score:", res.score)
```

---

## ⚡ Consejos de Rendimiento (Scoring de Alto Volumen)

* Evita loops de `evaluate()` para cientos/miles de filas: la latencia por request se acumula.
* Usa batch (`batch_evaluate`) o, mejor, destilación + `distill_predict_batch`.
* Para curación, no puntúes todo: usa `pipeline_identify_seeds(top_k_percent)` y trabaja sólo con ese subconjunto.
* Si una operación larga devuelve `status: "partial"`, reanuda con el `cursor` (serverless-friendly).

### A) Batch Scoring (rápido, sin destilación)

```python
BATCH = 200
scores = []
for i in range(0, len(dataset), BATCH):
    chunk = dataset[i:i+BATCH]
    scores.extend(sdk.batch_evaluate(chunk, config))
```

### B) Distillation (más rápido y barato en volumen)

```python
# 1) Entrena el sustituto una vez
sdk.distill_train(config, samples=1000, batch_size=100)

# 2) Predice en batch (chunking recomendado)
CHUNK = 200
scores = []
for i in range(0, len(dataset), CHUNK):
    scores.extend(sdk.distill_predict_batch(dataset[i:i+CHUNK], config))
```

### C) Curación Eficiente (Active Learning)

```python
# Selecciona sólo el 30–50% más informativo
seeds = sdk.pipeline_identify_seeds(dataset=dataset, config=config, top_k_percent=0.5)
print("Muestras prioritarias:", seeds.get("seeds_count", 0))
```

### D) Reanudación de Operaciones Parciales

```python
resp = sdk.pipeline_generate_critical(config, original_dataset=dataset, k_variants=3)
while isinstance(resp, dict) and resp.get("status") == "partial":
    resp = sdk.pipeline_generate_critical(
        config=config,
        original_dataset=dataset,
        cursor=resp.get("cursor"),
        partial_results=resp.get("partial_results", []),
        k_variants=3
    )
```

**Tip:** Si no necesitas modo no lineal, no envíes `adjustments/adjustments_values`; reduce coste y latencia.

---

## 💡 Casos de Uso

### 1. Curación de Datos: Conserva Solo lo Importante
Retén el **10–30% de muestras más informativas** cerca de las fronteras de decisión, descarta duplicados y casos fáciles.

```python
# Empiezas con 10,000 muestras
result = sdk.pipeline_full_cycle(dataset=datos_completos, config=config, max_iterations=3)
print(f"Reducido: {len(datos_completos)} → {result['final_size']} muestras")
# Salida típica: "Reducido: 10000 → 1500 muestras" (85% reducción)
```

### 2. Pruebas de Estrés de Políticas: Genera Casos Borde
Crea escenarios frontera para probar políticas ML (ej: compromisos precisión vs latencia).

```python
# Genera variantes críticas alrededor del umbral de decisión
seeds = sdk.pipeline_identify_seeds(datos_produccion, config, top_k_percent=0.1)
casos_borde = sdk.pipeline_generate_critical(
    config=config,
    original_dataset=datos_produccion,
    epsilon=0.05  # banda ajustada alrededor del umbral
)
# Usa casos_borde para pruebas de estrés de tus modelos
```

### 3. Despliegue en Edge: Inferencia Sub-milisegundo
Despliega un sustituto lineal para **típicamente inferencia <1ms en CPU** sin GPUs.

```python
# Entrena sustituto desde tu modelo complejo
sdk.distill_train(config, samples=1000)

# Despliega con huella mínima
def inferencia_edge(muestra):
    return sdk.distill_predict(muestra, config)  # típicamente <1ms en CPU

# Benchmark: típicamente 10-50× más rápido que el modelo original
```

### 4. Control de Costos: 70–90% Menos Datos de Entrenamiento
El pipeline Evaluar → Reducir → Entrenar reduce dramáticamente los costos en la nube.

```python
# Enfoque tradicional: entrenar con todas las 100K muestras
tamano_original = 100_000

# Enfoque DSF: enfócate en muestras críticas
datos_reducidos = sdk.pipeline_full_cycle(dataset, config)
tamano_nuevo = len(datos_reducidos['final_samples'])

reduccion = (1 - tamano_nuevo/tamano_original) * 100
print(f"Reducción de datos: {reduccion:.0f}%")
print(f"Ahorro proporcional de costos: ~{reduccion:.0f}%")
# Salida típica: "Reducción de datos: 87%"
```

### Resumen
**DSF AML entrega:**
- **Menos datos**: Reducción del 70–90% preservando fronteras de decisión
- **Entrenamiento más rápido**: Enfoque solo en muestras críticas
- **Capacidad de síntesis**: Genera casos borde desde datos semilla mínimos
- **Listo para producción**: Manejo de resultados parciales para entornos serverless

---

## 🔄 Capacidades de Optimización de Datos

### Active Learning (Community+)
Prioriza muestras cercanas a la frontera de decisión (umbral de fórmula o predicción del sustituto si está entrenado y activo para pre-scoring masivo).

```python
seeds = sdk.pipeline_identify_seeds(dataset=datos_entrenamiento, config=config, top_k_percent=0.1)
print("Muestras prioritarias:", seeds.get("seeds_count", 0))
```

### Curriculum Learning (Enterprise)
Refina iterativamente los datasets enfocándose en ejemplos difíciles. Puede retornar `status: "partial"` con `cursor` para continuación serverless-friendly.

```python
result = sdk.pipeline_full_cycle(dataset, config, max_iterations=5)
```

### Data Augmentation (Enterprise)
Genera variantes sintéticas cerca de fronteras de decisión para pruebas de estrés y aumento de datos.

```python
gen = sdk.pipeline_generate_critical(
    config=config,
    original_dataset=datos_entrenamiento,
    k_variants=5,
    epsilon=0.05,
    diversity_threshold=0.95,
    non_critical_ratio=0.15,
    advanced={"require_middle": False, "max_retries": 20}
)
print("Nuevos ejemplos:", gen.get("total_generated", 0))
```

---

## ⏱️ Manejo de Resultados Parciales (Compatible con Serverless)

Las operaciones largas pueden retornar `status: "partial"` con un cursor para continuación. La API maneja timeouts automáticamente—simplemente re-envía con el cursor proporcionado para continuar.

### Generación Crítica (Enterprise)

```python
import time

resp = sdk.pipeline_generate_critical(cfg, original_dataset=datos_entrenamiento, k_variants=3)

while isinstance(resp, dict) and resp.get("status") == "partial":
    time.sleep(resp.get("retry_after", 1))  # Respetar retry_after si se proporciona
    resp = sdk.pipeline_generate_critical(
        config=cfg,
        original_dataset=datos_entrenamiento,
        cursor=resp.get("cursor", 0),
        partial_results=resp.get("partial_results", []),
        k_variants=3
    )

print(f"Total generado: {resp.get('total_generated', 0)}")
```

---

## 📊 Límites de Tasa

| Tier         | Evaluaciones/Día | Tamaño Batch | Semillas/Día | Vista Previa Semillas |
|--------------|------------------|--------------|--------------|----------------------|
| Community    | 500              | ❌           | 100          | hasta 100            |
| Professional | ilimitado        | ✅ ≤1000     | ilimitado    | ilimitado            |
| Enterprise   | ilimitado        | ✅ ≤1000     | ilimitado    | ilimitado            |

*Los límites pueden variar por cuenta. Contacta a ventas para detalles.*  
*Vista Previa Semillas = número de muestras devueltas por `pipeline_identify_seeds`.*

---

## 🆚 Comparación de Tiers

| Característica             | Community              | Professional | Enterprise         |
|----------------------------|------------------------|--------------|-------------------|
| Evaluación individual      | ✅ (500/día)           | ✅           | ✅                |
| Evaluación batch           | ❌                     | ✅           | ✅                |
| Métricas                   | ❌                     | ✅           | ✅ (mejoradas)    |
| Identificar semillas       | ✅ (límite diario)     | ✅           | ✅                |
| Generar variantes críticas | ❌                     | ❌           | ✅ (completo)     |
| Pipeline ciclo completo    | ❌                     | ❌           | ✅                |
| Aprendizaje curricular     | ❌                     | ❌           | ✅                |
| Evaluación no lineal       | ❌                     | ✅           | ✅                |
| Destilación                | ❌                     | ✅           | ✅                |
| Exportar sustituto         | ❌                     | ❌           | ✅                |

---

## 📖 Referencia API

### Inicialización
```python
AMLSDK(
    tier='community'|'professional'|'enterprise',
    license_key=None,
    base_url=None,
    timeout=30
)
```

### Configuración
```python
# Firma del método
create_config() -> ConfigBuilder
ConfigBuilder.add_field(
    name: str,
    default: Any,
    importance: float,
    sensitivity: float,
    *,
    string_floor: float | None = None
) -> ConfigBuilder

# Ejemplo
config = (sdk.create_config()
    .add_field('campo1', 0.5, 2.0, 1.5)
    .add_field('campo2', 100, 1.8, 2.0)
    .add_field('campo_texto', 'default', 1.0, string_floor=0.1)
)

# Como dict (alternativa)
config = {
    "campo1": {"default": 0.5, "importance": 2.0, "sensitivity": 1.5},
    "campo2": {"default": 100, "importance": 1.8, "sensitivity": 2.0}
}
```

### Métodos Principales
- `evaluate(data: dict, config) -> EvaluationResult` - Evaluación individual
- `evaluate_nonlinear(data: dict, config, adjustments: dict, adjustments_values: dict)` - No lineal (Pro/Ent)
- `batch_evaluate(data_points: list[dict], config) -> list[float]` - Procesamiento batch (Pro/Ent)
- `get_metrics() -> dict` - Métricas de rendimiento (Pro/Ent)

### Métodos de Pipeline
- `pipeline_identify_seeds(dataset: list[dict], config, top_k_percent=0.1) -> dict`
- `pipeline_generate_critical(config, original_dataset: list[dict], **kwargs) -> dict` (Enterprise)
- `pipeline_full_cycle(dataset: list[dict], config, max_iterations=5) -> dict` (Enterprise)

### Métodos de Destilación (Pro/Ent)
- `distill_train(config, samples=1000, batch_size=100, seed=42) -> dict`
- `distill_predict(data: dict, config) -> float`
- `distill_predict_batch(data_points: list[dict], config) -> list[float]`
- `distill_export() -> dict` (Solo Enterprise)

---

## ⚠️ Errores Comunes

### 422 Model Not Trained
**Causa**: Sustituto no entrenado o config no coincide  
**Solución**: Ejecutar `sdk.distill_train(config, ...)` con la misma config

### 429 Rate Limited
**Causa**: Se excedieron los límites del tier  
**Solución**: Usar operaciones batch, dividir requests grandes, respetar el header `Retry-After`

### 413 Payload Too Large
**Causa**: Dataset o payload excede límites de tamaño  
**Solución**: Dividir dataset en chunks más pequeños o reducir parámetros de generación (solo Enterprise)

### 400 Invalid Config
**Causa**: Faltan campos requeridos o valores de parámetros inválidos  
**Solución**: Asegurar que config tenga `default`, `importance`, `sensitivity` por cada campo

---



## 📞 Soporte

- **Documentación**: https://docs.dsf-aml.ai
- **Issues**: https://github.com/dsf-aml/sdk/issues
- **Enterprise**: contacto@softwarefinanzas.com.co

---

## 📄 Licencia

MIT para tier Community. Professional/Enterprise bajo términos comerciales.

© 2025 DSF AML SDK — ML Adaptativo impulsado por Destilación de Conocimiento