#!/usr/bin/env python3
"""Generation pass: resolved requirements -> one JSON Schema per platform.

Stands in for parsing Button.md + button.md + policy.md. The resolution below is
what that parse would produce; emitting the schema from it is mechanical, which is
the point. Every constraint carries $comment (requirement id) and title (the
statement verbatim) so a failure can be reported in the contract's own words.
"""
import json, hashlib, pathlib

HERE = pathlib.Path(__file__).parent
CONTRACT = (HERE / "Button.md").read_text()
SRC_HASH = "sha256:" + hashlib.sha256(CONTRACT.encode()).hexdigest()[:16]

# --- resolved requirement set -------------------------------------------------
# scope: platforms it binds on. divergence: platforms where L2 overrides it.
MIN_TARGET = {"web": 24, "ios": 44, "android": 48}      # BTN-11, per platform standard
IDENTITY   = {"web":   {"enum": ["button", "input[type=button]", "input[type=submit]"]},
              "ios":   {"enum": ["Button"]},
              "android": {"enum": ["android.widget.Button", "androidx.compose.ui.Node"]}}

def req(cid, title):
    return {"$comment": cid, "title": title}

def schema_for(platform):
    tokens_required = ["APP-01", "APP-02", "APP-03", "APP-04", "APP-05", "APP-06", "APP-07"]
    behavior_ids = ["BTN-04", "BTN-05", "BTN-06", "BTN-09", "BTN-13"]

    # A requirement that does not bind here stays VISIBLE, marked n/a with a reason.
    # Dropping it from the schema would let a platform hide behind exclusions.
    na = {}
    if platform == "ios":
        tokens_required.remove("APP-05")
        na["APP-05"] = "L2 divergence: iOS defers to the platform's automatic pressed dimming"
    if platform != "web":
        behavior_ids.remove("BTN-13")
        na["BTN-13"] = "archetype scope: no platform-level form model exists off the web"

    def mark(cid, node):
        if cid in na:
            return {"$comment": cid, "title": node["title"], "x-not-applicable": na[cid]}
        return node

    def result_pass(cid, title):
        return mark(cid, {**req(cid, title), "type": "object", "required": ["result"],
                          "properties": {"result": {"const": "pass"}}})

    def token_slot(cid, title, slot):
        return mark(cid, {**req(cid, title), "type": "object", "required": ["slot", "literal"],
                          "properties": {"slot": {"const": slot}, "literal": {"const": False}}})

    return {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "$id": f"Button.{platform}.schema.json",
      "title": f"Button - {platform} conformance manifest",
      "description": f"GENERATED from Button.md v1.0 + button archetype v1.0 + system policy. Do not edit.",
      "x-contract": {"component": "Button", "version": "1.0", "platform": platform,
                     "source_hash": SRC_HASH},
      "type": "object",
      "required": ["contract", "platform", "sections"],
      "properties": {
        "contract": {"const": "Button"},
        "platform": {"const": platform},
        "sections": {
          "type": "object",
          "required": ["api", "tokens", "structure", "behavior"],
          "properties": {

            "api": {"type": "object", "required": ["status", "props"], "properties": {
              "props": {"type": "object",
                "required": ["label", "variant", "disabled", "iconName", "onPress"],
                "properties": {
                  "label":    {**req("API-01", "label: string, required"),
                               "properties": {"type": {"const": "string"}, "required": {"const": True}},
                               "required": ["type", "required"]},
                  "variant":  {**req("API-02", "variant: primary|secondary|ghost, optional, default primary"),
                               "properties": {"type": {"const": "enum"},
                                              "values": {"const": ["primary", "secondary", "ghost"]},
                                              "default": {"const": "primary"}},
                               "required": ["type", "values", "default"]},
                  "disabled": {**req("API-03", "disabled: boolean, optional, default false"),
                               "properties": {"type": {"const": "boolean"}, "default": {"const": False}},
                               "required": ["type", "default"]},
                  "iconName": {**req("API-04", "iconName: string, optional"),
                               "properties": {"type": {"const": "string"}, "required": {"const": False}},
                               "required": ["type"]},
                  "onPress":  {**req("API-05", "onPress: handler, required"),
                               "properties": {"required": {"const": True}}, "required": ["required"]}}}}},

            "tokens": {"type": "object", "required": ["status", "resolved", "literals_found"], "properties": {
              "resolved": {"type": "object", "required": tokens_required, "properties": {
                "APP-01": token_slot("APP-01", "background resolves through color.action.primary.bg", "color.action.primary.bg"),
                "APP-02": token_slot("APP-02", "label colour resolves through color.action.primary.fg", "color.action.primary.fg"),
                "APP-03": token_slot("APP-03", "corner radius resolves through radius.control", "radius.control"),
                "APP-04": token_slot("APP-04", "icon-label gap resolves through space.inline.sm", "space.inline.sm"),
                "APP-05": token_slot("APP-05", "pressed background resolves through color.action.primary.pressed", "color.action.primary.pressed"),
                "APP-06": token_slot("APP-06", "disabled background resolves through color.action.primary.disabled.bg", "color.action.primary.disabled.bg"),
                "APP-07": token_slot("APP-07", "disabled label colour resolves through color.action.primary.disabled.fg", "color.action.primary.disabled.fg")}},
              "literals_found": {**req("POL-04", "no literal value appears in a contract-relevant style property"),
                "type": "array", "items": {"type": "object", "required": ["exempt"],
                  "properties": {"exempt": {"const": True}}}}}},

            "structure": {"type": "object", "required": ["status", "captures"], "properties": {
              "captures": {"type": "object", "required": ["default", "disabled", "focused"], "properties": {

                "default": {"type": "object", "required": ["tree"], "properties": {"tree": {
                  "type": "object", "required": ["zone", "identity", "role", "name", "focusable", "box", "children"],
                  "properties": {
                    "zone": {"const": "root"},
                    "identity": {**req("BTN-01b", "the rendered control is a real button, not a generic element given a role"),
                                 **IDENTITY[platform]},
                    "role": {**req("BTN-01", "the control is exposed to assistive technology as a button"),
                             "anyOf": [{"const": "button"}, {"type": "null"}]},
                    "name": {**req("BTN-02", "the control has a non-empty accessible name"),
                             "type": "string", "minLength": 1},
                    "focusable": {**req("BTN-03", "the control is reachable by sequential focus navigation"),
                                  "const": True},
                    "box": {**req("BTN-11", f"the control meets the platform minimum touch-target size ({MIN_TARGET[platform]})"),
                            "type": "object", "required": ["w", "h"],
                            "properties": {"w": {"type": "number", "minimum": MIN_TARGET[platform]},
                                           "h": {"type": "number", "minimum": MIN_TARGET[platform]}}},
                    "children": {**req("CMP-03", "zones are arranged along the inline axis, icon before label"),
                                 "type": "array", "minItems": 1,
                                 "items": [{"type": "object",
                                            "properties": {"zone": {"const": "icon"},
                                                           "role": {**req("ACC-01", "the icon is decorative and contributes nothing to the accessible name"),
                                                                    "const": "none"}},
                                            "required": ["zone", "role"]},
                                           {"type": "object", "properties": {"zone": {"const": "label"}},
                                            "required": ["zone"]}]}}}}},

                "disabled": {"type": "object", "required": ["tree"], "properties": {"tree": {
                  "type": "object", "required": ["states", "focusable"], "properties": {
                    "states": {**req("BTN-10", "when disabled, that state is conveyed to assistive technology"),
                               "type": "array", "contains": {"const": "disabled"}},
                    "focusable": {**req("BTN-08", "when disabled, the control is removed from sequential focus navigation"),
                                  "const": False}}}}},

                "focused": {"type": "object", "required": ["tree"], "properties": {"tree": {
                  "type": "object", "required": ["focus_indicator"], "properties": {
                    "focus_indicator": {**req("BTN-07", "while focused, a focus indicator is distinguishable from the unfocused appearance"),
                                        "const": True}}}}}}}}},

            "behavior": {"type": "object", "required": ["status"],
              "if": {"properties": {"status": {"const": "extracted"}}},
              "then": {"required": ["checks"], "properties": {
                "checks": {"type": "object", "required": behavior_ids, "properties": {
                  "BTN-04": result_pass("BTN-04", "activating by the primary non-pointer input performs the action"),
                  "BTN-05": result_pass("BTN-05", "where a hardware keyboard exists, both standard activation keys perform the action"),
                  "BTN-06": result_pass("BTN-06", "keyboard activation does not also scroll the surrounding surface"),
                  "BTN-09": result_pass("BTN-09", "when disabled, activation performs no action"),
                  "BTN-13": result_pass("BTN-13", "the control submits its containing form without scripting")}}}}}}}}}

for p in ("web", "ios", "android"):
    out = HERE / f"Button.{p}.schema.json"
    out.write_text(json.dumps(schema_for(p), indent=2) + "\n")
    print(f"generated {out.name}")
