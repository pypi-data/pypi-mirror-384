# pyright: reportArgumentType=false, reportOptionalSubscript=false, reportUnknownArgumentType=false
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    from bs4 import SoupStrainer

import pytest

from weba import (
    Component,
    ComponentAfterRenderError,
    ComponentAsyncError,
    ComponentSrcFileNotFoundError,
    ComponentSrcRequiredError,
    ComponentSrcRootTagNotFoundError,
    ComponentSrcTypeError,
    ComponentTagNotFoundError,
    ComponentTypeError,
    Tag,
    no_tag_context,
    tag,
    ui,
)

if TYPE_CHECKING:
    from pathlib import Path

MonkeyPatch = pytest.MonkeyPatch


def html():
    return ui.raw(
        """<div>
        <!-- #sidebar-nav -->
        <nav class="sidebar">
            <!-- #header-right-wrapper-refresh-data-btn -->
            <div id="foo">
                <div class="hs-tooltip inline-block [--placement:bottom]">
                    <a
                        type="button"
                        class="inline-flex items-center gap-x-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-800 shadow-sm hover:bg-gray-50 disabled:pointer-events-none disabled:opacity-50 dark:border-neutral-700 dark:bg-neutral-900 dark:text-white dark:hover:bg-neutral-800"
                    >
                        <span class="icon-[lucide--refresh-cw] size-4 flex-shrink-0"></span>
                    </a>
                    <span
                        class="hs-tooltip-content invisible absolute z-20 inline-block rounded-lg bg-gray-900 px-2.5 py-1.5 text-xs text-white opacity-0 hs-tooltip-shown:visible hs-tooltip-shown:opacity-100 dark:bg-neutral-700"
                        role="tooltip"
                    >
                        Refresh
                    </span>
                </div>
            </div>
            <!-- End #header-right-wrapper-refresh-data-btn -->
        </nav>
        <main>Content</main>
    </div>
    """
    )


class AppNavComponent(Component):
    src = html()
    src_root_tag = "<!-- #sidebar-nav -->"

    @tag("<!-- #header-right-wrapper-refresh-data-btn -->")
    def header_right_wrapper_refresh_data_btn(self, t: Tag):
        # sourcery skip: no-conditionals-in-tests
        if link := t.select_one("a"):
            link["href"] = "/home"
            link["hx-ext"] = "push-url-w-params"
            link["hx-push-url"] = "false"


class Button(Component):
    src = "<button>Example</button>"

    def __init__(self, msg: str):
        self.msg = msg

    def render(self):
        self.set_message()

    def set_message(self):
        self.string = self.msg


def test_basic_component():
    with ui.div() as container:
        Button("Click me")

    assert str(container) == "<div><button>Click me</button></div>"


def test_component_with_tag_decorator_passing_tag():
    class Button(Component):
        src = "<div><button class='btn'>Example</button></div>"

        def __init__(self, msg: str):
            self.msg = msg

        @tag("button")
        def button_tag(self, t: Tag):
            t.string = self.msg

    with ui.div() as container:
        Button("Submit")

    assert str(container) == '<div><div><button class="btn">Submit</button></div></div>'


def test_component_with_tag_decorator():
    class Button(Component):
        src = "<div><button class='btn'>Example</button></div>"

        def __init__(self, msg: str):
            self.msg = msg

        def render(self):
            self.button_tag.string = "Submit"

        @tag("button")
        def button_tag(self):
            pass

    with ui.div() as container:
        Button("Submit")

    assert str(Button("Foo")) == '<div><button class="btn">Submit</button></div>'
    assert str(container) == '<div><div><button class="btn">Submit</button></div></div>'


def test_component_with_comment_selector():
    class Button(Component):
        src = """<div><!-- #button --><button>Example</button></div>"""

        def __init__(self, msg: str):
            self.msg = msg

        @tag("<!-- #button -->")
        def button_tag(self, t: Tag):
            t.string = self.msg

    with ui.div() as container:
        Button("Delete")

    assert str(container) == "<div><div><!-- #button --><button>Delete</button></div></div>"


@pytest.mark.asyncio
async def test_component_async_context_isolation():
    """Test that components maintain proper context isolation in async tasks."""

    class SimpleCard(Component):
        src = '<div class="card"><!-- #content --><div class="content"></div></div>'

        def __init__(self, title: str, msg: str):
            self.title = title
            self.msg = msg

        @tag("<!-- #content -->")
        def content_tag(self, t: Tag):
            with t:
                ui.h2(self.title)
                ui.p(self.msg)

    async def task1():
        with ui.div() as div1:
            SimpleCard("Task 1", "First paragraph")
            await asyncio.sleep(0.1)  # Simulate some async work
            SimpleCard("Task 1", "Second paragraph")
        return div1

    async def task2():
        with ui.div() as div2:
            SimpleCard("Task 2", "First paragraph!")
            await asyncio.sleep(0.05)  # Different timing to interleave
            SimpleCard("Task 2", "Second paragraph!")
        return div2

    # Run both tasks concurrently
    div1, div2 = await asyncio.gather(task1(), task2())

    # Verify each task maintained its own context
    expected1 = (
        "<div>"
        '<div class="card"><!-- #content --><div class="content"><h2>Task 1</h2><p>First paragraph</p></div></div>'
        '<div class="card"><!-- #content --><div class="content"><h2>Task 1</h2><p>Second paragraph</p></div></div>'
        "</div>"
    )
    expected2 = (
        "<div>"
        '<div class="card"><!-- #content --><div class="content"><h2>Task 2</h2><p>First paragraph!</p></div></div>'
        '<div class="card"><!-- #content --><div class="content"><h2>Task 2</h2><p>Second paragraph!</p></div></div>'
        "</div>"
    )
    assert str(div1) == expected1
    assert str(div2) == expected2


def test_component_from_file():
    class Button(Component):
        src = "./button.html"

        def __init__(self, msg: str):
            self.msg = msg

        def render(self):
            self.string = self.msg

    with ui.div() as container:
        Button("Save")
        Button("Edit")
        Button("Delete")

    assert str(container) == "<div><button>Save</button><button>Edit</button><button>Delete</button></div>"


def test_component_from_relative_path():
    """Test loading component template from a relative path."""

    class SubdirButton(Component):
        src = "./button.html"

    assert str(SubdirButton()) == "<button>Test Button</button>"


def test_component_from_absolute_path():
    """Test loading component template from an absolute path."""
    abs_path = "tests/button.html"

    class AbsoluteButton(Component):
        src = abs_path

    assert str(AbsoluteButton()) == "<button>Test Button</button>"


