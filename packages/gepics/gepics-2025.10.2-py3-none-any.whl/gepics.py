import os
import re
from contextlib import ContextDecorator
from datetime import datetime
from enum import Enum

import epics
from epics.ca import current_context, attach_context, ChannelAccessGetFailure
from gi.repository import GLib, GObject

CA_CONTEXT = current_context()
REUSE = False
PACKAGE_DIR = os.path.dirname(__file__)


def get_version(prefix='v', package=PACKAGE_DIR):
    from subprocess import CalledProcessError, check_output

    # Return the version if it has been injected into the file by git-archive
    tag_re = re.compile(rf'\btag: {prefix}([0-9][^,]*)\b')
    version = tag_re.search('$Format:%D$')
    name = __name__.split('.')[0]

    if version:
        return version.group(1)

    package_dir = package
    if os.path.isdir(os.path.join(package_dir, '.git')):
        # Get the version using "git describe".
        version_cmd = 'git describe --tags --abbrev=0'
        release_cmd = 'git rev-list HEAD ^$(git describe --abbrev=0) | wc -l'
        try:
            version = check_output(version_cmd, shell=True).decode().strip()
            release = check_output(release_cmd, shell=True).decode().strip()
            return f'{version}.{release}'.strip(prefix)
        except CalledProcessError:
            version = '0.0'
            release = 'dev'
            return f'{version}.{release}'.strip(prefix)
    else:
        try:
            from importlib import metadata
        except ImportError:
            # Running on pre-3.8 Python; use importlib-metadata package
            import importlib_metadata as metadata

        version = metadata.version(name)

    return version


class Alarm(Enum):
    NORMAL, MINOR, MAJOR, INVALID = range(4)


class BasePV(GObject.GObject):
    """
    Process Variable Base Class
    """
    __gsignals__ = {
        'changed': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'active': (GObject.SignalFlags.RUN_FIRST, None, (bool,)),
        'alarm': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
        'time': (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(self, name, monitor=True):
        """

        :param name: Process variable name
        :param monitor: Whether to enable monitoring
        """
        GObject.GObject.__init__(self)
        self._state = {}

    def set_state(self, **kwargs):
        """
        Set and emit signals for the specified states. Re-emits signals even if values are the same
        :param kwargs: keywords correspond to signal names, values are signal values to emit
        """

        for state, value in kwargs.items():
            self._state[state] = value
            GLib.idle_add(self.emit, state, value)

    def get_state(self, item):
        """
        Get the current state value for a given signal name
        :param item: signal name
        :return: value emitted with the last signal event
        """
        return self._state.get(item)

    def get_states(self):
        """
        Get the full state dictionary for all signals
        """
        return self._state

    def is_active(self):
        """
        Returns True if the process variable is active and connected.
        """
        return self._state.get('active', False)

    def is_connected(self):
        """An alias for is_active()"""
        return self.is_active()


PV_REPR = (
    "<PV: {name}\n"
    "    Data type:  {type}\n"
    "    Elements:   {count}\n"
    "    Server:     {server}\n"
    "    Access:     {access}\n"
    "    Alarm:      {alarm}\n"
    "    Time-stamp: {time}\n"
    "    Connected:  {connected}\n"
    ">"
)


class PV(BasePV):
    """A Process Variable

    A PV encapsulates an EPICS Process Variable with additional GObject features

    The primary interface methods for a pv are to get() and put() its
    value:

      >>> p = PV(pv_name)    # create a pv object given a pv name
      >>> p.get()            # get pv value
      >>> p.put(value)         # set pv to specified value.

    Additional important attributes include:

      >>> p.name             # name of pv
      >>> p.count            # number of elements in array pvs
      >>> p.type             # EPICS data type

    Note that GObject, derived features are available only when a GObject
    or compatible main-loop is running.

    """

    __REGISTRY = {}  # registry for re-using PVs

    def __init__(self, name, monitor=True):
        """
        Process Variable Object
        :param name: PV name
        :param monitor: boolean, whether to enable monitoring of changes and emitting of change signals
        """
        super(PV, self).__init__(name, monitor=monitor)
        self.name = name
        self.monitor = monitor
        self.string = False

        # re-use existing instances
        if REUSE and name in self.__REGISTRY:
            self.raw = self.__REGISTRY[name]
            self.raw.add_callback(callback=self.on_change, with_ctrlvars=True)
            self.raw.connection_callbacks.append(self.on_connect)
            GLib.timeout_add(100, self.update_state)    # make sure we update the state if it is already connected
        else:
            self.raw = epics.PV(name, auto_monitor=True, callback=self.on_change, connection_callback=self.on_connect)
            self.__REGISTRY[name] = self.raw

    def update_state(self,):
        """
        Update the state of the PV and emit signals.
        This method is called when the PV is connected or its value changes.
        """

        if self.raw.status == 0:
            value = self.raw.char_value if self.string else self.raw.value
            alarm = Alarm(self.raw.severity)
            self.set_state(active=True, changed=value, time=datetime.fromtimestamp(self.raw.timestamp), alarm=alarm)

    def on_connect(self, **kwargs):
        self.set_state(active=kwargs['conn'])

    def on_change(self, **kwargs):
        self.string = kwargs['type'] in ['time_string'] or (kwargs['type'] in ['time_char'] and kwargs['count'] > 1)
        value = kwargs['char_value'] if self.string else kwargs['value']
        alarm = Alarm(kwargs.get('severity', 0))
        self.set_state(changed=value, time=datetime.fromtimestamp(kwargs['timestamp']), alarm=alarm)

    def get(self, *args, **kwargs):
        kwargs['as_string'] = self.string | kwargs.get('as_string', False)
        return self.raw.get(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.raw.put(*args, **kwargs)

    def toggle(self, value1, value2):
        self.raw.put(value1, wait=True)
        return self.raw.put(value2)

    def __getattr__(self, item):
        try:
            return getattr(self.raw, item)
        except AttributeError:
            raise AttributeError('%r object has no attribute %r' % (self.__class__.__name__, item))
        except ChannelAccessGetFailure:
            return None

    def __repr__(self):
        return PV_REPR.format(
            name=self.raw.pvname, connected=self.is_active(), alarm=Alarm(self.raw.severity).name, time=self.raw.timestamp,
            access=self.raw.access, count=self.raw.count, type=self.raw.type, server=self.raw.host,
        )


def threads_init():
    if current_context() != CA_CONTEXT:
        attach_context(CA_CONTEXT)


class epics_context(ContextDecorator):
    def __enter__(self):
        if current_context() != CA_CONTEXT:
            attach_context(CA_CONTEXT)
        return self

    def __exit__(self, *exc):
        return False


__all__ = ['PV', 'threads_init', 'epics_context']
