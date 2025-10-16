function Tt(a, t, n, e) {
  if (t === !1 || t == null || !t && a === "style") return "";
  if (t === !0) return " " + (a + '="' + a + '"');
  var i = typeof t;
  return i !== "object" && i !== "function" || typeof t.toJSON != "function" || (t = t.toJSON()), typeof t == "string" || (t = JSON.stringify(t), n) ? (t = ue(t), " " + a + '="' + t + '"') : " " + a + "='" + t.replace(/'/g, "&#39;") + "'";
}
function ue(a) {
  var t = "" + a, n = le.exec(t);
  if (!n) return a;
  var e, i, o, l = "";
  for (e = n.index, i = 0; e < t.length; e++) {
    switch (t.charCodeAt(e)) {
      case 34:
        o = "&quot;";
        break;
      case 38:
        o = "&amp;";
        break;
      case 60:
        o = "&lt;";
        break;
      case 62:
        o = "&gt;";
        break;
      default:
        continue;
    }
    i !== e && (l += t.substring(i, e)), i = e + 1, l += o;
  }
  return i !== e ? l + t.substring(i, e) : l;
}
var le = /["&<>]/;
function Bt(a, t, n, e) {
  if (!(a instanceof Error)) throw a;
  if (!(typeof window > "u" && t || e)) throw a.message += " on line " + n, a;
  var i, o, l, c;
  try {
    e = e || require("fs").readFileSync(t, { encoding: "utf8" }), i = 3, o = e.split(`
`), l = Math.max(n - i, 0), c = Math.min(o.length, n + i);
  } catch (d) {
    return a.message += " - could not read from " + t + " (" + d.message + ")", void Bt(a, null, n);
  }
  i = o.slice(l, c).map(function(d, u) {
    var h = u + l + 1;
    return (h == n ? "  > " : "    ") + h + "| " + d;
  }).join(`
`), a.path = t;
  try {
    a.message = (t || "Pug") + ":" + n + `
` + i + `

` + a.message;
  } catch {
  }
  throw a;
}
function ge(a) {
  var t = "", n, e;
  try {
    var i = a || {};
    (function(o) {
      e = 1, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + '<div class="g-config-breadcrumb-container"></div>', e = 2, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + '<form id="g-large-image-form" role="form">', e = 3, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + '<div class="form-group">', e = 4, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + "<label>", e = 4, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + "Store annotation history</label>", e = 5, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + '<p class="g-large-image-description">', e = 6, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + "Whenever annotations are saved, a record of the annotation's previous state can be kept.</p>", e = 7, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + '<div class="g-large-image-annotation-history-container">', e = 8, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + '<label class="radio-inline">', e = 9, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + "<input" + (' class="g-large-image-annotation-history-show" type="radio" name="g-large-image-annotation-history"' + Tt("checked", o["large_image.annotation_history"] !== !1 ? "checked" : void 0, !0, !1)) + "/>", e = 10, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + "Record annotation history</label>", e = 11, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + '<label class="radio-inline">', e = 12, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + "<input" + (' class="g-large-image-annotation-history-hide" type="radio" name="g-large-image-annotation-history"' + Tt("checked", o["large_image.annotation_history"] !== !1 ? void 0 : "checked", !0, !1)) + "/>", e = 13, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + "Don't store history</label></div></div>", e = 14, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + '<p class="g-validation-failed-message" id="g-large-image-error-message"></p>', e = 15, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/largeImageAnnotationConfig.pug", t = t + '<input class="btn btn-sm btn-primary" type="submit" value="Save"/></form>';
    }).call(this, "settings" in i ? i.settings : typeof settings < "u" ? settings : void 0);
  } catch (o) {
    Bt(o, n, e);
  }
  return t;
}
const ce = girder.views.View, de = girder.views.widgets.PluginConfigBreadcrumbWidget, { restRequest: he } = girder.rest, _e = girder.events;
var nt = ce.extend({
  events: {
    "submit #g-large-image-form": function(a) {
      a.preventDefault(), this.$("#g-large-image-error-message").empty(), this._saveSettings([{
        key: "large_image.annotation_history",
        value: this.$(".g-large-image-annotation-history-show").prop("checked")
      }]);
    }
  },
  initialize: function() {
    nt.getSettings((a) => {
      this.settings = a, this.render();
    });
  },
  render: function() {
    return this.$el.html(ge({
      settings: this.settings,
      viewers: nt.viewers
    })), this.breadcrumb || (this.breadcrumb = new de({
      pluginName: "Large image annotation",
      el: this.$(".g-config-breadcrumb-container"),
      parentView: this
    }).render()), this;
  },
  _saveSettings: function(a) {
    return he({
      type: "PUT",
      url: "system/setting",
      data: {
        list: JSON.stringify(a)
      },
      error: null
    }).done(() => {
      nt.clearSettings(), _e.trigger("g:alert", {
        icon: "ok",
        text: "Settings saved.",
        type: "success",
        timeout: 4e3
      });
    }).fail((t) => {
      this.$("#g-large-image-error-message").text(
        t.responseJSON.message
      );
    });
  }
}, {
  /* Class methods and objects */
  /**
   * Get settings if we haven't yet done so.  Either way, call a callback
   * when we have settings.
   *
   * @param {function} callback a function to call after the settings are
   *      fetched.  If the settings are already present, this is called
   *      without any delay.
   */
  getSettings: function(a) {
    return girder.plugins.large_image.views.ConfigView.getSettings(a);
  },
  /**
   * Clear the settings so that getSettings will refetch them.
   */
  clearSettings: function() {
    return girder.plugins.large_image.views.ConfigView.clearSettings();
  }
});
const fe = girder.events, pe = girder.router, { exposePluginConfig: Fe } = girder.utilities.PluginUtils;
Fe("large_image_annotation", "plugins/large_image_annotation/config");
pe.route("plugins/large_image_annotation/config", "largeImageAnnotationConfig", function() {
  fe.trigger("g:navigateTo", nt);
});
function qt(a, t, n, e) {
  if (!(a instanceof Error)) throw a;
  if (!(typeof window > "u" && t || e)) throw a.message += " on line " + n, a;
  var i, o, l, c;
  try {
    e = e || require("fs").readFileSync(t, { encoding: "utf8" }), i = 3, o = e.split(`
`), l = Math.max(n - i, 0), c = Math.min(o.length, n + i);
  } catch (d) {
    return a.message += " - could not read from " + t + " (" + d.message + ")", void qt(a, null, n);
  }
  i = o.slice(l, c).map(function(d, u) {
    var h = u + l + 1;
    return (h == n ? "  > " : "    ") + h + "| " + d;
  }).join(`
`), a.path = t;
  try {
    a.message = (t || "Pug") + ":" + n + `
` + i + `

` + a.message;
  } catch {
  }
  throw a;
}
function me(a) {
  var t = "", n, e;
  try {
    e = 1, n = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/imageViewerAnnotationList.pug", t = t + '<div class="g-annotation-list-container"></div>';
  } catch (i) {
    qt(i, n, e);
  }
  return t;
}
const ye = girder.Backbone, be = ye.Model.extend({
  idAttribute: "id"
}), we = girder.Backbone, Gt = we.Collection.extend({
  initialize: function() {
    this.on("add", this.track_addition, this), this.on("remove", this.track_remove, this), this.on("change", this.track_change, this);
  },
  model: be,
  comparator: void 0,
  track_addition: function(a) {
    !this.annotation || !this.annotation.get || !this.annotation.get("_version") || (this.annotation._changeLog || (this.annotation._changeLog = {}), this.annotation._changeLog[a.id] = { op: "add", path: `elements/id:${a.id}`, value: a.toJSON() });
  },
  track_remove: function(a) {
    !this.annotation || !this.annotation.get || !this.annotation.get("_version") || (this.annotation._changeLog || (this.annotation._changeLog = {}), this.annotation._changeLog[a.id] && this.annotation._changeLog[a.id].op === "add" ? delete this.annotation._changeLog[a.id] : this.annotation._changeLog[a.id] = { op: "remove", path: `elements/id:${a.id}` });
  },
  track_change: function(a) {
    !this.annotation || !this.annotation.get || !this.annotation.get("_version") || (this.annotation._changeLog || (this.annotation._changeLog = {}), this.annotation._changeLog[a.id] = { op: "replace", path: `elements/id:${a.id}`, value: a.toJSON() });
  }
});
function jt(a, t) {
  const n = Math.cos(a), e = Math.sin(a);
  return t = t || [0, 0], function(i) {
    const o = i[0] - t[0], l = i[1] - t[1];
    return [
      o * n - l * e + t[0],
      o * e + l * n + t[1]
    ];
  };
}
const ve = girder._;
function Ce(a) {
  const t = a.center, n = t[0], e = t[1], i = a.height, o = a.width, l = a.rotation || 0, c = n - o / 2, d = n + o / 2, u = e - i / 2, h = e + i / 2;
  return {
    type: "Polygon",
    coordinates: [ve.map([
      [c, u],
      [d, u],
      [d, h],
      [c, h],
      [c, u]
    ], jt(l, t))],
    annotationType: "rectangle"
  };
}
const Ae = girder._;
function Le(a) {
  const t = a.center, n = t[0], e = t[1], i = a.height, o = a.width, l = a.rotation || 0, c = n - o / 2, d = n + o / 2, u = e - i / 2, h = e + i / 2;
  return {
    type: "Polygon",
    coordinates: [Ae.map([
      [c, u],
      [d, u],
      [d, h],
      [c, h],
      [c, u]
    ], jt(l, t))],
    annotationType: "ellipse"
  };
}
function xe(a) {
  const t = a.center, n = t[0], e = t[1], i = a.radius, o = n - i, l = n + i, c = e - i, d = e + i;
  return {
    type: "Polygon",
    coordinates: [[
      [o, c],
      [l, c],
      [l, d],
      [o, d],
      [o, c]
    ]],
    annotationType: "circle"
  };
}
const bt = girder._;
function Ee(a) {
  const t = bt.map(a.points, (o) => bt.first(o, 2));
  var n, e, i;
  if (a.closed) {
    if (t.push(t[0]), e = [t], a.holes) {
      const o = (a.holes || []).map((l) => {
        const c = l.map((d) => bt.first(d, 2));
        return c.push(c[0]), c;
      });
      e = e.concat(o);
    }
    n = "Polygon", i = "polygon";
  } else
    n = "LineString", e = t, i = "line";
  return {
    type: n,
    coordinates: e,
    annotationType: i
  };
}
const je = girder._;
function We(a) {
  return {
    type: "Point",
    coordinates: je.first(a.center, 2),
    annotationType: "point"
  };
}
const xt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  circle: xe,
  ellipse: Le,
  point: We,
  polyline: Ee,
  rectangle: Ce
}, Symbol.toStringTag, { value: "Module" })), ke = {
  fillColor: "rgba(0,0,0,0)",
  lineColor: "rgb(0,0,0)",
  lineWidth: 2,
  rotation: 0,
  normal: [0, 0, 1]
}, $e = {
  fillColor: "rgba(0,0,0,0)",
  lineColor: "rgb(0,0,0)",
  lineWidth: 2,
  rotation: 0,
  normal: [0, 0, 1]
}, Oe = {
  fillColor: "rgba(0,0,0,0)",
  lineColor: "rgb(0,0,0)",
  lineWidth: 2
}, Se = {
  fillColor: "rgba(0,0,0,0)",
  lineColor: "rgb(0,0,0)",
  lineWidth: 2
}, Ie = {
  lineColor: "rgb(0,0,0)",
  lineWidth: 2,
  fillColor: "rgba(0,0,0,0)"
}, Wt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  circle: Oe,
  ellipse: $e,
  point: Ie,
  polyline: Se,
  rectangle: ke
}, Symbol.toStringTag, { value: "Module" }));
function Te(a) {
  return a && a.__esModule && Object.prototype.hasOwnProperty.call(a, "default") ? a.default : a;
}
var Qt = { exports: {} };
(function(a) {
  (function(t) {
    var n = /^\s+/, e = /\s+$/, i = 0, o = t.round, l = t.min, c = t.max, d = t.random;
    function u(r, g) {
      if (r = r || "", g = g || {}, r instanceof u)
        return r;
      if (!(this instanceof u))
        return new u(r, g);
      var s = h(r);
      this._originalInput = r, this._r = s.r, this._g = s.g, this._b = s.b, this._a = s.a, this._roundA = o(100 * this._a) / 100, this._format = g.format || s.format, this._gradientType = g.gradientType, this._r < 1 && (this._r = o(this._r)), this._g < 1 && (this._g = o(this._g)), this._b < 1 && (this._b = o(this._b)), this._ok = s.ok, this._tc_id = i++;
    }
    u.prototype = {
      isDark: function() {
        return this.getBrightness() < 128;
      },
      isLight: function() {
        return !this.isDark();
      },
      isValid: function() {
        return this._ok;
      },
      getOriginalInput: function() {
        return this._originalInput;
      },
      getFormat: function() {
        return this._format;
      },
      getAlpha: function() {
        return this._a;
      },
      getBrightness: function() {
        var r = this.toRgb();
        return (r.r * 299 + r.g * 587 + r.b * 114) / 1e3;
      },
      getLuminance: function() {
        var r = this.toRgb(), g, s, _, y, p, x;
        return g = r.r / 255, s = r.g / 255, _ = r.b / 255, g <= 0.03928 ? y = g / 12.92 : y = t.pow((g + 0.055) / 1.055, 2.4), s <= 0.03928 ? p = s / 12.92 : p = t.pow((s + 0.055) / 1.055, 2.4), _ <= 0.03928 ? x = _ / 12.92 : x = t.pow((_ + 0.055) / 1.055, 2.4), 0.2126 * y + 0.7152 * p + 0.0722 * x;
      },
      setAlpha: function(r) {
        return this._a = N(r), this._roundA = o(100 * this._a) / 100, this;
      },
      toHsv: function() {
        var r = w(this._r, this._g, this._b);
        return { h: r.h * 360, s: r.s, v: r.v, a: this._a };
      },
      toHsvString: function() {
        var r = w(this._r, this._g, this._b), g = o(r.h * 360), s = o(r.s * 100), _ = o(r.v * 100);
        return this._a == 1 ? "hsv(" + g + ", " + s + "%, " + _ + "%)" : "hsva(" + g + ", " + s + "%, " + _ + "%, " + this._roundA + ")";
      },
      toHsl: function() {
        var r = f(this._r, this._g, this._b);
        return { h: r.h * 360, s: r.s, l: r.l, a: this._a };
      },
      toHslString: function() {
        var r = f(this._r, this._g, this._b), g = o(r.h * 360), s = o(r.s * 100), _ = o(r.l * 100);
        return this._a == 1 ? "hsl(" + g + ", " + s + "%, " + _ + "%)" : "hsla(" + g + ", " + s + "%, " + _ + "%, " + this._roundA + ")";
      },
      toHex: function(r) {
        return R(this._r, this._g, this._b, r);
      },
      toHexString: function(r) {
        return "#" + this.toHex(r);
      },
      toHex8: function(r) {
        return S(this._r, this._g, this._b, this._a, r);
      },
      toHex8String: function(r) {
        return "#" + this.toHex8(r);
      },
      toRgb: function() {
        return { r: o(this._r), g: o(this._g), b: o(this._b), a: this._a };
      },
      toRgbString: function() {
        return this._a == 1 ? "rgb(" + o(this._r) + ", " + o(this._g) + ", " + o(this._b) + ")" : "rgba(" + o(this._r) + ", " + o(this._g) + ", " + o(this._b) + ", " + this._roundA + ")";
      },
      toPercentageRgb: function() {
        return { r: o(j(this._r, 255) * 100) + "%", g: o(j(this._g, 255) * 100) + "%", b: o(j(this._b, 255) * 100) + "%", a: this._a };
      },
      toPercentageRgbString: function() {
        return this._a == 1 ? "rgb(" + o(j(this._r, 255) * 100) + "%, " + o(j(this._g, 255) * 100) + "%, " + o(j(this._b, 255) * 100) + "%)" : "rgba(" + o(j(this._r, 255) * 100) + "%, " + o(j(this._g, 255) * 100) + "%, " + o(j(this._b, 255) * 100) + "%, " + this._roundA + ")";
      },
      toName: function() {
        return this._a === 0 ? "transparent" : this._a < 1 ? !1 : ae[R(this._r, this._g, this._b, !0)] || !1;
      },
      toFilter: function(r) {
        var g = "#" + W(this._r, this._g, this._b, this._a), s = g, _ = this._gradientType ? "GradientType = 1, " : "";
        if (r) {
          var y = u(r);
          s = "#" + W(y._r, y._g, y._b, y._a);
        }
        return "progid:DXImageTransform.Microsoft.gradient(" + _ + "startColorstr=" + g + ",endColorstr=" + s + ")";
      },
      toString: function(r) {
        var g = !!r;
        r = r || this._format;
        var s = !1, _ = this._a < 1 && this._a >= 0, y = !g && _ && (r === "hex" || r === "hex6" || r === "hex3" || r === "hex4" || r === "hex8" || r === "name");
        return y ? r === "name" && this._a === 0 ? this.toName() : this.toRgbString() : (r === "rgb" && (s = this.toRgbString()), r === "prgb" && (s = this.toPercentageRgbString()), (r === "hex" || r === "hex6") && (s = this.toHexString()), r === "hex3" && (s = this.toHexString(!0)), r === "hex4" && (s = this.toHex8String(!0)), r === "hex8" && (s = this.toHex8String()), r === "name" && (s = this.toName()), r === "hsl" && (s = this.toHslString()), r === "hsv" && (s = this.toHsvString()), s || this.toHexString());
      },
      clone: function() {
        return u(this.toString());
      },
      _applyModification: function(r, g) {
        var s = r.apply(null, [this].concat([].slice.call(g)));
        return this._r = s._r, this._g = s._g, this._b = s._b, this.setAlpha(s._a), this;
      },
      lighten: function() {
        return this._applyModification(q, arguments);
      },
      brighten: function() {
        return this._applyModification(D, arguments);
      },
      darken: function() {
        return this._applyModification(G, arguments);
      },
      desaturate: function() {
        return this._applyModification(M, arguments);
      },
      saturate: function() {
        return this._applyModification(m, arguments);
      },
      greyscale: function() {
        return this._applyModification(it, arguments);
      },
      spin: function() {
        return this._applyModification(Q, arguments);
      },
      _applyCombination: function(r, g) {
        return r.apply(null, [this].concat([].slice.call(g)));
      },
      analogous: function() {
        return this._applyCombination(E, arguments);
      },
      complement: function() {
        return this._applyCombination(J, arguments);
      },
      monochromatic: function() {
        return this._applyCombination(Ft, arguments);
      },
      splitcomplement: function() {
        return this._applyCombination(C, arguments);
      },
      triad: function() {
        return this._applyCombination(Z, arguments);
      },
      tetrad: function() {
        return this._applyCombination(at, arguments);
      }
    }, u.fromRatio = function(r, g) {
      if (typeof r == "object") {
        var s = {};
        for (var _ in r)
          r.hasOwnProperty(_) && (_ === "a" ? s[_] = r[_] : s[_] = ot(r[_]));
        r = s;
      }
      return u(r, g);
    };
    function h(r) {
      var g = { r: 0, g: 0, b: 0 }, s = 1, _ = null, y = null, p = null, x = !1, O = !1;
      return typeof r == "string" && (r = re(r)), typeof r == "object" && (B(r.r) && B(r.g) && B(r.b) ? (g = F(r.r, r.g, r.b), x = !0, O = String(r.r).substr(-1) === "%" ? "prgb" : "rgb") : B(r.h) && B(r.s) && B(r.v) ? (_ = ot(r.s), y = ot(r.v), g = L(r.h, _, y), x = !0, O = "hsv") : B(r.h) && B(r.s) && B(r.l) && (_ = ot(r.s), p = ot(r.l), g = b(r.h, _, p), x = !0, O = "hsl"), r.hasOwnProperty("a") && (s = r.a)), s = N(s), {
        ok: x,
        format: r.format || O,
        r: l(255, c(g.r, 0)),
        g: l(255, c(g.g, 0)),
        b: l(255, c(g.b, 0)),
        a: s
      };
    }
    function F(r, g, s) {
      return {
        r: j(r, 255) * 255,
        g: j(g, 255) * 255,
        b: j(s, 255) * 255
      };
    }
    function f(r, g, s) {
      r = j(r, 255), g = j(g, 255), s = j(s, 255);
      var _ = c(r, g, s), y = l(r, g, s), p, x, O = (_ + y) / 2;
      if (_ == y)
        p = x = 0;
      else {
        var I = _ - y;
        switch (x = O > 0.5 ? I / (2 - _ - y) : I / (_ + y), _) {
          case r:
            p = (g - s) / I + (g < s ? 6 : 0);
            break;
          case g:
            p = (s - r) / I + 2;
            break;
          case s:
            p = (r - g) / I + 4;
            break;
        }
        p /= 6;
      }
      return { h: p, s: x, l: O };
    }
    function b(r, g, s) {
      var _, y, p;
      r = j(r, 360), g = j(g, 100), s = j(s, 100);
      function x(P, rt, V) {
        return V < 0 && (V += 1), V > 1 && (V -= 1), V < 1 / 6 ? P + (rt - P) * 6 * V : V < 1 / 2 ? rt : V < 2 / 3 ? P + (rt - P) * (2 / 3 - V) * 6 : P;
      }
      if (g === 0)
        _ = y = p = s;
      else {
        var O = s < 0.5 ? s * (1 + g) : s + g - s * g, I = 2 * s - O;
        _ = x(I, O, r + 1 / 3), y = x(I, O, r), p = x(I, O, r - 1 / 3);
      }
      return { r: _ * 255, g: y * 255, b: p * 255 };
    }
    function w(r, g, s) {
      r = j(r, 255), g = j(g, 255), s = j(s, 255);
      var _ = c(r, g, s), y = l(r, g, s), p, x, O = _, I = _ - y;
      if (x = _ === 0 ? 0 : I / _, _ == y)
        p = 0;
      else {
        switch (_) {
          case r:
            p = (g - s) / I + (g < s ? 6 : 0);
            break;
          case g:
            p = (s - r) / I + 2;
            break;
          case s:
            p = (r - g) / I + 4;
            break;
        }
        p /= 6;
      }
      return { h: p, s: x, v: O };
    }
    function L(r, g, s) {
      r = j(r, 360) * 6, g = j(g, 100), s = j(s, 100);
      var _ = t.floor(r), y = r - _, p = s * (1 - g), x = s * (1 - y * g), O = s * (1 - (1 - y) * g), I = _ % 6, P = [s, x, p, p, O, s][I], rt = [O, s, s, x, p, p][I], V = [p, p, O, s, s, x][I];
      return { r: P * 255, g: rt * 255, b: V * 255 };
    }
    function R(r, g, s, _) {
      var y = [
        H(o(r).toString(16)),
        H(o(g).toString(16)),
        H(o(s).toString(16))
      ];
      return _ && y[0].charAt(0) == y[0].charAt(1) && y[1].charAt(0) == y[1].charAt(1) && y[2].charAt(0) == y[2].charAt(1) ? y[0].charAt(0) + y[1].charAt(0) + y[2].charAt(0) : y.join("");
    }
    function S(r, g, s, _, y) {
      var p = [
        H(o(r).toString(16)),
        H(o(g).toString(16)),
        H(o(s).toString(16)),
        H(lt(_))
      ];
      return y && p[0].charAt(0) == p[0].charAt(1) && p[1].charAt(0) == p[1].charAt(1) && p[2].charAt(0) == p[2].charAt(1) && p[3].charAt(0) == p[3].charAt(1) ? p[0].charAt(0) + p[1].charAt(0) + p[2].charAt(0) + p[3].charAt(0) : p.join("");
    }
    function W(r, g, s, _) {
      var y = [
        H(lt(_)),
        H(o(r).toString(16)),
        H(o(g).toString(16)),
        H(o(s).toString(16))
      ];
      return y.join("");
    }
    u.equals = function(r, g) {
      return !r || !g ? !1 : u(r).toRgbString() == u(g).toRgbString();
    }, u.random = function() {
      return u.fromRatio({
        r: d(),
        g: d(),
        b: d()
      });
    };
    function M(r, g) {
      g = g === 0 ? 0 : g || 10;
      var s = u(r).toHsl();
      return s.s -= g / 100, s.s = v(s.s), u(s);
    }
    function m(r, g) {
      g = g === 0 ? 0 : g || 10;
      var s = u(r).toHsl();
      return s.s += g / 100, s.s = v(s.s), u(s);
    }
    function it(r) {
      return u(r).desaturate(100);
    }
    function q(r, g) {
      g = g === 0 ? 0 : g || 10;
      var s = u(r).toHsl();
      return s.l += g / 100, s.l = v(s.l), u(s);
    }
    function D(r, g) {
      g = g === 0 ? 0 : g || 10;
      var s = u(r).toRgb();
      return s.r = c(0, l(255, s.r - o(255 * -(g / 100)))), s.g = c(0, l(255, s.g - o(255 * -(g / 100)))), s.b = c(0, l(255, s.b - o(255 * -(g / 100)))), u(s);
    }
    function G(r, g) {
      g = g === 0 ? 0 : g || 10;
      var s = u(r).toHsl();
      return s.l -= g / 100, s.l = v(s.l), u(s);
    }
    function Q(r, g) {
      var s = u(r).toHsl(), _ = (s.h + g) % 360;
      return s.h = _ < 0 ? 360 + _ : _, u(s);
    }
    function J(r) {
      var g = u(r).toHsl();
      return g.h = (g.h + 180) % 360, u(g);
    }
    function Z(r) {
      var g = u(r).toHsl(), s = g.h;
      return [
        u(r),
        u({ h: (s + 120) % 360, s: g.s, l: g.l }),
        u({ h: (s + 240) % 360, s: g.s, l: g.l })
      ];
    }
    function at(r) {
      var g = u(r).toHsl(), s = g.h;
      return [
        u(r),
        u({ h: (s + 90) % 360, s: g.s, l: g.l }),
        u({ h: (s + 180) % 360, s: g.s, l: g.l }),
        u({ h: (s + 270) % 360, s: g.s, l: g.l })
      ];
    }
    function C(r) {
      var g = u(r).toHsl(), s = g.h;
      return [
        u(r),
        u({ h: (s + 72) % 360, s: g.s, l: g.l }),
        u({ h: (s + 216) % 360, s: g.s, l: g.l })
      ];
    }
    function E(r, g, s) {
      g = g || 6, s = s || 30;
      var _ = u(r).toHsl(), y = 360 / s, p = [u(r)];
      for (_.h = (_.h - (y * g >> 1) + 720) % 360; --g; )
        _.h = (_.h + y) % 360, p.push(u(_));
      return p;
    }
    function Ft(r, g) {
      g = g || 6;
      for (var s = u(r).toHsv(), _ = s.h, y = s.s, p = s.v, x = [], O = 1 / g; g--; )
        x.push(u({ h: _, s: y, v: p })), p = (p + O) % 1;
      return x;
    }
    u.mix = function(r, g, s) {
      s = s === 0 ? 0 : s || 50;
      var _ = u(r).toRgb(), y = u(g).toRgb(), p = s / 100, x = {
        r: (y.r - _.r) * p + _.r,
        g: (y.g - _.g) * p + _.g,
        b: (y.b - _.b) * p + _.b,
        a: (y.a - _.a) * p + _.a
      };
      return u(x);
    }, u.readability = function(r, g) {
      var s = u(r), _ = u(g);
      return (t.max(s.getLuminance(), _.getLuminance()) + 0.05) / (t.min(s.getLuminance(), _.getLuminance()) + 0.05);
    }, u.isReadable = function(r, g, s) {
      var _ = u.readability(r, g), y, p;
      switch (p = !1, y = se(s), y.level + y.size) {
        case "AAsmall":
        case "AAAlarge":
          p = _ >= 4.5;
          break;
        case "AAlarge":
          p = _ >= 3;
          break;
        case "AAAsmall":
          p = _ >= 7;
          break;
      }
      return p;
    }, u.mostReadable = function(r, g, s) {
      var _ = null, y = 0, p, x, O, I;
      s = s || {}, x = s.includeFallbackColors, O = s.level, I = s.size;
      for (var P = 0; P < g.length; P++)
        p = u.readability(r, g[P]), p > y && (y = p, _ = u(g[P]));
      return u.isReadable(r, _, { level: O, size: I }) || !x ? _ : (s.includeFallbackColors = !1, u.mostReadable(r, ["#fff", "#000"], s));
    };
    var mt = u.names = {
      aliceblue: "f0f8ff",
      antiquewhite: "faebd7",
      aqua: "0ff",
      aquamarine: "7fffd4",
      azure: "f0ffff",
      beige: "f5f5dc",
      bisque: "ffe4c4",
      black: "000",
      blanchedalmond: "ffebcd",
      blue: "00f",
      blueviolet: "8a2be2",
      brown: "a52a2a",
      burlywood: "deb887",
      burntsienna: "ea7e5d",
      cadetblue: "5f9ea0",
      chartreuse: "7fff00",
      chocolate: "d2691e",
      coral: "ff7f50",
      cornflowerblue: "6495ed",
      cornsilk: "fff8dc",
      crimson: "dc143c",
      cyan: "0ff",
      darkblue: "00008b",
      darkcyan: "008b8b",
      darkgoldenrod: "b8860b",
      darkgray: "a9a9a9",
      darkgreen: "006400",
      darkgrey: "a9a9a9",
      darkkhaki: "bdb76b",
      darkmagenta: "8b008b",
      darkolivegreen: "556b2f",
      darkorange: "ff8c00",
      darkorchid: "9932cc",
      darkred: "8b0000",
      darksalmon: "e9967a",
      darkseagreen: "8fbc8f",
      darkslateblue: "483d8b",
      darkslategray: "2f4f4f",
      darkslategrey: "2f4f4f",
      darkturquoise: "00ced1",
      darkviolet: "9400d3",
      deeppink: "ff1493",
      deepskyblue: "00bfff",
      dimgray: "696969",
      dimgrey: "696969",
      dodgerblue: "1e90ff",
      firebrick: "b22222",
      floralwhite: "fffaf0",
      forestgreen: "228b22",
      fuchsia: "f0f",
      gainsboro: "dcdcdc",
      ghostwhite: "f8f8ff",
      gold: "ffd700",
      goldenrod: "daa520",
      gray: "808080",
      green: "008000",
      greenyellow: "adff2f",
      grey: "808080",
      honeydew: "f0fff0",
      hotpink: "ff69b4",
      indianred: "cd5c5c",
      indigo: "4b0082",
      ivory: "fffff0",
      khaki: "f0e68c",
      lavender: "e6e6fa",
      lavenderblush: "fff0f5",
      lawngreen: "7cfc00",
      lemonchiffon: "fffacd",
      lightblue: "add8e6",
      lightcoral: "f08080",
      lightcyan: "e0ffff",
      lightgoldenrodyellow: "fafad2",
      lightgray: "d3d3d3",
      lightgreen: "90ee90",
      lightgrey: "d3d3d3",
      lightpink: "ffb6c1",
      lightsalmon: "ffa07a",
      lightseagreen: "20b2aa",
      lightskyblue: "87cefa",
      lightslategray: "789",
      lightslategrey: "789",
      lightsteelblue: "b0c4de",
      lightyellow: "ffffe0",
      lime: "0f0",
      limegreen: "32cd32",
      linen: "faf0e6",
      magenta: "f0f",
      maroon: "800000",
      mediumaquamarine: "66cdaa",
      mediumblue: "0000cd",
      mediumorchid: "ba55d3",
      mediumpurple: "9370db",
      mediumseagreen: "3cb371",
      mediumslateblue: "7b68ee",
      mediumspringgreen: "00fa9a",
      mediumturquoise: "48d1cc",
      mediumvioletred: "c71585",
      midnightblue: "191970",
      mintcream: "f5fffa",
      mistyrose: "ffe4e1",
      moccasin: "ffe4b5",
      navajowhite: "ffdead",
      navy: "000080",
      oldlace: "fdf5e6",
      olive: "808000",
      olivedrab: "6b8e23",
      orange: "ffa500",
      orangered: "ff4500",
      orchid: "da70d6",
      palegoldenrod: "eee8aa",
      palegreen: "98fb98",
      paleturquoise: "afeeee",
      palevioletred: "db7093",
      papayawhip: "ffefd5",
      peachpuff: "ffdab9",
      peru: "cd853f",
      pink: "ffc0cb",
      plum: "dda0dd",
      powderblue: "b0e0e6",
      purple: "800080",
      rebeccapurple: "663399",
      red: "f00",
      rosybrown: "bc8f8f",
      royalblue: "4169e1",
      saddlebrown: "8b4513",
      salmon: "fa8072",
      sandybrown: "f4a460",
      seagreen: "2e8b57",
      seashell: "fff5ee",
      sienna: "a0522d",
      silver: "c0c0c0",
      skyblue: "87ceeb",
      slateblue: "6a5acd",
      slategray: "708090",
      slategrey: "708090",
      snow: "fffafa",
      springgreen: "00ff7f",
      steelblue: "4682b4",
      tan: "d2b48c",
      teal: "008080",
      thistle: "d8bfd8",
      tomato: "ff6347",
      turquoise: "40e0d0",
      violet: "ee82ee",
      wheat: "f5deb3",
      white: "fff",
      whitesmoke: "f5f5f5",
      yellow: "ff0",
      yellowgreen: "9acd32"
    }, ae = u.hexNames = Y(mt);
    function Y(r) {
      var g = {};
      for (var s in r)
        r.hasOwnProperty(s) && (g[r[s]] = s);
      return g;
    }
    function N(r) {
      return r = parseFloat(r), (isNaN(r) || r < 0 || r > 1) && (r = 1), r;
    }
    function j(r, g) {
      yt(r) && (r = "100%");
      var s = oe(r);
      return r = l(g, c(0, parseFloat(r))), s && (r = parseInt(r * g, 10) / 100), t.abs(r - g) < 1e-6 ? 1 : r % g / parseFloat(g);
    }
    function v(r) {
      return l(1, c(0, r));
    }
    function A(r) {
      return parseInt(r, 16);
    }
    function yt(r) {
      return typeof r == "string" && r.indexOf(".") != -1 && parseFloat(r) === 1;
    }
    function oe(r) {
      return typeof r == "string" && r.indexOf("%") != -1;
    }
    function H(r) {
      return r.length == 1 ? "0" + r : "" + r;
    }
    function ot(r) {
      return r <= 1 && (r = r * 100 + "%"), r;
    }
    function lt(r) {
      return t.round(parseFloat(r) * 255).toString(16);
    }
    function It(r) {
      return A(r) / 255;
    }
    var U = function() {
      var r = "[-\\+]?\\d+%?", g = "[-\\+]?\\d*\\.\\d+%?", s = "(?:" + g + ")|(?:" + r + ")", _ = "[\\s|\\(]+(" + s + ")[,|\\s]+(" + s + ")[,|\\s]+(" + s + ")\\s*\\)?", y = "[\\s|\\(]+(" + s + ")[,|\\s]+(" + s + ")[,|\\s]+(" + s + ")[,|\\s]+(" + s + ")\\s*\\)?";
      return {
        CSS_UNIT: new RegExp(s),
        rgb: new RegExp("rgb" + _),
        rgba: new RegExp("rgba" + y),
        hsl: new RegExp("hsl" + _),
        hsla: new RegExp("hsla" + y),
        hsv: new RegExp("hsv" + _),
        hsva: new RegExp("hsva" + y),
        hex3: /^#?([0-9a-fA-F]{1})([0-9a-fA-F]{1})([0-9a-fA-F]{1})$/,
        hex6: /^#?([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/,
        hex4: /^#?([0-9a-fA-F]{1})([0-9a-fA-F]{1})([0-9a-fA-F]{1})([0-9a-fA-F]{1})$/,
        hex8: /^#?([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$/
      };
    }();
    function B(r) {
      return !!U.CSS_UNIT.exec(r);
    }
    function re(r) {
      r = r.replace(n, "").replace(e, "").toLowerCase();
      var g = !1;
      if (mt[r])
        r = mt[r], g = !0;
      else if (r == "transparent")
        return { r: 0, g: 0, b: 0, a: 0, format: "name" };
      var s;
      return (s = U.rgb.exec(r)) ? { r: s[1], g: s[2], b: s[3] } : (s = U.rgba.exec(r)) ? { r: s[1], g: s[2], b: s[3], a: s[4] } : (s = U.hsl.exec(r)) ? { h: s[1], s: s[2], l: s[3] } : (s = U.hsla.exec(r)) ? { h: s[1], s: s[2], l: s[3], a: s[4] } : (s = U.hsv.exec(r)) ? { h: s[1], s: s[2], v: s[3] } : (s = U.hsva.exec(r)) ? { h: s[1], s: s[2], v: s[3], a: s[4] } : (s = U.hex8.exec(r)) ? {
        r: A(s[1]),
        g: A(s[2]),
        b: A(s[3]),
        a: It(s[4]),
        format: g ? "name" : "hex8"
      } : (s = U.hex6.exec(r)) ? {
        r: A(s[1]),
        g: A(s[2]),
        b: A(s[3]),
        format: g ? "name" : "hex"
      } : (s = U.hex4.exec(r)) ? {
        r: A(s[1] + "" + s[1]),
        g: A(s[2] + "" + s[2]),
        b: A(s[3] + "" + s[3]),
        a: It(s[4] + "" + s[4]),
        format: g ? "name" : "hex8"
      } : (s = U.hex3.exec(r)) ? {
        r: A(s[1] + "" + s[1]),
        g: A(s[2] + "" + s[2]),
        b: A(s[3] + "" + s[3]),
        format: g ? "name" : "hex"
      } : !1;
    }
    function se(r) {
      var g, s;
      return r = r || { level: "AA", size: "small" }, g = (r.level || "AA").toUpperCase(), s = (r.size || "small").toLowerCase(), g !== "AA" && g !== "AAA" && (g = "AA"), s !== "small" && s !== "large" && (s = "small"), { level: g, size: s };
    }
    a.exports ? a.exports = u : window.tinycolor = u;
  })(Math);
})(Qt);
var Re = Qt.exports;
const Me = /* @__PURE__ */ Te(Re);
var K = { entries: 0 };
function Rt(a) {
  if (K[a])
    return K[a];
  var t = Me(a), n = {
    rgb: t.toHexString(),
    alpha: t.getAlpha()
  };
  return K.entries += 1, K.entries > 100 && (K = { entries: 0 }), K[a] = n, n;
}
function kt(a) {
  var t;
  const n = {};
  return a.label && (n.label = a.label), a.fillColor && (t = Rt(a.fillColor), n.fillColor = t.rgb, n.fillOpacity = t.alpha), a.lineColor && (t = Rt(a.lineColor), n.strokeColor = t.rgb, n.strokeOpacity = t.alpha), a.lineWidth && (n.strokeWidth = a.lineWidth), n;
}
const _t = girder._;
function Pe(a) {
  return function(t, n) {
    if (("" + n).startsWith("_"))
      return;
    const e = t.type;
    if (t = _t.defaults({}, t, Wt[e] || {}), !_t.has(xt, e))
      return;
    const i = xt[e](t);
    return {
      type: "Feature",
      id: t.id,
      geometry: { type: i.type, coordinates: i.coordinates },
      properties: _t.extend({ element: t, annotationType: i.annotationType }, a, kt(t))
    };
  };
}
function Jt(a, t = {}) {
  return {
    type: "FeatureCollection",
    features: _t.chain(a).mapObject(Pe(t)).compact().value()
  };
}
function $t(a, t) {
  let n = 0, e = 1, i = 0, o = null;
  const l = {
    0: { r: 0, g: 0, b: 0, a: 0 },
    1: { r: 1, g: 1, b: 0, a: 1 }
  };
  if (a.colorRange && a.rangeValues) {
    if (a.normalizeRange || !t.length)
      for (let c = 0; c < a.colorRange.length && c < a.rangeValues.length; c += 1) {
        const d = Math.max(0, Math.min(1, a.rangeValues[c]));
        if (l[d] = a.colorRange[c], d >= 1)
          break;
      }
    else if (a.colorRange.length >= 2 && a.rangeValues.length >= 2) {
      n = e = a.rangeValues[0] || 0;
      for (let c = 1; c < a.rangeValues.length; c += 1) {
        const d = a.rangeValues[c] || 0;
        d < n && (n = d), d > e && (e = d);
      }
      n === e && (n -= 1), i = void 0;
      for (let c = 0; c < a.colorRange.length && c < a.rangeValues.length; c += 1) {
        let d = (a.rangeValues[c] - n) / (e - n || 1);
        if ((d <= 0 || i === void 0) && (i = a.rangeValues[c]), o = a.rangeValues[c], d = Math.max(0, Math.min(1, d)), l[d] = a.colorRange[c], d >= 1)
          break;
      }
    }
  }
  return {
    color: l,
    min: i,
    max: o
  };
}
function ze(a, t, n) {
  const e = n.map(), i = e.layers().find((u) => u instanceof window.geo.tileLayer && u.options && u.options.maxLevel !== void 0), o = i ? 2 ** -i.options.maxLevel : 1, l = e.createLayer("feature", { features: ["heatmap"] }), c = $t(a, a.points.map((u) => u[3])), d = l.createFeature("heatmap", {
    style: {
      radius: (a.radius || 25) * (a.scaleWithZoom ? o : 1),
      blurRadius: 0,
      gaussian: !0,
      color: c.color,
      scaleWithZoom: a.scaleWithZoom || !1
    },
    position: (u) => ({ x: u[0], y: u[1], z: u[2] }),
    intensity: (u) => u[3] || 0,
    minIntensity: c.min,
    maxIntensity: c.max,
    updateDelay: 100
  }).data(a.points);
  return d._ownLayer = !0, [d];
}
function De(a, t, n) {
  const e = n.map(), i = e.createLayer("feature", { features: ["heatmap"] }), o = (a.origin || [0, 0, 0])[0] || 0, l = (a.origin || [0, 0, 0])[1] || 0, c = (a.origin || [0, 0, 0])[2] || 0, d = a.dx || 1, u = a.dy || 1, h = $t(a, a.values), F = e.layers().find((w) => w instanceof window.geo.tileLayer && w.options && w.options.maxLevel !== void 0), f = F ? 2 ** -F.options.maxLevel : 1, b = i.createFeature("heatmap", {
    style: {
      radius: (a.radius || 25) * (a.scaleWithZoom ? f : 1),
      blurRadius: 0,
      gaussian: !0,
      color: h.color,
      scaleWithZoom: a.scaleWithZoom || !1
    },
    position: (w, L) => ({
      x: o + d * (L % a.gridWidth),
      y: l + u * Math.floor(L / a.gridWidth),
      z: c
    }),
    intensity: (w) => w || 0,
    minIntensity: h.min,
    maxIntensity: h.max,
    updateDelay: 100
  }).data(a.values);
  return b._ownLayer = !0, [b];
}
function He(a, t, n) {
  let e = a.values[0] || 0, i = e;
  for (let l = 1; l < a.values.length; l += 1)
    a.values[l] > i && (i = a.values[l]), a.values[l] < i && (e = a.values[l]);
  return e >= 0 && (e = -1), [n.createFeature("contour", {
    style: {
      value: (l) => l || 0
    },
    contour: {
      gridWidth: a.gridWidth,
      x0: (a.origin || [])[0] || 0,
      y0: (a.origin || [])[1] || 0,
      dx: a.dx || 1,
      dy: a.dy || 1,
      stepped: !1,
      colorRange: [
        a.minColor || { r: 0, g: 0, b: 1, a: 1 },
        a.zeroColor || { r: 0, g: 0, b: 0, a: 0 },
        a.maxColor || { r: 1, g: 1, b: 0, a: 1 }
      ],
      rangeValues: [e, 0, Math.max(0, i)]
    }
  }).data(a.values)];
}
const Mt = {
  griddata_contour: He,
  griddata_heatmap: De,
  heatmap: ze
};
function Zt(a, t = {}, n) {
  try {
    var e = [];
    return a.forEach((i) => {
      const o = Mt[i.type + "_" + i.interpretation] || Mt[i.type];
      o && (e = e.concat(o(i, t, n)));
    }), e;
  } catch (i) {
    console.error(i);
  }
}
const Ue = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  convertFeatures: Zt,
  heatmapColorTable: $t
}, Symbol.toStringTag, { value: "Module" })), et = girder._, Ve = girder.models.AccessControlledModel, { getCurrentUser: X } = girder.auth, { restRequest: gt } = girder.rest, Ne = girder.models.MetadataMixin, wt = {
  default: {
    fillColor: { r: 1, g: 120 / 255, b: 0 },
    fillOpacity: 0.8,
    strokeColor: { r: 0, g: 0, b: 0 },
    strokeOpacity: 1,
    strokeWidth: 1
  },
  rectangle: {
    fillColor: { r: 176 / 255, g: 222 / 255, b: 92 / 255 },
    strokeColor: { r: 153 / 255, g: 153 / 255, b: 153 / 255 },
    strokeWidth: 2
  },
  ellipse: {
    fillColor: { r: 176 / 255, g: 222 / 255, b: 92 / 255 },
    strokeColor: { r: 153 / 255, g: 153 / 255, b: 153 / 255 },
    strokeWidth: 2
  },
  circle: {
    fillColor: { r: 176 / 255, g: 222 / 255, b: 92 / 255 },
    strokeColor: { r: 153 / 255, g: 153 / 255, b: 153 / 255 },
    strokeWidth: 2
  },
  polyline: {
    strokeColor: { r: 1, g: 120 / 255, b: 0 },
    strokeOpacity: 0.5,
    strokeWidth: 4
  },
  polyline_closed: {
    fillColor: { r: 176 / 255, g: 222 / 255, b: 92 / 255 },
    strokeColor: { r: 153 / 255, g: 153 / 255, b: 153 / 255 },
    strokeWidth: 2
  }
};
function Pt(a) {
  Object.assign(a, kt(a));
  const t = a.type + (a.closed ? "_closed" : "");
  ["fillColor", "strokeColor", "strokeWidth", "fillOpacity", "strokeOpacity"].forEach((n) => {
    a[n] === void 0 && (a[n] = (wt[t] || wt.default)[n]), a[n] === void 0 && (a[n] = wt.default[n]);
  });
}
const st = Ve.extend({
  resourceName: "annotation",
  defaults: {
    annotation: {},
    minElements: 5e3,
    maxDetails: 5e5,
    maxCentroids: 5e6
  },
  initialize() {
    !this.get("updated") && X() && (this.attributes.updated = "" + Date.now(), this.attributes.updatedId = X().id), this._region = {
      maxDetails: this.get("maxDetails"),
      minElements: this.get("minElements"),
      sort: "size",
      sortdir: -1
    }, this._viewArea = 3, this._elements = new Gt(
      this.get("annotation").elements || []
    ), this._elements.annotation = this, this.listenTo(this._elements, "change add remove reset", () => {
      var a = et.extend({}, this.get("annotation"));
      a.elements = this._elements.toJSON(), this.set("annotation", a);
    }), this.listenTo(this._elements, "change add", this.handleElementChanged), this.listenTo(this._elements, "remove", this.handleElementRemoved);
  },
  handleElementChanged: function(a, t, n) {
    if (!this._centroids)
      return;
    const e = {
      type: a.get("type"),
      fillColor: a.get("fillColor"),
      lineColor: a.get("lineColor"),
      lineWidth: a.get("lineWidth"),
      closed: a.get("closed")
    };
    let i;
    for (i = 0; i < this._centroids.props.length; i += 1) {
      const h = this._centroids.props[i];
      if (h.type === e.type && h.fillColor === e.fillColor && h.lineColor === e.lineColor && h.lineWidth === e.lineWidth && h.closed === e.closed)
        break;
    }
    i === this._centroids.props.length && (Pt(e), this._centroids.props.push(e));
    const o = a.id;
    let l;
    for (l = 0; l < this._centroids.centroids.id.length && this._centroids.centroids.id[l] !== o; l += 1)
      ;
    let c, d, u = 1;
    if (a.get("center"))
      c = a.get("center")[0], d = a.get("center")[0], a.get("radius") ? u = a.get("radius") : a.get("width") && (u = Math.max(1, (a.get("width") ** 2 + a.get("height") ** 2) ** 0.5 / 2));
    else if (a.get("points")) {
      const h = a.get("points");
      let F = h[0][0], f = h[0][0], b = h[0][1], w = h[0][1];
      for (const [L, R] of h)
        F = Math.min(F, L), b = Math.min(b, R), f = Math.max(f, L), w = Math.max(w, R);
      c = (f + F) / 2, d = (w + b) / 2, u = Math.max(1, ((f - F) ** 2 + (w - b) ** 2) ** 0.5);
    }
    if (l === this._centroids.centroids.id.length) {
      this._centroids.centroids.id.push(o);
      const h = new Float32Array(l + 1);
      h.set(this._centroids.centroids.x), h[l] = c, this._centroids.centroids.x = h;
      const F = new Float32Array(l + 1);
      F.set(this._centroids.centroids.y), F[l] = d, this._centroids.centroids.y = F;
      const f = new Float32Array(l + 1);
      f.set(this._centroids.centroids.r), f[l] = u, this._centroids.centroids.r = f;
      const b = new Uint32Array(l + 1);
      b.set(this._centroids.centroids.s), b[l] = i, this._centroids.centroids.s = b;
    } else
      this._centroids.centroids.x[l] = c, this._centroids.centroids.y[l] = d, this._centroids.centroids.r[l] = u, this._centroids.centroids.s[l] = i;
    this._centroids._redraw = !0, this._centroids.data = { length: this._centroids.centroids.id.length };
  },
  handleElementRemoved: function(a, t, n) {
    if (!this._centroids)
      return;
    const e = a.id;
    for (let i = 0; i < this._centroids.centroids.id.length; i += 1)
      if (this._centroids.centroids.id[i] === e) {
        this._shownIds && this._shownIds.add(e);
        const o = this._centroids.centroids.id.length - 1;
        this._centroids.centroids.id[i] = this._centroids.centroids.id[o], this._centroids.centroids.x[i] = this._centroids.centroids.x[o], this._centroids.centroids.y[i] = this._centroids.centroids.y[o], this._centroids.centroids.r[i] = this._centroids.centroids.r[o], this._centroids.centroids.s[i] = this._centroids.centroids.s[o], this._centroids.centroids.id.splice(o, 1), this._centroids.data = { length: this._centroids.centroids.id.length }, this._centroids._redraw = !0;
        break;
      }
  },
  /**
   * Fetch the centroids and unpack the binary data.
   */
  fetchCentroids: function() {
    var a = (this.altUrl || this.resourceName) + "/" + this.get("_id"), t = {
      url: a,
      data: {
        centroids: !0,
        _: (this.get("updated") || this.get("created")) + "_" + this.get("_version")
      },
      xhrFields: {
        responseType: "arraybuffer"
      },
      error: null
    };
    return (this.get("_elementQuery") || {}).count && (this.get("_elementQuery") || {}).count > this.get("maxCentroids") && (t.data.sort = "size", t.data.sortdir = -1, t.data.limit = this.get("maxCentroids")), gt(t).done((n) => {
      let e = new DataView(n), i = 0, o = e.byteLength - 1;
      for (; e.getUint8(i) && i < e.byteLength; i += 1) ;
      for (; e.getUint8(o) && o >= 0; o -= 1) ;
      if (i >= o)
        throw new Error("invalid centroid data");
      const l = new Uint8Array(i + e.byteLength - o - 1);
      l.set(new Uint8Array(n.slice(0, i)), 0), l.set(new Uint8Array(n.slice(o + 1)), i);
      const c = JSON.parse(decodeURIComponent(escape(String.fromCharCode.apply(null, l))));
      if (c.props = c._elementQuery.props.map((F) => {
        const f = {};
        return c._elementQuery.propskeys.forEach((b, w) => {
          f[b] = F[w];
        }), Pt(f), f;
      }), e = new DataView(n, i + 1, o - i - 1), e.byteLength !== c._elementQuery.returned * 28)
        throw new Error("invalid centroid data size");
      const d = {
        id: new Array(c._elementQuery.returned),
        x: new Float32Array(c._elementQuery.returned),
        y: new Float32Array(c._elementQuery.returned),
        r: new Float32Array(c._elementQuery.returned),
        s: new Uint32Array(c._elementQuery.returned)
      };
      let u, h;
      for (u = h = 0; h < e.byteLength; u += 1, h += 28)
        d.id[u] = ("0000000" + e.getUint32(h, !1).toString(16)).substr(-8) + ("0000000" + e.getUint32(h + 4, !1).toString(16)).substr(-8) + ("0000000" + e.getUint32(h + 8, !1).toString(16)).substr(-8), d.x[u] = e.getFloat32(h + 12, !0), d.y[u] = e.getFloat32(h + 16, !0), d.r[u] = e.getFloat32(h + 20, !0), d.s[u] = e.getUint32(h + 24, !0);
      return c.centroids = d, c.data = { length: c._elementQuery.returned }, c._elementQuery.count > c._elementQuery.returned && (c.partial = !0), this._centroids = c, c;
    });
  },
  fetchCentroidsWrapper: function(a) {
    return this._inFetch = "centroids", this.fetchCentroids().then(() => (this._inFetch = !0, a.extraPath ? this.trigger("g:fetched." + a.extraPath) : this.trigger("g:fetched"), null)).always(() => {
      if (this._inFetch = !1, this._nextFetch) {
        var t = this._nextFetch;
        this._nextFetch = null, t();
      }
      return null;
    });
  },
  /**
   * Fetch a single resource from the server. Triggers g:fetched on success,
   * or g:error on error.
   * To ignore the default error handler, pass
   *     ignoreError: true
   * in your opts object.
   */
  fetch: function(a) {
    if (this.altUrl === null && this.resourceName === null) {
      console.error("Error: You must set an altUrl or a resourceName on your model.");
      return;
    }
    a = a || {};
    var t = X(), n = {
      url: (this.altUrl || this.resourceName) + "/" + this.get("_id"),
      /* Add our region request into the query */
      data: Object.assign({}, this._region, { _: (this.get("updated") || this.get("created")) + (t && t.id ? "_" + t.id : "") + "_" + this.get("_version") })
    };
    return a.extraPath && (n.url += "/" + a.extraPath), a.ignoreError && (n.error = null), this._pageElements === void 0 && (this.get("_elementCount") || 0) > this.get("minElements") && (this.get("_detailsCount") || 0) > this.get("maxDetails") ? (this._pageElements = !0, this.fetchCentroidsWrapper(a)) : (this._inFetch = !0, this._refresh && (delete this._pageElements, delete this._centroids, this._refresh = !1), gt(n).always(() => {
      if (this._inFetch !== "centroids" && (this._inFetch = !1, this._nextFetch)) {
        var e = this._nextFetch;
        this._nextFetch = null, this._pageElements !== !1 && e();
      }
    }).done((e) => {
      const o = (e.annotation || {}).elements || [];
      this._fromFetch = !0, this.set(e), this._fromFetch = null, this._pageElements === void 0 && e._elementQuery && (this._pageElements = e._elementQuery.count > e._elementQuery.returned, this._pageElements ? this.fetchCentroidsWrapper(a) : this._nextFetch = null), this._inFetch !== "centroids" && (a.extraPath ? this.trigger("g:fetched." + a.extraPath) : this.trigger("g:fetched")), this._fromFetch = !0, this._elements.reset(o, et.extend({ sync: !0 }, a)), this._fromFetch = null;
    }).fail((e) => {
      this.trigger("g:error", e);
    }));
  },
  /**
   * Get/set for a refresh flag.
   *
   * @param {boolean} [val] If specified, set the refresh flag.  If not
   *    specified, return the refresh flag.
   * @returns {boolean|this}
   */
  refresh(a) {
    return a === void 0 ? self._refresh : (self._refresh = a, this);
  },
  /**
   * Perform a PUT or POST request on the annotation data depending
   * on whether the annotation is new or not.  This mirrors somewhat
   * the api of `Backbone.Model.save`.  For new models, the `itemId`
   * attribute is required.
   */
  save(a) {
    let t, n;
    const e = this.isNew();
    if (e && this._changeLog && delete this._changeLog, e) {
      if (!this.get("itemId"))
        throw new Error("itemId is required to save new annotations");
      t = `annotation?itemId=${this.get("itemId")}`, n = "POST";
    } else
      t = `annotation/${this.id}`, n = "PUT", X() && (this.attributes.updated = (/* @__PURE__ */ new Date()).toISOString(), this.attributes.updatedId = X().id);
    let i;
    if (this._changeLog) {
      n = "PATCH";
      const o = this.get("annotation");
      i = Object.values(this._changeLog), i.forEach((l) => {
        l.value && l.value.label && !l.value.label.value && delete l.value.label;
      }), Object.keys(o).forEach((l) => {
        l !== "elements" && i.push({ op: "replace", path: l, value: o[l] });
      }), delete this._changeLog;
    } else
      i = et.extend({}, this.get("annotation")), this._pageElements === !1 || e ? (this._pageElements = !1, i.elements = et.map(i.elements, (o) => (o = et.extend({}, o), o.label && !o.label.value && delete o.label, o))) : (delete i.elements, this._pageElements);
    return this._inSave = !0, gt({
      url: t,
      method: n,
      contentType: "application/json",
      processData: !1,
      data: JSON.stringify(i)
    }).done((o) => {
      if (this._inSave = !1, e && (o.elements = (this.get("annotation") || {}).elements || [], this.set(o)), this.trigger("sync", this, o, a), this._nextFetch && !this._inFetch && (this._saveAgain === void 0 || this._saveAgain === !1)) {
        var l = this._nextFetch;
        this._nextFetch = null, l();
      }
    });
  },
  /**
   * Perform a DELETE request on the annotation model and remove all
   * event listeners.  This mirrors the api of `Backbone.Model.destroy`
   * without the backbone specific options, which are not supported by
   * girder's base model either.
   */
  destroy(a) {
    return this.stopListening(), this.trigger("destroy", this, this.collection, a), this.delete(a);
  },
  name() {
    return (this.get("annotation") || {}).name;
  },
  /**
   * Perform a DELETE request on the annotation model and reset the id
   * attribute, but don't remove event listeners.
   */
  delete(a) {
    this.trigger("g:delete", this, this.collection, a);
    let t = !1;
    return this.isNew() || (X() && (this.attributes.updated = "" + Date.now(), this.attributes.updatedId = X().id), t = gt({
      url: `annotation/${this.id}`,
      method: "DELETE"
    })), this.unset("_id"), t;
  },
  /**
   * Return the annotation as a geojson FeatureCollection.
   *
   * WARNING: Not all annotations are representable in geojson.
   * Annotation types that cannot be converted will be ignored.
   */
  geojson() {
    const t = (this.get("annotation") || {}).elements || [];
    return Jt(t, { annotation: this.id });
  },
  /**
   * Return annotations that cannot be represented as geojson as geojs
   * features specifications.
   *
   * @param webglLayer: the parent feature layer.
   */
  non_geojson(a) {
    const n = (this.get("annotation") || {}).elements || [];
    return Zt(n, { annotation: this.id }, a);
  },
  /**
   * Return annotation elements that cannot be represented as geojs
   * features, such as image overlays.
   */
  overlays() {
    const a = ["image", "pixelmap"];
    return ((this.get("annotation") || {}).elements || []).filter((e) => a.includes(e.type));
  },
  /**
   * Set the view.  If we are paging elements, possibly refetch the elements.
   * Callers should listen for the g:fetched event to know when new elements
   * have been fetched.
   *
   * @param {object} bounds the corners of the visible region.  This is an
   *      object with left, top, right, bottom in pixels.
   * @param {number} zoom the zoom factor.
   * @param {number} maxZoom the maximum zoom factor.
   * @param {boolean} noFetch Truthy to not perform a fetch if the view
   *  changes.
   * @param {number} sizeX the maximum width to query.
   * @param {number} sizeY the maximum height to query.
   */
  setView(a, t, n, e, i, o) {
    if (!(this._pageElements === !1 || this.isNew())) {
      var l = a.right - a.left, c = a.bottom - a.top, d = l * (this._viewArea - 1) / 2, u = c * (this._viewArea - 1) / 2, h = d / 2, F = u / 2, f = this._region.left !== void 0 && a.left >= this._region.left + h && a.top >= this._region.top + F && a.right <= this._region.right - h && a.bottom <= this._region.bottom - F && Math.abs(this._lastZoom - t) < 1;
      if (!(f && !this._inFetch)) {
        if (this._pageElements || this._region.left !== void 0) {
          var b = Object.assign({}, this._region);
          if (this._region.left = Math.max(0, a.left - d), this._region.top = Math.max(0, a.top - u), this._region.right = Math.min(i || 1e6, a.right + d), this._region.bottom = Math.min(o || 1e6, a.bottom + u), this._region.maxDetails = t + 1 < n ? this.get("maxDetails") : void 0, this._lastZoom = t, ["left", "top", "right", "bottom", "maxDetails"].every((L) => this._region[L] === b[L]))
            return;
        }
        if (!e && !this._nextFetch) {
          var w = () => {
            this.fetch();
          };
          this._inFetch || this._inSave ? this._nextFetch = w : w();
        }
      }
    }
  },
  /**
   * Return a backbone collection containing the annotation elements.
   */
  elements() {
    return this._elements;
  }
});
et.extend(st.prototype, Ne);
const Be = girder.collections.Collection, { SORT_DESC: qe } = girder.constants, Yt = Be.extend({
  resourceName: "annotation",
  model: st,
  // this is a large number so that we probably never need to page
  // annotations.
  pageLimit: 1e4,
  sortField: "created",
  sortDir: qe
});
function T(a, t, n, e) {
  if (t === !1 || t == null || !t && (a === "class" || a === "style")) return "";
  if (t === !0) return " " + (a + '="' + a + '"');
  var i = typeof t;
  return i !== "object" && i !== "function" || typeof t.toJSON != "function" || (t = t.toJSON()), typeof t == "string" || (t = JSON.stringify(t), n || t.indexOf('"') === -1) ? (n && (t = $(t)), " " + a + '="' + t + '"') : " " + a + "='" + t.replace(/'/g, "&#39;") + "'";
}
function ft(a, t) {
  return Array.isArray(a) ? Ge(a, t) : a && typeof a == "object" ? Qe(a) : a || "";
}
function Ge(a, t) {
  for (var n, e = "", i = "", o = Array.isArray(t), l = 0; l < a.length; l++) (n = ft(a[l])) && (o && t[l] && (n = $(n)), e = e + i + n, i = " ");
  return e;
}
function Qe(a) {
  var t = "", n = "";
  for (var e in a) e && a[e] && Je.call(a, e) && (t = t + n + e, n = " ");
  return t;
}
function $(a) {
  var t = "" + a, n = Ze.exec(t);
  if (!n) return a;
  var e, i, o, l = "";
  for (e = n.index, i = 0; e < t.length; e++) {
    switch (t.charCodeAt(e)) {
      case 34:
        o = "&quot;";
        break;
      case 38:
        o = "&amp;";
        break;
      case 60:
        o = "&lt;";
        break;
      case 62:
        o = "&gt;";
        break;
      default:
        continue;
    }
    i !== e && (l += t.substring(i, e)), i = e + 1, l += o;
  }
  return i !== e ? l + t.substring(i, e) : l;
}
var Je = Object.prototype.hasOwnProperty, Ze = /["&<>]/;
function Xt(a, t, n, e) {
  if (!(a instanceof Error)) throw a;
  if (!(typeof window > "u" && t || e)) throw a.message += " on line " + n, a;
  var i, o, l, c;
  try {
    e = e || require("fs").readFileSync(t, { encoding: "utf8" }), i = 3, o = e.split(`
`), l = Math.max(n - i, 0), c = Math.min(o.length, n + i);
  } catch (d) {
    return a.message += " - could not read from " + t + " (" + d.message + ")", void Xt(a, null, n);
  }
  i = o.slice(l, c).map(function(d, u) {
    var h = u + l + 1;
    return (h == n ? "  > " : "    ") + h + "| " + d;
  }).join(`
`), a.path = t;
  try {
    a.message = (t || "Pug") + ":" + n + `
` + i + `

` + a.message;
  } catch {
  }
  throw a;
}
function Ye(a) {
  var t = "", n, e, i;
  try {
    var o = a || {};
    (function(l, c, d, u, h, F, f, b, w, L) {
      if (i = 1, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<div class="g-annotation-list-header">', i = 2, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-pencil"></i>', i = 3, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + " Annotations", i = 4, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<div class="btn-group pull-right">', i = 5, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", b && (i = 6, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<a class="g-annotation-upload" title="Upload annotation">', i = 7, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-upload"></i></a>'), t = t + "</div></div>", i = 9, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", u.length) {
        i = 10, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<table class="g-annotation-list table table-hover table-condensed">', i = 11, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<thead>", i = 12, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<th class="g-annotation-select">', i = 13, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<input class="pr-2" id="select-all" type="checkbox" title="Select all annotations for bulk actions"/></th>', i = 14, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<th class="g-annotation-toggle">', i = 15, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<a" + (T("class", ft(["g-annotation-toggle-all", F ? "disabled" : ""], [!1, !0]), !1, !1) + ' title="Hide or show all annotations"') + ">", i = 16, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug";
        let R = u.models.some((S) => w.has(S.id));
        i = 17, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", R ? (i = 18, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-eye"></i>') : (i = 20, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-eye-off"></i>'), t = t + "</a></th>", i = 21, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", (function() {
          var S = f.columns || [];
          if (typeof S.length == "number")
            for (var W = 0, M = S.length; W < M; W++) {
              var m = S[W];
              i = 22, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", (m.type !== "record" || m.value !== "controls") && (i = 23, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<th class="g-annotation-column">', i = 24, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", m.title !== void 0 ? (i = 25, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = m.title) == null ? "" : n)) : (i = 27, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = `${m.value.substr(0, 1).toUpperCase()}${m.value.substr(1)}`) == null ? "" : n)), t = t + "</th>");
            }
          else {
            var M = 0;
            for (var W in S) {
              M++;
              var m = S[W];
              i = 22, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", (m.type !== "record" || m.value !== "controls") && (i = 23, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<th class="g-annotation-column">', i = 24, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", m.title !== void 0 ? (i = 25, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = m.title) == null ? "" : n)) : (i = 27, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = `${m.value.substr(0, 1).toUpperCase()}${m.value.substr(1)}`) == null ? "" : n)), t = t + "</th>");
            }
          }
        }).call(this), i = 28, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<th class="g-annotation-actions">', i = 29, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", u.length && (i = 30, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<a class="g-annotation-download-selected" title="Download selected annotations">', i = 31, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-download"></i></a>'), i = 32, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", d >= l.ADMIN && u.length && (i = 33, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<a class="g-annotation-permissions" title="Adjust permissions">', i = 34, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-lock"></i></a>', i = 35, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<a class="g-annotation-delete" title="Delete">', i = 36, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-cancel"></i></a>'), t = t + "</th></thead>", i = 37, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<tbody>", i = 38, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", (function() {
          var S = u.models;
          if (typeof S.length == "number")
            for (var W = 0, M = S.length; W < M; W++) {
              var m = S[W];
              i = 39, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug";
              var it = m.get("annotation").name, q = L.get(m.get("creatorId")), D = q ? q.get("login") : m.get("creatorId"), G = L.get(m.get("updatedId")), Q = G ? G.get("login") : m.get("updatedId");
              i = 45, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<tr" + (' class="g-annotation-row"' + T("data-annotation-id", m.id, !0, !1)) + ">", i = 46, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<td class="g-annotation-select">', i = 47, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<input type="checkbox" title="Select annotation for bulk actions"/></td>', i = 48, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<td class="g-annotation-toggle">', i = 49, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<a" + (T("class", ft(["g-annotation-toggle-select", F ? "disabled" : ""], [!1, !0]), !1, !1) + ' title="Show annotation"') + ">", i = 50, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", w.has(m.id) ? (i = 51, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-eye"></i>') : (i = 53, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-eye-off"></i>'), t = t + "</a></td>", i = 54, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", (function() {
                var J = f.columns || [];
                if (typeof J.length == "number")
                  for (var Z = 0, at = J.length; Z < at; Z++) {
                    var C = J[Z];
                    if (i = 55, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", C.type !== "record" || C.value !== "controls") {
                      i = 56, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug";
                      var E;
                      C.type === "record" && C.value === "creator" ? E = D : C.type === "record" && C.value === "updatedId" ? E = Q || D : C.type === "record" && C.value === "updated" ? E = m.get("updated") || m.get("created") : C.type === "metadata" ? (E = m.get("annotation").attributes || {}, C.value.split(".").forEach((Ft) => {
                        E = (E || {})[Ft];
                      })) : E = C.type === "record" ? m.get(C.value) || m.get("annotation")[C.value] : "", i = 72, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<td" + (' class="g-annotation-entry"' + T("title", E, !0, !1)) + ">", i = 73, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", C.format === "user" ? (i = 74, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<a" + T("href", `#user/${m.get(C.value) || m.get(C.value + "Id")}`, !0, !1) + ">", i = 75, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = E) == null ? "" : n) + "</a>") : C.format === "datetime" ? (i = 77, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(E).toLocaleString()) == null ? "" : n)) : C.format === "date" ? (i = 79, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(E).toLocaleDateString()) == null ? "" : n)) : C.format === "time" ? (i = 81, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(E).toLocaleTimeString()) == null ? "" : n)) : (i = 83, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = E) == null ? "" : n)), t = t + "</td>";
                    }
                  }
                else {
                  var at = 0;
                  for (var Z in J) {
                    at++;
                    var C = J[Z];
                    if (i = 55, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", C.type !== "record" || C.value !== "controls") {
                      i = 56, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug";
                      var E;
                      C.type === "record" && C.value === "creator" ? E = D : C.type === "record" && C.value === "updatedId" ? E = Q || D : C.type === "record" && C.value === "updated" ? E = m.get("updated") || m.get("created") : C.type === "metadata" ? (E = m.get("annotation").attributes || {}, C.value.split(".").forEach((N) => {
                        E = (E || {})[N];
                      })) : E = C.type === "record" ? m.get(C.value) || m.get("annotation")[C.value] : "", i = 72, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<td" + (' class="g-annotation-entry"' + T("title", E, !0, !1)) + ">", i = 73, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", C.format === "user" ? (i = 74, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<a" + T("href", `#user/${m.get(C.value) || m.get(C.value + "Id")}`, !0, !1) + ">", i = 75, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = E) == null ? "" : n) + "</a>") : C.format === "datetime" ? (i = 77, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(E).toLocaleString()) == null ? "" : n)) : C.format === "date" ? (i = 79, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(E).toLocaleDateString()) == null ? "" : n)) : C.format === "time" ? (i = 81, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(E).toLocaleTimeString()) == null ? "" : n)) : (i = 83, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = E) == null ? "" : n)), t = t + "</td>";
                    }
                  }
                }
              }).call(this), i = 84, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<td class="g-annotation-actions">', i = 85, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<!--", i = 86, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "if annotation.get('_accessLevel') >= AccessType.WRITE", i = 87, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + `
`, i = 87, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "  a.g-annotation-edit(title='Edit annotation')", i = 88, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + `
`, i = 88, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "    i.icon-cog-->", i = 89, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<a" + (' class="g-annotation-download"' + T("href", `${h}/annotation/${m.id}`, !0, !1) + ' title="Download"' + T("download", `${it}.json`, !0, !1)) + ">", i = 90, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-download"></i></a>', i = 91, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", m.get("_accessLevel") >= l.ADMIN && (i = 92, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<a class="g-annotation-permissions" title="Adjust permissions">', i = 93, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-lock"></i></a>'), i = 94, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", m.get("_accessLevel") >= l.WRITE && (i = 95, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<a class="g-annotation-delete" title="Delete">', i = 96, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-cancel"></i></a>'), t = t + "</td></tr>";
            }
          else {
            var M = 0;
            for (var W in S) {
              M++;
              var m = S[W];
              i = 39, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug";
              var it = m.get("annotation").name, q = L.get(m.get("creatorId")), D = q ? q.get("login") : m.get("creatorId"), G = L.get(m.get("updatedId")), Q = G ? G.get("login") : m.get("updatedId");
              i = 45, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<tr" + (' class="g-annotation-row"' + T("data-annotation-id", m.id, !0, !1)) + ">", i = 46, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<td class="g-annotation-select">', i = 47, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<input type="checkbox" title="Select annotation for bulk actions"/></td>', i = 48, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<td class="g-annotation-toggle">', i = 49, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<a" + (T("class", ft(["g-annotation-toggle-select", F ? "disabled" : ""], [!1, !0]), !1, !1) + ' title="Show annotation"') + ">", i = 50, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", w.has(m.id) ? (i = 51, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-eye"></i>') : (i = 53, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-eye-off"></i>'), t = t + "</a></td>", i = 54, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", (function() {
                var Y = f.columns || [];
                if (typeof Y.length == "number")
                  for (var N = 0, j = Y.length; N < j; N++) {
                    var v = Y[N];
                    if (i = 55, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", v.type !== "record" || v.value !== "controls") {
                      i = 56, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug";
                      var A;
                      v.type === "record" && v.value === "creator" ? A = D : v.type === "record" && v.value === "updatedId" ? A = Q || D : v.type === "record" && v.value === "updated" ? A = m.get("updated") || m.get("created") : v.type === "metadata" ? (A = m.get("annotation").attributes || {}, v.value.split(".").forEach((yt) => {
                        A = (A || {})[yt];
                      })) : A = v.type === "record" ? m.get(v.value) || m.get("annotation")[v.value] : "", i = 72, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<td" + (' class="g-annotation-entry"' + T("title", A, !0, !1)) + ">", i = 73, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", v.format === "user" ? (i = 74, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<a" + T("href", `#user/${m.get(v.value) || m.get(v.value + "Id")}`, !0, !1) + ">", i = 75, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = A) == null ? "" : n) + "</a>") : v.format === "datetime" ? (i = 77, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(A).toLocaleString()) == null ? "" : n)) : v.format === "date" ? (i = 79, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(A).toLocaleDateString()) == null ? "" : n)) : v.format === "time" ? (i = 81, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(A).toLocaleTimeString()) == null ? "" : n)) : (i = 83, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = A) == null ? "" : n)), t = t + "</td>";
                    }
                  }
                else {
                  var j = 0;
                  for (var N in Y) {
                    j++;
                    var v = Y[N];
                    if (i = 55, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", v.type !== "record" || v.value !== "controls") {
                      i = 56, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug";
                      var A;
                      v.type === "record" && v.value === "creator" ? A = D : v.type === "record" && v.value === "updatedId" ? A = Q || D : v.type === "record" && v.value === "updated" ? A = m.get("updated") || m.get("created") : v.type === "metadata" ? (A = m.get("annotation").attributes || {}, v.value.split(".").forEach((lt) => {
                        A = (A || {})[lt];
                      })) : A = v.type === "record" ? m.get(v.value) || m.get("annotation")[v.value] : "", i = 72, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<td" + (' class="g-annotation-entry"' + T("title", A, !0, !1)) + ">", i = 73, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", v.format === "user" ? (i = 74, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<a" + T("href", `#user/${m.get(v.value) || m.get(v.value + "Id")}`, !0, !1) + ">", i = 75, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = A) == null ? "" : n) + "</a>") : v.format === "datetime" ? (i = 77, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(A).toLocaleString()) == null ? "" : n)) : v.format === "date" ? (i = 79, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(A).toLocaleDateString()) == null ? "" : n)) : v.format === "time" ? (i = 81, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = new c(A).toLocaleTimeString()) == null ? "" : n)) : (i = 83, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + $((n = A) == null ? "" : n)), t = t + "</td>";
                    }
                  }
                }
              }).call(this), i = 84, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<td class="g-annotation-actions">', i = 85, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<!--", i = 86, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "if annotation.get('_accessLevel') >= AccessType.WRITE", i = 87, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + `
