const M = [
  [/^(<!--)(.+)(-->)$/, !1],
  [/^(\/\*)(.+)(\*\/)$/, !1],
  [/^(\/\/|["'#]|;{1,2}|%{1,2}|--)(.*)$/, !0],
  /**
   * for multi-line comments like this
   */
  [/^(\*)(.+)$/, !0]
];
function N(t, i, e) {
  const s = [];
  for (const n of t) {
    if (e === "v3") {
      const o = n.children.flatMap((a, l) => {
        if (a.type !== "element")
          return a;
        const h = a.children[0];
        if (h.type !== "text")
          return a;
        const f = l === n.children.length - 1;
        if (!k(h.value, f))
          return a;
        const d = h.value.split(/(\s+\/\/)/);
        if (d.length <= 1)
          return a;
        let m = [d[0]];
        for (let g = 1; g < d.length; g += 2)
          m.push(d[g] + (d[g + 1] || ""));
        return m = m.filter(Boolean), m.length <= 1 ? a : m.map((g) => ({
          ...a,
          children: [
            {
              type: "text",
              value: g
            }
          ]
        }));
      });
      o.length !== n.children.length && (n.children = o);
    }
    const r = n.children;
    let c = r.length - 1;
    e === "v1" ? c = 0 : i && (c = r.length - 2);
    for (let o = Math.max(c, 0); o < r.length; o++) {
      const a = r[o];
      if (a.type !== "element")
        continue;
      const l = a.children.at(0);
      if ((l == null ? void 0 : l.type) !== "text")
        continue;
      const h = o === r.length - 1, f = k(l.value, h);
      if (f)
        if (i && !h && o !== 0) {
          const u = x(r[o - 1], "{") && x(r[o + 1], "}");
          s.push({
            info: f,
            line: n,
            token: a,
            isLineCommentOnly: r.length === 3 && a.children.length === 1,
            isJsxStyle: u
          });
        } else
          s.push({
            info: f,
            line: n,
            token: a,
            isLineCommentOnly: r.length === 1 && a.children.length === 1,
            isJsxStyle: !1
          });
    }
  }
  return s;
}
function x(t, i) {
  if (t.type !== "element")
    return !1;
  const e = t.children[0];
  return e.type !== "text" ? !1 : e.value.trim() === i;
}
function k(t, i) {
  let e = t.trimStart();
  const s = t.length - e.length;
  e = e.trimEnd();
  const n = t.length - e.length - s;
  for (const [r, c] of M) {
    if (c && !i)
      continue;
    const o = r.exec(e);
    if (o)
      return [
        " ".repeat(s) + o[1],
        o[2],
        o[3] ? o[3] + " ".repeat(n) : void 0
      ];
  }
}
function b(t) {
  const i = t.match(/(?:\/\/|["'#]|;{1,2}|%{1,2}|--)(\s*)$/);
  return i && i[1].trim().length === 0 ? t.slice(0, i.index) : t;
}
function C(t, i, e, s) {
  return s == null && (s = "v3"), {
    name: t,
    code(n) {
      const r = n.children.filter((l) => l.type === "element"), c = [];
      n.data ?? (n.data = {});
      const o = n.data;
      o._shiki_notation ?? (o._shiki_notation = N(r, ["jsx", "tsx"].includes(this.options.lang), s));
      const a = o._shiki_notation;
      for (const l of a) {
        if (l.info[1].length === 0)
          continue;
        let h = r.indexOf(l.line);
        l.isLineCommentOnly && s !== "v1" && h++;
        let f = !1;
        if (l.info[1] = l.info[1].replace(i, (...d) => e.call(this, d, l.line, l.token, r, h) ? (f = !0, "") : d[0]), !f)
          continue;
        s === "v1" && (l.info[1] = b(l.info[1]));
        const u = l.info[1].trim().length === 0;
        if (u && (l.info[1] = ""), u && l.isLineCommentOnly)
          c.push(l.line);
        else if (u && l.isJsxStyle)
          l.line.children.splice(l.line.children.indexOf(l.token) - 1, 3);
        else if (u)
          l.line.children.splice(l.line.children.indexOf(l.token), 1);
        else {
          const d = l.token.children[0];
          d.type === "text" && (d.value = l.info.join(""));
        }
      }
      for (const l of c) {
        const h = n.children.indexOf(l), f = n.children[h + 1];
        let u = 1;
        (f == null ? void 0 : f.type) === "text" && (f == null ? void 0 : f.value) === `
` && (u = 2), n.children.splice(h, u);
      }
    }
  };
}
function _(t) {
  if (!t)
    return null;
  const i = t.match(/\{([\d,-]+)\}/);
  return i ? i[1].split(",").flatMap((s) => {
    const n = s.split("-").map((r) => Number.parseInt(r, 10));
    return n.length === 1 ? [n[0]] : Array.from({ length: n[1] - n[0] + 1 }, (r, c) => c + n[0]);
  }) : null;
}
const v = Symbol("highlighted-lines");
function R(t = {}) {
  const {
    className: i = "highlighted"
  } = t;
  return {
    name: "@shikijs/transformers:meta-highlight",
    line(e, s) {
      var c;
      if (!((c = this.options.meta) != null && c.__raw))
        return;
      const n = this.meta;
      return n[v] ?? (n[v] = _(this.options.meta.__raw)), (n[v] ?? []).includes(s) && this.addClassToHast(e, i), e;
    }
  };
}
function j(t) {
  return t ? Array.from(t.matchAll(/\/((?:\\.|[^/])+)\//g)).map((e) => e[1].replace(/\\(.)/g, "$1")) : [];
}
function W(t = {}) {
  const {
    className: i = "highlighted-word"
  } = t;
  return {
    name: "@shikijs/transformers:meta-word-highlight",
    preprocess(e, s) {
      var r;
      if (!((r = this.options.meta) != null && r.__raw))
        return;
      const n = j(this.options.meta.__raw);
      s.decorations || (s.decorations = []);
      for (const c of n) {
        const o = O(e, c);
        for (const a of o)
          s.decorations.push({
            start: a,
            end: a + c.length,
            properties: {
              class: i
            }
          });
      }
    }
  };
}
function O(t, i) {
  const e = [];
  let s = 0;
  for (; ; ) {
    const n = t.indexOf(i, s);
    if (n === -1 || n >= t.length || n < s)
      break;
    e.push(n), s = n + i.length;
  }
  return e;
}
function w(t) {
  return t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function y(t = {}, i = "@shikijs/transformers:notation-map") {
  const {
    classMap: e = {},
    classActivePre: s = void 0
  } = t;
  return C(
    i,
    new RegExp(`\\s*\\[!code (${Object.keys(e).map(w).join("|")})(:\\d+)?\\]`),
    function([n, r, c = ":1"], o, a, l, h) {
      const f = Number.parseInt(c.slice(1), 10);
      for (let u = h; u < Math.min(h + f, l.length); u++)
        this.addClassToHast(l[u], e[r]);
      return s && this.addClassToHast(this.pre, s), !0;
    },
    t.matchAlgorithm
  );
}
function B(t = {}) {
  const {
    classLineAdd: i = "diff add",
    classLineRemove: e = "diff remove",
    classActivePre: s = "has-diff"
  } = t;
  return y(
    {
      classMap: {
        "++": i,
        "--": e
      },
      classActivePre: s,
      matchAlgorithm: t.matchAlgorithm
    },
    "@shikijs/transformers:notation-diff"
  );
}
function J(t = {}) {
  const {
    classMap: i = {
      error: ["highlighted", "error"],
      warning: ["highlighted", "warning"]
    },
    classActivePre: e = "has-highlighted"
  } = t;
  return y(
    {
      classMap: i,
      classActivePre: e,
      matchAlgorithm: t.matchAlgorithm
    },
    "@shikijs/transformers:notation-error-level"
  );
}
function F(t = {}) {
  const {
    classActiveLine: i = "focused",
    classActivePre: e = "has-focused"
  } = t;
  return y(
    {
      classMap: {
        focus: i
      },
      classActivePre: e,
      matchAlgorithm: t.matchAlgorithm
    },
    "@shikijs/transformers:notation-focus"
  );
}
function D(t = {}) {
  const {
    classActiveLine: i = "highlighted",
    classActivePre: e = "has-highlighted"
  } = t;
  return y(
    {
      classMap: {
        highlight: i,
        hl: i
      },
      classActivePre: e,
      matchAlgorithm: t.matchAlgorithm
    },
    "@shikijs/transformers:notation-highlight"
  );
}
function T(t, i, e, s) {
  const n = A(t);
  let r = n.indexOf(e);
  for (; r !== -1; )
    H.call(this, t.children, i, r, e.length, s), r = n.indexOf(e, r + 1);
}
function A(t) {
  return t.type === "text" ? t.value : t.type === "element" && t.tagName === "span" ? t.children.map(A).join("") : "";
}
function H(t, i, e, s, n) {
  let r = 0;
  for (let c = 0; c < t.length; c++) {
    const o = t[c];
    if (o.type !== "element" || o.tagName !== "span" || o === i)
      continue;
    const a = o.children[0];
    if (a.type === "text") {
      if (L([r, r + a.value.length - 1], [e, e + s])) {
        const l = Math.max(0, e - r), h = s - Math.max(0, r - e);
        if (h === 0)
          continue;
        const f = S(o, a, l, h);
        this.addClassToHast(f[1], n);
        const u = f.filter(Boolean);
        t.splice(c, 1, ...u), c += u.length - 1;
      }
      r += a.value.length;
    }
  }
}
function L(t, i) {
  return t[0] <= i[1] && t[1] >= i[0];
}
function S(t, i, e, s) {
  const n = i.value, r = (c) => E(t, {
    children: [
      {
        type: "text",
        value: c
      }
    ]
  });
  return [
    e > 0 ? r(n.slice(0, e)) : void 0,
    r(n.slice(e, e + s)),
    e + s < n.length ? r(n.slice(e + s)) : void 0
  ];
}
function E(t, i) {
  return {
    ...t,
    properties: {
      ...t.properties
    },
    ...i
  };
}
function V(t = {}) {
  const {
    classActiveWord: i = "highlighted-word",
    classActivePre: e = void 0
  } = t;
  return C(
    "@shikijs/transformers:notation-highlight-word",
    /\s*\[!code word:((?:\\.|[^:\]])+)(:\d+)?\]/,
    function([s, n, r], c, o, a, l) {
      const h = r ? Number.parseInt(r.slice(1), 10) : a.length;
      n = n.replace(/\\(.)/g, "$1");
      for (let f = l; f < Math.min(l + h, a.length); f++)
        T.call(this, a[f], o, n, i);
      return e && this.addClassToHast(this.pre, e), !0;
    },
    t.matchAlgorithm
  );
}
function q() {
  return {
    name: "@shikijs/transformers:remove-line-break",
    code(t) {
      t.children = t.children.filter((i) => !(i.type === "text" && i.value === `
`));
    }
  };
}
function $(t) {
  return t === "	";
}
function p(t) {
  return t === " " || t === "	";
}
function I(t) {
  const i = [];
  let e = "";
  function s() {
    e.length && i.push(e), e = "";
  }
  return t.forEach((n, r) => {
    $(n) || p(n) && (p(t[r - 1]) || p(t[r + 1])) ? (s(), i.push(n)) : e += n;
  }), s(), i;
}
function P(t, i, e = !0) {
  if (i === "all")
    return t;
  let s = 0, n = 0;
  if (i === "boundary")
    for (let c = 0; c < t.length && p(t[c]); c++)
      s++;
  if (i === "boundary" || i === "trailing")
    for (let c = t.length - 1; c >= 0 && p(t[c]); c--)
      n++;
  const r = t.slice(s, t.length - n);
  return [
    ...t.slice(0, s),
    ...e ? I(r) : [r.join("")],
    ...t.slice(t.length - n)
  ];
}
function z(t = {}) {
  const i = {
    " ": t.classSpace ?? "space",
    "	": t.classTab ?? "tab"
  }, e = t.position ?? "all", s = Object.keys(i);
  return {
    name: "@shikijs/transformers:render-whitespace",
    // We use `root` hook here to ensure it runs after all other transformers
    root(n) {
      const r = n.children[0];
      (r.tagName === "pre" ? r.children[0] : { children: [n] }).children.forEach(
        (o) => {
          if (o.type !== "element" && o.type !== "root")
            return;
          const a = o.children.filter((h) => h.type === "element"), l = a.length - 1;
          o.children = o.children.flatMap((h) => {
            if (h.type !== "element")
              return h;
            const f = a.indexOf(h);
            if (e === "boundary" && f !== 0 && f !== l || e === "trailing" && f !== l)
              return h;
            const u = h.children[0];
            if (u.type !== "text" || !u.value)
              return h;
            const d = P(
              u.value.split(/([ \t])/).filter((m) => m.length),
              e === "boundary" && f === l && l !== 0 ? "trailing" : e,
              e !== "trailing"
            );
            return d.length <= 1 ? h : d.map((m) => {
              const g = {
                ...h,
                properties: { ...h.properties }
              };
              return g.children = [{ type: "text", value: m }], s.includes(m) && (this.addClassToHast(g, i[m]), delete g.properties.style), g;
            });
          });
        }
      );
    }
  };
}
export {
  R as transformerMetaHighlight,
  W as transformerMetaWordHighlight,
  B as transformerNotationDiff,
  J as transformerNotationErrorLevel,
  F as transformerNotationFocus,
  D as transformerNotationHighlight,
  V as transformerNotationWordHighlight,
  q as transformerRemoveLineBreak,
  z as transformerRenderWhitespace
};
