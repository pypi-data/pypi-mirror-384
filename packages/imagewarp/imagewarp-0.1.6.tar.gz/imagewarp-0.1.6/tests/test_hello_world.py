"""This module tests the hello_world module."""

from imagewarp import hello_world


def test_hello():
    """A simple test."""
    known = "Hello World!"
    found = hello_world.greet()

    assert known == found
