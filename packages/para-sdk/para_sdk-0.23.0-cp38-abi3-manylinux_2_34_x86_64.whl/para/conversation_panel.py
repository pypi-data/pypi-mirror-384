import threading
import time
from typing import cast
import panel as pn

from .messages import *

class ConversationPanel:
  def __init__(self, out):
    self._out = out

  def create(self, stream):
    self._stream = stream
    self._conversation = stream._conversation
    self._recipient = 'actor' if self._conversation.provider is None else self._conversation.provider.split('@')[0]
    self._request = cast(PncpRequest, self._conversation.get_request())

    self._status = 'Live'

    # build panel
    self.spinner = pn.indicators.LoadingSpinner(value=True, width=20, height=20, color="primary")
    self.title = pn.pane.Markdown(self._title_display())
    self.status_text = pn.pane.HTML(self._status_display(), width=400)
    self.column = pn.Column(
        self.title,
        self.spinner
    )
    self._insert = 1
    self._poller = pn.state.add_periodic_callback(self._update_status, period=1000)
    return self.column

  def _title_display(self):
    req = self._request.request
    title = f"### {self._status}: {req['subject']}/{req['action']}"
    if self._conversation.provider is not None:
      title += ' -> ' + self._conversation.provider.split('@')[0]
    return title

  def _status_display(self):
    return f"<B>{self._status}</B>"

  def _update_status(self):
    while True:
      obj = self._stream.next()
      if obj is None:
        return
      if self._out is not None:
        self._out.append_stdout(f"got: {obj}\n")
      self._append_message(obj)
      if isinstance(obj, PncpResponse) or isinstance(obj, PncpError):
        self._status = 'Complete' if isinstance(obj, PncpResponse) else 'Failed'
        self.status_text.object = self._status_display()
        self.title.object = self._title_display()
        self.spinner.value = False
        self.column.pop()
        self._poller.stop()
        self._out.append_stdout(f"{self._status}\n")

  def _append_message(self, msg):
    match msg:
      case PncpRequest():
        party = 'you'
      case _:
        party = self._recipient
    index = self._insert
    self._insert += 1
    self.column.insert(index, pn.pane.HTML(f"({party}) {msg.display_text()}", width=400))