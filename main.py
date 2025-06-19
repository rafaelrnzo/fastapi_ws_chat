import socketio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Store nicknames by sid
connected_users = {}

# FastAPI app
fastapi_app = FastAPI()

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTML Page
html = """
<!DOCTYPE html>
<html>
<head>
    <title>Socket.IO Chat</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        #messages { border: 1px solid #ccc; height: 300px; overflow-y: scroll; list-style: none; padding: 10px; }
        #messages li { margin-bottom: 5px; }
    </style>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
</head>
<body>
    <h1>Chat</h1>
    <form onsubmit="sendMessage(event)">
        <input id="itemId" placeholder="Room" value="room1">
        <input id="nickname" placeholder="Nickname" value="Anonymous">
        <input id="token" value="test-token" hidden>
        <button type="button" onclick="connect()">Connect</button><br>
        <input id="messageText" placeholder="Type a message...">
        <button>Send</button>
    </form>
    <ul id="messages"></ul>
    <script>
        let socket = null;
        let roomId = null;
        let nickname = null;

        function connect() {
            roomId = document.getElementById("itemId").value;
            nickname = document.getElementById("nickname").value;
            const token = document.getElementById("token").value;

            socket = io("http://" + location.host, {
                query: { token }
            });

            socket.on("connect", () => {
                log("✅ Connected");
                socket.emit("join", { room: roomId, nickname: nickname });
            });

            socket.on("chat_message", msg => {
                log(msg);
            });

            socket.on("disconnect", () => {
                log("❌ Disconnected");
            });
        }

        function sendMessage(e) {
            e.preventDefault();
            const text = document.getElementById("messageText").value;
            if (socket && socket.connected) {
                socket.emit("chat_message", { room: roomId, message: text });
                document.getElementById("messageText").value = "";
            }
        }

        function log(msg) {
            const li = document.createElement("li");
            li.textContent = msg;
            document.getElementById("messages").appendChild(li);
        }
    </script>
</body>
</html>
"""

@fastapi_app.get("/")
async def index():
    return HTMLResponse(html)

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

@sio.event
async def connect(sid, environ, auth):
    print(f"✅ Connected: {sid}")

@sio.event
async def disconnect(sid):
    nickname = connected_users.pop(sid, "Unknown")
    print(f"❌ Disconnected: {sid} ({nickname})")

@sio.event
async def join(sid, data):
    room = data.get("room")
    nickname = data.get("nickname", "Anonymous")
    connected_users[sid] = nickname
    await sio.enter_room(sid, room)
    await sio.emit("chat_message", f"🔔 {nickname} joined {room}", room=room)

@sio.event
async def chat_message(sid, data):
    room = data.get("room")
    message = data.get("message")
    nickname = connected_users.get(sid, "Anonymous")
    await sio.emit("chat_message", f"{nickname}: {message}", room=room)
