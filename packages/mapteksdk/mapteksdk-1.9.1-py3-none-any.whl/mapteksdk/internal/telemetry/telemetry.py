"""Classes related to sending telemetry events.

Warnings
--------
Vendors and clients should not develop scripts or applications against
this package. The contents may change at any time without warning.
"""

###############################################################################
#
# (C) Copyright 2024, Maptek Pty Ltd. All rights reserved.
#
###############################################################################
from __future__ import annotations

from collections import Counter
import os
import pathlib
import logging
import subprocess
from time import monotonic_ns
import typing
from uuid import UUID, uuid4

from .file_info import get_script_information
from .telemetry_protocol import TelemetryProtocol

if typing.TYPE_CHECKING:
  from collections.abc import MutableSequence

  from .file_info import FileInformation

LOG = logging.getLogger("mapteksdk.telemetry")


class Telemetry(TelemetryProtocol):
  """Record and send telemetry events.

  Parameters
  ----------
  uuid_generator
    The UUID which identifies this script run.
    This is used to name the telemetry file and included in every telemetry
    event.
    If None (default), a UUID will be automatically generated.
  """
  def __init__(self, uuid: UUID | None=None):
    self.__function_call_tallies: Counter[str] = Counter()
    self.__object_sizes: MutableSequence[tuple[str, int]] = []
    self.__uuid = uuid or uuid4()
    self.__sent = False
    self.__script_information: FileInformation | None = None
    self.__start_time = monotonic_ns()
    try:
      self.__script_information = get_script_information()
    # Failing to record the script information telemetry should not
    # error out the whole script.
    # pylint: disable=broad-exception-caught
    except Exception:
      LOG.info("Failed to record script information telemetry", exc_info=True)

  def __write_telemetry(self, destination: typing.TextIO):
    """Internal sending of the telemetry."""
    self.__write_script_information(destination)
    self.__write_runtime_telemetry(destination)
    self.__write_function_calls(destination)
    self.__write_object_sizes(destination)

  def __send_telemetry(self, telemetry_directory: pathlib.Path):
    """Send all telemetry files in `telemetry_directory`.

    This will send any unsent telemetry from previous script runs.
    """
    telemetry_sender_path = (
      pathlib.Path(__file__).parent
      / "TelemetrySender.exe"
    )
    if not telemetry_sender_path.exists():
      # This is likely a workspace build so the telemetry sender will be in
      # the build folder.
      telemetry_sender_path = (
        pathlib.Path(__file__).parent.parent.parent.parent
        / "build"
        / "lib"
        / "mapteksdk"
        / "internal"
        / "telemetry"
        / "TelemetrySender.exe"
      )
    try:
      # Using Popen in a context manager will cause Python to wait for the
      # telemetry sender process to exit before the context manager will be
      # exited.
      # pylint: disable=consider-using-with
      subprocess.Popen(
        [
          telemetry_sender_path,
          "Mapteksdk",
          telemetry_directory
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=(
          subprocess.CREATE_NEW_PROCESS_GROUP
          | subprocess.DETACHED_PROCESS
          # VS Code creates a job, so this option is required to avoid the
          # telemetry sender being killed when this process exits when
          # running in VS Code.
          | subprocess.CREATE_BREAKAWAY_FROM_JOB
        ),
      )
    except OSError:
      LOG.info("Failed to start the telemetry sender.", exc_info=True)

  def __write_script_information(self, destination: typing.TextIO):
    """Write script information telemetry."""
    file_info = self.__script_information
    if file_info:
      destination.write(
        f"FileInfo|{file_info.name}|{file_info.file_hash}|{self.__uuid}\n"
      )

  def __write_runtime_telemetry(self, destination: typing.TextIO):
    """Write telemetry based on the runtime."""
    end_time = monotonic_ns()
    # Divide by one million to convert from nanoseconds to milliseconds.
    total_time = int((end_time - self.__start_time) / 1000000)
    destination.write(
      f"ScriptRuntime|{total_time}|{self.__uuid}\n"
    )

  def __write_function_calls(self, destination: typing.TextIO):
    """Write function call tally telemetry to `destination`."""
    for name, tally in self.__function_call_tallies.items():
      destination.write(
        f"FunctionCallCount|{name}|{tally}|{self.__uuid}\n"
      )

  def __write_object_sizes(self, destination: typing.TextIO):
    """Write object sizes telemetry to `destination`."""
    for name, size in self.__object_sizes:
      destination.write(
        f"ObjectSize|{name}|{size}|{self.__uuid}\n"
      )

  def record_function_call(self, name: str):
    self.__function_call_tallies[name] += 1

  def record_object_size(self, name: str, size: int):
    self.__object_sizes.append((name, size))

  def send(self):
    if self.__sent:
      return
    self.__sent = True

    appdata = os.getenv('LOCALAPPDATA')
    if not appdata:
      # Local application data is not available, so cannot record any
      # telemetry.
      LOG.info("Failed to send telemetry. %LOCALAPPDATA% was not available.")
      return
    telemetry_directory = (
      pathlib.Path(appdata)
      / "Maptek"
      / "PythonSdk"
      / "Telemetry"
    )
    target_path = (
      telemetry_directory
      / f"{self.__uuid}-Telemetry.txt"
    )
    try:
      telemetry_directory.mkdir(parents=True, exist_ok=True)
      with open(target_path, "w", encoding="utf-8") as file:
        self.__write_telemetry(file)
      self.__send_telemetry(telemetry_directory)
    except OSError:
      LOG.info(
        "Failed to write the telemetry file.",
        exc_info=True
      )
