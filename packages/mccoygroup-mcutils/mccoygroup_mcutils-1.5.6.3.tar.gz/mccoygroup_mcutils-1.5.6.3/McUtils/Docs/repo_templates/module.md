# <a id="{id}">{name}</a> 
{include$:'includes/source_links.md'}
    
{description}

{$:"### Members\n" + objlink_grid(members, root=root) if nonempty(members) else ""}

{optional$:'long_description'}

{include$:'includes/footer.md'}