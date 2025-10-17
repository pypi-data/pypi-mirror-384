# Orrery

[![PyPI - Version](https://img.shields.io/pypi/v/orrery)](https://pypi.org/project/orrery/)
[![License](https://img.shields.io/github/license/CodeChoreography/orrery)](https://github.com/CodeChoreography/orrery/blob/main/LICENSE)
[![Test](https://github.com/CodeChoreography/orrery/actions/workflows/test.yml/badge.svg)](https://github.com/CodeChoreography/orrery/actions/workflows/test.yml)
[![lint](https://github.com/CodeChoreography/orrery/actions/workflows/lint.yml/badge.svg)](https://github.com/CodeChoreography/orrery/actions/workflows/lint.yml)
[![Publish](https://github.com/CodeChoreography/orrery/actions/workflows/publish.yml/badge.svg)](https://github.com/CodeChoreography/orrery/actions/workflows/publish.yml)
[![Docs](https://github.com/CodeChoreography/orrery/actions/workflows/docs.yml/badge.svg)](https://github.com/CodeChoreography/orrery/actions/workflows/docs.yml)

A framework for supporting MVC and observer patterns in Python

## Install
```console
pip install orrery
```

## Update
```console
pip install --update orrery
```

## Documentation

- [Tutorial](https://codechoreography.github.io/orrery/tutorial.html)
- [API reference](https://codechoreography.github.io/orrery/_autosummary/orrery.html)
- [Documentation homepage](https://CodeChoreography.github.io/orrery)

## Quick start

See the [Tutorial](https://codechoreography.github.io/orrery/tutorial.html) page for more information 

Create a model containing an initial value
```python
from orrery.models import ValueModel
my_model = ValueModel(value=5)
```

Read or set the model value
```python
my_model.value = 6
print(my_model.value)
```

Constant model:
```python
from orrery.models import ConstantModel
my_model = ConstantModel(value=5)
```

Model containing a class (i.e. store without copying)

```python
from orrery.models import ClassModel
my_object = MyClass()
my_model = ClassModel(my_object)
```

Check if a model has been given a value:
```python
print(my_model.has_value())
```

Observe changes to a model:
```python
class CallbackClass:
    def value_changed(self, model):
        print(f"New value: {model.value}")

callback_class = CallbackClass()
my_model.add_value_changed_listener(callback_class.value_changed)
```

Create a model which depends on other models:
```python
from orrery.models import DependentModel, ValueModel

model_a = ValueModel(value=2)
model_b = ValueModel(value=3)
sum_model = DependentModel(
    dependencies=dict(model_a=model_a, model_b=model_b), 
    get_result=lambda dependencies: dependencies["model_a"].value + dependencies["model_b"].value
)
print(sum_model.value)
```

## Source code
- [GitHub](https://github.com/CodeChoreography/orrery)

## License

See [license file](https://github.com/CodeChoreography/orrery/blob/main/LICENSE)

## Copyright

&copy; 2025 Code Choreography Limited
