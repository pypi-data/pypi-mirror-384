# interface-py

**interface-py** is a lightweight Python package for defining **interfaces** and **concrete implementations** with enforced contracts.  
It ensures that concrete classes implement all required methods, properties, and **fields**, including validation for empty or invalid property getters.

---

## Features

- Define **interfaces** using the `@interface` decorator.
- Enforce that concrete classes implement all interface methods, fields, and properties.
- Detects and enforces rules for **empty**, **explicit**, and **invalid getters/setters**.
- Support for **fields** with four declaration styles:
  1. With annotation only → `x: int`
  2. With annotation + `...` → `y: float = ...`
  3. Without annotation + `...` → `z = ...`
  4. With direct type assignment → `DataModel = dict` or any other type/class
- Ensures that **property getters** defined explicitly in interfaces always raise an error.
- Allows defining properties in interfaces with empty bodies (`...`, `pass`, or docstring-only`).
- Enforce **getter**, **setter**, and **deleter** implementation rules for properties.
- Supports **multi-level interface hierarchies** with automatic **contract aggregation**.
- Prevents runtime errors from missing implementations.
- Works alongside Python's built-in ABCs.

---

## Installation

```bash
pip install interface-py
```

---

## Usage

### Defining an Interface

```python
from interface_py import interface

@interface
class HumanInterface:
    # field definitions
    name: str
    age: int = ...
    nickname = ...
    DataModel = dict  # direct type assignment
    
    def speak(self): ...
    
    @property
    def rank(self): ...
    
    @rank.setter
    def rank(self, value): ...
```

- Property definitions in interfaces may have an **empty body** (`...`, `pass`, or docstring-only`).
- However, **explicit getters** (e.g. `@rank.getter`) are **not allowed** in interfaces, even if their body is empty.

---

### Multi-level Interface Example

```python
from interface_py import interface, concrete

@interface
class MilitaryHumanInterface(HumanInterface):
    def march(self): ...

@concrete
class Soldier(MilitaryHumanInterface):
    name: str = "John"
    age: int = 25
    nickname = "Eagle"
    
    def speak(self):
        print("Reporting for duty!")

    def march(self):
        print("Marching!")

    @property
    def rank(self):
        return self._rank
    
    @rank.setter
    def rank(self, value):
        self._rank = value
```

- `MilitaryHumanInterface` **extends** `HumanInterface`.  
- `Soldier` **implements all required methods, fields, and properties** from both interfaces automatically.  
- Multi-level inheritance automatically merges all parent interface contracts.

---

## Field Enforcement Examples

```python
from interface_py import interface, concrete

@interface
class ExampleInterface:
    x: int              # only annotation
    y: float = ...      # annotation with ellipsis
    z = ...             # plain ellipsis
    DataModel = dict    # direct type assignment


# ✅ Correct implementation
@concrete
class GoodImpl(ExampleInterface):
    x: int = 10
    y: float = 3.14
    z = "hello"
    DataModel = dict


# ❌ Incorrect implementation
@concrete
class BadImpl(ExampleInterface):
    x: str = "oops"   # wrong type (expected int)
    # y missing → TypeError
    z = ...           # not allowed to keep ellipsis
    DataModel = list   # wrong type assignment
```

---

## Method Enforcement Rules

In **interfaces**, all methods must have an **empty body**.  
Empty bodies are recognized as:
- `pass`
- `...`
- docstring-only functions (for example, a function that only contains a string literal as its body)

In **concrete classes**, all methods must have a **non-empty body**.  
Methods defined with only `pass`, `...`, or docstring-only are considered **unimplemented** and raise a `TypeError`.

---

## Property Enforcement Rules

- A property can be declared in an interface as:

  ```python
  @property
  def data(self): ...
  ```

- The above is valid and treated as a contract placeholder.  
- However, the following is **invalid** and raises an error:

  ```python
  @property
  def data(self):
      pass

  @data.getter
  def data(self):
      ...
  ```

- Concrete classes **must** implement the getter, and if defined in the interface, also the setter and deleter.

---

## Validation

- Instantiating a concrete class that **does not implement all interface methods/fields/properties** raises a `TypeError`.
- Ensures consistent **interface contracts** across your project.
- The decorator `@interface` automatically enforces the interface behavior without requiring any base class.
- The decorator `@concrete` ensures that at least one parent of the concrete class is an interface.

---

## Why Use interface-py?

- Provides **contract enforcement** in dynamically typed Python.
- Detects incomplete or empty implementations early.
- Helps structure large codebases with clear **interface and implementation separation**.
- Avoids runtime errors from missing or placeholder methods.
- Enforces correctness while remaining Pythonic.

---

## License

MIT License
