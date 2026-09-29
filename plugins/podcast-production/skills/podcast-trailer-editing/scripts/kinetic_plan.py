#!/usr/bin/env python3
"""Compile a manually authored kinetic plan to reviewable AE batches. Never calls AE.
See references/helper-contracts.md for the manifest and measurement contracts.
"""
import argparse
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
import sys


def fail(message):
    raise ValueError(message)


def number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        fail(f'{name}: expected finite number')
    return value


def positive(value, name):
    if number(value, name) <= 0:
        fail(f'{name}: must be positive')
    return value


def integer(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        fail(f'{name}: expected integer >= {minimum}')
    return value


def string(value, name):
    if not isinstance(value, str) or not value.strip():
        fail(f'{name}: expected nonempty string')
    return value


def vector(value, name, count):
    if not isinstance(value, list) or len(value) != count:
        fail(f'{name}: expected {count} numbers')
    return [number(v, name) for v in value]


def rgb(value, name):
    if any(not 0 <= n <= 1 for n in vector(value, name, 3)):
        fail(f'{name}: colors must be 0..1')
    return value


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    # Exclusive creation, including refusal to follow/overwrite an existing symlink.
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def op(operation, **args):
    return {'operation': operation, 'args': args}


class Plan:
    def __init__(self, data):
        self.data = data
        if data.get('schema_version') != 1:
            fail('schema_version must be 1')
        self.comp = string(data.get('comp'), 'comp')
        fps = data.get('fps', {})
        self.fps = Fraction(integer(fps.get('num'), 'fps.num', 1), integer(fps.get('den'), 'fps.den', 1))
        self.frames = integer(data.get('duration_frames'), 'duration_frames', 1)
        canvas = data.get('canvas', {})
        self.width = integer(canvas.get('width'), 'canvas.width', 1)
        self.height = integer(canvas.get('height'), 'canvas.height', 1)
        self.words = []
        self.shapes = []
        self.names = set()
        lines = data.get('lines')
        if not isinstance(lines, list) or not lines:
            fail('lines must be a nonempty list')
        for line in lines:
            left = number(line.get('left'), 'line.left')
            baseline = number(line.get('baseline'), 'line.baseline')
            gap = number(line.get('gap_px'), 'line.gap_px')
            if gap < 0:
                fail('line.gap_px cannot be negative')
            line_words = line.get('words')
            if not isinstance(line_words, list) or not line_words:
                fail('every line needs words')
            previous = -1
            for w in line_words:
                name = self.unique(w.get('name'))
                text = string(w.get('text'), name + '.text')
                if '\n' in text or '\r' in text:
                    fail(name + ': only single-line point text is supported')
                start, end = self.interval(w.get('onset'), w.get('end', line.get('end')), name)
                if start < previous:
                    fail(name + ': word onsets in a line must be ordered')
                previous = start
                size = positive(w.get('font_size', line.get('font_size')), name + '.font_size')
                font = string(w.get('font', line.get('font')), name + '.font')
                axes = w.get('font_axes', line.get('font_axes', {}))
                if not isinstance(axes, dict):
                    fail(name + ': font_axes must map four-character axis tags to numbers')
                for axis, value in axes.items():
                    if not isinstance(axis, str) or len(axis) != 4 or not axis.isascii():
                        fail(name + ': invalid variable-font axis tag')
                    number(value, name + '.font_axes.' + axis)
                fill = rgb(w.get('fill', line.get('fill', [1, 1, 1])), name + '.fill')
                stroke_width = number(w.get('stroke_width', line.get('stroke_width', 0)), 'stroke_width')
                if stroke_width < 0:
                    fail(name + ': stroke_width must be nonnegative')
                stroke = rgb(w.get('stroke', line.get('stroke', [.03, .03, .03])), 'stroke')
                # This is an explicit conservative design envelope, NOT measured ink bounds.
                envelope = vector(w.get('vertical_envelope', line.get('vertical_envelope', [-size, size * .3])), 'vertical_envelope', 2)
                if envelope[0] >= envelope[1]:
                    fail(name + ': vertical_envelope must be [top,bottom] relative to baseline')
                if baseline + envelope[0] < 0 or baseline + envelope[1] > self.height:
                    fail(name + ': vertical envelope is off canvas')
                x = w.get('x')
                if x is not None:
                    number(x, name + '.x')
                if left < 0 or left >= self.width or (x is not None and not 0 <= x < self.width):
                    fail(name + ': left/x is off canvas')
                self.words.append(dict(name=name, text=text, start=start, end=end, font=font,
                                       font_size=size, font_axes=axes, fill=fill, stroke_width=stroke_width, stroke=stroke,
                                       left=left, baseline=baseline, x=x, gap=gap, line_id=id(line), envelope=envelope))
        for s in data.get('shapes', []):
            name = self.unique(s.get('name'))
            if s.get('kind') not in ('plate', 'underline'):
                fail(name + ': kind must be plate or underline')
            position = vector(s.get('position'), name + '.position', 2)
            size = vector(s.get('size'), name + '.size', 2)
            if min(size) <= 0:
                fail(name + ': shape size must be positive')
            self.rect(position[0], position[1], *size, name)
            start, end = self.interval(s.get('onset'), s.get('end'), name)
            fill = rgb(s.get('fill', [1, 87 / 255, 10 / 255]), name + '.fill')
            keys = []
            for k in s.get('width_keys', []):
                frame = self.frame(k.get('time'))
                width = number(k.get('width'), name + '.width_keys.width')
                if not 0 <= width <= size[0] or not start <= frame < end:
                    fail(name + ': width key exceeds size or visible interval')
                if keys and frame <= keys[-1]['frame']:
                    fail(name + ': width keyframes collapse or are unordered after rounding')
                easing = k.get('easing', 'linear')
                if easing not in ('linear', 'hold', 'ease', 'easeIn', 'easeOut'):
                    fail(name + ': unsupported easing')
                keys.append(dict(frame=frame, width=width, easing=easing))
            if keys and keys[0]['frame'] != start:
                fail(name + ': first width key must equal in point; prevents backward extrapolation')
            self.shapes.append(dict(name=name, position=position, size=size, start=start, end=end, fill=fill, keys=keys))

    def unique(self, value):
        name = string(value, 'name')
        if name in self.names:
            fail('duplicate layer name: ' + name)
        self.names.add(name)
        return name

    def frame(self, value):
        if isinstance(value, dict):
            return integer(value.get('frame'), 'time.frame')
        if isinstance(value, bool) or value is None:
            fail('time: expected decimal seconds or {"frame": integer}')
        try:
            seconds = Fraction(str(value))
        except (ValueError, ZeroDivisionError):
            fail('invalid seconds: ' + repr(value))
        if seconds < 0:
            fail('negative time')
        # Exact rational nearest-frame, ties toward +infinity. Avoid Python bankers rounding.
        value = seconds * self.fps + Fraction(1, 2)
        return value.numerator // value.denominator

    def interval(self, start, end, name):
        a, b = self.frame(start), self.frame(end)
        if not 0 <= a < b <= self.frames:
            fail(name + ': invalid/collapsed interval after frame rounding')
        return a, b

    def seconds(self, frame):
        return float(Fraction(frame, 1) / self.fps)

    def rect(self, left, top, width, height, name):
        if min(left, top) < 0 or left + width > self.width or top + height > self.height:
            fail(name + ': rectangle is off canvas')

    def signature(self, w):
        data = {k: w[k] for k in ('text', 'font', 'font_size', 'font_axes', 'fill', 'stroke_width', 'stroke')}
        return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    def plan_signature(self):
        return hashlib.sha256(json.dumps(self.data, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()

    def document(self, phase, ops, chunk_size, extra=None):
        result = {'schema_version': 1, 'phase': phase, 'comp': self.comp, 'plan_signature': self.plan_signature(),
                  'fps': {'num': self.fps.numerator, 'den': self.fps.denominator},
                  'duration_frames': self.frames,
                  'batches': [op('batch.run', ops=ops[i:i + chunk_size], stopOnError=True)
                              for i in range(0, len(ops), chunk_size)]}
        if extra:
            result.update(extra)
        return result

    def prepare(self, chunk_size):
        ops = [op('comp.create', name=self.comp, width=self.width, height=self.height,
                  fps=float(self.fps), duration=self.seconds(self.frames))]
        for w in self.words:
            common = dict(comp=self.comp, layer=w['name'])
            ops += [op('layer.create_text', comp=self.comp, name=w['name'], text=w['text']),
                    op('text.set_style', **common, font=w['font'], fontSize=w['font_size'],
                       fillColor=w['fill'], applyFill=True, strokeColor=w['stroke'],
                       strokeWidth=w['stroke_width'], applyStroke=bool(w['stroke_width']),
                       strokeOverFill=False, tracking=0, justification='left')]
            if w['font_axes']:
                ops.append(op('text.set_variable_font', **common, axes=w['font_axes']))
            ops += [op('transform.set', **common, anchorPoint=[0, 0], position=[0, 0]),
                    op('text.measure', **common)]
        return self.document('prepare', ops, chunk_size,
                             {'warning': 'Execute only into a new unique composition. Read every batch result before continuing. This is not an idempotent apply script.'})

    def normalize(self, prepared, responses):
        if prepared.get('comp') != self.comp or prepared.get('phase') != 'prepare':
            fail('prepared document does not match plan')
        if prepared.get('plan_signature') != self.plan_signature():
            fail('plan changed after prepare; execute a matching prepare and capture new measurements')
        if len(responses) != len(prepared['batches']):
            fail('one structured AE response per prepared batch is required')
        words = {w['name']: w for w in self.words}
        measurements = {}
        for batch, response in zip(prepared['batches'], responses):
            # Accept the raw native payload or the actual ae_do structuredContent envelope.
            if 'result' in response:
                if not response.get('ok') or response.get('warnings') or response.get('error'):
                    fail('failed/warning AE response envelope; inspect native state')
                response = response['result']
            if not response.get('ok') or response.get('failed', 0):
                fail('failed/uncertain AE response; inspect native state before continuing')
            results = response.get('results', [])
            ops = batch['args']['ops']
            if len(results) != len(ops):
                fail('response length does not match operations')
            for operation, result in zip(ops, results):
                if not isinstance(result, dict) or not result.get('ok') or result.get('warnings') or result.get('error'):
                    fail('operation failed, skipped or warned: ' + operation['operation'] + '; inspect native state')
                if operation['operation'] != 'text.measure':
                    continue
                name = operation['args']['layer']
                w = words[name]
                baseline = result.get('baselineLocs')
                if not result.get('ok') or result.get('text') != w['text']:
                    fail(name + ': measurement text mismatch')
                if result.get('boxText') or not isinstance(baseline, list) or len(baseline) != 4:
                    fail(name + ': expected one composed line with four baselineLocs')
                advance = positive(baseline[2] - baseline[0], name + '.advance')
                measurements[name] = dict(signature=self.signature(w), advance=advance,
                                          fontFamily=result.get('fontFamily'), fontStyle=result.get('fontStyle'))
        if set(measurements) != set(words):
            fail('missing word measurement')
        return {'schema_version': 1, 'measurements': measurements,
                'source': 'Native text.measure baselineLocs; review fontFamily/fontStyle against requested fonts.'}

    def compile(self, metrics, chunk_size):
        measured = metrics.get('measurements', {})
        if metrics.get('schema_version') != 1:
            fail('measurements schema_version must be 1')
        ops, layout = [], []
        cursor, last_line = 0, None
        for w in self.words:
            m = measured.get(w['name'])
            if not m or m.get('signature') != self.signature(w):
                fail(w['name'] + ': missing/stale measurement; remeasure after any text/font/style change')
            advance = positive(m.get('advance'), w['name'] + '.advance')
            if w['line_id'] != last_line:
                cursor, last_line = w['left'], w['line_id']
            x = w['x'] if w['x'] is not None else cursor
            self.rect(x, w['baseline'] + w['envelope'][0], advance,
                      w['envelope'][1] - w['envelope'][0], w['name'])
            cursor = x + advance + w['gap']
            common = dict(comp=self.comp, layer=w['name'])
            ops += [op('transform.set', **common, anchorPoint=[0, 0], position=[x, w['baseline']]),
                    op('layer.set_props', **common, props={'inPoint': self.seconds(w['start']), 'outPoint': self.seconds(w['end'])})]
            layout.append(dict(name=w['name'], x=x, baseline=w['baseline'], advance=advance,
                               onset_frame=w['start'], end_frame=w['end']))
        for index, s in enumerate(self.shapes):
            common = dict(comp=self.comp, layer=s['name'])
            ops += [op('layer.create_shape', comp=self.comp, name=s['name']),
                    op('shape.add_group', **common, name='Editable rectangle'),
                    op('shape.add_rect', **common, groupIndex=1, size=s['size'],
                       position=[s['size'][0] / 2, s['size'][1] / 2], roundness=0),
                    op('shape.add_fill', **common, groupIndex=1, color=s['fill'] + [1]),
                    op('transform.set', **common, anchorPoint=[0, 0], position=s['position']),
                    op('layer.set_props', **common, props={'inPoint': self.seconds(s['start']), 'outPoint': self.seconds(s['end'])}),
                    op('layer.move', **common, toIndex=len(self.words) + index + 1)]
            if s['keys']:
                ops.append(op('keyframe.set_batch', **common, property=['Transform', 'Scale'],
                              times=[self.seconds(k['frame']) for k in s['keys']],
                              values=[[k['width'] / s['size'][0] * 100, 100] for k in s['keys']]))
                for i, k in enumerate(s['keys'], 1):
                    ops.append(op('keyframe.set_easing', **common, property=['Transform', 'Scale'], keyIndex=i, preset=k['easing']))
        ops.append(op('comp.info', comp=self.comp))
        return self.document('layout', ops, chunk_size, {'layout': layout,
                    'warning': 'Run only after the matching prepare batches succeed. Shapes are explicit geometry, not dynamic reflow; visual rendering remains required.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['prepare', 'normalize', 'compile'])
    parser.add_argument('plan')
    parser.add_argument('--out', required=True, help='New JSON file; existing paths are refused')
    parser.add_argument('--measurements')
    parser.add_argument('--prepared')
    parser.add_argument('--responses', help='JSON array of structuredContent responses, one per prepare batch')
    parser.add_argument('--chunk-size', type=int, default=64)
    args = parser.parse_args()
    if not 1 <= args.chunk_size <= 256:
        fail('chunk-size must be 1..256')
    plan = Plan(read(args.plan))
    if args.phase == 'prepare':
        result = plan.prepare(args.chunk_size)
    elif args.phase == 'normalize':
        if not args.prepared or not args.responses:
            fail('normalize requires --prepared and --responses')
        result = plan.normalize(read(args.prepared), read(args.responses))
    else:
        if not args.measurements:
            fail('compile requires --measurements')
        result = plan.compile(read(args.measurements), args.chunk_size)
    write_new(args.out, result)
    print(json.dumps({'output': str(Path(args.out).resolve()), 'phase': args.phase,
                      'word_count': len(plan.words), 'shape_count': len(plan.shapes),
                      'batch_count': len(result.get('batches', []))}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)
