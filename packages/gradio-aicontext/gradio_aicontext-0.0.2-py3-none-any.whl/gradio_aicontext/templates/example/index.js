const {
  SvelteComponent: g,
  add_iframe_resize_listener: v,
  add_render_callback: y,
  append_hydration: b,
  attr: m,
  binding_callbacks: w,
  children: z,
  claim_element: S,
  claim_text: k,
  detach: d,
  element: p,
  init: E,
  insert_hydration: q,
  noop: u,
  safe_not_equal: C,
  set_data: D,
  text: I,
  toggle_class: r
} = window.__gradio__svelte__internal, { onMount: M } = window.__gradio__svelte__internal;
function P(t) {
  let e, l = o(
    /*value*/
    t[0]
  ) + "", a, _;
  return {
    c() {
      e = p("div"), a = I(l), this.h();
    },
    l(i) {
      e = S(i, "DIV", { class: !0 });
      var n = z(e);
      a = k(n, l), n.forEach(d), this.h();
    },
    h() {
      m(e, "class", "svelte-84cxb8"), y(() => (
        /*div_elementresize_handler*/
        t[5].call(e)
      )), r(
        e,
        "table",
        /*type*/
        t[1] === "table"
      ), r(
        e,
        "gallery",
        /*type*/
        t[1] === "gallery"
      ), r(
        e,
        "selected",
        /*selected*/
        t[2]
      );
    },
    m(i, n) {
      q(i, e, n), b(e, a), _ = v(
        e,
        /*div_elementresize_handler*/
        t[5].bind(e)
      ), t[6](e);
    },
    p(i, [n]) {
      n & /*value*/
      1 && l !== (l = o(
        /*value*/
        i[0]
      ) + "") && D(a, l), n & /*type*/
      2 && r(
        e,
        "table",
        /*type*/
        i[1] === "table"
      ), n & /*type*/
      2 && r(
        e,
        "gallery",
        /*type*/
        i[1] === "gallery"
      ), n & /*selected*/
      4 && r(
        e,
        "selected",
        /*selected*/
        i[2]
      );
    },
    i: u,
    o: u,
    d(i) {
      i && d(e), _(), t[6](null);
    }
  };
}
function V(t, e) {
  t.style.setProperty("--local-text-width", `${e && e < 150 ? e : 200}px`), t.style.whiteSpace = "unset";
}
function o(t, e = 60) {
  if (!t) return "";
  const l = String(t);
  return l.length <= e ? l : l.slice(0, e) + "...";
}
function W(t, e, l) {
  let { value: a } = e, { type: _ } = e, { selected: i = !1 } = e, n, c;
  M(() => {
    V(c, n);
  });
  function f() {
    n = this.clientWidth, l(3, n);
  }
  function h(s) {
    w[s ? "unshift" : "push"](() => {
      c = s, l(4, c);
    });
  }
  return t.$$set = (s) => {
    "value" in s && l(0, a = s.value), "type" in s && l(1, _ = s.type), "selected" in s && l(2, i = s.selected);
  }, [a, _, i, n, c, f, h];
}
class j extends g {
  constructor(e) {
    super(), E(this, e, W, P, C, { value: 0, type: 1, selected: 2 });
  }
}
export {
  j as default
};
