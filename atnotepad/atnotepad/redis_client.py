import redis

redis_instance = redis.StrictRedis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

def set_notebook_content(notebook_id, content):
    redis_instance.set(f"notebook:{notebook_id}:content", content)

def get_notebook_content(notebook_id):
    return redis_instance.get(f"notebook:{notebook_id}:content")

def delete_notebook_content(notebook_id):
    redis_instance.delete(f"notebook:{notebook_id}:content")
