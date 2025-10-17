# react-tk

React-tk is an experimental framework building Tkinter UIs using React principles. It uses a shadow UI reconciliation system, tracking changes in props and context to determine what needs to be updated in the actual Tkinter widgets.

Features and limitations:

- Full type hints for everything, like props
- Runtime validation for a lot of things, like props
- Narrow interface, you only need a few key imports.
- Most similar to older-style React with class components.
- ShadowNodes use an extensible property schema system using TypedDicts.

- Two building blocks: ShadowNode and Component. These are "renderables"
- ShadowNode are provided by the library and represent Tk UI elements.
- ShadowNodes are equivalent to React-provided HTML components.
- ShadowNode is subclassed by different UI nodes.
- Components are user-defined abstractions that produce other renderables, one or more.
- Components are not used internally by the framework.
- Components act via their `render()` method.

- There is no JSX equivalent. UI elements are described by Python objects.
- These objects have props passed via their constructors.
- User-defined Components are expected to be dataclasses with `kw_only=True`
- The children of a component or a ShadowNode are specified with square brackets `[...]`
- You can access the children of a component using `self.KIDS`.

- Components don't support state, only props and context.
- Since there is no state, all the `render()` methods are called with every change.

- ShadowNodes sometimes accept several kinds of props.
- For example, Widgets accept base props and layout manager props.
- This works using a separate method you need to call. See below.

## Install

```bash
poetry add react-tk
```

## Tk Nodes / Widgets / Resources

Currently only a handful of UI elements are supported:

- Label
- Window
- Frame

## Step by step

Let's take a look at building a very simple UI step by step.

### Importing

First, let's import the stuff we'll need:

```python
from react_tk import Window, WindowRoot, Widget, Label, Component
```

1. The `WindowRoot` which is used to mount components into Tk.
2. The `Window` node that represents a window.
3. The `Label` node that represents a Label.
4. The `Component` base class.
5. The `Widget` node we use to express Widget components.

### Define a custom widget component

We typically define Components as dataclasses with `kw_only=True`. This Component should have a `render` method that returns other components or ShadowNode objects, such as those representing various Tk elements.

In this case, our component returns a single `Label`.

The Label's props are divided into the base props and the layout manager props. To set to layout manager props, you need to call the appropriate method on the Widget ShadowNode.

Right now only `Pack` is supported.

```python
Label().Pack(
    ipadx=20,
    fill="both"
)
```

Return this from your component:

```python
@dataclass(kw_only=True)
class TextComponent(Component[Widget]):
    text: str

    def render(self):
        return Label(
            text=self.text,
            background="#000001",
            foreground="#ffffff",
            font=Font(family="Arial", size=20, style="bold"),
        ).Pack(ipadx=20, ipady=15, fill="both")
```

Note that you can just subclass `Component` and not `Component[X]`. It just adds a bit of type checking. There is no difference between `Component[Widget]` and `Component[Window]` during runtime.

### Define a Window component

Widgets are must be contained in Windows. Windows aren't contained in anything, as we'll see. We need to create a component that returns Window nodes.

To have our previous component be contained in a Window node, we create the Window node and then use `[...]` square brackets to specify children.

```py
Window()[
    TextComponent(text="abc")
]
```

Now we create the Window component. We'll use context, which works kind of like in React. It's passed down all the components. You can access it from a component using `self.ctx`.

```py
@dataclass(kw_only=True)
class WindowComponent(Component[Window]):
    def render(self):
        return Window(topmost=True, background="black", alpha=85).Geometry(
            width=500, height=500, x=500, y=500, anchor_point="lt"
        )[TextComponent(text=self.ctx.text)]
```

1. Inherent Window props are set via the constructor.
2. Window Geometry is kind of like a layout manager and is set separately.

#### Using a single component

You can also just use a single Window component. you don't have to use a widget component at all. However, doing so is less readable.

```py
@dataclass(kw_only=True)
class WindowComponent(Component[Window]):
    def render(self):
        displayed_text = self.ctx.text
        lbl = Label(
            text=displayed_text,
            background="#000001",
            foreground="#ffffff",
            font=Font(family="Arial", size=20, style="bold"),
        ).Pack(ipadx=20, ipady=15, fill="both")
        return Window(topmost=True, background="black", alpha=85).Geometry(
            width=500, height=500, x=500, y=500, anchor_point="lt"
        )[lbl]
```

### Create a WindowRoot

Windows aren't contained in anything. Instead they're "mounted" on the WindowRoot. To do that, we create a `WindowRoot` around a specific component instance. We can pass it kwargs to initialize its context.

Once the WindowRoot is constructed, the UI will immediately mount. However, the context starts out as an empty object.

To add attributes to it, we can pass them as kwargs to the `WindowRoot` constructor. This part is untyped.

```py
ui_root = WindowRoot(WindowComponent(), text="Hello World!")
```

After this, we can modify the context any time by "calling" the `WindowRoot` with kwargs, like this:

```py
ui_root(text="Hello again!")
```

This will regenerate the component tree and reconcile any changes with the mounted UI.

## Technical stuff
