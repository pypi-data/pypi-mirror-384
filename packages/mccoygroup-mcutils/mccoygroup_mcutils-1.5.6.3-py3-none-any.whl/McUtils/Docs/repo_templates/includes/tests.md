

{assign%:test_links={loop_template$:
    """- [{{k}}](#{{k}})""",
    k=tests['names'],
    joiner='\n'
}}

{%:setup=apply('''
Before we can run our examples we should get a bit of setup out of the way.
Since these examples were harvested from the unit tests not all pieces
will be necessary for all situations.

All tests are wrapped in a test class
```python
{{class_setup}}
```
''',
    class_setup=tests['class_setup']
)}
{%:test_setup=collapse('### Setup', setup)}
{%:example_template="""#### <a name="{{name}}">{{name}}</a>
```python
{{body}}
```
"""}
{%:test_examples=loop_template(example_template,
    name=tests['names'],
    body=tests['tests'],
    joiner='\n'
)}

{%:test_body=collapse(
    '## Tests',
    join(
        test_links,
        test_setup,
        test_examples,
        joiner="\n"
    )
)}

{$:test_body if len(tests['names']) > 0 else ""}