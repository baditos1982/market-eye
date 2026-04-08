"""
Módulo para obtener datos financieros de Yahoo Finance
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """Clase para obtener datos financieros de múltiples fuentes"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=5)  # Aumentado a 5 minutos para reducir llamadas API
    
    def get_current_price(self, symbol: str) -> dict:
        """
        Obtener precio actual de un símbolo
        
        Args:
            symbol: Símbolo del activo (ej: AAPL, TSLA)
            
        Returns:
            Diccionario con información del precio
        """
        try:
            ticker = yf.Ticker(symbol)
            # Obtener información rápida
            info = ticker.info
            
            # Obtener datos históricos recientes para el precio actual
            hist = ticker.history(period='1d')
            
            if hist.empty:
                logger.warning(f"No hay datos disponibles para {symbol}")
                return None
            
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Open'].iloc[0] if len(hist) > 0 else current_price
            
            return {
                'symbol': symbol,
                'price': float(current_price),
                'open': float(hist['Open'].iloc[-1]),
                'high': float(hist['High'].iloc[-1]),
                'low': float(hist['Low'].iloc[-1]),
                'volume': int(hist['Volume'].iloc[-1]),
                'previous_close': float(prev_close),
                'change': float(current_price - prev_close),
                'change_percent': float(((current_price - prev_close) / prev_close) * 100) if prev_close else 0,
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error obteniendo precio para {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        Obtener datos históricos para cálculo de indicadores
        
        Args:
            symbol: Símbolo del activo
            period: Período de datos (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Intervalo de tiempo (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            DataFrame con datos históricos
        """
        # Verificar caché primero
        cache_key = f"{symbol}_{period}_{interval}"
        now = datetime.now()
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (now - timestamp) < self.cache_duration:
                return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No hay datos históricos para {symbol}")
                return pd.DataFrame()
            
            # Actualizar caché
            self.cache[cache_key] = (df, now)
            return df
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos para {symbol}: {e}")
            return pd.DataFrame()
    
    def get_multiple_prices(self, symbols: list) -> dict:
        """
        Obtener precios de múltiples símbolos en paralelo (optimizado)
        
        Args:
            symbols: Lista de símbolos
            
        Returns:
            Diccionario con precios por símbolo
        """
        results = {}
        
        # Usar yfinance download para obtener múltiples símbolos eficientemente
        try:
            # Descargar datos de todos los símbolos de una vez
            import yfinance as yf
            tickers_data = yf.download(symbols, period='1d', group_by='ticker')
            
            if not tickers_data.empty:
                for symbol in symbols:
                    try:
                        # Manejar estructura de datos multi-nivel de yfinance
                        if len(tickers_data.columns.levels) == 2:
                            symbol_data = tickers_data[symbol]
                        else:
                            symbol_data = tickers_data
                        
                        if symbol in symbol_data.columns or len(tickers_data) > 0:
                            current_price = symbol_data['Close'].iloc[-1] if hasattr(symbol_data, 'iloc') else None
                            if current_price is not None:
                                results[symbol] = {
                                    'symbol': symbol,
                                    'price': float(current_price),
                                    'timestamp': datetime.now()
                                }
                    except Exception:
                        pass
            
            # Fallback individual para símbolos fallidos
            for symbol in symbols:
                if symbol not in results:
                    price_data = self.get_current_price(symbol)
                    if price_data:
                        results[symbol] = price_data
                    else:
                        logger.warning(f"No se pudo obtener precio para {symbol}")
        
        except Exception as e:
            logger.error(f"Error obteniendo múltiples precios: {e}")
            # Fallback a método individual
            for symbol in symbols:
                if symbol not in results:
                    price_data = self.get_current_price(symbol)
                    if price_data:
                        results[symbol] = price_data
        
        return results
    
    def get_market_status(self) -> dict:
        """
        Obtener estado del mercado
        
        Returns:
            Diccionario con estado de mercados principales
        """
        # Yahoo Finance no proporciona estado directo del mercado
        # Podemos inferirlo verificando si hay volumen en índices principales
        try:
            spy = yf.Ticker("SPY")
            spy_data = spy.fast_info
            
            return {
                'market_open': True,  # Simplificado
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error obteniendo estado del mercado: {e}")
            return {'market_open': False, 'timestamp': datetime.now()}
