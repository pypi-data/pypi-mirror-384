import threading
from unittest import TestCase, mock

import sentry_sdk
from sentry_sdk.envelope import Envelope

from openmodule import sentry
from openmodule_test.utils import wait_for_value


class SentryTestTransport(sentry_sdk.transport.Transport):
    """
    Custom transport for testing that stores envelopes in a list.
    """

    def __init__(self, options=None):
        super().__init__(options)
        self.envelopes: list[Envelope] = []
        self.envelopes_lock = threading.Lock()

    def capture_envelope(self, envelope: Envelope):
        with self.envelopes_lock:
            self.envelopes.append(envelope)

    def get_envelopes(self, clear: bool = True) -> list[Envelope]:
        with self.envelopes_lock:
            envelopes = self.envelopes
            if clear:
                self.envelopes = []
            return envelopes


class SentryTestMixin(TestCase):
    """
    Test mixin for testing with sentry. It patches the sentry transport to store envelopes in a list.
    Provides the get_sent_envelopes method to get the stored envelopes.
    """
    _sentry_transport_patch: mock._patch

    @classmethod
    def setUpClass(cls) -> None:
        cls._sentry_transport_patch = mock.patch("openmodule.sentry.StoringTransport", SentryTestTransport)
        cls._sentry_transport_patch.start()
        super().setUpClass()

    def tearDown(self) -> None:
        super().tearDown()
        sentry.deinit_sentry()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls._sentry_transport_patch.stop()

    @property
    def sentry_transport(self) -> SentryTestTransport:
        transport = sentry_sdk.get_global_scope().client.transport
        self.assertIsInstance(transport, SentryTestTransport)
        return transport

    def _get_envelopes(self) -> list[Envelope]:
        return self.sentry_transport.get_envelopes(clear=False)

    def get_sent_envelopes(self, timeout: float = 0, clear: bool = True) -> list[Envelope]:
        wait_for_value(self._get_envelopes, target=[], invert_target=True, timeout=timeout)
        return self.sentry_transport.get_envelopes(clear=clear)
