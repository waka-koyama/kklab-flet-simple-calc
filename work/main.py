import json, copy
import flet as ft
from datetime import date, datetime, timezone
from pathlib import Path

SAVE_FILE = Path(__file__).parent / "data.json"

try:
    from js import localStorage as _storage
    _STORAGE_KEY = "job_app_data"
    def _save_storage(data):
        _storage.setItem(_STORAGE_KEY, json.dumps(data, ensure_ascii=False))
    def _load_storage():
        val = _storage.getItem(_STORAGE_KEY)
        if val is None:
            return None
        return json.loads(val)
except ImportError:
    def _save_storage(data):
        pass
    def _load_storage():
        return None

INDUSTRIES = {
    "IT・Web":       {"color": ft.Colors.BLUE_400,   "emoji": "💻"},
    "金融・保険":     {"color": ft.Colors.GREEN_400,  "emoji": "💴"},
    "商社":           {"color": ft.Colors.ORANGE_400, "emoji": "🌐"},
    "メーカー":       {"color": ft.Colors.CYAN_400,   "emoji": "🏭"},
    "マスコミ・広告":  {"color": ft.Colors.PINK_400,  "emoji": "📺"},
    "コンサル":       {"color": ft.Colors.PURPLE_400, "emoji": "📊"},
    "その他":         {"color": ft.Colors.GREY_400,   "emoji": "🏢"},
}

STATUSES = ["ES作成中", "ホームページ作成済み", "ES提出済み", "適性検査", "一次面接", "二次面接", "最終面接", "内定", "お祈り"]
STATUS_COLORS = {
    "ES作成中":            ft.Colors.GREY_400,
    "ホームページ作成済み": ft.Colors.LIGHT_BLUE_300,
    "ES提出済み":           ft.Colors.BLUE_300,
    "適性検査":             ft.Colors.CYAN_400,
    "一次面接":             ft.Colors.ORANGE_300,
    "二次面接":             ft.Colors.ORANGE_400,
    "最終面接":             ft.Colors.DEEP_ORANGE_400,
    "内定":                 ft.Colors.GREEN_400,
    "お祈り":               ft.Colors.GREY_600,
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
    """Task の状態から表示用 Container を新規作成する"""
    info = INDUSTRIES[task.industry]
    color = info["color"]
    emoji = info["emoji"]
    status_color = STATUS_COLORS.get(task.status, ft.Colors.GREY_400)

    badges = [ft.Container(
        content=ft.Text(task.status, size=11, color=ft.Colors.WHITE),
        bgcolor=status_color,
        padding=ft.Padding(left=8, right=8, top=2, bottom=2),
        border_radius=10,
    )]
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

    date_lines = []
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
    def __init__(self, company, industry, status, schedules, task_delete, task_save=None):
        super().__init__()
        self.completed = False
        self.company = company
        self.industry = industry
        self.status = status
        self.schedules = schedules
        self.task_delete = task_delete
        self.task_save = task_save

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "industry": self.industry,
            "status": self.status,
            "completed": self.completed,
            "schedules": [schedule_to_dict(s) for s in self.schedules],
        }

    def build(self):
        self.display_task = ft.Checkbox(
            value=self.completed, label=self.company, on_change=self.status_changed)
        self.controls = [_make_display_view(self)]

    def refresh(self):
        """保存後に表示を更新する（controls[0] を差し替え）"""
        self.display_task.label = self.company
        self.controls = [_make_display_view(self)]
        if self.page:
            self.update()

    def edit_clicked(self, e):
        name_field = ft.TextField(label="企業名", value=self.company, expand=True)
        industry_dd = ft.Dropdown(
            label="業界", value=self.industry, width=160,
            options=[ft.dropdown.Option(k) for k in INDUSTRIES],
        )
        status_dd = ft.Dropdown(
            label="選考状況", value=self.status, width=175,
            options=[ft.dropdown.Option(s) for s in STATUSES],
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

        # 初期描画（まだ page に属していないので sched_col.update() はしない）
        sched_col.controls = [_row(i, s) for i, s in enumerate(sched_data)]

        def save(e):
            self.company  = name_field.value
            self.industry = industry_dd.value
            self.status   = status_dd.value
            self.schedules = sched_data
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
                ft.Row(wrap=True, spacing=8, controls=[industry_dd, status_dd]),
                ft.Divider(),
                ft.Text("日程", weight=ft.FontWeight.BOLD),
                sched_col,
                ft.TextButton("＋ 日程を追加", on_click=_add),
            ]),
            actions=[
                ft.TextButton("保存", on_click=save),
                ft.TextButton("キャンセル", on_click=cancel),
            ],
        )
        self.page.show_dialog(dlg)

    def status_changed(self, e):
        self.completed = self.display_task.value
        if self.task_save:
            self.task_save()
        self.update()

    def delete_clicked(self, e):
        self.task_delete(self)