def test_component_empty():
    class UiList(Component):
        src = "<ul></ul>"

    assert str(UiList()) == "<ul></ul>"


def test_component_with_extract():
    class Button(Component):
        src = "<div><button class='btn'>Example</button></div>"

        def __init__(self, msg: str):
            self.msg = msg

        @tag("button", extract=True)
        def button_tag(self, t: Tag):
            t.string = self.msg

        def add_button(self):
            """Button that adds a button to the component."""
            self.append(self.button_tag)

    button = Button("Extracted")

    assert str(button) == "<div></div>"

    button.add_button()

    assert str(button) == '<div><button class="btn">Extracted</button></div>'


def test_component_with_clear():
    class Button(Component):
        src = "<div><button class='btn'>Example</button></div>"

        @tag("button", clear=True)
        def button_tag(self):
            pass

    assert str(Button()) == '<div><button class="btn"></button></div>'


def test_component_with_extract_and_clear():
    class Button(Component):
        src = "<div><button class='btn'>Example</button></div>"

        @tag("button", extract=True, clear=True)
        def button_tag(self):
            pass

    button = Button()

    assert str(button) == "<div></div>"
    assert str(button.button_tag) == '<button class="btn"></button>'


def test_component_context_manager():
    class List(Component):
        src = "<ul></ul>"

    assert str(List()) == "<ul></ul>"

    with List() as html:
        ui.li("item 1")
        ui.li("item 2")

    assert str(html) == "<ul><li>item 1</li><li>item 2</li></ul>"


def test_multiple_components_in_list():
    class Button(Component):
        src = "<button></button>"

        def __init__(self, msg: str):
            self.msg = msg

        def render(self):
            self.string = self.msg

    with ui.ul() as button_list:
        with ui.li():
            Button("first")

        with ui.li():
            Button("second")
            Button("third")

    expected = "<ul><li><button>first</button></li><li><button>second</button><button>third</button></li></ul>"

    assert str(button_list) == expected


@pytest.mark.asyncio
async def test_async_component_context_isolation():
    """Test that async components maintain proper context isolation."""

    class AsyncCard(Component):
        src = '<div class="card"><h2></h2><p></p></div>'

        def __init__(self, title: str, content: str):
            self.title = title
            self.content = content

        async def render(self):
            await asyncio.sleep(0.01)
            self.header_tag.string = self.title
            self.paragraph_tag.string = self.content

        @tag("h2")
        def header_tag(self):
            pass

        @tag("p")
        def paragraph_tag(self):
            pass

    async def task1():
        with ui.div() as div1:
            await AsyncCard("Task 1 Title", "Task 1 Content")
            await AsyncCard("Task 1 Second", "Task 1 More Content")
        return div1

    async def task2():
        with ui.div() as div2:
            await AsyncCard("Task 2 Title", "Task 2 Content")
            await AsyncCard("Task 2 Second", "Task 2 More Content")
        return div2

    # Run both tasks concurrently
    div1, div2 = await asyncio.gather(task1(), task2())

    # Verify each task maintained its own context
    expected1 = (
        "<div>"
        '<div class="card"><h2>Task 1 Title</h2><p>Task 1 Content</p></div>'
        '<div class="card"><h2>Task 1 Second</h2><p>Task 1 More Content</p></div>'
        "</div>"
    )
    expected2 = (
        "<div>"
        '<div class="card"><h2>Task 2 Title</h2><p>Task 2 Content</p></div>'
        '<div class="card"><h2>Task 2 Second</h2><p>Task 2 More Content</p></div>'
        "</div>"
    )
    assert str(div1) == expected1
    assert str(div2) == expected2


@pytest.mark.asyncio
async def test_async_component():
    class AsyncButton(Component):
        src = "<button></button>"

        def __init__(self, msg: str):
            self.msg = msg

        async def render(self):
            await asyncio.sleep(0.01)  # Simulate an async operation
            self.string = self.msg

    with ui.div() as container:
        await AsyncButton("Async Click Me")
        await AsyncButton("Async Click Me!")

    assert str(container) == "<div><button>Async Click Me</button><button>Async Click Me!</button></div>"


def test_component_with_layout():  # sourcery skip: extract-duplicate-method
    class Layout(Component):
        src = "./layout.html"

        @tag("header")
        def header(self):
            pass

        @tag("main")
        def main(self):
            pass

        @tag("footer")
        def footer(self):
            pass

    layout = Layout()

    assert str(layout).startswith("<!doctype html>")
    assert "<html" in str(layout)
    assert "<header" in str(layout)
    assert "<main" in str(layout)
    assert "<footer" in str(layout)

    with layout as html:
        with html.header:
            ui.nav("navbar")

        with html.main:
            ui.h1("Hello, World!")

        with html.footer:
            ui.span("contact us")

    html_str = str(html)

    assert "<header><nav>navbar</nav></header>" in html_str
    assert "<main><h1>Hello, World!</h1></main>" in html_str
    assert "<footer><span>contact us</span></footer>" in html_str


def test_component_with_layout_and_attributes():
    class Layout(Component):
        src = "./layout.html"

        @tag("header")
        def header(self):
            pass

        @tag("main")
        def main(self):
            pass

        @tag("footer")
        def footer(self):
            pass

    layout = Layout()

    with layout as html:
        # First method: Direct attribute assignment
        header = html.header
        header["class"] = "site-header"
        header["id"] = "top-header"

        with header:
            ui.nav("navbar")

        # Same approach for main
        main = html.main
        main["class"] = "site-main"
        main["id"] = "content"

        with main:
            ui.h1("Hello, World!")

        # And for footer
        footer = html.footer
        footer["class"] = "site-footer"
        footer["id"] = "bottom-footer"

        with footer:
            ui.span("contact us")

    html_str = str(html)

    assert '<header class="site-header" id="top-header"><nav>navbar</nav></header>' in html_str
    assert '<main class="site-main" id="content"><h1>Hello, World!</h1></main>' in html_str
    assert '<footer class="site-footer" id="bottom-footer"><span>contact us</span></footer>' in html_str


def test_component_with_layout_and_attribute_params():
    class Layout(Component):
        src = "./layout.html"

        @tag("header")
        def header(self):
            pass

        @tag("main")
        def main(self):
            pass

        @tag("footer")
        def footer(self):
            pass

    layout = Layout()

    with layout as html:
        # Use the with_attrs method to apply attributes
        with html.header.with_attrs(_class="site-header", id="top-header"):  # pyright: ignore[reportOptionalCall, reportGeneralTypeIssues]
            ui.nav("navbar")

        with html.main.with_attrs(_class="site-main", id="content"):  # pyright: ignore[reportOptionalCall, reportGeneralTypeIssues]
            ui.h1("Hello, World!")

        with html.footer.with_attrs(_class="site-footer", id="bottom-footer"):  # pyright: ignore[reportOptionalCall, reportGeneralTypeIssues]
            ui.span("contact us")

    html_str = str(html)

    assert '<header class="site-header" id="top-header"><nav>navbar</nav></header>' in html_str
    assert '<main class="site-main" id="content"><h1>Hello, World!</h1></main>' in html_str
    assert '<footer class="site-footer" id="bottom-footer"><span>contact us</span></footer>' in html_str


