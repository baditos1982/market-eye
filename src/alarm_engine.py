"""
Motor de evaluación de alarmas
Evalúa condiciones y activa notificaciones
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class Alarm:
    """Clase que representa una alarma configurada"""
    id: str
    symbol: str
    alarm_type: str  # 'price', 'rsi', 'macd', 'sma_cross', 'volume', etc.
    condition: str   # Descripción legible de la condición
    threshold: float
    comparison: str  # '>', '<', '>=', '<=', '==', 'cross_above', 'cross_below'
    enabled: bool = True
    created_at: datetime = None
    last_triggered: datetime = None
    trigger_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convertir a diccionario para serialización"""
        d = asdict(self)
        d['created_at'] = self.created_at.isoformat() if self.created_at else None
        d['last_triggered'] = self.last_triggered.isoformat() if self.last_triggered else None
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Alarm':
        """Crear instancia desde diccionario"""
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data.get('last_triggered'):
            data['last_triggered'] = datetime.fromisoformat(data['last_triggered'])
        return cls(**data)


class AlarmEngine:
    """Motor para evaluar y gestionar alarmas"""
    
    def __init__(self):
        self.alarms: Dict[str, Alarm] = {}
        self.trigger_cooldown_minutes = 15  # Evitar múltiples triggers en corto tiempo
    
    def add_alarm(self, alarm: Alarm) -> bool:
        """
        Agregar una alarma
        
        Args:
            alarm: Objeto Alarm a agregar
            
        Returns:
            True si se agregó correctamente
        """
        if alarm.id in self.alarms:
            logger.warning(f"La alarma {alarm.id} ya existe, actualizando...")
        
        self.alarms[alarm.id] = alarm
        logger.info(f"Alarma agregada: {alarm.id} - {alarm.symbol} - {alarm.alarm_type}")
        return True
    
    def remove_alarm(self, alarm_id: str) -> bool:
        """
        Eliminar una alarma
        
        Args:
            alarm_id: ID de la alarma a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        if alarm_id in self.alarms:
            del self.alarms[alarm_id]
            logger.info(f"Alarma eliminada: {alarm_id}")
            return True
        logger.warning(f"Alarma no encontrada: {alarm_id}")
        return False
    
    def enable_alarm(self, alarm_id: str) -> bool:
        """Activar una alarma"""
        if alarm_id in self.alarms:
            self.alarms[alarm_id].enabled = True
            logger.info(f"Alarma activada: {alarm_id}")
            return True
        return False
    
    def disable_alarm(self, alarm_id: str) -> bool:
        """Desactivar una alarma"""
        if alarm_id in self.alarms:
            self.alarms[alarm_id].enabled = False
            logger.info(f"Alarma desactivada: {alarm_id}")
            return True
        return False
    
    def get_active_alarms(self) -> List[Alarm]:
        """Obtener todas las alarmas activas"""
        return [a for a in self.alarms.values() if a.enabled]
    
    def get_all_alarms(self) -> List[Alarm]:
        """Obtener todas las alarmas"""
        return list(self.alarms.values())
    
    def evaluate_price_alarm(self, alarm: Alarm, current_price: float) -> bool:
        """
        Evaluar alarma de precio
        
        Args:
            alarm: Alarma a evaluar
            current_price: Precio actual
            
        Returns:
            True si la condición se cumple
        """
        threshold = alarm.threshold
        comparison = alarm.comparison
        
        if comparison == '>':
            return current_price > threshold
        elif comparison == '>=':
            return current_price >= threshold
        elif comparison == '<':
            return current_price < threshold
        elif comparison == '<=':
            return current_price <= threshold
        elif comparison == '==':
            return abs(current_price - threshold) < 0.01  # Margen pequeño
        
        return False
    
    def evaluate_rsi_alarm(self, alarm: Alarm, rsi_value: float) -> bool:
        """
        Evaluar alarma de RSI
        
        Args:
            alarm: Alarma a evaluar
            rsi_value: Valor actual del RSI
            
        Returns:
            True si la condición se cumple
        """
        threshold = alarm.threshold
        comparison = alarm.comparison
        
        if comparison == '>':
            return rsi_value > threshold
        elif comparison == '>=':
            return rsi_value >= threshold
        elif comparison == '<':
            return rsi_value < threshold
        elif comparison == '<=':
            return rsi_value <= threshold
        
        return False
    
    def evaluate_macd_alarm(self, alarm: Alarm, macd_value: float, signal_value: float) -> bool:
        """
        Evaluar alarma de cruce MACD
        
        Args:
            alarm: Alarma a evaluar
            macd_value: Valor actual de MACD
            signal_value: Valor actual de la línea de señal
            
        Returns:
            True si hay cruce
        """
        comparison = alarm.comparison
        
        if comparison == 'cross_above':
            # MACD cruza por encima de Signal
            return macd_value > signal_value
        elif comparison == 'cross_below':
            # MACD cruza por debajo de Signal
            return macd_value < signal_value
        
        return False
    
    def evaluate_sma_cross_alarm(self, alarm: Alarm, sma_short: float, sma_long: float) -> bool:
        """
        Evaluar alarma de cruce de medias móviles
        
        Args:
            alarm: Alarma a evaluar
            sma_short: Media móvil corta
            sma_long: Media móvil larga
            
        Returns:
            True si hay cruce
        """
        comparison = alarm.comparison
        
        if comparison == 'cross_above':
            # SMA corta cruza por encima de SMA larga (señal alcista)
            return sma_short > sma_long
        elif comparison == 'cross_below':
            # SMA corta cruza por debajo de SMA larga (señal bajista)
            return sma_short < sma_long
        
        return False
    
    def evaluate_bollinger_alarm(self, alarm: Alarm, current_price: float, 
                                 bb_upper: float, bb_lower: float) -> bool:
        """
        Evaluar alarma de Bandas de Bollinger
        
        Args:
            alarm: Alarma a evaluar
            current_price: Precio actual
            bb_upper: Banda superior
            bb_lower: Banda inferior
            
        Returns:
            True si toca o rompe bandas
        """
        comparison = alarm.comparison
        
        if comparison == 'touch_upper':
            return current_price >= bb_upper
        elif comparison == 'touch_lower':
            return current_price <= bb_lower
        elif comparison == 'break_upper':
            return current_price > bb_upper
        elif comparison == 'break_lower':
            return current_price < bb_lower
        
        return False
    
    def evaluate_volume_alarm(self, alarm: Alarm, current_volume: int, avg_volume: int) -> bool:
        """
        Evaluar alarma de volumen
        
        Args:
            alarm: Alarma a evaluar
            current_volume: Volumen actual
            avg_volume: Volumen promedio
            
        Returns:
            True si el volumen supera el umbral
        """
        threshold = alarm.threshold  # Porcentaje sobre promedio
        percent_increase = ((current_volume - avg_volume) / avg_volume) * 100
        
        return percent_increase >= threshold
    
    def can_trigger(self, alarm: Alarm) -> bool:
        """
        Verificar si la alarma puede dispararse (cooldown)
        
        Args:
            alarm: Alarma a verificar
            
        Returns:
            True si puede dispararse
        """
        if not alarm.enabled:
            return False
        
        if alarm.last_triggered is None:
            return True
        
        time_since_last = (datetime.now() - alarm.last_triggered).total_seconds() / 60
        return time_since_last >= self.trigger_cooldown_minutes
    
    def evaluate_alarm(self, alarm: Alarm, market_data: dict, indicators: dict) -> bool:
        """
        Evaluar una alarma con los datos actuales del mercado
        
        Args:
            alarm: Alarma a evaluar
            market_data: Datos de mercado (precio, volumen, etc.)
            indicators: Indicadores técnicos calculados
            
        Returns:
            True si la alarma se dispara
        """
        if not self.can_trigger(alarm):
            return False
        
        triggered = False
        
        try:
            if alarm.alarm_type == 'price':
                triggered = self.evaluate_price_alarm(alarm, market_data.get('price', 0))
            
            elif alarm.alarm_type == 'rsi':
                rsi_key = f'rsi_{int(alarm.threshold)}' if alarm.threshold in [7, 14, 21] else 'rsi_14'
                rsi_value = indicators.get(rsi_key, indicators.get('rsi_14'))
                if rsi_value is not None:
                    triggered = self.evaluate_rsi_alarm(alarm, rsi_value)
            
            elif alarm.alarm_type == 'macd':
                macd = indicators.get('macd')
                signal = indicators.get('macd_signal')
                if macd is not None and signal is not None:
                    triggered = self.evaluate_macd_alarm(alarm, macd, signal)
            
            elif alarm.alarm_type == 'sma_cross':
                sma_short = indicators.get('sma_20')
                sma_long = indicators.get('sma_50')
                if sma_short is not None and sma_long is not None:
                    triggered = self.evaluate_sma_cross_alarm(alarm, sma_short, sma_long)
            
            elif alarm.alarm_type == 'bollinger':
                price = market_data.get('price', 0)
                bb_upper = indicators.get('bb_upper')
                bb_lower = indicators.get('bb_lower')
                if bb_upper and bb_lower:
                    triggered = self.evaluate_bollinger_alarm(alarm, price, bb_upper, bb_lower)
            
            elif alarm.alarm_type == 'volume':
                current_vol = market_data.get('volume', 0)
                avg_vol = indicators.get('volume_avg_20')
                if avg_vol and avg_vol > 0:
                    triggered = self.evaluate_volume_alarm(alarm, current_vol, avg_vol)
            
            if triggered:
                alarm.last_triggered = datetime.now()
                alarm.trigger_count += 1
                logger.info(f"Alarma disparada: {alarm.id} - {alarm.symbol}")
            
        except Exception as e:
            logger.error(f"Error evaluando alarma {alarm.id}: {e}")
        
        return triggered
    
    def evaluate_all_alarms(self, symbol: str, market_data: dict, indicators: dict) -> List[Alarm]:
        """
        Evaluar todas las alarmas activas para un símbolo
        
        Args:
            symbol: Símbolo del activo
            market_data: Datos de mercado
            indicators: Indicadores técnicos
            
        Returns:
            Lista de alarmas disparadas
        """
        triggered_alarms = []
        
        for alarm in self.get_active_alarms():
            if alarm.symbol == symbol:
                if self.evaluate_alarm(alarm, market_data, indicators):
                    triggered_alarms.append(alarm)
        
        return triggered_alarms
    
    def get_status(self) -> dict:
        """Obtener estado del motor de alarmas"""
        active = len(self.get_active_alarms())
        total = len(self.alarms)
        
        return {
            'total_alarms': total,
            'active_alarms': active,
            'inactive_alarms': total - active,
            'alarms': [a.to_dict() for a in self.alarms.values()]
        }
    
    def save_to_file(self, filepath: str):
        """Guardar alarmas en archivo JSON"""
        try:
            data = {aid: a.to_dict() for aid, a in self.alarms.items()}
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Alarmas guardadas en {filepath}")
        except Exception as e:
            logger.error(f"Error guardando alarmas: {e}")
    
    def load_from_file(self, filepath: str):
        """Cargar alarmas desde archivo JSON"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            for aid, alarm_data in data.items():
                alarm = Alarm.from_dict(alarm_data)
                self.alarms[aid] = alarm
            
            logger.info(f"Alarmas cargadas desde {filepath}")
        except FileNotFoundError:
            logger.info("No hay archivo de alarmas previo")
        except Exception as e:
            logger.error(f"Error cargando alarmas: {e}")
