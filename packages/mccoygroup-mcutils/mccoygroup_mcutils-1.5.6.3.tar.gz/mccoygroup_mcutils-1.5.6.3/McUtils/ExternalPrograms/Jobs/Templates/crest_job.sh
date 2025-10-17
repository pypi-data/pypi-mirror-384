#!/bin/bash

{process_setup}

input_file="{geom_file}"
cat > "$input_file" <<- EOM
{system}
EOM

{crest_path} "$input_file" {command_line} > "{log_file}"