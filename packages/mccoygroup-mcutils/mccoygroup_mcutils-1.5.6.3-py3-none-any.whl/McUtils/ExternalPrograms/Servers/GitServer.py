from .NodeCommServer import ShellCommHandler

__all__ = [
    "GitHandler"
]

class GitHandler(ShellCommHandler):

    DEFAULT_CONNECTION = None
    DEFAULT_PORT_ENV_VAR = 'GIT_SOCKET_PORT'
    # DEFAULT_CONNECTION = os.path.expanduser("~/.gitsocket")
    def get_methods(self) -> 'dict[str,method]':
        return {
            'git':self.do_git
        }
    def do_git(self, args, kwargs):
        return self.subprocess_response("git", args)