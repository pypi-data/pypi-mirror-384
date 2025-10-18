import typing as t
import warnings
from threading import Lock
from weakref import WeakKeyDictionary

if t.TYPE_CHECKING:
    import typing_extensions as te

ANY = object()
ANY_ID = 0

class NamedSignal:
    __slots__ = ('name', 'receivers', 'is_muted', 'lock')

    def __init__(self, name: str) -> None:
        self.name = name
        self.receivers: t.List[t.Callable] = []
        self.is_muted = False
        self.lock = Lock()

    def connect(self, receiver: t.Callable) -> None:
        with self.lock:
            if receiver not in self.receivers:
                self.receivers.append(receiver)

    def disconnect(self, receiver: t.Callable) -> None:
        with self.lock:
            if receiver in self.receivers:
                self.receivers.remove(receiver)

    def send(self, sender: t.Any, **kwargs: t.Any) -> t.List[t.Tuple[t.Callable, t.Any]]:
        if self.is_muted:
            return []
        
        results = []
        for receiver in self.receivers:
            try:
                result = receiver(sender, **kwargs)
                results.append((receiver, result))
            except Exception as e:
                warnings.warn(f"Signal {self.name} receiver {receiver} failed: {e}")
        return results

    def mute(self) -> None:
        self.is_muted = True

    def unmute(self) -> None:
        self.is_muted = False

    def has_receivers(self) -> bool:
        return len(self.receivers) > 0

    def __repr__(self) -> str:
        return f"<NamedSignal '{self.name}'>"

class Signal:
    __slots__ = ('receivers', 'lock')

    def __init__(self) -> None:
        self.receivers: t.List[t.Callable] = []
        self.lock = Lock()

    def connect(self, receiver: t.Callable) -> None:
        with self.lock:
            if receiver not in self.receivers:
                self.receivers.append(receiver)

    def disconnect(self, receiver: t.Callable) -> None:
        with self.lock:
            if receiver in self.receivers:
                self.receivers.remove(receiver)

    def send(self, sender: t.Any, **kwargs: t.Any) -> t.List[t.Tuple[t.Callable, t.Any]]:
        results = []
        for receiver in self.receivers:
            try:
                result = receiver(sender, **kwargs)
                results.append((receiver, result))
            except Exception as e:
                warnings.warn(f"Signal receiver {receiver} failed: {e}")
        return results

    def has_receivers(self) -> bool:
        return len(self.receivers) > 0

    def __repr__(self) -> str:
        return "<Signal>"

class SignalRegistry:
    __slots__ = ('_signals', '_lock')

    def __init__(self) -> None:
        self._signals: t.Dict[str, NamedSignal] = {}
        self._lock = Lock()

    def get_signal(self, name: str) -> NamedSignal:
        with self._lock:
            if name not in self._signals:
                self._signals[name] = NamedSignal(name)
            return self._signals[name]

    def mute_all(self) -> None:
        with self._lock:
            for signal in self._signals.values():
                signal.mute()

    def unmute_all(self) -> None:
        with self._lock:
            for signal in self._signals.values():
                signal.unmute()

    def reset(self) -> None:
        with self._lock:
            self._signals.clear()

signals = Signal()
request_started = NamedSignal('request_started')
request_finished = NamedSignal('request_finished')
got_request_exception = NamedSignal('got_request_exception')
before_render_template = NamedSignal('before_render_template')
template_rendered = NamedSignal('template_rendered')
message_flashed_signal = NamedSignal('message_flashed')

def message_flashed(sender: t.Any, message: str, category: str = 'message') -> None:
    message_flashed_signal.send(sender, message=message, category=category)

def connect_default_signals(app: t.Any) -> None:
    pass

def disconnect_default_signals(app: t.Any) -> None:
    request_started.receivers.clear()
    request_finished.receivers.clear()
    got_request_exception.receivers.clear()
    before_render_template.receivers.clear()
    template_rendered.receivers.clear()
    message_flashed_signal.receivers.clear()

def reset_signals() -> None:
    disconnect_default_signals(None)

class SignalContext:
    __slots__ = ('signal', 'receiver')

    def __init__(self, signal: t.Union[Signal, NamedSignal], receiver: t.Callable) -> None:
        self.signal = signal
        self.receiver = receiver

    def __enter__(self) -> 'SignalContext':
        return self

    def __exit__(self, exc_type: t.Any, exc_val: t.Any, exc_tb: t.Any) -> None:
        self.signal.disconnect(self.receiver)

def temporary_connection(signal: t.Union[Signal, NamedSignal], receiver: t.Callable) -> SignalContext:
    signal.connect(receiver)
    return SignalContext(signal, receiver)

__all__ = [
    'signals',
    'request_started',
    'request_finished', 
    'got_request_exception',
    'before_render_template',
    'template_rendered',
    'message_flashed_signal',
    'message_flashed',
    'connect_default_signals',
    'disconnect_default_signals',
    'reset_signals',
    'temporary_connection',
    'NamedSignal',
    'Signal',
    'SignalRegistry',
    'SignalContext'
]