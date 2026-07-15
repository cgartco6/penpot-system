import redis, json, os, subprocess
from orchestrator import plan_task

r = redis.Redis(host='penpot-redis', port=6379, decode_responses=True)

while True:
    task = r.brpop('task_queue', timeout=5)
    if task:
        _, data = task
        data = json.loads(data)
        if data['type'] == 'build':
            subprocess.run(data['command'], shell=True)
        elif data['type'] == 'plan':
            result = plan_task(data['prompt'])
            r.lpush('result_queue', json.dumps({"id": data['id'], "result": result}))
