# DeFiLlama Stablecoin Yield Telegram Bot

Bot Telegram theo dõi và thông báo về stablecoin yield pools từ DeFiLlama.

## Tính năng

- **Thông báo tự động** lúc 9h sáng hàng ngày với top 20 stablecoin pools (APR > 12%, TVL > $5M)
- **Tra cứu thủ công** với lệnh `/TopTVL`

## Cài đặt Local

```bash
# Clone repo
git clone <your-repo-url>
cd <repo-name>

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt

# Chạy bot
python main.py
```

## Lệnh Bot

| Lệnh                          | Mô tả             |
| ----------------------------- | ----------------- |
| `/start`                      | Xem thông tin bot |
| `/help`                       | Hướng dẫn sử dụng |
| `/TopTVL [count] [tvl] [apr]` | Tra cứu top pools |

**Ví dụ:**

- `/TopTVL 25 2 15` → Top 25, TVL > $2M, APR > 15%
- `/TopTVL 10` → Top 10, TVL > $5M, APR > 12%
- `/TopTVL` → Top 20, TVL > $5M, APR > 12%
