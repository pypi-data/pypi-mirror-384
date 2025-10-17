import os
import streamlit.components.v1 as components

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
# (This is, of course, optional - there are innumerable ways to manage your
# release process.)
_RELEASE = True
# Declare a Streamlit component. `declare_component` returns a function
# that is used to create instances of the component. We're naming this
# function "_component_func", with an underscore prefix, because we don't want
# to expose it directly to users. Instead, we will create a custom wrapper
# function, below, that will serve as our component's public API.

# It's worth noting that this call to `declare_component` is the
# *only thing* you need to do to create the binding between Streamlit and
# your component frontend. Everything else we do in this file is simply a
# best practice.

if not _RELEASE:
    _component_func = components.declare_component(
        # We give the component a simple, descriptive name ("my_component"
        # does not fit this bill, so please choose something better for your
        # own component :)
        "streamlit_lexical_extended",
        # Pass `url` here to tell Streamlit that the component will be served
        # by the local dev server that you run via `npm run start`.
        # (This is useful while your component is in development.)
        url="http://localhost:3001",
    )
else:
    # When we're distributing a production version of the component, we'll
    # replace the `url` param with `path`, and point it to the component's
    # build directory:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("streamlit_lexical_extended", path=build_dir)


# Create a wrapper function for the component. This is an optional
# best practice - we could simply expose the component function returned by
# `declare_component` and call it done. The wrapper allows us to customize
# our component's API: we can pre-process its input args, post-process its
# output value, and add a docstring for users.


def streamlit_lexical_extended(
    value="",
    placeholder="",
    height=None,
    min_height=400,
    debounce=500,
    key=None,
    overwrite=True,
    on_change=None,
):
    """Create a new instance of "streamlit_lexical_extended".

    Parameters
    ----------
    value: str
        Optional initial value to pass to editor
    placeholder: str
        Optional initial placeholder text to display in editor
    height: int or None
        Fixed height in pixels. If specified, editor will have this exact height.
        If None, editor will auto-expand to fit content (respecting min_height).
    min_height: int
        Minimum height in pixels. Default is 400. Editor will never be smaller than this.
        Only used when height is None (auto-expand mode).
    debounce: int
        Time delay to save editor contents in milliseconds. Default is 500 ms.
    key: str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.
    overwrite: bool
        Whether to overwrite the existing value in the editor. Default is True.
    on_change: function
        Optional callback function that is called when the editor content changes.

    Returns
    -------
    str
        Markdown string of content in editor

    """
    assert debounce > 0, "Debounce must be greater than 0."
    assert min_height > 0, "min_height must be greater than 0."
    if height is not None:
        assert height > 0, "height must be greater than 0."

    component_value = _component_func(
        value=value,
        placeholder=placeholder,
        height=height,
        min_height=min_height,
        debounce=debounce,
        key=key,
        overwrite=overwrite,
        on_change=on_change,
    )
    return component_value
