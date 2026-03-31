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
        self.cache_duration = timedelta(minutes=1)
    
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
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                logger.warning(f"No hay datos históricos para {symbol}")
                return pd.DataFrame()
            
            return df
        except Exception as e:
            logger.error(f"Error obteniendo datos históricos para {symbol}: {e}")
            return pd.DataFrame()
    
    def get_multiple_prices(self, symbols: list) -> dict:
        """
        Obtener precios de múltiples símbolos
        
        Args:
            symbols: Lista de símbolos
            
        Returns:
            Diccionario con precios por símbolo
        """
        results = {}
        for symbol in symbols:
            price_data = self.get_current_price(symbol)
            if price_data:
                results[symbol] = price_data
            else:
                logger.warning(f"No se pudo obtener precio para {symbol}")
        
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
