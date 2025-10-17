import { defineComponent as _, ref as B, computed as n, normalizeClass as l, watch as b, createElementBlock as T, openBlock as w, createElementVNode as i, unref as u, toDisplayString as N } from "vue";
import { useBindingGetter as L } from "instaui";
import { highlighterTask as D, getTransformers as H, readyCopyButton as x } from "@/shiki_code_logic";
const E = { class: "lang" }, M = ["innerHTML"], z = /* @__PURE__ */ _({
  __name: "Shiki_Code",
  props: {
    code: {},
    language: {},
    theme: {},
    themes: {},
    transformers: {},
    lineNumbers: { type: Boolean },
    useDark: { type: Boolean }
  },
  setup(f) {
    const e = f, {
      transformers: h = [],
      themes: g = {
        light: "vitesse-light",
        dark: "vitesse-dark"
      },
      useDark: d
    } = e, { getValue: p } = L(), m = B(""), s = n(() => e.language || "python"), a = n(
      () => e.theme || (p(d) ? "dark" : "light")
    ), v = n(() => e.lineNumbers ?? !0), k = n(() => l([
      `language-${s.value}`,
      `theme-${a.value}`,
      "shiki-code",
      { "line-numbers": v.value }
    ]));
    b(
      [() => e.code, a],
      async ([t, o]) => {
        if (!t)
          return;
        t = t.trim();
        const r = await D, y = await H(h);
        m.value = await r.codeToHtml(t, {
          themes: g,
          lang: s.value,
          transformers: y,
          defaultColor: a.value,
          colorReplacements: {
            "#ffffff": "#f8f8f2"
          }
        });
      },
      { immediate: !0 }
    );
    const { copyButtonClick: c, btnClasses: C } = x(e);
    return (t, o) => (w(), T("div", {
      class: l(k.value)
    }, [
      i("button", {
        class: l(u(C)),
        title: "Copy Code",
        onClick: o[0] || (o[0] = //@ts-ignore
        (...r) => u(c) && u(c)(...r))
      }, null, 2),
      i("span", E, N(s.value), 1),
      i("div", {
        innerHTML: m.value,
        style: { overflow: "hidden" }
      }, null, 8, M)
    ], 2));
  }
});
export {
  z as default
};
