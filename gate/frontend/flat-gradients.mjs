// HeroUI's stylesheet ships gradients (skeleton shimmer, color slider, masks) for
// components this app does not render. The workspace uses flat colors only.
export function flattenGradients(css) {
  const start = /(?:-webkit-)?(?:repeating-)?(?:linear|radial|conic)-gradient\(/g;
  let out = '', last = 0, m;
  while ((m = start.exec(css))) {
    let depth = 1, i = m.index + m[0].length;
    while (depth && i < css.length) { if (css[i] === '(') depth++; else if (css[i] === ')') depth--; i++; }
    out += css.slice(last, m.index) + 'none';
    last = start.lastIndex = i;
  }
  return out + css.slice(last);
}

export const flatGradients = () => ({
  name: 'flat-gradients',
  generateBundle(_, bundle) {
    for (const file of Object.values(bundle))
      if (file.type === 'asset' && file.fileName.endsWith('.css')) file.source = flattenGradients(String(file.source));
  },
});
