import asyncio

result_queue = {}

def get_result_queue(room_id: str):
    if room_id not in result_queue:
        result_queue[room_id] = asyncio.Queue()
    return result_queue[room_id]