def test_component_with_layout_and_attribute_with_chaining():
    class Layout(Component):
        src = "./layout.html"

        @tag("header")
        def header(self):
            pass

        @tag("main")
        def main(self):
            pass

        @tag("footer")
        def footer(self):
            pass

    with Layout() as html:
        # Use the with_attrs method with chaining - add attributes and immediately use in context
        with html.header(_class="site-header", id="top-header"):  # pyright: ignore[reportOptionalCall, reportGeneralTypeIssues]
            ui.nav("navbar")

        # Test with separated approach to show both styles work
        # 1. Create tag with attributes
        main_with_attrs = html.main.with_attrs(_class="site-main", id="content", data_testid="main-content")  # pyright: ignore[reportOptionalCall]
        # 2. Use in context
        with main_with_attrs:  # pyright: ignore[reportGeneralTypeIssues]
            ui.h1("Hello, World!")

        # Additional attributes can be set directly
        footer = html.footer
        footer["class"] = "site-footer"
        footer["id"] = "bottom-footer"
        footer["data-testid"] = "footer"

        with footer:
            ui.span("contact us")

    html_str = str(html)

    assert '<header class="site-header" id="top-header"><nav>navbar</nav></header>' in html_str
    assert '<main class="site-main" id="content" data_testid="main-content"><h1>Hello, World!</h1></main>' in html_str
    assert (
        '<footer class="site-footer" id="bottom-footer" data-testid="footer"><span>contact us</span></footer>'
        in html_str
    )


def test_component_with_class_append_prepend():
    """Test using class append and prepend functionality with components."""

    class ClassAppendPrependLayout(Component):
        src = "./layout_append_prepend.html"

        @tag("header")
        def header(self):
            pass

        @tag("main")
        def main(self):
            pass

        @tag("footer")
        def footer(self):
            pass

    with ClassAppendPrependLayout() as layout:
        # The header already has a base class="header" in the HTML
        # Test appending classes to existing ones in the HTML
        with layout.header(_append_class="sticky top-0"):
            ui.h1("Page Title")

        # Test both call styles for prepending classes
        # 1. Direct method call with _prepend_class
        with layout.main.with_attrs(_class="content", _prepend_class="flex container"):
            ui.p("Content goes here")

        # 2. Property access and call style
        footer = layout.footer
        # Add a base class first
        footer.with_attrs(_class="footer")
        # Both append and prepend classes in one call
        footer(_append_class="mt-4 pb-2", _prepend_class="grid gap-4")
        # Use in context
        with footer:  # pyright: ignore[reportGeneralTypeIssues]
            ui.p("Footer content")

    # Verify the classes were applied in the correct order
    header_str = str(layout.header)
    main_str = str(layout.main)
    footer_str = str(layout.footer)

    # Check header: initial "header" class + appended "sticky top-0"
    assert 'class="header sticky top-0"' in header_str
    assert "<h1>Page Title</h1>" in header_str

    # Check main: prepended "flex container" + "content"
    assert 'class="flex container content"' in main_str
    assert "<p>Content goes here</p>" in main_str

    # Check footer: prepended "grid gap-4" + "footer" + appended "mt-4 pb-2"
    assert 'class="grid gap-4 footer mt-4 pb-2"' in footer_str
    assert "<p>Footer content</p>" in footer_str


def test_component_with_layout_append_to_body():  # sourcery skip: extract-duplicate-method
    append_text = "<span>one</span><span>two</span>"

    class Layout(Component):
        src = "./layout.html"

        @tag("body")
        def body(self):
            pass

        def render(self):
            self.body.append(ui.raw(append_text))

    assert append_text in str(Layout())
    assert "</>" not in str(Layout())


def test_component_fragment():
    html = "<h1>One</h1><h2>Two</h2><h3>Three</h3>"

    class FragmentComponent(Component):
        src = html

    assert str(FragmentComponent()) == "<h1>One</h1><h2>Two</h2><h3>Three</h3>"


def test_component_layout_appends():
    class Layout(Component):
        src = "./layout.html"

    with Layout() as html:
        ui.h1("Hello, World!")

    assert "Hello, World!" in str(html)


@pytest.mark.asyncio
async def test_component_async_layout_appends():
    class Layout(Component):
        src = "./layout.html"

    async with Layout() as html:
        ui.h1("Hello, World!")

    assert "Hello, World!" in str(html)


def test_component_select_root_tag():
    class ListC(Component):
        src = """
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
        """

        def __init__(self, list_items: list[str]):
            self.list_items = list_items

        def render(self):
            # sourcery skip: no-loop-in-tests
            for item in self.list_items:
                list_item = self.list_item_tag.copy()
                list_item.string = item

                self.list_tag.append(list_item)

        @tag("li", extract=True)
        def list_item_tag(self):
            pass

        @tag(clear=True)
        def list_tag(self):
            pass

    list_c = ListC(["one", "two", "three"])

    assert str(list_c) == "<ul><li>one</li><li>two</li><li>three</li></ul>"


def test_component_tag_decorator_cache():
    class CachedComponent(Component):
        src = "<div><span>Original</span></div>"

        def __init__(self):
            self.counter = 0

        @tag("span")
        def span_tag(self):
            self.counter += 1
            return ui.span(f"Called {self.counter} times")

    component = CachedComponent()
    # First call should modify the content
    assert str(component.span_tag) == "<span>Called 1 times</span>"
    # Subsequent calls should return cached result
    assert str(component.span_tag) == "<span>Called 1 times</span>"
    assert str(component.span_tag) == "<span>Called 1 times</span>"


def test_component_tag_render_return():
    class Render(Component):
        src = "<div>Original</div>"

        def render(self):
            return ui.h1("Hello, World!")

    component = Render()

    assert str(component) == "<h1>Hello, World!</h1>"


def test_component_type_error():
    """Test that ComponentTypeError is raised with correct message when non-Tag is returned."""

    class BadComponent(Component):
        src = "<div>Original</div>"

        def render(self):
            return "not a tag"  # This should raise ComponentTypeError

    with pytest.raises(ComponentTypeError) as exc_info:
        BadComponent()

    assert "Expected Tag, got <class 'str'>" in str(exc_info)


