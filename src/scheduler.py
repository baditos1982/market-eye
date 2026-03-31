"""
Programador de tareas para verificación periódica de alarmas
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Clase para programar tareas periódicas de verificación"""
    
    def __init__(self, check_interval_minutes: int = 5):
        """
        Inicializar el scheduler
        
        Args:
            check_interval_minutes: Intervalo entre verificaciones (minutos)
        """
        self.check_interval = check_interval_minutes
        self.scheduler = AsyncIOScheduler()
        self.tasks = []
    
    def add_job(self, func, job_id: str = None, **kwargs):
        """
        Agregar una tarea programada
        
        Args:
            func: Función a ejecutar
            job_id: ID único para la tarea
            **kwargs: Argumentos adicionales para APScheduler
        """
        trigger = IntervalTrigger(minutes=self.check_interval)
        
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            **kwargs
        )
        logger.info(f"Tarea agregada: {job_id or func.__name__} (cada {self.check_interval} min)")
    
    def start(self):
        """Iniciar el scheduler"""
        try:
            self.scheduler.start()
            logger.info(f"Scheduler iniciado - Verificando cada {self.check_interval} minutos")
        except Exception as e:
            logger.error(f"Error iniciando scheduler: {e}")
            raise
    
    def shutdown(self, wait: bool = True):
        """
        Detener el scheduler
        
        Args:
            wait: Esperar a que las tareas actuales terminen
        """
        try:
            self.scheduler.shutdown(wait=wait)
            logger.info("Scheduler detenido")
        except Exception as e:
            logger.error(f"Error deteniendo scheduler: {e}")
    
    def pause_job(self, job_id: str):
        """Pausar una tarea"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Tarea pausada: {job_id}")
        except Exception as e:
            logger.error(f"Error pausando tarea {job_id}: {e}")
    
    def resume_job(self, job_id: str):
        """Reanudar una tarea"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Tarea reanudada: {job_id}")
        except Exception as e:
            logger.error(f"Error reanudando tarea {job_id}: {e}")
    
    def remove_job(self, job_id: str):
        """Eliminar una tarea"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Tarea eliminada: {job_id}")
        except Exception as e:
            logger.error(f"Error eliminando tarea {job_id}: {e}")
    
    def get_jobs(self) -> list:
        """Obtener lista de tareas programadas"""
        return self.scheduler.get_jobs()
    
    def modify_job_interval(self, job_id: str, new_interval_minutes: int):
        """
        Modificar intervalo de una tarea
        
        Args:
            job_id: ID de la tarea
            new_interval_minutes: Nuevo intervalo en minutos
        """
        try:
            trigger = IntervalTrigger(minutes=new_interval_minutes)
            self.scheduler.modify_job(job_id, trigger=trigger)
            logger.info(f"Intervalo modificado para {job_id}: {new_interval_minutes} min")
        except Exception as e:
            logger.error(f"Error modificando intervalo de {job_id}: {e}")


async def create_verification_task(data_fetcher, indicator_calc, alarm_engine, 
                                   telegram_notifier, symbols: list):
    """
    Crear tarea de verificación de alarmas
    
    Esta función es un factory que retorna la función async a programar
    
    Args:
        data_fetcher: Instancia de DataFetcher
        indicator_calc: Instancia de IndicatorCalculator
        alarm_engine: Instancia de AlarmEngine
        telegram_notifier: Instancia de TelegramNotifier
        symbols: Lista de símbolos a monitorear
        
    Returns:
        Función async para verificar alarmas
    """
    
    async def verify_alarms():
        """Función principal de verificación (optimizada)"""
        logger.info(f"Iniciando verificación de alarmas - {datetime.now()}")
        
        try:
            # 1. Obtener todos los precios de una vez (optimizado)
            all_market_data = data_fetcher.get_multiple_prices(symbols)
            
            if not all_market_data:
                logger.warning("No se pudieron obtener datos de ningún símbolo")
                return
            
            # 2. Obtener datos históricos en batch por símbolo
            historical_cache = {}
            for symbol in symbols:
                if symbol in all_market_data:
                    historical_df = data_fetcher.get_historical_data(symbol, period="3mo", interval="1d")
                    if not historical_df.empty:
                        historical_cache[symbol] = historical_df
                        logger.info(f"{symbol}: ${all_market_data[symbol]['price']:.2f}")
                    else:
                        logger.warning(f"No hay datos históricos para {symbol}")
            
            # 3. Procesar cada símbolo
            for symbol in symbols:
                if symbol not in all_market_data or symbol not in historical_cache:
                    continue
                
                market_data = all_market_data[symbol]
                historical_df = historical_cache[symbol]
                
                try:
                    # Calcular indicadores
                    indicators = indicator_calc.calculate_all_indicators(symbol, historical_df)
                    
                    # Log de indicadores principales
                    if indicators.get('rsi_14'):
                        logger.debug(f"{symbol} RSI(14): {indicators['rsi_14']:.2f}")
                    if indicators.get('macd'):
                        logger.debug(f"{symbol} MACD: {indicators['macd']:.4f}")
                    
                    # Evaluar alarmas
                    triggered = alarm_engine.evaluate_all_alarms(symbol, market_data, indicators)
                    
                    # Enviar notificaciones
                    for alarm in triggered:
                        message = None
                        
                        if alarm.alarm_type == 'price':
                            message = telegram_notifier.format_price_alert(
                                symbol=symbol,
                                condition=alarm.condition,
                                current_value=market_data['price'],
                                threshold=alarm.threshold
                            )
                        
                        elif alarm.alarm_type == 'rsi':
                            rsi_value = indicators.get('rsi_14', 0)
                            condition_text = "Sobrecompra" if rsi_value > 70 else "Sobreventa"
                            message = telegram_notifier.format_indicator_alert(
                                symbol=symbol,
                                indicator_name="RSI",
                                indicator_value=rsi_value,
                                condition=condition_text
                            )
                        
                        elif alarm.alarm_type == 'volume':
                            current_vol = market_data.get('volume', 0)
                            avg_vol = indicators.get('volume_avg_20', 0)
                            if avg_vol > 0:
                                pct_increase = ((current_vol - avg_vol) / avg_vol) * 100
                                message = telegram_notifier.format_volume_alert(
                                    symbol=symbol,
                                    current_volume=current_vol,
                                    avg_volume=int(avg_vol),
                                    percent_increase=pct_increase
                                )
                        
                        else:
                            # Mensaje genérico
                            message = f"""
🔔 <b>ALERTA ACTIVADA</b> 🔔

<b>Símbolo:</b> {symbol}
<b>Tipo:</b> {alarm.alarm_type}
<b>Condición:</b> {alarm.condition}

<i>Hora: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</i>
"""
                        
                        if message:
                            telegram_notifier.send_alert_sync(message)
                    
                    if triggered:
                        logger.info(f"{len(triggered)} alarma(s) disparada(s) para {symbol}")
                
                except Exception as e:
                    logger.error(f"Error procesando {symbol}: {e}", exc_info=False)
        
        except Exception as e:
            logger.error(f"Error en verificación: {e}", exc_info=True)
        
        logger.info(f"Verificación completada - {datetime.now()}")
    
    return verify_alarms
