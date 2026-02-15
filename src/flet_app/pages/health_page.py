"""
Personal Password Manager - Password Health Page
==================================================

Dashboard showing the overall security health of stored passwords.
Fetches all password entries (decrypted), runs them through the
PasswordHealthService, and displays:

- Overall security score gauge (0-100)
- Weak passwords table
- Duplicate password groups table
- Old/stale passwords table
- Prioritized recommendations list

All data is loaded in a background thread so the UI stays responsive.

Version: 3.0.0
"""

import threading
from typing import Optional

import flet as ft

from ..components.confirm_dialog import show_snack_bar
from ..components.nav_rail import NavRail
from ..state import AppState


def _score_color(score: int) -> str:
    """Return a color string based on the security score (0-100)."""
    if score >= 80:
        return ft.Colors.GREEN
    elif score >= 60:
        return ft.Colors.LIGHT_GREEN
    elif score >= 40:
        return ft.Colors.ORANGE
    elif score >= 20:
        return ft.Colors.DEEP_ORANGE
    return ft.Colors.RED


class HealthPage(ft.Container):
    """
    Password health dashboard.

    Shows security score, weak/duplicate/old password tables, and
    recommendations. Data is fetched once on page load.

    Args:
        state: The shared AppState object
    """

    def __init__(self, state: AppState):
        self.state = state

        # --- Score display ---
        self._score_text = ft.Text(
            "—",
            size=48,
            weight=ft.FontWeight.BOLD,
        )
        self._score_label = ft.Text("Security Score", size=14, opacity=0.7)
        self._total_label = ft.Text("", size=13, opacity=0.6)

        # --- Summary chips ---
        self._weak_chip = ft.Chip(
            label=ft.Text("Weak: —"),
            bgcolor=ft.Colors.RED_100,
        )
        self._duplicate_chip = ft.Chip(
            label=ft.Text("Duplicates: —"),
            bgcolor=ft.Colors.ORANGE_100,
        )
        self._old_chip = ft.Chip(
            label=ft.Text("Old: —"),
            bgcolor=ft.Colors.YELLOW_100,
        )

        # --- Tables ---
        self._weak_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Website")),
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Strength")),
            ],
            rows=[],
            visible=False,
        )

        self._duplicate_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Websites")),
                ft.DataColumn(ft.Text("Count")),
            ],
            rows=[],
            visible=False,
        )

        self._old_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Website")),
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Age (days)")),
            ],
            rows=[],
            visible=False,
        )

        # --- Recommendations list ---
        self._recommendations_list = ft.Column(spacing=4, visible=False)

        # --- Loading ---
        self._loading = ft.ProgressRing(visible=True, width=30, height=30)

        # --- Build layout ---
        content_area = ft.Column(
            [
                ft.Text("Password Health", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                # Loading indicator
                ft.Container(
                    content=self._loading,
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=30),
                ),
                # Score card
                ft.Container(
                    content=ft.Column(
                        [
                            self._score_text,
                            self._score_label,
                            self._total_label,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(top=16, bottom=16),
                ),
                # Summary chips row
                ft.Row(
                    [self._weak_chip, self._duplicate_chip, self._old_chip],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                ),
                ft.Container(height=16),
                # Weak passwords section
                ft.Text("Weak Passwords", size=16, weight=ft.FontWeight.W_600),
                self._weak_table,
                ft.Container(height=8),
                # Duplicate passwords section
                ft.Text("Duplicate Passwords", size=16, weight=ft.FontWeight.W_600),
                self._duplicate_table,
                ft.Container(height=8),
                # Old passwords section
                ft.Text("Old Passwords (> 180 days)", size=16, weight=ft.FontWeight.W_600),
                self._old_table,
                ft.Container(height=8),
                # Recommendations
                ft.Text("Recommendations", size=16, weight=ft.FontWeight.W_600),
                self._recommendations_list,
            ],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        nav_rail = NavRail(state=state, current_route="/health")

        super().__init__(
            content=ft.Row(
                [
                    nav_rail,
                    ft.VerticalDivider(width=1),
                    ft.Container(
                        content=content_area,
                        padding=ft.padding.all(24),
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            expand=True,
        )

        # Start loading data
        self._load_health_data()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_health_data(self) -> None:
        """Fetch all entries and run the health analysis in a background thread."""
        thread = threading.Thread(target=self._analyze_background, daemon=True)
        thread.start()

    def _analyze_background(self) -> None:
        """Background: fetch entries, analyze, update UI."""
        try:
            from core.password_manager import SearchCriteria

            # Fetch all entries with decrypted passwords
            entries = self.state.password_manager.search_password_entries(
                session_id=self.state.session_id,
                criteria=SearchCriteria(),
                include_passwords=True,
            )

            # Run health analysis
            report = self.state.health_service.analyze_health(entries)
            self._display_report(report)

        except Exception as ex:
            self._loading.visible = False
            try:
                self.update()
            except Exception:
                pass
            show_snack_bar(self.state.page, f"Health analysis failed: {ex}")

    # ------------------------------------------------------------------
    # Display the report
    # ------------------------------------------------------------------

    def _display_report(self, report) -> None:
        """Populate UI controls from the HealthReport."""
        # Score
        self._score_text.value = str(report.score)
        self._score_text.color = _score_color(report.score)
        self._total_label.value = f"{report.total_count} passwords analyzed"

        # Summary chips
        self._weak_chip.label = ft.Text(f"Weak: {len(report.weak_passwords)}")
        self._duplicate_chip.label = ft.Text(f"Duplicates: {report.reused_count}")
        self._old_chip.label = ft.Text(f"Old: {len(report.old_passwords)}")

        # --- Weak passwords table ---
        if report.weak_passwords:
            rows = []
            for wp in report.weak_passwords[:20]:  # Cap at 20 rows for performance
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(wp.website, size=13)),
                            ft.DataCell(ft.Text(wp.username, size=13)),
                            ft.DataCell(ft.Text(wp.strength_level, size=13)),
                        ]
                    )
                )
            self._weak_table.rows = rows
            self._weak_table.visible = True
        else:
            self._weak_table.visible = False

        # --- Duplicate passwords table ---
        if report.duplicate_groups:
            rows = []
            for dg in report.duplicate_groups[:20]:
                websites_str = ", ".join(dg.websites[:5])
                if len(dg.websites) > 5:
                    websites_str += f" (+{len(dg.websites) - 5} more)"
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(websites_str, size=13)),
                            ft.DataCell(ft.Text(str(dg.count), size=13)),
                        ]
                    )
                )
            self._duplicate_table.rows = rows
            self._duplicate_table.visible = True
        else:
            self._duplicate_table.visible = False

        # --- Old passwords table ---
        if report.old_passwords:
            rows = []
            for op in report.old_passwords[:20]:
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(op.website, size=13)),
                            ft.DataCell(ft.Text(op.username, size=13)),
                            ft.DataCell(ft.Text(str(op.age_days), size=13)),
                        ]
                    )
                )
            self._old_table.rows = rows
            self._old_table.visible = True
        else:
            self._old_table.visible = False

        # --- Recommendations ---
        if report.recommendations:
            self._recommendations_list.controls.clear()
            for rec in report.recommendations:
                icon = ft.Icons.WARNING_AMBER if rec.priority == "high" else ft.Icons.INFO_OUTLINE
                color = ft.Colors.ORANGE if rec.priority == "high" else None
                self._recommendations_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(icon, color=color, size=20),
                        title=ft.Text(rec.title, size=14, weight=ft.FontWeight.W_500),
                        subtitle=ft.Text(rec.description, size=12),
                    )
                )
            self._recommendations_list.visible = True
        else:
            self._recommendations_list.visible = False

        # Hide loading spinner
        self._loading.visible = False

        try:
            self.update()
        except Exception:
            pass
