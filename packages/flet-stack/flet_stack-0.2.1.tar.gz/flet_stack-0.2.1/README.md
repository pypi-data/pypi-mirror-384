# flet-stack

**Component-based routing with automatic view stacking for Flet applications.**

[![PyPI version](https://badge.fury.io/py/flet-stack.svg)](https://badge.fury.io/py/flet-stack)
[![Python versions](https://img.shields.io/pypi/pyversions/flet-stack.svg)](https://pypi.org/project/flet-stack/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/flet-stack?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/flet-stack)


## Features

- 🎯 **Decorator-based routing** - Clean, intuitive `@view()` decorator for route definitions
- 🔄 **Observable state management** - Built-in state management using `@ft.observable` dataclasses
- ⚡ **Async support** - Handle async data loading with automatic loading indicators
- 🎨 **URL parameters** - Extract parameters from routes like `/user/{id}`
- 🧩 **Component-based architecture** - Uses Flet's modern `@ft.component` pattern
- 🚀 **Simple setup** - Just call `page.render_views(FletStack)` in your app
- 🔐 **Custom initial routes** - Start your app at any route

## Requirements

- Python 3.9+
- Flet >= 0.70.0.dev6281

## Installation

### From PyPI

```bash
pip install flet-stack
```

### From GitHub

```bash
pip install git+https://github.com/fasilwdr/flet-stack.git
```

### Install Specific Version

```bash
pip install git+https://github.com/fasilwdr/flet-stack.git@v0.2.1
```

### From Source

```bash
git clone https://github.com/fasilwdr/flet-stack.git
cd flet-stack
pip install .
```

## Quick Start

```python
import flet as ft
from flet_stack import view, FletStack
import asyncio

# Define your routes with the @view decorator
@view("/")
@ft.component
def home_view():
    return [
        ft.Text("Home Page", size=30),
        ft.Button(
            "Go to Profile",
            on_click=lambda _: asyncio.create_task(
                ft.context.page.push_route("/profile")
            )
        ),
    ]

@view("/profile", appbar=ft.AppBar())
@ft.component
def profile_view():
    return [
        ft.Text("Profile Page", size=30),
    ]

# Run your app
ft.run(lambda page: page.render_views(FletStack))
```

That's it! The routing is automatically handled by FletStack.

## Advanced Usage

### URL Parameters

Extract parameters from your routes:

```python
@view("/user/{user_id}")
@ft.component
def user_view(user_id):
    return [
        ft.Text(f"User Profile: {user_id}", size=30),
    ]
```

### State Management

Use observable dataclasses to manage component state:

```python
from dataclasses import dataclass

@ft.observable
@dataclass
class CounterState:
    count: int = 0
    
    def increment(self, e):
        self.count += 1
    
    def decrement(self, e):
        self.count -= 1

@view("/counter", state_class=CounterState, appbar=ft.AppBar())
@ft.component
def counter_view(state):
    return [
        ft.Text(f"Count: {state.count}", size=30),
        ft.Row([
            ft.Button("Decrement", on_click=state.decrement),
            ft.Button("Increment", on_click=state.increment),
        ]),
    ]
```

### Async Data Loading

Load data asynchronously before showing your view:

```python
@ft.observable
@dataclass
class UserState:
    user_data: dict = None

async def load_user_data(state, user_id):
    # Simulate API call
    await asyncio.sleep(1)
    state.user_data = {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }

@view("/user/{user_id}", state_class=UserState, on_load=load_user_data)
@ft.component
def user_detail_view(state, user_id):    
    return [
        ft.Text(f"Name: {state.user_data['name']}", size=20),
        ft.Text(f"Email: {state.user_data['email']}", size=16),
        ft.Text(f"ID: {state.user_data['id']}", size=16),
    ]
```

While loading, a progress indicator is automatically displayed.

### Sync Data Loading

You can also use synchronous loading functions:

```python
def load_item_info(state, category, item_id, page):
    """Sync data loading with access to page object"""
    state.info = {
        "category": category.capitalize(),
        "item_id": item_id,
        "name": f"{category.capitalize()} Item #{item_id}",
        "price": f"${int(item_id) * 10}.99"
    }

@view(
    "/category/{category}/item/{item_id}",
    state_class=ItemState,
    on_load=load_item_info
)
@ft.component
def item_view(state, category, item_id):
    return [
        ft.Text(f"{state.info['name']}", size=20),
        ft.Text(f"Price: {state.info['price']}", size=18),
    ]
```

### View Configuration

Pass additional Flet view properties:

```python
@view(
    "/settings",
    appbar=ft.AppBar(title=ft.Text("Settings")),
    bgcolor=ft.Colors.BLUE_GREY_50,
    padding=20,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    vertical_alignment=ft.MainAxisAlignment.CENTER,
)
@ft.component
def settings_view():
    return [ft.Text("Settings", size=30)]
```

### Multiple URL Parameters

Handle routes with multiple parameters:

```python
@view("/category/{category}/item/{item_id}")
@ft.component
def item_view(category, item_id):
    return [
        ft.Text(f"Category: {category}", size=20),
        ft.Text(f"Item ID: {item_id}", size=20),
    ]
```

### Setting Initial Route

You can start your app at any route instead of the default `/`:

```python
def main(page: ft.Page):
    page.title = "My App"
    page.route = "/login"  # Start at login page
    page.render_views(FletStack)

ft.run(main)
```

## API Reference

### `@view` Decorator

```python
@view(route: str, state_class: Type = None, on_load: Optional[Callable] = None, **view_kwargs)
```

- **route**: The route path for this view (e.g., `/`, `/user/{user_id}`)
- **state_class**: Optional dataclass decorated with `@ft.observable` for state management
- **on_load**: Optional function to call before rendering (can be async)
  - Can accept parameters: `state`, `page`, and any URL parameters
- **view_kwargs**: Additional kwargs passed to `ft.View` (e.g., `appbar`, `bgcolor`, `padding`)

### `FletStack` Component

Main component that manages the routing stack and renders views.

```python
# Option 1: Direct render
ft.run(lambda page: page.render_views(FletStack))

# Option 2: In main function
def main(page: ft.Page):
    page.title = "My App"
    page.route = "/login"  # Optional: Set initial route
    page.render_views(FletStack)

ft.run(main)
```

### Navigation

Use `asyncio.create_task` with `ft.context.page.push_route`:

```python
# Navigate to a route
asyncio.create_task(ft.context.page.push_route("/profile"))

# In button click handler
ft.Button(
    "Go to Profile",
    on_click=lambda _: asyncio.create_task(
        ft.context.page.push_route("/profile")
    )
)
```

## Examples

Check the `examples/` directory for more detailed examples:
- `basic_example.py` - Simple routing and navigation
- `advanced_example.py` - State management, async loading, and URL parameters

## How It Works

**flet-stack** provides a `FletStack` component that:

1. Registers all `@view` decorated functions
2. Manages a navigation stack for route changes
3. Handles state management with observable dataclasses
4. Manages async/sync loading with automatic progress indicators
5. Renders views with proper navigation support
6. Supports custom initial routes via `page.route`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built on top of the amazing [Flet](https://docs.flet.dev) framework by Feodor Fitsner.

## Support

If you encounter any issues or have questions:
- Open an issue on [GitHub](https://github.com/fasilwdr/flet-stack/issues)
- Check the [examples](examples/) directory
- Read the [Flet documentation](https://docs.flet.dev)