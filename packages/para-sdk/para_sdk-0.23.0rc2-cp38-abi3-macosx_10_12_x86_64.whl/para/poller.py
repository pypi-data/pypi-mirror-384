import time
from dataclasses import dataclass
from typing import Tuple
from queue import Queue
from threading import Lock, Thread

class Poller:
  _client: any
  _subscribers: dict[str,list[Tuple[int,Queue]]]
  _lock: Lock

  def __init__(self, client):
    self._client = client
    self._subscribers = {}
    self._lock = Lock()

  def start(self):
    self._thread = Thread(target=self._mainloop, daemon=True)
    self._thread.start()

  def _mainloop(self):
    while True:
      resp = self._client.poll_next()
      if resp is not None:
        if resp['type'] == 'message':
          body = resp['body']
          cid = body['id'].split('@')[0]
          if self._lock.acquire():
            try:
              if cid in self._subscribers:
                for (_, q) in self._subscribers[cid]:
                  q.put(resp)
            except Exception as ex:
              print(ex)
            self._lock.release()
      else:
        time.sleep(0.1)

  def subscribe(self, uid: int, cid: str) -> Queue:
    if self._lock.acquire():
      try:
        if cid not in self._subscribers:
          self._subscribers[cid] = []
        q = Queue()
        self._subscribers[cid].append((uid, q))
      except Exception as ex:
        print(ex)
      self._lock.release()
      return q

  def unsubscribe(self, uid: int, cid: str):
    if self._lock.acquire():
      try:
        if cid in self._subscribers:
          self._subscribers[cid] = [sub for sub in self._subscribers[cid] if sub[0] != uid]
          if len(self._subscribers[cid]) == 0:
            del self._subscribers[cid]
      except Exception as ex:
        print(ex)
      self._lock.release()
