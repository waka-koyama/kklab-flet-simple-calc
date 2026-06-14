import json, copy, asyncio
import flet as ft
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

SAVE_FILE = Path(__file__).parent / "data.json"

try:
    from flet_js import _getLocalStorage, _setLocalStorage
    _STORE_KEY = "job_app_data"
    async def _save_storage(data):
        await _setLocalStorage(_STORE_KEY, json.dumps(data, ensure_ascii=False))
    async def _load_storage():
        val = await _getLocalStorage(_STORE_KEY)
        if val is None:
            return None
        return json.loads(str(val))
except (ImportError, AttributeError):
    async def _save_storage(data): pass
    async def _load_storage(): return None

INDUSTRIES = {
    "IT・Web":       {"color": ft.Colors.BLUE_400,   "emoji": "💻"},
    "金融・保険":     {"color": ft.Colors.GREEN_400,  "emoji": "💴"},
    "商社":           {"color": ft.Colors.ORANGE_400, "emoji": "🌐"},
    "メーカー":       {"color": ft.Colors.CYAN_400,   "emoji": "🏭"},
    "マスコミ・広告":  {"color": ft.Colors.PINK_400,   "emoji": "📺"},
    "コンサル":       {"color": ft.Colors.PURPLE_400, "emoji": "📊"},
    "インフラ":       {"color": ft.Colors.BROWN_400,  "emoji": "🔧"},
    "食品":           {"color": ft.Colors.AMBER_400,  "emoji": "🍱"},
    "その他":         {"color": ft.Colors.GREY_400,   "emoji": "🏢"},
}

MAIN_STATUSES = ["ホームページ作成済み", "選考中", "一次面接", "二次面接", "最終面接", "内定", "お祈り", "その他（自由記入）"]
MAIN_STATUS_COLORS = {
    "ホームページ作成済み": ft.Colors.LIGHT_BLUE_300,
    "選考中":             ft.Colors.ORANGE_300,
    "一次面接":           ft.Colors.ORANGE_300,
    "二次面接":           ft.Colors.ORANGE_400,
    "最終面接":           ft.Colors.DEEP_ORANGE_400,
    "内定":               ft.Colors.GREEN_400,
    "お祈り":             ft.Colors.GREY_600,
    "その他（自由記入）":   ft.Colors.GREY_400,
}

TAG_GROUPS = [
    {"label": "ES", "options": ["なし", "未提出", "提出済み"]},
    {"label": "適性検査", "options": ["なし", "未受験", "受験済み"]},
    {"label": "性格検査", "options": ["なし", "未受験", "受験済み"]},
]
TAG_GROUP_COLORS = {
    "ES":     ft.Colors.BLUE_200,
    "適性検査": ft.Colors.INDIGO_200,
    "性格検査": ft.Colors.PURPLE_200,
}

SCHEDULE_TYPES = ["ES提出", "適性検査締切", "面接案内", "インターン", "選考", "その他"]
SCHEDULE_ICONS = {
    "ES提出":     "📋",
    "適性検査締切": "📝",
    "面接案内":   "📬",
    "インターン": "🏢",
    "選考":       "📅",
    "その他":     "🗓",
}
INTERN_STATES = ["希望", "確定", "不参加"]


def fmt(d: date) -> str:
    return d.strftime("%Y/%m/%d")

def countdown(d: date) -> str:
    delta = (d - date.today()).days
    if delta < 0:   return f"{fmt(d)} 経過"
    if delta == 0:  return f"🔥 今日！({fmt(d)})"
    return f"⏳ あと {delta} 日 ({fmt(d)})"


def schedule_to_dict(s: dict) -> dict:
    out = {"type": s["type"]}
    if s["type"] == "インターン":
        out["start"] = s["start"].isoformat() if s.get("start") else None
        out["end"]   = s["end"].isoformat()   if s.get("end")   else None
        out["state"] = s.get("state", "希望")
    else:
        out["date"] = s["date"].isoformat() if s.get("date") else None
    return out

def schedule_from_dict(d: dict) -> dict:
    def p(s): return date.fromisoformat(s) if s else None
    if d["type"] == "インターン":
        return {"type": "インターン", "start": p(d.get("start")), "end": p(d.get("end")), "state": d.get("state", "希望")}
    return {"type": d["type"], "date": p(d.get("date"))}


