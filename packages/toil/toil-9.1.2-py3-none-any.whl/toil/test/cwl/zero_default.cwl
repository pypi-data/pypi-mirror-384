#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: Workflow
requirements:
  MultipleInputFeatureRequirement: {}
  InlineJavascriptRequirement: {}
inputs:
  valueA:
    type: int?
    default: 0
  valueB:
    type: int?
  someFile:
    type: File?
steps:
  prev_step:
    run:
      class: ExpressionTool
      requirements:
        InlineJavascriptRequirement: {}
      inputs:
        someFile:
          type: File
      outputs:
        valueA:
          type: int
      expression: |
        ${
          return {valueA: 1};
        }
    in:
      someFile: someFile
    out: [valueA]
    when: $(inputs.someFile != null)
    
  main_step:
    run:
      class: ExpressionTool
      requirements:
        InlineJavascriptRequirement: {}
      inputs:
        valueA:
          type: int
      outputs:
        valueA:
          type: int
      expression: |
        ${
          return {valueA: inputs.valueA};
        }
    in:
      valueA:
        source: [prev_step/valueA, valueA]
        pickValue: first_non_null
    out: [valueA]
outputs:
  valueA:
    type: int
    outputSource: main_step/valueA


