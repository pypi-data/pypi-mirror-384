"""
MIT License

Copyright (c) 2025 Lorenz Ohly, Dheepak Krishnamurthy
"""

import json
import re
from typing import Any, Literal


type Expression = str
"""TypeAlias for `str`, used in places where a DataStar expression is expected.
Expressions must always be strings as they are evaluated in the browser as JavaScript expressions.
This means that `data_signals({"x": "1"})` will set $x to the _number_ `1`. Use `data_signals({"x": '"1"'})`
to set $x to the string `"1"`.
"""

type Signal = str
"""TypeAlias for `str`, used in places where a DataStar signal name is expected, which must be defined without a leading $"""


type Case = Literal["camel", "kebab", "pascal", "snake"]
type Duration = str


_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")

SCRIPT_CDN = (
    "https://cdn.jsdelivr.net/gh/starfederation/datastar@1.0.0-RC.5/bundles/datastar.js"
)


def kebabify(camel_str: str) -> str:
    return _PATTERN.sub("-", camel_str).replace("_", "-").lower()


def data_on(
    event: str,
    expr: Expression,
    once: bool = False,
    passive: bool = False,
    capture: bool = False,
    case_: Case | None = None,
    delay: Duration | None = None,
    debounce: Duration | None = None,
    debounce_leading: bool = False,
    debounce_notrail: bool = False,
    throttle: Duration | None = None,
    throttle_noleading: bool = False,
    throttle_trail: bool = False,
    viewtransition: bool = False,
    window: bool = False,
    outside: bool = False,
    prevent: bool = False,
    stop: bool = False,
) -> dict[str, Expression]:
    """
    Attaches an event listener to an element, executing an expression whenever the event is triggered.

    An `evt` variable that represents the event object is available in the expression.

    This helper works with standard HTML events and custom events. The `submit` event
    listener (`data_on("submit", ...)`) prevents the default submission behavior of forms.

    Args:
        event: The name of the event to listen for (e.g., 'click', 'submit', 'myevent').
        expr: The DataStar expression to execute when the event is triggered.
        once: If True, only trigger the event listener once.
        passive: If True, do not call `preventDefault` on the event listener.
        capture: If True, use a capture event listener.
        case_: Converts the casing of the event name. One of 'camel', 'kebab', 'snake', 'pascal'.
        delay: Delays the event listener. E.g., '500ms', '1s'.
        debounce: Debounces the event listener. E.g., '500ms', '1s'.
        debounce_leading: If True, use debounce with a leading edge.
        debounce_notrail: If True, use debounce without a trailing edge.
        throttle: Throttles the event listener. E.g., '500ms', '1s'.
        throttle_noleading: If True, use throttle without a leading edge.
        throttle_trail: If True, use throttle with a trailing edge.
        viewtransition: If True, wraps the expression in `document.startViewTransition()`.
        window: If True, attaches the event listener to the `window` object.
        outside: If True, triggers when the event is outside the element.
        prevent: If True, calls `preventDefault` on the event listener.
        stop: If True, calls `stopPropagation` on the event listener.

    Returns:
        A dictionary representing the complete data-on attribute for use in a component.

    Example:
        ```python
        from fasthtml.common import Button, Div

        # Basic usage
        Button("Reset", data_on("click", "$foo = ''"))

        # Using the event object
        Div(data_on("myevent", "$foo = evt.detail"))

        # Using modifiers
        Button("Debounced Action",
               data_on("click", "$foo = ''",
                       window=True,
                       debounce="500ms",
                       debounce_leading=True))

        Div(data_on("my-event", "$foo = ''", case_="camel"))
        ```


    See Also:
        https://data-star.dev/reference/attributes#data-on
    """
    attr = f"data-on-{event}"

    if once:
        attr += "__once"
    if passive:
        attr += "__passive"
    if capture:
        attr += "__capture"
    if case_:
        attr += f"__case.{case_}"
    if delay:
        attr += f"__delay.{delay}"
    if debounce:
        attr += f"__debounce.{debounce}"
        if debounce_leading:
            attr += ".leading"
        if debounce_notrail:
            attr += ".notrail"
    if throttle:
        attr += f"__throttle.{throttle}"
        if throttle_noleading:
            attr += ".noleading"
        if throttle_trail:
            attr += ".trail"
    if viewtransition:
        attr += "__viewtransition"
    if window:
        attr += "__window"
    if outside:
        attr += "__outside"
    if prevent:
        attr += "__prevent"
    if stop:
        attr += "__stop"

    return {attr: expr}


