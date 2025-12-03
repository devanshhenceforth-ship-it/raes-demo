import asyncio

job_queues = {}  
yolo_queues = {}  
def get_job_queue(room_id: str):
    if room_id not in job_queues:
        job_queues[room_id] = asyncio.Queue()
    return job_queues[room_id]

def get_yolo_queue(room_id: str):
    if room_id not in yolo_queues:
        yolo_queues[room_id] = asyncio.Queue()
    return yolo_queues[room_id]