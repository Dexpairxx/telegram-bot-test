# DeFiLlama Stablecoin Yield Telegram Bot

Bot Telegram theo dõi và thông báo về stablecoin yield pools từ DeFiLlama.

## Tính năng

- 🔔 **Thông báo tự động** lúc 9h sáng hàng ngày với top 20 stablecoin pools (APR > 12%, TVL > $5M)
- 📊 **Tra cứu thủ công** với lệnh `/TopTVL`

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

## Deploy lên Railway

### Bước 1: Push lên GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

### Bước 2: Deploy trên Railway

1. Truy cập [railway.com/new](https://railway.com/new)
2. Chọn **"Deploy from GitHub repo"**
3. Chọn repository của bạn
4. Railway sẽ tự động detect Procfile và deploy

### Bước 3: Cấu hình Environment Variables

Trong Railway dashboard, vào **Variables** và thêm:

| Variable    | Value                   | Mô tả                             |
| ----------- | ----------------------- | --------------------------------- |
| `BOT_TOKEN` | `8305431317:AAFr-wf...` | Token của bot Telegram            |
| `CHAT_ID`   | `123456789`             | Chat ID để nhận thông báo tự động |

> 💡 **Lấy Chat ID:** Gửi `/start` cho bot, bot sẽ hiển thị Chat ID của bạn.

## Nguồn dữ liệu

- [DeFiLlama Yields API](https://yields.llama.fi/pools)
- Chỉ lọc các pools có `stablecoin: true`

## License

MIT