def data_show(expr: Expression) -> dict[str, Expression]:
    """
    Shows or hides an element based on whether an expression evaluates to `true` or `false`.

    For anything with custom requirements, use `data_class` instead. To prevent flickering
    of the element before Datastar has processed the DOM, you can add a `display: none`
    style to the element to hide it initially.

    Args:
        expr: The DataStar expression that evaluates to a boolean.

    Returns:
        A dictionary representing the data-show attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # This div will be visible only when the signal `$foo` is truthy.
        Div("Conditionally visible content", data_show("$foo"))

        # To prevent flickering on page load, hide the element initially.
        Div("No flicker", data_show("$foo"), style="display: none")
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-show
    """
    return {"data-show": expr}


def data_text(expr: Expression) -> dict[str, str]:
    """
    Binds the text content of an element to an expression.

    The value of the attribute is a DataStar expression that is evaluated,
    meaning that JavaScript methods and properties can be used.

    Args:
        expr: The DataStarExpression whose result will be rendered as the
              element's text content.

    Returns:
        A dictionary representing the data-text attribute.

    Example:
        ```python
        from fasthtml.common import Div, Input, to_xml
        from datastar_attrs import data_bind, data_text

        # Display the value of the '$foo' signal.
        # Renders: <div data-text="$foo"></div>
        print(to_xml(Div(data_text("$foo"))))

        # Use a JavaScript expression to transform the signal's value.
        # Renders: <div data-text="$foo.toUpperCase()"></div>
        print(to_xml((
            Input(data_bind("foo")),
            Div(data_text("$foo.toUpperCase()"))
        )))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-text
    """
    return {"data-text": expr}


def data_attr(
    posattrs: dict[str, Expression] | None = None,
    *,
    kebabify: bool = True,
    **attrs: Expression,
) -> dict[str, Expression]:
    """
    Sets the value of any HTML attribute(s) to an expression, and keeps it in sync.

    It accepts attributes as keyword arguments (for valid Python identifiers) or
    as a dictionary (for attributes with special characters). By default, it converts
    underscores in attribute names to hyphens.

    Args:
        posattrs: A dictionary of attributes. Useful for attribute names that are
                  not valid Python identifiers (e.g., 'data-custom-attr').
        kebabify: If True (default), automatically converts underscores `_` in
                  attribute names to hyphens `-`. Set to False to preserve
                  underscores.
        **attrs: A mapping of HTML attribute names to DataStar expressions,
                 provided as keyword arguments.

    Returns:
        A dictionary representing the complete data-attr attribute(s).

    Example:
        ```python
        from fasthtml.common import Div

        # Sets a single 'title' attribute. Renders as: data-attr-title="$foo"
        Div(data_attr(title="$foo"))

        # Keyword `aria_label` becomes `aria-label` attribute due to default kebabify.
        # Renders as: data-attr-aria-label="'Some label'"
        Div(data_attr(aria_label="'Some label'"))

        # Preserve underscores by setting kebabify=False.
        # Renders as: data-attr-my_custom_attr="$bar"
        Div(data_attr(my_custom_attr="$bar", kebabify=False))

        # Sets multiple attributes.
        # Renders as: data-attr="{title: $foo, disabled: $bar}"
        Div(data_attr(title="$foo", disabled="$bar"))

        # Sets an attribute with a hyphen using a dictionary.
        # Renders as: data-attr-data-custom-attr="'value'"
        Div(data_attr({'data-custom-attr': "'value'"}))
        ```

    See Also:
        https://data-star-dev.github.io/reference/attributes#data-attr
    """
    attrs |= posattrs or {}

    if not attrs:
        raise ValueError("data_attr requires at least one attribute.")

    if kebabify:
        attrs = {key.replace("_", "-"): value for key, value in attrs.items()}

    if len(attrs) == 1:
        key, value = next(iter(attrs.items()))
        return {f"data-attr-{key}": value}
    else:
        return {"data-attr": _dict_to_js_obj_str(attrs)}


