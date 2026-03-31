# Memoria del Proyecto - Warren Indicator

## Objetivo
Sistema de alarmas para inversión que monitorea activos financieros y envía notificaciones vía Telegram cuando se cumplen condiciones específicas.

## Arquitectura

### Estructura de Directorios
```
/workspace/
├── config/              # Archivos de configuración
│   └── settings.json    # Configuración principal (API keys, símbolos, etc.)
├── data/                # Datos históricos y caché
├── logs/                # Logs del sistema
├── src/                 # Código fuente
│   ├── __init__.py
│   ├── main.py          # Punto de entrada principal
│   ├── telegram_bot.py  # Integración con Telegram
│   ├── data_fetcher.py  # Obtención de datos financieros
│   ├── indicators.py    # Cálculo de indicadores técnicos
│   ├── alarm_engine.py  # Motor de evaluación de alarmas
│   └── scheduler.py     # Programador de tareas
├── memoria.md           # Este archivo
└── README.md            # Documentación pública
└── requirements.txt     # Dependencias Python
```

## Stack Tecnológico

### Lenguaje
- Python 3.8+

### Librerías Principales
- `yfinance`: Obtención de datos financieros (gratis, Yahoo Finance)
- `pandas`: Manipulación de datos
- `numpy`: Cálculos numéricos
- `pandas-ta` o `ta-lib`: Indicadores técnicos
- `python-telegram-bot`: Integración con Telegram
- `APScheduler`: Programación de tareas periódicas
- `sqlite3`: Base de datos ligera (incluida en Python)

### API Externa
- **Yahoo Finance** (vía yfinance): Datos de precios, volumen, históricos
- **Telegram Bot API**: Notificaciones push

## Funcionalidades Implementadas

### 1. Tipos de Alarmas
- **Precio**: 
  - Cruce de umbral superior/inferior
  - Variación porcentual diaria
- **Indicadores Técnicos**:
  - RSI (Relative Strength Index): Sobrecompra (>70) / Sobreventa (<30)
  - Medias Móviles: Cruces SMA/EMA (corto/largo plazo)
  - MACD: Cruces de línea de señal
  - Bandas de Bollinger: Toque o ruptura de bandas
- **Volumen**:
  - Picos de volumen (% sobre promedio)
- **Condiciones Compuestas**:
  - Múltiples condiciones con operadores AND/OR

### 2. Sistema de Notificaciones (Telegram)
- Bot personalizado para enviar alertas
- Formato de mensajes claro con:
  - Símbolo del activo
  - Condición activada
  - Valor actual
  - Hora de la alerta
  - Enlace a gráfico (opcional)
- Soporte para múltiples usuarios (configurable)

### 3. Scheduler
- Ejecución periódica configurable (ej: cada 5 min, 15 min, 1 hora)
- Verificación asíncrona de todas las alarmas activas
- Manejo de rate limiting de APIs

### 4. Persistencia
- SQLite para guardar:
  - Alarmas configuradas
  - Historial de alertas enviadas
  - Estado del sistema
- Logs detallados en archivos rotativos

## Configuración

### Variables de Entorno / Config
- `TELEGRAM_BOT_TOKEN`: Token del bot de Telegram
- `TELEGRAM_CHAT_ID`: ID del chat para recibir alertas
- `CHECK_INTERVAL`: Intervalo de verificación (minutos)
- `SYMBOLS`: Lista de símbolos a monitorear (ej: AAPL, GOOGL, TSLA)

### Crear Bot de Telegram
1. Abrir Telegram y buscar @BotFather
2. Enviar `/newbot`
3. Seguir instrucciones para nombrar el bot
4. Guardar el token proporcionado
5. Iniciar conversación con el bot
6. Obtener Chat ID usando @userinfobot o similar

## Flujo de Ejecución

1. **Inicio**: Cargar configuración e inicializar componentes
2. **Scheduler**: Despertar cada N minutos
3. **Fetch Data**: Obtener precios actuales de todos los símbolos
4. **Calculate Indicators**: Calcular indicadores técnicos necesarios
5. **Evaluate Alarms**: Evaluar todas las alarmas activas
6. **Send Notifications**: Enviar alertas vía Telegram si corresponde
7. **Log & Save**: Registrar actividad y guardar estado
8. **Sleep**: Esperar hasta próximo ciclo

