"""
Módulo para cálculo de indicadores técnicos
"""

import pandas as pd
import talib
import numpy as np
import logging

logger = logging.getLogger(__name__)


class IndicatorCalculator:
    """Clase para calcular indicadores técnicos"""
    
    def __init__(self):
        pass
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calcular RSI (Relative Strength Index)
        
        Args:
            df: DataFrame con datos históricos (debe tener columna 'Close')
            period: Período para el cálculo (default: 14)
            
        Returns:
            Valor actual del RSI
        """
        try:
            if df.empty or len(df) < period + 1:
                return None
            
            rsi = talib.RSI(df['Close'].values, timeperiod=period)
            return float(rsi[-1])
        except Exception as e:
            logger.error(f"Error calculando RSI: {e}")
            return None
    
    def calculate_sma(self, df: pd.DataFrame, period: int = 20) -> float:
        """
        Calcular Simple Moving Average (SMA)
        
        Args:
            df: DataFrame con datos históricos
            period: Período de la media móvil
            
        Returns:
            Valor actual de la SMA
        """
        try:
            if df.empty or len(df) < period:
                return None
            
            sma = talib.SMA(df['Close'].values, timeperiod=period)
            return float(sma[-1])
        except Exception as e:
            logger.error(f"Error calculando SMA: {e}")
            return None
    
    def calculate_ema(self, df: pd.DataFrame, period: int = 20) -> float:
        """
        Calcular Exponential Moving Average (EMA)
        
        Args:
            df: DataFrame con datos históricos
            period: Período de la media móvil exponencial
            
        Returns:
            Valor actual de la EMA
        """
        try:
            if df.empty or len(df) < period:
                return None
            
            ema = talib.EMA(df['Close'].values, timeperiod=period)
            return float(ema[-1])
        except Exception as e:
            logger.error(f"Error calculando EMA: {e}")
            return None
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
        """
        Calcular MACD
        
        Args:
            df: DataFrame con datos históricos
            fast: Período rápido (default: 12)
            slow: Período lento (default: 26)
            signal: Período de señal (default: 9)
            
        Returns:
            Diccionario con valores MACD, Signal y Histogram
        """
        try:
            if df.empty or len(df) < slow + signal:
                return None
            
            macd, signal_line, histogram = talib.MACD(
                df['Close'].values, 
                fastperiod=fast, 
                slowperiod=slow, 
                signalperiod=signal
            )
            
            return {
                'macd': float(macd[-1]),
                'signal': float(signal_line[-1]),
                'histogram': float(histogram[-1])
            }
        except Exception as e:
            logger.error(f"Error calculando MACD: {e}")
            return None
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> dict:
        """
        Calcular Bandas de Bollinger
        
        Args:
            df: DataFrame con datos históricos
            period: Período (default: 20)
            std_dev: Desviación estándar (default: 2.0)
            
        Returns:
            Diccionario con upper, middle y lower bands
        """
        try:
            if df.empty or len(df) < period:
                return None
            
            upper, middle, lower = talib.BBANDS(
                df['Close'].values, 
                timeperiod=period, 
                nbdevup=std_dev, 
                nbdevdn=std_dev
            )
            
            return {
                'upper': float(upper[-1]),
                'middle': float(middle[-1]),
                'lower': float(lower[-1])
            }
        except Exception as e:
            logger.error(f"Error calculando Bandas de Bollinger: {e}")
            return None
    
    def calculate_volume_average(self, df: pd.DataFrame, period: int = 20) -> float:
        """
        Calcular promedio de volumen
        
        Args:
            df: DataFrame con datos históricos
            period: Período para el promedio
            
        Returns:
            Promedio de volumen
        """
        try:
            if df.empty or len(df) < period:
                return None
            
            return float(df['Volume'].tail(period).mean())
        except Exception as e:
            logger.error(f"Error calculando promedio de volumen: {e}")
            return None
    
    def calculate_all_indicators(self, symbol: str, historical_df: pd.DataFrame) -> dict:
        """
        Calcular todos los indicadores para un símbolo
        
        Args:
            symbol: Símbolo del activo
            historical_df: DataFrame con datos históricos
            
        Returns:
            Diccionario con todos los indicadores calculados
        """
        indicators = {}
        
        # RSI
        indicators['rsi_14'] = self.calculate_rsi(historical_df, 14)
        indicators['rsi_7'] = self.calculate_rsi(historical_df, 7)  # RSI más sensible
        
        # Medias Móviles
        indicators['sma_20'] = self.calculate_sma(historical_df, 20)
        indicators['sma_50'] = self.calculate_sma(historical_df, 50)
        indicators['sma_200'] = self.calculate_sma(historical_df, 200)
        indicators['ema_12'] = self.calculate_ema(historical_df, 12)
        indicators['ema_26'] = self.calculate_ema(historical_df, 26)
        
        # MACD
        macd = self.calculate_macd(historical_df)
        if macd:
            indicators['macd'] = macd['macd']
            indicators['macd_signal'] = macd['signal']
            indicators['macd_histogram'] = macd['histogram']
        
        # Bandas de Bollinger
        bbands = self.calculate_bollinger_bands(historical_df)
        if bbands:
            indicators['bb_upper'] = bbands['upper']
            indicators['bb_middle'] = bbands['middle']
            indicators['bb_lower'] = bbands['lower']
        
        # Volumen
        indicators['volume_avg_20'] = self.calculate_volume_average(historical_df, 20)
        
        return indicators
