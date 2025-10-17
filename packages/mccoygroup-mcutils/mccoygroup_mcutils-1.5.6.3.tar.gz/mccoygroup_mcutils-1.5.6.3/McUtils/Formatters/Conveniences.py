
import numpy as np
from .TableFormatters import TableFormatter

__all__ = [
    "format_tensor_element_table",
    "format_symmetric_tensor_elements",
    "format_mode_labels",
    "format_zmatrix",
    "format_state_vector_frequency_table"
]

def format_tensor_element_table(inds, vals,
                                headers=("Indices", "Value"),
                                format="{:8.3f}",
                                column_join="|",
                                index_format="{:>5.0f}",
                                **etc
                                ):
    if isinstance(column_join, str):
        column_join = (" ", column_join)
    vals = np.asanyarray(vals)
    if vals.ndim == 1:
        vals = vals[:, np.newaxis]
    spans = [len(inds), vals.shape[-1]]
    return TableFormatter(
        column_formats=[index_format] * spans[0] + (
            [format] * spans[1]
                if isinstance(format, str) else
            format
        ),
        headers=headers,
        header_spans=spans,
        column_join=(
            [column_join[0]] * (spans[0]-1)
            + [column_join[1]]
            + [column_join[0]] * (vals.shape[-1]-1)
        ),
        **etc
    ).format(np.concatenate([np.array(inds).T, vals], axis=1))

def format_symmetric_tensor_elements(
        tensor,
        symmetries=None,
        cutoff=1e-6,
        headers=("Indices", "Value"),
        format="{:12.3f}",
        **etc
):
    tensor = np.asanyarray(tensor)
    if symmetries is None:
        symmetries = [np.arange(tensor.ndim)]

    symmetries = [np.sort(s) for s in symmetries]

    inds = np.where(np.abs(tensor) >= cutoff)
    if len(symmetries) > 0:
        inds_tests = [
            np.all(np.diff([inds[i] for i in symm], axis=0) >= 0, axis=0)
            for symm in symmetries
        ]
        inds_mask = np.all(inds_tests, axis=0)
        inds = tuple(x[inds_mask] for x in inds)

    vals = tensor[inds]

    return format_tensor_element_table(inds, vals, headers=headers, format=format, **etc)

def format_mode_labels(labels,
                       freqs=None,
                       high_to_low=True,
                       mode_index_format="{:.0f}",
                       frequency_format="{:.0f}",
                       headers=None,
                       column_join=" | ",
                       none_tag="mixed",
                       **etc
                       ):
    labels = [
        none_tag
            if lab.type is None else
        " ".join(t for t in lab.type if t is not None)
        for lab in labels
    ]

    if freqs is not None:
        return TableFormatter(
            [mode_index_format, frequency_format, "{}"],
            headers=("Mode", "Frequency", "Label") if headers is None else headers,
            column_join=column_join,
            **etc
        ).format([
            [i+1, f, lab]
            for i,(f,lab) in enumerate(zip(
                reversed(freqs) if high_to_low else freqs,
                reversed(labels) if high_to_low else labels
            ))
        ])
    else:
        return TableFormatter(
            [mode_index_format, "{}"],
            headers=("Mode", "Label") if headers is None else headers,
            column_join=column_join,
            **etc
        ).format([
            [i + 1, lab]
            for i, lab in enumerate(
                reversed(labels) if high_to_low else labels
            )
        ])

def format_zmatrix(zm, preserve_embedding=True, preserve_indices=True, list_form=True):
    max_ind = int(np.log10(max([max(z) for z in zm]))) + 2
    formatter = TableFormatter(
        f"{{:>{max_ind}.0f}}",
        column_join=", " if list_form else " ",
        row_padding=" [" if list_form else "",
        row_join="],\n" if list_form else "\n"
    )
    if not preserve_embedding:
        if isinstance(zm, np.ndarray):
            zm = zm.tolist()
        else:
            zm = [list(z) for z in zm]
        if len(zm[0]) == 4:
            zm[0][1] = ""
            zm[0][2] = ""
            zm[0][3] = ""

            zm[1][2] = ""
            zm[1][3] = ""

            zm[2][3] = ""
        else:
            zm[0][1] = ""
            zm[0][2] = ""

            zm[1][2] = ""

    if not preserve_indices:
        if len(zm[0]) == 4:
            zm = [z[1:] for z in zm[1:]]

    base = formatter.format(zm)
    if list_form:
        base = "[" + base[1:] + "]]"

    return base

def format_state_vector_frequency_table(state_list, freq_data,
                                        state_header="State",
                                        freq_header="Freq.",
                                        freq_fmt='{:.3f}',
                                        sep=" | ",
                                        join=" "
                                        ):
    state_cols = (
            len(state_list[0])
                if not isinstance(state_list[0], str) else
            1
    )
    freq_data = np.asanyarray(freq_data)
    if freq_data.ndim == 1:
        freq_data = freq_data[:, np.newaxis]
    freq_cols = freq_data.shape[-1]
    if isinstance(freq_fmt, str):
        freq_fmt = [freq_fmt] * freq_cols
    else:
        freq_fmt = list(freq_fmt) * freq_cols
        freq_fmt = freq_fmt[:freq_cols]

    if isinstance(freq_header, str):
        freq_header = [freq_header] * freq_cols
    else:
        freq_header = list(freq_header) * freq_cols
        freq_header = freq_header[:freq_cols]

    formatter = TableFormatter(
        [""] * state_cols + freq_fmt,
        headers=[state_header] + freq_header,
        header_spans=[state_cols] + [1] * freq_cols,
        column_join=[" "] * (state_cols - 1) + [sep] + [join] * (freq_cols - 1)
    )
    return formatter.format(
        [list(x) + v for x, v in zip(state_list, freq_data.tolist())]
    )
