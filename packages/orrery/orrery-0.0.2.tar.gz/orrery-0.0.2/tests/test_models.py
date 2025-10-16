from src.orrery.models import Model, ModelRegistry, ValueModel


class MockObserver:
    def __init__(self, model: Model):
        self.value_changed_events = []
        self.model = model
        model.add_value_changed_listener(self.value_changed)

    def value_changed(self, model):
        assert model == self.model
        self.value_changed_events.append(model.value)

    def get_and_clear_changed_events(self) -> list:
        events = self.value_changed_events
        self.value_changed_events = []
        return events


def test_value_changed_listener():
    model = ValueModel()
    observer = MockObserver(model)
    assert observer.get_and_clear_changed_events() == []
    model.value = "Foo"
    assert observer.get_and_clear_changed_events() == ["Foo"]
    model.value = "Bar"
    model.value = "Bar2"
    assert observer.get_and_clear_changed_events() == ["Bar", "Bar2"]


def test_value_changed_listener_initial_value():
    model = ValueModel(value="Foo")
    observer = MockObserver(model)
    assert observer.get_and_clear_changed_events() == ["Foo"]
    model.value = "Bar"
    assert observer.get_and_clear_changed_events() == ["Bar"]


def test_model_names():
    registry = ModelRegistry()
    observer = MockObserver(registry.model_names())
    assert observer.get_and_clear_changed_events() == [[]]
    registry.add_model(name="Foo", model=ValueModel())
    assert observer.get_and_clear_changed_events() == [["Foo"]]
    registry.add_model(name="Bar", model=ValueModel())
    assert observer.get_and_clear_changed_events() == [["Foo", "Bar"]]
