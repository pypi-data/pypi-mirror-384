# DSF Label SDK

**Accelerate AI development with programmatic data labeling and weak supervision. Reduce labeling costs by 90% and time from months to minutes.**

## Why DSF Label?

The 80/20 rule in AI: 80% of effort goes to data preparation and labeling, 20% to actual model development. Manual data labeling is slow, expensive, and inconsistent. This SDK transforms your domain expertise into **programmatic heuristics** that label datasets at scale with human-like accuracy.

---

## Core Concepts

Instead of manually labeling thousands of examples, define a set of weighted **heuristics** based on your domain knowledge. The system evaluates how well each data point matches these rules, producing labels with confidence scores. Data that falls into uncertain ranges gets flagged for human review, optimizing your labeling budget.

---

## Installation

```bash
# Standard version
pip install dsf-label-sdk

# For optimized performance (requires C++ compiler)
pip install dsf-label-sdk[optimized]
```

---

## Configuration (Environment Variables)

### For SDK Usage

Professional and Enterprise tiers require license validation through our secure server. You'll need to configure two environment variables that you'll receive with your license purchase:

-   `SUPABASE_URL`: The URL of our validation service
-   `SUPABASE_ANON_KEY`: The public key for service authentication

### How to Configure

#### On Linux or macOS

Add to your shell profile (`~/.bashrc` or `~/.zshrc`):

```bash
export SUPABASE_URL="your_provided_url"
export SUPABASE_ANON_KEY="your_provided_key"
```

#### On Windows (PowerShell)

```powershell
$env:SUPABASE_URL="your_provided_url"
$env:SUPABASE_ANON_KEY="your_provided_key"
```

#### For Local Development (Recommended)

Create a `.env` file in your project root:

```
SUPABASE_URL="your_provided_url"
SUPABASE_ANON_KEY="your_provided_key"

# Optional: Specify a self-hosted API endpoint instead of the default
DSF_API_ENDPOINT="https://your-project.vercel.app/api/evaluate"

# Optional: Enable fallback for development (not for production)
ENABLE_LICENSE_FALLBACK=false
```

Load the variables using `python-dotenv`:

```python
# Instala la librería: pip install python-dotenv
from dotenv import load_dotenv
load_dotenv()

# El resto de tu código ahora tendrá acceso a las variables
from dsf_label import LabelSDK
```

---

## Quick Start

### Community Edition (Free)

```python
from dsf_label import LabelSDK

# Initialize SDK
sdk = LabelSDK()

# Build configuration directly
config = (sdk.create_config()
    .add_field('contains_spam_keywords', default=True, weight=5.0, criticality=5.0)
    .add_field('has_suspicious_links', default=True, weight=4.0, criticality=4.0)
    .add_field('text_length', default=50, weight=2.0, criticality=1.5)
    .add_field('excessive_caps_ratio', default=0.3, weight=3.0, criticality=3.0)
)

# Alternative: Build configuration programmatically
# config = sdk.create_config()
# for field_data in your_field_definitions:
#     config.add_field(name=field_data['name'], **field_data['params'])

# Label individual data points
email_features = {
    'contains_spam_keywords': True,
    'has_suspicious_links': True,
    'text_length': 45,
    'excessive_caps_ratio': 0.8
}

result = sdk.evaluate(email_features, config)
print(f"Score: {result.score:.3f}")
print(f"Above threshold: {result.is_above_threshold}")
```

### Professional Edition

⚠️ **Importante:** Para usar las características de Professional o Enterprise, primero debes haber configurado tus variables de entorno. Consulta la sección de **Configuration** para más detalles.

```python
from dsf_label import LabelSDK
import pandas as pd

# Initialize with license
sdk = LabelSDK(
    license_key='PRO-2026-12-31-XXXX-XXXX',
    tier='professional'
)

# Professional: Batch processing
df = pd.read_csv('unlabeled_reviews.csv')
results = sdk.batch_evaluate(
    data_points=df.to_dict('records'),
    config=config
)

# Access adaptive metrics
metrics = sdk.get_metrics()
print(f"Adapted threshold: {metrics['current_confidence_level']:.3f}")
print(f"Average score: {metrics['avg_score']:.3f}")
print(f"Total evaluations: {metrics['evaluations']}")
```

### Enterprise Edition

