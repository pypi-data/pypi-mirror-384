"""custom initialization and factory examples."""

from fastalloc import Pool, PoolBuilder


class ConfiguredObject:
    """object with configuration."""

    def __init__(self, config_value, mode="default"):
        self.config_value = config_value
        self.mode = mode
        self.data = []


def example_custom_factory():
    """use custom factory function."""
    print("=== Custom Factory ===\n")

    # factory that creates pre-configured objects
    def factory():
        return ConfiguredObject(config_value=42, mode="optimized")

    pool = Pool(ConfiguredObject, capacity=10, factory=factory)

    obj = pool.get()
    print(f"Object config: {obj.config_value}, mode: {obj.mode}")
    pool.release(obj)
    print()


def example_builder_factory():
    """use builder with factory."""
    print("=== Builder with Factory ===\n")

    def custom_factory():
        obj = ConfiguredObject(config_value=99, mode="advanced")
        obj.data = [1, 2, 3]  # pre-populate
        return obj

    pool = (
        PoolBuilder()
        .type(ConfiguredObject)
        .capacity(20)
        .factory(custom_factory)
        .pre_initialize(True)
        .enable_statistics(True)
        .build()
    )

    obj = pool.get()
    print(f"Pre-populated data: {obj.data}")
    print(f"Available objects: {pool.available()}")
    pool.release(obj)
    print()


def example_lazy_vs_eager():
    """compare lazy and eager initialization."""
    print("=== Lazy vs Eager Initialization ===\n")

    # lazy: objects created on demand
    lazy_pool = Pool(ConfiguredObject, capacity=10, pre_initialize=False)
    print(f"Lazy pool available: {lazy_pool.available()}")  # 0

    obj = lazy_pool.get()
    lazy_pool.release(obj)
    print(f"After first get: {lazy_pool.available()}")  # 1

    # eager: all objects created upfront
    eager_pool = Pool(ConfiguredObject, capacity=10, pre_initialize=True)
    print(f"Eager pool available: {eager_pool.available()}")  # 10
    print()


if __name__ == "__main__":
    example_custom_factory()
    example_builder_factory()
    example_lazy_vs_eager()
