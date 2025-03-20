from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from datetime import datetime
import data

import data


class ProjectDialog(MDBoxLayout):
    """Dialog for adding or editing a project."""
    project_id = NumericProperty(None)


class FilterDialog(MDBoxLayout):
    """Dialog for filtering projects."""
    pass


class ProjectsTableApp(MDApp):
    dialog = None
    project_being_edited = None

    def build(self):
        # Set theme colors
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"

        # Sample data for projects - with ID field
        self.projects_data = data.get_projects()

        return ProjectsTableScreen()

    def on_start(self):
        """Called when the application starts."""
        # Set up table with initial data
        self.root.ids.projects_table.column_data = [
            ("ID", dp(10)),
            ("Project Name", dp(30)),
            ("Budget", dp(20)),
            ("Spending", dp(20)),
            ("Budget End Date", dp(30)),
            ("Est. End Date", dp(30)),
        ]
        self.root.ids.projects_table.row_data = self.projects_data

        # Set up table events
        self.root.ids.projects_table.bind(on_check_press=self.on_check_press)
        self.root.ids.projects_table.bind(on_row_press=self.on_row_press)

        # Apply initial color coding
        Clock.schedule_once(self.apply_color_coding, 0.5)

    def apply_color_coding(self, dt):
        """Apply color coding to rows based on budget and schedule status."""
        table = self.root.ids.projects_table
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
                table.update_row_background(row_index, (0.9, 0.2, 0.2, 0.2))
            elif budget_ratio > 0.9:
                # Over budget - Orange
                table.update_row_background(row_index, (1, 0.65, 0, 0.2))
            elif est_end > budget_end:
                # Behind schedule - Yellow
                table.update_row_background(row_index, (1, 1, 0.4, 0.2))
            elif budget_ratio < 0.5 and est_end < budget_end:
                # Under budget and ahead of schedule - Green
                table.update_row_background(row_index, (0.2, 0.8, 0.2, 0.2))

    def on_check_press(self, instance_table, current_row):
        """Handle check press event."""
        checked_rows = instance_table.get_row_checks()
        self.root.ids.delete_button.disabled = len(checked_rows) == 0
        self.root.ids.edit_button.disabled = len(checked_rows) != 1

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
            self.dialog = None

        dialog_content = ProjectDialog()
        dialog_content.project_id = project_data[0]
        dialog_content.ids.project_name.text = project_data[1]
        dialog_content.ids.project_budget.text = project_data[2].replace("$", "").replace(",", "")
        dialog_content.ids.project_spending.text = project_data[3].replace("$", "").replace(",", "")
        dialog_content.ids.project_budget_end_date.text = project_data[4]
        dialog_content.ids.project_est_end_date.text = project_data[5]

        self.dialog = MDDialog(
            title="Edit Project",
            type="custom",
            content_cls=dialog_content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=self.close_dialog),
                MDRaisedButton(text="SAVE", on_release=self.save_edited_project)
            ]
        )
        self.dialog.open()

    def show_filter_dialog(self):
        """Show dialog for filtering projects."""
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

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
            self.dialog = None

    def save_new_project(self, *args):
        """Save a new project."""
        if self.dialog:
            content = self.dialog.content_cls

            # Create a new project ID
            new_id = max([p[0] for p in self.projects_data]) + 1 if self.projects_data else 1

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
                # In a real app, show an error message
                pass

    def save_edited_project(self, *args):
        """Save changes to an edited project."""
        if self.dialog and self.project_being_edited:
            content = self.dialog.content_cls
            project_id = content.project_id

            # Format currency values
            try:
                budget = float(content.ids.project_budget.text)
                budget_str = f"${budget:,.0f}"

                spending = float(content.ids.project_spending.text)
                spending_str = f"${spending:,.0f}"

                # Create updated project tuple
                updated_project = (
                    project_id,
                    content.ids.project_name.text,
                    budget_str,
                    spending_str,
                    content.ids.project_budget_end_date.text,
                    content.ids.project_est_end_date.text
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
                # In a real app, show an error message
                pass

    def edit_selected_project(self):
        """Edit the selected project."""
        table = self.root.ids.projects_table
        checked_rows = table.get_row_checks()
        if checked_rows:
            row_index = checked_rows[0]
            self.project_being_edited = self.projects_data[row_index]
            self.show_edit_project_dialog(self.project_being_edited)

    def delete_selected_projects(self):
        """Delete the selected projects."""
        table = self.root.ids.projects_table
        checked_rows = table.get_row_checks()
        if checked_rows:
            # Sort in reverse order to avoid index issues when deleting
            project_ids_to_delete = []
            for row_index in checked_rows:
                project_ids_to_delete.append(self.projects_data[row_index][0])

            # Remove from projects data
            self.projects_data = [p for p in self.projects_data if p[0] not in project_ids_to_delete]

            # Update table
            self.refresh_table()

            # Disable buttons
            self.root.ids.edit_button.disabled = True
            self.root.ids.delete_button.disabled = True

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
                    try:
                        budget_value = float(budget.replace("$", "").replace(",", ""))
                        if budget_value < float(budget_min):
                            continue
                    except ValueError:
                        continue

                # Check budget max filter
                if budget_max:
                    try:
                        budget_value = float(budget.replace("$", "").replace(",", ""))
                        if budget_value > float(budget_max):
                            continue
                    except ValueError:
                        continue

                # Project passed all filters
                filtered_data.append(project)

            # Update table with filtered data
            self.root.ids.projects_table.row_data = filtered_data

            # Close dialog
            self.close_dialog()

    def refresh_table(self):
        """Refresh the table with current data."""
        self.root.ids.projects_table.row_data = self.projects_data
        Clock.schedule_once(self.apply_color_coding, 0.5)

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"

    def clear_filters(self):
        """Clear all filters and reset table to show all data."""
        self.refresh_table()


class ProjectsTableScreen(MDScreen):
    """Main screen for projects table application."""
    pass


if __name__ == "__main__":
    ProjectsTableApp().run()
