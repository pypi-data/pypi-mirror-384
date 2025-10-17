
import os, shutil

from .DocWalker import DocWalker
from ..Formatters.TemplateEngine import ResourceLocator

__all__ = [
    "DocBuilder"
]

class DocBuilder:
    """
    A documentation builder class that uses a `DocWalker`
    to build documentation, but which also has support for more
    involved use cases, like setting up a `_config.yml` or other
    documentation template things.


    :related: .DocWalker.DocWalker, .DocWalker.ModuleWriter, .DocWalker.ClassWriter,
              .DocWalker.FunctionWriter, .DocWalker.MethodWriter, .DocWalker.ObjectWriter, .DocWalker.IndexWriter
    """

    defaults_root = os.path.dirname(__file__)
    default_config_file="_config.yml"

    def __init__(self,
                 packages=None,
                 config=None,
                 target=None,
                 root=None,
                 config_file=None,
                 templates_directory=None,
                 examples_directory=None,
                 tests_directory=None,
                 readme=None
                 ):
        """
        :param packages: list of package configs to write
        :type packages: Iterable[str|dict]
        :param config: parameters for _config.yml file
        :type config: dict
        :param target: target directory to which files should be written
        :type target: str
        :param root: root directory
        :type root: str
        :param root: root directory
        :type root: str
        """
        self.packages = packages
        self.config = config
        self.target = target
        self.root = root
        self.template_dir=self.get_template_locator(templates_directory, use_repo_templates='gh_repo' in self.config)
        self.examples_dir=examples_directory
        self.tests_directory=tests_directory
        self.config_file=self.default_config_file if config_file is None else config_file

        if isinstance(readme, str):
            if os.path.isfile(readme):
                with open(readme) as r:
                    readme = r.read()
        self.readme=readme

    default_template_extension = 'templates'
    default_repo_extension = 'repo_templates'
    def get_template_locator(self, template_directory, use_repo_templates=False):
        if not isinstance(template_directory, ResourceLocator):
            template_extension = [self.default_template_extension]
            if use_repo_templates:
                template_extension = [self.default_repo_extension] + template_extension
            tdirs = [os.path.dirname(os.path.abspath(__file__))]
            if template_directory is not None:
                if isinstance(template_directory, str):
                    template_directory = [template_directory]
                template_directory = list(template_directory)
                tdirs = list(template_directory) + tdirs
                template_directory = ResourceLocator([template_directory, (tdirs, template_extension)])
            else:
                template_directory = ResourceLocator([(tdirs, template_extension)])
        return template_directory

    config_defaults = {
        "theme":"McCoyGroup/finx",
        "gh_username":"McCoyGroup-bot",
        "footer": ""
    }
    def load_config(self):
        """
        Loads the config file to be used and fills in template parameters

        :return:
        :rtype:
        """
        cfg = self.config_defaults.copy()
        if self.config is not None:
            cfg.update(**self.config)
        self.config = cfg

        test_cfg = self.template_dir.locate(self.config_file)
        cfg_file = self.config_file if os.path.isfile(self.config_file) else (
            test_cfg if os.path.isfile(test_cfg) else self.template_dir.locate('_config.yml')
        )

        if os.path.isfile(cfg_file):
            print('reading config template from {}'.format(cfg_file))
            with open(cfg_file) as config_dump:
                cfg_string = config_dump.read().format(**cfg)

            return cfg_string

    def create_layout(self):
        """
        Creates the documentation layout that will be expanded upon by
        a `DocWalker`

        :return:
        :rtype:
        """

        if self.config is not None:
            conf = self.load_config()
            if isinstance(conf, str):
                config_file = os.path.join(self.target, '_config.yml') # hard coded for now, can change later
                print('writing config file to {}'.format(config_file))
                try:
                    os.makedirs(os.path.dirname(config_file))
                except OSError:
                    pass
                with open(config_file, 'w') as out:
                    out.write(conf)

        for fname in ['404.html', 'Contributing.md', 'Gemfile']:
            conf_file = os.path.join(self.target, fname)  # hard coded for now, can change later
            base_file = self.template_dir.locate(fname)
            if not os.path.isfile(conf_file) and os.path.isfile(fname):
                print('writing {} file to {}'.format(fname, fname))
                try:
                    os.makedirs(os.path.dirname(conf_file))
                except OSError:
                    pass
                shutil.copy(base_file, conf_file)

        # do other layout stuff maybe in the future?

    def load_walker(self):
        """
        Loads the `DocWalker` used to write docs.
        A hook that can be overriden to sub in different walkers.

        :return:
        :rtype:
        """
        return DocWalker(
            out=self.target,
            description=self.readme,
            template_locator=self.template_dir,
            examples_directory=self.examples_dir,
            tests_directory=self.tests_directory,
            **self.config
        )

    def build(self):
        """
        Writes documentation layout to `self.target`

        :return:
        :rtype:
        """
        print("using templates from {}".format(self.template_dir))
        print("using examples from {}".format(self.examples_dir))
        self.create_layout()
        walker = self.load_walker()
        return walker.write(self.packages)
