# cabinet/utils/redis_lock.py
from django_redis import get_redis_connection
import uuid

class RedisLock:
    def __init__(self, lock_name, expire_time=10):
        self.redis_conn = get_redis_connection("default")
        self.lock_name = f"cabinet:lock:{lock_name}"
        self.expire_time = expire_time
        self.identifier = str(uuid.uuid4())
        self.acquired = False

    def acquire(self):
        """Attempt to acquire a lock"""
        acquired = self.redis_conn.set(
            self.lock_name, self.identifier, ex=self.expire_time, nx=True
        )
        self.acquired = acquired
        return acquired

    def release(self):
        """Release the lock if it's owned by us"""
        if self.acquired:
            # Execute a Lua script to release the lock only if it's owned by us
            script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('del', KEYS[1])
            else
                return 0
            end
            """
            self.redis_conn.eval(script, 1, self.lock_name, self.identifier)
            self.acquired = False
            return True
        return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()