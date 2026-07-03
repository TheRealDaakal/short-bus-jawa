class RaidSession:
    def __init__(self, operation):
        self.operation = operation

        self.tanks = []
        self.healers = []
        self.dps = []
        self.bench = []

    def remove_player(self, user_id):
        self.tanks = [p for p in self.tanks if p.id != user_id]
        self.healers = [p for p in self.healers if p.id != user_id]
        self.dps = [p for p in self.dps if p.id != user_id]
        self.bench = [p for p in self.bench if p.id != user_id]