import sys
import json
import html
import builtins
from datetime import datetime
from dataclasses import dataclass
from types import MethodType
from IPython.core import display_functions
import mimeparse

def value_summary(v):
  if type(v) == list:
    elms = [value_summary(e) for e in v]
    return '[' + ', '.join(elms) + ']'
  elif type(v) == dict:
    elms = []
    for k in v:
      elms.append(k+': ' + value_summary(v[k]))
    return '{' + ', '.join(elms) + '}'
  elif type(v) == str:
    return json.dumps(v)
  return str(v)

def data_summary(data):
    if type(data) == dict:
      elms = []
      for k in data:
        elms.append(k+': ' + value_summary(data[k]))
      return ', '.join(elms)
    else:
      return value_summary(data)

@dataclass
class PncpMessage:
  id: str
  created: datetime

  def display_text(self):
    return f"Unknown message type"

@dataclass
class PncpStatus(PncpMessage):
  status: dict

  def _repr_json_(self):
    meta = {'root': 'message', 'expanded': True}
    data = {'id': self.id, 'created': self.created, 'status': self.status}
    return (data, meta)

  def display_text(self):
    keys = list(self.status.keys())
    if len(keys) == 1:
      k = keys[0].lower()
      if k == 'message' or k == 'status':
        return 'Status: ' + data_summary(self.status[keys[0]])
    return 'Status: ' + data_summary(self.status)

@dataclass
class PncpResponse(PncpMessage):
  response: dict

  def _repr_json_(self):
    meta = {'root': 'message', 'expanded': True}
    data = {'id': self.id, 'created': self.created, 'response': self.response}
    return (data, meta)

  def display_text(self):
    keys = list(self.response.keys())
    if len(keys) == 1:
      k = keys[0].lower()
      if k == 'message' or k == 'response' or k == 'result':
        return 'Response: ' + data_summary(self.response[keys[0]])
    return 'Response: ' + data_summary(self.response)

@dataclass
class PncpError(PncpMessage):
  error: dict

  def _repr_json_(self):
    meta = {'root': 'message', 'expanded': True}
    data = {'id': self.id, 'created': self.created, 'error': self.error}
    return (data, meta)

  def display_text(self):
    keys = list(self.error.keys())
    if len(keys) == 1:
      k = keys[0].lower()
      if k == 'message' or k == 'error' or k == 'result':
        return 'Error: ' + data_summary(self.error[keys[0]])
    return 'Error: ' + data_summary(self.error)

@dataclass
class PncpRequest(PncpMessage):
  request: dict

  def _repr_json_(self):
    meta = {'root': 'message', 'expanded': True}
    request = {'subject': self.request['subject'], 'action': self.request['action'], 'data': self.request['data']}
    data = {'id': self.id, 'created': self.created, 'request': request}
    return (data, meta)

  def display_text(self):
    args = data_summary(self.request['data'])
    return f"Request: {self.request['subject']}/{self.request['action']}({args})"

def get_mime_field(body: dict[str,any]):
  if type(body) == dict:
    for mk in body:
      if mk.startswith('Mime'):
        k = mk[4:]
        k = k[0:1].lower() + k[1:]
        if k in body:
          try:
            mime_type = mimeparse.parse_mime_type(body[mk])
            return (mime_type, body[k])
          except:
            pass
      elif mk.startswith('_mime_'):
        k = mk[6:]
        if k in body:
          try:
            mime_type = mimeparse.parse_mime_type(body[mk])
            return (mime_type, body[k])
          except:
            pass

def apply_rendering(msg: PncpMessage, body: dict[str,any]):
  if not hasattr(builtins, "__IPYTHON__"):
    return msg

  render = get_mime_field(body)
  if render is not None:
    (mime, data) = render
    (base, subtype, params) = mime
    if base == 'application' and subtype == 'vnd.paranet.embed+html':
      width = params.get('width', '100%')
      height = params.get('height', '400')
      iframe = f"<iframe width=\"{width}\" height=\"{height}\" srcdoc=\"{html.escape(data)}\" frameborder=\"0\"></iframe>"
      # Notebook prioritizes json over html, so this method circumvents that by only providing html
      def display(self):
        display_functions.display({'text/html': iframe}, raw=True)
      setattr(msg, '_ipython_display_', display.__get__(msg, msg.__class__))
      
  return msg

def graphql_to_py(msg):
  id = msg['id']
  created = datetime.fromisoformat(msg['createdAt'].replace("Z", "+00:00"))
  if msg['contents']['packet']['type'] == 'request':
    request = msg['contents']['packet']['body']['body']
    request['data'] = request['body']
    del request['body']
    return PncpRequest(id=id, created=created, request=request)
  elif msg['contents']['packet']['type'] == 'message':
    body = msg['contents']['packet']['body']
    if body['message']['type'] == 'response':
      response = body['message']['body']['data']
      return apply_rendering(PncpResponse(id=id, created=created, response=response), response)
    elif body['message']['type'] == 'status':
      status = body['message']['body']['data']
      return PncpStatus(id=id, created=created, status=status)
    elif body['message']['type'] == 'error':
      error = body['message']['body']['data']
      return PncpError(id=id, created=created, error=error)
  print('Unexpected GQL message', msg, file=sys.stderr)

def pncp_to_py(msg):
  if msg['type'] == 'message':
    body = msg['body']
    id = body['messageId']
    created = datetime.fromisoformat(body['timeCreated'].replace("Z", "+00:00"))
    if body['message']['message']['type'] == 'response':
      response = body['message']['message']['body']['data']
      return apply_rendering(PncpResponse(id=id, created=created, response=response), response)
    elif body['message']['message']['type'] == 'status':
      status = body['message']['message']['body']['data']
      return PncpStatus(id=id, created=created, status=status)
    elif body['message']['message']['type'] == 'error':
      error = body['message']['message']['body']['data']
      return PncpError(id=id, created=created, error=error)
  print('Unexpected PNCP message', msg, file=sys.stderr)
