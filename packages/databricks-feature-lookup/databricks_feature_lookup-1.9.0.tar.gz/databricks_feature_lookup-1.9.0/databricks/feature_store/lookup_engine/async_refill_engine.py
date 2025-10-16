import logging
import time

import gevent
from gevent.lock import Semaphore
from gevent.queue import Empty, Queue
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from databricks.feature_store.utils.logging_utils import get_logger

_logger = get_logger(__name__, log_level=logging.INFO)
BASE_URL = "postgresql+psycopg2://"


class AsyncRefillEngine:
    """
    A PostgreSQL engine that maintains pool of connections and actively refills
    the pool when connections expire.

    Unlike the standard SQLAlchemy engine, the connection pool in this engine
    usually does not create new connections in the critical query path. Instead,
    when aquiring a connection,it skip and discard expired connections from the
    head of the queue to get the next available connection as soon as possible.
    Then it refills the pool with new connections asynchronously.

    The engine also starts a background greenlet that keeps acquiring and
    releasing connections to keep the pool warm even when there is no active
    query.

    Gevent compatible: this engine works in a gevent environment. If not, the
    async operations won't start.

    Usage:
        Use `acquire` to get a connection from the pool and `release` to return
        it back to the pool. Calling close on the connection object will not
        return it back to the pool.
    """

    def __init__(
        self,
        pool_size,
        pool_recycle,
        pool_warming_interval=5,
        pool_timeout=2,
        pool_init_gap=2,
        creator=None,
    ):
        """
        Initialize an AsyncRefillEngine.

        :param pool_size: The size of the pool.
        :param pool_recycle: The time in seconds before the connection expires.
        :param pool_warming_interval: The interval in seconds at which the pool
          warming thread runs. In the pool warming thread, we recycle connections
          3x of pool_warming_interval before the expiration. So this number
          should be much smaller than 1/3 of pool_recycle to keep the connections
          alive longer. But an extremely small interval can also cause too many
          requests to the connection pool.
        :param pool_timeout: The timeout in seconds for getting a connection from
          the pool.
        :param pool_init_gap: The gap in seconds between initializing connections.
          This is needed to avoid connections expiring at the same time. Also to
          avoid too many requests to hit the auth rate limit for creating
          connections during initialization.
        :param creator: The creator function to use to create the connection.
        """
        self._engine = create_engine(BASE_URL, creator=creator, poolclass=NullPool)
        self._pool = Queue(maxsize=pool_size)
        self._lock = Semaphore()
        self._pool_size = pool_size
        self._pool_recycle = pool_recycle
        self._pool_timeout = pool_timeout
        self._pool_warming_interval = pool_warming_interval
        # How long before the connection expires should the pool warming thread
        # recycle the connection. this makes sure there is at least one connection
        # in the pool can last until the next warming cycle.
        #
        # Choosing 3x because in production there are at most 2 connections checked
        # out at the same time. Keeping one extra connection for edge cases. This might
        # needs tuning when we support parallel queries for multiple tables.
        self._pre_recycle_time = pool_warming_interval * 3
        # Number of connections currently checked out
        self._in_use = 0

        # Warm-up pool
        while self._pool.qsize() < self._pool_size:
            try:
                conn = None
                conn = self._create_conn()
                self._pool.put(conn)
            except Exception as e:
                _logger.warning(f"[pool] Retrying to init connection because: {e}")
                if conn:
                    try:
                        conn.close()
                    except Exception:
                        pass
            # Initialize the connections with gaps to avoid expiring them all
            # together.
            gevent.sleep(pool_init_gap)
        if pool_warming_interval > 0:
            gevent.spawn(self._pool_warming_thread)

    def _create_conn(self):
        conn = self._engine.connect()
        conn.starttime = time.time()
        return conn

    def _pool_warming_thread(self):
        while True:
            try:
                conn = self.acquire(is_warming=True)
                self.release(conn)
            except Exception as e:
                _logger.warning(f"[pool] Error warming up connection: {e}")
            gevent.sleep(self._pool_warming_interval)

    def _is_valid(self, conn, is_warming=False):
        # Validate the connection based on if the check is for a connection warming request.
        # For connection warming request, we recycle the connections sooner than normal to make sure
        # a real request doesn't stuck on a stale connection.
        start = getattr(conn, "starttime", None)
        if start and self._pool_recycle > -1:
            recycle_time = (
                self._pool_recycle - self._pre_recycle_time
                if is_warming
                else self._pool_recycle
            )
            if time.time() - start > recycle_time:
                return False
        return True

    def acquire(self, is_warming=False):
        if self._pool.qsize() == 0:
            if not is_warming:
                # If on critical path (is_warming==False), creating a new connection is causing latency.
                # This is avoided as much as possible through pool warming, but we have to recover by
                # creating a new connection if it happens.
                _logger.warning(
                    f"[pool] connection pool empty with {self.checkedout()} connections checked out"
                )
            conn = self._create_conn()
        else:
            # When there are connections in the pool, try to get one from the pool.
            # If it's invalid, dispose it and try again recursively.
            try:
                conn = self._pool.get(timeout=self._pool_timeout)
            except Empty:
                _logger.error(
                    f"[pool] timeout getting connection. checked-out {self.checkedout()}s"
                )
                raise TimeoutError(f"No available connection in {self._pool_timeout}s")

            if not self._is_valid(conn, is_warming):
                try:
                    conn.close()
                except Exception:
                    pass

                # If pool nearly empty, replace immediately
                if self._pool.qsize() == 0:
                    conn = self._create_conn()
                else:
                    gevent.spawn(self._refill)
                    # Recursively try again.
                    return self.acquire(is_warming=is_warming)

        with self._lock:
            self._in_use += 1
        return conn

    def _put_in_queue(self, conn):
        try:
            self._pool.put_nowait(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    def release(self, conn):
        with self._lock:
            self._in_use -= 1
        self._put_in_queue(conn)

    def _refill(self):
        try:
            conn = self._create_conn()
            self._put_in_queue(conn)
        except Exception as e:
            _logger.error(f"[pool] async refill failed: {e}")

    # Observability
    # How many connections are in the pool.
    def checkedin(self):
        return self._pool.qsize()

    # How many connections are checked out and being used.
    def checkedout(self):
        with self._lock:
            return self._in_use
