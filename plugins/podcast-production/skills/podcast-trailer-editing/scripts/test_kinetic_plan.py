#!/usr/bin/env python3
"""Local-only regression checks for compiler invariants. No AE execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from kinetic_plan import Plan, write_new

ROOT = Path(__file__).resolve().parents[1]


class CompilerChecks(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'assets/examples/pilot-plan.json').read_text())
        self.metrics = json.loads((ROOT / 'assets/examples/pilot-measurements.json').read_text())

    def test_exact_frame_math(self):
        p = Plan(self.data)
        self.assertEqual(p.frame('4.04'), 242)
        self.assertEqual(p.frame('9.3760333333'), 562)
        self.assertEqual(p.frame('10.01'), 600)
        self.assertEqual(p.frame('1001/120000'), 1)
        self.assertEqual(p.frame({'frame': 247}), 247)
        self.assertEqual(p.seconds(600), 10.01)

    def test_pilot_layout_and_underline(self):
        p = Plan(self.data)
        result = p.compile(self.metrics, 64)
        layout = {w['name']: w for w in result['layout']}
        self.assertEqual(len(layout), 26)
        self.assertAlmostEqual(layout['01 • 03 • model']['x'], 721.264000854492)
        self.assertAlmostEqual(layout['01 • 10 • BENCH']['x'], 802.479992675781)
        self.assertAlmostEqual(layout['03 • 23 • role,']['x'], 1103.1999992370604)
        self.assertEqual(layout['04 • 26 • Definitely.']['end_frame'], 600)
        ops = [o for b in result['batches'] for o in b['args']['ops']]
        scale = next(o for o in ops if o['operation'] == 'keyframe.set_batch')
        self.assertEqual(scale['args']['values'], [[0.0, 100], [100.0, 100]])
        self.assertAlmostEqual(scale['args']['times'][1] - scale['args']['times'][0], 5 * 1001 / 60000)
        self.assertEqual(sum(o['operation'] == 'layer.create_shape' for o in ops), 4)

    def test_invalid_plans(self):
        for mutation in ('duplicate', 'collapsed', 'negative', 'offcanvas_text', 'offcanvas_shape', 'key_before_in', 'colliding_keys'):
            data = copy.deepcopy(self.data)
            word = data['lines'][0]['words'][0]
            if mutation == 'duplicate':
                word['name'] = data['lines'][0]['words'][1]['name']
            elif mutation == 'collapsed':
                word['end'] = '0.001'
            elif mutation == 'negative':
                word['onset'] = '-1'
            elif mutation == 'offcanvas_text':
                data['lines'][0]['baseline'] = 10
            elif mutation == 'offcanvas_shape':
                data['shapes'][0]['position'][0] = 3800
            elif mutation == 'key_before_in':
                data['shapes'][2]['width_keys'][0]['time'] = {'frame': 241}
            elif mutation == 'colliding_keys':
                data['shapes'][2]['width_keys'][1]['time'] = {'frame': 242}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                Plan(data)

    def test_missing_stale_and_oversized_widths(self):
        p = Plan(self.data)
        name = p.words[0]['name']
        for mutation in ('missing', 'stale', 'offcanvas', 'nan'):
            metrics = copy.deepcopy(self.metrics)
            if mutation == 'missing':
                del metrics['measurements'][name]
            elif mutation == 'stale':
                metrics['measurements'][name]['signature'] = 'old-font'
            elif mutation == 'offcanvas':
                metrics['measurements'][name]['advance'] = 5000
            else:
                metrics['measurements'][name]['advance'] = float('nan')
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                p.compile(metrics, 64)

    def test_normalizer_response_mapping(self):
        p = Plan(self.data)
        prepared = p.prepare(64)
        responses = []
        words = {w['name']: w for w in p.words}
        for batch in prepared['batches']:
            results = []
            for o in batch['args']['ops']:
                result = {'ok': True}
                if o['operation'] == 'text.measure':
                    name = o['args']['layer']
                    result.update(text=words[name]['text'], boxText=False,
                                  baselineLocs=[0, 0, self.metrics['measurements'][name]['advance'], 0])
                results.append(result)
            responses.append({'ok': True, 'failed': 0, 'results': results})
        normalized = p.normalize(prepared, responses)
        self.assertEqual(len(p.compile(normalized, 64)['layout']), 26)
        wrapped = [{'ok': True, 'result': r, 'context': {}} for r in responses]
        self.assertEqual(len(p.normalize(prepared, wrapped)['measurements']), 26)
        changed = copy.deepcopy(self.data)
        changed['lines'][0]['font_size'] = 80
        with self.assertRaisesRegex(ValueError, 'plan changed'):
            Plan(changed).normalize(prepared, responses)
        warning_responses = copy.deepcopy(responses)
        warning_responses[0]['results'][2]['warnings'] = ['font assignment failed']
        with self.assertRaisesRegex(ValueError, 'warned'):
            p.normalize(prepared, warning_responses)
        responses[0]['ok'] = False
        with self.assertRaises(ValueError):
            p.normalize(prepared, responses)

    def test_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'existing.json'
            write_new(path, {'preserve': True})
            with self.assertRaises(FileExistsError):
                write_new(path, {'preserve': False})
            self.assertEqual(json.loads(path.read_text()), {'preserve': True})


if __name__ == '__main__':
    unittest.main()
