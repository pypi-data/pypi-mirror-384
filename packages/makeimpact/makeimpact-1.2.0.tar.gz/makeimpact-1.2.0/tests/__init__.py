"""
Test package initialization.

This file is mostly empty because it mainly serves to mark the 'tests' directory
as a Python package, making the test modules importable.

== Setting up the API key for tests ==

The tests look for an environment variable called 'TEST_API_KEY'.
You can set this in your terminal before running tests:

On Linux/Mac:
    export TEST_API_KEY=your_sandbox_api_key_here
    pytest

On Windows:
    set TEST_API_KEY=your_sandbox_api_key_here
    pytest

You can also create a .env file in the project root with:
    TEST_API_KEY=your_sandbox_api_key_here

And then use python-dotenv in the test file to load it:
    from dotenv import load_dotenv
    load_dotenv()
"""
