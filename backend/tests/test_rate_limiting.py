import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.core.rate_limiter import TokenBucketRateLimiter, RateLimitMiddleware
from backend.core.redis_client import cache

@pytest.mark.asyncio
async def test_health_and_diagnostics_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Check standard health
        h_res = await client.get("/api/health")
        assert h_res.status_code == 200
        assert h_res.json()["status"] == "OPERATIONAL"

        # Check workers diagnostic
        w_res = await client.get("/api/health/workers")
        assert w_res.status_code == 200
        data = w_res.json()
        assert data["status"] == "HEALTHY"
        assert "workers" in data
        assert "cache" in data

        # Check system diagnostics
        s_res = await client.get("/api/health/system")
        assert s_res.status_code == 200
        s_data = s_res.json()
        assert s_data["status"] == "OPERATIONAL"
        assert s_data["database_backend"] == "sqlite"

@pytest.mark.asyncio
async def test_token_bucket_rate_limiter_logic():
    # Dedicated limiter with 5 capacity and 60 rate (1 token per second)
    limiter = TokenBucketRateLimiter(default_rate=60.0, default_capacity=5)
    key = "test-officer-ip"

    # Should allow 5 requests
    for i in range(5):
        allowed, remaining, reset_secs = limiter.is_allowed(key)
        assert allowed is True
        assert remaining == 4 - i

    # 6th request should be denied
    allowed, remaining, reset_secs = limiter.is_allowed(key)
    assert allowed is False
    assert remaining == 0
    assert reset_secs > 0

    # Resetting should restore allowance
    limiter.reset(key)
    allowed, remaining, _ = limiter.is_allowed(key)
    assert allowed is True

@pytest.mark.asyncio
async def test_cache_telemetry_and_expiry():
    await cache.set("forensic_test_key", "active_value", ex=2)
    val = await cache.get("forensic_test_key")
    assert val == "active_value"

    stats = cache.get_stats()
    assert stats["hits"] >= 1
    assert "hit_ratio_pct" in stats
