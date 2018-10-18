# Copyright 2017 The Forseti Security Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests the LocationRulesEngine."""

import copy
import itertools
import json
import mock
import tempfile
import unittest
import yaml

from tests.unittest_utils import ForsetiTestCase
from google.cloud.forseti.common.util import file_loader
from google.cloud.forseti.scanner.audit.errors import InvalidRulesSchemaError
from google.cloud.forseti.scanner.audit import location_rules_engine
from google.cloud.forseti.scanner.audit import rules as scanner_rules
from tests.unittest_utils import get_datafile_path
from tests.scanner.test_data import fake_location_scanner_data as data


rule_tmpl = """
rules:
  - name: Location test rule
    mode: {mode}
    resource:
      - type: 'organization'
        resource_ids: ['234']
    applies_to: ['{type}']
    locations: {locations}
"""



def get_rules_engine_with_rule(rule):
    with tempfile.NamedTemporaryFile(suffix='.yaml') as f:
        f.write(rule)
        f.flush()
        rules_engine = location_rules_engine.LocationRulesEngine(
            rules_file_path=f.name)
        rules_engine.build_rule_book()
    return rules_engine


class LocationRulesEngineTest(ForsetiTestCase):
    """Tests for the LocationRulesEngine."""

    def setUp(self):
        location_rules_engine.LOGGER = mock.MagicMock()

    def test_build_rule_book_from_local_yaml_file(self):
        rule = rule_tmpl.format(
            mode='whitelist',
            type='bucket',
            locations=['eu*'],
        )
        rules_engine = get_rules_engine_with_rule(rule)
        self.assertEqual(1, len(rules_engine.rule_book.resource_to_rules))

    def test_find_violations_bucket_whitelist_no_violations(self):
        rule = rule_tmpl.format(
            mode='whitelist',
            type='bucket',
            locations=['eu*'],
        )
        rules_engine = get_rules_engine_with_rule(rule)
        got_violations = list(rules_engine.find_violations(data.BUCKET))
        self.assertEqual(got_violations, [])

    def test_find_violations_bucket_whitelist_has_violations(self):
        rule = rule_tmpl.format(
            mode='whitelist',
            type='bucket',
            locations=['us*'],
        )
        rules_engine = get_rules_engine_with_rule(rule)
        got_violations = list(rules_engine.find_violations(data.BUCKET))
        self.assertEqual(got_violations, data.build_violations(data.BUCKET))

    def test_find_violations_bucket_blacklist_no_violations(self):
        rule = rule_tmpl.format(
            mode='blacklist',
            type='bucket',
            locations=['us*'],
        )
        rules_engine = get_rules_engine_with_rule(rule)
        got_violations = list(rules_engine.find_violations(data.BUCKET))
        self.assertEqual(got_violations, [])

    def test_find_violations_bucket_blacklist_has_violations(self):
        rule = rule_tmpl.format(
            mode='blacklist',
            type='bucket',
            locations=['eu*'],
        )
        rules_engine = get_rules_engine_with_rule(rule)
        got_violations = list(rules_engine.find_violations(data.BUCKET))
        self.assertEqual(got_violations, data.build_violations(data.BUCKET))

    def test_find_violations_exact(self):
        rule = rule_tmpl.format(
            mode='blacklist',
            type='bucket',
            locations=['europe-west1'],
        )
        rules_engine = get_rules_engine_with_rule(rule)
        got_violations = list(rules_engine.find_violations(data.BUCKET))
        self.assertEqual(got_violations, data.build_violations(data.BUCKET))

    def test_find_violations_multiple_locations(self):
        rule = rule_tmpl.format(
            mode='blacklist',
            type='bucket',
            locations=['us*', 'eu*'],
        )
        rules_engine = get_rules_engine_with_rule(rule)
        got_violations = list(rules_engine.find_violations(data.BUCKET))
        self.assertEqual(got_violations, data.build_violations(data.BUCKET))


if __name__ == '__main__':
    unittest.main()
