import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from textformatter import *

def test_capitalize_words():
    assert capitalize_words("hello world") == "Hello World"

def test_remove_extra_spaces():
    assert remove_extra_spaces("hello   world") == "hello world"

def test_to_snake_case():
    assert to_snake_case("Hello World") == "hello_world"

def test_to_camel_case():
    assert to_camel_case("hello world") == "helloWorld"

def test_normalize():
    assert normalize("Hello@# 123!") == "hello 123"

print("✅ All tests passed successfully!")
