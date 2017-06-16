#!/usr/bin/python2

import os
import sys
import unittest
from data_files import *
from collections import OrderedDict
from os.path import join

try:
    from process.sequence import AlignmentList, Alignment
    from process.error_handling import *
    from process.data import Partitions
except ImportError:
    from trifusion.process.sequence import AlignmentList, Alignment
    from trifusion.process.error_handling import *
    from trifusion.process.data import Partitions


class ExpectingTestCase(unittest.TestCase):
    def run(self, result=None):
        self._result = result
        self._num_expectations = 0
        super(ExpectingTestCase, self).run(result)

    def _fail(self, failure):
        try:
            raise failure
        except failure.__class__:
            self._result.addFailure(self, sys.exc_info())

    def expect_true(self, a, msg):
        if not a:
            self._fail(self.failureException(msg))
        self._num_expectations += 1

    def expect_equal(self, a, b, msg=''):
        if a != b:
            msg = '({}) Expected {} to equal {}. '.format(
                self._num_expectations, a, b) + msg
            self._fail(self.failureException(msg))
        self._num_expectations += 1

sql_db = "sequencedb"

data_path = join("trifusion/tests/data/")

class PartitonsTest(ExpectingTestCase):

    def setUp(self):

        self.aln_obj = AlignmentList(dna_data_fas, sql_db=sql_db)
        self.aln_obj.partitions.reset()

    def tearDown(self):

        self.aln_obj.clear_alignments()
        os.remove(sql_db)

    def test_read_from_nexus(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_parNex[0])

        self.assertEqual(len(self.aln_obj.partitions.partitions), 7)

    def test_read_from_phylip(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_par[0])

        self.assertEqual(len(self.aln_obj.partitions.partitions), 7)

    def test_get_partition_names(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_par[0])

        res = self.aln_obj.partitions.get_partition_names()

        self.assertEqual(res, ["BaseConc1.fas", "BaseConc2.fas",
                               "BaseConc3.fas", "BaseConc4.fas",
                               "BaseConc5.fas", "BaseConc6.fas",
                               "BaseConc7.fas"])

    def test_get_partition_names_withCodon(self):

        self.aln_obj.partitions.read_from_file(
            concatenated_smallCodon_parNex[0])

        res = self.aln_obj.partitions.get_partition_names()

        self.assertEqual(res, ["BaseConc1.fas_1_1", "BaseConc1.fas_1_2",
                               "BaseConc1.fas_1_3", "BaseConc2.fas",
                               "BaseConc3.fas", "BaseConc4.fas",
                               "BaseConc5.fas", "BaseConc6.fas",
                               "BaseConc7.fas"])

    def test_single_partition(self):

        self.aln_obj = AlignmentList([dna_data_fas[0]],
                                     db_con=self.aln_obj.con,
                                     db_cur=self.aln_obj.cur)

        self.assertTrue(self.aln_obj.partitions.is_single())

    def test_multiple_partitions(self):

        self.assertFalse(self.aln_obj.partitions.is_single())

    def test_remove_partition_from_name(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_parNex[0])
        self.aln_obj.partitions.remove_partition("BaseConc3.fas")

        # Check keys from partitions, partitions_alignment and models
        key_data = [list(self.aln_obj.partitions.partitions.keys()),
                    list(self.aln_obj.partitions.partitions_alignments.keys()),
                    list(self.aln_obj.partitions.models.keys())]

        self.expect_equal(key_data,
                          [["BaseConc1.fas", "BaseConc2.fas",
                           "BaseConc4.fas",
                           "BaseConc5.fas", "BaseConc6.fas",
                           "BaseConc7.fas"]] * 3)

        # Check if remaining partition ranges are continuous
        cont = True
        prev = 0
        for r in self.aln_obj.partitions.partitions.values():
            if r[0][0] == prev:
                prev = r[0][1] + 1
            else:
                cont = False

        self.expect_equal(cont, True)

    def test_remove_partition_from_file(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_parNex[0])
        self.aln_obj.partitions.remove_partition("BaseConc3.fas")

        # Check keys from partitions, partitions_alignment and models
        key_data = [list(self.aln_obj.partitions.partitions.keys()),
                    list(self.aln_obj.partitions.partitions_alignments.keys()),
                    list(self.aln_obj.partitions.models.keys())]

        self.expect_equal(key_data,
                          [["BaseConc1.fas", "BaseConc2.fas",
                            "BaseConc4.fas",
                            "BaseConc5.fas", "BaseConc6.fas",
                            "BaseConc7.fas"]] * 3)

        # Check if remaining partition ranges are continuous
        cont = True
        prev = 0
        for r in self.aln_obj.partitions.partitions.values():
            if r[0][0] == prev:
                prev = r[0][1] + 1
            else:
                cont = False

        self.expect_equal(cont, True)

    def test_change_name(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_parNex[0])

        self.aln_obj.partitions.change_name("BaseConc1.fas", "OtherName")

        key_data = [list(self.aln_obj.partitions.partitions.keys()),
                    list(self.aln_obj.partitions.partitions_alignments.keys()),
                    list(self.aln_obj.partitions.models.keys())]

        self.expect_equal(key_data,
                          [["BaseConc2.fas",
                           "BaseConc3.fas", "BaseConc4.fas",
                           "BaseConc5.fas", "BaseConc6.fas",
                           "BaseConc7.fas", "OtherName"]] * 3)

        # Check if remaining partition ranges are continuous
        cont = True
        prev = 0

        self.aln_obj.partitions.partitions = OrderedDict(sorted(
            self.aln_obj.partitions.partitions.iteritems(),
            key=lambda x: x[1][0]
        ))

        for r in self.aln_obj.partitions.partitions.values():
            if r[0][0] == prev:
                prev = r[0][1] + 1
            else:
                cont = False

        self.expect_equal(cont, True)

    def test_merge_partitions(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_parNex[0])

        self.aln_obj.partitions.merge_partitions(
            ["BaseConc1.fas", "BaseConc2.fas", "BaseConc3.fas", "BaseConc4.fas",
             "BaseConc5.fas", "BaseConc6.fas", "BaseConc7.fas"], "New_part")

        key_data = [list(self.aln_obj.partitions.partitions.keys()),
                    list(self.aln_obj.partitions.partitions_alignments.keys()),
                    list(self.aln_obj.partitions.models.keys())]

        self.assertEqual(key_data, [["New_part"]] * 3)

    def test_split_partition(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_parNex[0])

        self.aln_obj.partitions.split_partition("BaseConc1.fas",
                                                [(0, 50), (51, 84)],
                                                ["part1", "part2"])

        key_data = [list(self.aln_obj.partitions.partitions.keys()),
                    list(self.aln_obj.partitions.partitions_alignments.keys()),
                    list(self.aln_obj.partitions.models.keys())]

        self.expect_equal(key_data,
                          [["BaseConc2.fas",
                            "BaseConc3.fas", "BaseConc4.fas",
                            "BaseConc5.fas", "BaseConc6.fas",
                            "BaseConc7.fas", "part1", "part2"]] * 3)

        # Check if remaining partition ranges are continuous
        cont = True
        prev = 0

        self.aln_obj.partitions.partitions = OrderedDict(sorted(
            self.aln_obj.partitions.partitions.iteritems(),
            key=lambda x: x[1][0]
        ))

        for r in self.aln_obj.partitions.partitions.values():
            if r[0][0] == prev:
                prev = r[0][1] + 1
            else:
                cont = False

        self.expect_equal(cont, True)

    def test_model_detection(self):

        self.aln_obj = AlignmentList(models_nexus_data,
                                     db_con=self.aln_obj.con,
                                     db_cur=self.aln_obj.cur)

        self.assertEqual(self.aln_obj.partitions.models,
                         OrderedDict([('Teste1.fas', [
                             [['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None], []]), ('Teste2.fas', [
                             [['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None], []]), ('Teste3.fas', [
                             [['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None], []]), ('Teste4.fas', [
                             [['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None], []]), ('Teste5.fas', [
                             [['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None], []]), ('Teste6.fas', [
                             [['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None], []]), ('Teste7.fas', [
                             [['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None], []])]))

    def test_model_detection_codons(self):

        self.aln_obj = AlignmentList(models_codon_nexus_data,
                                     db_cur=self.aln_obj.cur,
                                     db_con=self.aln_obj.con)

        self.assertEqual(self.aln_obj.partitions.models,
                         OrderedDict([('Teste1.fas_1', [
                             [['nst=2', 'statefreqpr=dirichlet(1,1,1,1)'],
                              ['nst=6', 'statefreqpr=fixed(equal)'],
                              ['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None, None, None], []]), ('Teste2.fas_86', [
                             [['nst=2', 'statefreqpr=dirichlet(1,1,1,1)'],
                              ['nst=6', 'statefreqpr=fixed(equal)'],
                              ['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None, None, None], []]), ('Teste3.fas_171', [
                             [['nst=2', 'statefreqpr=dirichlet(1,1,1,1)'],
                              ['nst=6', 'statefreqpr=fixed(equal)'],
                              ['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None, None, None], []]), ('Teste4.fas_256', [
                             [['nst=2', 'statefreqpr=dirichlet(1,1,1,1)'],
                              ['nst=6', 'statefreqpr=fixed(equal)'],
                              ['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None, None, None], []]), ('Teste5.fas_341', [
                             [['nst=2', 'statefreqpr=dirichlet(1,1,1,1)'],
                              ['nst=6', 'statefreqpr=fixed(equal)'],
                              ['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None, None, None], []]), ('Teste6.fas_426', [
                             [['nst=2', 'statefreqpr=dirichlet(1,1,1,1)'],
                              ['nst=6', 'statefreqpr=fixed(equal)'],
                              ['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None, None, None], []]), ('Teste7.fas_511', [
                             [['nst=2', 'statefreqpr=dirichlet(1,1,1,1)'],
                              ['nst=6', 'statefreqpr=fixed(equal)'],
                              ['nst=6', 'statefreqpr=dirichlet(1,1,1,1)']],
                             [None, None, None], []])]))

    def test_set_model(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_parNex[0])

        self.aln_obj.partitions.set_model("BaseConc1.fas", ["GTR"])

        self.assertEqual(self.aln_obj.partitions.models,
                         OrderedDict([('BaseConc1.fas', [[[]], ['GTR'], []]),
                                      ('BaseConc2.fas', [[[]], [None], []]),
                                      ('BaseConc3.fas', [[[]], [None], []]),
                                      ('BaseConc4.fas', [[[]], [None], []]),
                                      ('BaseConc5.fas', [[[]], [None], []]),
                                      ('BaseConc6.fas', [[[]], [None], []]),
                                      ('BaseConc7.fas', [[[]], [None], []])])
                         )

    def test_set_model_all(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_parNex[0])

        self.aln_obj.partitions.set_model("BaseConc1.fas", ["GTR"],
                                          apply_all=True)

        self.assertEqual(self.aln_obj.partitions.models,
                         OrderedDict([('BaseConc1.fas', [[[]], ['GTR'], []]),
                                      ('BaseConc2.fas', [[[]], ['GTR'], []]),
                                      ('BaseConc3.fas', [[[]], ['GTR'], []]),
                                      ('BaseConc4.fas', [[[]], ['GTR'], []]),
                                      ('BaseConc5.fas', [[[]], ['GTR'], []]),
                                      ('BaseConc6.fas', [[[]], ['GTR'], []]),
                                      ('BaseConc7.fas', [[[]], ['GTR'], []])])
                         )

    def test_set_model_codon(self):

        self.aln_obj.partitions.read_from_file(concatenated_small_parNex[0])

        self.aln_obj.partitions.set_model("BaseConc1.fas", ["GTR", "SYM"],
                                          links=["12", "3"],
                                          apply_all=True)

        self.assertEqual(self.aln_obj.partitions.models,
                         OrderedDict([('BaseConc1.fas',
                                       [[[]], ['GTR', 'SYM'], ['12', '3']]), (
                                      'BaseConc2.fas',
                                      [[[]], ['GTR', 'SYM'], ['12', '3']]), (
                                      'BaseConc3.fas',
                                      [[[]], ['GTR', 'SYM'], ['12', '3']]), (
                                      'BaseConc4.fas',
                                      [[[]], ['GTR', 'SYM'], ['12', '3']]), (
                                      'BaseConc5.fas',
                                      [[[]], ['GTR', 'SYM'], ['12', '3']]), (
                                      'BaseConc6.fas',
                                      [[[]], ['GTR', 'SYM'], ['12', '3']]), (
                                      'BaseConc7.fas',
                                      [[[]], ['GTR', 'SYM'], ['12', '3']])]))


if __name__ == "__main__":
    unittest.main()
