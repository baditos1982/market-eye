"""
Módulo para integración con Telegram Bot
"""

import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Clase para enviar notificaciones y manejar comandos de Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Inicializar el bot de Telegram
        
        Args:
            bot_token: Token del bot obtenido de BotFather
            chat_id: ID del chat donde enviar alertas
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = None
        self.application = None
        self.alarm_callback = None
        
        if bot_token and chat_id:
            self._initialize_bot()
    
    def _initialize_bot(self):
        """Inicializar el bot de Telegram"""
        try:
            self.bot = Bot(token=self.bot_token)
            logger.info("Bot de Telegram inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando bot de Telegram: {e}")
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Enviar mensaje al chat configurado
        
        Args:
            message: Mensaje a enviar
            parse_mode: Modo de parseo (HTML, Markdown, etc.)
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        if not self.bot:
            logger.warning("Bot no inicializado, no se puede enviar mensaje")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            logger.info(f"Mensaje enviado a Telegram: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje a Telegram: {e}")
            return False
    
    def send_alert_sync(self, message: str) -> bool:
        """
        Enviar alerta de forma síncrona (wrapper para código no async)
        
        Args:
            message: Mensaje de la alerta
            
        Returns:
            True si se envió correctamente
        """
        if not self.bot:
            return False
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message(message))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error enviando alerta síncrona: {e}")
            return False
    
    def format_price_alert(self, symbol: str, condition: str, current_value: float, 
                          threshold: float = None, timestamp: datetime = None) -> str:
        """
        Formatear mensaje de alerta de precio
        
        Args:
            symbol: Símbolo del activo
            condition: Descripción de la condición activada
            current_value: Valor actual
            threshold: Valor umbral (opcional)
            timestamp: Fecha y hora de la alerta
            
        Returns:
            Mensaje formateado para Telegram
        """
        ts = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        emoji = "🔔"
        if "sube" in condition.lower() or "supera" in condition.lower():
            emoji = "📈"
        elif "baja" in condition.lower() or "cae" in condition.lower():
            emoji = "📉"
        
        message = f"""
{emoji} <b>ALERTA DE PRECIO</b> {emoji}

<b>Símbolo:</b> {symbol}
<b>Condición:</b> {condition}
<b>Valor Actual:</b> ${current_value:.2f}
"""
        if threshold:
            message += f"<b>Umbral:</b> ${threshold:.2f}\n"
        
        message += f"\n<i>Hora: {ts}</i>"
        
        return message
    
    def format_indicator_alert(self, symbol: str, indicator_name: str, 
                               indicator_value: float, condition: str,
                               timestamp: datetime = None) -> str:
        """
        Formatear mensaje de alerta de indicador técnico
        
        Args:
            symbol: Símbolo del activo
            indicator_name: Nombre del indicador (RSI, MACD, etc.)
            indicator_value: Valor del indicador
            condition: Descripción de la condición
            timestamp: Fecha y hora
            
        Returns:
            Mensaje formateado para Telegram
        """
        ts = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        emoji = "📊"
        if "sobrecompra" in condition.lower():
            emoji = "⚠️"
        elif "sobreventa" in condition.lower():
            emoji = "💰"
        
        message = f"""
{emoji} <b>ALERTA TÉCNICA</b> {emoji}

<b>Símbolo:</b> {symbol}
<b>Indicador:</b> {indicator_name}
<b>Valor:</b> {indicator_value:.2f}
<b>Condición:</b> {condition}

<i>Hora: {ts}</i>
"""
        
        return message
    
    def format_volume_alert(self, symbol: str, current_volume: int, 
                           avg_volume: int, percent_increase: float,
                           timestamp: datetime = None) -> str:
        """
        Formatear mensaje de alerta de volumen
        
        Args:
            symbol: Símbolo del activo
            current_volume: Volumen actual
            avg_volume: Volumen promedio
            percent_increase: Porcentaje de incremento
            timestamp: Fecha y hora
            
        Returns:
            Mensaje formateado para Telegram
        """
        ts = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""
📢 <b>ALERTA DE VOLUMEN</b> 📢

<b>Símbolo:</b> {symbol}
<b>Volumen Actual:</b> {current_volume:,}
<b>Volumen Promedio:</b> {avg_volume:,}
<b>Incremento:</b> +{percent_increase:.1f}%

<i>Hora: {ts}</i>
"""
        
        return message
    
    # Handlers para comandos de Telegram
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar comando /start"""
        await update.message.reply_text(
            "👋 ¡Hola! Soy Warren Indicator Bot.\n\n"
            "Puedo ayudarte a monitorear tus inversiones y enviarte alertas.\n\n"
            "Comandos disponibles:\n"
            "/status - Ver estado del sistema\n"
            "/help - Mostrar ayuda\n\n"
            "Las alertas se enviarán automáticamente cuando se activen las condiciones configuradas."
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar comando /status"""
        if self.alarm_callback:
            status = await self.alarm_callback()
            await update.message.reply_text(status)
        else:
            await update.message.reply_text("Sistema en funcionamiento. No hay alarmas activas configuradas.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar comando /help"""
        help_text = """
<b>Ayuda de Warren Indicator Bot</b>

Este bot te envía alertas automáticas sobre:
• Cruces de precio
• Indicadores técnicos (RSI, MACD, Medias Móviles)
• Picos de volumen

<b>Configuración:</b>
Las alarmas se configuran en el archivo config/settings.json o mediante la API del sistema.

<b>Comandos:</b>
/start - Iniciar el bot
/status - Ver estado del sistema
/help - Esta ayuda

Para más información, consulta la documentación en memoria.md
"""
        await update.message.reply_text(help_text, parse_mode="HTML")
    
    def set_alarm_callback(self, callback):
        """
        Establecer callback para obtener estado de alarmas
        
        Args:
            callback: Función asíncrona que retorna el estado
        """
        self.alarm_callback = callback
    
    def setup_command_handlers(self, application: Application):
        """
        Configurar handlers para comandos
        
        Args:
            application: Aplicación de python-telegram-bot
        """
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(CommandHandler("help", self.help_command))
    
    async def run_bot(self):
        """Ejecutar el bot en modo polling (para desarrollo)"""
        if not self.bot_token:
            logger.warning("No hay token de Telegram configurado")
            return
        
        try:
            application = Application.builder().token(self.bot_token).build()
            self.setup_command_handlers(application)
            self.set_alarm_callback(lambda: self.get_status())
            
            logger.info("Iniciando bot de Telegram en modo polling...")
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Error ejecutando bot de Telegram: {e}")
    
    def get_status(self) -> str:
        """Obtener estado básico del sistema"""
        return "✅ Sistema operativo\n🤖 Bot de Telegram conectado"
