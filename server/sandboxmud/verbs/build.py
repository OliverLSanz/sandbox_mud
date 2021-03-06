from . import verb
from .. import entities
from .. import util

class Build(verb.Verb):
    """This verb allows the user to create a new room connected to his current location.
    All the user need to know is the command he should write to start creation. That
    command will start a text wizard that drives him across the creation process.
    """
    command = 'construir'
    permissions = verb.PRIVILEGED

    def __init__(self, session):
        super().__init__(session)
        self.new_room = entities.Room(save_on_creation=False, world_state=self.session.user.room.world_state)
        self.exit_from_here = entities.Exit(destination=self.new_room, room=self.session.user.room, save_on_creation=False)
        self.exit_from_there = entities.Exit(destination=self.session.user.room, room=self.new_room, save_on_creation=False)
        self.current_process_function = self.process_first_message

    def process(self, message):
        if message == '/':
            self.session.send_to_client("Construcción cancelada.")
            self.finish_interaction()
        else:
            self.current_process_function(message)

    def process_first_message(self, message):
        self.session.send_to_client(f"Comienzas a construir una habitación.\n{chr(9472)*37}\n{chr(10060)} Para cancelar, introduce '/' en cualquier momento.\n\nEscribe los siguientes datos:\n {chr(9873)} Nombre de la habitación")
        self.current_process_function = self.process_room_name

    def process_room_name(self, message):
        if not message:
            self.session.send_to_client("Tienes que poner un nombre a tu habitación. Prueba otra vez.")
        else:
            self.new_room.name = message
            self.session.send_to_client(f" {chr(128065)} Descripción")
            self.current_process_function = self.process_room_description

    def process_room_description(self, message):
        this_room = self.session.user.room.name
        new_room = self.new_room.name
        self.new_room.description = message
        self.session.send_to_client(f' \u2B95 Nombre de la salida en "{this_room}" hacia "{new_room}"\n   [Por defecto: "a {new_room}"]')
        self.current_process_function = self.process_here_exit_name

    def process_here_exit_name(self, message):
        if not message:
            message = "a {}".format(self.new_room.name)
            message = self.make_exit_name_valid(message, self.session.user.room)

        self.exit_from_here.name = message
        try:
            self.exit_from_here.ensure_i_am_valid()
        except entities.WrongNameFormat:
            self.session.send_to_client("El nombre no puede acabar con # y un número. Prueba con otro.")
        except entities.RoomNameClash:
            self.session.send_to_client("Ya hay un objeto o salida con ese nombre en esta sala. Prueba con otro.")
        except entities.TakableItemNameClash:
            self.session.send_to_client("Hay en el mundo un objeto tomable con ese nombre. Los objetos tomables deben tener un nombre único en todo el mundo, así que prueba a poner otro.")
        else:
            self.session.send_to_client(f' \u2B95 Nombre de la salida en "{self.new_room.name}" hacia "{self.session.user.room.name}"\n   [Por defecto: "a {self.new_room.name}"]')
            self.current_process_function = self.process_there_exit_name

    def process_there_exit_name(self, message):
        if not message:
            message = "a {}".format(self.session.user.room.name)
            message = self.make_exit_name_valid(message, self.new_room)  

        self.exit_from_there.name = message
        
        try:
            self.exit_from_there.ensure_i_am_valid()
        except entities.WrongNameFormat:
            self.session.send_to_client("El nombre no puede acabar con # y un número. Prueba con otro.")
        except entities.TakableItemNameClash:
            self.session.send_to_client("Hay en el mundo un objeto tomable con ese nombre. Los objetos tomables deben tener un nombre único en todo el mundo, así que prueba a poner otro.")
        else:
            self.new_room.save()
            self.exit_from_here.save()
            self.exit_from_there.save()

            self.session.send_to_client("¡Enhorabuena! Tu nueva habitación está lista.")
            if not self.session.user.master_mode:
                self.session.send_to_others_in_room("Los ojos de {} se ponen en blanco un momento. Una nueva salida aparece en la habitación.".format(self.session.user.name))
            self.finish_interaction()

    def make_exit_name_valid(self, exit_name, room):
        while not entities.Exit.name_is_valid(exit_name, room):
            exit_name = 'directo ' + exit_name
        return exit_name

    def cancel():
        self.session.user.room.exits.remove(self.exit_from_here)