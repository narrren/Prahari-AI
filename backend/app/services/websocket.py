import socketio

# Create a single AsyncServer instance
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
sio_app = socketio.ASGIApp(sio)

async def notify_alert(alert_data):
    """
    Emit critical alert to all connected dashboards.
    """
    try:
        await sio.emit('new_alert', alert_data)
        print(f"WS EMIT: {alert_data['type']} - {alert_data['message']}")
    except Exception as e:
        print(f"WS Emit Error: {e}")

async def broadcast_telemetry(telemetry_data):
    """
    Broadcast live tourist position to the map.
    """
    try:
        await sio.emit('telemetry_update', telemetry_data)
    except Exception as e:
        print(f"WS Telemetry Emit Error: {e}")
