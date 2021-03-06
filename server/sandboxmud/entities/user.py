import mongoengine
from . import inventory as inventory_module

class User(mongoengine.Document):
    name = mongoengine.StringField(required=True)
    room = mongoengine.ReferenceField('Room')
    client_id = mongoengine.IntField(default=None)
    master_mode = mongoengine.BooleanField(default=False)

    def __init__(self, *args, save_on_creation=True,  **kwargs):
        super().__init__(*args, **kwargs)
        if self.id is None and save_on_creation:
            self.save()

    def move(self, exit_name):
        if exit_name in [exit.name for exit in self.room.exits]:
            self.room = self.room.get_exit(exit_name).destination
            self.save()

    def teleport(self, room):
        self.room = room
        self.save()

    def save_item(self, item):
        item_snapshot = item.clone()
        item_snapshot.saved_in = self.room.world_state
        item_snapshot.item_id = item_snapshot._generate_item_id()
        item_snapshot.save()
        self.save()
        return item_snapshot

    def connect(self, client_id):
        self.client_id = client_id
        self.save()

    def disconnect(self):
        self.client_id = None
        self.save()

    def enter_master_mode(self):
        self.master_mode = True
        self.save()

    def leave_master_mode(self):
        self.master_mode = False
        self.save()

    def get_inventory_from(self, world_state):
        inventory = next(inventory_module.Inventory.objects(user=self, world_state=world_state), None)
        if inventory is None:
            inventory = inventory_module.Inventory(user=self, world_state=world_state)
        return inventory

    def get_current_world_inventory(self):
        return self.get_inventory_from(self.room.world_state)