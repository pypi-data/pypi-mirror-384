# eamin Quick Start Guide

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install eamin

# Or install in development mode
cd /home/cc/eamin-package
pip install -e .

# Or use directly in Python (without installation)
import sys
sys.path.insert(0, '/home/cc')
import eamin
```

### Basic Usage

```python
import eamin

# Simplest usage
eamin.hello_world(print)  # Output: hello_world
eamin.printout(print)     # Output: printout

# Works with any attribute!
eamin.anything_you_want(print)  # Output: anything_you_want
```

## 💡 Creative Uses

### 1. Get Attribute Name as String

```python
name = eamin.variable_name(lambda x: x)
print(name)  # "variable_name"
```

### 2. Custom Output Function

```python
def custom(text):
    print(f"✨ {text} ✨")

eamin.magic(custom)  # Output: ✨ magic ✨
```

### 3. Transform and Process

```python
# Convert to uppercase
upper = eamin.hello(lambda x: x.upper())  # "HELLO"

# Get length
length = eamin.long_name(lambda x: len(x))  # 9

# Reverse
reversed_text = eamin.test(lambda x: x[::-1])  # "tset"
```

### 4. Batch Generate Configuration Keys

```python
keys = ['database', 'cache', 'api']
config = {k: getattr(eamin, k)(lambda x: x) for k in keys}
# {'database': 'database', 'cache': 'cache', 'api': 'api'}
```

### 5. Multilingual Support

```python
eamin.hello(print)      # Output: hello
eamin.你好(print)       # Output: 你好
eamin.مرحبا(print)      # Output: مرحبا
```

## 🎯 Run Examples

```bash
# Run basic tests
python /home/cc/eamin-package/test_eamin.py

# Run more examples
python /home/cc/eamin-package/examples.py
```

## 🔧 How It Works

`eamin` uses Python's module system and the `__getattr__` magic method:

1. Replaces the module object with a custom class instance
2. Intercepts all attribute access
3. Returns a closure that accepts a function
4. Calls that function with the attribute name

Core code:

```python
class EaminModule:
    def __getattr__(self, name):
        def magic_func(func=print):
            return func(name)
        return magic_func

sys.modules[__name__] = EaminModule()
```

## 🎪 Why Is This Fun?

- 🎨 Dynamic behavior: No need to predefine any attributes
- 🔮 Magical feeling: Looks like magic
- 📚 Learning value: Demonstrates Python's metaprogramming capabilities
- 🎮 Playability: Can create various interesting uses

## ⚠️ Notes

This package is mainly for:
- Learning Python metaprogramming
- Entertainment and experimentation
- Demonstrating Python's flexibility

Not recommended for production critical code.

## 📝 License

MIT License - Free to use!