def _make_display_view(task: "Task") -> ft.Container:
    info = INDUSTRIES[task.industry]
    color = info["color"]
    emoji = info["emoji"]

    badges = [ft.Container(
        content=ft.Text(task.display_main_status, size=11, color=ft.Colors.WHITE),
        bgcolor=MAIN_STATUS_COLORS.get(task.main_status, ft.Colors.GREY_400),
        padding=ft.Padding(left=8, right=8, top=2, bottom=2),
        border_radius=10,
    )]
    for group_label, option in task.tag_groups.items():
        badges.append(ft.Container(
            content=ft.Text(f"{group_label}:{option}", size=11, color=ft.Colors.WHITE),
            bgcolor=TAG_GROUP_COLORS.get(group_label, ft.Colors.GREY_400),
            padding=ft.Padding(left=8, right=8, top=2, bottom=2),
            border_radius=10,
        ))
    if task.custom_tag:
        badges.append(ft.Container(
            content=ft.Text(task.custom_tag, size=11, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREY_400,
            padding=ft.Padding(left=8, right=8, top=2, bottom=2),
            border_radius=10,
        ))
    for s in task.schedules:
        if s["type"] == "インターン" and s.get("state") == "確定" and s.get("start"):
            label = f"🏢 {fmt(s['start'])}"
            if s.get("end"):
                label += f"〜{fmt(s['end'])}"
            badges.append(ft.Container(
                content=ft.Text(label, size=11, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.TEAL_400,
                padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                border_radius=10,
            ))

    memo_text = None
    if task.memo:
        memo_text = ft.Text(task.memo[:40] + ("…" if len(task.memo) > 40 else ""),
                            size=10, color=ft.Colors.GREY_400, italic=True, no_wrap=True,
                            overflow=ft.TextOverflow.ELLIPSIS)

    date_lines = []
    if memo_text:
        date_lines.append(memo_text)
    for s in task.schedules:
        icon = SCHEDULE_ICONS.get(s["type"], "🗓")
        if s["type"] == "インターン":
            state = s.get("state", "希望")
            start = s.get("start")
            end   = s.get("end")
            if start:
                label = f"{icon} インターン[{state}] {fmt(start)}"
                if end:
                    label += f"〜{fmt(end)}"
                color_map = {"希望": ft.Colors.GREY_500, "確定": ft.Colors.TEAL_300, "不参加": ft.Colors.GREY_400}
                date_lines.append(ft.Text(label, size=12,
                                          color=color_map.get(state, ft.Colors.GREY_500),
                                          italic=(state == "不参加")))
        else:
            if s.get("date"):
                date_lines.append(ft.Text(
                    f"{icon} {s['type']} {countdown(s['date'])}",
                    size=12, color=ft.Colors.GREY_500))

    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(spacing=4, controls=[
                    ft.Row(spacing=6, controls=[
                        ft.Text(f"{emoji} {task.industry}", size=11, color=color, weight=ft.FontWeight.BOLD),
                        *badges,
                    ]),
                    task.display_task,
                    *date_lines,
                ]),
                ft.Row(spacing=0, controls=[
                    ft.IconButton(ft.Icons.CREATE_OUTLINED, tooltip="編集", on_click=task.edit_clicked),
                    ft.IconButton(ft.Icons.DELETE_OUTLINE,  tooltip="削除", on_click=task.delete_clicked),
                ]),
            ],
        ),
        border=ft.Border.only(left=ft.border.BorderSide(4, color)),
        padding=ft.Padding(left=8, top=6, bottom=6, right=0),
        border_radius=4,
    )


