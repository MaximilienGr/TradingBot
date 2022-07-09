export BINANCE_API_KEY=$(gpg -d BINANCE_API_KEY.gpg 2>/dev/null)
export BINANCE_SECRET_KEY=$(gpg -d BINANCE_SECRET_KEY.gpg 2>/dev/null)
