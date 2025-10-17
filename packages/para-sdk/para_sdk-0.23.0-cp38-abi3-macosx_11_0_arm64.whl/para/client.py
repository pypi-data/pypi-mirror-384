import os
import json
import base64
import builtins
from dataclasses import dataclass
from queue import Empty, Queue

from para import para

from .poller import Poller
from .messages import *
if hasattr(builtins, "__IPYTHON__"):
  from .conversation_panel import ConversationPanel

class PncpConversation:
  """Represents and active or completed conversation.
  """

  id: str
  """The unique conversation ID"""

  messages: list[PncpMessage]
  """List of messages in the conversation"""

  _user_client: any
  _complete: bool
  _message_ids: set[str]

  def __init__(self, id: str, client, actor=None):
    self.id = id
    self._user_client = client
    self._complete = False
    self._message_ids = set()
    self.provider = actor
    self.messages = []

  def _repr_json_(self):
    meta = {'root': 'conversation', 'expanded': True}
    data = {'id': self.id, 'messages': [m._repr_json_()[0] for m in self.messages]}
    return (data, meta)

  def _push_pncp(self, msg):
    body = msg['body']
    id = body['messageId']
    if id not in self._message_ids:
      obj = pncp_to_py(msg)
      if obj is not None:
        if isinstance(obj, PncpResponse) or isinstance(obj, PncpError):
          self._complete = True
        self.messages.append(obj)
        self._message_ids.add(obj.id)
        return obj

  def _push_gql(self, msg):
    id = msg['id']
    if id not in self._message_ids:
      obj = graphql_to_py(msg)
      if obj is not None:
        if isinstance(obj, PncpResponse) or isinstance(obj, PncpError):
          self._complete = True
        self.messages.append(obj)
        self._message_ids.add(obj.id)
        return obj

  def _sort(self):
    self.messages.sort(key=lambda x: x.created)

  def dup(self):
    return PncpConversation(self.id, self._user_client, actor=self.provider)

  def get_last_message(self) -> PncpMessage:
    if len(self.messages) > 0:
      return self.messages[-1]

  def get_request(self) -> PncpRequest:
    for m in self.messages:
      if isinstance(m, PncpRequest):
        return m
    return None

  def get_response(self) -> PncpMessage:
    for m in self.messages:
      if isinstance(m, PncpResponse) or isinstance(m, PncpError):
        return m
    return None

  def update(self):
    """Update `messages` attribute with any new messages.
    """

    if self._complete:
      return
    list_resp = self._user_client._client.list_messages(self.id, 9999)
    for m in list_resp['messages']:
      self._push_gql(m)
    self._sort()

  def wait_response(self, show_status=False) -> PncpMessage:
    """Wait for the conversation to complete.

    Returns the response (`PncpResponse`) and an error (`PncpError`).
    """

    if not self._complete:
      # start poller before update to ensure no messages are missed
      q = self._user_client._poller.subscribe(id(self), self.id)
      self.update()
      try:
        while not self._complete:
          try:
            item = q.get(timeout=0.5)
            if item['type'] == 'message':
              obj = self._push_pncp(item)
              if show_status and obj is not None:
                if isinstance(obj, PncpStatus):
                  print(obj.display_text())
              self._sort()
          except Empty:
            pass
      finally:
        self._user_client._poller.unsubscribe(id(self), self.id)
    return self.get_response()
  
  def panel(self, out=None):
    """Create a live notebook panel that displays conversation status and messages."""

    if hasattr(builtins, "__IPYTHON__"):
      return make_panel(self, out)
    else:
      raise Exception('Not an ipython environment')


class ConversationStream:
  def __init__(self, conv: PncpConversation):
    self._conversation = conv
    # start poller before update to ensure no messages are missed
    self._queue = conv._user_client._poller.subscribe(id(self), conv.id)
    self._position = 0
    conv.update()
    if conv._complete:
      conv._user_client._poller.unsubscribe(id(self), conv.id)

  def _poll(self):    
    try:
      item = self._queue.get(block=False)
      if item['type'] == 'message':
        self._conversation._push_pncp(item)
        if self._conversation._complete:
          self._conversation._user_client._poller.unsubscribe(id(self), self._conversation.id)
        self._conversation._sort()
    except Empty:
      pass

  def next(self):
    cur = self._position
    if cur == len(self._conversation.messages):
      if not self._conversation._complete:
        self._poll()

    if cur < len(self._conversation.messages):
      self._position += 1
      return self._conversation.messages[cur]
    return None

def make_panel(conv: PncpConversation, out) -> ConversationStream:
  # create new instance of PncpConversation panel uses on background thread
  copy = conv.dup()
  stream = ConversationStream(copy)
  p = ConversationPanel(out)
  return p.create(stream)


@dataclass
class ActorList:
  actors: list[dict]

  def _repr_markdown_(self):
    lines = ['| id | kind |', '| --- | --- |']
    for a in self.actors:
      lines.append(f"| {a['id']} | {a['kind']} |")
    return '\n'.join(lines)