class Task(ft.Column):
    def __init__(self, company, industry, main_status, tag_groups=None, task_delete=None, task_save=None,
                 schedules=None, memo="", custom_main_status="", custom_tag="", created_at=""):
        super().__init__()
        self.company = company
        self.industry = industry
        self.main_status = main_status
        self.tag_groups = dict(tag_groups) if tag_groups else {}
        self.custom_main_status = custom_main_status or ""
        self.custom_tag = custom_tag or ""
        self.schedules = schedules or []
        self.memo = memo or ""
        self.task_delete = task_delete
        self.task_save = task_save
        self.created_at = created_at or datetime.now().isoformat()
        self._completed = self.main_status in ("内定", "お祈り")
        self.display_main_status = self._resolve_display_main_status()

    def _resolve_display_main_status(self):
        if self.main_status == "その他（自由記入）" and self.custom_main_status:
            return self.custom_main_status
        return self.main_status

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, value):
        self._completed = value

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "industry": self.industry,
            "main_status": self.main_status,
            "custom_main_status": self.custom_main_status,
            "tag_groups": dict(self.tag_groups),
            "custom_tag": self.custom_tag,
            "completed": self.completed,
            "schedules": [schedule_to_dict(s) for s in self.schedules],
            "memo": self.memo,
            "created_at": self.created_at,
        }

    def build(self):
        self.display_task = ft.Checkbox(
            value=self.completed, label=self.company, on_change=self.status_changed)
        self.controls = [_make_display_view(self)]

    def refresh(self):
        self._completed = self.main_status in ("内定", "お祈り")
        self.display_main_status = self._resolve_display_main_status()
        self.display_task.label = self.company
        self.display_task.value = self.completed
        self.controls = [_make_display_view(self)]
        if self.page:
            self.update()

    def edit_clicked(self, e):
        name_field = ft.TextField(label="企業名", value=self.company, expand=True)
        industry_dd = ft.Dropdown(
            label="業界", value=self.industry, width=160,
            options=[ft.dropdown.Option(k) for k in INDUSTRIES],
        )
        main_status_dd = ft.Dropdown(
            label="選考状況", value=self.main_status, width=200,
            options=[ft.dropdown.Option(s) for s in MAIN_STATUSES],
        )
        custom_main_field = ft.TextField(
            label="その他（自由記入）", value=self.custom_main_status,
            visible=(self.main_status == "その他（自由記入）"),
            expand=True,
        )

        def on_main_status_change(e):
            custom_main_field.visible = (main_status_dd.value == "その他（自由記入）")
            self.page.update()
        main_status_dd.on_select = on_main_status_change

        group_sel = dict(self.tag_groups)
        all_btns = []
        group_rows = []
        for g in TAG_GROUPS:
            label = g["label"]
            opts = g["options"]
            row_ctrls = [ft.Text(f"{label}：", size=12, weight=ft.FontWeight.BOLD)]
            for opt in opts:
                selected = group_sel.get(label) == opt
                btn = ft.TextButton(
                    content=ft.Text(opt, size=12),
                    data=(label, opt),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_400 if selected else ft.Colors.GREY_200,
                        color=ft.Colors.WHITE if selected else ft.Colors.BLACK,
                    ),
                    on_click=lambda e, lbl=label, o=opt: _select_group(lbl, o),
                )
                all_btns.append(btn)
                row_ctrls.append(btn)
            group_rows.append(ft.Row(spacing=4, controls=row_ctrls))

        def _select_group(lbl, opt):
            group_sel[lbl] = opt
            for btn in all_btns:
                b_lbl, b_opt = btn.data
                sel = group_sel.get(b_lbl) == b_opt
                btn.style = ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_400 if sel else ft.Colors.GREY_200,
                    color=ft.Colors.WHITE if sel else ft.Colors.BLACK,
                )
            self.page.update()

        tag_column = ft.Column(spacing=4, controls=group_rows)

        custom_tag_field = ft.TextField(
            label="その他（自由記入）", value=self.custom_tag,
            expand=True,
        )

        sched_data = copy.deepcopy(self.schedules)
        sched_col = ft.Column(spacing=6)
        picker_ctx = {"idx": 0, "field": "date"}

        def on_pick(e):
            if not date_picker.value:
                return
            v = date_picker.value
            if isinstance(v, datetime):
                d = v.replace(tzinfo=timezone.utc).astimezone().date()
            else:
                d = v
            sched_data[picker_ctx["idx"]][picker_ctx["field"]] = d
            _rebuild()
            self.page.update()

        date_picker = ft.DatePicker(on_change=on_pick, on_dismiss=on_pick)

        def open_picker(idx, field):
            picker_ctx["idx"] = idx
            picker_ctx["field"] = field
            self.page.show_dialog(date_picker)

        def _rebuild():
            sched_col.controls = [_row(i, s) for i, s in enumerate(sched_data)]
            if sched_col.page:
                sched_col.update()

        def _row(i, s):
            type_dd = ft.Dropdown(
                value=s["type"], width=130,
                options=[ft.dropdown.Option(t) for t in SCHEDULE_TYPES],
                on_select=lambda e, i=i: (_type_change(i, e.control.value)),
            )
            ctrls = [type_dd]
            if s["type"] == "インターン":
                ctrls += [
                    ft.TextButton(fmt(s["start"]) if s.get("start") else "開始日",
                                  on_click=lambda e, i=i: open_picker(i, "start")),
                    ft.Text("〜"),
                    ft.TextButton(fmt(s["end"]) if s.get("end") else "終了日",
                                  on_click=lambda e, i=i: open_picker(i, "end")),
                    ft.Dropdown(
                        value=s.get("state", "希望"), width=90,
                        options=[ft.dropdown.Option(st) for st in INTERN_STATES],
                        on_select=lambda e, i=i: sched_data[i].update({"state": e.control.value}),
                    ),
                ]
            else:
                ctrls.append(ft.TextButton(
                    fmt(s["date"]) if s.get("date") else "日付を選択",
                    on_click=lambda e, i=i: open_picker(i, "date")))
            ctrls.append(ft.IconButton(ft.Icons.CLOSE, icon_size=16,
                                       on_click=lambda e, i=i: (_remove(i))))
            return ft.Row(controls=ctrls, wrap=True, spacing=4)

        def _type_change(i, new_type):
            if new_type == "インターン":
                sched_data[i] = {"type": "インターン", "start": None, "end": None, "state": "希望"}
            else:
                sched_data[i] = {"type": new_type, "date": None}
            _rebuild()
            self.page.update()

        def _remove(i):
            sched_data.pop(i)
            _rebuild()
            self.page.update()

        def _add(e):
            sched_data.append({"type": "ES提出", "date": None})
            _rebuild()
            self.page.update()

        sched_col.controls = [_row(i, s) for i, s in enumerate(sched_data)]

        memo_field = ft.TextField(label="メモ・備考", value=self.memo, multiline=True, min_lines=2, max_lines=4)

        def save(e):
            self.company = name_field.value
            self.industry = industry_dd.value
            self.main_status = main_status_dd.value
            self.custom_main_status = custom_main_field.value if main_status_dd.value == "その他（自由記入）" else ""
            self.tag_groups = {k: v for k, v in group_sel.items() if v}
            self.custom_tag = custom_tag_field.value or ""
            self.schedules = sched_data
            self.memo = memo_field.value or ""
            self._completed = main_status_dd.value in ("内定", "お祈り")
            dlg.open = False
            self.page.update()
            self.refresh()
            if self.task_save:
                self.task_save()
            self.page.update()

        def cancel(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("企業情報を編集"),
            content=ft.Column(spacing=10, width=420, scroll=ft.ScrollMode.AUTO, controls=[
                name_field,
                ft.Row(wrap=True, spacing=8, controls=[industry_dd, main_status_dd]),
                custom_main_field,
                ft.Divider(),
                ft.Text("タグ（複数選択可）", weight=ft.FontWeight.BOLD),
                tag_column,
                custom_tag_field,
                ft.Divider(),
                ft.Text("日程", weight=ft.FontWeight.BOLD),
                sched_col,
                ft.TextButton("＋ 日程を追加", on_click=_add),
                ft.Divider(),
                memo_field,
            ]),
            actions=[
                ft.TextButton("保存", on_click=save),
                ft.TextButton("キャンセル", on_click=cancel),
            ],
        )
        self.page.show_dialog(dlg)

    def status_changed(self, e):
        self._completed = self.display_task.value
        if self.task_save:
            self.task_save()
        self.update()

    def delete_clicked(self, e):
        self.task_delete(self)


