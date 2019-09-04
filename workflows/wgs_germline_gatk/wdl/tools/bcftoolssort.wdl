version development

task bcftoolssort {
  input {
    Int? runtime_cpu
    Int? runtime_memory
    File vcf
    String outputFilename = "generated-1cb610cc-c3b0-11e9-917e-f218985ebfa7.sorted.vcf"
    String? outputType
    String? tempDir
  }
  command {
    bcftools sort \
      ${"--output-file " + if defined(outputFilename) then outputFilename else "generated-1cb6148c-c3b0-11e9-917e-f218985ebfa7.sorted.vcf"} \
      ${"--output-type " + outputType} \
      ${"--temp-dir " + tempDir} \
      ${vcf}
  }
  runtime {
    docker: "michaelfranklin/bcftools:1.9"
    cpu: if defined(runtime_cpu) then runtime_cpu else 1
    memory: if defined(runtime_memory) then "${runtime_memory}G" else "4G"
    preemptible: 2
  }
  output {
    File out = if defined(outputFilename) then outputFilename else "generated-1cb610cc-c3b0-11e9-917e-f218985ebfa7.sorted.vcf"
  }
}