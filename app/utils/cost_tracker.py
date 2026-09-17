# app/utils/cost_tracker.py
from typing import Optional
from app.db.session import SessionLocal
from app.models.cost import TokenUsage

# Current USD to INR Exchange Rate
USD_TO_INR = 83.50

# Official Model Pricing Registry (USD per 1 Million Tokens)
MODEL_PRICING_TABLE = {
    # Large High-Parameter Models
    "openai/gpt-oss-120b": {
        "input_per_million_usd": 0.60,
        "output_per_million_usd": 0.80,
    },
    # Embedding Models (Input only)
    "gemini-embedding-001": {
        "input_per_million_usd": 0.02,
        "output_per_million_usd": 0.00,
    },
    # Default fallback
    "default": {
        "input_per_million_usd": 0.10,
        "output_per_million_usd": 0.20,
    }
}


def calculate_cost_inr(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Calculates exact cost in Indian Rupees (₹) based on model rates and token volume.
    Formula: (Input Tokens * Input Rate + Output Tokens * Output Rate) * USD_TO_INR
    """
    rates = MODEL_PRICING_TABLE.get(model, MODEL_PRICING_TABLE["openai/gpt-oss-120b"])

    input_cost_usd = (prompt_tokens / 1_000_000.0) * rates["input_per_million_usd"]
    output_cost_usd = (completion_tokens / 1_000_000.0) * rates["output_per_million_usd"]
    total_cost_usd = input_cost_usd + output_cost_usd

    total_cost_inr = total_cost_usd * USD_TO_INR
    return round(total_cost_inr, 5)


def track_tokens(feature: str, model: str, usage, user_id: Optional[int] = None):
    """
    Dynamically logs real tokens and real calculated cost into PostgreSQL,
    linked strictly to the user who triggered the request!
    """
    if not usage:
        return

    prompt_tok = getattr(usage, "prompt_tokens", 0) or 0
    comp_tok = getattr(usage, "completion_tokens", 0) or 0
    total_tok = prompt_tok + comp_tok

    cost_inr = calculate_cost_inr(model, prompt_tok, comp_tok)

    db = SessionLocal()
    try:
        record = TokenUsage(
            user_id=user_id,
            feature=feature,
            model=model,
            prompt_tokens=prompt_tok,
            completion_tokens=comp_tok,
            total_tokens=total_tok,
            cost_inr=cost_inr
        )
        db.add(record)
        db.commit()
    except Exception as e:
        print(f"[!] Cost logging failed: {e}")
    finally:
        db.close()