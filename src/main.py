#!/usr/bin/env python3
"""
Warren Indicator - Sistema de Alarmas para Inversión
Punto de entrada principal

Ejecuta el sistema de monitoreo y envío de alertas vía Telegram
"""

import os
import sys
import json
import logging
import signal
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent))

from data_fetcher import DataFetcher
from indicators import IndicatorCalculator
from alarm_engine import AlarmEngine, Alarm
from telegram_bot import TelegramNotifier
from scheduler import TaskScheduler, create_verification_task
from web_server import app, update_stats

# Cargar variables de entorno
load_dotenv()

# Configurar logging
def setup_logging(log_file: str = "logs/warren_indicator.log", level: str = "INFO"):
    """Configurar sistema de logging"""
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configurar logging básico para Render
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Intentar agregar file handler si es posible
    try:
        if log_dir and os.path.exists(log_dir):
            file_handler = logging.FileHandler(log_file)
            logging.getLogger().addHandler(file_handler)
    except Exception:
        pass  # Ignorar errores de escritura en Render
    
    return logging.getLogger(__name__)


def load_config(config_path: str = "config/settings.json") -> dict:
    """Cargar configuración desde archivo JSON"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Sobrescribir con variables de entorno si existen
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            config['telegram']['bot_token'] = os.getenv("TELEGRAM_BOT_TOKEN")
        if os.getenv("TELEGRAM_CHAT_ID"):
            config['telegram']['chat_id'] = os.getenv("TELEGRAM_CHAT_ID")
        if os.getenv("CHECK_INTERVAL"):
            config['scheduler']['check_interval_minutes'] = int(os.getenv("CHECK_INTERVAL"))
        if os.getenv("SYMBOLS"):
            config['symbols'] = os.getenv("SYMBOLS").split(",")
        
        return config
    except FileNotFoundError:
        logger.warning(f"Archivo de configuración no encontrado: {config_path}")
        return {}
    except Exception as e:
        logger.error(f"Error cargando configuración: {e}")
        return {}


def create_sample_alarms(alarm_engine: AlarmEngine):
    """Crear alarmas de ejemplo para demostración"""
    sample_alarms = [
        Alarm(
            id="rsi_overbought_aapl",
            symbol="AAPL",
            alarm_type="rsi",
            condition="RSI > 70 (Sobrecompra)",
            threshold=70,
            comparison=">"
        ),
        Alarm(
            id="rsi_oversold_aapl",
            symbol="AAPL",
            alarm_type="rsi",
            condition="RSI < 30 (Sobreventa)",
            threshold=30,
            comparison="<"
        ),
        Alarm(
            id="price_target_tsla",
            symbol="TSLA",
            alarm_type="price",
            condition="Precio supera $250",
            threshold=250.0,
            comparison=">"
        ),
        Alarm(
            id="volume_spike_googl",
            symbol="GOOGL",
            alarm_type="volume",
            condition="Volumen +50% sobre promedio",
            threshold=50.0,
            comparison=">"
        ),
    ]
    
    for alarm in sample_alarms:
        alarm_engine.add_alarm(alarm)
    
    logger.info(f"{len(sample_alarms)} alarmas de ejemplo creadas")


async def get_system_status(alarm_engine, scheduler, data_fetcher):
    """Obtener estado del sistema para comando /status"""
    status = alarm_engine.get_status()
    jobs = scheduler.get_jobs()
    
    status_text = f"""
<b>Estado del Sistema Warren Indicator</b>

📊 <b>Alarmas:</b>
• Total: {status['total_alarms']}
• Activas: {status['active_alarms']}
• Inactivas: {status['inactive_alarms']}

⏰ <b>Scheduler:</b>
• Tareas programadas: {len(jobs)}
• Intervalo: {scheduler.check_interval} minutos