def _py_to_js_obj_str(py_obj: Any) -> str:
    """Recursively converts a Python object to a JavaScript object/literal string."""
    if py_obj is None:
        return "null"
    if isinstance(py_obj, bool):
        return "true" if py_obj else "false"
    if isinstance(py_obj, (int, float)):
        return str(py_obj)
    if isinstance(py_obj, str):
        # Don't quote DataStar expressions ($) or actions (@)
        if py_obj.startswith(("$", "@")):
            return py_obj
        # Basic escaping for single quotes in the string
        escaped_str = py_obj.replace("'", "\\'")
        return f"'{escaped_str}'"
    if isinstance(py_obj, dict):
        items = []
        for k, v in py_obj.items():
            key_str = (
                f"'{k}'"
                if not (
                    isinstance(k, str) and re.match(r"^[a-zA-Z_$][a-zA-Z0-9_$]*$", k)
                )
                else k
            )
            items.append(f"{key_str}: {_py_to_js_obj_str(v)}")
        return f"{{{', '.join(items)}}}"
    if isinstance(py_obj, (list, tuple)):
        return f"[{', '.join(_py_to_js_obj_str(item) for item in py_obj)}]"
    raise TypeError(f"Unsupported type for JS conversion: {type(py_obj)}")


def data_signals(
    pos_signals: dict[str, Any] | None = None,
    *,
    ifmissing: bool = False,
    case_: Case | None = None,
    **signals: Any,
) -> dict[str, Any]:
    """
    Patches (adds, updates or removes) one or more signals.

    This function can generate all three forms of the `data-signals` attribute.
    If exactly one simple-valued signal (str, int, bool) is provided, it generates
    the `data-signals-name="value"` form. Otherwise, it generates the object
    form `data-signals="{...}"`.

    Args:
        pos_signals: A dictionary of signals. Useful for namespaced signals
                     (e.g., 'foo.bar') or signals with names that are not valid
                     Python identifiers.
        ifmissing: If True, only patches signals if their keys do not already exist.
                   This modifier only applies to the single-signal form.
        case_: Converts the casing of the signal name (e.g., 'camel', 'kebab').
               This modifier only applies to the single-signal form.
        **signals: Signals provided as keyword arguments.

    Returns:
        A dictionary representing the complete data-signals attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # Single-signal form
        # Renders as: <div data-signals-foo="1"></div>
        Div(data_signals(foo=1))

        # Namespaced signal (still a single signal)
        # Renders as: <div data-signals-foo.bar="1"></div>
        Div(data_signals({'foo.bar': 1}))

        # Object form (triggered by multiple signals)
        # Renders as: <div data-signals="{foo: 1, bar: true}"></div>
        Div(data_signals(foo=1, bar=True))

        # Object form (triggered by a nested dict value)
        # Renders as: <div data-signals="{form: {input: 2}}"></div>
        Div(data_signals(form={'input': 2}))

        # Using the `ifmissing` modifier with a single signal
        # Renders as: <div data-signals-counter__ifmissing="0"></div>
        Div(data_signals(counter=0, ifmissing=True))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-signals
    """
    all_signals = signals.copy()
    if pos_signals:
        all_signals.update(pos_signals)

    if not all_signals:
        raise ValueError("data_signals requires at least one signal.")

    is_single_simple_signal = len(all_signals) == 1 and not isinstance(
        next(iter(all_signals.values())), (dict, list, tuple)
    )

    if is_single_simple_signal:
        key, value = next(iter(all_signals.items()))
        attr = f"data-signals-{key}"
        if case_:
            attr += f"__case.{case_}"
        if ifmissing:
            attr += "__ifmissing"
        return {attr: json.dumps(value)}
    else:
        if ifmissing or case_:
            raise ValueError(
                "'ifmissing' and 'case_' modifiers can only be used when defining a single, simple-valued signal."
            )
        return {"data-signals": _py_to_js_obj_str(all_signals)}


