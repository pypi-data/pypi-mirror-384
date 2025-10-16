# orrery

[![PyPI - Version](https://img.shields.io/pypi/v/orrery)](https://pypi.org/project/pyreporting/)
[![License](https://img.shields.io/github/license/CodeChoreography/orrery)](https://github.com/CodeChoreography/orrery/blob/main/LICENSE)
[![Test](https://github.com/CodeChoreography/orrery/actions/workflows/test.yml/badge.svg)](https://github.com/CodeChoreography/orrery/actions/workflows/test.yml)
[![lint](https://github.com/CodeChoreography/orrery/actions/workflows/lint.yml/badge.svg)](https://github.com/CodeChoreography/orrery/actions/workflows/lint.yml)
[![Publish](https://github.com/CodeChoreography/orrery/actions/workflows/publish.yml/badge.svg)](https://github.com/CodeChoreography/orrery/actions/workflows/publish.yml)

A framework for supporting MVC and observer patterns in Python

## Example usage

Create a basic model to hold a simple value
```python
from orrery.models import ValueModel
my_model = ValueModel()
```
Define a class to listen to callbacks
```python
class CallbackClass:
    def value_changed(self, model):
        print(f"New value: {model.value}")

callback_class = CallbackClass()
```
_Note: at present the callback needs to be a class function_

Add an observer to listed to changes to the model:
```python
my_model.add_value_changed_listener(callback_class.value_changed)
```

Change the value of the model:
```python
my_model.value = "Foo"
```

read the value of a model:
```python
current_value = model.value
print(f"Current model value is {current_value}")
```

### Initial values
Models start in an uninitialised state. When a value is set, the model is
initialised. You can use the Model's `has_value()` method to determine if the
Model has been initialised
```python
my_model = ValueModel()
print(my_model.has_value())
my_model.value = "Foo"
print(my_model.has_value())
```


If you want to create a model with 
an initial value, use:
```python
my_model = ValueModel(value="Foo")
```
When you add an observer to an unititialised Model, the observer will 
receive a callback when the Model is set. If you add an observer to a Model 
which already has a value, the observer will immediately receive a callback with
the value.

This ensures that te behaviour of your application is the same 
regardless of whether you set the values of the Models before or after you add
the observers.

### Dependent models

A dependent model is one that changes when other models change.
You create a dependent model by subclassing `DependentModel` and defining a
method `get_model_results` which computes the model value.
```python
from orrery.models import Model, DependentModel

class SumModel(DependentModel):
    def __init__(self, model_a: Model, model_b: Model):
        self.model_a = model_a
        self.model_b = model_b
        super().__init__([model_a, model_b])

    def get_model_result(self):
        return self.model_a.value + self.model_b.value

model_a = ValueModel(value=2)
model_b = ValueModel(value=3)
sum_model = SumModel(model_a, model_b)

print(sum_model.value)
```

The key use of a DependentModel is that it will _automatically_ recompute its
value and fire value changed events whenever any of its dependencies change.

For example, if we use the CallbackClass we defined previously to listen for
changes in our SumModel clas:

```python
sum_model.add_value_changed_listener(callback_class.value_changed)
model_a.value = 8
```

We see that the change in the value of model_a automatically triggers an 
update to the SumModel.

### Delayed initialisation and default values

`ValueModels` can also be given default values on creation. These are used for
delayed initialisation. You may not know the required value of a ValueModel at 
the time it is created (for example, if the values are read in later from a 
configuration file or web API) but you can set a default value:
```python
my_model = ValueModel(default="Foo")
print(my_model.value)
```
Later, after your code has had a chance to optionally set the initial model 
value, you can call the Model's `initialise()` method:   
```python
my_model.initialise()
print(my_model.value)
```
If the value has not been set, the model will then take on the default value.

Why is this different from setting an initial value? Because an initial value
will cause an immediate callback with the initial value, and then a second 
callback when the delayed initialisation occurs. Using a default value, the
initial callback only occurs once. This avoids the GUI flickering you can see 
with applications using other frameworks. 

## Source code
- [GitHub](https://github.com/CodeChoreography/orrery)

## License

See [license file](https://github.com/CodeChoreography/orrery/blob/main/LICENSE)

## Copyright

&copy; 2025 Code Choreography Limited
