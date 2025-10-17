"""
Just a simple text table formatter with support for headers, separators, any kind of python formatting spec
etc.
"""
from __future__ import annotations

import itertools
import numpy as np

__all__ = [
    "TableFormatter"
]

class TableFormatter:

    __props__ = (
        "header_spans",
        "header_format",
        "column_join",
        "row_join",
        "header_column_join",
        "header_row_join",
        "separator",
        "separator_lines",
        "content_join",
        "column_alignments",
        "header_alignments",
        "row_padding",
    )

    default_header_format=""
    default_column_join = '  '
    default_row_join = '\n'
    default_separator = "-"
    default_column_alignment = '.'
    default_header_alignment = '^'
    default_row_padding = ""
    def __init__(self,
                 column_formats,
                 *,
                 headers=None,
                 header_spans=None,
                 header_format=None,
                 column_join=None,
                 row_join=None,
                 header_column_join=None,
                 header_row_join=None,
                 separator=None,
                 separator_lines=1,
                 content_join=None,
                 column_alignments=None,
                 header_alignments=None,
                 row_padding=None
                 ):
        self.headers = headers
        self.header_spans = header_spans
        self.header_format = header_format
        self.column_formats = column_formats
        self.column_alignments = column_alignments
        self.header_alignments = header_alignments
        self.column_join = column_join
        self.row_join = row_join
        self.header_column_join = header_column_join
        self.header_row_join = header_row_join
        self.separator = separator
        self.separator_lines = separator_lines
        self.content_join = content_join
        self.row_padding = row_padding

    @classmethod
    def prep_input_arrays(cls, headers, data, header_spans):
        if headers is not None:
            if isinstance(headers, np.ndarray):
                if headers.ndim == 1: headers = headers[np.newaxis]
                header_cols = headers.shape[1]
            else:
                if isinstance(headers[0], (str, float, int, np.integer, np.floating)):
                    headers = [headers]
                header_cols = max(len(h) for h in headers)
            if header_spans is None:
                header_spans = []
            elif isinstance(header_spans[0], (int, np.integer)):
                header_spans = [header_spans]
            header_spans = header_spans + [
                [1] * header_cols
            ] * (len(headers) - len(header_spans))
        else:
            header_cols = 0
            header_spans = None

        if isinstance(data, np.ndarray):
            data_cols = data.shape[1]
        else:
            data_cols = max(len(a) for a in data)

        max_cols = max([header_cols, data_cols])

        data = [
            list(d) + [""]*(max_cols - len(d))
            for d in data
        ]

        if headers is not None:
            headers = [
                list(h) + [""]*(max_cols - len(h))
                for h in headers
            ]
            # header_spans = [
            #     list(h) + [1]*(max_cols - len(h))
            #     for h in header_spans
            # ]

        return headers, data, header_spans
    @classmethod
    def custom_formatter(cls, f):
        if isinstance(f, str):
            return "{:" + f + "}" if not f.startswith("{") else f
        elif hasattr(f, 'format'):
            return f
        elif isinstance(f, (list, tuple)):
            fmt_func = cls.custom_formatter(f[0])
            pad = f[1] if len(f) > 1 else ""
            def format_iterable(obj, fmt_func=fmt_func, pad=pad):
                return pad.join(fmt_func.format(o) for o in obj)
            format_iterable.format = format_iterable
            return format_iterable
        else:
            def format_func(obj, f=f):
                return f(obj)
            format_func.format = format_func
            return format_func
    @classmethod
    def resolve_formatters(cls, ncols, col_formats):
        if isinstance(col_formats, str):
            col_formats = [col_formats]
        col_formats = list(col_formats)
        pad_formats = col_formats * (ncols//len(col_formats)+1)

        return pad_formats[:ncols]
    @classmethod
    def prep_formatters(cls, formats):
        if isinstance(formats, str):
            formats = [formats]
        return [
            cls.custom_formatter(f)
            for f in formats
        ]

    @classmethod
    def _format_entry(cls, data, fmt, strict=False):
        if strict:
            return fmt.format(data)
        else:
            try:
                return fmt.format(data)
            except ValueError:
                return str(data)

    @classmethod
    def format_tablular_data_columns(cls, data, formats, row_padding=None, strict=False):
        ncols = len(data[0])
        return [
            [
                (
                    row_padding + cls._format_entry(d[i], formats[i], strict=strict)
                        if row_padding is not None and i == 0 else
                    cls._format_entry(d[i], formats[i], strict=strict)
                ) for d in data
            ]
            for i in range(ncols)
        ]

    @classmethod
    def align_left(cls, col, width):
        f_spec = "{:<"+str(width)+"}"
        return [f_spec.format(c) for c in col]
    @classmethod
    def align_right(cls, col, width):
        f_spec = "{:>" + str(width) + "}"
        return [f_spec.format(c) for c in col]

    @classmethod
    def align_center(cls, col, width):
        f_spec = "{:^" + str(width) + "}"
        return [f_spec.format(c) for c in col]

    @classmethod
    def align_dot(cls, col, width, dot='.'):
        dot_pos = [c.rfind(dot) for c in col]
        dot_pos = [
            # find position from right to pad everything to the same number of spaces after the decimal
            len(c) - dp if dp > 0 else -1
            for c,dp in zip(col, dot_pos)
        ]
        max_dot_pos = max(dot_pos)
        col = [
            c + " "*(max_dot_pos - dp if dp > 0 else 0)
            for c,dp in zip(col, dot_pos)
        ]
        new_width = max(len(c) for c in col)
        return cls.align_right(col, max(width, new_width))
    supported_alignments = {
            '<':'align_left',
            '>':'align_right',
            '^':'align_center',
            '.':'align_dot'
        }
    @classmethod
    def resolve_aligner(cls, alignment): return getattr(cls, cls.supported_alignments[alignment])
    @classmethod
    def align_column(cls,
                     header_data, cols_data, header_alignment, column_alignment,
                     join_widths:list[int],
                     header_widths
                     ):
        if header_data is not None:
            header_width = max(len(c) for c in header_data)
        else:
            header_width = 0

        col_widths = [
            max(len(c) for c in col)
            for col in cols_data
        ]
        cols_data = [
            cls.resolve_aligner(al)(c, w)
            for c, w, al in zip(cols_data, col_widths, column_alignment)
        ]
        col_widths = [
            max(len(c) for c in col)
            for col in cols_data
        ]


        if header_data is not None:
            join_widths = list(join_widths)
            join_widths = (join_widths * len(col_widths))[:len(col_widths)]
            join_widths[0] = 0
            max_width = sum(col_widths)
            width = max([header_width, max_width]) + sum(join_widths)
            header_data = cls.resolve_aligner(header_alignment)(header_data, width)


            if len(col_widths) == 1:
                header_width = max(len(c) for c in header_data)
                width = max([header_width, max_width])# + sum(join_widths)*max(len(col_widths)-1, 0)
                cols_data = [
                    cls.resolve_aligner(al)(c, width+j)
                    for c, al,j in zip(cols_data, column_alignment, join_widths)
                ]

        # if format_data:
        # cols_data = [
        #     cls.resolve_aligner(al)(c, w)
        #     for c,w,al in zip(cols_data, col_widths, column_alignment)
        # ]
        return header_data, cols_data

    def format(self,
               headers_or_table, *table_data,
               header_format=None,
               header_spans=None,
               column_formats=None,
               column_alignments=None,
               header_alignments=None,
               column_join=None,
               row_join=None,
               header_column_join=None,
               header_row_join=None,
               separator=None,
               separator_lines=None,
               content_join=None,
               row_padding=None
               ):
        if len(table_data) == 0:
            headers = None
            table_data = headers_or_table
        elif len(table_data) > 1:
            raise ValueError("expected only one tabular data argument")
        else:
            headers = headers_or_table
            table_data = table_data[0]

        if headers is None: headers = self.headers
        if header_spans is None: header_spans = self.header_spans

        headers, table_data, header_spans = self.prep_input_arrays(headers, table_data, header_spans)

        if column_formats is None:
            if column_formats is None: column_formats = self.column_formats
        column_formats = self.resolve_formatters(len(table_data[0]), self.prep_formatters(column_formats))

        if column_alignments is None:
            if column_alignments is None: column_alignments = self.column_alignments
            if column_alignments is None: column_alignments = self.default_column_alignment
        if isinstance(column_alignments, str): column_alignments = [column_alignments]
        column_alignments = self.resolve_formatters(len(table_data[0]), column_alignments)

        for alignment in column_alignments:
            if alignment not in self.supported_alignments:
                raise ValueError("unknown alignment spec {}".format(alignment))

        if headers is not None:
            if header_alignments is None:
                if header_alignments is None: header_alignments = self.header_alignments
                if header_alignments is None: header_alignments = self.default_header_alignment
            if isinstance(header_alignments, str): header_alignments = [header_alignments]
            header_alignments = self.resolve_formatters(len(table_data[0]), header_alignments)

            for alignment in header_alignments:
                if alignment not in self.supported_alignments:
                    raise ValueError("unknown alignment spec {}".format(alignment))

        if headers is not None:
            if header_format is None: header_format = self.header_format
            if header_format is None: header_format = self.default_header_format
            header_format = self.resolve_formatters(len(headers[0]), self.prep_formatters(header_format))

        if headers is not None:
            header_columns = self.format_tablular_data_columns(headers, header_format)
        else:
            header_columns = None

        if row_padding is None: row_padding = self.row_padding
        if row_padding is None: row_padding = self.default_row_padding
        data_columns = self.format_tablular_data_columns(table_data, column_formats, row_padding)

        if column_join is None: column_join = self.column_join
        if column_join is None: column_join = self.default_column_join

        if headers is None:
            col_ = []
            sp = [1] * len(data_columns)
            split_cols = []
            split_alignments = []
            p = 0
            for s in sp:
                split_alignments.append(column_alignments[p:p + s])
                split_cols.append(data_columns[p:p + s])
                p += s

            for d,al in zip(split_cols, column_alignments):
                _, dc = self.align_column(
                    None, d,
                    None, al,
                    0, True
                )
                col_.extend(dc)

            data_columns = col_
        else:
            header_rows = []
            col_ = []

            join_width = (
               [len(column_join)]
                    if isinstance(column_join, str) else
                [len(j) for j in column_join]
                    if hasattr(column_join, "__getitem__") else
                [0]
            )

            join_width = [0] + (join_width * len(data_columns))
            join_width = join_width[:len(data_columns)]

            for i,sp in enumerate(header_spans):
                subcol = []

                header_subcol = [
                    [hc[i]]
                    for hc in header_columns
                ]

                split_cols = []
                split_alignments = []
                split_joins = []
                p = 0
                for s in sp:
                    split_alignments.append(column_alignments[p:p + s])
                    split_cols.append(data_columns[p:p + s])
                    split_joins.append(join_width[p:p + s])
                    p += s

                subrow = []
                # format_cols = i == 0
                for h,c,hal,cal,jw in zip(
                        header_subcol, split_cols,
                        header_alignments, split_alignments,
                        split_joins
                ):
                    hc, dc = self.align_column(
                        h, c,
                        hal, cal,
                        jw, True
                    )
                    subrow.extend(hc)
                    subcol.extend(dc)
                if len(col_) == 0:
                    col_ = subcol
                else:
                    col_ = [
                        c1 if len(c1[0]) >= len(c2[0]) else c2
                        for c1, c2 in zip(col_, subcol)
                    ]
            data_columns = col_

            for i, sp in enumerate(header_spans):
                header_subcol = [
                    [hc[i]]
                    for hc in header_columns
                ]

                split_cols = []
                split_alignments = []
                split_joins = []
                p = 0
                for s in sp:
                    split_alignments.append(column_alignments[p:p + s])
                    split_cols.append(data_columns[p:p + s])
                    split_joins.append(join_width[p:p + s])
                    p += s

                subrow = []
                # format_cols = i == 0
                for h, c, hal, cal, jw in zip(
                        header_subcol, split_cols,
                        header_alignments, split_alignments,
                        split_joins
                ):
                    hc, dc = self.align_column(
                        h, c,
                        hal, cal,
                        jw, True
                    )
                    subrow.extend(hc)
                header_rows.append(subrow)

        data_rows = [
            [dc[n] for dc in data_columns]
            for n in range(len(data_columns[0]))
        ]

        if row_join is None: row_join = self.row_join
        if row_join is None: row_join = self.default_row_join

        if isinstance(column_join, str):
            body_rows = [
                column_join.join(r) for r in data_rows
            ]
        else:
            joins = list(column_join) + [""] * (len(data_rows[0]) - len(column_join))
            body_rows = [
                "".join(
                    x
                    for body_join in zip(r, joins)
                    for x in body_join
                )
                for r in data_rows
            ]
        body = row_join.join(body_rows)

        if headers is not None:
            if header_column_join is None: header_column_join = self.header_column_join
            if header_column_join is None:
                if isinstance(column_join, str):
                    header_column_join = column_join
                else:
                    pos = np.cumsum(header_spans) - 1
                    header_column_join = [
                        column_join[p] if len(column_join) > p else
                        "" for p in pos
                    ]

            if isinstance(header_column_join, str):
                header_rows = [header_column_join.join(r) for r in header_rows]
            else:
                joins = list(header_column_join) + [""] * (len(header_rows[0]) - len(column_join))
                header_rows = [
                    "".join(
                        x
                        for body_join in zip(r, joins)
                        for x in body_join
                    )
                    for r in header_rows
                ]

            if header_row_join is None: header_row_join = self.header_row_join
            if header_row_join is None: header_row_join = row_join

            if separator is None: separator = self.separator
            if separator is None: separator = self.default_separator
            if separator_lines is None: separator_lines = self.separator_lines

            sep_line = (separator * len(header_rows[0]))[:len(header_rows[0])]
            header_rows = header_rows + [sep_line for i in range(separator_lines)]
            header = header_row_join.join(header_rows)

            if content_join is None: content_join = self.content_join
            if content_join is None: content_join = row_join
            body = content_join.join([header, body])


        return body





