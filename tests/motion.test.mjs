import test from 'node:test';
import assert from 'node:assert/strict';
import {animate, smooth, mix} from '../site/motion.mjs';

function clock() {
  let time = 0, next = 0;
  const pending = new Map();
  return {
    performance: {now: () => time},
    requestAnimationFrame: cb => { pending.set(++next, cb); return next; },
    cancelAnimationFrame: id => pending.delete(id),
    at(t) { time = t; const callbacks = [...pending.values()]; pending.clear(); callbacks.forEach(cb => cb(t)); },
    get pending() { return pending.size; }
  };
}

test('One presentation frame moves both agents synchronously and reaches exact endpoints', () => {
  const c = clock(), positions = [], progress = []; let completed = 0;
  animate({duration: 400, update: t => { progress.push(t); positions.push([mix(0, 72, t), mix(300, 228, t)]); }, complete: () => completed++}, c);
  c.at(100); c.at(200); c.at(399); c.at(400); c.at(900);
  assert.deepEqual(positions[2], [36, 264]);
  assert.deepEqual(positions.at(-1), [72, 228]);
  assert(progress.every((t, i) => i === 0 || t >= progress[i - 1]));
  assert.equal(completed, 1); assert.equal(c.pending, 0);
});

test('Interrupted motion cannot repaint after reset; settling is exact and idempotent', () => {
  const c = clock(), values = []; let completed = 0;
  const old = animate({duration: 400, update: t => values.push(t), complete: () => completed++}, c);
  c.at(100); old.cancel(); const count = values.length; c.at(500);
  assert.equal(values.length, count); assert.equal(completed, 0);
  const replacement = animate({duration: 400, update: t => values.push(t), complete: () => completed++}, c);
  replacement.finish(); replacement.finish(); c.at(1000);
  assert.equal(values.at(-1), 1); assert.equal(completed, 1); assert.equal(c.pending, 0);
});

test('Reduced motion and environments without RAF draw only the exact final state', () => {
  for (const c of [clock(), {}]) {
    const values = []; let completed = 0;
    animate({duration: 0, update: t => values.push(t), complete: () => completed++}, c);
    assert.deepEqual(values, [1]); assert.equal(completed, 1);
  }
  assert.equal(smooth(0), 0); assert.equal(smooth(1), 1);
});
