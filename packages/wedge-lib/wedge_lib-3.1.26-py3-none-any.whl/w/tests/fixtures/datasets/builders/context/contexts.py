from w.services.technical.models.context import BaseContext


class FakeContext(BaseContext):
    def __init__(self, message):
        super().__init__()
        self.message = message

    def to_dict(self):
        return {"message": self.message}
