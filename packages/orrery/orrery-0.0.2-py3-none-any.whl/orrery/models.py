"""Classes for implementing Models for storage of data with automated value
change callbacks"""

import copy
from enum import Enum
from typing import TypeVar, Generic, Type, Optional

from orrery.observable import Observable, Event

T = TypeVar('T')


class Model(Observable):
    """Base class for storing values"""
    EVENT_VALUE_CHANGED = Event("valueChanged")
    EVENT_INVALIDATED = Event("Invalidated")

    @property
    def value(self):
        """Return value of model"""
        if not self.initialised():
            raise RuntimeError('Value fetched before initialisation')
        return self._get_value()

    @value.setter
    def value(self, value):
        """Change value of model"""
        if not self.initialised() or not self.compare(value):
            self._set_value(value)
            self.notify(self.EVENT_INVALIDATED, model=self)
            self.notify(self.EVENT_VALUE_CHANGED, model=self)

    def add_value_changed_listener(self, callback, **kwargs):
        """Add an observer to listen for changes to this model's value'"""
        callback_id = self.add_observer(
            event=Model.EVENT_VALUE_CHANGED, callback=callback, **kwargs)

        if self.initialised():
            # Trigger an immediate callback with the current model value
            callback(model=self, **kwargs)

        return callback_id

    def add_invalidated_listener(self, callback, **kwargs):
        """Add an observer to listen to notifications that this model has
        become invalid"""
        callback_id = self.add_observer(
            event=Model.EVENT_INVALIDATED, callback=callback, **kwargs)

        return callback_id

    def remove_value_changed_listener(self, callback_id):
        """Remove a previously added observer for value changed events"""
        self.remove_observer(
            event=Model.EVENT_VALUE_CHANGED, callback_id=callback_id)

    def remove_invalidated_listener(self, callback_id):
        """Remove a previously added observer for invalidated events"""
        self.remove_observer(
            event=Model.EVENT_INVALIDATED, callback_id=callback_id)

    def has_value(self) -> bool:
        """Return True if the model has valid value """
        return self.initialised() and self.value is not None

    def initialised(self) -> bool:
        """Return True if the model value has been set (even if set to None)"""
        raise NotImplementedError

    def initialise(self, error_if_already_initialised: bool = True):
        """Set model to its default state"""
        raise NotImplementedError

    def compare(self, value) -> bool:
        """Return True if the model value is equal to the specified value"""
        return self.value == value

    def _get_value(self):
        raise NotImplementedError

    def _set_value(self, value):
        raise NotImplementedError

    def from_yaml(self, value):
        """Set the model value using the value reprentation returned from the
        YAML parser"""
        raise NotImplementedError

    def to_yaml(self):
        """Return a representation of the model value suitable for storing in
        YAML"""
        raise NotImplementedError


class NotInitialised:
    """Special class for indicating a value should be non-initialised"""


NOT_INITIALISED = NotInitialised()


class ValueModel(Model):
    """A simple model holding a single object value. This model does not depend
     on other models and its value only changes when set explicitly"""

    def __init__(self, default=None, value=NOT_INITIALISED):
        super().__init__()
        self._default = default
        self._set_value(value)

    def initialised(self) -> bool:
        return self._initialised

    def initialise(self, error_if_already_initialised: bool = True):
        if self.initialised():
            if error_if_already_initialised:
                raise RuntimeError('Model value has already been initialised')
        else:
            self.value = copy.deepcopy(self._default)

    def _get_value(self):
        # Return a deep copy of the object - this is necessary to ensure that
        # the model value can't be modified without triggering the dependency
        # updates
        return copy.deepcopy(self._value)

    def _set_value(self, value):
        # ValueModel makes a deep copy of the provided object
        self._value = copy.deepcopy(value)
        self._initialised = value != NOT_INITIALISED

    def from_yaml(self, value):
        self.value = value

    def to_yaml(self):
        return self._value


class ConstantModel(ValueModel):
    """A simple model holding a single fixed object value. It is the same as
    a ValueModel but does not permit the value to the changed"""

    @Model.value.setter
    def value(self, value):
        if self.initialised():
            raise ValueError('The value of a ConstantModel cannot be changed')
        else:
            super(ConstantModel, self.__class__).value.fset(self, value)


