from django.conf import settings

from db.redis.base import BaseRedisDb
from polyaxon.settings import RedisPools


class RedisHeartBeat(BaseRedisDb):
    """
    RedisHeartBeat provides a db to store experiment/job heartbeats.
    """
    KEY_EXPERIMENT = 'heartbeat.experiment:{}'
    KEY_JOB = 'heartbeat.job:{}'
    KEY_BUILD = 'heartbeat.build:{}'

    # A Run should report under this value, otherwise it could be considered zombie
    TTL_HEARTBEAT = settings.TTL_HEARTBEAT
    REDIS_POOL = RedisPools.HEARTBEAT

    def __init__(self, experiment=None, job=None, build=None):
        if len([1 for i in [experiment, job, build] if i]) != 1:
            raise ValueError('RedisHeartBeat expects an experiment, build or a job.')

        self.__dict__['_is_experiment'] = False
        self.__dict__['_is_job'] = False
        self.__dict__['_is_build'] = False
        if experiment:
            self.__dict__['_is_experiment'] = True
        if job:
            self.__dict__['_is_job'] = True
        if build:
            self.__dict__['_is_build'] = True
        self.__dict__['key'] = experiment or job or build
        self.__dict__['_red'] = self._get_redis()

    def __getattr__(self, key):
        value = self.get_value()

        try:
            return value
        except KeyError as e:
            raise AttributeError(e)

    def is_alive(self):
        if not self.redis_key:
            return False

        value = self._red.get(self.redis_key)
        if not value:
            return False

        return True

    def ping(self):
        self._red.setex(name=self.redis_key, value=1, time=self.TTL_HEARTBEAT)

    @property
    def redis_key(self):
        if self._is_experiment:
            return self.KEY_EXPERIMENT.format(self.key)
        if self._is_job:
            return self.KEY_JOB.format(self.key)
        if self._is_build:
            return self.KEY_BUILD.format(self.key)
        raise KeyError('Wrong RedisHeartBeat key')

    def clear(self):
        if not self.redis_key:
            return

        self._red.delete(self.redis_key)

    @classmethod
    def experiment_ping(cls, experiment_id):
        heart_beat = RedisHeartBeat(experiment=experiment_id)
        heart_beat.ping()

    @classmethod
    def job_ping(cls, job_id):
        heart_beat = RedisHeartBeat(job=job_id)
        heart_beat.ping()

    @classmethod
    def build_ping(cls, build_id):
        heart_beat = RedisHeartBeat(build=build_id)
        heart_beat.ping()

    @classmethod
    def experiment_is_alive(cls, experiment_id):
        heart_beat = RedisHeartBeat(experiment=experiment_id)
        return heart_beat.is_alive()

    @classmethod
    def job_is_alive(cls, job_id):
        heart_beat = RedisHeartBeat(job=job_id)
        return heart_beat.is_alive()

    @classmethod
    def build_is_alive(cls, build_id):
        heart_beat = RedisHeartBeat(build=build_id)
        return heart_beat.is_alive()
