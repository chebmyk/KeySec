"""Tests for in-process service-provider registration."""

from __future__ import annotations

import unittest

from keysec.config import ConfigurationError, ProviderConfig, ProviderGroupConfig
from keysec.providers.provider import Provider
from keysec.providers.service.service_provider import ServiceProvider
from keysec.providers.service.service_provider_registry import ServiceProviderRegistry


class LocalMemoryProvider(ServiceProvider):
    def get_secret(self, secret: str) -> str:
        return f"{self.name}:{secret}"


class UnrelatedProvider(Provider):
    pass


class ServiceRegistryTests(unittest.TestCase):
    def make_registry(self) -> ServiceProviderRegistry:
        registry = ServiceProviderRegistry()
        registry.register("memory", LocalMemoryProvider)
        return registry

    def test_creates_provider_selected_by_name(self) -> None:
        group = ProviderGroupConfig(
            default="first",
            providers={
                "first": ProviderConfig("first", "memory", {}),
                "second": ProviderConfig("second", "memory", {}),
            },
        )

        provider = self.make_registry().create(group.select("second"))

        self.assertEqual(provider.name, "second")
        self.assertEqual(provider.get_secret("item"), "second:item")

    def test_uses_configured_default_provider(self) -> None:
        group = ProviderGroupConfig(
            default="first",
            providers={"first": ProviderConfig("first", "memory", {})},
        )

        provider = self.make_registry().create(group.select(None))

        self.assertEqual(provider.name, "first")

    def test_unknown_implementation_type_is_explicit(self) -> None:
        registry = self.make_registry()
        config = ProviderConfig("missing", "unknown", {})

        with self.assertRaisesRegex(ConfigurationError, "not registered"):
            registry.create(config)

    def test_rejects_non_service_provider_implementation(self) -> None:
        registry = ServiceProviderRegistry()

        with self.assertRaisesRegex(TypeError, "ServiceProvider"):
            registry.register("unrelated", UnrelatedProvider)  # type: ignore[arg-type]

    def test_rejects_duplicate_implementation_type(self) -> None:
        registry = self.make_registry()

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register("memory", LocalMemoryProvider)


if __name__ == "__main__":
    unittest.main()
