import re

from ..Parsers import FileStreamReader, StringStreamReader
from ..Devutils import Logger, LogLevel, NullLogger, LoggingBlock
from ..Graphs import TreeWrapper

__all__ = [
    "Logger",
    "NullLogger",
    "LogLevel",
    "LogParser"
]


class LogParser(FileStreamReader):
    """
    A parser that will take a log file and stream it as a series of blocks
    """
    def __init__(self, file, block_settings=None, binary=False, block_level_padding=None, **kwargs):
        if block_settings is None:
            block_settings = LoggingBlock.block_settings
        self.block_settings = block_settings
        if block_level_padding is None:
            block_level_padding = LoggingBlock.block_level_padding
        self.block_level_padding = block_level_padding
        super().__init__(file, binary=binary, **kwargs)

    def get_block_settings(self, block_level):
        block_level_padding = self.block_level_padding
        if block_level >= len(self.block_settings):
            padding = block_level_padding * (block_level - len(self.block_settings) + 1)
            return {k: padding + v for k, v in self.block_settings[-1].items()}
        else:
            return self.block_settings[block_level]

    class LogBlockParser:
        """
        A little holder class that allows block data to be parsed on demand
        """
        def __init__(self, block_data, parent, block_depth):
            """
            :param block_data:
            :type block_data: str
            :param parent:
            :type parent: LogParser
            :param block_depth:
            :type block_depth: int
            """
            self.data = block_data
            self._lines = None
            self._tag = None
            self.parent = parent
            self.depth = block_depth

        @property
        def lines(self):
            if self._lines is None:
                self._tag, self._lines = self.parse_block_data()
            return self._lines
        @property
        def tag(self):
            if self._tag is None:
                self._tag, self._lines = self.parse_block_data()
            return self._tag

        def block_iterator(self, opener, closer,
                           preblock_handler=lambda c,w: w,
                           postblock_handler=lambda e:e,
                           start=0):

            where = self.data.find(opener, start)
            while where > -1:
                chunk = self.data[start:where]
                where = preblock_handler(chunk, where)
                end = self.data.find(closer, where)
                end = postblock_handler(end)
                subblock = self.data[where:end]
                start = end
                yield subblock, start
                where = self.data.find(opener, start)

        def line_iterator(self, pattern=""):
            og_settings = self.parent.get_block_settings(self.depth)
            prompt = og_settings['prompt'].format(meta="") + pattern
            raise NotImplementedError('Never finished the line iterator')

        def parse_prompt_blocks(self, chunk, prompt):
            splitsies = chunk.split("\n" + prompt)
            if splitsies[0] == "":
                splitsies = splitsies[1:]
            return splitsies

        def make_subblock(self, block):
            return type(self)(block, self.parent, self.depth+1)

        def parse_block_data(self):
            # find where subblocks are
            # parse around them
            og_settings = self.parent.get_block_settings(self.depth)
            prompt = og_settings['prompt'].split("{meta}", 1)[0]

            new_settings = self.parent.get_block_settings(self.depth+1)
            opener = "\n" + new_settings['opener'].split("{tag}", 1)[0]
            closer = "\n" + new_settings['closer'].split("{tag}", 1)[0]

            start = 0
            lines = []

            with StringStreamReader(self.data) as parser:
                header = parser.parse_key_block(None, {"tag":opener, "skip_tag":False})
                if header is not None:
                    lines.extend(self.parse_prompt_blocks(header, prompt))
                    block = parser.parse_key_block(None, {"tag":closer, "skip_tag":True})
                    if block is None:
                        raise ValueError("unclosed block found at position {} in stream '{}'".format(parser.tell(), parser.read()))
                    lines.append(self.make_subblock(block))
                    # print("??", parser.stream.read(1))
                    while header is not None:
                        header = parser.parse_key_block(None, {"tag":opener, "skip_tag":False})
                        curp = parser.tell()
                        if header is None:
                            break #
                        lines.extend(self.parse_prompt_blocks(header, prompt))
                        block = parser.parse_key_block(None, {"tag":closer, "skip_tag":True})
                        if block is None:
                            parser.seek(curp)
                            raise ValueError("unclosed block found at position {} in stream (from block '{}')".format(curp, parser.read(-1)))
                        lines.append(self.make_subblock(block))

                rest = parser.stream.read()
                lines.extend(self.parse_prompt_blocks(rest, prompt))

            tag_start = og_settings['opener'].split("{tag}", 1)[0]
            tag_end = og_settings['opener'].split("{tag}", 2)[-1]
            tag = lines[0]
            if tag_start != "":
                tag = tag.split(tag_start, 1)[-1]
            if tag_end != "":
                tag = tag.split(tag_end)[0]
            else:
                tag = tag.split("\n")[0]
            tag = tag.strip()

            block_end = "\n" + og_settings['closer'].split("{tag}", 1)[0]
            if isinstance(lines[-1], str):
                lines[-1] = lines[-1].split(block_end, 1)[0]

            return tag, lines[1:]

        def __repr__(self):
            return "{}('{}', #records={})".format(
                type(self).__name__,
                self.tag,
                len(self.lines)
            )

        def to_tree(self, tag_filter=None, depth=-1, combine_subtrees=True):
            tag, lines = self.tag, self.lines
            if depth < 0 or depth > 0:
                lines = [
                    b.to_tree(depth-1)
                        if not isinstance(b, str) else
                    b
                    for b in lines
                    if not (
                            not isinstance(b, str)
                            and self.parent.tag_match(b.tag, tag_filter)
                    )
                ]
                lines = self.parent.post_process_treelist(lines, combine_subtrees=combine_subtrees)

            if tag is not None:
                return {tag:lines}
            else:
                return lines

    def get_block(self, level=0, tag=None):
        """
        :param level:
        :type level:
        :param tag:
        :type tag:
        :return:
        :rtype:
        """

        block_settings = self.get_block_settings(level)
        if tag is None:
            opener = block_settings['opener'].split("{tag}", 1)[0]
        else:
            opener_split = block_settings['opener'].split("{tag}", 1)
            opener = opener_split[0]
            if len(opener_split) > 1:
                opener += " {} ".format(tag)

        if tag is None:
            closer = block_settings['closer'].split("{tag}", 1)[0]
        else:
            close_split = block_settings['closer'].split("{tag}", 1)
            closer = close_split[0]
            if len(close_split) > 1:
                closer += " {} ".format(tag)

        block_data = self.parse_key_block(opener, "\n"+closer, mode="Single", parser=lambda x:x) #type: str
        if block_data is None:
            raise ValueError("no more blocks")
        # I now need to process get_block further...
        block_data = opener + block_data.split("\n"+closer, 1)[0]

        return self.LogBlockParser(block_data, self, level)

    def get_line(self, level=0, tag=None):
        """
        :param level:
        :type level:
        :param tag:
        :type tag:
        :return:
        :rtype:
        """

        block_settings = self.get_block_settings(level)
        prompt = block_settings['prompt'].split("{meta}", 1)[0]
        if tag is not None:
            prompt += " {}".format(tag)

        # at some point I can try to refactor to keep the header info or whatever
        block_data = self.parse_key_block({'tag':"\n" + prompt, 'skip_tag':True}, {"tag":"\n", 'skip_tag': False}, mode="Single", parser=lambda x:x) #type: str
        if block_data is None:
            raise ValueError("no more lines")

        return block_data

    def get_blocks(self, tag=None, level=0):
        while True: # would be nice to have a smarter iteration protocol but ah well...
            try:
                next_block = self.get_block(level=level, tag=tag)
            except ValueError as e:
                args = e.args
                if len(args) == 1 and isinstance(args[0], str) and args[0] == "no more blocks":
                    return None
                raise
            else:
                if next_block is None:
                    return None
                yield next_block

    def get_lines(self, tag=None, level=0):
        while True: # would be nice to have a smarter iteration protocol but ah well...
            try:
                next_block = self.get_line(level=level, tag=tag)
            except ValueError as e:
                args = e.args
                if len(args) == 1 and isinstance(args[0], str) and args[0] == "no more lines":
                    return None
                raise
            else:
                if next_block is None:
                    return None
                yield next_block

    @classmethod
    def tag_match(cls, tag, tag_filter):
        if tag_filter is None or tag is None: return False
        elif isinstance(tag_filter, (str, re.Pattern)):
            return re.match(tag_filter, tag)
        elif callable(tag_filter):
            return tag_filter(tag)
        else:
            return tag in tag
    @classmethod
    def post_process_treelist(cls, res, combine_subtrees=True):
        if len(res) == 1:
            res = res[0]
        elif combine_subtrees and all(isinstance(r, dict) for r in res):
            nice_tree = {}
            key_conflicts = False
            for r in res:
                for k,v in r.items():
                    key_conflicts = k in nice_tree
                    if key_conflicts:
                        break
                    nice_tree[k] = v
                if key_conflicts:
                    break
            else:
                res = nice_tree
        return res
    def to_tree(self, tag_filter=None, depth=-1, combine_subtrees=True):
        res = []
        for b in self.get_blocks():
            if self.tag_match(b.tag, tag_filter): continue
            if depth < 0 or depth > 0:
                subtree = b.to_tree(tag_filter=tag_filter, depth=depth - 1, combine_subtrees=combine_subtrees)
            else:
                subtree = b
            res.append(subtree)

        return TreeWrapper(self.post_process_treelist(res, combine_subtrees=combine_subtrees))