✅ <b>Estado:</b> Operativo
<i>Última actualización: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</i>
"""
    return status_text


def main():
    """Función principal"""
    global logger
    
    # Setup logging
    logger = setup_logging()
    
    # Crear directorios necesarios para Render
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("WARREN INDICATOR - Sistema de Alarmas")
    logger.info("=" * 60)
    
    # Cargar configuración
    config = load_config()
    if not config:
        logger.error("No se pudo cargar la configuración. Saliendo...")
        sys.exit(1)
    
    logger.info("Configuración cargada correctamente")
    
    # Validar configuración de Telegram
    bot_token = config.get('telegram', {}).get('bot_token')
    chat_id = config.get('telegram', {}).get('chat_id')
    
    if not bot_token or not chat_id:
        logger.warning("⚠️  TOKEN o CHAT_ID de Telegram no configurados")
        logger.warning("Las notificaciones no se enviarán hasta que los configures")
        logger.warning("Consulta memoria.md para instrucciones de configuración")
    
    # Inicializar componentes
    logger.info("Inicializando componentes...")
    
    data_fetcher = DataFetcher()
    indicator_calc = IndicatorCalculator()
    alarm_engine = AlarmEngine()
    telegram_notifier = TelegramNotifier(bot_token, chat_id)
    
    # Cargar alarmas guardadas
    alarms_file = "data/alarms.json"
    if os.path.exists(alarms_file):
        alarm_engine.load_from_file(alarms_file)
    else:
        # Crear alarmas de ejemplo
        create_sample_alarms(alarm_engine)
        alarm_engine.save_to_file(alarms_file)
    
    # Configurar scheduler
    check_interval = config.get('scheduler', {}).get('check_interval_minutes', 5)
    scheduler = TaskScheduler(check_interval_minutes=check_interval)
    symbols = config.get('symbols', ['AAPL', 'GOOGL', 'TSLA'])
    
    # Crear tarea de verificación
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    verify_task = loop.run_until_complete(
        create_verification_task(
            data_fetcher, 
            indicator_calc, 
            alarm_engine, 
            telegram_notifier, 
            symbols
        )
    )
    
    # Configurar callback para /status
    telegram_notifier.set_alarm_callback(
        lambda: get_system_status(alarm_engine, scheduler, data_fetcher)
    )
    
    # Agregar tarea al scheduler
    scheduler.add_job(verify_task, job_id="alarm_verification")
    
    # Manejo de señales para shutdown limpio
    def signal_handler(sig, frame):
        logger.info("\nRecibida señal de terminación...")
        logger.info("Guardando estado...")
        alarm_engine.save_to_file(alarms_file)
        scheduler.shutdown(wait=True)
        logger.info("Sistema detenido correctamente")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar scheduler
    logger.info("Iniciando scheduler...")
    scheduler.start()
    
    # Ejecutar primera verificación inmediata
    logger.info("Ejecutando primera verificación...")
    loop.run_until_complete(verify_task())
    
    # Mantener el programa corriendo
    logger.info("Sistema en ejecución. Presiona Ctrl+C para detener.")
    logger.info(f"Monitoreando símbolos: {', '.join(symbols)}")
    logger.info(f"Intervalo de verificación: {check_interval} minutos")
    
    # Iniciar servidor web en un thread separado para Render
    import threading
    from flask import Flask
    
    def run_web_server():
        """Ejecutar servidor web Flask para health checks"""
        port = int(os.environ.get('PORT', 8000))
        app.run(host='0.0.0.0', port=port, debug=False)
    
    # Iniciar servidor web solo si no está en modo de desarrollo local
    if os.environ.get('PORT'):
        web_thread = threading.Thread(target=run_web_server, daemon=True)
        web_thread.start()
        logger.info(f"Servidor web iniciado en puerto {os.environ.get('PORT')}")
    
    try:
        # Loop principal
        while True:
            loop.run_until_complete(asyncio.sleep(60))
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        logger.info("Guardando estado antes de salir...")
        alarm_engine.save_to_file(alarms_file)
        scheduler.shutdown(wait=True)
        loop.close()
        logger.info("¡Hasta luego!")


if __name__ == "__main__":
    main()
