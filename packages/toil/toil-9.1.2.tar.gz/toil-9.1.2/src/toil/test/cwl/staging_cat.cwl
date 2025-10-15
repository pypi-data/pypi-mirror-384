#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: [ "bash", "run.sh" ]

requirements:
  DockerRequirement: # <- this is the part that causes the error
    dockerPull: ubuntu:latest
  InitialWorkDirRequirement:
    listing:
      - entryname: some_dir # <- put all the input files into a dir
        writable: true
        entry: "$({class: 'Directory', listing: inputs.input_files})"
      - entryname: run.sh
        entry: |-
          for i in \$(find some_dir -type f); do cat \$i ; done

stdout: output.txt

inputs:
  input_files:
    type: File[]

outputs:
  output_file:
    type: stdout