```python
from dsf_label import LabelSDK

# Initialize with enterprise features
sdk = LabelSDK(
    license_key='ENT-2026-12-31-XXXX-XXXX',
    tier='enterprise',
    mode='temporal_forgetting'  # Use recent data window for adaptation
)

# Enterprise exclusive: Control weight calibration
sdk.set_adjustment_factor(0.4)  # 60% expert weights, 40% algorithm-optimized

# Process large datasets with automatic weight optimization
for batch in large_dataset_batches:
    results = sdk.batch_evaluate(batch, config)
    
    # Reset learning when data patterns change significantly
    if detected_pattern_shift():
        sdk.invalidate_cache()

# View how the system adapted heuristic weights
metrics = sdk.get_metrics()
if metrics['adaptive_weights']:
    print("Heuristic weight optimizations:")
    for field, change in metrics['weight_changes'].items():
        print(f"  {field}: {change:+.2%} from initial")
    print(f"Cache version: {metrics['cache_version']}")
```

---

## Using Config Builder

The SDK provides a fluent ConfigBuilder interface with two equivalent usage patterns:

```python
from dsf_label import LabelSDK

sdk = LabelSDK()

# Method 1: Chained calls (best for fixed configurations)
config = (sdk.create_config()
    .add_field('temperature', default=20, weight=1.0, criticality=1.5)
    .add_field('pressure', default=1.0, weight=0.8, criticality=1.2)
    .add_field('humidity', default=0.5, weight=0.6, criticality=1.0)
)

# Method 2: Sequential calls (best for dynamic configurations)
config = sdk.create_config()
for field_name, params in dynamic_field_definitions.items():
    config.add_field(field_name, **params)

# Both methods produce the same configuration
result = sdk.evaluate(data, config)
```

---

## Context Manager Pattern

```python
from dsf_label import LabelSDK

# Automatic resource cleanup
with LabelSDK(license_key='...', tier='enterprise') as sdk:
    result = sdk.evaluate(data, config)
    metrics = sdk.get_metrics()
    # Connection automatically cleaned up on exit
```

---

## Error Handling

```python
from dsf_label import LabelSDK, LicenseError, ValidationError

try:
    sdk = LabelSDK(license_key='invalid', tier='professional')
    result = sdk.evaluate(data, config)
    
except LicenseError as e:
    print(f"License error: {e}")
    # Fallback to community tier
    sdk = LabelSDK()
    
except ValidationError as e:
    print(f"Invalid configuration: {e}")
    # Check config format: weight/criticality must be 0.0-5.0
```

---

## Tier Comparison

| Feature                          |  Community  |      Professional       |       Enterprise         |
|----------------------------------|-------------|-------------------------|--------------------------|
| **Labels/month**                 | Unlimited†  |      Unlimited          |       Unlimited          |
| **Single evaluation**            |    ✅       |          ✅            |          ✅              |
| **Batch evaluation**             |    ❌       |          ✅            |          ✅              |
| **DataFrame Processing**         |    ❌       |          ✅            |          ✅              |
| **Adaptive Thresholds**          |    ❌       |          ✅            |          ✅              |
| **Performance Metrics**          |    ❌       |          ✅            |          ✅    Enhanced  |
| **Weight Auto-Calibration**      |    ❌       |          ❌            |          ✅              |
| **Temporal Forgetting Mode**     |    ❌       |          ❌            |          ✅              |
| **Cache Invalidation**           |    ❌       |          ❌            |          ✅              |
| **Support**                      |  Community   |         Email          |     Priority SLA          |
| **License validity**             |    N/A       |        Annual          |        Annual             |

†Community tier is free for evaluation and development. Production use requires registration at https://dsflabel.ai/register (free, provides usage analytics and updates).

---

## Enterprise Features

### Weight Calibration (Enterprise Exclusive)
Enterprise tier automatically optimizes heuristic weights based on data patterns:

```python
# Control the balance between expert and algorithm weights
sdk.set_adjustment_factor(0.3)  # Default: 70% expert, 30% algorithm

# Factor range:
# 0.0 = 100% expert weights (trust configuration)
# 0.5 = 50/50 mix  
# 1.0 = 100% algorithm weights (full automation)
```

The algorithm tracks feature magnitudes using running statistics and mixes expert and algorithmic weights according to your adjustment factor.

### Adaptation Modes (Enterprise Exclusive)
Control how the system learns from historical data:

```python
# Standard mode: Uses full history for adaptation
sdk = LabelSDK(tier='enterprise', mode='standard')

# Temporal forgetting: Only uses recent 20 evaluations
# Better for evolving data patterns
sdk = LabelSDK(tier='enterprise', mode='temporal_forgetting')
```

### Cache Management (Enterprise Exclusive)
Reset the learning system when data patterns change:

```python
# Invalidate cache to restart optimization
sdk.invalidate_cache()  # Clears statistics and resets weight learning
```

---

## Configuration Guidelines

### Heuristic Parameters

```python
config = {
    'field_name': {
        'default': expected_value,    # Target/ideal value
        'weight': 1.0,                # Importance (0.0-5.0)
        'criticality': 1.5             # Sensitivity (0.0-5.0)
    }
}
```

### Parameter Ranges

