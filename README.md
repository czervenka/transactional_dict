# Pure Python transactional dict

## Examples

This module makes it easy to use transactional updates to Python dict.

### Basic usage as context manager

```python
from transactional_dict import transaction
data = {"vegetable": "apple"}

with transaction(data) as data_copy:
    data_copy["vegetable"] = "carrot"
    print(data["vegetable"])
    print(data_copy["vegetable"])
print(data["vegetable"])
```
```
apple
carrot
carrot
```

### Exceptions aborts transaction

```python
data = {"nested": {"vegetable": "apple"}}
try:
    with transaction(data) as data_copy:
        data_copy["nested"]["vegetable"] = "carrot"
        print(data["nested"]["vegetable"])
        print(data_copy["nested"]["vegetable"])
        raise Exception()
except Exception:
    print(data["nested"]["vegetable"])
```
```
apple
carrot
apple
```

### The nested dicts are transacted as well

```python
data = {"vegetable": "apple"}
with transaction(data) as data_copy:
    data_copy["vegetable"] = "carrot"
    print(data["vegetable"])
    print(data_copy["vegetable"])
print(data["vegetable"])
```
```
apple
carrot
carrot
```

See doctests in [transactional_dict.py](transactional_dict.py) for more information and examples.

## Running tests

```sh
poetry install --dev
python3 transactional_dict
```