`, i = 87, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "  a.g-annotation-edit(title='Edit annotation')", i = 88, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + `
`, i = 88, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "    i.icon-cog-->", i = 89, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + "<a" + (' class="g-annotation-download"' + T("href", `${h}/annotation/${m.id}`, !0, !1) + ' title="Download"' + T("download", `${it}.json`, !0, !1)) + ">", i = 90, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-download"></i></a>', i = 91, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", m.get("_accessLevel") >= l.ADMIN && (i = 92, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<a class="g-annotation-permissions" title="Adjust permissions">', i = 93, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-lock"></i></a>'), i = 94, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", m.get("_accessLevel") >= l.WRITE && (i = 95, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<a class="g-annotation-delete" title="Delete">', i = 96, e = "/root/project/girder_annotation/girder_large_image_annotation/web_client/templates/annotationListWidget.pug", t = t + '<i class="icon-cancel"></i></a>'), t = t + "</td></tr>";
            }
          }
        }).call(this), t = t + "</tbody></table>";
      }
    }).call(this, "AccessType" in o ? o.AccessType : typeof AccessType < "u" ? AccessType : void 0, "Date" in o ? o.Date : typeof Date < "u" ? Date : void 0, "accessLevel" in o ? o.accessLevel : typeof accessLevel < "u" ? accessLevel : void 0, "annotations" in o ? o.annotations : typeof annotations < "u" ? annotations : void 0, "apiRoot" in o ? o.apiRoot : typeof apiRoot < "u" ? apiRoot : void 0, "canDraw" in o ? o.canDraw : typeof canDraw < "u" ? canDraw : void 0, "confList" in o ? o.confList : typeof confList < "u" ? confList : void 0, "creationAccess" in o ? o.creationAccess : typeof creationAccess < "u" ? creationAccess : void 0, "drawn" in o ? o.drawn : typeof drawn < "u" ? drawn : void 0, "users" in o ? o.users : typeof users < "u" ? users : void 0);
  } catch (l) {
    Xt(l, e, i);
  }
  return t;
}
const z = girder.$, ct = girder._, { AccessType: Xe } = girder.constants, zt = girder.utilities.EventStream, { getCurrentUser: Ke } = girder.auth, { confirm: Dt } = girder.dialog, { getApiRoot: vt, restRequest: tn } = girder.rest, en = girder.views.widgets.AccessWidget, nn = girder.events, an = girder.collections.UserCollection, on = girder.views.widgets.UploadWidget, rn = girder.views.View, sn = rn.extend({
  events: {
    "click .g-annotation-toggle-select": "_displayAnnotation",
    "click .g-annotation-toggle-all": "_displayAllAnnotations",
    "click .g-annotation-select": "_selectAnnotation",
    "click .g-annotation-download-selected": "_downloadSelectedAnnotations",
    "click .g-annotation-delete": "_deleteAnnotation",
    "click .g-annotation-upload": "_uploadAnnotation",
    "click .g-annotation-permissions": "_changePermissions",
    "click .g-annotation-metadata": "_annotationMetadata",
    "click .g-annotation-row"(a) {
      var t = z(a.currentTarget);
      t.find(".g-annotation-toggle-select").click();
    },
    "click .g-annotation-row a,.g-annotation-toggle-select"(a) {
      a.stopPropagation();
    }
  },
  initialize() {
    this._drawn = /* @__PURE__ */ new Set(), this._viewer = null, this._sort = {
      field: "name",
      direction: 1
    }, this.collection = this.collection || new Yt([], { comparator: null }), this.users = new an(), this.listenTo(this.collection, "all", this.render), this.listenTo(this.users, "all", this.render), this.listenTo(zt, "g:event.large_image_annotation.create", () => this.collection.fetch(null, !0)), this.listenTo(zt, "g:event.large_image_annotation.remove", () => this.collection.fetch(null, !0)), tn({
      type: "GET",
      url: "annotation/folder/" + this.model.get("folderId") + "/create",
      error: null
    }).done((a) => {
      this.createResp = a, girder.plugins.large_image.views.ConfigView.getConfigFile(this.model.get("folderId")).done((t) => {
        this._liconfig = t || {}, this._confList = this._liconfig.annotationList || {
          columns: [{
            type: "record",
            value: "name"
          }, {
            type: "record",
            value: "creator",
            format: "user"
          }, {
            type: "record",
            value: "created",
            format: "date"
          }]
        }, this.collection.comparator = ct.constant(0), this._lastSort = this._confList.defaultSort || [{
          type: "record",
          value: "updated",
          dir: "up"
        }, {
          type: "record",
          value: "updated",
          dir: "down"
        }], this.collection.sortField = JSON.stringify(this._lastSort.reduce((n, e) => (n.push([
          (e.type === "metadata" ? "annotation.attributes." : "") + e.value,
          e.dir === "down" ? 1 : -1
        ]), e.type === "record" && n.push([
          `annotation.${e.value}`,
          e.dir === "down" ? 1 : -1
        ]), n), [])), this.collection.fetch({
          itemId: this.model.id,
          sort: this.collection.sortField || "created",
          sortdir: -1
        }).done(() => {
          this._fetchUsers();
        });
      });
    });
  },
  render() {
    this.$el.html(Ye({
      item: this.model,
      accessLevel: this.model.getAccessLevel(),
      creationAccess: this.createResp,
      annotations: this.collection,
      users: this.users,
      canDraw: this._viewer && this._viewer.annotationAPI(),
      drawn: this._drawn,
      apiRoot: vt(),
      confList: this._confList,
      AccessType: Xe
    }));
    const a = this.$(".g-annotation-select input:checked").length > 0;
    return [".g-annotation-download-selected", ".g-annotation-delete", ".g-annotation-permissions"].forEach((t) => {
      this.$(`thead ${t}`).prop("disabled", !a).toggleClass("disabled", !a).css("color", a ? "" : "grey");
    }), this;
  },
  setViewer(a) {
    return this._drawn.clear(), this._viewer = a, this;
  },
  _displayAnnotation(a) {
    if (!this._viewer || !this._viewer.annotationAPI())
      return;
    const t = z(a.currentTarget).closest(".g-annotation-row"), n = t.data("annotationId"), e = this.collection.get(n), i = t.find(".g-annotation-toggle-select i.icon-eye").length;
    i ? (this._drawn.delete(n), this._viewer.removeAnnotation(e)) : (this._drawn.add(n), e.fetch().then(() => (this._drawn.has(n) && this._viewer.drawAnnotation(e), null))), t.find(".g-annotation-toggle-select i").toggleClass("icon-eye", !i).toggleClass("icon-eye-off", !!i);
    const o = this.collection.some((l) => this._drawn.has(l.id));
    this.$el.find("th.g-annotation-toggle i").toggleClass("icon-eye", !!o).toggleClass("icon-eye-off", !o);
  },
  _displayAllAnnotations(a) {
    if (!this._viewer || !this._viewer.annotationAPI())
      return;
    const t = this.collection.some((n) => this._drawn.has(n.id));
    this.collection.forEach((n) => {
      const e = n.id;
      let i = this._drawn.has(n.id);
      t && i ? (this._drawn.delete(e), this._viewer.removeAnnotation(n), i = !1) : !t && !i && (this._drawn.add(e), n.fetch().then(() => (this._drawn.has(e) && this._viewer.drawAnnotation(n), null)), i = !0), this.$el.find(`.g-annotation-row[data-annotation-id="${e}"] .g-annotation-toggle-select i`).toggleClass("icon-eye", !!i).toggleClass("icon-eye-off", !i);
    }), this.$el.find("th.g-annotation-toggle i").toggleClass("icon-eye", !t).toggleClass("icon-eye-off", !!t);
  },
  _selectAnnotation(a) {
    a.stopPropagation();
    const n = z(a.currentTarget).parents(".g-annotation-row").data("annotationId"), e = this.$el.find("td.g-annotation-select input[type=checkbox]"), i = this.$(".g-annotation-select input:checked").length > 0, o = this.$("#select-all"), l = e.filter(":checked");
    this.$("thead .g-annotation-download-selected, thead .g-annotation-delete, thead .g-annotation-permissions").prop("disabled", !i).toggleClass("disabled", !i).css("color", i ? "" : "grey"), n ? o.prop("checked", l.length === e.length) : e.prop("checked", o.is(":checked"));
  },
  _downloadSelectedAnnotations(a) {
    if (a.preventDefault(), this.$("#select-all").is(":checked")) {
      const n = `${vt()}/annotation/item/${this.model.id}/`, e = document.createElement("a");
      e.setAttribute("href", n), e.setAttribute("download", `${this.model.get("name")}_annotations.json`), document.body.appendChild(e), e.click();
    } else
      this.$(".g-annotation-select input:checked").closest(".g-annotation-row").map((e, i) => z(i).data("annotationId")).get().forEach((e) => {
        const i = this.collection.get(e);
        i && i.fetch().then(() => {
          const o = `${vt()}/annotation/${i.id}`, l = document.createElement("a");
          return l.setAttribute("href", o), l.setAttribute("download", `${i.get("annotation").name}.json`), document.body.appendChild(l), l.click(), document.body.removeChild(l), null;
        });
      });
  },
  _deleteAnnotation(a) {
    const n = z(a.currentTarget).parents(".g-annotation-row").data("annotationId"), e = this.$el.find(".g-annotation-select input[type=checkbox]:checked"), i = [];
    if (!n) {
      for (let l = 0; l < e.length; l++) {
        const c = z(e[l]).parents(".g-annotation-row").data("annotationId");
        i.push(c);
      }
      if (e.length !== 0) {
        Dt({
          text: `<h3>Are you sure you want to delete the following annotations?</h3>
                        <ul"
    >${ct.map(i, (l) => {
            if (l !== void 0) {
              const c = this.collection.get(l);
              if (c) {
                const d = c.get("annotation").name;
                return `<li>${ct.escape(d)}</li>`;
              }
            }
            return "";
          }).join("")}</ul>`,
          escapedHtml: !0,
          yesText: "Delete",
          confirmCallback: () => {
            for (let l = 0; l < i.length; l++)
              i[l] !== void 0 && (this._drawn.delete(i[l]), this.collection.get(i[l]).destroy());
          }
        });
        return;
      }
    }
    const o = this.collection.get(n);
    Dt({
      text: `Are you sure you want to delete <b>${ct.escape(o.get("annotation").name)}</b>?`,
      escapedHtml: !0,
      yesText: "Delete",
      confirmCallback: () => {
        this._drawn.delete(n), o.destroy();
      }
    });
  },
  _uploadAnnotation() {
    var a = new on({
      el: z("#g-dialog-container"),
      title: "Upload Annotation",
      parent: this.model,
      parentType: "item",
      parentView: this,
      multiFile: !0,
      otherParams: {
        reference: JSON.stringify({
          identifier: "LargeImageAnnotationUpload",
          itemId: this.model.id,
          fileId: this.model.get("largeImage") && this.model.get("largeImage").fileId,
          userId: (Ke() || {}).id
        })
      }
    }).on("g:uploadFinished", () => {
      nn.trigger("g:alert", {
        icon: "ok",
        text: "Uploaded annotations.",
        type: "success",
        timeout: 4e3
      }), this.collection.fetch(null, !0);
    }, this);
    this._uploadWidget = a, a.render();
  },
  _changePermissions(a) {
    let n = z(a.currentTarget).parents(".g-annotation-row").data("annotationId");
    const e = this.$el.find(".g-annotation-select input[type=checkbox]:checked"), i = [];
    !n && this.collection.length === 1 && (n = this.collection.at(0).id);
    const o = n ? this.collection.get(n) : this.collection.at(0).clone();
    if (!n) {
      for (let l = 0; l < e.length; l++) {
        const c = z(e[l]).parents(".g-annotation-row").data("annotationId");
        i.push(c);
      }
      o.get("annotation").name = "Selected Annotations", o.save = () => {
      }, o.updateAccess = () => {
        const l = {
          access: o.get("access"),
          public: o.get("public"),
          publicFlags: o.get("publicFlags")
        };
        for (let c = 0; c < i.length; c++) {
          const d = this.collection.get(i[c]);
          d && (d.set(l), d.updateAccess());
        }
        this.collection.fetch(null, !0), o.trigger("g:accessListSaved");
      };
    }
    new en({
      el: z("#g-dialog-container"),
      type: "annotation",
      hideRecurseOption: !0,
      parentView: this,
      model: o,
      noAccessFlag: !0
    }).on("g:accessListSaved", () => {
      this.collection.fetch(null, !0);
    });
  },
  _fetchUsers() {
    this.collection.each((a) => {
      this.users.add({ _id: a.get("creatorId") }), this.users.add({ _id: a.get("updatedId") });
    }), z.when.apply(z, this.users.map((a) => a.fetch())).always(() => {
      this.render();
    });
  }
}), Ct = girder._, { wrap: At } = girder.utilities.PluginUtils, un = girder.events;
un.on("g:appload.before", function() {
  const a = girder.plugins.large_image.views.ImageViewerSelectWidget;
  At(a, "initialize", function(t, n) {
    this.itemId = n.imageModel.id, this.model = n.imageModel, this._annotationList = new sn({
      model: this.model,
      parentView: this
    }), t.apply(this, Ct.rest(arguments));
  }), At(a, "render", function(t) {
    return t.apply(this, Ct.rest(arguments)), this.$el.append(me()), this._annotationList.setViewer(this.currentViewer).setElement(this.$(".g-annotation-list-container")).render(), this;
  }), At(a, "_selectViewer", function(t) {
    return t.apply(this, Ct.rest(arguments)), this._annotationList.setViewer(this.currentViewer).render(), this;
  });
});
const ln = girder._;
function ut(a, t) {
  return t = t || a.type(), ln.extend({}, Wt[t] || {});
}
function Ot(a) {
  return [a.x, a.y, a.z || 0];
}
const gn = girder._;
function cn(a) {
  const t = ut(a);
  return gn.extend(t, {
    type: "point",
    center: Ot(a.coordinates()[0])
  });
}
const dn = girder._;
function St(a) {
  const t = ut(a);
  let n = a.coordinates(), e = [
    Math.atan2(n[1].y - n[0].y, n[1].x - n[0].x),
    Math.atan2(n[2].y - n[1].y, n[2].x - n[1].x),
    Math.atan2(n[3].y - n[2].y, n[3].x - n[2].x),
    Math.atan2(n[0].y - n[3].y, n[0].x - n[3].x)
  ], i = e.indexOf(Math.min(...e));
  e[(i + 1) % 4] - e[i] > Math.PI && (n = [n[0], n[3], n[2], n[1]], e = [
    Math.atan2(n[1].y - n[0].y, n[1].x - n[0].x),
    Math.atan2(n[2].y - n[1].y, n[2].x - n[1].x),
    Math.atan2(n[3].y - n[2].y, n[3].x - n[2].x),
    Math.atan2(n[0].y - n[3].y, n[0].x - n[3].x)
  ], i = e.indexOf(Math.min(...e))), e[i] < -0.75 * Math.PI && (i += 1);
  const o = n[i % 4], l = n[(i + 1) % 4], c = n[(i + 2) % 4], d = n[(i + 3) % 4], u = [c.x - l.x, c.y - l.y], h = [l.x - o.x, l.y - o.y], F = Math.atan2(u[1], u[0]), f = Math.sqrt(h[0] * h[0] + h[1] * h[1]), b = Math.sqrt(u[0] * u[0] + u[1] * u[1]), w = [
    0.25 * (o.x + l.x + c.x + d.x),
    0.25 * (o.y + l.y + c.y + d.y),
    0
  ];
  return dn.extend(t, {
    type: "rectangle",
    center: w,
    width: b,
    height: f,
    rotation: F
  });
}
function hn(a) {
  const t = St(a);
  return t.type = "ellipse", t;
}
function _n(a) {
  const t = St(a);
  return t.type = "circle", t.radius = Math.max(t.width, t.height) / 2, delete t.width, delete t.height, delete t.rotation, delete t.normal, t;
}
const fn = girder._;
function pt(a) {
  return fn.map(a, Ot);
}
const pn = girder._;
function Fn(a) {
  const t = ut(a, "polyline");
  let n = a.coordinates();
  const e = n.inner ? n.inner.map((i) => pt(i)) : void 0;
  return n = pt(n.outer || n), pn.extend(t, {
    type: "polyline",
    closed: !0,
    points: n,
    holes: e
  });
}
const mn = girder._;
function yn(a) {
  const t = ut(a, "polyline"), n = pt(a.coordinates());
  return mn.extend(t, {
    type: "polyline",
    closed: !!a.style("closed"),
    points: n
  });
}
const Et = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  circle: _n,
  ellipse: hn,
  line: yn,
  point: cn,
  polygon: Fn,
  rectangle: St
}, Symbol.toStringTag, { value: "Module" })), bn = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  array: pt,
  point: Ot
}, Symbol.toStringTag, { value: "Module" })), wn = girder._;
function Kt(a) {
  var t = a.type();
  if (!wn.has(Et, t))
    throw new Error(
      `Unknown annotation type "${t}"`
    );
  return Et[t](a);
}
const vn = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  common: ut,
  convert: Kt,
  coordinates: bn,
  types: Et
}, Symbol.toStringTag, { value: "Module" })), Cn = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  convert: Jt,
  convertFeatures: Ue,
  defaults: Wt,
  geojs: vn,
  geometry: xt,
  rotate: jt,
  style: kt
}, Symbol.toStringTag, { value: "Module" })), An = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  AnnotationCollection: Yt,
  ElementCollection: Gt
}, Symbol.toStringTag, { value: "Module" })), Ln = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  AnnotationModel: st
}, Symbol.toStringTag, { value: "Module" })), xn = girder.$, { wrap: En } = girder.utilities.PluginUtils, te = girder.views.widgets.HierarchyWidget, { restRequest: ee } = girder.rest, jn = girder.views.widgets.AccessWidget;
En(te, "render", function(a) {
  a.call(this), this.parentModel.get("_modelType") === "folder" && Wn(this, this.parentModel.id);
});
function Wn(a, t) {
  ee({
    type: "GET",
    url: "annotation/folder/" + t + "/present",
    data: {
      recurse: !0
    }
  }).done((n) => {
    n && kn(a);
  });
}
function kn(a) {
  a.$(".g-edit-annotation-access").length === 0 && (a.$(".g-folder-actions-menu > .divider").length > 0 ? a.$(".g-folder-actions-menu > .divider").before(
    '<li role="presentation"><a class="g-edit-annotation-access" role="menuitem"><i class="icon-lock"></i>Annotation access control</a></li>'
  ) : a.$("ul.g-folder-actions-menu").append(
    '<li role="presentation"><a class="g-edit-annotation-access" role="menuitem"><i class="icon-lock"></i>Annotation access control</a></li>'
  ), a.events["click .g-edit-annotation-access"] = $n, a.delegateEvents());
}
function $n() {
  ee({
    type: "GET",
    url: "annotation/folder/" + this.parentModel.get("_id"),
    data: {
      recurse: !0,
      limit: 1
    }
  }).done((a) => {
    const t = new st(a[0]);
    t.get("annotation").name = "Your Annotations", t.save = () => {
    }, t.updateAccess = (n) => {
      const e = {
        access: t.get("access"),
        public: t.get("public"),
        publicFlags: t.get("publicFlags")
      }, i = new st();
      i.id = this.parentModel.get("_id"), i.altUrl = "annotation/folder", i.set(e), i.updateAccess(n), t.trigger("g:accessListSaved");
    }, t.fetchAccess(!0).done(() => {
      new jn({
        // eslint-disable-line no-new
        el: xn("#g-dialog-container"),
        modelType: "annotation",
        model: t,
        hideRecurseOption: !1,
        parentView: this,
        noAccessFlag: !0
      });
    });
  });
}
const Lt = girder.$, Ht = girder._, { restRequest: On } = girder.rest, { wrap: Sn } = girder.utilities.PluginUtils, ne = girder.views.widgets.ItemListWidget;
Sn(ne, "render", function(a) {
  a.apply(this, Ht.rest(arguments));
  function t(n, e, i, o) {
    const l = Lt('.large_image_thumbnail[g-item-cid="' + n.cid + '"]', e).first();
    if (!l.length)
      return;
    let c = l.find(".large_image_annotation_badge");
    c.length === 0 && (c = Lt('<div class="large_image_annotation_badge hidden"></div>').appendTo(l)), c.attr("title", o ? "Referenced by an annotation" : `${i} annotation${i === 1 ? "" : "s"}`).text(i).toggleClass("hidden", !i);
  }
  nt.getSettings((n) => {
    if (n["large_image.show_thumbnails"] === !1 || this.$(".large_image_annotation_badge").length > 0)
      return;
    const e = this.collection.toArray();
    if (!Ht.some(e, (c) => c.has("largeImage")) || this._inFetch || this._needsFetch)
      return;
    const o = e.filter((c) => c._annotationCount === void 0 && c.has("largeImage")).map((c) => (c._annotationCount = null, delete c._annotationReferenced, c.id));
    let l;
    o.length ? l = On({
      type: "POST",
      url: "annotation/counts",
      data: {
        items: o.join(",")
      },
      headers: { "X-HTTP-Method-Override": "GET" },
      error: null
    }).done((c) => {
      Object.entries(c).forEach(([d, u]) => {
        d === "referenced" ? Object.keys(u).forEach((h) => {
          this.collection.get(h) && (this.collection.get(h)._annotationReferenced = !0);
        }) : this.collection.get(d) && (this.collection.get(d)._annotationCount = u);
      });
    }) : l = Lt.Deferred().resolve({}), l.then(() => (this.collection.forEach((c) => {
      c._annotationCount !== void 0 && (c._annotationReferenced ? t(c, this.$el, "*", !0) : t(c, this.$el, c._annotationCount));
    }), null));
  });
});
const In = girder._;
var Ut = {
  /**
   * Returns whether or not the view supports drawing and rendering
   * annotations.
   */
  annotationAPI: In.constant(!1),
  /**
   * Render an annotation model on the image.
   *
   * @param {AnnotationModel} annotation
   */
  drawAnnotation: function() {
    throw new Error("Viewer does not support drawing annotations");
  },
  /**
   * Remove an annotation from the image.  This simply
   * finds a layer with the given id and removes it because
   * each annotation is contained in its own layer.  If
   * the annotation is not drawn, this is a noop.
   *
   * @param {AnnotationModel} annotation
   */
  removeAnnotation: function() {
    throw new Error("Viewer does not support drawing annotations");
  },
  /**
   * Set the image interaction mode to region drawing mode.  This
   * method takes an optional `model` argument where the region will
   * be stored when created by the user.  In any case, this method
   * returns a promise that resolves to an array defining the region:
   *   [ left, top, width, height ]
   *
   * @param {Backbone.Model} [model] A model to set the region to
   * @returns {Promise}
   */
  drawRegion: function() {
    throw new Error("Viewer does not support drawing annotations");
  },
  /**
   * Set the image interaction mode to draw the given type of annotation.
   *
   * @param {string} type An annotation type
   * @param {object} [options]
   * @param {boolean} [options.trigger=true]
   *      Trigger a global event after creating each annotation element.
   * @returns {Promise}
   *      Resolves to an array of generated annotation elements.
   */
  startDrawMode: function() {
    throw new Error("Viewer does not support drawing annotations");
  }
};
const Tn = girder.$, k = girder._, Rn = girder.Backbone, tt = girder.events, { wrap: Mn } = girder.utilities.PluginUtils, { restRequest: Pn, getApiRoot: dt } = girder.rest;
function Vt() {
  function a() {
    return Math.floor((1 + Math.random()) * 65536).toString(16).substring(1);
  }
  return a() + a() + a() + a() + a() + a();
}
var zn = function(a) {
  return Mn(a, "initialize", function(t) {
    var n = arguments[1];
    return this._annotations = {}, this._featureOpacity = {}, this._unclampBoundsForOverlay = !0, this._globalAnnotationOpacity = n.globalAnnotationOpacity || 1, this._globalAnnotationFillOpacity = n.globalAnnotationFillOpacity || 1, this.listenTo(tt, "s:widgetDrawRegionEvent", this.drawRegion), this.listenTo(tt, "s:widgetClearRegion", this.clearRegion), this.listenTo(tt, "g:startDrawMode", this.startDrawMode), this._hoverEvents = n.hoverEvents, t.apply(this, k.rest(arguments));
  }), {
    _postRender: function() {
      this.featureLayer = this.viewer.createLayer("feature", {
        features: ["point", "line", "polygon", "marker"]
      }), this.setGlobalAnnotationOpacity(this._globalAnnotationOpacity), this.setGlobalAnnotationFillOpacity(this._globalAnnotationFillOpacity), this.annotationLayer = this.viewer.createLayer("annotation", {
        annotations: ["point", "line", "rectangle", "ellipse", "circle", "polygon"],
        showLabels: !1
      });
      var t = window.geo;
      this.viewer.geoOn(t.event.pan, () => {
        this.setBounds();
      });
    },
    annotationAPI: k.constant(!0),
    /**
     * @returns whether to clamp viewer bounds when image overlays are
     * rendered
     */
    getUnclampBoundsForOverlay: function() {
      return this._unclampBoundsForOverlay;
    },
    /**
     *
     * @param {bool} newValue Set whether to clamp viewer bounds when image
     * overlays are rendered.
     */
    setUnclampBoundsForOverlay: function(t) {
      this._unclampBoundsForOverlay = t;
    },
    /**
     * Given an image overlay annotation element, compute and return
     * a proj-string representation of its transform specification.
     * @param {object} overlay A image annotation element.
     * @returns a proj-string representing how to overlay should be
     *   transformed.
     */
    _getOverlayTransformProjString: function(t) {
      const n = t.transform || {};
      let e = n.xoffset || 0, i = n.yoffset || 0;
      const o = n.matrix || [[1, 0], [0, 1]];
      let l = o[0][0], c = o[0][1], d = o[1][0], u = o[1][1];
      const h = 2 ** this._getOverlayRelativeScale(t);
      h && h !== 1 && (l /= h, c /= h, d /= h, u /= h, e *= h, i *= h);
      let F = "+proj=longlat +axis=enu";
      return e !== 0 && (e = -1 * e, F = F + ` +xoff=${e}`), i !== 0 && (F = F + ` +yoff=${i}`), (l !== 1 || c !== 0 || d !== 0 || u !== 1) && (F = F + ` +s11=${1 / l} +s12=${c} +s21=${d} +s22=${1 / u}`), F;
    },
    /**
     * Given an overlay with a transform matrix, compute an approximate
     * scale compaared to the base.
     *
     * @param {object} overlay The overlay annotation record.
     * @returns {number} The approximate scale as an integer power of two.
     */
    _getOverlayRelativeScale: function(t) {
      const e = (t.transform || {}).matrix || [[1, 0], [0, 1]], i = e[0][0], o = e[0][1], l = e[1][0], c = e[1][1], d = Math.sqrt(Math.abs(i * c - o * l)) || 1;
      return Math.floor(Math.log2(d));
    },
    /**
     * @returns The number of currently drawn overlay elements across
     * all annotations.
     */
    _countDrawnImageOverlays: function() {
      let t = 0;
      return k.each(this._annotations, (n, e, i) => {
        const o = n.overlays || [];
        t += o.length;
      }), t;
    },
    /**
     * Set additional parameters for pixelmap overlays.
     * @param {object} layerParams An object containing layer parameters. This should already have
     * generic properties for overlay annotations set, such as the URL, opacity, etc.
     * @param {object} pixelmapElement A pixelmap annotation element
     * @param {number} levelDifference The difference in zoom level between the base image and the overlay
     * @returns An object containing parameters needed to create a pixelmap layer.
     */
    _addPixelmapLayerParams(t, n, e, i) {
      i = i || "", t.keepLower = !1, k.isFunction(t.url) || e ? t.url = (d, u, h) => dt() + "/item/" + n.girderId + `/tiles/zxy/${h - e}/${d}/${u}?encoding=PNG` + i : t.url = t.url + "?encoding=PNG" + i;
      let o = n.values;
      if (n.boundaries) {
        const d = new Array(o.length * 2);
        for (let u = 0; u < o.length; u++)
          d[u * 2] = d[u * 2 + 1] = o[u];
        o = d;
      }
      t.data = o;
      const l = n.categories, c = n.boundaries;
      return t.style = {
        color: (d, u) => {
          if (d < 0 || d >= l.length)
            return console.warn(`No category found at index ${d} in the category map.`), "rgba(0, 0, 0, 0)";
          let h;
          const F = l[d];
          return c ? h = u % 2 === 0 ? F.fillColor : F.strokeColor : h = F.fillColor, h;
        }
      }, t;
    },
    /**
     * Generate layer parameters for an image overlay layer
     * @param {object} overlayImageMetadata metadata such as size, tile size, and levels for the overlay image
     * @param {string} overlayImageId ID of a girder image item
     * @param {object} overlay information about the overlay such as opacity
     * @returns layer params for the image overlay layer
     */
    _generateOverlayLayerParams(t, n, e) {
      const o = window.geo.util.pixelCoordinateParams(
        this.viewer.node(),
        t.sizeX,
        t.sizeY,
        t.tileWidth,
        t.tileHeight
      );
      o.layer.useCredentials = !0, o.layer.url = `${dt()}/item/${n}/tiles/zxy/{z}/{x}/{y}`;
      let l = "";
      this._countDrawnImageOverlays() <= 5 ? o.layer.autoshareRenderer = !1 : (o.layer.renderer = "canvas", l = "&edge=%23ffffff00", o.layer.url += "?" + l.substr(1)), o.layer.opacity = e.opacity || 1, o.layer.opacity *= this._globalAnnotationOpacity;
      let c = this.levels - t.levels;
      return c -= this._getOverlayRelativeScale(e), this.levels !== t.levels && (o.layer.url = (d, u, h) => dt() + "/item/" + n + `/tiles/zxy/${h - c}/${d}/${u}` + (l ? "?" + l.substr(1) : ""), o.layer.minLevel = c, o.layer.maxLevel += c, o.layer.tilesMaxBounds = (d) => {
        var u = Math.pow(2, o.layer.maxLevel - d);
        return {
          x: Math.floor(t.sizeX / u),
          y: Math.floor(t.sizeY / u)
        };
      }, o.layer.tilesAtZoom = (d) => {
        var u = Math.pow(2, o.layer.maxLevel - d);
        return {
          x: Math.ceil(t.sizeX / t.tileWidth / u),
          y: Math.ceil(t.sizeY / t.tileHeight / u)
        };
      }), e.type === "pixelmap" ? o.layer = this._addPixelmapLayerParams(o.layer, e, c, l) : e.hasAlpha && (o.layer.keepLower = !1, o.layer.url = (d, u, h) => dt() + "/item/" + n + `/tiles/zxy/${h - c}/${d}/${u}?encoding=PNG` + l), o.layer;
    },
    /**
     * Render an annotation model on the image.  Currently, this is limited
     * to annotation types that can be (1) directly converted into geojson
     * primitives, (2) be represented as heatmaps, or (3) shown as image
     * overlays.
     *
     * Internally, this generates a new feature layer for the annotation
     * that is referenced by the annotation id.  All "elements" contained
     * inside this annotation are drawn in the referenced layer.
     *
     * @param {AnnotationModel} annotation
     * @param {object} [options]
     * @param {boolean} [options.fetch=true] Enable fetching the annotation
     *   from the server, including paging the results.  If false, it is
     *   assumed the elements already exist on the annotation object.  This
     *   is useful for temporarily showing annotations that are not
     *   propagated to the server.
     */
    drawAnnotation: function(t, n) {
      if (!this.viewer)
        return;
      var e = window.geo;
      n = k.defaults(n || {}, { fetch: !0 });
      var i = t.geojson();
      const o = t.overlays() || [];
      var l = k.has(this._annotations, t.id), c;
      let d = !1;
      if (l && (k.each(this._annotations[t.id].features, (h, F) => {
        F || !t._centroids || !h._centroidFeature ? h._ownLayer ? h.layer().map().deleteLayer(h.layer()) : (this.featureLayer.deleteFeature(h), d = !0) : c = h;
      }), this._annotations[t.id].overlays && k.each(this._annotations[t.id].overlays, (h) => {
        const F = this._annotations[t.id].overlays.map((b) => b.id), f = o.map((b) => b.id);
        k.each(F, (b) => {
          if (!f.includes(b)) {
            const w = this.viewer.layers().find((L) => L.id() === b);
            this.viewer.deleteLayer(w);
          }
        });
      })), this._annotations[t.id] = {
        features: c ? [c] : [],
        options: n,
        annotation: t,
        overlays: o
      }, !(n.fetch && (!l || t.refresh() || t._inFetch === "centroids") && (t.off("g:fetched", null, this).on("g:fetched", () => {
        this.trigger(
          "g:mouseResetAnnotation",
          t
        ), this.drawAnnotation(t);
      }, this), this.setBounds({ [t.id]: this._annotations[t.id] }), t._inFetch === "centroids"))) {
        t.refresh(!1);
        var u = this._annotations[t.id].features;
        if (t._centroids && !c) {
          const h = this.featureLayer.createFeature("point");
          h._centroidFeature = !0, u.push(h), h.data(t._centroids.data).position((F, f) => ({
            x: t._centroids.centroids.x[f],
            y: t._centroids.centroids.y[f]
          })).style({
            radius: (F, f) => {
              let b = t._centroids.centroids.r[f];
              return b ? (b /= 2.5 * this.viewer.unitsPerPixel(this.viewer.zoom()), b) : 8;
            },
            stroke: (F, f) => !t._shownIds || t._centroids.centroids.id[f] && !t._shownIds.has(t._centroids.centroids.id[f]),
            strokeColor: (F, f) => {
              const b = t._centroids.centroids.s[f];
              return t._centroids.props[b].strokeColor;
            },
            strokeOpacity: (F, f) => {
              const b = t._centroids.centroids.s[f];
              return t._centroids.props[b].strokeOpacity;
            },
            strokeWidth: (F, f) => {
              const b = t._centroids.centroids.s[f];
              return t._centroids.props[b].strokeWidth;
            },
            fill: (F, f) => !t._shownIds || t._centroids.centroids.id[f] && !t._shownIds.has(t._centroids.centroids.id[f]),
            fillColor: (F, f) => {
              const b = t._centroids.centroids.s[f];
              return t._centroids.props[b].fillColor;
            },
            fillOpacity: (F, f) => {
              const b = t._centroids.centroids.s[f];
              return t._centroids.props[b].fillOpacity;
            }
          }), t._centroidLastZoom = void 0, h.geoOn(e.event.pan, () => {
            if (this.viewer.zoom() !== t._centroidLastZoom)
              if (t._centroidLastZoom = this.viewer.zoom(), h.verticesPerFeature) {
                const w = 2.5 * this.viewer.unitsPerPixel(this.viewer.zoom()), L = h.verticesPerFeature(), R = h.data().length, S = new Float32Array(L * R);
                for (var F = 0, f = 0; F < R; F += 1) {
                  let W = t._centroids.centroids.r[F];
                  W ? W /= w : W = 8;
                  for (var b = 0; b < L; b += 1, f += 1)
                    S[f] = W;
                }
                h.updateStyleFromArray("radius", S, !0);
              } else
                h.modified().draw();
          }), t._centroids._redraw = !1;
        } else t._centroids && c && t._centroids._redraw && (c.data(t._centroids.data), t._centroids._redraw = !1, d = !0);
        this.getUnclampBoundsForOverlay() && this._annotations[t.id].overlays.length > 0 && (this.viewer.clampBoundsY(!1), this.viewer.clampBoundsX(!1)), k.each(this._annotations[t.id].overlays, (h) => {
          const F = h.girderId;
          Pn({
            url: `item/${F}/tiles`
          }).done((f) => {
            if (!this.viewer)
              return;
            const b = this.viewer.layers().filter(
              (M) => M.id() === h.id
            );
            b.length > 0 && k.each(b, (M) => {
              this.viewer.deleteLayer(M);
            });
            const w = this._generateOverlayLayerParams(f, F, h), L = h.type === "pixelmap" ? "pixelmap" : "osm", R = this._getOverlayTransformProjString(h), S = this.viewer.createLayer(L, Object.assign({}, w, { id: h.id, gcs: R }));
            this.annotationLayer.moveToTop(), this.trigger("g:drawOverlayAnnotation", h, S);
            const W = e.event.feature;
            S.geoOn(
              [
                W.mousedown,
                W.mouseup,
                W.mouseclick,
                W.mouseoff,
                W.mouseon,
                W.mouseover,
                W.mouseout
              ],
              (M) => this._onMouseFeature(M, t.elements().get(h.id), S)
            ), this.viewer.scheduleAnimationFrame(this.viewer.draw, !0);
          }).fail((f) => {
            console.error(`There was an error overlaying image with ID ${F}`);
          });
        }), this._featureOpacity[t.id] = {}, e.createFileReader("geojsonReader", { layer: this.featureLayer }).read(i, (h) => {
          h.length === 0 && (h = t.non_geojson(this.featureLayer), h.length && this.featureLayer.map().draw()), k.each(h || [], (f) => {
            var b = e.event.feature;
            u.push(f), f.selectionAPI(this._hoverEvents), f.geoOn(
              [
                b.mousedown,
                b.mouseup,
                b.mouseclick,
                b.mouseoff,
                b.mouseon,
                b.mouseover,
                b.mouseout
              ],
              (w) => this._onMouseFeature(w)
            ), t._centroids && (t._shownIds = new Set(f.data().map((w) => w.id))), this._featureOpacity[t.id][f.featureType] = f.data().map(({ id: w, properties: L }) => ({
              id: w,
              fillOpacity: L.fillOpacity,
              strokeOpacity: L.strokeOpacity
            }));
          }), this._mutateFeaturePropertiesForHighlight(t.id, h);
          const F = u.find((f) => f._centroidFeature);
          t._centroids && F && (F.verticesPerFeature ? this.viewer.scheduleAnimationFrame(() => {
            if (!t._shownIds)
              return;
            const f = u.find((L) => L._centroidFeature), b = f.data().length, w = new Float32Array(b);
            for (let L = 0; L < b; L += 1)
              w[L] = t._shownIds.has(t._centroids.centroids.id[L]) ? 0 : 1;
            f.updateStyleFromArray({
              stroke: w,
              fill: w
            }, void 0, !0);
          }) : F.modified()), this.viewer.scheduleAnimationFrame(this.viewer.draw, !0);
        }), d && this.featureLayer._update();
      }
    },
    /**
     * Highlight the given annotation/element by reducing the opacity of all
     * other elements by 75%.  For performance reasons, features with a large
     * number of elements are not modified.  The limit for this behavior is
     * configurable via the constructor option `highlightFeatureSizeLimit`.
     *
     * Both arguments are optional.  If no element is provided, then all
     * elements in the given annotation are highlighted.  If no annotation
     * is provided, then highlighting state is reset and the original
     * opacities are used for all elements.
     *
     * @param {string?} annotation The id of the annotation to highlight
     * @param {string?} element The id of the element to highlight
     */
    highlightAnnotation: function(t, n) {
      return (t !== this._highlightAnnotation || n !== this._highlightElement) && (this._highlightAnnotation = t, this._highlightElement = n, k.each(this._annotations, (e, i) => {
        const o = e.features;
        this._mutateFeaturePropertiesForHighlight(i, o);
      }), this.viewer.scheduleAnimationFrame(this.viewer.draw)), this;
    },
    /**
     * Hide the given annotation/element by settings its opacity to 0.  See
     * highlightAnnotation for caveats.
     *
     * If either argument is not provided, hiding is turned off.
     *
     * @param {string?} annotation The id of the annotation to hide
     * @param {string?} element The id of the element to hide
     */
    hideAnnotation: function(t, n) {
      return this._hideAnnotation = t, this._hideElement = n, k.each(this._annotations, (e, i) => {
        const o = e.features;
        console.log(o), this._mutateFeaturePropertiesForHighlight(i, o);
      }), this.viewer.scheduleAnimationFrame(this.viewer.draw), this;
    },
    /**
     * Use geojs's `updateStyleFromArray` to modify the opacities of all
     * elements in a feature.  This method uses the private attributes
     * `_highlightAnntotation` and `_highlightElement` to determine which
     * element to modify.
     */
    _mutateFeaturePropertiesForHighlight: function(t, n) {
      k.each(n, (i) => {
        const o = this._featureOpacity[t][i.featureType];
        if (!o)
          return;
        var l = {
          datalen: o.length,
          annotationId: t,
          fillOpacity: this._globalAnnotationFillOpacity,
          highlightannot: this._highlightAnnotation,
          highlightelem: this._highlightElement,
          hideannot: this._hideAnnotation,
          hideelem: this._hideElement
        };
        if (k.isMatch(i._lastFeatureProp, l))
          return;
        const c = new Array(o.length), d = new Array(o.length);
        for (let u = 0; u < o.length; u += 1) {
          const h = o[u].id, F = o[u].fillOpacity * this._globalAnnotationFillOpacity, f = o[u].strokeOpacity;
          this._hideAnnotation && t === this._hideAnnotation && h === this._hideElement ? (c[u] = 0, d[u] = 0) : !this._highlightAnnotation || !this._highlightElement && t === this._highlightAnnotation || this._highlightElement === h ? (c[u] = F, d[u] = f) : (c[u] = F * 0.25, d[u] = f * 0.25);
        }
        i.updateStyleFromArray("fillOpacity", c), i.updateStyleFromArray("strokeOpacity", d), i._lastFeatureProp = l;
      });
      const e = this._annotations[t].overlays || null;
      e && k.each(e, (i) => {
        const o = this.viewer.layers().find((l) => l.id() === i.id);
        if (o) {
          let l = (i.opacity || 1) * this._globalAnnotationOpacity;
          this._highlightAnnotation && t !== this._highlightAnnotation && (l = l * 0.25), o.opacity(l);
        }
      });
    },
    /**
     * When the image visible bounds change, or an annotation is first created,
     * set the view information for any annotation which requires it.
     *
     * @param {object} [annotations] If set, a dictionary where the keys are
     *      annotation ids and the values are an object which includes the
     *      annotation options and a reference to the annotation.  If not
     *      specified, use `this._annotations` and update the view for all
     *      relevant annotatioins.
     */
    setBounds: function(t) {
      var n = this.viewer.zoom(), e = this.viewer.bounds(), i = this.viewer.zoomRange();
      k.each(t || this._annotations, (o) => {
        o.options.fetch && o.annotation.setView && o.annotation.setView(e, n, i.max, void 0, this.sizeX, this.sizeY);
      });
    },
    /**
     * Remove an annotation from the image.  If the annotation is not
     * drawn, this does nothing.
     *
     * @param {AnnotationModel} annotation
     */
    removeAnnotation: function(t) {
      t.off("g:fetched", null, this), this.trigger(
        "g:mouseResetAnnotation",
        t
      ), k.has(this._annotations, t.id) && (k.each(this._annotations[t.id].features, (n) => {
        n._ownLayer ? n.layer().map().deleteLayer(n.layer()) : this.featureLayer.deleteFeature(n);
      }), k.each(this._annotations[t.id].overlays, (n) => {
        const e = this.viewer.layers().filter(
          (i) => i.id() === n.id
        );
        k.each(e, (i) => {
          this.trigger("g:removeOverlayAnnotation", n, i), this.viewer.deleteLayer(i);
        });
      }), delete this._annotations[t.id], delete this._featureOpacity[t.id], this._countDrawnImageOverlays() === 0 && this.getUnclampBoundsForOverlay() && (this.viewer.clampBoundsY(!0), this.viewer.clampBoundsX(!0)), this.viewer.scheduleAnimationFrame(this.viewer.draw));
    },
    /**
     * Combine two regions into a multipolygon region.
     */
    _mergeRegions(t, n) {
      return !t || !t.length || t.length < 2 || t === [-1, -1, -1, -1] ? n : (t.length === 4 ? t = [
        t[0],
        t[1],
        t[0] + t[2],
        t[1],
        t[0] + t[2],
        t[1] + t[3],
        t[0],
        t[1] + t[3]
      ] : t.length === 6 && (t = [
        t[0] - t[3],
        t[1] - t[4],
        t[0] + t[3],
        t[1] - t[4],
        t[0] + t[3],
        t[1] + t[4],
        t[0] - t[3],
        t[1] + t[4]
      ]), n.length === 4 ? n = [
        n[0],
        n[1],
        n[0] + n[2],
        n[1],
        n[0] + n[2],
        n[1] + n[3],
        n[0],
        n[1] + n[3]
      ] : n.length === 6 && (n = [
        n[0] - n[3],
        n[1] - n[4],
        n[0] + n[3],
        n[1] - n[4],
        n[0] + n[3],
        n[1] + n[4],
        n[0] - n[3],
        n[1] + n[4]
      ]), t.length === 2 && n.length === 2 && (n = [n[0], n[1], -1, -1]), t.concat([-1, -1]).concat(n));
    },
    /**
     * Set the image interaction mode to region drawing mode.  This
     * method takes an optional `model` argument where the region will
     * be stored when created by the user.  In any case, this method
     * returns a promise that resolves to an array defining the region:
     *   [ left, top, width, height ]
     *
     * @param {Backbone.Model|Object} [model] A model to set the region to,
     *   or an object with model, mode, add, and submitCtrl.
     * @param {string} [drawMode='rectangle'] An annotation drawing mode.
     * @param {boolean} [addToExisting=false] If truthy, add the new
     *   annotation to any existing annotation making a multipolygon.
     * @returns {$.Promise}
     */
    drawRegion: function(t, n, e) {
      let i, o;
      t && t.model && t.add !== void 0 && (n = t.mode, e = t.add, i = t.submitCtrl, o = t.event, t = t.model), t = t || new Rn.Model();
      const l = ["polygon", "line", "point", "rectangle"].includes(n) ? n : n === "polyline" ? "line" : o ? n : "rectangle";
      return this.startDrawMode(l, { trigger: !1, signalModeChange: !0 }).then((c) => {
        var d = c[0];
        let u = "-1,-1,-1,-1";
        switch (n) {
          case "point":
            u = [Math.round(d.center[0]), Math.round(d.center[1])];
            break;
          case "line":
            u = d.points.map(([w, L, R]) => [Math.round(w), Math.round(L)]).flat(), u = u.slice(0, 4), u.push(-2), u.push(-2), u.push(-2), u.push(-2);
            break;
          case "polyline":
            for (u = d.points.map(([w, L, R]) => [Math.round(w), Math.round(L)]).flat(), u.push(-2), u.push(-2); u.length > 0 && u.length <= 6; )
              u.push(-2), u.push(-2);
            break;
          case "polygon":
            for (u = d.points.map(([w, L, R]) => [Math.round(w), Math.round(L)]).flat(); u.length > 0 && u.length <= 6; )
              u.push(u[0]), u.push(u[1]);
            break;
          default:
            var h = Math.round(d.center[0] - d.width / 2), F = Math.round(d.center[1] - d.height / 2), f = Math.round(d.width), b = Math.round(d.height);
            u = [h, F, f, b];
            break;
        }
        return e && (u = this._mergeRegions(t.get("value"), u)), t.set("value", u, { trigger: !0 }), tt.trigger("li:drawRegionUpdate", { values: u, submit: i, originalEvent: o }), t.get("value");
      });
    },
    clearRegion: function(t) {
      t && t.set("value", [-1, -1, -1, -1], { trigger: !0 });
    },
    /**
     * Set the image interaction mode to draw the given type of annotation.
     *
     * @param {string} type An annotation type, or null to turn off
     *    drawing.
     * @param {object} [options]
     * @param {boolean} [options.trigger=true] Trigger a global event after
     *    creating each annotation element.
     * @param {boolean} [options.keepExisting=false] If true, don't
     *    remove extant annotations.
     * @param {object} [options.modeOptions] Additional options to pass to
     *    the annotationLayer mode.
     * @returns {$.Promise}
     *    Resolves to an array of generated annotation elements.
     */
    startDrawMode: function(t, n) {
      var e = this.annotationLayer, i = [], o = [], l = Tn.Deferred(), c;
      return e.geoOff(window.geo.event.annotation.mode), e.mode(null), e.geoOff(window.geo.event.annotation.state), n = k.defaults(n || {}, { trigger: !0 }), n.keepExisting || e.removeAllAnnotations(), e.geoOn(
        window.geo.event.annotation.state,
        (d) => {
          if (d.annotation.state() !== window.geo.annotation.state.done)
            return;
          e.geoOff(window.geo.event.annotation.mode);
          const u = {};
          e.currentBooleanOperation && (u.currentBooleanOperation = e.currentBooleanOperation()), c = Kt(d.annotation), c.id || (c.id = Vt()), i.push(c), o.push(d.annotation), n.trigger && tt.trigger("g:annotationCreated", c, d.annotation, u), e.removeAllAnnotations(), e.geoOff(window.geo.event.annotation.state), l.resolve(i, o, u);
        }
      ), e.mode(t, void 0, n.modeOptions), e.geoOn(window.geo.event.annotation.mode, (d) => {
        e.geoOff(window.geo.event.annotation.state), e.geoOff(window.geo.event.annotation.mode), n.signalModeChange && tt.trigger("li:drawModeChange", { event: d }), l.reject();
      }), l.promise();
    },
    setGlobalAnnotationOpacity: function(t) {
      return this._globalAnnotationOpacity = t, this.featureLayer && this.featureLayer.opacity(t), Object.values(this._annotations).forEach((n) => n.features.forEach((e) => {
        e._ownLayer && e.layer().opacity(t);
      })), k.each(this._annotations, (n) => {
        k.each(n.overlays, (e) => {
          const i = this.viewer.layers().find((o) => o.id() === e.id);
          if (i) {
            const o = e.opacity || 1;
            i.opacity(t * o);
          }
        });
      }), this;
    },
    setGlobalAnnotationFillOpacity: function(t) {
      return this._globalAnnotationFillOpacity = t, this.featureLayer && (k.each(this._annotations, (n, e) => {
        const i = n.features;
        this._mutateFeaturePropertiesForHighlight(e, i);
      }), this.viewer.scheduleAnimationFrame(this.viewer.draw)), this;
    },
    _setEventTypes: function() {
      var t = window.geo.event.feature;
      this._eventTypes = {
        [t.mousedown]: "g:mouseDownAnnotation",
        [t.mouseup]: "g:mouseUpAnnotation",
        [t.mouseclick]: "g:mouseClickAnnotation",
        [t.mouseoff]: "g:mouseOffAnnotation",
        [t.mouseon]: "g:mouseOnAnnotation",
        [t.mouseover]: "g:mouseOverAnnotation",
        [t.mouseout]: "g:mouseOutAnnotation"
      };
    },
    _onMouseFeature: function(t, n, e) {
      var i = t.data.properties || {}, o;
      if (this._eventTypes || this._setEventTypes(), i.element && i.annotation)
        o = this._eventTypes[t.event], o && this.trigger(
          o,
          i.element,
          i.annotation,
          t
        );
      else if (n && e && (o = this._eventTypes[t.event], o)) {
        const l = o + "Overlay";
        this.trigger(l, n, e, t);
      }
    },
    _guid: Vt
  };
};
const Nt = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  geojs: zn
}, Symbol.toStringTag, { value: "Module" })), ie = {};
for (var ht in girder.plugins.large_image.views.imageViewerWidget) {
  const a = girder.plugins.large_image.views.imageViewerWidget[ht];
  if (Object.keys(Ut).forEach(function(t) {
    a.prototype[t] = Ut[t];
  }), Nt[ht]) {
    const t = Nt[ht](a);
    Object.keys(t).forEach(function(n) {
      a.prototype[n] = t[n];
    });
  }
  ie[ht] = a;
}
const Dn = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  ConfigView: nt,
  HierarchyWidget: te,
  ItemListWidget: ne,
  ViewerWidget: ie
}, Symbol.toStringTag, { value: "Module" })), Hn = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  annotations: Cn,
  collections: An,
  models: Ln,
  views: Dn
}, Symbol.toStringTag, { value: "Module" })), Un = girder.views.widgets.SearchFieldWidget, { registerPluginNamespace: Vn } = girder.pluginUtils;
Vn("large_image_annotation", Hn);
Un.addMode(
  "li_annotation_metadata",
  ["item"],
  "Annotation Metadata search",
  'You can search specific annotation metadata keys by adding "key:<key name>" to your search.  Otherwise, all primary metadata keys are searched.  For example "key:quality good" would find any items with annotations that have attributes with a key named quality (case sensitive) that contains the word "good" (case insensitive) anywhere in its value.'
);
//# sourceMappingURL=girder-plugin-large-image-annotation.js.map