def test_component_before_render_sync():
    """Test that synchronous before_render hook is called and can modify the component."""

    class BeforeRenderComponent(Component):
        src = "<div>Original</div>"

        def before_render(self):
            self.msg = "Modified in before_render"

        def render(self):
            self.string = self.msg

    component = BeforeRenderComponent()
    assert str(component) == "<div>Modified in before_render</div>"


@pytest.mark.asyncio
async def test_component_async_before_render():
    """Test that asynchronous before_render hook is called and can modify the component."""

    class AsyncBeforeRenderComponent(Component):
        src = "<div>Original</div>"

        async def before_render(self):
            await asyncio.sleep(0.01)  # Simulate async operation
            self.msg = "Modified in before_render"

        async def render(self):
            return ui.h1(self.msg)

    component = await AsyncBeforeRenderComponent()
    assert str(component) == "<h1>Modified in before_render</h1>"


def test_component_before_render_only():
    """Test that before_render hook works without a render method."""

    class BeforeRenderOnlyComponent(Component):
        src = "<div>Original</div>"

        def before_render(self):
            self.string = "Modified in before_render"

    component = BeforeRenderOnlyComponent()

    assert str(component) == "<div>Modified in before_render</div>"


@pytest.mark.asyncio
async def test_component_async_before_render_sync_render():
    """Test that asynchronous before_render hook is called and can modify the component."""

    class AsyncBeforeRenderComponent(Component):
        src = "<div>Original</div>"

        async def before_render(self):
            await asyncio.sleep(0.01)  # Simulate async operation
            self.msg = "Modified in before_render"

        def render(self):
            return ui.h1(self.msg)

    component = await AsyncBeforeRenderComponent()
    assert str(component) == "<h1>Modified in before_render</h1>"


@pytest.mark.asyncio
async def test_component_async_before_render_sync_render_with_context():
    """Test that asynchronous before_render hook is called and can modify the component."""

    class AsyncBeforeRenderComponent(Component):
        src = "<div>Original</div>"

        async def before_render(self):
            await asyncio.sleep(0.01)  # Simulate async operation
            self.msg = "Modified in before_render"

        def render(self):
            return ui.h1(self.msg)

    async with AsyncBeforeRenderComponent() as component:
        assert str(component) == "<h1>Modified in before_render</h1>"

    async with AsyncBeforeRenderComponent() as component:
        component.string = f"{component.string}!"

    assert str(component) == "<h1>Modified in before_render!</h1>"


@pytest.mark.asyncio
async def test_component_async_before_render_async_render_with_context():
    """Test that asynchronous before_render hook is called and can modify the component."""

    class AsyncBeforeRenderComponent(Component):
        src = "<div>Original</div>"

        async def before_render(self):
            await asyncio.sleep(0.01)  # Simulate async operation
            self.msg = "Modified in before_render"

        async def render(self):
            return ui.h1(self.msg)

    async with AsyncBeforeRenderComponent() as component:
        assert str(component) == "<h1>Modified in before_render</h1>"

    async with AsyncBeforeRenderComponent() as component:
        component.string = f"{component.string}!"

    assert str(component) == "<h1>Modified in before_render!</h1>"


def test_component_async_before_render_sync_with_context():
    """Test that asynchronous before_render hook is called and can modify the component."""

    class SyncBeforeRenderComponent(Component):
        src = "<div>Original</div>"

        def before_render(self):
            self.msg = "Modified in before_render"

        def render(self):
            return ui.h1(self.msg)

    with SyncBeforeRenderComponent() as component:
        assert str(component) == "<h1>Modified in before_render</h1>"

    with SyncBeforeRenderComponent() as component:
        component.string = f"{component.string}!"

    assert str(component) == "<h1>Modified in before_render!</h1>"


def test_component_async_before_render_sync_with_context_with_tag():
    """Test that asynchronous before_render hook is called and can modify the component."""

    class SyncBeforeRenderComponent(Component):
        src = "<div>Original</div>"

        def before_render(self):
            self.msg = "Modified in before_render"

        def render(self):
            return self.h1_tag

        @tag()
        def h1_tag(self, t: Tag):
            t.name = "h1"
            t.string = self.msg

    with SyncBeforeRenderComponent() as component:
        assert str(component) == "<h1>Modified in before_render</h1>"

    with SyncBeforeRenderComponent() as component:
        component.string = f"{component.string}!"

    assert str(component) == "<h1>Modified in before_render!</h1>"


@pytest.mark.asyncio
async def test_component_async_before_render_async_with_context_with_tag():
    """Test that asynchronous before_render hook is called and can modify the component."""

    class SyncBeforeRenderComponent(Component):
        src = "<div>Original</div>"

        async def before_render(self):
            self.msg = "Modified in before_render"

        async def render(self):
            return self.h1_tag

        @tag
        def h1_tag(self, t: Tag):
            t.name = "h1"
            t.string = self.msg

    async with SyncBeforeRenderComponent() as component:
        assert str(component) == "<h1>Modified in before_render</h1>"

    async with SyncBeforeRenderComponent() as component:
        component.string = f"{component.string}!"

    assert str(component) == "<h1>Modified in before_render!</h1>"


def test_component_after_render():
    """Test that after_render is called when not using context manager."""

    class AfterRenderComponent(Component):
        src = "<div>Original</div>"

        def __init__(self):
            self.steps: list[str] = []

        def before_render(self):
            self.steps.append("before")

        def render(self):
            self.steps.append("render")

        def after_render(self):
            self.steps.append("after")
            self.string = "after render"

    component = AfterRenderComponent()

    assert component.steps == ["before", "render", "after"]
    assert str(component) == "<div>after render</div>"


def test_no_tag_context_nested():
    """Test that no_tag_context works correctly with nested contexts."""

    with ui.div() as container:
        ui.p("First paragraph")  # Should be appended

        with no_tag_context():
            standalone = ui.p("Not appended")  # Should not be appended

            with ui.div() as inner:  # Should not be appended
                ui.p("Not appended paragraph")  # Should be appended to inner

            with ui.div() as inner:  # Should not be appended
                ui.p("Inner paragraph")  # Should be appended to inner

            container.append(inner)  # Manually append inner

        ui.p("Last paragraph")  # Should be appended

    expected = "<div><p>First paragraph</p><div><p>Inner paragraph</p></div><p>Last paragraph</p></div>"

    assert str(container) == expected
    assert str(standalone) == "<p>Not appended</p>"


