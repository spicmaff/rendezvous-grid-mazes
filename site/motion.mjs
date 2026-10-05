// MIT. Presentation-only timing; the exact discrete model never uses this clock.
export const smooth = t => t * t * (3 - 2 * t);
export const mix = (a, b, t) => a + (b - a) * t;

export function animate({duration = 300, update, complete = () => {}, easing = smooth}, clock = globalThis) {
  let frame, stopped = false;
  const now = () => clock.performance.now();
  const finish = () => {
    if (stopped) return;
    stopped = true;
    if (frame !== undefined) clock.cancelAnimationFrame(frame);
    update(1);
    complete();
  };
  const cancel = () => {
    if (stopped) return;
    stopped = true;
    if (frame !== undefined) clock.cancelAnimationFrame(frame);
  };
  if (duration <= 0 || !clock.requestAnimationFrame) {
    finish();
    return {finish, cancel};
  }
  const start = now();
  function tick(time) {
    if (stopped) return;
    const t = Math.min(1, Math.max(0, (time - start) / duration));
    if (t === 1) finish();
    else { update(easing(t)); frame = clock.requestAnimationFrame(tick); }
  }
  update(0);
  frame = clock.requestAnimationFrame(tick);
  return {finish, cancel};
}
