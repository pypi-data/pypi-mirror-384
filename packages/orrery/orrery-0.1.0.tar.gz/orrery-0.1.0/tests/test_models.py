from src.orrery.models import DependentModel, Model, ModelRegistry, ValueModel


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


def test_dependent_model():
    model_1 = ValueModel()
    model_2 = ValueModel()
    get_result_fn = lambda dependencies: dependencies["model_1"].value + dependencies["model_2"].value
    dm = DependentModel(get_result=get_result_fn, dependencies=dict(model_1=model_1, model_2=model_2))
    assert not dm.initialised()
    model_1.value = 2
    model_2.value = 3
    assert dm.initialised()
    assert dm.value == 5


def test_dependent_model_subclass():
    class DependentModelSubclass(DependentModel):
        def get_model_result(self):
            return self.dependencies["model_1"].value + self.dependencies["model_2"].value

    model_1 = ValueModel()
    model_2 = ValueModel()
    dm = DependentModelSubclass(dependencies=dict(model_1=model_1, model_2=model_2))
    assert not dm.initialised()
    model_1.value = 2
    model_2.value = 3
    assert dm.initialised()
    assert dm.value == 5