def test_component_xml_parser():
    """Test that SVG files automatically use XML parser."""

    class SvgButton(Component):
        src = "./button.svg"

        def render(self):
            # sourcery skip: no-conditionals-in-tests
            if text_elem := self.select_one("text"):
                text_elem.string = "Test"

    button = SvgButton()
    assert button.src_parser == "xml"
    assert "<text" in str(button)
    assert ">Test</text>" in str(button)


def test_component_after_render_called_before_exit():
    """Test that after_render raises error in sync context."""

    class AfterRenderComponent(Component):
        src = "<div>Original</div>"

        def __init__(self):
            self.steps: list[str] = []

        def before_render(self):
            self.steps.append("before")

        def render(self):
            self.steps.append("render")

        def after_render(self):
            self.steps.append("after")

    with pytest.raises(ComponentAfterRenderError) as exc_info:
        with AfterRenderComponent() as component:
            component.append(ui.text("!"))

    assert "after_render cannot be called in a synchronous context manager" in str(exc_info.value)


@pytest.mark.asyncio
async def test_component_async_after_render_called_before_exit():
    """Test that after_render is called when not using context manager."""

    class AfterRenderComponent(Component):
        src = "<div>Original</div>"

        def __init__(self):
            self.steps: list[str] = []

        async def before_render(self):
            self.steps.append("before")

        async def render(self):
            self.steps.append("render")

        async def after_render(self):
            self.steps.append("after")
            assert "!" in str(self)

    async with AfterRenderComponent() as component:
        component.append(ui.text("!"))

    assert component.steps == ["before", "render", "after"]
    assert str(component) == "<div>Original!</div>"


@pytest.mark.asyncio
async def test_component_async_after_render():
    """Test that after_render is called when not using context manager."""

    class AfterRenderComponent(Component):
        src = "<div>Original</div>"

        def __init__(self):
            self.steps: list[str] = []

        async def before_render(self):
            self.steps.append("before")

        async def render(self):
            self.steps.append("render")

        async def after_render(self):
            self.steps.append("after")
            self.string = "after render"

    component = await AfterRenderComponent()

    async with AfterRenderComponent() as component2:
        pass

    assert component.steps == ["before", "render", "after"]
    assert str(component) == "<div>after render</div>"
    assert component2.steps == ["before", "render", "after"]
    assert str(component2) == "<div>after render</div>"


def test_component_sync_after_render_error_explanation():
    """Test that sync after_render in sync context raises clear error."""

    class SyncAfterRenderComponent(Component):
        src = "<div>Original</div>"

        def after_render(self):
            self.string = "after render"

    # This raises because sync after_render in sync context would be inconsistent
    # with async behavior where after_render runs at context exit
    with pytest.raises(ComponentAfterRenderError) as exc_info:
        with SyncAfterRenderComponent():
            pass

    assert "after_render cannot be called in a synchronous context manager" in str(exc_info.value)
    assert "Either make the context manager async or remove after_render" in str(exc_info.value)


def test_component_sync_after_render_without_context():
    """Test that sync after_render works fine outside context manager."""

    class SyncAfterRenderComponent(Component):
        src = "<div>Original</div>"

        def after_render(self):
            self.string = "after render"

    # Without context manager, sync after_render runs immediately after render
    component = SyncAfterRenderComponent()
    assert str(component) == "<div>after render</div>"


def test_component_missing_src_attribute():
    """Test that ComponentAttributeError is raised when src attribute is missing."""

    class MissingSrcComponent(Component):
        pass

    with pytest.raises(ComponentSrcRequiredError) as exc_info:
        MissingSrcComponent()

    assert "Component (MissingSrcComponent): Must define 'src' class attribute" in str(exc_info.value)


def test_component_invalid_src_type():
    """Test that ComponentSrcTypeError is raised when src is an invalid type."""

    class InvalidSrcComponent(Component):
        src = 42  # type: ignore[assignment]

    with pytest.raises(ComponentSrcTypeError) as exc_info:  # type: ignore[reportUnknownVariableType]
        InvalidSrcComponent()

    assert "Component (InvalidSrcComponent): 'src' must be either a str, callable[..., str | Tag] or Tag" in str(
        exc_info.value
    )  # type: ignore[reportUnknownMemberType]


def test_component_callable_src():
    """Test that src can be a callable that returns HTML."""

    class CallableSrcComponent(Component):
        src = lambda: "<div><h1>Dynamic</h1></div>"

    component = CallableSrcComponent()

    assert str(component) == "<div><h1>Dynamic</h1></div>"


def test_component_callable_src_str():
    """Test that src can be a callable that returns HTML."""

    def html():
        return "<div><h1>Dynamic</h1></div>"

    class CallableSrcComponent(Component):
        src = html

    component = CallableSrcComponent()

    assert str(component) == "<div><h1>Dynamic</h1></div>"


def test_component_callable_src_tag():
    """Test that src can be a callable that returns HTML."""

    def html():
        return ui.raw("<div><h1>Dynamic</h1></div>")

    class CallableSrcComponent(Component):
        src = html

    component = CallableSrcComponent()

    assert str(component) == "<div><h1>Dynamic</h1></div>"


def test_component_callable_src_current_parent_context():
    """Test that src can be a callable that returns HTML."""

    def load_html():
        return str(ui.raw("<div><h1>Dynamic</h1></div>"))

    class CallableSrcComponent(Component):
        src = load_html

    with CallableSrcComponent() as html:
        CallableSrcComponent()

    assert str(html) == "<div><h1>Dynamic</h1><div><h1>Dynamic</h1></div></div>"


def test_component_no_tag_context():
    """Test that no_tag_context prevents automatic tag appending."""

    with ui.div() as container:
        # Normal context - tag gets appended
        ui.p("Normal paragraph")

        # no_tag_context - tag doesn't get appended
        with no_tag_context():
            standalone = ui.p("Standalone paragraph")

        # Manually append the standalone tag
        container.append(standalone)

        # Verify normal context still works
        ui.p("Another normal paragraph")

    expected = "<div><p>Normal paragraph</p><p>Standalone paragraph</p><p>Another normal paragraph</p></div>"

    assert str(container) == expected


def test_component_replace_with():
    class HelloComponent(Component):
        src = "./layout.html"

        @tag("body > main")
        def main(self):
            pass

        def render(self):
            self.main = ui.raw("<main>Hello</main>")

    with HelloComponent() as html:
        html.main.append(ui.text(", World!"))

    assert "Hello, World!" in str(html)


@pytest.mark.asyncio
async def test_component_async_callable_src_current_parent_context():
    """Test that src can be a callable that returns HTML."""

    def load_html():
        return str(ui.raw("<div><h1>Dynamic</h1></div>"))

    class CallableSrcComponent(Component):
        src = load_html

        async def render(self):
            pass

    async with CallableSrcComponent() as html:
        await CallableSrcComponent()

    assert str(html) == "<div><h1>Dynamic</h1><div><h1>Dynamic</h1></div></div>"