| Weight      | Meaning      | Use Case                |
|-------------|--------------|-------------------------|
| 0.0 - 1.0   | Minor        | Weak signals            |
| 1.0 - 2.0   | Nice to have | Supporting indicators   |
| 2.0 - 3.0   | Moderate     | Standard features       |
| 3.0 - 4.0   | Important    | Key decision factors    |
| 4.0 - 5.0   | Critical     | Must-have requirements  |

| Criticality | Meaning       | Use Case                    |
|-------------|---------------|-----------------------------|
| 0.0 - 1.0   | Very Flexible | High variation tolerance    |
| 1.0 - 2.0   | Flexible      | Allow variations            |
| 2.0 - 3.0   | Moderate      | Standard strictness         |
| 3.0 - 4.0   | Strict        | Low tolerance for deviation |
| 4.0 - 5.0   | Very Strict   | Near-exact match required   |

---

## Hybrid Model Integration

The SDK accepts **any predictive model** as an additional heuristic, creating powerful ensemble systems:

```python
import joblib
from transformers import pipeline

# Load pre-trained models
bert_classifier = pipeline('sentiment-analysis')
xgboost_model = joblib.load('fraud_detector.pkl')

# Define hybrid configuration
config = {
    # Traditional expert rules
    'transaction_amount': {'default': 100, 'weight': 3.0, 'criticality': 2.0},
    'time_of_day': {'default': 14, 'weight': 2.0, 'criticality': 1.5},
    
    # ML models as heuristics
    'bert_sentiment_score': {'default': 0.8, 'weight': 4.0, 'criticality': 3.0},
    'xgboost_risk_score': {'default': 0.3, 'weight': 4.5, 'criticality': 4.0}
}

# Process with hybrid ensemble
def process_transaction(transaction_data):
    # Get ML predictions
    text_sentiment = bert_classifier(transaction_data['description'])[0]['score']
    xgb_risk = xgboost_model.predict_proba([transaction_data['features']])[0][1]
    
    # Combine all signals
    hybrid_data = {
        'transaction_amount': transaction_data['amount'],
        'time_of_day': transaction_data['hour'],
        'bert_sentiment_score': text_sentiment,
        'xgboost_risk_score': xgb_risk
    }
    
    return sdk.evaluate(hybrid_data, config)
```

---

## API Reference

### LabelSDK

Main SDK interface for programmatic labeling.

**Methods:**
- `__init__(tier='community', license_key=None, mode='standard', api_endpoint=None)` - Initialize SDK
- `evaluate(data, config)` - Evaluate single data point
- `batch_evaluate(data_points, config)` - Process multiple points (Pro/Enterprise)
- `create_config()` - Create config builder
- `get_metrics()` - Get performance statistics (Pro/Enterprise)
- `set_adjustment_factor(factor)` - Weight calibration control (Enterprise)
- `set_confidence_level(level)` - Manual threshold adjustment
- `invalidate_cache()` - Reset learning cache (Enterprise)

### EvaluationResult

Result of evaluation operation.

**Attributes:**
- `score` (float): Confidence score (0.0-1.0)
- `tier` (str): License tier used
- `confidence_level` (float): Current threshold
- `is_above_threshold` (bool): Whether score exceeds threshold
- `metrics` (dict): Performance metrics (Pro/Enterprise only)

### ConfigBuilder

Fluent interface for building configurations.

**Methods:**
- `add_field(name, default, weight=1.0, criticality=1.5)` - Add field configuration
- `remove_field(name)` - Remove field
- `build()` - Get final configuration dict

---

## Deployment Options

### Local SDK Usage
The SDK can operate locally for Community tier or connect to remote API for licensed tiers.

### Vercel Deployment
Deploy the evaluation API to Vercel:

```bash
# Clone repository with API code
git clone https://github.com/dsflabel/api
cd api

# Configure environment variables in Vercel dashboard
# SUPABASE_URL, SUPABASE_ANON_KEY, ENABLE_LICENSE_FALLBACK

# Deploy
vercel deploy
```

### Rate Limiting Note
The API includes rate limiting per instance. In serverless environments like Vercel, this is reset per invocation. For production rate limiting, integrate with external services like Upstash Redis.

---

## Performance Metrics (Pro/Enterprise)

Access detailed metrics to understand system performance:

```python
metrics = sdk.get_metrics()

# Available for Professional and Enterprise
print(f"Total evaluations: {metrics['evaluations']}")
print(f"Average score: {metrics['avg_score']:.3f}")
print(f"Min score: {metrics['min_score']:.3f}")
print(f"Max score: {metrics['max_score']:.3f}")
print(f"Current threshold: {metrics['current_confidence_level']:.3f}")

# Enterprise-only metrics
if metrics.get('adaptive_weights'):
    print(f"Adjusted fields: {metrics['adjusted_fields']}")
    print(f"Weight changes: {metrics['weight_changes']}")
    print(f"Cache version: {metrics['cache_version']}")
    print(f"Adjustment factor: {metrics['adjustment_factor']}")
    print(f"Mode: {metrics['mode']}")  # standard or temporal_forgetting
```

