#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║           ماسح إشارات العملات المشفرة - Crypto Spot Signal Scanner          ║
║                                                                  ║
║  هذا السكربت يقوم بمسح جميع أزواج USDT على بينانس ويبحث عن      ║
║  إشارات شراء محتملة باستخدام التحليل الفني على الإطار الزمني   ║
║  每ساعة (1H) باستخدام استراتيجيات متعددة.                           ║
║                                                                  ║
║  Author: AI Trading Engine                                       ║
║  Version: 1.0.0                                                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import requests
import time
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import math

# ─────────────────────────────────────────────────────────────────────────────
# إعداد السجل (Logging)
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s │ [%(levelname)s] │ %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scanner.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# ثوابت الاتصال بـ Binance API
# ─────────────────────────────────────────────────────────────────────────────
# محاولة عدة نقاط وصول (Binance has regional endpoints)
BINANCE_ENDPOINTS = [
    "https://api.binance.com/api/v3",
    "https://api1.binance.com/api/v3",
    "https://api2.binance.com/api/v3",
    "https://api3.binance.com/api/v3",
]
BINANCE_USDT_QUOTE    = "USDT"
MIN_VOLUME_USDT       = 1_000_000      # الحد الأدنى لحجم التداول خلال 24 ساعة (USDT)
MAX_PAIRS             = 200            # الحد الأقصى لأزواج العملات للمعالجة
REQUEST_TIMEOUT       = 30             # مهلة الطلب بالثواني
RATE_LIMIT_DELAY      = 0.25           # تأخير بين الطلبات لتجنب تجاوز الحد (ثانية)
MAX_RETRIES           = 2              # عدد محاولات إعادة الطلب (للإصدار المحلي)
RETRY_DELAY           = 5              # تأخير بين المحاولات

# ─────────────────────────────────────────────────────────────────────────────
# CoinGecko API (fallback when Binance is geo-blocked)
# ─────────────────────────────────────────────────────────────────────────────
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

# ─────────────────────────────────────────────────────────────────────────────
# CryptoCompare API (alternative independent source) - Requires API Key
# ─────────────────────────────────────────────────────────────────────────────
CRYPTOCOMPARE_API = "https://min-api.cryptocompare.com/data"

# ─────────────────────────────────────────────────────────────────────────────
# Yahoo Finance - مصدر بديل للعملات المشفرة الرئيسية
# ─────────────────────────────────────────────────────────────────────────────
YFINANCE_COINS = [
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD",
    "ADA-USD", "DOGE-USD", "DOT-USD", "MATIC-USD", "SHIB-USD",
    "LTC-USD", "AVAX-USD", "LINK-USD", "UNI-USD", "ATOM-USD",
    "XLM-USD", "ETC-USD", "FIL-USD", "APT-USD", "NEAR-USD",
    "ALGO-USD", "FTM-USD", "AAVE-USD", "GRT-USD", "ARB-USD",
    "OP-USD", "INJ-USD", "SAND-USD", "MANA-USD", "AXS-USD",
    "THETA-USD", "EOS-USD", "XTZ-USD", "CAKE-USD", "SNX-USD",
    "CRV-USD", "LDO-USD", "MKR-USD", "RUNE-USD", "ZIL-USD",
    "ENJ-USD", "BAT-USD", "COMP-USD", "1INCH-USD", "CHZ-USD",
    "ENS-USD", "FXS-USD", "GMX-USD", "WOO-USD", "GALA-USD",
    "IMX-USD", "RNDR-USD", "OCEAN-USD", "FET-USD", "AGIX-USD",
    "VET-USD", "HBAR-USD", "NEO-USD", "KCS-USD", "TRX-USD",
    "KAVA-USD", "ZEC-USD", "DASH-USD", "WAVES-USD", "HOT-USD",
    "XMR-USD", "NANO-USD", "IOTA-USD", "DCR-USD", "ZRX-USD",
    "OMG-USD", "SC-USD", "RVN-USD", "KSM-USD", "ICX-USD",
    "QTUM-USD", "ONT-USD", "ADA-USD", "ALPHA-USD", "BAND-USD",
    "BEL-USD", "BLZ-USD", "COTI-USD", "DENT-USD", "DGB-USD",
    "EGLD-USD", "HNT-USD", "IOTX-USD", "JASMY-USD", "JOE-USD",
    "KDA-USD", "KEY-USD", "LINA-USD", "LRC-USD", "LSK-USD",
    "MINA-USD", "MOVR-USD", "OGN-USD", "ONE-USD", "ONG-USD",
    "PAXG-USD", "PIXEL-USD", "POLS-USD", "POND-USD", "POWR-USD",
    "QI-USD", "RAD-USD", "RARE-USD", "REEF-USD", "REN-USD",
    "REQ-USD", "RLC-USD", "RSR-USD", "RSS-USD", "RVC-USD",
    "SCRT-USD", "SFP-USD", "SLP-USD", "SPELL-USD", "SRM-USD",
    "STMX-USD", "STORJ-USD", "SUSHI-USD", "SXP-USD", "SYS-USD",
    "T-USD", "TFUEL-USD", "TKO-USD", "TLM-USD", "TROY-USD",
    "TVK-USD", "UMA-USD", "UNFI-USD", "UTK-USD", "VGX-USD",
    "VIDT-USD", "VTHO-USD", "WAN-USD", "WAXP-USD", "WIN-USD",
    "WNC-USD", "WRX-USD", "XEM-USD", "XNO-USD", "XVS-USD",
    "YFI-USD", "YFII-USD", "YGG-USD", "ZEN-USD", "ZKS-USD",
    "ZK-USD", "SUI-USD", "SEI-USD", "TIA-USD", "PEPE-USD",
    "WIF-USD", "FLOKI-USD", "BONK-USD", "PYTH-USD", "JTO-USD",
    "WLD-USD", "STRK-USD", "REZ-USD", "BB-USD", "NOT-USD",
    "IO-USD", "PIXEL-USD", "PORTAL-USD", "ALT-USD", "W-USD",
    "BOME-USD", "SAGA-USD", "MER-USD", "LISTA-USD", "DOGS-USD",
    "HMSTR-USD", "CATI-USD", "SLERF-USD", "NFP-USD", "UXLINK-USD",
    "KAIA-USD", "ACT-USD", "PNUT-USD", "CHILL-USD", "MOODENG-USD",
]

