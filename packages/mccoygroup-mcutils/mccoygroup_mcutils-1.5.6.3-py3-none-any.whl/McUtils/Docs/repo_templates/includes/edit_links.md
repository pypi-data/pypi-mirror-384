
{html$:'Div', 
    grid([
    ['**Feedback**', '**Examples**', '**Templates**', '**Documentation**', '', '', ''],
    [
        '[Bug](https://github.com/{gh_username}/{gh_repo}/issues/new?title=Documentation%20Improvement%20Needed)/[Request](https://github.com/{gh_username}/{gh_repo}/issues/new?title=Example%20Request)',
        '[Edit](https://github.com/{gh_username}/{gh_repo}/edit/gh-pages/ci/examples/{url})/[New](https://github.com/{gh_username}/{gh_repo}/new/gh-pages/?filename=ci/examples/{url})',
        '[Edit](https://github.com/{gh_username}/{gh_repo}/edit/gh-pages/ci/docs/{url})/[New](https://github.com/{gh_username}/{gh_repo}/new/gh-pages/?filename=ci/docs/templates/{url})',
        '[Edit](https://github.com/{gh_username}/{gh_repo}/edit/{gh_branch}/{file_url}#L{lineno}?message=Update%20Docs)',
        '', '', ''
    ]
]),
    cls='text-secondary'
}