def test_component_replace_root():
    """Test replacing a component's root tag."""

    class RootComponent(Component):
        src = "<div>Content <span>here</span></div>"

        def render(self):
            self.replace_root_tag(ui.section(class_="container"))

    component = RootComponent()
    assert str(component) == '<section class="container"></section>'


def test_component_with_soup_strainer():
    """Test that src_strainer works to limit parsing to specific tags."""
    from bs4 import SoupStrainer

    class ComponentWithStrainer(Component):
        src = """
        <div id="root">
            <header>This is a header</header>
            <main>
                <p>First paragraph</p>
                <p>Second paragraph</p>
            </main>
            <footer>This is a footer</footer>
        </div>
        """
        src_strainer = SoupStrainer(["main", "footer"])

    component = ComponentWithStrainer()

    # The main tag should be found
    assert component.find("main") is not None
    # The footer tag should be found
    assert component.find("footer") is not None
    # The header tag should NOT be found because of the strainer
    assert component.find("header") is None


def test_component_with_string_strainer():
    """Test that src_strainer can accept a string selector."""

    class ComponentWithStringStrainer(Component):
        src = """
        <div id="root">
            <header>This is a header</header>
            <main>
                <p>First paragraph</p>
                <p>Second paragraph</p>
            </main>
            <footer>This is a footer</footer>
        </div>
        """
        src_strainer: ClassVar[SoupStrainer | str | list[str] | None] = "main"

    component = ComponentWithStringStrainer()

    # Component itself should be the main tag
    assert component.name == "main"
    # Should have paragraph children
    assert component.find("p") is not None
    # The header tag should NOT be found because of the strainer
    assert component.find("header") is None
    # The footer tag should NOT be found because of the strainer
    assert component.find("footer") is None


def test_component_with_list_strainer():
    """Test that src_strainer can accept a list of string selectors."""

    class ComponentWithListStrainer(Component):
        src = """
        <div id="root">
            <header>This is a header</header>
            <main>
                <p>First paragraph</p>
                <p>Second paragraph</p>
            </main>
            <footer>This is a footer</footer>
        </div>
        """
        src_strainer: ClassVar[SoupStrainer | str | list[str] | None] = ["main", "footer"]

    component = ComponentWithListStrainer()

    # The main tag should be found
    assert component.find("main") is not None
    # The footer tag should be found
    assert component.find("footer") is not None
    # The header tag should NOT be found because of the strainer
    assert component.find("header") is None


def test_component_tag_root_replacement():
    """Test that root_tag option replaces the component's root tag."""

    class RootTagComponent(Component):
        src = "<div>Content <span>here</span></div>"

        @tag(root_tag=True)
        def root(self):
            return ui.section(class_="container")

    component = RootTagComponent()

    assert str(component) == '<section class="container"></section>'


def test_auto_src_strainer_from_tags():
    """Test that src_strainer is automatically generated from @tag decorators."""

    class ComponentWithTagDecorators(Component):
        src = """
        <div id="root">
            <header>This is a header</header>
            <main>
                <p>First paragraph</p>
                <p>Second paragraph</p>
            </main>
            <footer>This is a footer</footer>
        </div>
        """

        @tag("main")
        def main_content(self):
            return ui.main("Modified main content")

        @tag("footer")
        def footer_content(self):
            return ui.footer("Modified footer content")

    component = ComponentWithTagDecorators()

    # The main tag should be found
    assert component.find("main") is not None
    # The footer tag should be found
    assert component.find("footer") is not None
    # The header tag should NOT be found because of the auto-generated strainer
    assert component.find("header") is None


def test_component_tag_root_replacement_with_nested():
    """Test that root_tag option replaces the component's root tag."""

    class RootTagComponent(Component):
        src = "<div>Content <span>here</span><section class='container'>Content <span>here</span></section></div>"

        @tag("section", root_tag=True)
        def section(self):
            pass

    component = RootTagComponent()

    assert str(component) == '<section class="container">Content <span>here</span></section>'


def test_component_tag_root_replacement_with_nested_modified():
    """Test that root_tag option replaces the component's root tag."""

    class RootTagComponent(Component):
        src = "<div>Content <span>here</span><section class='container'>Content <span>here</span></section></div>"

        @tag("section", root_tag=True)
        def section(self, t: Tag):
            t["class"].append("prose")

    component = RootTagComponent()

    assert str(component) == '<section class="container prose">Content <span>here</span></section>'


def test_component_tag_root_replacement_with_nested_modified_returned():
    """Test that root_tag option replaces the component's root tag."""

    class RootTagComponent(Component):
        src = "<div>Content <span>here</span><section class='container'>Content <span>here</span></section></div>"

        @tag("section", root_tag=True)
        def section(self, t: Tag):
            t["class"].append("prose")

            return t

    component = RootTagComponent()

    assert str(component) == '<section class="container prose">Content <span>here</span></section>'


def test_component_tag_root_replacement_with_comment_nested_modified_returned():
    """Test that root_tag option replaces the component's root tag."""

    class RootTagComponent(Component):
        src = """
            <div>Content
                <span>here</span>
                <!-- #section -->
                <section class='container'>Content <span>here</span></section>
            </div>
        """

        @tag("<!-- #section -->", root_tag=True)
        def section(self, t: Tag):
            t["class"].append("prose")

    component = RootTagComponent()
    html = str(component)

    assert html == '<section class="container prose">Content <span>here</span></section>'


def test_component_sync_call_async_component_error():
    """Test that using a sync call with an async component raises an error."""

    class AsyncComponent(Component):
        src = "<div>Original</div>"

        async def render(self):
            return ui.h1("Hello")

    with pytest.raises(ComponentAsyncError) as exc_info:
        with AsyncComponent():  # This should raise because it's an async component called synchronously
            pass

    assert "Component (AsyncComponent): has async hooks but was called synchronously" in str(exc_info.value)

    # with pytest.raises(ComponentAsyncError) as exc_info:
    #     AsyncComponent()  # This should raise because it's an async component called synchronously
    #
    # assert "Component has async hooks but was called synchronously" in str(exc_info.value)


def test_component_tag_src():
    """Test that src can be a Tag instance."""

    class TagSrcComponent(Component):
        src = ui.div(class_="container")

    component = TagSrcComponent()
    assert str(component) == '<div class="container"></div>'