def data_class(
    pos_classes: dict[str, Expression] | None = None,
    *,
    case_: Case | None = None,
    kebabify: bool = True,
    **classes: Expression,
) -> dict[str, Expression]:
    """
    Adds or removes a CSS class (or classes) to or from an element based on an expression.

    If a single class is provided, it generates `data-class-name="expr"`. If multiple
    classes are provided, it generates `data-class="{name1: expr1, ...}"`.

    Args:
        pos_classes: A dictionary of class names to expressions. Useful for class
                     names that are not valid Python identifiers (e.g., 'font-bold').
        case_: Converts the casing of the class name (e.g., 'camel', 'kebab').
               This modifier only applies when defining a single class.
        kebabify: If True (default), converts underscores `_` in class names from
                  keyword arguments to hyphens `-`.
        **classes: Class names and their corresponding DataStar expressions,
                   provided as keyword arguments.

    Returns:
        A dictionary representing the complete data-class attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # Single-class form: adds 'hidden' class if $foo is truthy.
        # Renders as: <div data-class-hidden="$foo"></div>
        Div(data_class(hidden="$foo"))

        # Multi-class form: toggles 'hidden' and 'font-bold' classes.
        # Renders as: <div data-class="{hidden: $foo, 'font-bold': $bar}"></div>
        Div(data_class({'font-bold': '$bar'}, hidden="$foo"))

        # Using the `case_` modifier for a single class.
        # Renders as: <div data-class-my-class__case.camel="$foo"></div>
        Div(data_class(my_class="$foo", case_="camel", kebabify=False))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-class
    """
    all_classes = classes.copy()
    if pos_classes:
        all_classes.update(pos_classes)

    if not all_classes:
        raise ValueError("data_class requires at least one class.")

    if kebabify:
        all_classes = {
            key.replace("_", "-"): value for key, value in all_classes.items()
        }

    if len(all_classes) == 1:
        key, value = next(iter(all_classes.items()))
        attr = f"data-class-{key}"
        if case_:
            attr += f"__case.{case_}"
        return {attr: value}
    else:
        if case_:
            raise ValueError(
                "'case_' modifier can only be used when defining a single class."
            )
        return {"data-class": _dict_to_js_obj_str(all_classes)}


def data_on_interval(
    expr: Expression,
    *,
    duration: Duration = "1s",
    leading: bool = False,
    viewtransition: bool = False,
) -> dict[str, Expression]:
    """
    Runs an expression at a regular interval.

    Args:
        expr: The DataStar expression to execute.
        duration: The interval duration, e.g., '500ms', '2s'. Defaults to '1s'.
        leading: If True, executes the expression immediately on load, before
                 the first interval.
        viewtransition: If True, wraps the expression in `document.startViewTransition()`.

    Returns:
        A dictionary representing the data-on-interval attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # Increments a counter every 500 milliseconds.
        # Renders as: <div data-on-interval__duration.500ms="$count++"></div>
        Div(data_on_interval("$count++", duration="500ms"))

        # Polls an endpoint every 5 seconds, starting immediately.
        # Renders as: <div data-on-interval__duration.5s.leading="@get('/endpoint')"></div>
        Div(data_on_interval("@get('/endpoint')", duration="5s", leading=True))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-on-interval
    """
    attr = "data-on-interval"
    duration_mod = f"__duration.{duration}"
    if leading:
        duration_mod += ".leading"
    attr += duration_mod
    if viewtransition:
        attr += "__viewtransition"

    return {attr: expr}