class ClassModel(ValueModel):
    """A model wrapping an instance. No copy will be made when getting or
    setting the value; the value refers to the original object. This is
    intended for storing a runtime instance of a class and is not intended to
    be serialisable"""

    def _get_value(self):
        return self._value

    def _set_value(self, value):
        # A ClassModel does not make a deep copy
        self._value = value
        self._initialised = True

    def from_yaml(self, value):
        raise RuntimeError("ClassModel does not support serialisation")

    def to_yaml(self):
        raise RuntimeError("ClassModel does not support serialisation")


class EnumValueModel(ValueModel, Generic[T]):
    """Model for holding an Enumeration. Ensures safe encoding/decoding to
    str when storing in YAML"""

    def __init__(self, enum_type: Type[T], default=None):
        super().__init__(default=default)
        self.enum_type = enum_type

    def from_yaml(self, value):
        self.value = self.enum_type[value]

    def to_yaml(self):
        return self._value.name


class DependentModel(Model):
    """A Model whose value depends on one or more other models. The Model's
    value is automatically recalculated when any of the dependencies change"""

    def __init__(self, dependencies: Optional[list[Model]] = None,
                 name: Optional[str] = None):
        super().__init__()
        self.name = name
        self._cached_value = None
        self._cached_value_is_valid = False
        self._dependencies = dependencies
        for dependency in dependencies:
            dependency.add_observer(event=Model.EVENT_VALUE_CHANGED,
                                    callback=self._dependency_changed)
            dependency.add_observer(event=Model.EVENT_INVALIDATED,
                                    callback=self._dependency_invalidated)

    def initialise(self, error_if_already_initialised: bool = True):
        pass

    def initialised(self) -> bool:
        for dependency in self._dependencies:
            if not dependency.initialised():
                return False
        return True

    def _dependency_invalidated(self, model):  # pylint:disable=unused-argument
        """Callback when any dependency gives an invalidated event"""
        self._cached_value_is_valid = False
        self.notify(self.EVENT_INVALIDATED, model=self)

    def _dependency_changed(self, model):  # pylint:disable=unused-argument
        """Callback when any dependency gives a changed event"""
        if self.initialised():
            if not self._cached_value_is_valid:
                self._run_and_update_cached_value()

    def get_model_result(self):
        """Override this method to compute the value of the dependent model"""
        raise NotImplementedError

    def set_model_result(self):
        """Override this method to set the value of the dependent model"""
        raise NotImplementedError

    def _run_and_update_cached_value(self):
        self._cached_value = self.get_model_result()
        self._cached_value_is_valid = True
        self.notify(self.EVENT_VALUE_CHANGED, model=self)

    def _get_value(self):
        if not self._cached_value_is_valid:
            self._run_and_update_cached_value()
        return self._cached_value

    def _set_value(self, value):
        self.set_model_result(value)

    def from_yaml(self, value):
        raise RuntimeError("DependentModel does not support serialisation")

    def to_yaml(self):
        raise RuntimeError("DependentModel does not support serialisation")


class IndirectDependentModel(Model):
    """A model which reflects the value of a child model """

    def __init__(self, parent_model: Model = None, model_name: str = None):
        super().__init__()
        self.parent_model = parent_model
        self.model_name = model_name
        self._model_callback_id = None
        self._model_invalidation_callback_id = None
        self._last_parent = None
        parent_model.add_value_changed_listener(
            callback=self._parent_value_changed)
        parent_model.add_invalidated_listener(
            callback=self._parent_value_invalidated)

    def initialise(self, error_if_already_initialised: bool = True):
        pass

    def initialised(self) -> bool:
        return self.parent_model.initialised() and \
               self.parent_model.value.models.get_model(
                   self.model_name).initialised()

    def _parent_value_invalidated(self, model):  # pylint:disable=unused-argument
        if self._model_callback_id:
            self._last_parent.models.remove_observer(
                name=self.model_name,
                callback_id=self._model_callback_id
            )
            self._last_parent.models.remove_observer(
                name=self.model_name,
                callback_id=self._model_invalidation_callback_id
            )
        self._last_parent = self.parent_model.value
        self._model_callback_id = self._last_parent.models.add_observer(
            name=self.model_name,
            callback=self._model_value_changed
        )
        self._model_invalidation_callback_id = self._last_parent.models.add_observer(
            name=self.model_name,
            callback=self._model_value_invalidated
        )
        self.notify(self.EVENT_INVALIDATED, model=self)

    def _parent_value_changed(self, model):  # pylint:disable=unused-argument
        self.notify(self.EVENT_VALUE_CHANGED, model=self)

    def _model_value_changed(self, model):  # pylint:disable=unused-argument
        self.notify(self.EVENT_VALUE_CHANGED, model=self)

    def _model_value_invalidated(self, model):  # pylint:disable=unused-argument
        self.notify(self.EVENT_INVALIDATED, model=self)

    def _set_value(self, value):
        raise NotImplementedError

    def _get_value(self):
        parent = self.parent_model.value
        return parent.models.get_model(self.model_name).value


