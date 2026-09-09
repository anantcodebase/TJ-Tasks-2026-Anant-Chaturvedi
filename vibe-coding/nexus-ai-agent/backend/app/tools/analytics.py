from statistics import mean
from app.models import AnalyticsMetric, AnalyticsResult


DATA = {
    "Mon": {"engagement": 58.0, "sessions": 420, "conversion": 7.6, "sales": 18200.0},
    "Tue": {"engagement": 64.0, "sessions": 510, "conversion": 8.1, "sales": 21400.0},
    "Wed": {"engagement": 61.0, "sessions": 486, "conversion": 7.9, "sales": 20750.0},
    "Thu": {"engagement": 72.0, "sessions": 620, "conversion": 8.8, "sales": 24900.0},
    "Fri": {"engagement": 76.0, "sessions": 710, "conversion": 9.1, "sales": 28700.0},
    "Sat": {"engagement": 69.0, "sessions": 590, "conversion": 8.5, "sales": 23100.0},
    "Sun": {"engagement": 74.0, "sessions": 648, "conversion": 8.9, "sales": 26200.0}
}


async def query_analytics(metric: AnalyticsMetric) -> AnalyticsResult:
    labels = list(DATA.keys())
    values = [DATA[label][metric] for label in labels]
    average = mean(values)

    if metric == "engagement":
        summary = f"Average engagement was {average:.1f}%, with a peak of {max(values):.1f}% on Friday."
    elif metric == "sessions":
        summary = f"The dashboard recorded {sum(values):,} sessions across seven days, averaging {average:,.0f} per day."
    elif metric == "conversion":
        summary = f"Average conversion was {average:.1f}%, peaking at {max(values):.1f}% on Friday."
    else:
        summary = f"Sales totaled ${sum(values):,.0f}, averaging ${average:,.0f} per day, with the strongest day on Friday."

    return AnalyticsResult(
        metric=metric,
        period="7d",
        values=values,
        labels=labels,
        summary=summary
    )