def data_on_intersect(
    expr: Expression,
    *,
    once: bool = False,
    half: bool = False,
    full: bool = False,
    delay: Duration | None = None,
    debounce: Duration | None = None,
    throttle: Duration | None = None,
    viewtransition: bool = False,
) -> dict[str, Expression]:
    """
    Runs an expression when the element intersects with the viewport.

    Args:
        expr: The DataStar expression to execute on intersection.
        once: If True, only trigger the event once.
        half: If True, triggers when half of the element is visible.
        full: If True, triggers when the full element is visible.
        delay: Delays the event listener, e.g., '500ms'.
        debounce: Debounces the event listener, e.g., '200ms'.
        throttle: Throttles the event listener, e.g., '1s'.
        viewtransition: If True, wraps the expression in `document.startViewTransition()`.

    Returns:
        A dictionary representing the data-on-intersect attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # Set a signal to true when the element becomes visible.
        # Renders as: <div data-on-intersect="$intersected = true"></div>
        Div(data_on_intersect("$intersected = true"))

        # Load more content only once the element is fully visible.
        # Renders as: <div data-on-intersect__once__full="@get('/more')"></div>
        Div(data_on_intersect("@get('/more')", once=True, full=True))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-on-intersect
    """
    if half and full:
        raise ValueError("'half' and 'full' modifiers cannot be used together.")

    attr = "data-on-intersect"
    if once:
        attr += "__once"
    if half:
        attr += "__half"
    if full:
        attr += "__full"
    if delay:
        attr += f"__delay.{delay}"
    if debounce:
        attr += f"__debounce.{debounce}"  # Note: .leading/.notrail not supported in docs for intersect
    if throttle:
        attr += f"__throttle.{throttle}"  # Note: .noleading/.trail not supported in docs for intersect
    if viewtransition:
        attr += "__viewtransition"

    return {attr: expr}


def _is_valid_js_identifier(s: str) -> bool:
    """Checks if a string is a valid JavaScript identifier."""
    return re.match(r"^[a-zA-Z_$][a-zA-Z0-9_$]*$", s) is not None


def _dict_to_js_obj_str(d: dict[str, Expression]) -> str:
    """Converts a Python dict to a JavaScript object literal string."""
    items: list[str] = []
    for k, v in d.items():
        # Quote keys if they are not valid JS identifiers (e.g., 'font-bold')
        key_str = f"'{k}'" if not _is_valid_js_identifier(k) else k
        items.append(f"{key_str}: {v}")
    return f"{{{', '.join(items)}}}"


def data_style(
    pos_styles: dict[str, Expression] | None = None,
    *,
    kebabify: bool = True,
    **styles: Expression,
) -> dict[str, Expression]:
    """
    Sets the value of inline CSS styles on an element based on an expression.

    If a single style property is provided, it generates `data-style-property="expr"`.
    If multiple properties are provided, it generates the object form
    `data-style="{prop1: expr1, ...}"`.

    Args:
        pos_styles: A dictionary of CSS properties to expressions. Useful for properties
                    that are not valid Python identifiers (e.g., 'background-color').
        kebabify: If True (default), converts underscores `_` in property names from
                  keyword arguments to hyphens `-`.
        **styles: CSS properties and their corresponding DataStar expressions,
                  provided as keyword arguments.

    Returns:
        A dictionary representing the complete data-style attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # Single-style form using a keyword argument.
        # Renders as: <div data-style-background-color="$usingRed ? 'red' : 'blue'"></div>
        Div(data_style(background_color="$usingRed ? 'red' : 'blue'"))

        # Multi-style form using multiple keyword arguments.
        # Renders as: <div data-style="{display: $hiding ? 'none' : 'flex', flexDirection: 'column'}"></div>
        Div(data_style(display="$hiding ? 'none' : 'flex'", flexDirection="'column'", kebabify=False))

        # Using a dictionary for a property with a hyphen.
        # Renders as: <div data-style-font-weight="'bold'"></div>
        Div(data_style({'font-weight': "'bold'"}))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-style
    """
    all_styles = styles.copy()
    if pos_styles:
        all_styles.update(pos_styles)

    if not all_styles:
        raise ValueError("data_style requires at least one style property.")

    if kebabify:
        all_styles = {key.replace("_", "-"): value for key, value in all_styles.items()}

    if len(all_styles) == 1:
        key, value = next(iter(all_styles.items()))
        return {f"data-style-{key}": value}
    else:
        return {"data-style": _dict_to_js_obj_str(all_styles)}