---

## Migration from Manual Labeling

### Before:
```python
# Manual labeling workflow
labeled_data = []
for data_point in unlabeled_dataset:
    # Human manually reviews each example
    label = human_annotator.label(data_point)
    labeled_data.append((data_point, label))
    
# Months of work, high cost, potential inconsistency
```

### After:
```python
# Programmatic labeling with selective human review
sdk = LabelSDK()
review_queue = []

for data_point in unlabeled_dataset:
    result = sdk.evaluate(data_point, config)
    if result.score > 0.75:
        labeled_data.append((data_point, 'POSITIVE'))
    elif result.score < 0.35:
        labeled_data.append((data_point, 'NEGATIVE'))
    else:
        # Only uncertain cases need human review
        review_queue.append(data_point)

# 90% reduction in manual work
```

---

## Use Cases

### Email Spam Detection

```python
config = {
    'contains_spam_keywords': {'default': True, 'weight': 5.0, 'criticality': 5.0},
    'sender_reputation_score': {'default': 0.8, 'weight': 3.0, 'criticality': 3.0},
    'link_count': {'default': 2, 'weight': 2.5, 'criticality': 2.0},
    'image_to_text_ratio': {'default': 0.3, 'weight': 2.0, 'criticality': 2.0}
}
```

### Sentiment Analysis

```python
config = {
    'positive_word_count': {'default': 3, 'weight': 4.0, 'criticality': 2.0},
    'negative_word_count': {'default': 1, 'weight': 4.0, 'criticality': 3.0},
    'has_intensifiers': {'default': True, 'weight': 2.0, 'criticality': 1.5},
    'punctuation_intensity': {'default': 0.1, 'weight': 1.5, 'criticality': 1.5}
}
```

### Content Moderation

```python
config = {
    'contains_profanity': {'default': False, 'weight': 5.0, 'criticality': 5.0},
    'toxicity_score': {'default': 0.2, 'weight': 4.0, 'criticality': 4.0},
    'personal_attacks': {'default': False, 'weight': 4.5, 'criticality': 5.0},
    'context_appropriateness': {'default': 0.8, 'weight': 3.0, 'criticality': 2.0}
}
```

---

## Frequently Asked Questions

### How accurate are the generated labels?
Well-designed configurations achieve 70-90% precision, comparable to human annotators but at scale. The adaptive system improves accuracy over time.

### Can I combine this with active learning?
Yes. Use confidence scores to identify uncertain examples for human review, creating an optimal human-in-the-loop pipeline.

### How do I handle imbalanced datasets?
Adjust the confidence threshold based on class distribution. For rare positive cases, lower the threshold to capture more candidates.

### What's the difference between weight and criticality?
- **Weight**: How much a field contributes to the final score (importance)
- **Criticality**: How strictly deviations are penalized (sensitivity)

### How does adaptive learning work?
- **Professional/Enterprise**: Automatically adjusts decision thresholds based on score distributions after 10+ evaluations
- **Enterprise only**: Additionally optimizes individual field weights based on data patterns and magnitudes

### What is temporal forgetting mode?
Enterprise feature that bases adaptation only on recent evaluations (last 20) instead of full history. Better for data with evolving patterns.

### When should I invalidate the cache?
Use `invalidate_cache()` when your data distribution changes significantly (e.g., new product category, seasonal shift, different data source).

---

## Support

- **Documentation:** https://docs.dsflabel.ai
- **Community:** https://github.com/dsflabel/sdk/discussions  
- **Issues:** https://github.com/dsflabel/sdk/issues
- **Professional/Enterprise Support:** contacto@softwarefinanzas.com.co

---

## Professional & Enterprise Licensing

Professional and Enterprise tiers include:
- Adaptive threshold learning from labeling patterns
- Real-time quality metrics and insights
- Support for batch processing
- Production-ready optimization algorithms
- Enterprise: Automatic weight calibration, temporal modes, cache control

**To purchase a license:**
- Professional: $299/month or $2,999/year
- Enterprise: Contact for custom pricing
- Email: contacto@softwarefinanzas.com.co

**License format:**
- Professional: `PRO-YYYY-MM-DD-XXXX-XXXX`
- Enterprise: `ENT-YYYY-MM-DD-XXXX-XXXX`

---

## License

MIT License for Community Edition. Professional and Enterprise editions are subject to commercial licensing terms.

© 2025 DSF Label SDK. Weak Supervision technology powered by Adaptive Formula.