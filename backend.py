# updated backend.py (improved sentiment + stable weighting, preserves timings)
import os
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

import pandas as pd
import numpy as np
import requests
import yfinance as yf
from dotenv import load_dotenv
import urllib.parse
import math

# ML
from sklearn.ensemble import RandomForestRegressor, VotingRegressor
from sklearn.model_selection import train_test_split, TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Transformers (FinBERT)
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Persistence
import joblib

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "stocksentry")
SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE", "stsn-478509-8fe20c776dfb.json")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://navneetgupta.app.n8n.cloud/webhook/138bb9dd-f80c-4c3a-a941-f90b62870a37")
SENTIMENT_CACHE_FILE = os.getenv("SENTIMENT_CACHE_FILE", ".sentiment_cache.json")
MODEL_STORE = os.getenv("MODEL_STORE", "stock_sentry_model.joblib")

logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("StockSentry")

# ---------- Helper utilities ----------
def safe_load_json(path: str) -> Dict:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load json cache {path}: {e}")
    return {}

def safe_save_json(path: str, obj: Dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save json cache {path}: {e}")

# ---------- Main class ----------
class StockSentryML:
    """
    Backend updated to:
      - Preserve original behavior and timing (n8n wait/polling unchanged)
      - Improved sentiment: caching, recency weighting, normalization, stable weights
      - Backwards-compatible with 2-column sheet (headline, snippet). Supports optional 'takeaway' and 'date' if present.
    """

    def __init__(self,
                 google_sheet_name: str = SHEET_NAME,
                 service_account_file: str = SERVICE_ACCOUNT_FILE,
                 webhook_url: str = N8N_WEBHOOK_URL,
                 sentiment_cache_file: str = SENTIMENT_CACHE_FILE,
                 model_store: str = MODEL_STORE):

        try:
            if not google_sheet_name or not isinstance(google_sheet_name, str):
                raise ValueError("google_sheet_name must be a non-empty string")
            if not webhook_url or not isinstance(webhook_url, str):
                raise ValueError("webhook_url must be a non-empty string")

            self.google_sheet_name = google_sheet_name
            self.service_account_file = service_account_file
            self.webhook_url = webhook_url
            self.sentiment_cache_file = sentiment_cache_file
            self.model_store = model_store

            self.headline_db = pd.DataFrame()
            self.data = pd.DataFrame()
            self.model = None
            self.sentiment_pipeline = None
            self._sentiment_cache = safe_load_json(self.sentiment_cache_file) or {}

            logger.info("Initializing StockSentryML (improved sentiment)")

            # Load FinBERT once if possible; fall back gracefully
            try:
                self._load_finbert()
            except Exception as e:
                logger.error(f"FinBERT initialization failed: {e}")
                self.sentiment_pipeline = None

            # Try load headlines once
            try:
                self.headline_db = self.load_headlines_from_sheet()
            except Exception as e:
                logger.warning(f"Failed to load headlines on init: {e}")
                self.headline_db = pd.DataFrame()

        except Exception as e:
            logger.error(f"Critical initialization error: {e}")
            raise RuntimeError(f"Failed to initialize StockSentryML: {e}")

    # ---------- FinBERT loading & sentiment helpers ----------
    def _load_finbert(self):
        try:
            model_name = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")
            logger.info("Loading FinBERT model: %s", model_name)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)
            # device=-1 forces CPU; preserves behavior
            self.sentiment_pipeline = pipeline("text-classification", model=model, tokenizer=tokenizer, device=-1)
            logger.info("FinBERT loaded successfully (CPU).")
        except Exception as e:
            logger.error("Failed to load FinBERT model: %s", e)
            self.sentiment_pipeline = None

    def _predict_sentiment_for_texts(self, texts: List[str]) -> List[float]:
        """
        Predict sentiment for a list of texts, using cache, FinBERT if available, otherwise heuristic.
        Returns a list of floats in [-1, 1].
        """
        results = []
        for txt in texts:
            key = txt.strip()
            if not key:
                results.append(0.0)
                continue

            # Use cache first
            if key in self._sentiment_cache:
                try:
                    results.append(float(self._sentiment_cache[key]))
                    continue
                except Exception:
                    # fallback to recompute if cache corrupted
                    pass

            score = 0.0
            if self.sentiment_pipeline is None:
                # fall back to heuristic
                score = self._simple_heuristic_sentiment(key)
                logger.debug("Heuristic sentiment for text (len=%d): %.4f", len(key), score)
            else:
                try:
                    pipe_result = self.sentiment_pipeline([key], truncation=True, max_length=512)
                    res = pipe_result[0]
                    label = res.get('label', '').lower()
                    score_prob = float(res.get('score', 0.0))
                    if 'positive' in label:
                        score = min(1.0, score_prob)
                    elif 'negative' in label:
                        score = -min(1.0, score_prob)
                    else:
                        score = 0.0
                except Exception as e:
                    logger.warning("FinBERT run failed for a text; falling back to heuristic: %s", e)
                    score = self._simple_heuristic_sentiment(key)

            # Normalize and clamp
            score = float(max(-1.0, min(1.0, score)))
            # Save to cache
            try:
                self._sentiment_cache[key] = score
            except Exception:
                pass
            results.append(score)

        # Persist cache
        try:
            safe_save_json(self.sentiment_cache_file, self._sentiment_cache)
        except Exception:
            pass

        return results

    def _simple_heuristic_sentiment(self, text: str) -> float:
        positive_words = ['gain', 'rise', 'up', 'beat', 'record', 'strong', 'positive', 'outperform', 'surge']
        negative_words = ['drop', 'fall', 'down', 'loss', 'weak', 'negative', 'miss', 'decline', 'slump']
        txt = text.lower()
        score = 0
        for w in positive_words:
            if w in txt:
                score += 1
        for w in negative_words:
            if w in txt:
                score -= 1
        if score == 0:
            return 0.0
        # scale to [-1,1] but don't exaggerate
        return max(-1.0, min(1.0, score / 5.0))

    # ---------- Google Sheets loading ----------
    def load_headlines_from_sheet(self) -> pd.DataFrame:
        """
        Loads a sheet expected to contain: headline, snippet (both lowercase).
        Also supports optional 'takeaway' and 'date' fields if present.
        If service account missing, attempts public CSV fallback (if GOOGLE_SHEET_ID set).
        """
        try:
            if os.path.exists(self.service_account_file):
                scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
                creds = ServiceAccountCredentials.from_json_keyfile_name(self.service_account_file, scope)
                client = gspread.authorize(creds)
                sheet = client.open(self.google_sheet_name).sheet1
                records = sheet.get_all_records()
                df = pd.DataFrame(records)
            else:
                logger.warning("Service account file not found. Using public CSV fallback.")
                sheet_id = os.getenv("GOOGLE_SHEET_ID", "")
                gid = os.getenv("GOOGLE_SHEET_GID", "0")
                if not sheet_id:
                    logger.error("GOOGLE_SHEET_ID not set and service account file missing.")
                    return pd.DataFrame()
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
                resp = requests.get(csv_url, timeout=10)
                resp.raise_for_status()
                from io import StringIO
                df = pd.read_csv(StringIO(resp.text))

            # normalize columns to lower-case and strip spaces
            df.columns = [c.strip().lower() for c in df.columns]
            # fill optional columns
            if 'headline' not in df.columns and 'headline ' in df.columns:
                df.rename(columns={'headline ': 'headline'}, inplace=True)
            if 'headline' not in df.columns:
                logger.warning("Loaded sheet missing 'headline' column")
                return pd.DataFrame()

            if 'snippet' not in df.columns:
                df['snippet'] = ''
            else:
                df['snippet'] = df['snippet'].fillna('')

            # optional takeaway
            if 'takeaway' not in df.columns:
                df['takeaway'] = ''

            # optional date (try to parse)
            if 'date' in df.columns:
                try:
                    df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
                except Exception:
                    df['date_parsed'] = pd.NaT
            else:
                df['date_parsed'] = pd.NaT

            df = df[['headline', 'snippet', 'takeaway', 'date_parsed']]

            logger.info("Loaded %d headline rows from sheet", len(df))
            return df
        except Exception as e:
            logger.exception("Failed to load headlines from sheet: %s", e)
            return pd.DataFrame()

    # ---------- n8n webhook + polling (unchanged timings) ----------
    def trigger_on_demand_fetch(self, user_query: str, resolved_ticker: Optional[str] = None, max_attempts: int = 1) -> bool:
        """
        Trigger n8n webhook and poll sheet for changes in total row count.
        Behavior & timings preserved (initial 10s wait + poll_for_headlines default).
        """
        ticker_value = resolved_ticker if resolved_ticker else user_query
        payload = {"ticker": ticker_value}
        headers = {"Content-Type": "application/json"}

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info("Triggering n8n webhook (attempt %d) for ticker '%s'", attempt, ticker_value)
                resp = requests.post(self.webhook_url, json=payload, headers=headers, timeout=30)
                if resp.status_code in (200, 202):
                    logger.info("Webhook accepted (status=%d). Waiting 10 seconds before polling...", resp.status_code)
                    time.sleep(10)  # unchanged initial delay
                    return self.poll_for_headlines(timeout=120, interval=5)  # unchanged polling timing
                else:
                    logger.warning("Webhook responded with status %d: %s", resp.status_code, getattr(resp, 'text', ''))
            except Exception as e:
                logger.warning("Webhook attempt %d failed: %s", attempt, e)
            time.sleep(3)

        logger.error("All webhook attempts failed for ticker %s", ticker_value)
        return False

    def poll_for_headlines(self, timeout: int = 120, interval: int = 5) -> bool:
        start_time = time.time()
        initial_count = self._row_count()
        logger.info("Initial total row count: %d", initial_count)
        while time.time() - start_time < timeout:
            time.sleep(interval)
            self.headline_db = self.load_headlines_from_sheet()
            current_count = self._row_count()
            logger.info("Polling... current_count=%d", current_count)
            if current_count != initial_count:
                logger.info("Detected row count change: %d -> %d", initial_count, current_count)
                return True
        logger.warning("Polling timed out after %ds", timeout)
        return False

    def _row_count(self) -> int:
        try:
            if self.headline_db is None or self.headline_db.empty:
                return 0
            return int(len(self.headline_db))
        except Exception:
            return 0

    # ---------- Stock data & features ----------
    def fetch_stock_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        if not isinstance(ticker, str):
            logger.warning("Ticker argument not str; attempting coercion")
            if isinstance(ticker, (list, tuple)) and ticker:
                ticker = str(ticker[0])
            else:
                ticker = str(ticker)

        attempts = 0
        last_error = None
        while attempts < 3:
            try:
                logger.info("yfinance download attempt %d for ticker=%s (start=%s end=%s)", attempts + 1, ticker, start_date, end_date)
                df = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if df is None or df.empty:
                    raise ValueError("No data returned from yfinance")
                df = df.reset_index()
                df.rename(columns={df.columns[0]: 'date'}, inplace=True)
                if 'Close' not in df.columns:
                    if 'Adj Close' in df.columns:
                        df['Close'] = df['Adj Close']
                        logger.warning("'Close' column missing; using 'Adj Close' as Close")
                    elif 'close' in df.columns:
                        df['Close'] = df['close']
                        logger.warning("'Close' column lowercase found; normalizing to 'Close'")
                    else:
                        logger.error("No Close/Adj Close column found in data. Columns: %s", list(df.columns))
                        raise ValueError("Missing Close column in yfinance data")
                # unify date format to string YYYY-MM-DD for downstream expected behavior
                df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                self.data = df
                logger.info("Fetched %d rows for %s via download", len(df), ticker)
                return df
            except Exception as e:
                attempts += 1
                last_error = e
                logger.warning("yfinance download attempt %d failed: %s", attempts, e)
                time.sleep(2)

        logger.error("Primary download failed for %s after %d attempts (last error: %s). Trying Ticker().history fallback.", ticker, attempts, last_error)
        try:
            tkr = yf.Ticker(ticker)
            hist = tkr.history(start=start_date, end=end_date)
            if hist is None or hist.empty:
                raise ValueError("Ticker().history returned empty frame")
            hist = hist.reset_index()
            hist.rename(columns={hist.columns[0]: 'date'}, inplace=True)
            if 'Close' not in hist.columns:
                if 'Adj Close' in hist.columns:
                    hist['Close'] = hist['Adj Close']
                elif 'close' in hist.columns:
                    hist['Close'] = hist['close']
                else:
                    raise ValueError("Fallback history missing Close column")
            hist['date'] = pd.to_datetime(hist['date']).dt.strftime('%Y-%m-%d')
            self.data = hist
            logger.info("Fetched %d rows for %s via fallback history", len(hist), ticker)
            return hist
        except Exception as e2:
            logger.error("Fallback history failed for %s: %s", ticker, e2)
            return pd.DataFrame()

    def build_features(self, df: pd.DataFrame) -> (np.ndarray, np.ndarray, pd.DataFrame):
        try:
            if df is None or df.empty:
                logger.error("Input DataFrame is None or empty")
                return np.array([]), np.array([]), pd.DataFrame()

            if 'Close' not in df.columns:
                logger.error(f"'Close' column missing. Available columns: {list(df.columns)}")
                return np.array([]), np.array([]), pd.DataFrame()

            dff = df.copy()
            dff['close'] = dff['Close'].astype(float)
            dff['return_1d'] = dff['close'].pct_change()
            dff['ma_3'] = dff['close'].rolling(window=3, min_periods=1).mean()
            dff['ma_7'] = dff['close'].rolling(window=7, min_periods=1).mean()
            dff['vol_7'] = dff['return_1d'].rolling(window=7, min_periods=1).std().fillna(0)

            if 'date' in dff.columns:
                dff['day_of_week'] = pd.to_datetime(dff['date']).dt.dayofweek
            elif 'Date' in dff.columns:
                dff['day_of_week'] = pd.to_datetime(dff['Date']).dt.dayofweek
            else:
                logger.warning("No date column found, using default day_of_week=0")
                dff['day_of_week'] = 0

            dff['target_next_close'] = dff['close'].shift(-1)
            dff = dff.dropna(subset=['target_next_close']).reset_index(drop=True)

            if len(dff) == 0:
                logger.error("No valid rows after feature engineering")
                return np.array([]), np.array([]), pd.DataFrame()

            features = dff[['close', 'return_1d', 'ma_3', 'ma_7', 'vol_7', 'day_of_week']].fillna(0).values
            targets = dff['target_next_close'].values.astype(float)

            logger.info(f"Built {len(features)} feature samples")
            return features, targets, dff
        except Exception as e:
            logger.error(f"Error in build_features: {e}")
            return np.array([]), np.array([]), pd.DataFrame()

    # ---------- Model training & evaluation ----------
    def initialize_models(self) -> Dict[str, object]:
        models = {
            'RandomForest': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        try:
            import xgboost as xgb
            models['XGBoost'] = xgb.XGBRegressor(n_estimators=100, random_state=42, verbosity=0)
        except Exception:
            logger.info('XGBoost not available; skipping')
        return models

    def train_baseline_model(self, X: np.ndarray, y: np.ndarray) -> object:
        if len(X) < 10:
            logger.warning("Not enough data to train robust model. Need at least 10 samples.")
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            model.fit(X, y)
            self.model = model
            return model

        models = self.initialize_models()
        best_model = None
        best_r2 = -np.inf

        tscv = TimeSeriesSplit(n_splits=3)
        for name, m in models.items():
            try:
                scores = []
                for train_idx, val_idx in tscv.split(X):
                    X_train_cv, X_val_cv = X[train_idx], X[val_idx]
                    y_train_cv, y_val_cv = y[train_idx], y[val_idx]
                    m.fit(X_train_cv, y_train_cv)
                    preds = m.predict(X_val_cv)
                    scores.append(r2_score(y_val_cv, preds))
                mean_score = np.mean(scores)
                logger.info("Model %s CV mean R2: %.4f", name, mean_score)
                if mean_score > best_r2:
                    best_r2 = mean_score
                    best_model = m
            except Exception as e:
                logger.warning("Model %s failed during CV: %s", name, e)

        if best_model is None:
            logger.warning("No model survived CV; training default RandomForest on full data")
            best_model = RandomForestRegressor(n_estimators=100, random_state=42)
            best_model.fit(X, y)

        best_model.fit(X, y)
        self.model = best_model

        return best_model

    # ---------- Sentiment aggregation with recency weighting ----------
    def _row_recency_weight(self, row_date: Optional[pd.Timestamp], half_life_days: float = 30.0) -> float:
        """
        Exponential decay weight based on difference from now.
        half_life_days controls how fast older rows lose weight.
        If row_date is NaT, returns 1.0 (neutral weight).
        """
        try:
            if pd.isna(row_date):
                return 1.0
            days_old = (pd.Timestamp.now() - row_date).days
            if days_old < 0:
                days_old = 0
            # weight = 2^(-days / half_life)
            weight = math.pow(2.0, -float(days_old) / float(max(1.0, half_life_days)))
            return float(weight)
        except Exception:
            return 1.0

    def get_overall_sentiment(self) -> float:
        """
        Combine 'headline' + 'snippet' + optional 'takeaway' for ALL rows.
        Uses cached predictions where possible, applies recency weighting (if date present),
        and returns a scaled weighted average in [-1, 1].
        """
        if self.headline_db is None or self.headline_db.empty:
            logger.info("Headline DB empty; no sentiment")
            return 0.0
        try:
            df = self.headline_db.copy()
            if 'headline' not in df.columns:
                logger.warning("Headline column missing in sheet")
                return 0.0

            # Prepare texts and recency weights
            texts = []
            weights = []
            for idx, row in df.iterrows():
                headline = str(row.get('headline', '')).strip()
                snippet = str(row.get('snippet', '')).strip()
                takeaway = str(row.get('takeaway', '')).strip() if 'takeaway' in row else ''
                unified = " ".join([x for x in [headline, snippet, takeaway] if x])
                texts.append(unified)

                # Use 'date_parsed' if available; fallback to NaT
                row_date = row.get('date_parsed', pd.NaT) if 'date_parsed' in df.columns else pd.NaT
                w = self._row_recency_weight(row_date)
                weights.append(w)

            if len(texts) == 0:
                return 0.0

            raw_scores = self._predict_sentiment_for_texts(texts)
            # Convert to numpy arrays
            scores = np.array(raw_scores, dtype=float)
            wts = np.array(weights, dtype=float)

            # If all weights are zero for any reason, use uniform weights
            if np.all(wts == 0):
                wts = np.ones_like(wts)

            weighted_avg = float(np.sum(scores * wts) / np.sum(wts))
            simple_mean = float(np.mean(scores))
            count = int(len(scores))

            # Normalize extreme sentiment using tanh (compresses extremes but preserves sign)
            normalized = float(math.tanh(weighted_avg * 1.5))  # 1.5 factor to keep sensitivity

            logger.info("Sentiment: count=%d mean=%.4f weighted=%.4f normalized=%.4f", count, simple_mean, weighted_avg, normalized)
            return normalized
        except Exception as e:
            logger.exception("Sentiment aggregation failed: %s", e)
            return 0.0

    # ---------- Company name -> ticker resolution ----------
    def resolve_ticker(self, query: str) -> str:
        try:
            q_raw = query.strip()
            if not q_raw:
                raise ValueError("Empty company name / ticker provided")

            q_norm = ' '.join(q_raw.lower().split())
            alias_map = {
                'adani power': 'ADANIPOWER.NS',
                'adani powers': 'ADANIPOWER.NS',
                'adani enterprises': 'ADANIENT.NS',
                'adani ports': 'ADANIPORTS.NS',
                'adani total gas': 'ATGL.NS',
                'adani green': 'ADANIGREEN.NS',
                'adani transmission': 'ADANITRANS.NS',
                'reliance industries': 'RELIANCE.NS',
                'tata motors': 'TATAMOTORS.NS',
                'hdfc bank': 'HDFCBANK.NS',
                'apple': 'AAPL',
                'microsoft': 'MSFT',
                'google': 'GOOGL',
                'amazon': 'AMZN',
                'tesla': 'TSLA'
            }

            if q_norm in alias_map:
                ticker = alias_map[q_norm]
                logger.info("Alias map resolved '%s' -> %s", q_raw, ticker)
                return ticker

            if q_raw.upper() == q_raw and len(q_raw) <= 12 and (' ' not in q_raw):
                logger.info("Input looks like ticker; using as-is: %s", q_raw.upper())
                return q_raw.upper()

            try:
                url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(q_raw)}"
                logger.info("Resolving ticker for query '%s' via Yahoo search", q_raw)
                resp = requests.get(url, timeout=8)
                resp.raise_for_status()
                data = resp.json()
                quotes = data.get('quotes', [])
                if not quotes:
                    logger.warning("Yahoo search returned no quotes for '%s'", q_raw)
                    return q_raw.upper()
                top = quotes[0]
                sym = top.get('symbol')
                if sym:
                    logger.info("Resolved '%s' -> %s (source=%s)", q_raw, sym, top.get('exchange', 'unknown'))
                    return sym
                logger.warning("Top quote missing symbol; returning input uppercased")
                return q_raw.upper()
            except requests.exceptions.Timeout:
                logger.error("Yahoo search timed out for '%s'", q_raw)
                return q_raw.upper()
            except requests.exceptions.RequestException as e:
                logger.warning("Ticker resolution request failed for '%s': %s. Returning uppercased input.", q_raw, e)
                return q_raw.upper()
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                logger.warning("Failed to parse Yahoo search response for '%s': %s", q_raw, e)
                return q_raw.upper()
        except ValueError as e:
            logger.error(f"Input validation error in resolve_ticker: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in resolve_ticker: {e}")
            return query.strip().upper() if query and query.strip() else "UNKNOWN"

    # ---------- Final prediction combining baseline ML + sentiment ----------
    def compute_final_prediction(self, ml_pred: float, sentiment: float, recent_volatility: float = 0.0) -> float:
        """
        Improved, bounded sentiment -> price adjustment:
          - sentiment is expected in [-1,1] (we apply tanh earlier)
          - compute an alpha that grows with volatility but is capped
          - use a compressed sentiment value and cap final adjustment to +/- MAX_ADJUST (default 12%)
        """
        try:
            # Base parameters
            BASE_ALPHA = 0.12          # baseline maximum influence scale factor
            VOL_MULTIPLIER = min(3.0, recent_volatility * 10.0)  # amplify with volatility (capped)
            alpha = BASE_ALPHA * (1.0 + VOL_MULTIPLIER)          # provisional alpha
            # Keep alpha within sensible bounds
            alpha = max(0.02, min(0.30, alpha))

            # compress sentiment so extreme values don't explode adjustment
            sent_comp = math.tanh(sentiment * 1.8)  # still in (-1,1), more sensitive mid-range

            # preliminary adjustment (signed)
            preliminary_adj = alpha * sent_comp

            # cap the *relative* adjustment to avoid huge swings (e.g., +/-12% max)
            MAX_ADJUST = 0.12
            adj = max(-MAX_ADJUST, min(MAX_ADJUST, preliminary_adj))

            final = float(ml_pred * (1.0 + adj))

            logger.info("ML_pred=%.4f sentiment=%.4f comp=%.4f alpha=%.4f preliminary=%.4f capped_adj=%.4f final=%.4f",
                        ml_pred, sentiment, sent_comp, alpha, preliminary_adj, adj, final)
            return final
        except Exception as e:
            logger.exception("compute_final_prediction failed: %s", e)
            return float(ml_pred)

    # ---------- End-to-end flow (unchanged public behavior) ----------
    def run_full_workflow(self, company_or_ticker: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[float]:
        """
        End-to-end flow preserved as before: resolve ticker, trigger n8n, fetch prices, train model,
        compute sentiment and return final predicted price.
        """
        try:
            if not company_or_ticker or not isinstance(company_or_ticker, str):
                raise ValueError("company_or_ticker must be a non-empty string")

            company_or_ticker = company_or_ticker.strip()
            if not company_or_ticker:
                raise ValueError("company_or_ticker cannot be empty after stripping")

            if end_date is None or (isinstance(end_date, str) and end_date.lower() == 'today'):
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError as e:
                logger.error(f"Invalid date format: {e}")
                raise ValueError(f"Dates must be in YYYY-MM-DD format: {e}")

            logger.info("Starting full workflow for input '%s' (%s to %s)", company_or_ticker, start_date, end_date)

            # Step 1: Resolve ticker
            resolved = self.resolve_ticker(company_or_ticker)
            if not resolved or resolved == "UNKNOWN":
                raise ValueError(f"Could not resolve ticker for '{company_or_ticker}'")

            # Step 2: Trigger n8n (non-blocking if fails)
            try:
                self.trigger_on_demand_fetch(company_or_ticker, resolved_ticker=resolved)
            except Exception as e:
                logger.warning(f"Webhook trigger failed, continuing with existing data: {e}")

            # Step 3: Fetch historical prices
            hist = self.fetch_stock_data(resolved, start_date, end_date)
            if hist is None or hist.empty:
                raise ValueError(f"No historical data available for {resolved}")

            # Step 4: Feature engineering
            X, y, df_features = self.build_features(hist)
            if X is None or len(X) == 0:
                raise ValueError("Feature engineering produced no valid samples")
            if len(X) < 10:
                logger.warning(f"Only {len(X)} samples available, model may be unreliable")

            # Step 5: Train
            model = self.train_baseline_model(X, y)
            if model is None:
                raise ValueError("Model training returned None")

            # Step 6: Predict baseline next close
            latest_row = df_features.iloc[-1:]
            baseline_features = latest_row[['close', 'return_1d', 'ma_3', 'ma_7', 'vol_7', 'day_of_week']].values
            ml_pred = float(model.predict(baseline_features)[0])
            logger.info("Baseline ML predicted next close: %.4f", ml_pred)

            # Step 7: Compute sentiment
            try:
                self.headline_db = self.load_headlines_from_sheet()
                sentiment = self.get_overall_sentiment()
            except Exception as e:
                logger.warning(f"Sentiment computation failed, using neutral: {e}")
                sentiment = 0.0

            # Step 8: Final prediction
            try:
                recent_volatility = float(df_features['vol_7'].iloc[-1]) if 'vol_7' in df_features.columns else 0.0
                final_price = self.compute_final_prediction(ml_pred, sentiment, recent_volatility)

                if final_price <= 0:
                    logger.warning(f"Predicted price is non-positive ({final_price}), returning ML baseline")
                    final_price = ml_pred

                logger.info("Final predicted price for '%s' (ticker=%s): %.4f", company_or_ticker, resolved, final_price)
                return final_price
            except Exception as e:
                logger.error(f"Final prediction computation failed: {e}")
                return ml_pred if 'ml_pred' in locals() else None

        except ValueError as e:
            logger.error(f"Validation error in workflow: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in run_full_workflow: {e}")
            return None

if __name__ == "__main__":
    print("StockSentryML - improved backend (sentiment caching + stable weighting)")
    company = input("Enter company name or ticker (e.g., 'Apple' or 'AAPL'): ").strip()
    if not company:
        company = 'AAPL'
        print("Defaulting to AAPL")

    start = input("Start date (YYYY-MM-DD) [default=6 months ago]: ").strip()
    end = input("End date (YYYY-MM-DD) [default=today]: ").strip()

    ss = StockSentryML()
    try:
        final = ss.run_full_workflow(company, start_date=start if start else None, end_date=end if end else None)
        if final is not None:
            print(f"Final predicted next-day price for {company}: ${final:.2f}")
        else:
            print("Prediction failed. Check logs for details.")
    except Exception as exc:
        logger.exception("Fatal error running workflow: %s", exc)