def data_bind(signal_name: Signal) -> dict[Literal["data-bind"], Signal]:
    """
    Creates a signal and sets up two-way data binding with an element's value.

    This helper generates the `data-bind="signalName"` form. The initial value
    of the signal is set to the element's `value`, unless the signal has been
    predefined with `data_signals`. If predefined, the signal's type (e.g., number,
    boolean, array) is preserved on subsequent updates.

    Args:
        signal_name: The name of the signal to bind to.

    Returns:
        A dictionary representing the data-bind attribute.

    Example:
        ```python
        from fasthtml.common import Div, Input, Select, Option, data_signals

        # Simple two-way binding. The signal 'foo' will be created.
        Input(data_bind("foo"))

        # The signal 'foo' is initialized with the value "bar".
        Input(data_bind("foo"), value="bar")

        # The signal 'foo' is predefined as "baz", so the input's
        # initial value "bar" is ignored.
        Div(
            data_signals(foo="baz"),
            Input(data_bind("foo"), value="bar")
        )

        # Predefining a signal's type. When the option is selected,
        # `$foo` will be the number 10, not the string "10".
        Div(
            data_signals(foo=0),
            Select(
                data_bind("foo"),
                Option("10", value="10")
            )
        )
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-bind
    """
    if not signal_name:
        raise ValueError("data_bind requires a signal name.")
    return {"data-bind": signal_name}


def data_computed(
    signal_name: Signal,
    expr: Expression,
    *,
    case_: Case | None = None,
) -> dict[str, Expression]:
    """
    Creates a read-only signal that is computed based on an expression.

    The computed signal's value is automatically updated when any signals in the
    expression are updated. This helper only generates the single-signal form,
    `data-computed-signalName="expression"`.

    Args:
        signal_name: The name for the new computed signal.
        expr: The DataStar expression that defines the signal's value.
        case_: Converts the casing of the signal name (e.g., 'camel', 'kebab').

    Returns:
        A dictionary representing the data-computed attribute.

    Example:
        ```python
        from fasthtml.common import Div, data_text

        # Creates a signal 'foo' that is the sum of 'bar' and 'baz'.
        # Renders as: <div data-computed-foo="$bar + $baz"></div>
        Div(data_computed("foo", "$bar + $baz"))

        # The computed signal can then be used in other expressions.
        Div(data_computed("foo", "$bar + $baz")),
        Div(data_text("$foo"))

        # Using the case modifier.
        # Renders as: <div data-computed-my-signal__case.kebab="$bar + $baz"></div>
        Div(data_computed("mySignal", "$bar + $baz", case_="kebab"))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-computed
    """
    if not signal_name:
        raise ValueError("data_computed requires a signal name.")

    attr = f"data-computed-{kebabify(signal_name)}"
    if case_:
        attr += f"__case.{case_}"

    return {attr: expr}


def data_json_signals(
    *, include: str | None = None, exclude: str | None = None, terse: bool = False
) -> dict[str, Any]:
    """
    Sets the text content of an element to a reactive, JSON-stringified version of signals.

    This is primarily useful for debugging.

    Args:
        include: A regular expression string to include signals that match.
        exclude: A regular expression string to exclude signals that match.
        terse: If True, outputs a more compact JSON format without extra whitespace.

    Returns:
        A dictionary representing the data-json-signals attribute.

    Example:
        ```python
        from fasthtml.common import Pre

        # Display all signals.
        # Renders as: <pre data-json-signals></pre>
        Pre(data_json_signals())

        # Only show signals that include "user" in their path.
        # Renders as: <pre data-json-signals="{include: /user/}"></pre>
        Pre(data_json_signals(include="user"))

        # Show all signals except those ending with "temp".
        # Renders as: <pre data-json-signals="{exclude: /temp$/}"></pre>
        Pre(data_json_signals(exclude="temp$"))

        # Use the terse modifier for compact inline display.
        # Renders as: <pre data-json-signals__terse></pre>
        Pre(data_json_signals(terse=True))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-json-signals
    """
    attr = "data-json-signals"
    if terse:
        attr += "__terse"

    if not include and not exclude:
        return {attr: True}
    else:
        filters: list[str] = []
        if include:
            filters.append(f"include: /{include}/")
        if exclude:
            filters.append(f"exclude: /{exclude}/")
        value = f"{{{', '.join(filters)}}}"
        return {attr: value}