## Comandos de Usuario (Telegram)
- `/start`: Iniciar bot, mostrar menú
- `/status`: Ver estado del sistema
- `/alarms`: Listar alarmas activas
- `/add <símbolo> <tipo> <condición>`: Crear alarma
- `/delete <id>`: Eliminar alarma
- `/help`: Mostrar ayuda

## Próximas Mejoras (Roadmap)
- [x] Dashboard web simple (Flask/FastAPI)
- [x] Despliegue en Render
- [ ] Backtesting de estrategias
- [ ] Soporte para criptomonedas (Binance API)
- [ ] Alertas por email como fallback
- [ ] Condiciones personalizadas con expresiones
- [ ] Gráficos adjuntos en alertas
- [ ] Soporte multi-usuario con autenticación

## Despliegue en Render

### Configuración Automática
El proyecto incluye un archivo `render.yaml` que configura automáticamente el despliegue en Render:

```yaml
services:
  - type: web
    name: warren-indicator
    env: python
    region: frankfurt
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn src.web_server:app --bind 0.0.0.0:$PORT & python src/main.py
```

### Pasos para Desplegar

1. **Conectar Repositorio**:
   - En Render, ve a "New +" → "Web Service"
   - Conecta tu repositorio de GitHub
   - Render detectará automáticamente el archivo `render.yaml`

2. **Configurar Variables de Entorno**:
   En el dashboard de Render, añade las siguientes variables:
   - `TELEGRAM_BOT_TOKEN`: Tu token de bot de Telegram
   - `TELEGRAM_CHAT_ID`: Tu chat ID de Telegram
   
3. **Desplegar**:
   - Render construirá e iniciará automáticamente el servicio
   - El servicio estará disponible en `https://warren-indicator.onrender.com`

4. **Verificar Estado**:
   - Visita `/health` para verificar que el servicio está funcionando
   - Visita `/stats` para ver estadísticas del sistema
   - Visita `/` para ver el estado general

### Endpoints Web Disponibles

Una vez desplegado, tendrás acceso a:

- `GET /`: Página de inicio con estado del sistema
  ```json
  {
    "status": "running",
    "service": "Warren Indicator",
    "last_check": "2024-01-15T10:30:00",
    "alerts_sent": 5,
    "active_alarms": 3
  }
  ```

- `GET /health`: Endpoint de salud para monitoreo
  ```json
  {"status": "healthy"}
  ```

- `GET /stats`: Estadísticas detalladas
  ```json
  {
    "service": "Warren Indicator",
    "version": "1.0.0",
    "last_check": "2024-01-15T10:30:00",
    "total_alerts": 5,
    "active_alarms": 3
  }
  ```

### Consideraciones para Render Free Tier

- **Sleep Mode**: El plan gratuito de Render pone los servicios en sleep después de 15 minutos de inactividad. 
- **Solución**: El servidor web mantiene el proceso activo y el health check previene el sleep.
- **Disco Persistente**: Se configura un disco de 1GB para guardar datos de alarmas y logs.
- **Región**: Configurado en Frankfurt (eu-central) para menor latencia en Europa.

### Comandos Útiles

```bash
# Ver logs en tiempo real desde Render CLI
render logs -w warren-indicator

# Reiniciar servicio
render service restart warren-indicator

# Ver variables de entorno
render env list -w warren-indicator
```

## Notas Importantes
- Rate limiting de Yahoo Finance: ~2000 consultas/día gratis
- Recomendado usar intervalos >= 5 minutos para evitar bloqueos
- Para producción, considerar APIs premium (Alpha Vantage, Polygon.io)
- Mantener tokens y claves sensibles fuera del repositorio (usar .env)
- **Render Free Tier**: El servicio puede tardar 30-50 segundos en despertar si entra en sleep mode

## Comandos de Ejecución
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export TELEGRAM_BOT_TOKEN="tu_token"
export TELEGRAM_CHAT_ID="tu_chat_id"

# Ejecutar sistema
python src/main.py
```

---
*Última actualización: Fecha de creación del proyecto*
