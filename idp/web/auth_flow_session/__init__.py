from storage import storage
import json
import random, string
import logging

class auth_flow_session:
    def create(self,
                 client_id,
                 scope=None,
                 response_type=None,
                 redirect_uri=None,
                 state=None,
                 nonce=None):

        log_header = 'Method=************** Message=Method Called'
        logging.info(log_header)

        self.client_id = client_id
        self.scope = scope
        self.response_type = response_type
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.state = state
        self.nonce = nonce
        self.code_valid = True
        self.authenticated = False

        self.claims = {}
        self.code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(16)]) #uuid.uuid4().hex

        logging.info(log_header + ' Code=%s' % self.code)

        self._persist()

    def load(self, code):
        self.code = code
        self._retrieve()

    def set_claims(self, claims={}):
        for key, value in claims.items():
            self.claims[key] = value

    def create_access_token(self):
        self.access_token = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(16)]) #uuid.uuid4().hex

    def save(self):
        self._persist()

    def invalidate_code(self):
        self.code_valid = False
        self._persist()

    def _persist(self):
        storage.set('sessions_%s' % self.code, json.dumps(self.__dict__))
        storage.expire('sessions_%s' % self.code, 600) # 10 minutes - RFC 6749 4.1.2 max lifetime for a code

    def _retrieve(self):
        state = json.loads(storage.get('sessions_%s' % self.code))

        for key, value in state.items():
            self.__dict__[key] = value

