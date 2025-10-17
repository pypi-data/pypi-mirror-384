## <a id="{id}">{name}</a> 

{include$:'includes/source_links.md'}

{description}
{include$:'includes/parameters.md'}

{%:prop_list=code(loop_template(
    "{{0[0]}}: {{0[1]}}",
    [[p[0], p[1].__name__ if isinstance(p[1], type) else type(p[1]).__name__] for p in props],
    joiner="""
"""
)) if len(props) > 0 else ""}

{%:method_list=[
    m.handle(write=False).strip()
    for m in methods
]}

{collapse$:
    "## Methods and Properties", 
    prop_list + "\n" + join(method_list, joiner="\n\n\n"),
    name="methods",
    open=not nonempty(examples) or nonempty(tests)
}

{include$:'includes/footer.md'}