def test_component_src_root_tag():
    """Test that src_root_tag selects a new root from the source."""

    class RootTagComponent(Component):
        src = "<div><section class='container'>Content <span>here</span></section></div>"
        src_root_tag = "section"

    component = RootTagComponent()
    assert str(component) == '<section class="container">Content <span>here</span></section>'


def test_component_src_root_tag_with_nested():
    """Test that src_root_tag works with deeply nested elements."""

    class RootTagComponent(Component):
        src = "<div><main><section class='container'>Content <span>here</span></section></main></div>"
        src_root_tag = "section.container"

    component = RootTagComponent()
    assert str(component) == '<section class="container">Content <span>here</span></section>'


def test_component_src_root_tag_with_comment():
    """Test that src_root_tag works with comment selectors."""

    class NavComponent(Component):
        src = """
        <div>
            <!-- #sidebar-nav -->
            <nav class="sidebar">
                <ul>
                    <li>Home</li>
                </ul>
            </nav>
            <main>Content</main>
        </div>
        """
        src_root_tag = "<!-- #sidebar-nav -->"

    nav = NavComponent()
    nav_str = "".join(str(nav).split("\n"))
    assert nav_str == '<nav class="sidebar"><ul><li>Home</li></ul></nav>'

    # @tag("<!-- #header-right-wrapper-refresh-data-btn -->")
    # def header_right_wrapper_refresh_data_btn(self, t: Tag):
    #     if link := t.select_one("a"):
    #         link["href"] = self.request.url.path
    #         link["hx-ext"] = "push-url-w-params"
    #         link["hx-push-url"] = "false"


def test_component_src_root_tag_with_comment_replace():
    """Test that src_root_tag works with comment selectors."""

    nav = AppNavComponent()
    nav_str = "".join(str(nav).split("\n"))

    assert 'href="/home"' in nav_str

    nav = AppNavComponent()
    nav_str = "".join(str(nav).split("\n"))

    assert 'href="/home"' in nav_str

    with AppNavComponent() as nav:
        assert 'href="/home"' in str(nav)

    # class AsyncNavComponent(NavComponent):
    #     async def render(self):
    #         pass
    #
    # async with AsyncNavComponent() as component:
    #     assert 'href="/home"' in str(component)


def test_component_src_root_tag_with_comment_replace_inherited():
    class InheritedAppNavComponent(AppNavComponent):
        pass

    with InheritedAppNavComponent() as nav:
        assert 'href="/home"' in str(nav)


def test_component_with_comment_tag():
    """Test that src_root_tag works with comment selectors."""

    class NavComponent(Component):
        src = """
        <div>
            <!-- section -->
            <section>
                <!-- #sidebar-nav-wrong -->
                <nav class="sidebar">
                    <ul>
                        <li>Home</li>
                    </ul>
                </nav>
                <!-- #sidebar-nav -->
                <nav class="sidebar">
                    <ul>
                        <!-- .list_item -->
                        <li>Home</li>
                    </ul>
                </nav>
                <main>Content</main>
            </section>

            <!-- section-two -->
            <section>
                <!-- #sidebar-nav -->
                <nav class="sidebar">
                    <ul>
                        <li>Home</li>
                    </ul>
                </nav>
                <main>Content</main>
            </section>
        </div>
        """
        src_root_tag = "<!-- section -->"

        @tag("<!-- #sidebar-nav -->", extract=True)
        def sidebar_nav(self):
            pass

        def render(self):
            sidebar_nav = self.sidebar_nav.copy()
            list_item = cast("Tag", sidebar_nav.comment_one(".list_item"))
            list_item.string = "Hello"
            self.append(sidebar_nav)

    assert "Hello" in str(NavComponent())


def test_component_src_root_tag_not_found():
    """Test that component raises error when src_root_tag selector isn't found."""

    class RootTagComponent(Component):
        src = "<div>Content <span>here</span></div>"
        src_root_tag = ".not-found"

    with pytest.raises(ComponentSrcRootTagNotFoundError) as exc_info:
        RootTagComponent()

    assert "src_root_tag selector '.not-found' not found in source HTML" in str(exc_info.value)


def test_component_no_src_only_render():
    class NoSrcComponent(Component):
        def render(self):
            with ui.div() as html:
                ui.h1("Hello, World!")

            return html

    assert str(NoSrcComponent()) == "<div><h1>Hello, World!</h1></div>"


def test_tag_not_found_error():
    """Test that TagNotFoundError is raised with correct message."""

    class MissingTagComponent(Component):
        src = "<div>Content</div>"

        @tag(".non-existent")
        def missing_tag(self):
            pass

    with pytest.raises(ComponentTagNotFoundError) as exc_info:
        MissingTagComponent()

    assert "MissingTagComponent.missing_tag did not find selector: .non-existent" in str(exc_info.value)


@pytest.mark.asyncio
async def test_component_mixed_sync_async_hooks():
    """Test component with mix of sync and async lifecycle hooks."""

    class MixedComponent(Component):
        src = "<div>Original</div>"

        def __init__(self):
            self.steps: list[str] = []

        def before_render(self):
            self.steps.append("sync before")

        async def render(self):
            await asyncio.sleep(0.01)
            self.steps.append("async render")

        async def after_render(self):
            self.steps.append("async after")
            self.string = "all done"

    async with MixedComponent() as component:
        assert "sync before" in component.steps
        assert "async render" in component.steps
        component.append(ui.text("!"))

    assert component.steps == ["sync before", "async render", "async after"]
    assert str(component) == "<div>all done</div>"


def test_component_parse_content():
    """Test _parse_content with various inputs."""
    # No doctype
    content = "<div>Test</div>"
    # pyright: ignore[reportPrivateUsage]
    # pyright: ignore[reportPrivateUsage]
    result = Component._parse_content(content)  # pyright: ignore[reportPrivateUsage]
    assert result == (content, None)

    # With doctype
    content_with_doctype = "<!DOCTYPE html>\n<div>Test</div>"
    # pyright: ignore[reportPrivateUsage]
    # pyright: ignore[reportPrivateUsage]
    result = Component._parse_content(content_with_doctype)  # pyright: ignore[reportPrivateUsage]
    assert result == (content_with_doctype, "<!DOCTYPE html>")

    # With doctype variations
    content_with_doctype = "<!doctype HTML>\n<div>Test</div>"
    result = Component._parse_content(content_with_doctype)  # pyright: ignore[reportPrivateUsage]
    assert result == (content_with_doctype, "<!doctype HTML>")


