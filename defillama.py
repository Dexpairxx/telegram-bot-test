"""
DeFiLlama API Client for fetching stablecoin yield pools.
"""
import requests
from typing import List, Dict, Any, Optional


DEFILLAMA_YIELDS_URL = "https://yields.llama.fi/pools"
DEFILLAMA_PROTOCOLS_URL = "https://api.llama.fi/protocols"
DEFILLAMA_CHART_URL = "https://yields.llama.fi/chart"


def fetch_pool_age(pool_id: str) -> Optional[int]:
    """
    Fetch pool age in days from DeFiLlama chart API.
    Returns the number of days since the pool was first listed.
    """
    try:
        response = requests.get(f"{DEFILLAMA_CHART_URL}/{pool_id}", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "success" or not data.get("data"):
            return None
        
        # Get the first data point (oldest)
        first_entry = data["data"][0]
        first_timestamp = first_entry.get("timestamp")
        
        if not first_timestamp:
            return None
        
        # Parse timestamp and calculate days
        from datetime import datetime
        first_date = datetime.strptime(first_timestamp[:10], "%Y-%m-%d")
        today = datetime.now()
        age_days = (today - first_date).days
        
        return age_days
    except Exception:
        return None


def fetch_protocols() -> Dict[str, Dict[str, Any]]:
    """Fetch protocols data from DeFiLlama to get audit and category info."""
    try:
        response = requests.get(DEFILLAMA_PROTOCOLS_URL, timeout=30)
        response.raise_for_status()
        protocols = response.json()
        
        # Create a mapping from protocol slug to protocol info
        protocol_map = {}
        for protocol in protocols:
            slug = protocol.get("slug", "").lower()
            name = protocol.get("name", "").lower()
            
            # Map by slug and name variations
            protocol_info = {
                "audits": protocol.get("audits", "0"),
                "category": protocol.get("category", "N/A"),
                "audit_links": protocol.get("audit_links", []),
            }
            
            if slug:
                protocol_map[slug] = protocol_info
            if name:
                protocol_map[name] = protocol_info
                # Also map without spaces/dashes
                protocol_map[name.replace(" ", "-")] = protocol_info
                protocol_map[name.replace("-", " ")] = protocol_info
        
        return protocol_map
    except Exception as e:
        print(f"Error fetching protocols: {e}")
        return {}


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
        
        # Fetch protocol info for audit and category
        protocol_map = fetch_protocols()
        
        # Enrich pools with protocol info
        for pool in stablecoin_pools:
            project = pool.get("project", "").lower()
            
            # Try to find protocol info
            protocol_info = protocol_map.get(project, {})
            if not protocol_info:
                # Try with variations
                protocol_info = protocol_map.get(project.replace("-", " "), {})
            if not protocol_info:
                protocol_info = protocol_map.get(project.replace(" ", "-"), {})
            
            # Add protocol info to pool
            pool["audits"] = protocol_info.get("audits", "N/A")
            pool["category"] = protocol_info.get("category", "N/A")
            pool["audit_links"] = protocol_info.get("audit_links", [])
            
        
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
                pool.get("apy")
                or pool.get("apyBase")
                or pool.get("apyReward")
                or pool.get("apyMean30d")
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
    
    # Get new fields
    audits = pool.get("audits", "N/A")
    category = pool.get("category", "N/A")
    
    # Format audit status
    if audits == "2":
        audit_str = "yes"
    elif audits == "0":
        audit_str = "no"
    else:
        audit_str = "N/A"
    
    # Get pool age
    pool_age = pool.get("age_days")
    if pool_age is not None:
        if pool_age >= 365:
            age_str = f"{pool_age // 365}y {(pool_age % 365) // 30}m"
        elif pool_age >= 30:
            age_str = f"{pool_age // 30}m {pool_age % 30}d"
        else:
            age_str = f"{pool_age}d"
    else:
        age_str = "N/A"
    
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
        f"   🏷️ Category: {category}\n"
        f"   🔒 Audit: {audit_str}\n"
        f"   ⏱️ Age: {age_str}\n"
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
        return "Không thể lấy dữ liệu từ DeFiLlama. Vui lòng thử lại sau."
    
    filtered_pools = filter_pools(pools, min_tvl_millions, min_apr, top_n)
    
    if not filtered_pools:
        return (
            f"Không tìm thấy stablecoin pool nào với:\n"
            f"• APR > {min_apr}%\n"
            f"• TVL > ${min_tvl_millions}M"
        )
    
    header = (
        f"🔥 TOP {len(filtered_pools)} STABLECOIN YIELD POOLS\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Điều kiện: APR > {min_apr}% | TVL > ${min_tvl_millions}M\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    # Fetch pool age for filtered pools (only for the ones we'll display)
    for pool in filtered_pools:
        pool_id = pool.get("pool", "")
        if pool_id:
            pool["age_days"] = fetch_pool_age(pool_id)
    
    pool_messages = [format_pool_message(pool, i + 1) for i, pool in enumerate(filtered_pools)]
    
    footer = (
        f"\n━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    return header + "\n\n".join(pool_messages) + footer


if __name__ == "__main__":
    # Test the module
    print(get_top_pools_message(min_tvl_millions=5, min_apr=12, top_n=5))