# ─────────────────────────────────────────────────────────────────────────────
# إعدادات المؤشرات الفنية
# ─────────────────────────────────────────────────────────────────────────────
INDICATOR_CONFIG = {
    "ema_short":     20,
    "ema_medium":    50,
    "ema_long":      200,
    "rsi_period":    14,
    "st_atr":        10,
    "st_multiplier": 3,
    "vol_sma_period": 20,
    "vol_threshold":   1.5,
    "macd_fast":     12,
    "macd_slow":     26,
    "macd_signal":   9,
}

# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
#                          فئة الماسح الرئيسية
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

class BinanceSpotScanner:
    """
    فئة الماسح الرئيسية للتعامل مع Binance API وتنفيذ التحليل الفني.
    """

    def __init__(self):
        """تهيئة الاتصال بجلسة الطلبات."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.binance.com/",
        })
        self._endpoints = BINANCE_ENDPOINTS.copy()
        self._current_endpoint_idx = 0
        self._indicators_config = INDICATOR_CONFIG.copy()
        self.signals: List[Dict[str, Any]] = []
        self.stats: Dict[str, Any] = {}

    @property
    def base_url(self) -> str:
        """الحصول على نقطة الوصول الحالية."""
        return self._endpoints[self._current_endpoint_idx]

    def _rotate_endpoint(self) -> bool:
        """التبديل إلى نقطة الوصول التالية. يُرجع True إذا وجدت واحدة."""
        for i in range(1, len(self._endpoints)):
            idx = (self._current_endpoint_idx + i) % len(self._endpoints)
            logger.info(f"🔄 التبديل إلى نقطة الوصول: {self._endpoints[idx]}")
            self._current_endpoint_idx = idx
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # وظائف المساعدة - الطلبات الآمنة
    # ─────────────────────────────────────────────────────────────────────────

    def _safe_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        تنفيذ طلب HTTP آمن مع إعادة المحاولة ومعالجة الأخطاء.

        Args:
            endpoint: مسار API (مثل '/ticker/24hr' أو '/coins/markets')
            params: معاملات الاستعلام الاختيارية

        Returns:
            بيانات الاستجابة كقاموس أو None في حالة الفشل
        """
        # تحديد الـ base URL بناءً على نوع الـ endpoint
        if endpoint.startswith("/coins"):
            url = f"{COINGECKO_API_BASE}{endpoint}"
        else:
            url = f"{self.base_url}{endpoint}"

        for endpoint_idx in range(len(self._endpoints)):
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.HTTPError as e:
                    status = e.response.status_code
                    if status == 429:
                        # تجاوز حد معدل الطلبات - انتظار طويل
                        wait = RETRY_DELAY * 3
                        logger.warning(f"⚠️ تجاوز حد Rate Limit، انتظار {wait}s...")
                        time.sleep(wait)
                    elif status == 451:
                        # غير متاح لأسباب قانونية - تخطي فوراً
                        logger.warning(f"⚠️ HTTP 451 من {url}، تخطي...")
                        break  # keluar dari retry loop
                    else:
                        logger.warning(f"⚠️ خطأ HTTP {status} في {endpoint} - المحاولة {attempt}/{MAX_RETRIES}")
                        if attempt < MAX_RETRIES:
                            time.sleep(RETRY_DELAY)
                except requests.exceptions.RequestException as e:
                    logger.warning(f"⚠️ خطأ: {e} - المحاولة {attempt}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
            else:
                continue  # semua retry gagal, coba endpoint lain

            # التبديل لنقطة الوصول التالية
            if not endpoint.startswith("/coins"):
                if self._rotate_endpoint():
                    url = f"{self.base_url}{endpoint}"
                    continue
            break  # لم تعد هناك نقاط وصول متاحة

        return None

    def _safe_request_list(self, endpoint: str, params: Optional[Dict] = None) -> Optional[List]:
        """
        تنفيذ طلب HTTP آمن لبيانات القائمة مع إعادة المحاولة.
        على 451 (geo-block) يرجع None فوراً لتسريع التبديل للمصادر البديلة.
        """
        url = f"{self.base_url}{endpoint}"

        for endpoint_idx in range(len(self._endpoints)):
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                    return response.json()
                except requests.exceptions.HTTPError as e:
                    status = e.response.status_code
                    if status == 429:
                        wait = RETRY_DELAY * 3
                        logger.warning(f"⚠️ تجاوز حد Rate Limit، انتظار {wait}s...")
                        time.sleep(wait)
                    elif status == 451:
                        logger.warning(f"⚠️ HTTP 451، تخطي...")
                        break  # تخطي فوراً
                    else:
                        logger.warning(f"⚠️ خطأ HTTP {status} - المحاولة {attempt}/{MAX_RETRIES}")
                        if attempt < MAX_RETRIES:
                            time.sleep(RETRY_DELAY)
                except requests.exceptions.RequestException as e:
                    logger.warning(f"⚠️ خطأ: {e} - المحاولة {attempt}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
            else:
                continue

            if self._rotate_endpoint():
                url = f"{self.base_url}{endpoint}"
                continue
            break

        return None

    def _safe_request_list(self, endpoint: str, params: Optional[Dict] = None) -> Optional[List]:
        """
        تنفيذ طلب HTTP آمن لبيانات القائمة مع إعادة المحاولة.

        Args:
            endpoint: مسار API
            params: معاملات الاستعلام الاختيارية

        Returns:
            قائمة البيانات أو None في حالة الفشل
        """
        url = f"{self.base_url}{endpoint}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
                if status == 429:
                    wait = RETRY_DELAY * 3
                    logger.warning(f"⚠️ تجاوز حد Rate Limit، انتظار {wait}s...")
                    time.sleep(wait)
                else:
                    logger.warning(f"⚠️ خطأ HTTP {status} - المحاولة {attempt}/{MAX_RETRIES}")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠️ خطأ: {e} - المحاولة {attempt}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
        return None

    # ─────────────────────────────────────────────────────────────────────────
    # جلب أزواج USDT النشطة
    # ─────────────────────────────────────────────────────────────────────────

    def get_usdt_pairs(self) -> List[Dict[str, Any]]:
        """
        جلب جميع أزواج USDT النشطة من Binance مع معلومات الحجم.
        يحاول جميع نقاط الوصول (Binance global + regional) ثم CoinGecko كبديل.

        Returns:
            قائمة القواميس تحتوي على اسم الزوج والحجم وغيرها
        """
        logger.info("🔍 جاري جلب جميع أزواج USDT من Binance (مع نقاط وصول متعددة)...")

        # محاولة Binance مع نقاط الوصول المتعددة
        for i in range(len(self._endpoints)):
            logger.info(f"🔗 محاولة نقطة الوصول {i+1}/{len(self._endpoints)}: {self._endpoints[i]}")
            data = self._safe_request("/ticker/24hr")
            if data:
                pairs = self._parse_binance_ticker(data)
                if pairs:
                    return pairs
            # التبديل لنقطة الوصول التالية
            if i < len(self._endpoints) - 1:
                self._rotate_endpoint()

        # ─────────────────────────────────────────────────────────────────────────
        # Fallback: استخدام CoinGecko API
        # ─────────────────────────────────────────────────────────────────────────
        logger.warning("⚠️ تعذر الوصول إلى Binance، جاري استخدام CoinGecko كبديل...")
        return self._get_pairs_from_coingecko()

    def _parse_binance_ticker(self, data: List) -> List[Dict[str, Any]]:
        """تحليل بيانات Binance ticker."""
        pairs = []
        for item in data:
            # تصفية: فقط أزواج USDT المنتهية بـ USDT
            if not item.get("symbol", "").endswith(BINANCE_USDT_QUOTE):
                continue

            # تصفية: الأزواج فقط (ليسادات)
            if item.get("isIsolated", False):
                continue

            # تصفية: حالة التداول
            if item.get("status", "") != "TRADING":
                continue

            # تصفية: الحجم المحدد بـ quoteVolume (USDT)
            try:
                volume_24h = float(item.get("quoteVolume", 0))
            except (ValueError, TypeError):
                continue

            if volume_24h < MIN_VOLUME_USDT:
                continue

            pairs.append({
                "symbol":      item["symbol"],
                "price":       float(item.get("lastPrice", 0)),
                "volume_24h":  volume_24h,
                "price_change": float(item.get("priceChangePercent", 0)),
                "high_24h":    float(item.get("highPrice", 0)),
                "low_24h":     float(item.get("lowPrice", 0)),
            })

        # ترتيب حسب الحجم (الأكبر أولاً)
        pairs.sort(key=lambda x: x["volume_24h"], reverse=True)

        # تحديد الحد الأقصى
        pairs = pairs[:MAX_PAIRS]

        logger.info(f"✅ تم العثور على {len(pairs)} زوج USDT نشط من Binance")
        return pairs

    def _get_pairs_from_coingecko(self) -> List[Dict[str, Any]]:
        """
        جلب أزواج العملات من CoinGecko API كبديل لـ Binance.
        CoinGecko قد يكون متاحاً من مناطق محظورة.
        """
        logger.info("🔍 جاري جلب بيانات السوق من CoinGecko...")
        url = f"{COINGECKO_API_BASE}/coins/markets"
        params = {
            "vs_currency":    "usd",
            "order":          "volume_desc",
            "per_page":       str(MAX_PAIRS),
            "page":           "1",
            "sparkline":      "false",
            "price_change_percentage": "24h",
        }
        data = self._safe_request("/coins/markets", params)

        if not data:
            logger.error("❌ فشل في جلب البيانات من CoinGecko!")
            return []

        pairs = []
        for item in data:
            try:
                volume_usd = float(item.get("total_volume", 0) or 0)
                price_change = float(item.get("price_change_percentage_24h", 0) or 0)
            except (ValueError, TypeError):
                continue

            # تصفية: الحجم الأدنى
            if volume_usd < MIN_VOLUME_USDT:
                continue

            symbol = (item.get("symbol", "") or "").upper()
            # CoinGecko uses lowercase symbols; convert to Binance format
            pair_symbol = f"{symbol}USDT"

            pairs.append({
                "symbol":      pair_symbol,
                "baseAsset":   symbol,
                "price":       float(item.get("current_price", 0) or 0),
                "volume_24h":  volume_usd,
                "price_change": price_change,
                "high_24h":    float(item.get("high_24h", 0) or 0),
                "low_24h":     float(item.get("low_24h", 0) or 0),
                "source":      "coingecko",
                "coin_id":     item.get("id", ""),
            })

        pairs.sort(key=lambda x: x["volume_24h"], reverse=True)
        logger.info(f"✅ تم العثور على {len(pairs)} عملة نشطة من CoinGecko")
        return pairs

    def _get_histohour_from_cryptocompare(self, symbol: str) -> Optional[List]:
        """
        جلب بيانات OHLCV كل ساعة من CryptoCompare API كبديل.
        ملاحظة: يتطلب مفتاح API للوصول لمعظم نقاط النهاية.

        Args:
            symbol: رمز العملة بدون USDT (مثل 'BTC')

        Returns:
            قائمة الشموع أو None في حالة الفشل
        """
        url = f"{CRYPTOCOMPARE_API}/v2/histohour"
        params = {
            "fsym":  symbol.upper(),
            "tsym":  "USDT",
            "limit": 200,
            "aggregate": 1,
        }
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                result = response.json()
                if result.get("Response") == "Success":
                    data = result.get("Data", {}).get("Data", [])
                    # تحويل تنسيق CryptoCompare إلى تنسيق مشابه لـ Binance klines
                    # [open_time, open, high, low, close, volume]
                    klines = []
                    for candle in data:
                        klines.append([
                            candle.get("time", 0),
                            candle.get("open", 0),
                            candle.get("high", 0),
                            candle.get("low", 0),
                            candle.get("close", 0),
                            candle.get("volumefrom", 0),
                        ])
                    return klines
                return None
            except Exception as e:
                logger.warning(f"⚠️ خطأ CryptoCompare {symbol}: {e} - المحاولة {attempt}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
        return None

    def _get_klines_from_yfinance(self, symbol: str) -> Optional[List[List]]:
        """
        جلب بيانات OHLCV كل ساعة من Yahoo Finance كبديل.

        Args:
            symbol: رمز العملة بدون USDT (مثل 'BTC')

        Returns:
            قائمة الشموع بصيغة Binance klines أو None
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.warning("⚠️ yfinance غير مثبت")
            return None

        yf_symbol = f"{symbol.upper()}-USD"

        try:
            ticker = yf.Ticker(yf_symbol)
            # جلب بيانات 15 يوم بأطار ساعة للحصول على 350+ شمعة
            hist = ticker.history(period="15d", interval="1h", auto_adjust=True)

            if hist.empty or len(hist) < 50:
                logger.warning(f"⚠️ Yahoo Finance: لا توجد بيانات كافية لـ {yf_symbol}")
                return None

            # تحويل إلى تنسيق Binance klines
            # [open_time, open, high, low, close, volume]
            klines = []
            for dt, row in hist.iterrows():
                timestamp = int(dt.timestamp())
                klines.append([
                    timestamp,           # open_time
                    float(row['Open']), # open
                    float(row['High']), # high
                    float(row['Low']),  # low
                    float(row['Close']),# close
                    float(row['Volume']),# volume
                ])

            logger.info(f"✅ Yahoo Finance: تم جلب {len(klines)} شمعة لـ {yf_symbol}")
            return klines

        except Exception as e:
            logger.warning(f"⚠️ خطأ Yahoo Finance {yf_symbol}: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────────
    # جلب بيانات الشموع (Klines)
    # ─────────────────────────────────────────────────────────────────────────

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 250) -> Optional[List[List]]:
        """
        جلب بيانات الشموع (OHLCV) لزوج محدد.
        يحاول: Binance → Yahoo Finance كبديل.

        Args:
            symbol: رمز العملة (مثل 'BTCUSDT')
            interval: الإطار الزمني (مثل '1h', '4h', '1d')
            limit: عدد الشموع المطلوب (الحد الأقصى 1000)

        Returns:
            قائمة الشموع أو None في حالة الفشل
        """
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        data = self._safe_request_list("/klines", params)

        if data is not None:
            time.sleep(RATE_LIMIT_DELAY)
            return data

        # ─────────────────────────────────────────────────────────────────────────
        # Fallback: Yahoo Finance
        # ─────────────────────────────────────────────────────────────────────────
        base = symbol.replace("USDT", "").upper()
        return self._get_klines_from_yfinance(base)

    # ─────────────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────
    #                      المؤشرات الفنية - التنفيذ اليدوي
    # ─────────────────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _sma(values: List[float], period: int) -> List[Optional[float]]:
        """
        حساب المتوسطات المتحركة البسيطة (SMA).

        Args:
            values: قائمة الأسعار
            period: فترة SMA

        Returns:
            قائمة القيم مع None للقيم غير المحسوبة بعد
        """
        result = []
        for i in range(len(values)):
            if i < period - 1:
                result.append(None)
            else:
                result.append(sum(values[i - period + 1:i + 1]) / period)
        return result

    @staticmethod
    def _ema(values: List[float], period: int) -> List[Optional[float]]:
        """
        حساب المتوسطات المتحركة الأسية (EMA).

        Formula: EMA = (Close - Previous EMA) * multiplier + Previous EMA
        multiplier = 2 / (period + 1)

        Args:
            values: قائمة الأسعار
            period: فترة EMA

        Returns:
            قائمة قيم EMA مع None للقيم غير المحسوبة بعد
        """
        if len(values) < period:
            return [None] * len(values)

        result: List[Optional[float]] = [None] * (period - 1)

        # أول قيمة EMA هي SMA للفترة الأولى
        first_sma = sum(values[:period]) / period
        result.append(first_sma)

        multiplier = 2 / (period + 1)

        for i in range(period, len(values)):
            ema = (values[i] - result[-1]) * multiplier + result[-1]
            result.append(ema)

        return result

    @staticmethod
    def _rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
        """
        حساب مؤشر القوة النسبية (RSI).

        RSI = 100 - (100 / (1 + RS))
        RS = متوسط الأرباح / متوسط الخسائر

        Args:
            prices: قائمة أسعار الإغلاق
            period: فترة RSI (الافتراضي 14)

        Returns:
            قائمة قيم RSI (0-100)
        """
        if len(prices) < period + 1:
            return [None] * len(prices)

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        result: List[Optional[float]] = [None] * period

        # أول متوسط باستخدام SMA
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100 - (100 / (1 + rs)))

        # تبسيط EMA للفترة المتبقية
        multiplier = 1 / period
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                result.append(100 - (100 / (1 + rs)))

        return result

    @staticmethod
    def _atr(highs: List[float], lows: List[float], closes: List[float], period: int = 10) -> List[Optional[float]]:
        """
        حساب متوسط المدى الحقيقي (ATR) اللازم لـ SuperTrend.

        True Range = max(H - L, |H - Close_prev|, |L - Close_prev|)
        ATR = Wilder's smoothing of True Range

        Args:
            highs: قائمة أعلى الأسعار
            lows: قائمة أدنى الأسعار
            closes: قائمة أسعار الإغلاق
            period: فترة ATR

        Returns:
            قائمة قيم ATR
        """
        if len(highs) < period + 1:
            return [None] * len(highs)

        tr_list = []
        for i in range(len(highs)):
            if highs[i] is None or lows[i] is None or closes[i] is None:
                tr_list.append(None)
                continue
            tr = highs[i] - lows[i]
            if i > 0 and closes[i - 1] is not None:
                hl = abs(highs[i] - closes[i - 1])
                ll = abs(lows[i] - closes[i - 1])
                tr = max(tr, hl, ll)
            tr_list.append(tr)

        result: List[Optional[float]] = [None] * period
        # أول ATR هو SMA للشموع الأولى
        valid_tr = [v for v in tr_list[:period] if v is not None]
        if not valid_tr:
            return [None] * len(tr_list)
        first_atr = sum(valid_tr) / len(valid_tr)
        result.append(first_atr)

        # Wilder's smoothing (EMA with alpha = 1/period)
        for i in range(period, len(tr_list)):
            if tr_list[i] is None or result[-1] is None:
                result.append(None)
            else:
                atr = (result[-1] * (period - 1) + tr_list[i]) / period
                result.append(atr)

        return result

    @staticmethod
    def _supertrend(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        atr_period: int = 10,
        multiplier: float = 3.0
    ) -> List[Dict[str, Any]]:
        """
        حساب مؤشر SuperTrend.

        Upper Band = (High + Low) / 2 + multiplier * ATR
        Lower Band = (High + Low) / 2 - multiplier * ATR

        الاتجاه الصاعد: عندما يكون السعر فوق Upper Band
        الاتجاه الهابط: عندما يكون السعر تحت Lower Band

        Args:
            highs: قائمة أعلى الأسعار
            lows: قائمة أدنى الأسعار
            closes: قائمة أسعار الإغلاق
            atr_period: فترة ATR
            multiplier: المضاعف

        Returns:
            قائمة القواميس مع direction (-1 bearish, 1 bullish) و upper_band و lower_band
        """
        atr_values = BinanceSpotScanner._atr(highs, lows, closes, atr_period)
        result = []

        for i in range(len(closes)):
            if atr_values[i] is None:
                result.append({"direction": 0, "upper_band": None, "lower_band": None})
                continue

            hl2 = (highs[i] + lows[i]) / 2
            upper_band = hl2 + multiplier * atr_values[i]
            lower_band = hl2 - multiplier * atr_values[i]

            if i == 0:
                direction = 1  # افتراضي صاعد
            else:
                prev_result = result[i - 1]
                prev_direction = prev_result["direction"]
                prev_upper = prev_result.get("upper_band")
                prev_lower = prev_result.get("lower_band")

                if prev_direction == -1 and prev_upper is not None:  # كان هابطاً
                    # الباندات قد ترتفع فقط
                    upper_band = min(upper_band, prev_upper)
                    if closes[i] > prev_upper:
                        direction = 1
                    else:
                        direction = -1
                elif prev_direction == 1 and prev_lower is not None:  # كان صاعداً
                    # الباندات قد تنخفض فقط
                    lower_band = max(lower_band, prev_lower)
                    if closes[i] < prev_lower:
                        direction = -1
                    else:
                        direction = 1
                else:
                    # حالة انتقالية أو غير محددة - تعيين الاتجاه الجديد
                    direction = 1 if closes[i] > upper_band else (-1 if closes[i] < lower_band else prev_direction)

            result.append({
                "direction":   direction,
                "upper_band":  upper_band,
                "lower_band":  lower_band,
            })

        return result

    @staticmethod
    def _macd(
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> List[Dict[str, Optional[float]]]:
        """
        حساب مؤشر MACD.

        MACD Line = EMA(fast) - EMA(slow)
        Signal Line = EMA(MACD Line, signal_period)
        Histogram = MACD Line - Signal Line

        Args:
            prices: قائمة أسعار الإغلاق
            fast: فترة EMA السريعة
            slow: فترة EMA البطيئة
            signal: فترة خط الإشارة

        Returns:
            قائمة القواميس مع macd_line, signal_line, histogram
        """
        if len(prices) < slow + signal:
            return [{"macd_line": None, "signal_line": None, "histogram": None}] * len(prices)

        ema_fast = BinanceSpotScanner._ema(prices, fast)
        ema_slow = BinanceSpotScanner._ema(prices, slow)

        macd_line_vals = []
        for i in range(len(prices)):
            if ema_fast[i] is not None and ema_slow[i] is not None:
                macd_line_vals.append(ema_fast[i] - ema_slow[i])
            else:
                macd_line_vals.append(None)

        # Signal line is EMA of MACD line
        # Find first valid MACD value
        first_valid = None
        for v in macd_line_vals:
            if v is not None:
                first_valid = v
                break

        if first_valid is None:
            return [{"macd_line": None, "signal_line": None, "histogram": None}] * len(prices)

        signal_line_vals: List[Optional[float]] = [None] * len(macd_line_vals)
        first_valid_idx = next(i for i, v in enumerate(macd_line_vals) if v is not None)

        # First signal value is SMA of first 'signal' values
        first_signal_sma = sum(
            macd_line_vals[first_valid_idx:first_valid_idx + signal]
        ) / signal
        signal_line_vals[first_valid_idx + signal - 1] = first_signal_sma

        multiplier = 2 / (signal + 1)
        current_signal = first_signal_sma

        for i in range(first_valid_idx + signal, len(macd_line_vals)):
            if macd_line_vals[i] is not None:
                current_signal = (macd_line_vals[i] - current_signal) * multiplier + current_signal
                signal_line_vals[i] = current_signal

        result = []
        for i in range(len(prices)):
            macd_val = macd_line_vals[i]
            sig_val = signal_line_vals[i]
            hist = (macd_val - sig_val) if (macd_val is not None and sig_val is not None) else None
            result.append({
                "macd_line":   macd_val,
                "signal_line": sig_val,
                "histogram":   hist,
            })

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # حساب جميع المؤشرات دفعة واحدة
    # ─────────────────────────────────────────────────────────────────────────

    def calculate_indicators(self, klines: List) -> Dict[str, Any]:
        """
        حساب جميع المؤشرات الفنية من بيانات الشموع.

        Args:
            klines: قائمة الشموع من Binance API

        Returns:
            قاموس يحتوي على جميع المؤشرات المحسوبة
        """
        if not klines or len(klines) < 50:
            return {}

        # استخراج القيم من الشموع
        # [open_time, open, high, low, close, volume, close_time, ...]
        highs  = [float(k[2]) for k in klines]
        lows   = [float(k[3]) for k in klines]
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[5]) for k in klines]

        cfg = self._indicators_config

        # حساب جميع المؤشرات
        ema_20   = self._ema(closes, cfg["ema_short"])
        ema_50   = self._ema(closes, cfg["ema_medium"])
        ema_200  = self._ema(closes, cfg["ema_long"])
        rsi      = self._rsi(closes, cfg["rsi_period"])
        st       = self._supertrend(highs, lows, closes, cfg["st_atr"], cfg["st_multiplier"])
        macd     = self._macd(closes, cfg["macd_fast"], cfg["macd_slow"], cfg["macd_signal"])
        vol_sma  = self._sma(volumes, cfg["vol_sma_period"])

        # آخر 3 قيم (للتحقق من التقاطعات)
        def last(vals, offset=0):
            """إرجاع آخر قيمة غير None مع إمكانية الإزاحة."""
            valid = [v for v in vals if v is not None]
            if not valid:
                return None
            return valid[-(1 + offset)] if offset > 0 else valid[-1]

        def prev(vals, n=1):
            """إرجاع القيمة قبل الأخيرة."""
            valid = [v for v in vals if v is not None]
            idx = len(valid) - n
            if idx < 0:
                return None
            return valid[idx]

        return {
            "close":      closes[-1],
            "ema_20":     last(ema_20),
            "ema_50":     last(ema_50),
            "ema_200":    last(ema_200),
            "rsi":        last(rsi),
            "rsi_prev":   prev(rsi, 1),
            "supertrend": last(st),
            "supertrend_prev": prev(st, 1),
            "macd":       last(macd),
            "macd_prev":  prev(macd, 1),
            "volume":     volumes[-1],
            "volume_sma": last(vol_sma),
            "volume_ratio": (volumes[-1] / last(vol_sma)) if last(vol_sma) and last(vol_sma) > 0 else 0,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # تقييم الاستراتيجيات
    # ─────────────────────────────────────────────────────────────────────────

    def evaluate_strategies(self, ind: Dict) -> List[str]:
        """
        تقييم جميع الاستراتيجيات وإرجاع قائمة الاستراتيجيات المحققة.

        Args:
            ind: قاموس المؤشرات المحسوبة

        Returns:
            قائمة بأسماء الاستراتيجيات المحققة
        """
        matched: List[str] = []

        e20  = ind.get("ema_20")
        e50  = ind.get("ema_50")
        e200 = ind.get("ema_200")
        rsi  = ind.get("rsi")
        st   = ind.get("supertrend", {})
        macd_cur  = ind.get("macd", {})
        macd_prev = ind.get("macd_prev", {})
        vol_ratio = ind.get("volume_ratio", 0)

        # ─────────────────────────────────────────────────────────────────────
        # الاستراتيجية A: استمرار الاتجاه الصاعد
        # الشروط:
        #   - السعر فوق EMA 200 (الاتجاه العام صاعد)
        #   - SuperTrend bullish (direction = 1)
        #   - RSI بين 45 و 65 (منطقة القوة المتوازنة)
        # ─────────────────────────────────────────────────────────────────────
        strategy_a = (
            e200 is not None and ind["close"] > e200
            and st.get("direction") == 1
            and rsi is not None and 45 <= rsi <= 65
        )
        if strategy_a:
            matched.append("A")

        # ─────────────────────────────────────────────────────────────────────
        # الاستراتيجية B: تقاطع الزخم الصاعد
        # الشروط:
        #   - EMA 20 يعبر فوق EMA 50 (تحتاج التقاطعين: السابق كان تحت أو يساوي، الحالي فوق)
        #   - الحجم أكبر من 1.5x من متوسط الحجم
        # ─────────────────────────────────────────────────────────────────────
        e20_prev  = ind.get("ema_20")   # إعادة الحساب للج_prev
        e50_prev  = ind.get("ema_50")
        # نستخدم قيم prev من ema
        ema_20_all = self._ema([float(k[4]) for k in self._last_klines_for_ema], self._indicators_config["ema_short"])
        ema_50_all = self._ema([float(k[4]) for k in self._last_klines_for_ema], self._indicators_config["ema_medium"])

        e20_prev_val = None
        e50_prev_val = None
        valid_ema20 = [v for v in ema_20_all if v is not None]
        valid_ema50 = [v for v in ema_50_all if v is not None]
        if len(valid_ema20) >= 2:
            e20_prev_val = valid_ema20[-2]
        if len(valid_ema50) >= 2:
            e50_prev_val = valid_ema50[-2]

        strategy_b = (
            e20 is not None and e50 is not None
            and e20_prev_val is not None and e50_prev_val is not None
            and e20_prev_val <= e50_prev_val          # كان تحت أو يساوي
            and e20 > e50                              # الآن فوق
            and vol_ratio >= self._indicators_config["vol_threshold"]
        )
        if strategy_b:
            matched.append("B")

        # ─────────────────────────────────────────────────────────────────────
        # الاستراتيجية C: انعكاس MACD الصاعد
        # الشروط:
        #   - خط MACD يعبر فوق خط الإشارة (histogram يتغير من سالب إلى موجب)
        #   - السعر فوق EMA 50
        # ─────────────────────────────────────────────────────────────────────
        macd_hist = macd_cur.get("histogram")
        macd_hist_prev = macd_prev.get("histogram")

        strategy_c = (
            macd_hist is not None and macd_hist_prev is not None
            and macd_hist_prev <= 0                 # كان عند أو تحت الصفر
            and macd_hist > 0                        # الآن فوق الصفر
            and e50 is not None and ind["close"] > e50
        )
        if strategy_c:
            matched.append("C")

        return matched

    # ─────────────────────────────────────────────────────────────────────────
    # تخزين مؤقت مؤقت للـ EMA
    # ─────────────────────────────────────────────────────────────────────────
    _last_klines_for_ema: List = []

    # ─────────────────────────────────────────────────────────────────────────
    # المسح الكامل
    # ─────────────────────────────────────────────────────────────────────────

    def run_scan(self) -> Dict[str, Any]:
        """
        تشغيل المسح الكامل لجميع الأزواج.

        Returns:
            قاموس يحتوي على الإحصائيات والإشارات
        """
        logger.info("=" * 60)
        logger.info("🚀 بدء مسح إشارات العملات المشفرة")
        logger.info("=" * 60)

        scan_start = datetime.now(timezone.utc)
        pairs = self.get_usdt_pairs()

        if not pairs:
            logger.error("❌ لم يتم العثور على أزواج USDT!")
            return {
                "timestamp": scan_start.isoformat(),
                "total_scanned": 0,
                "signals": [],
                "error": "فشل في جلب الأزواج",
            }

        signals: List[Dict[str, Any]] = []
        errors_count = 0

        logger.info(f"📊 جاري تحليل {len(pairs)} زوج...")

        for i, pair in enumerate(pairs):
            symbol = pair["symbol"]
            logger.info(f"  [{i+1}/{len(pairs)}] تحليل {symbol}...", extra={"continue": True})

            try:
                klines = self.get_klines(symbol, "1h", 250)
                if not klines or len(klines) < 50:
                    errors_count += 1
                    logger.info(f"\r  [{i+1}/{len(pairs)}] {symbol} - بيانات غير كافية")
                    continue

                # تخزين للاستخدام في الاستراتيجية B
                self._last_klines_for_ema = klines

                indicators = self.calculate_indicators(klines)
                if not indicators:
                    errors_count += 1
                    continue

                matched_strategies = self.evaluate_strategies(indicators)

                if matched_strategies:
                    strategy_labels = {
                        "A": "استمرار الاتجاه",
                        "B": "تقاطع الزخم",
                        "C": "انعكاس MACD الصاعد",
                    }

                    # تقييم حجم التداول
                    vol = indicators.get("volume", 0)
                    vol_sma = indicators.get("volume_sma", 1)
                    vol_ratio = vol / vol_sma if vol_sma and vol_sma > 0 else 0

                    signal = {
                        "symbol":         symbol,
                        "baseAsset":      symbol.replace(BINANCE_USDT_QUOTE, ""),
                        "price":          round(indicators["close"], 8),
                        "price_str":      self._format_price(indicators["close"]),
                        "volume_24h":     round(pair["volume_24h"], 2),
                        "volume_24h_str": self._format_volume(pair["volume_24h"]),
                        "price_change_24h": pair["price_change"],
                        "strategies":     matched_strategies,
                        "strategy_labels": [strategy_labels[s] for s in matched_strategies],
                        "rsi":            round(indicators["rsi"], 2) if indicators.get("rsi") else None,
                        "rsi_label":      self._rsi_label(indicators.get("rsi")),
                        "ema_20":         round(indicators["ema_20"], 8) if indicators.get("ema_20") else None,
                        "ema_50":         round(indicators["ema_50"], 8) if indicators.get("ema_50") else None,
                        "ema_200":        round(indicators["ema_200"], 8) if indicators.get("ema_200") else None,
                        "supertrend_dir": indicators.get("supertrend", {}).get("direction", 0),
                        "volume_ratio":   round(vol_ratio, 2),
                        "volume_label":   self._volume_label(vol_ratio),
                        "macd_hist":      round(indicators.get("macd", {}).get("histogram"), 8)
                                          if indicators.get("macd", {}).get("histogram") else None,
                        "timestamp":      scan_start.isoformat(),
                    }
                    signals.append(signal)
                    logger.info(
                        f"\r  ✅ {symbol} → استراتيجية: {', '.join(matched_strategies)} | "
                        f"RSI: {indicators.get('rsi', 0):.1f} | الحجم: {vol_ratio:.1f}x"
                    )
                else:
                    print(f"\r  [{i+1}/{len(pairs)}] {symbol} - لا توجد إشارات", end="")

            except Exception as e:
                errors_count += 1
                logger.error(f"\r  ❌ خطأ في تحليل {symbol}: {e}")

        scan_end = datetime.now(timezone.utc)

        # الإحصائيات
        stats = {
            "total_scanned":  len(pairs),
            "signals_found":  len(signals),
            "errors":         errors_count,
            "scan_duration": (scan_end - scan_start).total_seconds(),
            "scan_start":     scan_start.isoformat(),
            "scan_end":       scan_end.isoformat(),
            "min_volume":     MIN_VOLUME_USDT,
            "timeframe":      "1H",
            "strategies": {
                "A": len([s for s in signals if "A" in s["strategies"]]),
                "B": len([s for s in signals if "B" in s["strategies"]]),
                "C": len([s for s in signals if "C" in s["strategies"]]),
            },
        }

        self.stats = stats
        self.signals = signals

        # ترتيب الإشارات حسب الحجم (الأكبر أولاً)
        signals.sort(key=lambda x: x["volume_24h"], reverse=True)

        result = {
            "timestamp":     scan_start.isoformat(),
            "stats":         stats,
            "signals":       signals,
            "next_update":   self._next_update_time(),
        }

        logger.info("=" * 60)
        logger.info(f"✅ اكتمل المسح! تم العثور على {len(signals)} إشارة")
        logger.info(f"   الأزواج المفحوصة: {stats['total_scanned']}")
        logger.info(f"   الأخطاء: {stats['errors']}")
        logger.info(f"   المدة: {stats['scan_duration']:.1f} ثانية")
        logger.info("=" * 60)

        return result

    # ─────────────────────────────────────────────────────────────────────────
    # وظائف مساعدة
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _format_price(price: float) -> str:
        """تنسيق السعر بشكل مقروء."""
        if price >= 1000:
            return f"{price:,.2f}"
        elif price >= 1:
            return f"{price:.4f}"
        elif price >= 0.01:
            return f"{price:.6f}"
        else:
            return f"{price:.8f}"

    @staticmethod
    def _format_volume(volume: float) -> str:
        """تنسيق الحجم بمعاملات مناسبة."""
        if volume >= 1_000_000_000:
            return f"{volume / 1_000_000_000:.2f}B"
        elif volume >= 1_000_000:
            return f"{volume / 1_000_000:.2f}M"
        elif volume >= 1_000:
            return f"{volume / 1_000:.2f}K"
        return f"{volume:.2f}"

    @staticmethod
    def _rsi_label(rsi: Optional[float]) -> str:
        """إرجاع وصف حالة RSI."""
        if rsi is None:
            return "غير محدد"
        if rsi < 30:
            return "ذروة البيع"
        elif rsi < 45:
            return "قريب من ذروة البيع"
        elif rsi <= 55:
            return "محايد"
        elif rsi <= 65:
            return "قريب من ذروة الشراء"
        elif rsi < 70:
            return "ذروة الشراء"
        else:
            return "ذروة الشراء القوية"

    @staticmethod
    def _volume_label(ratio: float) -> str:
        """إرجاع وصف حالة الحجم."""
        if ratio >= 2.5:
            return "حجم كبير جداً ⚡"
        elif ratio >= 2.0:
            return "حجم كبير 📈"
        elif ratio >= 1.5:
            return "حجم فوق المتوسط 📊"
        elif ratio >= 1.0:
            return "حجم عادي"
        else:
            return "حجم منخفض 📉"

    @staticmethod
    def _next_update_time() -> str:
        """حساب وقت التحديث التالي."""
        now = datetime.now(timezone.utc)
        # اقتراب من الساعة التالية (مع علامة 5 دقائق)
        next_hour = now.replace(minute=5, second=0, microsecond=0)
        if now.minute >= 5:
            from datetime import timedelta
            next_hour += timedelta(hours=1)
        return next_hour.isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# نقطة الدخول الرئيسية
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """نقطة الدخول الرئيسية للسكربت."""
    scanner = BinanceSpotScanner()
    result = scanner.run_scan()

    # كتابة النتائج إلى ملف JSON
    output_file = "signals.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"💾 تم حفظ النتائج في {output_file}")
    return result


if __name__ == "__main__":
    main()