def data_on_signal_patch(
    expr: Expression,
    *,
    include: str | None = None,
    exclude: str | None = None,
    delay: Duration | None = None,
    debounce: Duration | None = None,
    throttle: Duration | None = None,
) -> dict[str, Any]:
    """
    Runs an expression whenever signals are patched (added, updated, or removed).

    If `include` or `exclude` filters are provided, this function will set both the
    `data-on-signal-patch` and `data-on-signal-patch-filter` attributes.

    Args:
        expr: The DataStar expression to execute when a signal changes.
        include: A regular expression string to watch signals that match.
        exclude: A regular expression string to ignore signals that match.
        delay: Delays the event listener, e.g., '500ms'.
        debounce: Debounces the event listener, e.g., '200ms'.
        throttle: Throttles the event listener, e.g., '1s'.

    Returns:
        A dictionary containing the necessary data-* attributes.

    Example:
        ```python
        from fasthtml.common import Div

        # Basic usage: log a message on any signal change.
        Div(data_on_signal_patch("console.log('A signal changed!')"))

        # Only react to changes in the 'counter' signal.
        Div(data_on_signal_patch("console.log('Counter changed!')", include="^counter$"))

        # Combine filters and timing modifiers.
        Div(
            data_on_signal_patch(
                "doSomething()",
                include="user",
                exclude="password",
                debounce="500ms"
            )
        )
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-on-signal-patch
    """
    result: dict[str, Any] = {}

    # Build the data-on-signal-patch attribute
    patch_attr = "data-on-signal-patch"
    if delay:
        patch_attr += f"__delay.{delay}"
    if debounce:
        patch_attr += f"__debounce.{debounce}"
    if throttle:
        patch_attr += f"__throttle.{throttle}"
    result[patch_attr] = expr

    # Build the data-on-signal-patch-filter attribute if needed
    if include or exclude:
        filters: list[str] = []
        if include:
            filters.append(f"include: /{include}/")
        if exclude:
            filters.append(f"exclude: /{exclude}/")
        filter_value = f"{{{', '.join(filters)}}}"
        result["data-on-signal-patch-filter"] = filter_value

    return result


def data_preserve_attr(*attr_names: str) -> dict[str, str]:
    """
    Preserves the value of one or more attributes when morphing DOM elements.

    Args:
        *attr_names: The names of the HTML attributes to preserve.

    Returns:
        A dictionary representing the data-preserve-attr attribute.

    Example:
        ```python
        from fasthtml.common import Details, Summary

        # Preserves the 'open' state of a details element during a DOM morph.
        # Renders as: <details data-preserve-attr="open">...</details>
        Details(
            Summary("Title"),
            "Content",
            data_preserve_attr("open"),
            open=True
        )

        # You can preserve multiple attributes.
        # Renders as: <details data-preserve-attr="open class">...</details>
        Details(
            ...,
            data_preserve_attr("open", "class")
        )
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-preserve-attr
    """
    if not attr_names:
        raise ValueError("data_preserve_attr requires at least one attribute name.")
    return {"data-preserve-attr": " ".join(attr_names)}


def data_ref(signal_name: Signal, *, case_: Case | None = None) -> dict[str, bool]:
    """
    Creates a new signal that is a reference to the element.

    The signal's value can then be used in expressions to reference the DOM element directly.

    Args:
        signal_name: The name for the new signal that will hold the element reference.
        case_: Converts the casing of the signal name (e.g., 'camel', 'kebab').

    Returns:
        A dictionary representing the data-ref attribute.

    Example:
        ```python
        from fasthtml.common import Div, Span, data_text

        # Creates a signal '$foo' that references the first div.
        # Renders as: <div data-ref-foo></div>
        Div(data_ref("foo")),
        Span(
            "$foo is a reference to a ",
            Span(data_text="$foo.tagName")),
            " element"
        )
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-ref
    """
    if not signal_name:
        raise ValueError("data_ref requires a signal name.")

    attr = f"data-ref-{signal_name}"
    if case_:
        attr += f"__case.{case_}"
    return {attr: True}


