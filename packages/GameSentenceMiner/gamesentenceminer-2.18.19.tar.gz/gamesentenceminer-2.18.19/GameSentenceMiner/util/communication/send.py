import json

from GameSentenceMiner.util.communication.websocket import websocket, Message

async def send_restart_signal():
    if websocket:
        await websocket.send(json.dumps(Message(function="restart").to_json()))