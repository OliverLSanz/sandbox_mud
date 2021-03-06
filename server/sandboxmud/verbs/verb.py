from .. import session

FREE = 'free'
PRIVILEGED = 'privileged'
CREATOR = 'creator'

LOBBYVERB = 'lobbyverb'
WORLDVERB = 'worldverb'

class Verb():
    """This is the template for creating new verbs. Every verb should have Verb as parent.
    This is an abstract class, with some methods not implemented.

    A verb is every action that a user can take in the world. Each verb object processes
    a fixed set of user messages, and takes all the actions relative to them.

    Each verb has its own criteria that determines if it can process a given message. This
    criteria is defined in its can_process(message) method. The session calls the can_process method
    of each verb in its verb list until it finds a verb that can process the message. 

    Then, the session creates a new instance of the verb and lets it process all user messages
    (via the process(message) method) until the verb instance returns True for its method command_finished.
    """

    command = 'verb '
    permissions = FREE  # possible values: FREE, PRIVILEGED and CREATOR.
    verbtype = WORLDVERB

    @classmethod
    def can_process(cls, message, session):
        if cls.verbtype == WORLDVERB and session.user.room is None:
            return False

        if cls.verbtype == LOBBYVERB and session.user.room is not None:
            return False

        if message.startswith(cls.command):
            return True
        
        return False

    def __init__(self, session):
        self.session = session
        self.finished = False

    def execute(self, message):
        if self.user_has_enough_privileges():
            self.process(message)
        else:
            self.session.send_to_client('No tienes permisos suficientes para hacer eso.')
            self.finish_interaction()

    def user_has_enough_privileges(self):
        if self.session.user is None:
            return True

        if self.session.user.room is None:
            return True

        world = self.session.user.room.world_state.get_world()
        
        if self.permissions == 'free':
            return True
        
        if self.permissions == 'privileged':
            if world.all_can_edit or isinstance(self.session, session.GhostSession) or world.is_privileged(self.session.user):
                return True
            else:
                return False
        
        if self.permissions == 'creator':
            if world.is_creator(self.session.user):
                return True
            else:
                return False

    def process(self, message):
        raise Exception('Abstract method of interface Verb not implemented')

    def command_finished(self):
        return self.finished

    def finish_interaction(self):
        """This method must be called from within the Verb when the interaction is finished, so the session
        can pass command to other verbs"""
        self.finished = True