class TodoApp(ft.Column):
    def build(self):
        self.company_input = ft.TextField(hint_text="企業名を入力…", on_submit=self.add_clicked, expand=True)
        self.industry_dd = ft.Dropdown(
            value="IT・Web", width=160, label="業界",
            options=[ft.dropdown.Option(k) for k in INDUSTRIES],
        )
        self.status_dd = ft.Dropdown(
            value="ES作成中", width=175, label="選考状況",
            options=[ft.dropdown.Option(s) for s in STATUSES],
        )
        self.tasks = ft.Column()
        self.filter = ft.TabBar(
            scrollable=False,
            tabs=[ft.Tab(label="すべて"), ft.Tab(label="選考中"), ft.Tab(label="終了")],
        )
        self.filter_tabs = ft.Tabs(length=3, selected_index=0, on_change=lambda e: self.update(), content=self.filter)
        self.items_left = ft.Text("0 社選考中")
        self.stats_text = ft.Text("", size=12, color=ft.Colors.GREY_500)
        self.save_indicator = ft.Container(
            content=ft.Row([ft.Text("💾", size=14), ft.Text("自動保存", size=11, color=ft.Colors.GREEN_600)],
                           spacing=2, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            visible=False,
        )

        self.width = 640
        self.controls = [
            ft.Row([ft.Text("📝 就活記録", theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM)],
                   alignment=ft.MainAxisAlignment.CENTER),
            self.stats_text,
            ft.Row(controls=[self.company_input,
                              ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=self.add_clicked)]),
            ft.Row(wrap=True, spacing=8, controls=[self.industry_dd, self.status_dd]),
            ft.Column(spacing=25, controls=[
                self.filter_tabs,
                self.tasks,
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[self.items_left,
                               self.save_indicator,
                               ft.OutlinedButton(content="終了分を削除", on_click=self.clear_clicked)],
                ),
            ]),
        ]

    def did_mount(self):
        self._load()
        self.page.update()

    def _save(self):
        data = [t.to_dict() for t in self.tasks.controls]
        _save_storage(data)
        SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.save_indicator.visible = True

    def _add(self, e):

    def _load(self):
        data = _load_storage()
        if data is None:
            if not SAVE_FILE.exists():
                return
            try:
                data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
            except Exception:
                return
        for d in data:
            if "schedules" in d:
                schedules = [schedule_from_dict(s) for s in d["schedules"]]
            else:
                # 後方互換
                def p(s): return date.fromisoformat(s) if s else None
                schedules = []
                if d.get("exam_date"):
                    schedules.append({"type": "選考", "date": p(d["exam_date"])})
                if d.get("intern_start"):
                    schedules.append({"type": "インターン", "start": p(d["intern_start"]),
                                      "end": p(d.get("intern_end")), "state": "確定"})

            task = Task(
                company=d["company"],
                industry=d.get("industry", "その他"),
                status=d.get("status", "ES作成中"),
                schedules=schedules,
                task_delete=self.task_delete,
                task_save=self._save,
            )
            task.completed = d.get("completed", False)
            self.tasks.controls.append(task)
        if self.tasks.controls:
            self.save_indicator.visible = True

    async def add_clicked(self, e):
        if not self.company_input.value:
            return
        task = Task(
            company=self.company_input.value,
            industry=self.industry_dd.value,
            status=self.status_dd.value,
            schedules=[],
            task_delete=self.task_delete,
            task_save=self._save,
        )
        self.tasks.controls.append(task)
        self.company_input.value = ""
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
        count = 0
        stats: dict[str, int] = {}
        for task in self.tasks.controls:
            task.visible = (
                status == "すべて"
                or (status == "選考中" and not task.completed)
                or (status == "終了" and task.completed)
            )
            if not task.completed:
                count += 1
                stats[task.status] = stats.get(task.status, 0) + 1
        self.items_left.value = f"{count} 社選考中"
        parts = [f"{s}: {n}社" for s, n in stats.items()]
        self.stats_text.value = "　".join(parts) if parts else ""


def main(page: ft.Page):
    page.title = "📝 就活記録"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.add(ft.SafeArea(content=TodoApp()))


if __name__ == "__main__":
    ft.run(main)
