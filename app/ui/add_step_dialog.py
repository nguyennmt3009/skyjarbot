"""
Dialog for manually adding a Step to a scenario.
Supports: Action, Condition, Delay, Branch, SetVariable, CallScenario.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional

from app.core.models import (
    ActionStep, ActionType,
    ConditionStep, ConditionType,
    DelayStep, BranchStep, SetVariableStep, CallScenarioStep,
    Step,
)


class AddStepDialog(tk.Toplevel):
    def __init__(self, parent: tk.Widget, on_add: Callable[[Step], None]):
        super().__init__(parent)
        self.title("Add Step")
        self.resizable(False, False)
        self.grab_set()           # modal
        self._on_add = on_add
        self._result: Optional[Step] = None

        self._step_type_var = tk.StringVar(value="condition")
        self._action_type_var = tk.StringVar(value=ActionType.MOUSE_CLICK.value)
        self._cond_type_var = tk.StringVar(value=ConditionType.PIXEL_COLOR.value)

        self._build_ui()
        self._refresh_panels()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 4}

        # ── Step type selector
        top = ttk.LabelFrame(self, text="Step type")
        top.pack(fill="x", **pad)
        for value, label in [
            ("action", "Action"), ("condition", "Condition"), ("delay", "Delay"),
            ("branch", "Branch"), ("set_variable", "Set Variable"), ("call_scenario", "Call Scenario"),
        ]:
            ttk.Radiobutton(
                top, text=label, variable=self._step_type_var, value=value,
                command=self._refresh_panels,
            ).pack(side="left", padx=8, pady=4)

        # ── Dynamic content area
        self._content = ttk.Frame(self)
        self._content.pack(fill="both", expand=True, **pad)

        self._panel_action       = self._build_action_panel(self._content)
        self._panel_condition    = self._build_condition_panel(self._content)
        self._panel_delay        = self._build_delay_panel(self._content)
        self._panel_branch       = self._build_branch_panel(self._content)
        self._panel_set_variable = self._build_set_variable_panel(self._content)
        self._panel_call_scenario = self._build_call_scenario_panel(self._content)

        # ── Buttons
        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill="x", **pad)
        ttk.Button(btn_bar, text="Add", width=12, command=self._on_add_clicked).pack(side="right", padx=4)
        ttk.Button(btn_bar, text="Cancel", width=12, command=self.destroy).pack(side="right")

    # ── Action panel ──────────────────────────────────────────────────────────

    def _build_action_panel(self, parent: tk.Widget) -> ttk.LabelFrame:
        f = ttk.LabelFrame(parent, text="Action")

        ttk.Label(f, text="Action type:").grid(row=0, column=0, sticky="w", padx=6, pady=3)
        action_opts = [a.value for a in ActionType]
        cb = ttk.Combobox(f, textvariable=self._action_type_var, values=action_opts,
                          state="readonly", width=18)
        cb.grid(row=0, column=1, sticky="w", padx=6, pady=3)
        cb.bind("<<ComboboxSelected>>", lambda _: self._refresh_action_fields())

        self._action_fields_frame = ttk.Frame(f)
        self._action_fields_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=4)

        self._ax = self._field(self._action_fields_frame, "X:", 0)
        self._ay = self._field(self._action_fields_frame, "Y:", 1)
        self._a_button = self._field(self._action_fields_frame, "Button (left/right):", 2, default="left")
        self._a_key = self._field(self._action_fields_frame, "Key:", 3)
        self._a_text = self._field(self._action_fields_frame, "Text:", 4)
        self._a_dx = self._field(self._action_fields_frame, "dx (scroll):", 5, default="0")
        self._a_dy = self._field(self._action_fields_frame, "dy (scroll):", 6, default="0")

        self._action_pick_btn = ttk.Button(
            self._action_fields_frame, text="🎯 Pick point",
            command=self._pick_action_xy,
        )
        self._action_pick_btn.grid(row=0, column=2, rowspan=2, padx=6, pady=2, sticky="w")

        self._refresh_action_fields()
        return f

    def _refresh_action_fields(self) -> None:
        t = ActionType(self._action_type_var.get())
        show = {
            ActionType.MOUSE_CLICK:  ["x", "y", "button"],
            ActionType.MOUSE_MOVE:   ["x", "y"],
            ActionType.MOUSE_SCROLL: ["x", "y", "dx", "dy"],
            ActionType.KEY_PRESS:    ["key"],
            ActionType.TYPE_TEXT:    ["text"],
        }.get(t, [])
        mapping = {
            "x": self._ax, "y": self._ay, "button": self._a_button,
            "key": self._a_key, "text": self._a_text,
            "dx": self._a_dx, "dy": self._a_dy,
        }
        for key, (lbl, ent) in mapping.items():
            if key in show:
                lbl.grid()
                ent.grid()
            else:
                lbl.grid_remove()
                ent.grid_remove()
        if "x" in show:
            self._action_pick_btn.grid()
        else:
            self._action_pick_btn.grid_remove()

    # ── Condition panel ───────────────────────────────────────────────────────

    def _build_condition_panel(self, parent: tk.Widget) -> ttk.LabelFrame:
        f = ttk.LabelFrame(parent, text="Condition")

        ttk.Label(f, text="Condition type:").grid(row=0, column=0, sticky="w", padx=6, pady=3)
        cond_opts = [c.value for c in ConditionType]
        cb = ttk.Combobox(f, textvariable=self._cond_type_var, values=cond_opts,
                          state="readonly", width=18)
        cb.grid(row=0, column=1, sticky="w", padx=6, pady=3)
        cb.bind("<<ComboboxSelected>>", lambda _: self._refresh_condition_fields())

        # shared timeout/poll
        self._c_timeout = self._field(f, "Timeout (ms):", 1, default="5000")
        self._c_poll    = self._field(f, "Poll interval (ms):", 2, default="200")

        # pixel_color fields
        self._pc_frame = ttk.LabelFrame(f, text="Pixel Color")
        self._pc_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
        self._pc_x         = self._field(self._pc_frame, "X:", 0)
        self._pc_y         = self._field(self._pc_frame, "Y:", 1)
        self._pc_r         = self._field(self._pc_frame, "R:", 2, default="0")
        self._pc_g         = self._field(self._pc_frame, "G:", 3, default="0")
        self._pc_b         = self._field(self._pc_frame, "B:", 4, default="0")
        self._pc_tolerance = self._field(self._pc_frame, "Tolerance:", 5, default="10")
        ttk.Button(
            self._pc_frame, text="🎯 Pick & sample pixel",
            command=self._pick_pc_xy,
        ).grid(row=0, column=2, rowspan=2, padx=6, pady=2, sticky="w")

        # image_match fields
        self._im_frame = ttk.LabelFrame(f, text="Image Match")
        self._im_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
        self._im_path      = self._field(self._im_frame, "Template path:", 0)
        ttk.Button(self._im_frame, text="Browse…",
                   command=self._browse_template).grid(row=1, column=0, columnspan=2, pady=2)
        self._im_threshold = self._field(self._im_frame, "Match threshold (0–1):", 2, default="0.8")
        self._im_region    = self._field(self._im_frame, "Search region (x,y,w,h):", 3,
                                         default="", hint="leave blank for full screen")
        ttk.Button(
            self._im_frame, text="🎯 Pick region",
            command=self._pick_im_region,
        ).grid(row=3, column=3, padx=6, pady=2, sticky="w")

        # ocr_text fields
        self._ocr_frame = ttk.LabelFrame(f, text="OCR Text")
        self._ocr_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
        self._ocr_text     = self._field(self._ocr_frame, "Expected text:", 0)
        self._ocr_contains = tk.BooleanVar(value=True)
        ttk.Checkbutton(self._ocr_frame, text="Substring match (uncheck = exact)",
                        variable=self._ocr_contains).grid(row=1, column=0, columnspan=2, pady=2)
        self._ocr_region   = self._field(self._ocr_frame, "OCR region (x,y,w,h):", 2,
                                         default="", hint="leave blank for full screen")
        ttk.Button(
            self._ocr_frame, text="🎯 Pick region",
            command=self._pick_ocr_region,
        ).grid(row=2, column=3, padx=6, pady=2, sticky="w")

        self._refresh_condition_fields()
        return f

    def _refresh_condition_fields(self) -> None:
        ct = self._cond_type_var.get()
        self._pc_frame.grid_remove()
        self._im_frame.grid_remove()
        self._ocr_frame.grid_remove()
        if ct == ConditionType.PIXEL_COLOR.value:
            self._pc_frame.grid()
        elif ct == ConditionType.IMAGE_MATCH.value:
            self._im_frame.grid()
        elif ct == ConditionType.OCR_TEXT.value:
            self._ocr_frame.grid()

    # ── Delay panel ───────────────────────────────────────────────────────────

    def _build_delay_panel(self, parent: tk.Widget) -> ttk.LabelFrame:
        f = ttk.LabelFrame(parent, text="Delay")
        self._delay_ms = self._field(f, "Duration (ms):", 0, default="1000")
        return f

    # ── Panel visibility ──────────────────────────────────────────────────────

    def _refresh_panels(self) -> None:
        for panel in (self._panel_action, self._panel_condition, self._panel_delay,
                      self._panel_branch, self._panel_set_variable, self._panel_call_scenario):
            panel.pack_forget()
        t = self._step_type_var.get()
        panel_map = {
            "action":       self._panel_action,
            "condition":    self._panel_condition,
            "delay":        self._panel_delay,
            "branch":       self._panel_branch,
            "set_variable": self._panel_set_variable,
            "call_scenario": self._panel_call_scenario,
        }
        panel_map.get(t, self._panel_action).pack(fill="both", expand=True)
        self.update_idletasks()
        self.geometry("")   # auto-resize

    # ── Branch panel ─────────────────────────────────────────────────────────

    def _build_branch_panel(self, parent: tk.Widget) -> ttk.LabelFrame:
        f = ttk.LabelFrame(parent, text="Branch (If/Else)")
        ttk.Label(f, text="Condition type:").grid(row=0, column=0, sticky="w", padx=6, pady=3)
        self._br_cond_type = tk.StringVar(value=ConditionType.PIXEL_COLOR.value)
        cond_opts = [c.value for c in ConditionType]
        ttk.Combobox(f, textvariable=self._br_cond_type, values=cond_opts,
                     state="readonly", width=18).grid(row=0, column=1, sticky="w", padx=6)

        self._br_px = self._field(f, "X:", 1)
        self._br_py = self._field(f, "Y:", 2)
        ttk.Button(
            f, text="🎯 Pick point",
            command=self._pick_branch_xy,
        ).grid(row=1, column=2, rowspan=2, padx=6, pady=2, sticky="w")
        self._br_pr = self._field(f, "R:", 3, default="0")
        self._br_pg = self._field(f, "G:", 4, default="0")
        self._br_pb = self._field(f, "B:", 5, default="0")
        self._br_tol = self._field(f, "Tolerance:", 6, default="10")
        self._br_timeout = self._field(f, "Timeout (ms):", 7, default="5000")

        ttk.Label(f, text="on_true / on_false steps can be added\nvia JSON editing after creation.",
                  foreground="#666", justify="left").grid(row=8, column=0, columnspan=3, padx=6, pady=4)
        return f

    # ── SetVariable panel ─────────────────────────────────────────────────────

    def _build_set_variable_panel(self, parent: tk.Widget) -> ttk.LabelFrame:
        f = ttk.LabelFrame(parent, text="Set Variable")
        self._sv_name  = self._field(f, "Variable name:", 0)
        self._sv_value = self._field(f, "Value:", 1, hint="supports {other_var}")
        return f

    # ── CallScenario panel ────────────────────────────────────────────────────

    def _build_call_scenario_panel(self, parent: tk.Widget) -> ttk.LabelFrame:
        f = ttk.LabelFrame(parent, text="Call Scenario")
        self._cs_path = self._field(f, "Scenario file:", 0)
        ttk.Button(f, text="Browse…", command=self._browse_scenario).grid(
            row=1, column=0, columnspan=2, pady=4)
        return f

    def _browse_scenario(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("JSON scenarios", "*.json")],
            title="Select scenario file", parent=self,
        )
        if path:
            self._cs_path[1].delete(0, tk.END)
            self._cs_path[1].insert(0, path)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _field(
        self, parent: tk.Widget, label: str, row: int,
        default: str = "", hint: str = ""
    ) -> tuple[ttk.Label, ttk.Entry]:
        lbl = ttk.Label(parent, text=label)
        lbl.grid(row=row, column=0, sticky="w", padx=6, pady=2)
        var = tk.StringVar(value=default)
        ent = ttk.Entry(parent, textvariable=var, width=28)
        ent.grid(row=row, column=1, sticky="w", padx=6, pady=2)
        if hint:
            ttk.Label(parent, text=hint, foreground="#888", font=("TkDefaultFont", 8)
                      ).grid(row=row, column=2, sticky="w", padx=2)
        return lbl, ent

    def _int(self, widget_tuple, default: int = 0) -> int:
        try:
            return int(widget_tuple[1].get())
        except ValueError:
            return default

    def _float(self, widget_tuple, default: float = 0.0) -> float:
        try:
            return float(widget_tuple[1].get())
        except ValueError:
            return default

    def _str(self, widget_tuple) -> str:
        return widget_tuple[1].get().strip()

    def _parse_region(self, widget_tuple) -> Optional[tuple]:
        raw = self._str(widget_tuple)
        if not raw:
            return None
        try:
            parts = [int(v.strip()) for v in raw.split(",")]
            if len(parts) != 4:
                raise ValueError
            return tuple(parts)
        except ValueError:
            messagebox.showerror("Invalid region",
                                 "Region must be 4 integers: x,y,w,h", parent=self)
            return None

    # ── Screen picker ─────────────────────────────────────────────────────────

    def _open_picker(self, mode: str, on_done) -> None:
        """Hide this modal dialog, open the fullscreen picker, then restore."""
        from app.ui.screen_picker import ScreenPickerOverlay

        self.grab_release()
        self.withdraw()

        def _callback(result):
            self.deiconify()
            self.grab_set()
            on_done(result)

        # Small delay so the dialog visually disappears before the screenshot
        self.after(150, lambda: ScreenPickerOverlay(self, mode=mode, callback=_callback))

    def _pick_action_xy(self) -> None:
        def _done(result):
            if result:
                x, y = result[0], result[1]
                self._ax[1].delete(0, tk.END); self._ax[1].insert(0, str(x))
                self._ay[1].delete(0, tk.END); self._ay[1].insert(0, str(y))
        self._open_picker("point", _done)

    def _pick_pc_xy(self) -> None:
        from app.platform.screen_capture import get_pixel_color

        def _done(result):
            if result:
                x, y = result[0], result[1]
                r, g, b = get_pixel_color(x, y)
                self._pc_x[1].delete(0, tk.END); self._pc_x[1].insert(0, str(x))
                self._pc_y[1].delete(0, tk.END); self._pc_y[1].insert(0, str(y))
                self._pc_r[1].delete(0, tk.END); self._pc_r[1].insert(0, str(r))
                self._pc_g[1].delete(0, tk.END); self._pc_g[1].insert(0, str(g))
                self._pc_b[1].delete(0, tk.END); self._pc_b[1].insert(0, str(b))
        self._open_picker("point", _done)

    def _pick_im_region(self) -> None:
        def _done(result):
            if result and len(result) == 4:
                x, y, w, h = result
                self._im_region[1].delete(0, tk.END)
                self._im_region[1].insert(0, f"{x},{y},{w},{h}")
        self._open_picker("region", _done)

    def _pick_ocr_region(self) -> None:
        def _done(result):
            if result and len(result) == 4:
                x, y, w, h = result
                self._ocr_region[1].delete(0, tk.END)
                self._ocr_region[1].insert(0, f"{x},{y},{w},{h}")
        self._open_picker("region", _done)

    def _pick_branch_xy(self) -> None:
        def _done(result):
            if result:
                x, y = result[0], result[1]
                self._br_px[1].delete(0, tk.END); self._br_px[1].insert(0, str(x))
                self._br_py[1].delete(0, tk.END); self._br_py[1].insert(0, str(y))
        self._open_picker("point", _done)

    def _browse_template(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")],
            title="Select template image", parent=self,
        )
        if path:
            self._im_path[1].delete(0, tk.END)
            self._im_path[1].insert(0, path)

    # ── Build step ────────────────────────────────────────────────────────────

    def _on_add_clicked(self) -> None:
        step = self._build_step()
        if step is not None:
            self._on_add(step)
            self.destroy()

    def _build_step(self) -> Optional[Step]:
        t = self._step_type_var.get()

        if t == "delay":
            return DelayStep(duration_ms=self._int(self._delay_ms, 1000))

        if t == "action":
            at = ActionType(self._action_type_var.get())
            step = ActionStep(action_type=at)
            step.x = self._int(self._ax) if self._str(self._ax) else None
            step.y = self._int(self._ay) if self._str(self._ay) else None
            step.button = self._str(self._a_button) or "left"
            step.key = self._str(self._a_key) or None
            step.text = self._str(self._a_text) or None
            step.dx = self._int(self._a_dx)
            step.dy = self._int(self._a_dy)
            return step

        if t == "condition":
            ct = ConditionType(self._cond_type_var.get())
            timeout = self._int(self._c_timeout, 5000)
            poll    = self._int(self._c_poll, 200)

            if ct == ConditionType.PIXEL_COLOR:
                return ConditionStep(
                    condition_type=ct,
                    x=self._int(self._pc_x),
                    y=self._int(self._pc_y),
                    expected_color=(
                        self._int(self._pc_r),
                        self._int(self._pc_g),
                        self._int(self._pc_b),
                    ),
                    tolerance=self._int(self._pc_tolerance, 10),
                    timeout_ms=timeout,
                    poll_interval_ms=poll,
                )

            if ct == ConditionType.IMAGE_MATCH:
                path = self._str(self._im_path)
                if not path:
                    messagebox.showerror("Missing field", "Template path is required.", parent=self)
                    return None
                region = self._parse_region(self._im_region)
                return ConditionStep(
                    condition_type=ct,
                    template_path=path,
                    match_threshold=self._float(self._im_threshold, 0.8),
                    search_region=region,
                    timeout_ms=timeout,
                    poll_interval_ms=poll,
                )

            if ct == ConditionType.OCR_TEXT:
                text = self._str(self._ocr_text)
                if not text:
                    messagebox.showerror("Missing field", "Expected text is required.", parent=self)
                    return None
                region = self._parse_region(self._ocr_region)
                return ConditionStep(
                    condition_type=ct,
                    expected_text=text,
                    ocr_contains=self._ocr_contains.get(),
                    ocr_region=region,
                    timeout_ms=timeout,
                    poll_interval_ms=poll,
                )

        if t == "branch":
            ct = ConditionType(self._br_cond_type.get())
            condition = ConditionStep(
                condition_type=ct,
                x=self._int(self._br_px),
                y=self._int(self._br_py),
                expected_color=(self._int(self._br_pr), self._int(self._br_pg), self._int(self._br_pb)),
                tolerance=self._int(self._br_tol, 10),
                timeout_ms=self._int(self._br_timeout, 5000),
            )
            return BranchStep(condition=condition)

        if t == "set_variable":
            name = self._str(self._sv_name)
            if not name:
                messagebox.showerror("Missing field", "Variable name is required.", parent=self)
                return None
            return SetVariableStep(name=name, value=self._str(self._sv_value))

        if t == "call_scenario":
            path = self._str(self._cs_path)
            if not path:
                messagebox.showerror("Missing field", "Scenario file path is required.", parent=self)
                return None
            return CallScenarioStep(scenario_path=path)

        return None
