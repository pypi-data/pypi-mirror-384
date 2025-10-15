#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow
requirements:
  MultipleInputFeatureRequirement: {}
  ScatterFeatureRequirement: {}
  StepInputExpressionRequirement: {}
  InlineJavascriptRequirement: {}
  SubworkflowFeatureRequirement: {}

inputs:
  samples:
    type:
      type: array
      items:
        type: record
        fields:
          sampleId: string

steps:
  make_file:
    run: staging_make_file.cwl
    scatter: sample
    in:
      sample: samples
      sampleId:
        valueFrom: ${ return inputs.sample['sampleId']; }
    out:
      [ output_file ]

  gather_files:
    run: staging_cat.cwl
    in:
      input_files: make_file/output_file
    out:
      [ output_file ]

outputs:
  output_file:
    type: File
    outputSource: gather_files/output_file