@dataclass
class SkillList:
  skills: list[dict]

  def _repr_markdown_(self):
    lines = ['| skillset | subject | action | inputs |', '| --- | --- | --- | --- |']
    for s in self.skills:
      schema = s.get('input_schema')
      inputs = []
      if schema is not None:
        if schema['type'] == 'object':
          for prop in schema['properties']:
            inp = prop
            typ = schema['properties'][prop].get('type')
            if typ is not None:
              inp = inp + ': ' + typ
            inputs.append(inp)

      lines.append(f"| {s['skillset']} | {s['subject']} | {s['action']} | {', '.join(inputs)} |")
    return '\n'.join(lines)

class UserClient:
  """A build-in instance of this class is created and accessible as `client` within the notebook environment.  The client is automatically logged in with your user ID."""

  _client: any
  _poller: Poller

  def __init__(self, paranet_client):
    self._client = paranet_client
    self._poller = Poller(paranet_client)
    self._poller.start()

  def new_request(self, subject: str, action: str, target_actor_id=None, **kwargs) -> PncpConversation:
    """Send a new skill request.

    - `subject` The skill request subject.
    - `action` The skill request action.
    - `kwargs` Any number of keyword arguments that are passed as the inputs for the skill request.

    Returns the active conversation (`PncpConversation`).

    """

    resp = self._client.skill_request(subject, action, target_actor_id=target_actor_id, **kwargs)
    cid = resp['id'].split('@')[0]
    conv = PncpConversation(cid, self, actor=resp.get('matched_id'))
    conv.update()
    return conv

  def skill_request(self, subject: str, action: str, target_actor_id=None, **kwargs) -> PncpMessage:
    """Send a new skill request and wait for the response.

    - `subject` The skill request subject.
    - `action` The skill request action.
    - `kwargs` Any number of keyword arguments that are passed as the inputs for the skill request.

    Returns the response (`PncpResponse`) and an error (`PncpError`).

    """

    resp = self._client.skill_request(subject, action, target_actor_id=target_actor_id, **kwargs)
    cid = resp['id'].split('@')[0]
    conv = PncpConversation(cid, self, actor=resp.get('matched_id'))
    return conv.wait_response(show_status=True)

  def list_actors(self):
    """Request a list of registered actors.

    Returns `ActorList`
    """

    resp = self.skill_request('paranode', 'list_actors')
    actors = resp.response['actors']
    return ActorList(actors=actors)

  def list_skills(self):
    """Request a full list of registered skills.

    Returns `SkillList`
    """

    resp = self.skill_request('paranode', 'list_skills')
    skills = resp.response['skills']
    return SkillList(skills=skills)

  def list_actor_skills(self, actor: str):
    """Request a list of the given actor's registered skills.

    `actor` Name of the actor to request skills for.

    Returns `SkillList`
    """

    if '@' not in actor:
      actor = actor + '@1.0.0'
    resp = self.skill_request('paranode', 'list_actor_skills', actor=actor)
    skills = resp.response['skills']
    return SkillList(skills=skills)

def new_connection(endpoint=None, actor=None, version=None, password=None, jwt=None, token=None, tls_id=None):
  endpoint = endpoint or os.environ['PARANET_ENDPOINT']

  broker_url = endpoint if endpoint else 'https://paranode:3131'
  service_url = endpoint+'/api/paranet-service' if endpoint else 'https://paranode:3132'

  actor = actor or os.environ.get('PARANET_ACTOR') or 'root'
  version = version or os.environ.get('PARANET_ACTOR_VERSION') or '1.0.0'
  actor_entity = f'{actor}@{version}'
  password = password or os.environ.get('PARANET_PASSWORD')
  jwt = jwt or os.environ.get('PARANET_JWT')
  token = token or os.environ.get('PARANET_TOKEN')

  tls_id = tls_id or os.environ.get('PARANET_TLS_ID')

  connection = para.connect(broker_url, service_url, actor_entity, password, jwt, token, tls_id)

  print(f'Connected to {broker_url} with actor {actor_entity}')

  return UserClient(connection)
  
def new_client(proxy=None):
  if 'PARANET_PROXY' in os.environ:
    endpoint = os.environ['PARANET_PROXY']
    broker_url = endpoint
    service_url = endpoint+'/api/paranet-service'
    if endpoint.startswith('http:'):
      client = para.connect(broker_url, service_url, 'root', None)
      return UserClient(client)
  else:
    broker_url = 'https://paranode:3131'
    service_url = 'https://paranode:3132'

  encoded_token = os.environ.get("PN_PY_USER")
  del os.environ["PN_PY_USER"]
  credentials = json.loads(base64.b64decode(encoded_token))
  actor_id = credentials['id']
  actor = actor_id.split('@')[0]
  access_token = {'access_token': credentials['token'], 'refresh_token': credentials['refresh']}
  client = para.connect(broker_url, service_url, actor, json.dumps(access_token))
  return UserClient(client)

if hasattr(builtins, "__IPYTHON__"):
  import panel as pn
  pn.extension()