class ModelRegistry:
    """Holds a list of named Models"""

    def __init__(self):
        super().__init__()
        self._models: dict[str, Model] = {}
        self._model_names = ValueModel(value=[])

    def add_model(self,
                  name: str,
                  model: Optional[Model] = None) -> Model:
        """Add a model to this registry with the specified name

        Args:
            name: Name used to reference the model in the registry
            model: The Model to add. If a model is not specified, a new
                   ValueModel will be created
        Returns:
            the Model that was added to the registry
        """
        if name in self._models:
            raise ValueError(
                f"A model named {name} already exists in this registry")
        if not model:
            model = ValueModel()
        self._models[name] = model
        self._model_names.value = list(self._models.keys())
        return model

    def get_model(self, name: str) -> Model:
        """Return the model in this registry with the specified name"""
        if isinstance(name, Enum):
            name = name.name
        return self._models[name]

    def models(self) -> dict[str, Model]:
        """Return dictionary of registered model names to models"""
        return self._models

    def model_names(self) -> Model:
        """Return a Model containing a list of current model names"""
        return self._model_names

    def add_observer(self, name: str, callback, **kwargs):
        """Add observer to listen to changed callback of the specified Model"""
        return self.get_model(name=name).add_value_changed_listener(
            callback=callback, **kwargs)

    def remove_observer(self, name: str, callback_id):
        """Remove previously added value changed observer"""
        self.get_model(name=name).\
            remove_value_changed_listener(callback_id=callback_id)

    def add_invalidated_observer(self, name: str, callback, **kwargs):
        """Add observer to listen to invalidated callback of the specified
        Model"""
        return self.get_model(name=name).add_invalidated_listener(
            callback=callback, **kwargs)

    def remove_invalidated_observer(self, name: str, callback_id):
        """Remove previously added invalidated observer"""
        self.get_model(name=name).\
            remove_invalidated_listener(callback_id=callback_id)


class GlobalModelRegistry(ModelRegistry):
    """A ModelRegistry where Models can be added with an additional identifying
    prefix, allowing multiple Models of the same name to be added. An example
    use might be an application which has multiple windows open, where each
    window has its own set of Models (which might be stored in a ModelRegistry).
    The prefix allows you to distinguish Models for different windows while
    still maintaining a single global list of Models
    """

    def add_model(self,
                  name: str,
                  model: Optional[Model] = None,
                  prefix: Optional[str] = None
                  ):
        """Add a model to this registry with the specified name

        Args:
            name: Name used to reference the model in the registry
            prefix: Optional prefix which to be added to the model name
            model: The Model to add. If a model is not specified, a new
                   ValueModel will be created
        Returns:
            the Model that was added to the registry
        """
        return super().add_model(name=self._key(prefix=prefix, name=name),
                                 model=model)

    def get_model(self, name: str, prefix: Optional[str] = None) -> Model:
        """Return the model in this registry with the specified name"""
        return super().get_model(name=self._key(prefix=prefix, name=name))

    def register_all(self, registry, prefix: Optional[str] = None):
        """Register models contained in another registry with this registry

        Args:
            registry: Registry containing the source models
            prefix: Optional prefix which will be added to each model name
                    when they are added to this registry
        """
        for name, model in registry.models().items():
            self.add_model(name=name, prefix=prefix, model=model)

    def add_observer(self, name: str, callback, prefix: Optional[str] = None,
                     **kwargs):
        return super().add_observer(name=self._key(prefix=prefix, name=name),
                                    callback=callback, **kwargs)

    def remove_observer(self, name: str, callback_id,
                        prefix: Optional[str] = None):
        super().remove_observer(
            name=self._key(prefix=prefix, name=name), callback_id=callback_id)

    @staticmethod
    def _key(prefix: str, name: str):
        return prefix + '.' + name if prefix else name
