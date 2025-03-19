from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty
from datetime import datetime, timedelta
import data


class ProjectDialog(MDBoxLayout):
    """Dialog for adding or editing a project."""

    def __init__(self, project_data=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.padding = dp(20)
        self.size_hint_y = None
        self.height = dp(360)

        # Project ID (hidden)
        self.project_id = None
        if project_data:
            self.project_id = project_data[0]

        # Project Name
        self.add_widget(MDLabel(text="Project Name:"))
        self.project_name = MDTextField()
        self.add_widget(self.project_name)

        # Project Budget
        self.add_widget(MDLabel(text="Budget:"))
        self.project_budget = MDTextField(hint_text="Enter amount (without $ or ,)")
        self.add_widget(self.project_budget)

        # Project Spending
        self.add_widget(MDLabel(text="Current Spending:"))
        self.project_spending = MDTextField(hint_text="Enter amount (without $ or ,)")
        self.add_widget(self.project_spending)

        # Project Budget End Date
        self.add_widget(MDLabel(text="Budget End Date:"))
        self.project_budget_end_date = MDTextField(hint_text="YYYY-MM-DD")
        self.add_widget(self.project_budget_end_date)

        # Project Estimated End Date
        self.add_widget(MDLabel(text="Estimated End Date:"))
        self.project_est_end_date = MDTextField(hint_text="YYYY-MM-DD")
        self.add_widget(self.project_est_end_date)

        # If editing, fill in existing data
        if project_data:
            self.project_name.text = project_data[1]
            self.project_budget.text = project_data[2].replace("$", "").replace(",", "")
            self.project_spending.text = project_data[3].replace("$", "").replace(",", "")
            self.project_budget_end_date.text = project_data[4]
            self.project_est_end_date.text = project_data[5]

    # Property to access the widgets by id
    @property
    def ids(self):
        return {
            'project_name': self.project_name,
            'project_budget': self.project_budget,
            'project_spending': self.project_spending,
            'project_budget_end_date': self.project_budget_end_date,
            'project_est_end_date': self.project_est_end_date
        }


class FilterDialog(MDBoxLayout):
    """Dialog for filtering projects."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.padding = dp(20)
        self.size_hint_y = None
        self.height = dp(200)

        # Filter by Name
        self.add_widget(MDLabel(text="Project Name Contains:"))
        self.filter_name = MDTextField()
        self.add_widget(self.filter_name)

        # Filter by Budget Range
        budget_range = MDBoxLayout(orientation="horizontal", spacing=dp(10))

        self.add_widget(MDLabel(text="Budget Range:"))

        self.filter_budget_min = MDTextField(hint_text="Min")
        budget_range.add_widget(self.filter_budget_min)

        self.filter_budget_max = MDTextField(hint_text="Max")
        budget_range.add_widget(self.filter_budget_max)

        self.add_widget(budget_range)

    # Property to access the widgets by id
    @property
    def ids(self):
        return {
            'filter_name': self.filter_name,
            'filter_budget_min': self.filter_budget_min,
            'filter_budget_max': self.filter_budget_max
        }


class ProjectsTableApp(MDApp):
    dialog = None
    project_being_edited = None

    def build(self):
        # Set theme colors
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"

        # Create main screen
        self.screen = MDScreen()

        # Create main layout
        self.layout = MDBoxLayout(orientation='vertical')

        # Create toolbar
        self.toolbar = MDTopAppBar(
            title="Shepherd",
            elevation=10,
            pos_hint={"top": 1},
            right_action_items=[
                ["magnify", lambda x: self.show_filter_dialog(), "Filter"],
                ["plus", lambda x: self.show_add_project_dialog(), "Add Project"],
                ["refresh", lambda x: self.refresh_table(), "Refresh"],
                ["theme-light-dark", lambda x: self.toggle_theme(), "Toggle Theme"],
            ]
        )

        # Sample data for projects - now with ID field
        self.projects_data = data.get_projects()

        # Create data table
        self.table = MDDataTable(
            size_hint=(1, 0.9),
            use_pagination=True,
            check=True,
            column_data=[
                ("ID", dp(18)),
                ("Project Name", dp(30)),
                ("Budget", dp(20)),
                ("Spending", dp(20)),
                ("Budget End Date", dp(30)),
                ("Est. End Date", dp(30)),
            ],
            row_data=self.projects_data,
            sorted_on="Budget",
            sorted_order="ASC",
        )

        # Set up table events
        self.table.bind(on_check_press=self.on_check_press)
        self.table.bind(on_row_press=self.on_row_press)

        # Create bottom action bar
        self.action_bar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, 0.1),
            padding=dp(10),
            spacing=dp(10)
        )

        self.edit_button = MDRaisedButton(
            text="Edit",
            disabled=True,
            on_release=lambda x: self.edit_selected_project()
        )

        self.delete_button = MDRaisedButton(
            text="Delete",
            disabled=True,
            on_release=lambda x: self.delete_selected_projects()
        )

        self.action_bar.add_widget(MDLabel(size_hint=(0.7, 1)))
        self.action_bar.add_widget(self.edit_button)
        self.action_bar.add_widget(self.delete_button)

        # Add widgets to layout
        self.layout.add_widget(self.toolbar)
        self.layout.add_widget(self.table)
        self.layout.add_widget(self.action_bar)

        # Add layout to screen
        self.screen.add_widget(self.layout)

        # Apply color coding
        Clock.schedule_once(self.apply_color_coding, 0.5)

        return self.screen

    def apply_color_coding(self, dt):
        """Apply color coding to rows based on budget and schedule status."""
        for row_index, row_data in enumerate(self.projects_data):
            project_id, name, budget, spending, budget_end_date, est_end_date = row_data

            # Check if over budget
            budget_value = float(budget.replace("$", "").replace(",", ""))
            spending_value = float(spending.replace("$", "").replace(",", ""))
            budget_ratio = spending_value / budget_value

            # Check if behind schedule
            budget_end = datetime.strptime(budget_end_date, "%Y-%m-%d")
            est_end = datetime.strptime(est_end_date, "%Y-%m-%d")

            if budget_ratio > 0.9 and est_end > budget_end:
                # Over budget and behind schedule - Red
                self.table.background_color_selected_cell = (0.9, 0.2, 0.2, 0.2)
            elif budget_ratio > 0.9:
                # Over budget - Orange
                self.table.background_color_selected_cell = (1, 0.65, 0, 0.2)
            elif est_end > budget_end:
                # Behind schedule - Yellow
                self.table.background_color_selected_cell = (1, 1, 0.4, 0.2)
            elif budget_ratio < 0.5 and est_end < budget_end:
                # Under budget and ahead of schedule - Green
                self.table.background_color_selected_cell = (0.2, 0.8, 0.2, 0.2)

    def on_check_press(self, instance_table, current_row):
        """Handle check press event."""
        if len(self.table.get_row_checks()) > 0:
            self.delete_button.disabled = False
            if len(self.table.get_row_checks()) == 1:
                self.edit_button.disabled = False
            else:
                self.edit_button.disabled = True
        else:
            self.edit_button.disabled = True
            self.delete_button.disabled = True

    def on_row_press(self, instance_table, instance_row):
        """Handle row press event."""
        row_index = int(instance_row.index / len(instance_table.column_data))
        self.project_being_edited = self.projects_data[row_index]
        self.show_edit_project_dialog(self.project_being_edited)

    def show_add_project_dialog(self):
        """Show dialog for adding a new project."""
        if not self.dialog:
            self.dialog = MDDialog(
                title="Add New Project",
                type="custom",
                content_cls=ProjectDialog(),
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=self.close_dialog),
                    MDRaisedButton(text="SAVE", on_release=self.save_new_project)
                ]
            )
        self.dialog.open()

    def show_edit_project_dialog(self, project_data):
        """Show dialog for editing an existing project."""
        if self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
            title="Edit Project",
            type="custom",
            content_cls=ProjectDialog(project_data=project_data),
            buttons=[
                MDFlatButton(text="CANCEL", on_release=self.close_dialog),
                MDRaisedButton(text="SAVE", on_release=self.save_edited_project)
            ]
        )
        self.dialog.open()

    def show_filter_dialog(self):
        """Show dialog for filtering projects."""
        if not self.dialog:
            self.dialog = MDDialog(
                title="Filter Projects",
                type="custom",
                content_cls=FilterDialog(),
                buttons=[
                    MDFlatButton(text="CANCEL", on_release=self.close_dialog),
                    MDRaisedButton(text="APPLY", on_release=self.apply_filter)
                ]
            )
        self.dialog.open()

    def close_dialog(self, *args):
        """Close the active dialog."""
        if self.dialog:
            self.dialog.dismiss()

    def save_new_project(self, *args):
        """Save a new project."""
        if self.dialog:
            content = self.dialog.content_cls

            # Create a new project ID
            new_id = max([p[0] for p in self.projects_data]) + 1

            # Format currency values
            try:
                budget = float(content.ids.project_budget.text)
                budget_str = f"${budget:,.0f}"

                spending = float(content.ids.project_spending.text)
                spending_str = f"${spending:,.0f}"

                # Create new project tuple
                new_project = (
                    new_id,
                    content.ids.project_name.text,
                    budget_str,
                    spending_str,
                    content.ids.project_budget_end_date.text,
                    content.ids.project_est_end_date.text
                )

                # Add to projects data
                self.projects_data.append(new_project)

                # Update table
                self.refresh_table()

                # Close dialog
                self.close_dialog()
            except ValueError:
                # Show error message (in a real app)
                pass

    def save_edited_project(self, *args):
        """Save changes to an edited project."""
        if self.dialog and self.project_being_edited:
            content = self.dialog.content_cls
            project_id = self.project_being_edited[0]

            # Format currency values
            try:
                budget = float(content.ids["project_budget"].text)
                budget_str = f"${budget:,.0f}"

                spending = float(content.ids["project_spending"].text)
                spending_str = f"${spending:,.0f}"

                # Create updated project tuple
                updated_project = (
                    project_id,
                    content.ids["project_name"].text,
                    budget_str,
                    spending_str,
                    content.ids["project_budget_end_date"].text,
                    content.ids["project_est_end_date"].text
                )

                # Update projects data
                for i, project in enumerate(self.projects_data):
                    if project[0] == project_id:
                        self.projects_data[i] = updated_project
                        break

                # Update table
                self.refresh_table()

                # Close dialog
                self.close_dialog()
            except ValueError:
                # Show error message (in a real app)
                pass

    def edit_selected_project(self):
        """Edit the selected project."""
        checked_rows = self.table.get_row_checks()
        if checked_rows:
            row_index = checked_rows[0]
            self.project_being_edited = self.projects_data[row_index]
            self.show_edit_project_dialog(self.project_being_edited)

    def delete_selected_projects(self):
        """Delete the selected projects."""
        checked_rows = self.table.get_row_checks()
        if checked_rows:
            # Sort in reverse order to avoid index issues when deleting
            for row_index in sorted(checked_rows, reverse=True):
                project_id = self.projects_data[row_index][0]

                # Remove from projects data
                self.projects_data = [p for p in self.projects_data if p[0] != project_id]

            # Update table
            self.refresh_table()

            # Disable buttons
            self.edit_button.disabled = True
            self.delete_button.disabled = True

    def apply_filter(self, *args):
        """Apply filter to the projects table."""
        if self.dialog:
            content = self.dialog.content_cls

            # Get filter values
            name_filter = content.ids.filter_name.text.lower()
            budget_min = content.ids.filter_budget_min.text
            budget_max = content.ids.filter_budget_max.text

            # Filter data
            filtered_data = []
            for project in self.projects_data:
                project_id, name, budget, spending, budget_end_date, est_end_date = project

                # Check name filter
                if name_filter and name_filter not in name.lower():
                    continue

                # Check budget min filter
                if budget_min:
                    budget_value = float(budget.replace("$", "").replace(",", ""))
                    if budget_value < float(budget_min):
                        continue

                # Check budget max filter
                if budget_max:
                    budget_value = float(budget.replace("$", "").replace(",", ""))
                    if budget_value > float(budget_max):
                        continue

                # Project passed all filters
                filtered_data.append(project)

            # Update table with filtered data
            self.table.row_data = filtered_data

            # Close dialog
            self.close_dialog()

    def refresh_table(self):
        """Refresh the table with current data."""
        self.table.row_data = self.projects_data
        Clock.schedule_once(self.apply_color_coding, 0.5)

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"


if __name__ == "__main__":
    ProjectsTableApp().run()
