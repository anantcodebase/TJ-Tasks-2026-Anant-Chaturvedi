import asyncio

from app.tools.analytics import DATA, query_analytics


def test_sales_analytics():
    result = asyncio.run(query_analytics("sales"))
    assert result.metric == "sales"
    assert len(result.values) == 7
    assert "Sales totaled" in result.summary


def test_mock_analytics_labels_are_unique():
    assert list(DATA.keys()) == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
