import unittest

from janis import Input, String, Step, Directory, Workflow, Array, Output
from janis_bioinformatics.data_types import FastaWithDict, Fastq, VcfIdx, VcfTabix
from janis_bioinformatics.tools.common import AlignSortedBam
import janis_bioinformatics.tools.gatk4 as GATK4


class TestSomaticPipeline(unittest.TestCase):


    def subpipeline(self):

        w = Workflow("somatic_subpipeline")

        # Declare inputs  Input("inputIdentifier", InputType())
        reference = Input('reference', FastaWithDict())
        inputs = Input('inputs', Array(Fastq()))
        knownSites = Input('knownSites', Array(VcfIdx()))

        # Declare steps   Step("stepIdentifier", Tool())
        read_group_header_line = Input('read_group_header_line', String())
        tmpdir = Input('tmpdir', Directory())

        s1_align_sortedbam = Step('align_sortedbam', AlignSortedBam())
        s2_mergeSam = Step('mergeSam', GATK4.Gatk4MergeSamFiles_4_0())
        s3_markDup = Step('makrDup', GATK4.Gatk4MarkDuplicates_4_0())
        s4_baseRecal = Step('baseRecal', GATK4.Gatk4BaseRecalibrator_4_0())
        s5_applyBQSR = Step('applyBQSR', GATK4.Gatk4ApplyBqsr_4_0())


        # Join steps like w.add_edge(start.out, step.in)
        w.add_edges([
            (reference, s1_align_sortedbam),
            (read_group_header_line, s1_align_sortedbam.read_group_header_line),
            (inputs, s1_align_sortedbam.fastq),
            (tmpdir, s1_align_sortedbam)
        ])

        w.add_edges([
            (s1_align_sortedbam.o3_sortsam, s2_mergeSam.input),
            (tmpdir, s2_mergeSam.tmpDir)
        ])
        w.add_default_value(s2_mergeSam.createIndex, True)
        w.add_default_value(s2_mergeSam.useThreading, True)
        w.add_default_value(s2_mergeSam.maxRecordsInRam, 5000000)
        w.add_default_value(s2_mergeSam.validationStringency, 'SILENT')

        w.add_edges([
            (s2_mergeSam.output, s3_markDup.input),
            (tmpdir, s3_markDup.tmpDir)
        ])
        w.add_default_value(s3_markDup.createIndex, True)
        w.add_default_value(s3_markDup.maxRecordsInRam, 5000000)

        w.add_edges([
            (s3_markDup.output, s4_baseRecal.input),
            (tmpdir, s4_baseRecal.tmpDir),
            (reference, s4_baseRecal.reference),
            (knownSites, s4_baseRecal.knownSites)
        ])

        w.add_edges([
            (reference, s5_applyBQSR.reference),
            (s4_baseRecal.output, s5_applyBQSR.recalFile),
            (s3_markDup.output, s5_applyBQSR.input),
            (tmpdir, s5_applyBQSR.tmpDir)
        ])

        # Declare outputs like w.add_edge(step.out, Output("outputIdentifier"))
        w.add_edges([
            (s5_applyBQSR, Output('output_bam')),
            (s3_markDup.metrics, Output('markDup_metrics')),
            (s4_baseRecal, Output('recal_table'))
        ])

        # w.dump_cwl(to_disk=True, with_docker=False)
        return w


    def test_pipeline(self):

        w = Workflow("somatic_pipeline")

        normalInputs = Input('normalInputs', Array(Fastq()))
        tumorInputs = Input('tumorInputs', Array(Fastq()))

        normal_read_group_header_line = Input('normal_read_group_header_line', String())
        tumor_read_group_header_line = Input('tumor_read_group_header_line', String())


        # Declare inputs  Input("inputIdentifier", InputType())
        reference = Input('reference', FastaWithDict())
        knownSites_dbSNP = Input('dbSNP', VcfIdx())
        knownSites_1000GP = Input('1000GP', VcfTabix())
        knownSites_OMNI = Input('OMNI', VcfTabix())
        knownSites_HAPMAP = Input('HAPMAP', VcfTabix())

        # Declare steps   Step("stepIdentifier", Tool())
        tmpdir = Input('tmpdir', Directory())

        s_tum = Step("tumor", self.subpipeline())
        s_norm = Step("normal", self.subpipeline())
        s_mutect = Step("mutect", GATK4.GatkMutect2_4_0())


        for s,i,h in [(s_tum, tumorInputs, tumor_read_group_header_line),
                  (s_norm, normalInputs, normal_read_group_header_line)]:
            w.add_edges([
                (reference, s.reference),
                (h, s.read_group_header_line),
                (i, s.inputs),
                (tmpdir, s.tmpdir),
                (knownSites_1000GP, s.knownSites),
                (knownSites_dbSNP, s.knownSites),
                (knownSites_HAPMAP, s.knownSites),
                (knownSites_OMNI, s.knownSites)
            ])

        w.add_edges([
            (reference, s_mutect),
            (s_tum, s_mutect.tumor),
            (s_norm, s_mutect.normal)
        ])

        w.add_edge(Input("tumorName", String()), s_mutect.tumorName)
        w.add_edge(Input("normalName", String()), s_mutect.normalName)


        w.add_edges([
            (s_mutect, Output("somatic_vcf")),
            # (s_validate.summaryMetrics, Output("summaryMetrics"))
        ])

        # w.draw_graph()

        w.dump_translation("cwl", to_disk=True, with_docker=False)
