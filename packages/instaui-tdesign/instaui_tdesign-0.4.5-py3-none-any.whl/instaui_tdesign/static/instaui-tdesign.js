import { defineComponent as Z, useAttrs as lt, useSlots as ct, createBlock as Y, openBlock as J, mergeProps as pt, unref as b, createSlots as gt, renderList as X, withCtx as j, renderSlot as dt, normalizeProps as ht, guardReactiveProps as _t, computed as w, ref as Jt, createElementVNode as St, createVNode as be, toDisplayString as rt, createTextVNode as Ct, resolveDynamicComponent as ve } from "vue";
import * as G from "tdesign-vue-next";
import { DateRangePickerPanel as me, useConfig as Ae } from "tdesign-vue-next";
function Te(t) {
  const { container: e = ".insta-main" } = t;
  return e;
}
const we = /* @__PURE__ */ Z({
  inheritAttrs: !1,
  __name: "Affix",
  setup(t) {
    const e = lt(), r = ct(), n = Te(e);
    return (a, i) => (J(), Y(G.Affix, pt(b(e), { container: b(n) }), gt({ _: 2 }, [
      X(b(r), (o, u) => ({
        name: u,
        fn: j((s) => [
          dt(a.$slots, u, ht(_t(s)))
        ])
      }))
    ]), 1040, ["container"]));
  }
});
function Oe(t) {
  const e = [], r = w(() => t.data ?? []);
  return {
    tableData: w(() => {
      const i = r.value;
      return e.reduce((o, u) => u(o), i);
    }),
    orgData: r,
    registerRowsHandler: (i) => {
      e.push(i);
    }
  };
}
function $e(t) {
  const { tableData: e, attrs: r } = t, n = [], a = w(() => {
    let u = !r.columns && e.value.length > 0 ? Pe(e.value) : r.columns ?? [];
    u = u.map(Se);
    for (const s of n)
      u = s(u);
    return u;
  });
  function i(o) {
    n.push(o);
  }
  return [a, i];
}
function Pe(t) {
  const e = t[0];
  return Object.keys(e).map((n) => ({
    colKey: n,
    title: n,
    sorter: !0
  }));
}
function Se(t) {
  const e = t.name ?? t.colKey, r = `header-cell-${e}`, n = `body-cell-${e}`, a = t.label ?? t.colKey;
  return {
    ...t,
    name: e,
    label: a,
    title: r,
    cell: n
  };
}
function Ce(t) {
  const { tableData: e, attrs: r } = t;
  return w(() => {
    const { pagination: n } = r;
    let a;
    if (typeof n == "boolean") {
      if (!n)
        return;
      a = {
        defaultPageSize: 10
      };
    }
    return typeof n == "number" && n > 0 && (a = {
      defaultPageSize: n
    }), typeof n == "object" && n !== null && (a = n), {
      defaultCurrent: 1,
      total: e.value.length,
      ...a
    };
  });
}
var Qt = typeof global == "object" && global && global.Object === Object && global, xe = typeof self == "object" && self && self.Object === Object && self, O = Qt || xe || Function("return this")(), C = O.Symbol, kt = Object.prototype, Ee = kt.hasOwnProperty, Re = kt.toString, N = C ? C.toStringTag : void 0;
function De(t) {
  var e = Ee.call(t, N), r = t[N];
  try {
    t[N] = void 0;
    var n = !0;
  } catch {
  }
  var a = Re.call(t);
  return n && (e ? t[N] = r : delete t[N]), a;
}
var je = Object.prototype, Fe = je.toString;
function Ie(t) {
  return Fe.call(t);
}
var Me = "[object Null]", Le = "[object Undefined]", xt = C ? C.toStringTag : void 0;
function M(t) {
  return t == null ? t === void 0 ? Le : Me : xt && xt in Object(t) ? De(t) : Ie(t);
}
function I(t) {
  return t != null && typeof t == "object";
}
var ze = "[object Symbol]";
function H(t) {
  return typeof t == "symbol" || I(t) && M(t) == ze;
}
function V(t, e) {
  for (var r = -1, n = t == null ? 0 : t.length, a = Array(n); ++r < n; )
    a[r] = e(t[r], r, t);
  return a;
}
var A = Array.isArray, Et = C ? C.prototype : void 0, Rt = Et ? Et.toString : void 0;
function te(t) {
  if (typeof t == "string")
    return t;
  if (A(t))
    return V(t, te) + "";
  if (H(t))
    return Rt ? Rt.call(t) : "";
  var e = t + "";
  return e == "0" && 1 / t == -1 / 0 ? "-0" : e;
}
function yt(t) {
  var e = typeof t;
  return t != null && (e == "object" || e == "function");
}
function ee(t) {
  return t;
}
var Ne = "[object AsyncFunction]", Be = "[object Function]", Ge = "[object GeneratorFunction]", He = "[object Proxy]";
function re(t) {
  if (!yt(t))
    return !1;
  var e = M(t);
  return e == Be || e == Ge || e == Ne || e == He;
}
var nt = O["__core-js_shared__"], Dt = function() {
  var t = /[^.]+$/.exec(nt && nt.keys && nt.keys.IE_PROTO || "");
  return t ? "Symbol(src)_1." + t : "";
}();
function Ue(t) {
  return !!Dt && Dt in t;
}
var Ke = Function.prototype, We = Ke.toString;
function R(t) {
  if (t != null) {
    try {
      return We.call(t);
    } catch {
    }
    try {
      return t + "";
    } catch {
    }
  }
  return "";
}
var qe = /[\\^$.*+?()[\]{}|]/g, Ve = /^\[object .+?Constructor\]$/, Xe = Function.prototype, Ze = Object.prototype, Ye = Xe.toString, Je = Ze.hasOwnProperty, Qe = RegExp(
  "^" + Ye.call(Je).replace(qe, "\\$&").replace(/hasOwnProperty|(function).*?(?=\\\()| for .+?(?=\\\])/g, "$1.*?") + "$"
);
function ke(t) {
  if (!yt(t) || Ue(t))
    return !1;
  var e = re(t) ? Qe : Ve;
  return e.test(R(t));
}
function tr(t, e) {
  return t?.[e];
}
function L(t, e) {
  var r = tr(t, e);
  return ke(r) ? r : void 0;
}
var ot = L(O, "WeakMap");
function er() {
}
function rr(t, e, r, n) {
  for (var a = t.length, i = r + -1; ++i < a; )
    if (e(t[i], i, t))
      return i;
  return -1;
}
function nr(t) {
  return t !== t;
}
function ir(t, e, r) {
  for (var n = r - 1, a = t.length; ++n < a; )
    if (t[n] === e)
      return n;
  return -1;
}
function ar(t, e, r) {
  return e === e ? ir(t, e, r) : rr(t, nr, r);
}
function or(t, e) {
  var r = t == null ? 0 : t.length;
  return !!r && ar(t, e, 0) > -1;
}
var sr = 9007199254740991, ur = /^(?:0|[1-9]\d*)$/;
function ne(t, e) {
  var r = typeof t;
  return e = e ?? sr, !!e && (r == "number" || r != "symbol" && ur.test(t)) && t > -1 && t % 1 == 0 && t < e;
}
function ie(t, e) {
  return t === e || t !== t && e !== e;
}
var fr = 9007199254740991;
function bt(t) {
  return typeof t == "number" && t > -1 && t % 1 == 0 && t <= fr;
}
function vt(t) {
  return t != null && bt(t.length) && !re(t);
}
var lr = Object.prototype;
function cr(t) {
  var e = t && t.constructor, r = typeof e == "function" && e.prototype || lr;
  return t === r;
}
function pr(t, e) {
  for (var r = -1, n = Array(t); ++r < t; )
    n[r] = e(r);
  return n;
}
var gr = "[object Arguments]";
function jt(t) {
  return I(t) && M(t) == gr;
}
var ae = Object.prototype, dr = ae.hasOwnProperty, hr = ae.propertyIsEnumerable, oe = jt(/* @__PURE__ */ function() {
  return arguments;
}()) ? jt : function(t) {
  return I(t) && dr.call(t, "callee") && !hr.call(t, "callee");
};
function _r() {
  return !1;
}
var se = typeof exports == "object" && exports && !exports.nodeType && exports, Ft = se && typeof module == "object" && module && !module.nodeType && module, yr = Ft && Ft.exports === se, It = yr ? O.Buffer : void 0, br = It ? It.isBuffer : void 0, st = br || _r, vr = "[object Arguments]", mr = "[object Array]", Ar = "[object Boolean]", Tr = "[object Date]", wr = "[object Error]", Or = "[object Function]", $r = "[object Map]", Pr = "[object Number]", Sr = "[object Object]", Cr = "[object RegExp]", xr = "[object Set]", Er = "[object String]", Rr = "[object WeakMap]", Dr = "[object ArrayBuffer]", jr = "[object DataView]", Fr = "[object Float32Array]", Ir = "[object Float64Array]", Mr = "[object Int8Array]", Lr = "[object Int16Array]", zr = "[object Int32Array]", Nr = "[object Uint8Array]", Br = "[object Uint8ClampedArray]", Gr = "[object Uint16Array]", Hr = "[object Uint32Array]", h = {};
h[Fr] = h[Ir] = h[Mr] = h[Lr] = h[zr] = h[Nr] = h[Br] = h[Gr] = h[Hr] = !0;
h[vr] = h[mr] = h[Dr] = h[Ar] = h[jr] = h[Tr] = h[wr] = h[Or] = h[$r] = h[Pr] = h[Sr] = h[Cr] = h[xr] = h[Er] = h[Rr] = !1;
function Ur(t) {
  return I(t) && bt(t.length) && !!h[M(t)];
}
function ue(t) {
  return function(e) {
    return t(e);
  };
}
var fe = typeof exports == "object" && exports && !exports.nodeType && exports, B = fe && typeof module == "object" && module && !module.nodeType && module, Kr = B && B.exports === fe, it = Kr && Qt.process, Mt = function() {
  try {
    var t = B && B.require && B.require("util").types;
    return t || it && it.binding && it.binding("util");
  } catch {
  }
}(), Lt = Mt && Mt.isTypedArray, le = Lt ? ue(Lt) : Ur, Wr = Object.prototype, qr = Wr.hasOwnProperty;
function Vr(t, e) {
  var r = A(t), n = !r && oe(t), a = !r && !n && st(t), i = !r && !n && !a && le(t), o = r || n || a || i, u = o ? pr(t.length, String) : [], s = u.length;
  for (var f in t)
    qr.call(t, f) && !(o && // Safari 9 has enumerable `arguments.length` in strict mode.
    (f == "length" || // Node.js 0.10 has enumerable non-index properties on buffers.
    a && (f == "offset" || f == "parent") || // PhantomJS 2 has enumerable non-index properties on typed arrays.
    i && (f == "buffer" || f == "byteLength" || f == "byteOffset") || // Skip index properties.
    ne(f, s))) && u.push(f);
  return u;
}
function Xr(t, e) {
  return function(r) {
    return t(e(r));
  };
}
var Zr = Xr(Object.keys, Object), Yr = Object.prototype, Jr = Yr.hasOwnProperty;
function Qr(t) {
  if (!cr(t))
    return Zr(t);
  var e = [];
  for (var r in Object(t))
    Jr.call(t, r) && r != "constructor" && e.push(r);
  return e;
}
function mt(t) {
  return vt(t) ? Vr(t) : Qr(t);
}
var kr = /\.|\[(?:[^[\]]*|(["'])(?:(?!\1)[^\\]|\\.)*?\1)\]/, tn = /^\w*$/;
function At(t, e) {
  if (A(t))
    return !1;
  var r = typeof t;
  return r == "number" || r == "symbol" || r == "boolean" || t == null || H(t) ? !0 : tn.test(t) || !kr.test(t) || e != null && t in Object(e);
}
var U = L(Object, "create");
function en() {
  this.__data__ = U ? U(null) : {}, this.size = 0;
}
function rn(t) {
  var e = this.has(t) && delete this.__data__[t];
  return this.size -= e ? 1 : 0, e;
}
var nn = "__lodash_hash_undefined__", an = Object.prototype, on = an.hasOwnProperty;
function sn(t) {
  var e = this.__data__;
  if (U) {
    var r = e[t];
    return r === nn ? void 0 : r;
  }
  return on.call(e, t) ? e[t] : void 0;
}
var un = Object.prototype, fn = un.hasOwnProperty;
function ln(t) {
  var e = this.__data__;
  return U ? e[t] !== void 0 : fn.call(e, t);
}
var cn = "__lodash_hash_undefined__";
function pn(t, e) {
  var r = this.__data__;
  return this.size += this.has(t) ? 0 : 1, r[t] = U && e === void 0 ? cn : e, this;
}
function E(t) {
  var e = -1, r = t == null ? 0 : t.length;
  for (this.clear(); ++e < r; ) {
    var n = t[e];
    this.set(n[0], n[1]);
  }
}
E.prototype.clear = en;
E.prototype.delete = rn;
E.prototype.get = sn;
E.prototype.has = ln;
E.prototype.set = pn;
function gn() {
  this.__data__ = [], this.size = 0;
}
function Q(t, e) {
  for (var r = t.length; r--; )
    if (ie(t[r][0], e))
      return r;
  return -1;
}
var dn = Array.prototype, hn = dn.splice;
function _n(t) {
  var e = this.__data__, r = Q(e, t);
  if (r < 0)
    return !1;
  var n = e.length - 1;
  return r == n ? e.pop() : hn.call(e, r, 1), --this.size, !0;
}
function yn(t) {
  var e = this.__data__, r = Q(e, t);
  return r < 0 ? void 0 : e[r][1];
}
function bn(t) {
  return Q(this.__data__, t) > -1;
}
function vn(t, e) {
  var r = this.__data__, n = Q(r, t);
  return n < 0 ? (++this.size, r.push([t, e])) : r[n][1] = e, this;
}
function $(t) {
  var e = -1, r = t == null ? 0 : t.length;
  for (this.clear(); ++e < r; ) {
    var n = t[e];
    this.set(n[0], n[1]);
  }
}
$.prototype.clear = gn;
$.prototype.delete = _n;
$.prototype.get = yn;
$.prototype.has = bn;
$.prototype.set = vn;
var K = L(O, "Map");
function mn() {
  this.size = 0, this.__data__ = {
    hash: new E(),
    map: new (K || $)(),
    string: new E()
  };
}
function An(t) {
  var e = typeof t;
  return e == "string" || e == "number" || e == "symbol" || e == "boolean" ? t !== "__proto__" : t === null;
}
function k(t, e) {
  var r = t.__data__;
  return An(e) ? r[typeof e == "string" ? "string" : "hash"] : r.map;
}
function Tn(t) {
  var e = k(this, t).delete(t);
  return this.size -= e ? 1 : 0, e;
}
function wn(t) {
  return k(this, t).get(t);
}
function On(t) {
  return k(this, t).has(t);
}
function $n(t, e) {
  var r = k(this, t), n = r.size;
  return r.set(t, e), this.size += r.size == n ? 0 : 1, this;
}
function P(t) {
  var e = -1, r = t == null ? 0 : t.length;
  for (this.clear(); ++e < r; ) {
    var n = t[e];
    this.set(n[0], n[1]);
  }
}
P.prototype.clear = mn;
P.prototype.delete = Tn;
P.prototype.get = wn;
P.prototype.has = On;
P.prototype.set = $n;
var Pn = "Expected a function";
function Tt(t, e) {
  if (typeof t != "function" || e != null && typeof e != "function")
    throw new TypeError(Pn);
  var r = function() {
    var n = arguments, a = e ? e.apply(this, n) : n[0], i = r.cache;
    if (i.has(a))
      return i.get(a);
    var o = t.apply(this, n);
    return r.cache = i.set(a, o) || i, o;
  };
  return r.cache = new (Tt.Cache || P)(), r;
}
Tt.Cache = P;
var Sn = 500;
function Cn(t) {
  var e = Tt(t, function(n) {
    return r.size === Sn && r.clear(), n;
  }), r = e.cache;
  return e;
}
var xn = /[^.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|$))/g, En = /\\(\\)?/g, Rn = Cn(function(t) {
  var e = [];
  return t.charCodeAt(0) === 46 && e.push(""), t.replace(xn, function(r, n, a, i) {
    e.push(a ? i.replace(En, "$1") : n || r);
  }), e;
});
function Dn(t) {
  return t == null ? "" : te(t);
}
function ce(t, e) {
  return A(t) ? t : At(t, e) ? [t] : Rn(Dn(t));
}
function tt(t) {
  if (typeof t == "string" || H(t))
    return t;
  var e = t + "";
  return e == "0" && 1 / t == -1 / 0 ? "-0" : e;
}
function wt(t, e) {
  e = ce(e, t);
  for (var r = 0, n = e.length; t != null && r < n; )
    t = t[tt(e[r++])];
  return r && r == n ? t : void 0;
}
function jn(t, e, r) {
  var n = t == null ? void 0 : wt(t, e);
  return n === void 0 ? r : n;
}
function Fn(t, e) {
  for (var r = -1, n = e.length, a = t.length; ++r < n; )
    t[a + r] = e[r];
  return t;
}
function In() {
  this.__data__ = new $(), this.size = 0;
}
function Mn(t) {
  var e = this.__data__, r = e.delete(t);
  return this.size = e.size, r;
}
function Ln(t) {
  return this.__data__.get(t);
}
function zn(t) {
  return this.__data__.has(t);
}
var Nn = 200;
function Bn(t, e) {
  var r = this.__data__;
  if (r instanceof $) {
    var n = r.__data__;
    if (!K || n.length < Nn - 1)
      return n.push([t, e]), this.size = ++r.size, this;
    r = this.__data__ = new P(n);
  }
  return r.set(t, e), this.size = r.size, this;
}
function T(t) {
  var e = this.__data__ = new $(t);
  this.size = e.size;
}
T.prototype.clear = In;
T.prototype.delete = Mn;
T.prototype.get = Ln;
T.prototype.has = zn;
T.prototype.set = Bn;
function Gn(t, e) {
  for (var r = -1, n = t == null ? 0 : t.length, a = 0, i = []; ++r < n; ) {
    var o = t[r];
    e(o, r, t) && (i[a++] = o);
  }
  return i;
}
function Hn() {
  return [];
}
var Un = Object.prototype, Kn = Un.propertyIsEnumerable, zt = Object.getOwnPropertySymbols, Wn = zt ? function(t) {
  return t == null ? [] : (t = Object(t), Gn(zt(t), function(e) {
    return Kn.call(t, e);
  }));
} : Hn;
function qn(t, e, r) {
  var n = e(t);
  return A(t) ? n : Fn(n, r(t));
}
function Nt(t) {
  return qn(t, mt, Wn);
}
var ut = L(O, "DataView"), ft = L(O, "Promise"), F = L(O, "Set"), Bt = "[object Map]", Vn = "[object Object]", Gt = "[object Promise]", Ht = "[object Set]", Ut = "[object WeakMap]", Kt = "[object DataView]", Xn = R(ut), Zn = R(K), Yn = R(ft), Jn = R(F), Qn = R(ot), S = M;
(ut && S(new ut(new ArrayBuffer(1))) != Kt || K && S(new K()) != Bt || ft && S(ft.resolve()) != Gt || F && S(new F()) != Ht || ot && S(new ot()) != Ut) && (S = function(t) {
  var e = M(t), r = e == Vn ? t.constructor : void 0, n = r ? R(r) : "";
  if (n)
    switch (n) {
      case Xn:
        return Kt;
      case Zn:
        return Bt;
      case Yn:
        return Gt;
      case Jn:
        return Ht;
      case Qn:
        return Ut;
    }
  return e;
});
var Wt = O.Uint8Array, kn = "__lodash_hash_undefined__";
function ti(t) {
  return this.__data__.set(t, kn), this;
}
function ei(t) {
  return this.__data__.has(t);
}
function W(t) {
  var e = -1, r = t == null ? 0 : t.length;
  for (this.__data__ = new P(); ++e < r; )
    this.add(t[e]);
}
W.prototype.add = W.prototype.push = ti;
W.prototype.has = ei;
function ri(t, e) {
  for (var r = -1, n = t == null ? 0 : t.length; ++r < n; )
    if (e(t[r], r, t))
      return !0;
  return !1;
}
function pe(t, e) {
  return t.has(e);
}
var ni = 1, ii = 2;
function ge(t, e, r, n, a, i) {
  var o = r & ni, u = t.length, s = e.length;
  if (u != s && !(o && s > u))
    return !1;
  var f = i.get(t), c = i.get(e);
  if (f && c)
    return f == e && c == t;
  var p = -1, l = !0, _ = r & ii ? new W() : void 0;
  for (i.set(t, e), i.set(e, t); ++p < u; ) {
    var d = t[p], y = e[p];
    if (n)
      var g = o ? n(y, d, p, e, t, i) : n(d, y, p, t, e, i);
    if (g !== void 0) {
      if (g)
        continue;
      l = !1;
      break;
    }
    if (_) {
      if (!ri(e, function(v, m) {
        if (!pe(_, m) && (d === v || a(d, v, r, n, i)))
          return _.push(m);
      })) {
        l = !1;
        break;
      }
    } else if (!(d === y || a(d, y, r, n, i))) {
      l = !1;
      break;
    }
  }
  return i.delete(t), i.delete(e), l;
}
function ai(t) {
  var e = -1, r = Array(t.size);
  return t.forEach(function(n, a) {
    r[++e] = [a, n];
  }), r;
}
function Ot(t) {
  var e = -1, r = Array(t.size);
  return t.forEach(function(n) {
    r[++e] = n;
  }), r;
}
var oi = 1, si = 2, ui = "[object Boolean]", fi = "[object Date]", li = "[object Error]", ci = "[object Map]", pi = "[object Number]", gi = "[object RegExp]", di = "[object Set]", hi = "[object String]", _i = "[object Symbol]", yi = "[object ArrayBuffer]", bi = "[object DataView]", qt = C ? C.prototype : void 0, at = qt ? qt.valueOf : void 0;
function vi(t, e, r, n, a, i, o) {
  switch (r) {
    case bi:
      if (t.byteLength != e.byteLength || t.byteOffset != e.byteOffset)
        return !1;
      t = t.buffer, e = e.buffer;
    case yi:
      return !(t.byteLength != e.byteLength || !i(new Wt(t), new Wt(e)));
    case ui:
    case fi:
    case pi:
      return ie(+t, +e);
    case li:
      return t.name == e.name && t.message == e.message;
    case gi:
    case hi:
      return t == e + "";
    case ci:
      var u = ai;
    case di:
      var s = n & oi;
      if (u || (u = Ot), t.size != e.size && !s)
        return !1;
      var f = o.get(t);
      if (f)
        return f == e;
      n |= si, o.set(t, e);
      var c = ge(u(t), u(e), n, a, i, o);
      return o.delete(t), c;
    case _i:
      if (at)
        return at.call(t) == at.call(e);
  }
  return !1;
}
var mi = 1, Ai = Object.prototype, Ti = Ai.hasOwnProperty;
function wi(t, e, r, n, a, i) {
  var o = r & mi, u = Nt(t), s = u.length, f = Nt(e), c = f.length;
  if (s != c && !o)
    return !1;
  for (var p = s; p--; ) {
    var l = u[p];
    if (!(o ? l in e : Ti.call(e, l)))
      return !1;
  }
  var _ = i.get(t), d = i.get(e);
  if (_ && d)
    return _ == e && d == t;
  var y = !0;
  i.set(t, e), i.set(e, t);
  for (var g = o; ++p < s; ) {
    l = u[p];
    var v = t[l], m = e[l];
    if (n)
      var x = o ? n(m, v, l, e, t, i) : n(v, m, l, t, e, i);
    if (!(x === void 0 ? v === m || a(v, m, r, n, i) : x)) {
      y = !1;
      break;
    }
    g || (g = l == "constructor");
  }
  if (y && !g) {
    var D = t.constructor, z = e.constructor;
    D != z && "constructor" in t && "constructor" in e && !(typeof D == "function" && D instanceof D && typeof z == "function" && z instanceof z) && (y = !1);
  }
  return i.delete(t), i.delete(e), y;
}
var Oi = 1, Vt = "[object Arguments]", Xt = "[object Array]", q = "[object Object]", $i = Object.prototype, Zt = $i.hasOwnProperty;
function Pi(t, e, r, n, a, i) {
  var o = A(t), u = A(e), s = o ? Xt : S(t), f = u ? Xt : S(e);
  s = s == Vt ? q : s, f = f == Vt ? q : f;
  var c = s == q, p = f == q, l = s == f;
  if (l && st(t)) {
    if (!st(e))
      return !1;
    o = !0, c = !1;
  }
  if (l && !c)
    return i || (i = new T()), o || le(t) ? ge(t, e, r, n, a, i) : vi(t, e, s, r, n, a, i);
  if (!(r & Oi)) {
    var _ = c && Zt.call(t, "__wrapped__"), d = p && Zt.call(e, "__wrapped__");
    if (_ || d) {
      var y = _ ? t.value() : t, g = d ? e.value() : e;
      return i || (i = new T()), a(y, g, r, n, i);
    }
  }
  return l ? (i || (i = new T()), wi(t, e, r, n, a, i)) : !1;
}
function $t(t, e, r, n, a) {
  return t === e ? !0 : t == null || e == null || !I(t) && !I(e) ? t !== t && e !== e : Pi(t, e, r, n, $t, a);
}
var Si = 1, Ci = 2;
function xi(t, e, r, n) {
  var a = r.length, i = a;
  if (t == null)
    return !i;
  for (t = Object(t); a--; ) {
    var o = r[a];
    if (o[2] ? o[1] !== t[o[0]] : !(o[0] in t))
      return !1;
  }
  for (; ++a < i; ) {
    o = r[a];
    var u = o[0], s = t[u], f = o[1];
    if (o[2]) {
      if (s === void 0 && !(u in t))
        return !1;
    } else {
      var c = new T(), p;
      if (!(p === void 0 ? $t(f, s, Si | Ci, n, c) : p))
        return !1;
    }
  }
  return !0;
}
function de(t) {
  return t === t && !yt(t);
}
function Ei(t) {
  for (var e = mt(t), r = e.length; r--; ) {
    var n = e[r], a = t[n];
    e[r] = [n, a, de(a)];
  }
  return e;
}
function he(t, e) {
  return function(r) {
    return r == null ? !1 : r[t] === e && (e !== void 0 || t in Object(r));
  };
}
function Ri(t) {
  var e = Ei(t);
  return e.length == 1 && e[0][2] ? he(e[0][0], e[0][1]) : function(r) {
    return r === t || xi(r, t, e);
  };
}
function Di(t, e) {
  return t != null && e in Object(t);
}
function ji(t, e, r) {
  e = ce(e, t);
  for (var n = -1, a = e.length, i = !1; ++n < a; ) {
    var o = tt(e[n]);
    if (!(i = t != null && r(t, o)))
      break;
    t = t[o];
  }
  return i || ++n != a ? i : (a = t == null ? 0 : t.length, !!a && bt(a) && ne(o, a) && (A(t) || oe(t)));
}
function Fi(t, e) {
  return t != null && ji(t, e, Di);
}
var Ii = 1, Mi = 2;
function Li(t, e) {
  return At(t) && de(e) ? he(tt(t), e) : function(r) {
    var n = jn(r, t);
    return n === void 0 && n === e ? Fi(r, t) : $t(e, n, Ii | Mi);
  };
}
function zi(t) {
  return function(e) {
    return e?.[t];
  };
}
function Ni(t) {
  return function(e) {
    return wt(e, t);
  };
}
function Bi(t) {
  return At(t) ? zi(tt(t)) : Ni(t);
}
function _e(t) {
  return typeof t == "function" ? t : t == null ? ee : typeof t == "object" ? A(t) ? Li(t[0], t[1]) : Ri(t) : Bi(t);
}
function Gi(t) {
  return function(e, r, n) {
    for (var a = -1, i = Object(e), o = n(e), u = o.length; u--; ) {
      var s = o[++a];
      if (r(i[s], s, i) === !1)
        break;
    }
    return e;
  };
}
var Hi = Gi();
function Ui(t, e) {
  return t && Hi(t, e, mt);
}
function Ki(t, e) {
  return function(r, n) {
    if (r == null)
      return r;
    if (!vt(r))
      return t(r, n);
    for (var a = r.length, i = -1, o = Object(r); ++i < a && n(o[i], i, o) !== !1; )
      ;
    return r;
  };
}
var Wi = Ki(Ui);
function qi(t, e) {
  var r = -1, n = vt(t) ? Array(t.length) : [];
  return Wi(t, function(a, i, o) {
    n[++r] = e(a, i, o);
  }), n;
}
function Vi(t, e) {
  var r = t.length;
  for (t.sort(e); r--; )
    t[r] = t[r].value;
  return t;
}
function Xi(t, e) {
  if (t !== e) {
    var r = t !== void 0, n = t === null, a = t === t, i = H(t), o = e !== void 0, u = e === null, s = e === e, f = H(e);
    if (!u && !f && !i && t > e || i && o && s && !u && !f || n && o && s || !r && s || !a)
      return 1;
    if (!n && !i && !f && t < e || f && r && a && !n && !i || u && r && a || !o && a || !s)
      return -1;
  }
  return 0;
}
function Zi(t, e, r) {
  for (var n = -1, a = t.criteria, i = e.criteria, o = a.length, u = r.length; ++n < o; ) {
    var s = Xi(a[n], i[n]);
    if (s) {
      if (n >= u)
        return s;
      var f = r[n];
      return s * (f == "desc" ? -1 : 1);
    }
  }
  return t.index - e.index;
}
function Yi(t, e, r) {
  e.length ? e = V(e, function(i) {
    return A(i) ? function(o) {
      return wt(o, i.length === 1 ? i[0] : i);
    } : i;
  }) : e = [ee];
  var n = -1;
  e = V(e, ue(_e));
  var a = qi(t, function(i, o, u) {
    var s = V(e, function(f) {
      return f(i);
    });
    return { criteria: s, index: ++n, value: i };
  });
  return Vi(a, function(i, o) {
    return Zi(i, o, r);
  });
}
function Ji(t, e, r, n) {
  return t == null ? [] : (A(e) || (e = e == null ? [] : [e]), r = r, A(r) || (r = r == null ? [] : [r]), Yi(t, e, r));
}
var Qi = 1 / 0, ki = F && 1 / Ot(new F([, -0]))[1] == Qi ? function(t) {
  return new F(t);
} : er, ta = 200;
function ea(t, e, r) {
  var n = -1, a = or, i = t.length, o = !0, u = [], s = u;
  if (i >= ta) {
    var f = e ? null : ki(t);
    if (f)
      return Ot(f);
    o = !1, a = pe, s = new W();
  } else
    s = e ? [] : u;
  t:
    for (; ++n < i; ) {
      var c = t[n], p = e ? e(c) : c;
      if (c = c !== 0 ? c : 0, o && p === p) {
        for (var l = s.length; l--; )
          if (s[l] === p)
            continue t;
        e && s.push(p), u.push(c);
      } else a(s, p, r) || (s !== u && s.push(p), u.push(c));
    }
  return u;
}
function Yt(t, e) {
  return t && t.length ? ea(t, _e(e)) : [];
}
function ra(t) {
  const { attrs: e, columns: r, registerRowsHandler: n } = t;
  let a = Jt(e.sort);
  const i = w(() => r.value?.some((s) => s.sorter)), o = w(
    () => r.value.filter((s) => s.sorter).length > 1
  );
  return n((s) => {
    if (!a.value)
      return s;
    const f = Array.isArray(a.value) ? a.value : [a.value], c = f.map((l) => l.sortBy), p = f.map(
      (l) => l.descending ? "desc" : "asc"
    );
    return Ji(s, c, p);
  }), {
    onSortChange: (s) => {
      i.value && (a.value = s);
    },
    multipleSort: o,
    sort: a
  };
}
function na(t) {
  return new Function("return " + t)();
}
function ia(t) {
  const { tableData: e, registerColumnsHandler: r, registerRowsHandler: n, columns: a } = t;
  r(
    (c) => c.map(
      (p) => aa(
        p,
        e,
        t.tdesignGlobalConfig
      )
    )
  );
  const i = Jt(), o = new Map(a.value.map((c) => [c.colKey, c]));
  n((c) => {
    if (!i.value)
      return c;
    const p = Object.keys(i.value).map((l) => {
      const _ = i.value[l], d = o.get(l).filter, y = d.type, g = d.predicate ? na(d.predicate) : void 0, v = y ?? d._type;
      return {
        key: l,
        value: _,
        type: v,
        predicate: g
      };
    });
    return c.filter((l) => p.every((_) => {
      const d = _.type, y = _.predicate;
      if (d === "multiple") {
        const g = _.value;
        return g.length === 0 ? !0 : y ? y(i, l) : g.includes(l[_.key]);
      }
      if (d === "single") {
        const g = _.value;
        return g ? y ? y(g, l) : l[_.key] === g : !0;
      }
      if (d === "input") {
        const g = _.value;
        return g ? y ? y(g, l) : l[_.key].toString().includes(g) : !0;
      }
      if (d === "date") {
        const g = _.value;
        if (!g || g === "") return !0;
        const [v, m] = g, x = new Date(l[_.key]);
        return y ? y(g, l) : new Date(v) <= x && x <= new Date(m);
      }
      throw new Error(`not support filter type ${d}`);
    }));
  });
  const u = (c, p) => {
    if (!p.col) {
      i.value = void 0;
      return;
    }
    i.value = {
      ...c
    };
  };
  function s() {
    i.value = void 0;
  }
  function f() {
    return i.value ? Object.keys(i.value).map((c) => {
      const p = o.get(c).label, l = i.value[c];
      return l.length === 0 ? "" : `${p}: ${JSON.stringify(l)}`;
    }).join("; ") : null;
  }
  return {
    onFilterChange: u,
    filterValue: i,
    resetFilters: s,
    filterResultText: f
  };
}
function aa(t, e, r) {
  if (!("filter" in t))
    return t;
  if (!("type" in t.filter)) throw new Error("filter type is required");
  const { colKey: a } = t, i = t.filter.type;
  if (i === "multiple") {
    const o = Yt(e.value, a).map((s) => ({
      label: s[a],
      value: s[a]
    })), u = {
      resetValue: [],
      list: [
        { label: r.selectAllText, checkAll: !0 },
        ...o
      ],
      ...t.filter
    };
    return {
      ...t,
      filter: u
    };
  }
  if (i === "single") {
    const u = {
      resetValue: null,
      list: Yt(e.value, a).map((s) => ({
        label: s[a],
        value: s[a]
      })),
      showConfirmAndReset: !0,
      ...t.filter
    };
    return {
      ...t,
      filter: u
    };
  }
  if (i === "input") {
    const o = {
      resetValue: "",
      confirmEvents: ["onEnter"],
      showConfirmAndReset: !0,
      ...t.filter,
      props: {
        ...t.filter?.props
      }
    };
    return {
      ...t,
      filter: o
    };
  }
  if (i === "date") {
    const o = {
      resetValue: "",
      showConfirmAndReset: !0,
      props: {
        firstDayOfWeek: 7,
        ...t.filter?.props
      },
      style: {
        fontSize: "14px"
      },
      classNames: "custom-class-name",
      attrs: {
        "data-type": "date-range-picker"
      },
      ...t.filter,
      component: me,
      _type: "date"
    };
    return delete o.type, {
      ...t,
      filter: o
    };
  }
  throw new Error(`not support filter type ${i}`);
}
const oa = {
  hover: !0,
  bordered: !0,
  tableLayout: "auto",
  showSortColumnBgColor: !0
};
function sa(t) {
  const { attrs: e } = t;
  return w(() => ({
    ...oa,
    ...e
  }));
}
function ua(t, e) {
  return w(() => {
    const r = Object.keys(t).filter(
      (n) => n.startsWith("header-cell-")
    );
    return e.value.filter((n) => !r.includes(n.title)).map((n) => ({
      slotName: `header-cell-${n.name}`,
      content: n.label ?? n.colKey
    }));
  });
}
const fa = /* @__PURE__ */ Z({
  inheritAttrs: !1,
  __name: "Table",
  setup(t) {
    const e = lt(), { t: r, globalConfig: n } = Ae("table"), { tableData: a, orgData: i, registerRowsHandler: o } = Oe(e), [u, s] = $e({
      tableData: a,
      attrs: e
    }), f = Ce({ tableData: a, attrs: e }), { sort: c, onSortChange: p, multipleSort: l } = ra({
      registerRowsHandler: o,
      attrs: e,
      columns: u
    }), { onFilterChange: _, filterValue: d, resetFilters: y, filterResultText: g } = ia({
      tableData: i,
      registerRowsHandler: o,
      registerColumnsHandler: s,
      columns: u,
      tdesignGlobalConfig: n.value
    }), v = sa({ attrs: e }), m = ct(), x = ua(m, u);
    return (D, z) => (J(), Y(G.Table, pt(b(v), {
      pagination: b(f),
      sort: b(c),
      data: b(a),
      columns: b(u),
      "filter-value": b(d),
      onSortChange: b(p),
      onFilterChange: b(_),
      "multiple-sort": b(l)
    }), gt({
      "filter-row": j(() => [
        St("div", null, [
          St("span", null, rt(b(r)(b(n).searchResultText, {
            result: b(g)(),
            count: b(a).length
          })), 1),
          be(G.Button, {
            theme: "primary",
            variant: "text",
            onClick: b(y)
          }, {
            default: j(() => [
              Ct(rt(b(n).clearFilterResultButtonText), 1)
            ]),
            _: 1
          }, 8, ["onClick"])
        ])
      ]),
      _: 2
    }, [
      X(b(x), (et) => ({
        name: et.slotName,
        fn: j(() => [
          Ct(rt(et.content), 1)
        ])
      })),
      X(b(m), (et, Pt) => ({
        name: Pt,
        fn: j((ye) => [
          dt(D.$slots, Pt, ht(_t(ye)))
        ])
      }))
    ]), 1040, ["pagination", "sort", "data", "columns", "filter-value", "onSortChange", "onFilterChange", "multiple-sort"]));
  }
});
function la(t) {
  const { affixProps: e = {} } = t;
  return {
    container: ".insta-main",
    ...e
  };
}
function ca(t) {
  const { container: e = ".insta-main" } = t;
  return e;
}
const pa = /* @__PURE__ */ Z({
  inheritAttrs: !1,
  __name: "Anchor",
  setup(t) {
    const e = lt(), r = ct(), n = la(e), a = ca(e);
    return (i, o) => (J(), Y(G.Anchor, pt(b(e), {
      container: b(a),
      "affix-props": b(n)
    }), gt({ _: 2 }, [
      X(b(r), (u, s) => ({
        name: s,
        fn: j((f) => [
          dt(i.$slots, s, ht(_t(f)))
        ])
      }))
    ]), 1040, ["container", "affix-props"]));
  }
}), ga = /* @__PURE__ */ Z({
  __name: "Icon",
  props: {
    name: {},
    size: {},
    color: {},
    prefix: {}
  },
  setup(t) {
    const e = t, r = w(() => {
      const [n, a] = e.name.split(":");
      return a ? e.name : `${e.prefix || "tdesign"}:${e.name}`;
    });
    return (n, a) => (J(), Y(ve("icon"), {
      class: "t-icon",
      icon: r.value,
      size: n.size,
      color: n.color
    }, null, 8, ["icon", "size", "color"]));
  }
});
function _a(t) {
  t.use(G), t.component("t-table", fa), t.component("t-affix", we), t.component("t-anchor", pa), t.component("t-icon", ga);
}
export {
  _a as install
};
