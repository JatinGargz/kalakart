"""PRICING ENGINE — Wage-floor anti-bargain shield formula."""
from __future__ import annotations

DEFAULT_WAGE_PER_HOUR = 80.0      # ~₹640 / 8-hr artisan day
DEFAULT_OVERHEAD_PCT = 12.0
DEFAULT_PROFIT_PCT = 25.0


def compute_pricing(material_cost: float, labour_hours: float,
                    wage_per_hour: float = DEFAULT_WAGE_PER_HOUR,
                    overhead_pct: float = DEFAULT_OVERHEAD_PCT,
                    profit_pct: float = DEFAULT_PROFIT_PCT,
                    buyer_offer: float | None = None) -> dict:
    material_cost = max(0.0, float(material_cost))
    labour_hours = max(0.0, float(labour_hours))
    labour_cost = round(labour_hours * wage_per_hour, 2)
    base = material_cost + labour_cost
    overhead = round(base * (overhead_pct / 100.0), 2)
    total_cost = round(base + overhead, 2)
    floor_price = round(total_cost * 1.10, 2)          # 10% minimum dignity margin
    suggested_price = round(total_cost * (1 + profit_pct / 100.0), 2)
    wholesale_price = round(total_cost * 1.15, 2)       # B2B lean margin

    out = {
        "material_cost": material_cost,
        "labour_hours": labour_hours,
        "wage_per_hour": wage_per_hour,
        "labour_cost": labour_cost,
        "overhead_pct": overhead_pct,
        "overhead": overhead,
        "total_cost": total_cost,
        "floor_price": floor_price,
        "suggested_price": suggested_price,
        "wholesale_price": wholesale_price,
        "profit_pct": profit_pct,
        "formula": "total=(material+hours*wage)*(1+overhead%); floor=total*1.10; suggested=total*(1+profit%)",
    }
    if buyer_offer is not None:
        offer = float(buyer_offer)
        out["buyer_offer"] = offer
        if offer < floor_price:
            verdict, code = "Too Low 🔴", "TOO_LOW"
            pct = round((1 - offer / suggested_price) * 100, 1) if suggested_price else 0
            msg_en = (f"Offer ₹{offer:,.0f} is {pct}% below suggested ₹{suggested_price:,.0f} "
                      f"and below your dignity floor ₹{floor_price:,.0f}. Counter at ₹{suggested_price:,.0f}.")
            msg_hi = (f"₹{offer:,.0f} का भाव बहुत कम है — लागत ₹{total_cost:,.0f}, "
                      f"न्यूनतम ₹{floor_price:,.0f} से भी नीचे। ₹{suggested_price:,.0f} पर अड़े रहें।")
        elif offer < suggested_price:
            verdict, code = "Negotiable 🟡", "NEGOTIABLE"
            msg_en = (f"Close! Offer ₹{offer:,.0f} is above floor ₹{floor_price:,.0f} "
                      f"but below suggested ₹{suggested_price:,.0f}. Counter at ₹{suggested_price:,.0f}.")
            msg_hi = (f"ठीक-ठाक भाव है, पर सुझाव ₹{suggested_price:,.0f} से कम। ₹{suggested_price:,.0f} मांगें।")
        else:
            verdict, code = "Fair 🟢", "FAIR"
            msg_en = f"Great! ₹{offer:,.0f} is at/above suggested ₹{suggested_price:,.0f}. Accept with confidence."
            msg_hi = f"बधाई! ₹{offer:,.0f} उचित दाम है — स्वीकार करें।"
        out.update({"verdict": verdict, "verdict_code": code,
                    "message_en": msg_en, "message_hi": msg_hi})
    return out