def data_indicator(
    signal_name: Signal, *, case_: Case | None = None
) -> dict[str, bool]:
    """
    Creates a boolean signal that is `true` while a fetch request is in flight.

    This is useful for showing loading spinners, disabling buttons, etc.

    Args:
        signal_name: The name for the new boolean signal.
        case_: Converts the casing of the signal name (e.g., 'camel', 'kebab').

    Returns:
        A dictionary representing the data-indicator attribute.

    Example:
        ```python
        from fasthtml.common import Button, Div, data_show, data_on

        # The 'fetching' signal will be true while the GET request is active.
        Button(
            "Fetch Data",
            data_on("click", "@get('/endpoint')"),
            data_indicator("fetching")
        )
        Div("Loading...", data_show("$fetching"))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-indicator
    """
    if not signal_name:
        raise ValueError("data_indicator requires a signal name.")

    attr = f"data-indicator-{signal_name}"
    if case_:
        attr += f"__case.{case_}"
    return {attr: True}


def data_on_load(
    expr: Expression,
    *,
    delay: Duration | None = None,
    viewtransition: bool = False,
) -> dict[str, Expression]:
    """
    Runs an expression when the element attribute is loaded into the DOM.

    This can happen on initial page load, when an element is patched into the DOM,
    or any time the attribute is modified.

    Args:
        expr: The DataStar expression to execute.
        delay: Delays the execution, e.g., '500ms', '1s'.
        viewtransition: If True, wraps the expression in `document.startViewTransition()`.

    Returns:
        A dictionary representing the data-on-load attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # Initialize a signal when the div is loaded.
        # Renders as: <div data-on-load="$count = 1"></div>
        Div(data_on_load("$count = 1"))

        # Use a delay modifier.
        # Renders as: <div data-on-load__delay.500ms="$count = 1"></div>
        Div(data_on_load("$count = 1", delay="500ms"))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-on-load
    """
    attr = "data-on-load"
    if delay:
        attr += f"__delay.{delay}"
    if viewtransition:
        attr += "__viewtransition"
    return {attr: expr}


def data_effect(expr: Expression) -> dict[str, Expression]:
    """
    Executes an expression on page load and whenever any signals in it change.

    This is useful for performing side effects, such as updating other signals,
    making requests, or manipulating the DOM.

    Args:
        expr: The DataStar expression to execute.

    Returns:
        A dictionary representing the data-effect attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # The signal '$foo' will be updated whenever '$bar' or '$baz' changes.
        # Renders as: <div data-effect="$foo = $bar + $baz"></div>
        Div(data_effect("$foo = $bar + $baz"))
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-effect
    """
    return {"data-effect": expr}


def data_ignore(*, self_only: bool = False) -> dict[str, bool]:
    """
    Instructs Datastar to ignore an element and (by default) its descendants.

    This can be useful for preventing conflicts with third-party libraries or when
    you are unable to escape user input.

    Args:
        self_only: If True, only ignore the element itself, not its descendants.

    Returns:
        A dictionary representing the data-ignore attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # Datastar will not process this div or its children.
        # Renders as: <div data-ignore>...</div>
        Div(
            Div("Datastar will not process this."),
            data_ignore()
        )

        # Ignore only the parent div, but process the child.
        # Renders as: <div data-ignore__self>...</div>
        Div(
            Div("Datastar WILL process this."),
            data_ignore(self_only=True)
        )
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-ignore
    """
    attr = "data-ignore"
    if self_only:
        attr += "__self"
    return {attr: True}


def data_ignore_morph() -> dict[str, bool]:
    """
    Tells the morphing engine to skip processing an element and its children.

    Returns:
        A dictionary representing the data-ignore-morph attribute.

    Example:
        ```python
        from fasthtml.common import Div

        # This element will not be morphed during DOM patching.
        # Renders as: <div data-ignore-morph></div>
        Div("This content is stable.", data_ignore_morph())
        ```

    See Also:
        https://data-star.dev/reference/attributes#data-ignore-morph
    """
    return {"data-ignore-morph": True}