def test_component_parse_source_content_with_caching(monkeypatch: MonkeyPatch, tmp_path: Path):
    with monkeypatch.context() as mp:
        mp.setenv("WEBA_LRU_CACHE_SIZE", "10")
        content = "<!DOCTYPE html>\n<div>Test</div>"

        # Test direct content with caching
        result1 = Component._parse_source_content(content)  # pyright: ignore[reportPrivateUsage]
        result2 = Component._parse_source_content(content)  # pyright: ignore[reportPrivateUsage]
        assert result1 == result2 == (content, "<!DOCTYPE html>")

        # Test file content with caching
        test_file = tmp_path / "test.html"
        test_file.write_text(content)
        result1 = Component._parse_source_content(str(test_file))  # pyright: ignore[reportPrivateUsage]
        result2 = Component._parse_source_content(str(test_file))  # pyright: ignore[reportPrivateUsage]
        assert result1 == result2 == (content, "<!DOCTYPE html>")


def test_component_parse_source_content_without_caching(monkeypatch: MonkeyPatch, tmp_path: Path):
    with monkeypatch.context() as mp:
        mp.setenv("WEBA_LRU_CACHE_SIZE", "")
        content = "<!DOCTYPE html>\n<div>Test</div>"

        # Test direct content without caching
        result1 = Component._parse_source_content(content)  # pyright: ignore[reportPrivateUsage]
        result2 = Component._parse_source_content(content)  # pyright: ignore[reportPrivateUsage]
        assert result1 == result2 == (content, "<!DOCTYPE html>")

        # Test file content without caching
        test_file = tmp_path / "test.html"
        test_file.write_text(content)
        result1 = Component._parse_source_content(str(test_file))  # pyright: ignore[reportPrivateUsage]
        result2 = Component._parse_source_content(str(test_file))  # pyright: ignore[reportPrivateUsage]
        assert result1 == result2 == (content, "<!DOCTYPE html>")


def test_component_parse_source_content_edge_cases(monkeypatch: MonkeyPatch, tmp_path: Path):
    with monkeypatch.context() as mp:
        mp.setenv("WEBA_LRU_CACHE_SIZE", "10")

        # Test with empty content (direct)
        result = Component._parse_source_content("")  # pyright: ignore[reportPrivateUsage]
        assert result == ("", None)

        # Test with empty content (file)
        empty_file = tmp_path / "empty.html"
        empty_file.write_text("")
        result = Component._parse_source_content(str(empty_file))  # pyright: ignore[reportPrivateUsage]
        assert result == ("", None)

        # Test with non-existent file
        non_existent = tmp_path / "does_not_exist.html"
        with pytest.raises(ComponentSrcFileNotFoundError) as exc_info:
            Component._parse_source_content(non_existent)  # pyright: ignore[reportPrivateUsage]
        assert "Source file not found" in str(exc_info.value)

        # Test with different doctype variations
        variations = [
            "<!DOCTYPE html>\n<div>Test</div>",
            "<!doctype HTML>\n<div>Test</div>",
            "<!DOCTYPE HTML PUBLIC '-//W3C//DTD HTML 4.01//EN'>\n<div>Test</div>",
        ]
        # sourcery skip: no-loop-in-tests
        for content in variations:
            result = Component._parse_source_content(content)  # pyright: ignore[reportPrivateUsage]
            assert result[0] == content
            assert "!doctype" in result[1].lower()  ## pyright: ignore[reportOptionalMemberAccess]


def test_component_tag_return_tag():
    class Render(Component):
        src = "<div><h1>Hello</h1></div>"

        def render(self):
            self.h1_tag.string = f"{self.h1_tag.string}, World!"

        @tag("h1")
        def h1_tag(self, t: Tag):
            t["class"].append("header")

            return t

    assert str(Render()) == '<div><h1 class="header">Hello, World!</h1></div>'


def test_component_appending_multiple_tags_from_ui_raw():
    class Layout(Component):
        src = "./layout.html"

        @tag("body")
        def body(self):
            pass

        def render(self):
            scripts = ui.raw("""
                <script src="script1.js"></script>
                <script src="script2.js"></script>
            """)

            # sourcery skip: no-conditionals-in-tests
            # sourcery skip: no-loop-in-tests
            for script in scripts:
                if isinstance(script, Tag):
                    script["foo"] = "bar"
                    self.body.append(script)

    layout_html = str(Layout())

    # The attribute order might be different, so check for presence of both attributes separately
    assert 'foo="bar"' in layout_html
    assert 'src="script1.js"' in layout_html

    # Same for the second script tag
    assert 'foo="bar"' in layout_html
    assert 'src="script2.js"' in layout_html


def test_component_form_input():
    class FormComponent(Component):
        src = "./form.html"

        @tag("input")
        def input_tag(self):
            pass

        def render(self):
            self.input_tag["name"] = self.input_name

        @property
        def input_name(self):
            order_id = 123456
            return f'orders["{order_id}"][loan_number]'

    form = FormComponent()
    html = str(form)

    assert form.input_name in html


class TestMemoryManagement:
    """Test memory management features."""

    def test_default_cache_size(self):
        """Test that default cache size is set to 256."""
        # Clear the cached value
        import os

        from weba.component import ComponentMeta

        ComponentMeta._cache_size = None  # pyright: ignore[reportPrivateUsage]
        # Temporarily unset the env var
        old_value = os.environ.pop("WEBA_LRU_CACHE_SIZE", None)
        try:
            cache_size = ComponentMeta.get_cache_size()
            assert cache_size == 256, "Default cache size should be 256"
        finally:
            # sourcery skip: no-conditionals-in-tests
            if old_value is not None:
                os.environ["WEBA_LRU_CACHE_SIZE"] = old_value

            ComponentMeta._cache_size = None  # pyright: ignore[reportPrivateUsage] # Reset for other tests

    # def test_instance_cache_clearing(self):
    #     """Test that instance cache can be cleared."""
    #
    #     class TestComponent(Component):
    #         src = "<div><span>Test</span></div>"
    #
    #         @tag("span")
    #         def some_tag(self):
    #             self["class"] = "cached"
    #
    #     component = TestComponent()
    #     # Access the tag to populate cache
    #     _ = component.some_tag
    #     assert len(component._cached_tags) > 0, "Cache should contain tags"  # pyright: ignore[reportPrivateUsage]
    #
    #     # Clear the cache
    #     component.clear_cache()
    #     assert len(component._cached_tags) == 0, "Cache should be empty after clearing"  # pyright: ignore[reportPrivateUsage]

    def test_tag_context_cleanup(self):
        """Test that tag context is properly cleaned up."""
        from weba.tag import current_tag_context

        # Ensure we start with no context
        assert current_tag_context.get() is None

        tag = ui.div()
        with tag:
            # Inside context, current_tag_context should be set
            assert current_tag_context.get() is tag

        # After exiting context, it should be None again
        assert current_tag_context.get() is None
