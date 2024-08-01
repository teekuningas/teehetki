import socketio
from aiohttp import web
import aiohttp_cors

# Create a new AsyncServer instance
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins=["http://localhost:3000"])

# Create a new Aiohttp web application
app = web.Application()
sio.attach(app)

# Define the connect event
@sio.event
async def connect(sid, environ):
    print('Client connected:', sid)  # Debug
    await sio.emit('message', 'Connected to server', room=sid)

# Define the disconnect event
@sio.event
async def disconnect(sid):
    print('Client disconnected:', sid)  # Debug

# Add a simple HTTP route for testing
app.router.add_get('/', lambda request: web.Response(text="WebSocket Audio Server"))

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*"
    )
})

for route in app.router.routes():
    if route.resource.canonical == '/':
        cors.add(route)

if __name__ == '__main__':
    # Run the web application on port 5000
    web.run_app(app, port=5000)
