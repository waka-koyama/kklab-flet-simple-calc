import json
import flet as ft
from datetime import date
from pathlib import Path

SAVE_FILE = Path(__file__).parent / "data.json"

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


def fmt(d: date) -> str:
    return d.strftime("%Y/%m/%d")

def countdown(d: date) -> str:
    delta = (d - date.today()).days
    if delta < 0:   return f"{fmt(d)} 経過"
    if delta == 0:  return f"🔥 今日！({fmt(d)})"
    return f"⏳ あと {delta} 日 ({fmt(d)})"


class Task(ft.Column):
    def __init__(self, company, industry, status, exam_date, intern_start, intern_end, task_delete, task_save=None):
        super().__init__()
        self.completed = False
        self.company = company
        self.industry = industry
        self.status = status
        self.exam_date = exam_date
        self.intern_start = intern_start
        self.intern_end = intern_end
        self.task_delete = task_delete
        self.task_save = task_save

    def to_dict(self) -> dict:
        return {
            "company": self.company,
            "industry": self.industry,
            "status": self.status,
            "completed": self.completed,
            "exam_date": self.exam_date.isoformat() if self.exam_date else None,
            "intern_start": self.intern_start.isoformat() if self.intern_start else None,
            "intern_end": self.intern_end.isoformat() if self.intern_end else None,
        }

    def build(self):
        self.display_task = ft.Checkbox(value=False, label=self.company, on_change=self.status_changed)
        self._render()

    def _render(self):
        info = INDUSTRIES[self.industry]
        color = info["color"]
        emoji = info["emoji"]
        status_color = STATUS_COLORS.get(self.status, ft.Colors.GREY_400)

        badges = [ft.Container(
            content=ft.Text(self.status, size=11, color=ft.Colors.WHITE),
            bgcolor=status_color,
            padding=ft.Padding(left=8, right=8, top=2, bottom=2),
            border_radius=10,
        )]
        if self.intern_start:
            label = f"🏢 {fmt(self.intern_start)}"
            if self.intern_end:
                label += f" 〜 {fmt(self.intern_end)}"
            badges.append(ft.Container(
                content=ft.Text(label, size=11, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.TEAL_400,
                padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                border_radius=10,
            ))

        date_lines = []
        if self.exam_date:
            date_lines.append(ft.Text(f"📅 選考日 {countdown(self.exam_date)}", size=12, color=ft.Colors.GREY_500))
        if self.intern_start:
            date_lines.append(ft.Text(f"🏢 インターン開始 {countdown(self.intern_start)}", size=12, color=ft.Colors.TEAL_300))

        self.display_view = ft.Container(
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(spacing=4, controls=[
                        ft.Row(spacing=6, controls=[
                            ft.Text(f"{emoji} {self.industry}", size=11, color=color, weight=ft.FontWeight.BOLD),
                            *badges,
                        ]),
                        self.display_task,
                        *date_lines,
                    ]),
                    ft.Row(spacing=0, controls=[
                        ft.IconButton(ft.Icons.CREATE_OUTLINED, tooltip="編集", on_click=self.edit_clicked),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="削除", on_click=self.delete_clicked),
                    ]),
                ],
            ),
            border=ft.Border.only(left=ft.border.BorderSide(4, color)),
            padding=ft.Padding(left=8, top=6, bottom=6, right=0),
            border_radius=4,
        )
        self.controls = [self.display_view]

    def edit_clicked(self, e):
        # ダイアログ内の各フィールド
        name_field = ft.TextField(label="企業名", value=self.company, expand=True)
        industry_dd = ft.Dropdown(
            label="業界", value=self.industry, width=160,
            options=[ft.dropdown.Option(k) for k in INDUSTRIES],
        )
        status_dd = ft.Dropdown(
            label="選考状況", value=self.status, width=175,
            options=[ft.dropdown.Option(s) for s in STATUSES],
        )

        # 選考日
        exam_ref = {"date": self.exam_date}
        exam_btn = ft.ElevatedButton(
            f"📅 {fmt(self.exam_date)}" if self.exam_date else "📅 選考日を選択",
            on_click=lambda e: open_picker("exam"),
        )

        # インターン
        intern_ref = {"start": self.intern_start, "end": self.intern_end}
        intern_start_btn = ft.ElevatedButton(
            f"🏢 開始 {fmt(self.intern_start)}" if self.intern_start else "🏢 開始日を選択",
            on_click=lambda e: open_picker("intern_start"),
        )
        intern_end_btn = ft.ElevatedButton(
            f"〜 終了 {fmt(self.intern_end)}" if self.intern_end else "〜 終了日を選択",
            visible=self.intern_start is not None,
            on_click=lambda e: open_picker("intern_end"),
        )
        intern_none_btn = ft.OutlinedButton("インターンなし", on_click=lambda e: clear_intern())

        picker_target = {"val": "exam"}

        def on_pick(e):
            if not date_picker.value:
                return
            v = date_picker.value
            d = v.date() if hasattr(v, "date") else v
            t = picker_target["val"]
            if t == "exam":
                exam_ref["date"] = d
                exam_btn.text = f"📅 {fmt(d)}"
            elif t == "intern_start":
                intern_ref["start"] = d
                intern_start_btn.text = f"🏢 開始 {fmt(d)}"
                intern_end_btn.visible = True
            elif t == "intern_end":
                intern_ref["end"] = d
                intern_end_btn.text = f"〜 終了 {fmt(d)}"
            self.page.update()

        date_picker = ft.DatePicker(on_change=on_pick, on_dismiss=on_pick)

        def open_picker(target):
            picker_target["val"] = target
            date_picker.open = True
            self.page.update()

        def clear_intern():
            intern_ref["start"] = None
            intern_ref["end"] = None
            intern_start_btn.text = "🏢 開始日を選択"
            intern_end_btn.text = "〜 終了日を選択"
            intern_end_btn.visible = False
            self.page.update()

        def save(e):
            self.company = name_field.value
            self.industry = industry_dd.value
            self.status = status_dd.value
            self.exam_date = exam_ref["date"]
            self.intern_start = intern_ref["start"]
            self.intern_end = intern_ref["end"]
            self.display_task.label = self.company
            self.page.overlay.remove(date_picker)
            dlg.open = False
            self._render()
            self.update()
            if self.task_save:
                self.task_save()
            self.page.update()

        def cancel(e):
            self.page.overlay.remove(date_picker)
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("企業情報を編集"),
            content=ft.Column(spacing=10, width=400, controls=[
                name_field,
                ft.Row(wrap=True, spacing=8, controls=[industry_dd, status_dd]),
                ft.Row(wrap=True, spacing=8, controls=[exam_btn]),
                ft.Row(wrap=True, spacing=8, controls=[intern_start_btn, intern_end_btn, intern_none_btn]),
            ]),
            actions=[
                ft.TextButton("保存", on_click=save),
                ft.TextButton("キャンセル", on_click=cancel),
            ],
        )
        self.page.overlay.append(date_picker)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

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

        self.exam_date_btn = ft.ElevatedButton("📅 選考日を選択", on_click=lambda e: self._open("exam"))
        self.selected_exam: date | None = None

        self.intern_start_btn = ft.ElevatedButton("🏢 開始日を選択", on_click=lambda e: self._open("intern_start"))
        self.intern_end_btn   = ft.ElevatedButton("〜 終了日を選択", on_click=lambda e: self._open("intern_end"), visible=False)
        self.intern_none_btn  = ft.OutlinedButton("インターンなし", on_click=self._clear_intern)
        self.selected_intern_start: date | None = None
        self.selected_intern_end:   date | None = None

        self._picker_target = "exam"
        self.date_picker = ft.DatePicker(on_change=self._date_picked, on_dismiss=self._date_picked)

        self.tasks = ft.Column()
        self.filter = ft.TabBar(
            scrollable=False,
            tabs=[ft.Tab(label="すべて"), ft.Tab(label="選考中"), ft.Tab(label="終了")],
        )
        self.filter_tabs = ft.Tabs(length=3, selected_index=0, on_change=lambda e: self.update(), content=self.filter)
        self.items_left = ft.Text("0 社選考中")
        self.stats_text = ft.Text("", size=12, color=ft.Colors.GREY_500)

        self.width = 640
        self.controls = [
            ft.Row([ft.Text("📝 就活記録", theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM)], alignment=ft.MainAxisAlignment.CENTER),
            self.stats_text,
            ft.Row(controls=[self.company_input, ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=self.add_clicked)]),
            ft.Row(wrap=True, spacing=8, controls=[self.industry_dd, self.status_dd]),
            ft.Row(wrap=True, spacing=8, controls=[self.exam_date_btn]),
            ft.Row(wrap=True, spacing=8, controls=[self.intern_start_btn, self.intern_end_btn, self.intern_none_btn]),
            ft.Column(spacing=25, controls=[
                self.filter_tabs,
                self.tasks,
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[self.items_left, ft.OutlinedButton(content="終了分を削除", on_click=self.clear_clicked)],
                ),
            ]),
        ]

    def did_mount(self):
        self.page.overlay.append(self.date_picker)
        self._load()
        self.page.update()

    def _save(self):
        data = [t.to_dict() for t in self.tasks.controls]
        SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load(self):
        if not SAVE_FILE.exists():
            return
        try:
            data = json.loads(SAVE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return
        for d in data:
            def parse(s): return date.fromisoformat(s) if s else None
            task = Task(
                company=d["company"],
                industry=d.get("industry", "その他"),
                status=d.get("status", "ES作成中"),
                exam_date=parse(d.get("exam_date")),
                intern_start=parse(d.get("intern_start")),
                intern_end=parse(d.get("intern_end")),
                task_delete=self.task_delete,
                task_save=self._save,
            )
            task.completed = d.get("completed", False)
            self.tasks.controls.append(task)

    def _open(self, target: str):
        self._picker_target = target
        self.date_picker.open = True
        self.page.update()

    def _date_picked(self, e):
        if not self.date_picker.value:
            return
        v = self.date_picker.value
        d = v.date() if hasattr(v, "date") else v
        if self._picker_target == "exam":
            self.selected_exam = d
            self.exam_date_btn.text = f"📅 {fmt(d)}"
        elif self._picker_target == "intern_start":
            self.selected_intern_start = d
            self.intern_start_btn.text = f"🏢 開始 {fmt(d)}"
            self.intern_end_btn.visible = True
        elif self._picker_target == "intern_end":
            self.selected_intern_end = d
            self.intern_end_btn.text = f"〜 終了 {fmt(d)}"
        self.page.update()

    def _clear_intern(self, e):
        self.selected_intern_start = None
        self.selected_intern_end = None
        self.intern_start_btn.text = "🏢 開始日を選択"
        self.intern_end_btn.text = "〜 終了日を選択"
        self.intern_end_btn.visible = False
        self.update()

    async def add_clicked(self, e):
        if not self.company_input.value:
            return
        task = Task(
            company=self.company_input.value,
            industry=self.industry_dd.value,
            status=self.status_dd.value,
            exam_date=self.selected_exam,
            intern_start=self.selected_intern_start,
            intern_end=self.selected_intern_end,
            task_delete=self.task_delete,
            task_save=self._save,
        )
        self.tasks.controls.append(task)
        self.company_input.value = ""
        self.selected_exam = None
        self.exam_date_btn.text = "📅 選考日を選択"
        self._clear_intern(None)
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
