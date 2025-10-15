from functools import lru_cache

from faker import Faker


class ObjectMother:
    @classmethod
    @lru_cache(maxsize=1)
    def _faker(cls) -> Faker:
        return Faker(use_weighting=False)
