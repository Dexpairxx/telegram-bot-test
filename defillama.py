"""
DeFiLlama API Client for fetching stablecoin yield pools.
"""
import requests
from typing import List, Dict, Any, Optional


DEFILLAMA_YIELDS_URL = "https://yields.llama.fi/pools"


def fetch_stablecoin_pools() -> List[Dict[str, Any]]:
    """Fetch all pools from DeFiLlama and filter for stablecoins only."""
    try:
        response = requests.get(DEFILLAMA_YIELDS_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "success":
            return []
        
        pools = data.get("data", [])
        # Filter for stablecoin pools only
        stablecoin_pools = [p for p in pools if p.get("stablecoin") is True]
        return stablecoin_pools
    except Exception as e:
        print(f"Error fetching pools: {e}")
        return []


def filter_pools(
    pools: List[Dict[str, Any]],
    min_tvl_millions: float = 5.0,
    min_apr: float = 12.0,
    top_n: int = 20
) -> List[Dict[str, Any]]:
    """
    Filter pools by TVL and APR thresholds, return top N sorted by APR descending.
    
    Args:
        pools: List of pool data from DeFiLlama
        min_tvl_millions: Minimum TVL in millions USD
        min_apr: Minimum APR percentage
        top_n: Number of top pools to return
    
    Returns:
        Filtered and sorted list of pools
    """
    min_tvl = min_tvl_millions * 1_000_000
    
    filtered = []
    for pool in pools:
        tvl = pool.get("tvlUsd") or 0
        apy = (
                pool.get("apyMean30d")
                or pool.get("apyReward")
                or pool.get("apyBase")
                or pool.get("apy")
                or 0
            )

        
        if tvl >= min_tvl and apy >= min_apr:
            filtered.append(pool)
    
    # Sort by APY descending
    filtered.sort(key=lambda x: x.get("apy", 0), reverse=True)
    
    return filtered[:top_n]


def format_pool_message(pool: Dict[str, Any], rank: int) -> str:
    """Format a single pool for Telegram message."""
    symbol = pool.get("symbol", "N/A")
    project = pool.get("project", "N/A")
    chain = pool.get("chain", "N/A")
    apy = pool.get("apy") or 0
    tvl = pool.get("tvlUsd", 0)
    pool_meta = pool.get("poolMeta", "")
    pool_id = pool.get("pool", "")
    
    # Format TVL
    if tvl >= 1_000_000_000:
        tvl_str = f"${tvl / 1_000_000_000:.2f}B"
    elif tvl >= 1_000_000:
        tvl_str = f"${tvl / 1_000_000:.2f}M"
    else:
        tvl_str = f"${tvl:,.0f}"
    
    meta_str = f" ({pool_meta})" if pool_meta else ""
    
    # Create DeFiLlama pool URL
    pool_url = f"https://defillama.com/yields/pool/{pool_id}" if pool_id else ""
    
    return (
        f"{rank}. {symbol}{meta_str}\n"
        f"   📊 Project: {project}\n"
        f"   🔗 Chain: {chain}\n"
        f"   💰 APR: {apy:.2f}%\n"
        f"   🏦 TVL: {tvl_str}\n"
        f"   🔎 {pool_url}"
    )


def get_top_pools_message(
    min_tvl_millions: float = 5.0,
    min_apr: float = 12.0,
    top_n: int = 20
) -> str:
    """
    Get formatted message with top stablecoin pools.
    
    Args:
        min_tvl_millions: Minimum TVL in millions USD
        min_apr: Minimum APR percentage
        top_n: Number of top pools to return
    
    Returns:
        Formatted message string for Telegram
    """
    pools = fetch_stablecoin_pools()
    
    if not pools:
        return "❌ Không thể lấy dữ liệu từ DeFiLlama. Vui lòng thử lại sau."
    
    filtered_pools = filter_pools(pools, min_tvl_millions, min_apr, top_n)
    
    if not filtered_pools:
        return (
            f"📊 Không tìm thấy stablecoin pool nào với:\n"
            f"• APR > {min_apr}%\n"
            f"• TVL > ${min_tvl_millions}M"
        )
    
    header = (
        f"🔥 TOP {len(filtered_pools)} STABLECOIN YIELD POOLS\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 Điều kiện: APR > {min_apr}% | TVL > ${min_tvl_millions}M\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    pool_messages = [format_pool_message(pool, i + 1) for i, pool in enumerate(filtered_pools)]
    
    footer = (
        f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 Nguồn: DeFiLlama\n"
        f"⏰ Cập nhật: Realtime"
    )
    
    return header + "\n\n".join(pool_messages) + footer


if __name__ == "__main__":
    # Test the module
    print(get_top_pools_message(min_tvl_millions=5, min_apr=12, top_n=5))