class TodoApp(ft.Column):
    def build(self):
        self.company_input = ft.TextField(hint_text="企業名を入力…", on_submit=self.add_clicked, expand=True)
        self.industry_dd = ft.Dropdown(
            value="IT・Web", width=130, label="業界",
            options=[ft.dropdown.Option(k) for k in INDUSTRIES],
        )
        self.add_main_status_dd = ft.Dropdown(
            value="", width=150, label="選考状況（任意）",
            options=[ft.dropdown.Option("")] + [ft.dropdown.Option(s) for s in MAIN_STATUSES],
        )
        self.add_group_sel = {}
        self.add_group_rows = []
        for g in TAG_GROUPS:
            label = g["label"]
            opts = g["options"]
            row_ctrls = [ft.Text(f"{label}：", size=12, color=ft.Colors.GREY_500)]
            for opt in opts:
                btn = ft.TextButton(
                    content=ft.Text(opt, size=12),
                    data=(label, opt),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.GREY_200,
                        color=ft.Colors.BLACK,
                    ),
                    on_click=lambda e, lbl=label, o=opt: self._toggle_add_group(lbl, o),
                )
                row_ctrls.append(btn)
            self.add_group_rows.append(ft.Row(spacing=4, controls=row_ctrls))
        self.tasks = ft.Column()
        self.filter = ft.TabBar(
            scrollable=False,
            tabs=[ft.Tab(label="すべて"), ft.Tab(label="選考中"), ft.Tab(label="終了"), ft.Tab(label="カレンダー")],
        )
        self.filter_tabs = ft.Tabs(length=4, selected_index=0, on_change=self._on_tab_change, content=self.filter)
        self.items_left = ft.Text("0 社選考中")
        self.stats_text = ft.Text("", size=12, color=ft.Colors.GREY_500)
        self.save_indicator = ft.Text("", size=11, color=ft.Colors.GREEN_600)
        self.save_btn = ft.FilledTonalButton("保存", on_click=self._save_all_clicked)

        # Filter / Sort controls
        self.filter_industry = ft.Dropdown(
            value="すべて", width=120, label="業界",
            options=[ft.dropdown.Option("すべて")] + [ft.dropdown.Option(k) for k in INDUSTRIES],
        )
        self.filter_main_status = ft.Dropdown(
            value="すべて", width=140, label="メイン状況",
            options=[ft.dropdown.Option("すべて")] + [ft.dropdown.Option(s) for s in MAIN_STATUSES],
        )
        tag_filter_opts = ["すべて"]
        for g in TAG_GROUPS:
            for opt in g["options"]:
                tag_filter_opts.append(f"{g['label']}:{opt}")
        self.filter_tag = ft.Dropdown(
            value="すべて", width=140, label="タグ",
            options=[ft.dropdown.Option(t) for t in tag_filter_opts],
        )
        self.sort_by = ft.Dropdown(
            value="追加日時順（新しい）", width=180, label="並び替え",
            options=[
                ft.dropdown.Option("追加日時順（新しい）"),
                ft.dropdown.Option("追加日時順（古い）"),
                ft.dropdown.Option("企業名順（昇順）"),
                ft.dropdown.Option("企業名順（降順）"),
                ft.dropdown.Option("業界順"),
                ft.dropdown.Option("メインステータス順"),
                ft.dropdown.Option("期限日順（近い）"),
            ],
        )
        self.filter_industry.on_select = lambda e: self.update()
        self.filter_main_status.on_select = lambda e: self.update()
        self.filter_tag.on_select = lambda e: self.update()
        self.sort_by.on_select = lambda e: self.update()

        # Calendar
        self._cal_view_mode = "month"
        self._calendar_ref = date.today()
        self.calendar_month_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
        self.calendar_prev = ft.IconButton(ft.Icons.NAVIGATE_BEFORE, on_click=self._cal_prev)
        self.calendar_next = ft.IconButton(ft.Icons.NAVIGATE_NEXT, on_click=self._cal_next)
        self.cal_today_btn = ft.TextButton("📅 今日", on_click=self._cal_today)
        self.calendar_grid = ft.Column(spacing=1)
        self.cal_mode_selector = ft.SegmentedButton(
            selected=["month"],
            on_change=self._on_cal_mode_change,
            segments=[
                ft.Segment(value="month", label=ft.Text("月")),
                ft.Segment(value="week",  label=ft.Text("週")),
                ft.Segment(value="list",  label=ft.Text("リスト")),
            ],
        )

        self._search_query = ""
        self._search_dirty = False
        self.search_input = ft.TextField(
            hint_text="🔍 企業名を検索…", expand=True, height=36,
            on_change=self._on_search_change, prefix_icon=ft.Icons.SEARCH,
        )
        self.search_clear = ft.IconButton(ft.Icons.CLEAR, visible=False, on_click=self._clear_search)

        self.task_list_view = ft.Column(spacing=10, controls=[
            ft.Row(vertical_alignment=ft.CrossAxisAlignment.CENTER,
                   controls=[self.search_input, self.search_clear]),
            self.tasks,
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[self.items_left,
                           ft.Row(spacing=6, controls=[self.save_btn, self.save_indicator]),
                           ft.OutlinedButton(content="終了分を削除", on_click=self.clear_clicked)],
            ),
        ])
        self.calendar_view = ft.Column(spacing=10, visible=False, controls=[
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[self.cal_mode_selector]),
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[
                self.calendar_prev, self.calendar_month_text, self.calendar_next, self.cal_today_btn,
            ]),
            ft.Container(content=self.calendar_grid, padding=ft.Padding(left=4, top=0, right=4, bottom=0)),
        ])

        self.width = 640
        self.controls = [
            ft.Row([ft.Text("📝 就活記録", theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM)],
                   alignment=ft.MainAxisAlignment.CENTER),
            self.stats_text,
            ft.Row(controls=[self.company_input, self.industry_dd, self.add_main_status_dd,
                              ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=self.add_clicked)]),
            ft.Column(spacing=2, controls=self.add_group_rows),
            ft.Column(spacing=25, controls=[
                self.filter_tabs,
                ft.Row(wrap=True, spacing=6, controls=[
                    self.filter_industry, self.filter_main_status, self.filter_tag, self.sort_by,
                ]),
                self.task_list_view,
                self.calendar_view,
            ]),
        ]

    def did_mount(self):
        self.page.update()
        asyncio.ensure_future(self._load())

    def _save(self):
        data = [t.to_dict() for t in self.tasks.controls]
        asyncio.ensure_future(_save_storage(data))
        SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.save_indicator.value = f"💾 {datetime.now().strftime('%H:%M')} 保存"
        self.update()

    def _save_all_clicked(self, e):
        self._save()

    def _on_tab_change(self, e):
        self.update()

    def _on_filter_change(self, e):
        self.update()

    def _toggle_add_group(self, label, opt):
        self.add_group_sel[label] = opt
        for row in self.add_group_rows:
            for c in row.controls[1:]:
                if isinstance(c, ft.TextButton):
                    b_lbl, b_opt = c.data
                    sel = self.add_group_sel.get(b_lbl) == b_opt
                    c.style = ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_400 if sel else ft.Colors.GREY_200,
                        color=ft.Colors.WHITE if sel else ft.Colors.BLACK,
                    )
        self.update()

    def _on_cal_mode_change(self, e):
        modes = self.cal_mode_selector.selected
        if modes:
            self._cal_view_mode = modes[0]
        self._update_calendar()
        self.update()

    def _cal_today(self, e):
        self._calendar_ref = date.today()
        self._update_calendar()
        self.update()

    def _cal_prev(self, e):
        if self._cal_view_mode == "month":
            m = self._calendar_ref.month - 1
            y = self._calendar_ref.year
            if m < 1:
                m = 12; y -= 1
            self._calendar_ref = self._calendar_ref.replace(year=y, month=m)
        elif self._cal_view_mode == "week":
            self._calendar_ref -= timedelta(days=7)
        elif self._cal_view_mode == "list":
            self._calendar_ref -= timedelta(days=30)
        self._update_calendar()
        self.update()

    def _cal_next(self, e):
        if self._cal_view_mode == "month":
            m = self._calendar_ref.month + 1
            y = self._calendar_ref.year
            if m > 12:
                m = 1; y += 1
            self._calendar_ref = self._calendar_ref.replace(year=y, month=m)
        elif self._cal_view_mode == "week":
            self._calendar_ref += timedelta(days=7)
        elif self._cal_view_mode == "list":
            self._calendar_ref += timedelta(days=30)
        self._update_calendar()
        self.update()

    def _build_sched_map(self):
        sched_map = {}
        for task in self.tasks.controls:
            for s in task.schedules:
                if s["type"] == "インターン":
                    st = s.get("start")
                    en = s.get("end") or st
                    if st:
                        d = st
                        while d <= en:
                            sched_map.setdefault(d, []).append((task.company, s))
                            d += timedelta(days=1)
                else:
                    dt = s.get("date")
                    if dt:
                        sched_map.setdefault(dt, []).append((task.company, s))
        return sched_map

    def _show_date_schedule(self, d, scheds):
        if not scheds:
            return
        lines = []
        for company, s in scheds:
            icon = SCHEDULE_ICONS.get(s["type"], "🗓")
            if s["type"] == "インターン":
                if s.get("start"):
                    label = f"{icon} {company}: インターン {fmt(s['start'])}"
                    if s.get("end"):
                        label += f"〜{fmt(s['end'])}"
                    label += f" [{s.get('state', '希望')}]"
                else:
                    label = f"{icon} {company}: インターン（日程未定）"
            else:
                if s.get("date"):
                    label = f"{icon} {company}: {s['type']} {countdown(s['date'])}"
                else:
                    label = f"{icon} {company}: {s['type']}（日程未定）"
            lines.append(ft.Text(label, size=13))

        dow = ["月", "火", "水", "木", "金", "土", "日"][d.weekday()]
        dlg = ft.AlertDialog(
            title=ft.Text(f"📅 {fmt(d)}（{dow}）"),
            content=ft.Column(spacing=6, controls=lines),
            actions=[ft.TextButton("閉じる", on_click=lambda e: self._close_dialog(dlg))],
        )
        self.page.show_dialog(dlg)

    def _close_dialog(self, dlg):
        dlg.open = False
        self.page.update()

    def _on_search_change(self, e):
        self._search_query = (e.control.value or "").strip()
        self.search_clear.visible = bool(self._search_query)
        self._search_dirty = True
        self.update()

    def _clear_search(self, e):
        self._search_query = ""
        self.search_input.value = ""
        self.search_clear.visible = False
        self._search_dirty = True
        self.update()

    def _update_calendar(self):
        if self._cal_view_mode == "month":
            self._update_calendar_month()
        elif self._cal_view_mode == "week":
            self._update_calendar_week()
        elif self._cal_view_mode == "list":
            self._update_calendar_list()

    def _day_cell(self, d, scheds, is_today, highlight=True):
        lines = []
        for company, s in scheds[:3]:
            icon = SCHEDULE_ICONS.get(s["type"], "🗓")
            lines.append(ft.Text(f"{icon}{company[:5]}", size=9, no_wrap=True,
                                 overflow=ft.TextOverflow.ELLIPSIS))
        if len(scheds) > 3:
            lines.append(ft.Text(f"+{len(scheds)-3}件", size=9, color=ft.Colors.GREY_500))
        return ft.Container(
            content=ft.Column(spacing=1, controls=[
                ft.Container(
                    content=ft.Text(str(d.day), size=10,
                                    weight=ft.FontWeight.BOLD if is_today else None,
                                    color=ft.Colors.WHITE if is_today else None),
                    width=20, height=20, border_radius=10,
                    bgcolor=ft.Colors.BLUE_400 if is_today else None,
                    alignment=ft.Alignment.CENTER,
                ),
                *lines,
            ]),
            width=85, height=72,
            border=ft.Border.all(0.5, ft.Colors.GREY_300),
            padding=ft.Padding(left=2, top=2, right=2, bottom=2),
            on_click=lambda e, d=d, s=scheds: self._show_date_schedule(d, s),
        )

    def _update_calendar_month(self):
        year, month = self._calendar_ref.year, self._calendar_ref.month
        self.calendar_month_text.value = f"{year}年{month}月"
        first_day = date(year, month, 1)
        start_offset = first_day.weekday()
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        num_days = last_day.day
        sched_map = self._build_sched_map()
        today = date.today()
        day_names = ["月", "火", "水", "木", "金", "土", "日"]
        rows = [ft.Row(controls=[
            ft.Container(ft.Text(n, size=11, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                         width=85, height=24, alignment=ft.Alignment.CENTER,
                         bgcolor=ft.Colors.GREY_100 if i >= 5 else None)
            for i, n in enumerate(day_names)
        ])]
        cells = []
        for _ in range(start_offset):
            cells.append(ft.Container(width=85, height=72))
        for day_num in range(1, num_days + 1):
            d = date(year, month, day_num)
            cells.append(self._day_cell(d, sched_map.get(d, []), d == today))
        while len(cells) % 7 != 0:
            cells.append(ft.Container(width=85, height=72))
        for i in range(0, len(cells), 7):
            rows.append(ft.Row(controls=cells[i:i+7]))
        self.calendar_grid.controls = rows

    def _update_calendar_week(self):
        week_start = self._calendar_ref - timedelta(days=self._calendar_ref.weekday())
        self.calendar_month_text.value = f"{week_start.year}年{week_start.month}月 第{(week_start.day - 1) // 7 + 1}週"
        sched_map = self._build_sched_map()
        today = date.today()
        day_names = ["月", "火", "水", "木", "金", "土", "日"]
        rows = [ft.Row(controls=[
            ft.Container(ft.Text(n, size=11, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                         width=85, height=24, alignment=ft.Alignment.CENTER,
                         bgcolor=ft.Colors.GREY_100 if i >= 5 else None)
            for i, n in enumerate(day_names)
        ])]
        cells = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            cells.append(self._day_cell(d, sched_map.get(d, []), d == today))
        rows.append(ft.Row(controls=cells))
        self.calendar_grid.controls = rows

    def _update_calendar_list(self):
        self.calendar_month_text.value = "日程一覧"
        items = []
        for task in self.tasks.controls:
            for s in task.schedules:
                items.append((task, s))
        def sort_key(item):
            task, s = item
            if s["type"] == "インターン":
                return s.get("start") or date.max
            return s.get("date") or date.max
        items.sort(key=sort_key)

        if not items:
            self.calendar_grid.controls = [ft.Text("予定が登録されていません", size=14, color=ft.Colors.GREY_400)]
            return

        lines = []
        for task, s in items:
            icon = SCHEDULE_ICONS.get(s["type"], "🗓")
            color = INDUSTRIES[task.industry]["color"]
            if s["type"] == "インターン":
                if s.get("start"):
                    detail = f"{fmt(s['start'])}"
                    if s.get("end"):
                        detail += f"〜{fmt(s['end'])}"
                    detail += f" [{s.get('state', '希望')}]"
                else:
                    detail = "日程未定"
            else:
                detail = countdown(s["date"]) if s.get("date") else "日程未定"
            lines.append(ft.Container(
                content=ft.Row(controls=[
                    ft.Text(f"{icon} {task.company}", size=13, weight=ft.FontWeight.BOLD, color=color),
                    ft.Text(f"{s['type']} {detail}", size=12, color=ft.Colors.GREY_500),
                ]),
                padding=ft.Padding(left=8, top=4, right=8, bottom=4),
                border=ft.border.only(bottom=ft.border.BorderSide(0.5, ft.Colors.GREY_300)),
            ))
        self.calendar_grid.controls = [ft.Column(spacing=2, controls=lines)]

    async def _load(self):
        if self.tasks.controls:
            return
        data = None
        for _ in range(3):
            try:
                data = await _load_storage()
                if data is not None:
                    break
            except Exception:
                pass
            await asyncio.sleep(0.3)
        if data is None:
            self.page.update()
            return
        for d in data:
            if "schedules" in d:
                schedules = [schedule_from_dict(s) for s in d["schedules"]]
            else:
                def p(s): return date.fromisoformat(s) if s else None
                schedules = []
                if d.get("exam_date"):
                    schedules.append({"type": "選考", "date": p(d["exam_date"])})
                if d.get("intern_start"):
                    schedules.append({"type": "インターン", "start": p(d["intern_start"]),
                                      "end": p(d.get("intern_end")), "state": "確定"})

            if "main_status" in d:
                main_status = d["main_status"]
                tag_groups = d.get("tag_groups", {})
                custom_main_status = d.get("custom_main_status", "")
                custom_tag = d.get("custom_tag", "")
                created_at = d.get("created_at", "")
                # backward compat: convert old tags list
                if not tag_groups and "tags" in d:
                    old_tags = d["tags"]
                    for ot in old_tags:
                        for g in TAG_GROUPS:
                            for opt in g["options"]:
                                if ot.endswith(opt) or ot == g["label"] + opt:
                                    tag_groups[g["label"]] = opt
            else:
                old_status = d.get("status", "ホームページ作成済み")
                main_status = old_status if old_status in MAIN_STATUSES else "ホームページ作成済み"
                tag_groups = {}
                custom_main_status = ""
                custom_tag = ""
                created_at = ""

            task = Task(
                company=d["company"],
                industry=d.get("industry", "その他"),
                main_status=main_status,
                tag_groups=tag_groups,
                custom_main_status=custom_main_status,
                custom_tag=custom_tag,
                schedules=schedules,
                task_delete=self.task_delete,
                task_save=self._save,
                memo=d.get("memo", ""),
                created_at=created_at,
            )
            task.completed = d.get("completed", False) or main_status in ("内定", "お祈り")
            self.tasks.controls.append(task)
        if self.tasks.controls:
            self.save_indicator.value = "💾 保存済み"
        self.page.update()

    async def add_clicked(self, e):
        if not self.company_input.value:
            return
        main_status = self.add_main_status_dd.value or "ホームページ作成済み"
        task = Task(
            company=self.company_input.value,
            industry=self.industry_dd.value,
            main_status=main_status,
            tag_groups={k: v for k, v in self.add_group_sel.items() if v},
            schedules=[],
            task_delete=self.task_delete,
            task_save=self._save,
        )
        self.tasks.controls.append(task)
        self.company_input.value = ""
        self.add_group_sel.clear()
        for row in self.add_group_rows:
            for c in row.controls[1:]:
                if isinstance(c, ft.TextButton):
                    c.style = ft.ButtonStyle(
                        bgcolor=ft.Colors.GREY_200,
                        color=ft.Colors.BLACK,
                    )
        await self.company_input.focus()
        self._save()
        self.update()

    def task_delete(self, task):
        self.tasks.controls.remove(task)
        self._save()
        self.update()

    def clear_clicked(self, e):
        for task in self.tasks.controls[:]:
            if task.completed:
                self.task_delete(task)

    def before_update(self):
        status = self.filter.tabs[self.filter_tabs.selected_index].label
        is_calendar = status == "カレンダー"
        self.task_list_view.visible = not is_calendar
        self.calendar_view.visible = is_calendar
        q = self._search_query.lower() if self._search_query else ""

        filter_industry = self.filter_industry.value
        filter_main_status = self.filter_main_status.value
        filter_tag = self.filter_tag.value
        sort_key = self.sort_by.value

        for task in self.tasks.controls:
            match_search = not q or q in task.company.lower()
            match_industry = filter_industry == "すべて" or task.industry == filter_industry
            match_main = filter_main_status == "すべて" or task.main_status == filter_main_status
            match_tag = (filter_tag == "すべて" or
                         any(f"{k}:{v}" == filter_tag for k, v in task.tag_groups.items()))

            task.visible = (
                not is_calendar
                and match_search
                and match_industry
                and match_main
                and match_tag
                and (
                    status == "すべて"
                    or (status == "選考中" and not task.completed)
                    or (status == "終了" and task.completed)
                )
            )

        count = 0
        stats: dict[str, int] = {}
        for task in self.tasks.controls:
            if not task.completed:
                count += 1
                stats[task.main_status] = stats.get(task.main_status, 0) + 1
        self.items_left.value = f"{count} 社選考中"
        parts = [f"{s}: {n}社" for s, n in stats.items()]
        self.stats_text.value = "　".join(parts) if parts else ""

        # Sort
        tasks_sorted = list(self.tasks.controls)
        if sort_key == "追加日時順（新しい）":
            tasks_sorted.sort(key=lambda t: t.created_at, reverse=True)
        elif sort_key == "追加日時順（古い）":
            tasks_sorted.sort(key=lambda t: t.created_at)
        elif sort_key == "企業名順（昇順）":
            tasks_sorted.sort(key=lambda t: t.company)
        elif sort_key == "企業名順（降順）":
            tasks_sorted.sort(key=lambda t: t.company, reverse=True)
        elif sort_key == "業界順":
            ind_order = list(INDUSTRIES.keys())
            tasks_sorted.sort(key=lambda t: ind_order.index(t.industry) if t.industry in ind_order else 999)
        elif sort_key == "メインステータス順":
            st_order = list(MAIN_STATUSES)
            tasks_sorted.sort(key=lambda t: st_order.index(t.main_status) if t.main_status in st_order else 999)
        elif sort_key == "期限日順（近い）":
            def nearest_date(task):
                best = None
                for s in task.schedules:
                    if s["type"] == "インターン":
                        d = s.get("start")
                    else:
                        d = s.get("date")
                    if d:
                        delta = abs((d - date.today()).days)
                        if best is None or delta < best:
                            best = delta
                return best if best is not None else 99999
            tasks_sorted.sort(key=nearest_date)
        self.tasks.controls = tasks_sorted

        if is_calendar:
            self._update_calendar()
        self._search_dirty = False


def main(page: ft.Page):
    page.title = "📝 就活記録"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.add(ft.SafeArea(content=TodoApp()))


if __name__ == "__main__":
    ft.run(main)
