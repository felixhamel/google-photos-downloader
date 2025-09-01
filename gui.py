import flet as ft
from datetime import datetime
from pathlib import Path
import threading
import asyncio

# Assuming the downloader class is in app/core/downloader.py
# This might need adjustment based on Python's path resolution
try:
    from app.core.downloader import GooglePhotosDownloader
except (ModuleNotFoundError, ImportError):
    # Fallback for running the script directly from the root directory
    import sys
    sys.path.append(str(Path(__file__).parent / 'app'))
    from core.downloader import GooglePhotosDownloader

def main(page: ft.Page):
    page.title = "Google Photos Downloader"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 700
    page.window_height = 700

    # --- App State ---
    app_state = {
        "start_date": None,
        "end_date": None,
        "folder_path": None,
        "downloader": GooglePhotosDownloader(),
        "is_authenticated": False,
        "is_running": False
    }

    # --- UI Controls ---
    login_button = ft.ElevatedButton("Login to Google", on_click=None) # Click handler assigned later
    auth_status = ft.Text("Status: Not authenticated", color="red")
    start_date_text = ft.Text("Start Date: (Not selected)")
    end_date_text = ft.Text("End Date: (Not selected)")
    folder_path_text = ft.Text("Output Folder: (Not selected)")
    download_button = ft.ElevatedButton("Download Photos", on_click=None, icon=ft.icons.DOWNLOAD, disabled=True)
    status_text = ft.Text("Welcome! Please log in to get started.")
    prog_bar = ft.ProgressBar(value=0, visible=False)

    # --- UI Update Functions (Thread-safe) ---
    def update_status(message: str):
        def _update():
            status_text.value = message
            page.update()
        page.run_thread_safe(_update)

    def update_progress(current: int, total: int, percentage: float, speed: float, eta: int):
        def _update():
            prog_bar.value = percentage / 100
            eta_str = f" ETA: {eta//60}m {eta%60}s" if eta is not None else ""
            status_text.value = f"Downloading: {current}/{total} ({percentage:.1f}%) | {speed:.1f} MB/s{eta_str}"
            page.update()
        page.run_thread_safe(_update)

    # --- Core Logic ---
    def auth_flow():
        app_state["is_running"] = True
        update_status("Authenticating... Please check your web browser.")
        page.run_thread_safe(lambda: page.update())

        try:
            authenticated = app_state["downloader"].authenticate()
            if authenticated:
                app_state["is_authenticated"] = True
                page.run_thread_safe(lambda: setattr(auth_status, "value", "Status: Authenticated"))
                page.run_thread_safe(lambda: setattr(auth_status, "color", "green"))
                update_status("Authentication successful. Ready to download.")
            else:
                app_state["is_authenticated"] = False
                update_status("Authentication failed. Please check logs or credentials.json.")
        except Exception as e:
            app_state["is_authenticated"] = False
            update_status(f"Authentication error: {e}")
        finally:
            app_state["is_running"] = False
            page.run_thread_safe(lambda: page.update())

    def download_flow():
        app_state["is_running"] = True
        page.run_thread_safe(lambda: setattr(prog_bar, "visible", True))
        page.run_thread_safe(lambda: page.update())

        try:
            update_status("Searching for media items...")
            media_items = asyncio.run(app_state["downloader"].get_media_items_async(
                start_date=app_state["start_date"],
                end_date=app_state["end_date"]
            ))

            if not media_items:
                update_status("No media items found in the selected date range.")
                return

            total_items = len(media_items)
            update_status(f"Found {total_items} items. Starting download...")
            app_state["downloader"].stats.start(total_items)

            output_path = Path(app_state["folder_path"])
            output_path.mkdir(exist_ok=True)

            for i, item in enumerate(media_items):
                success, size = asyncio.run(app_state["downloader"].download_media_item_async(item, output_path))
                if success:
                    app_state["downloader"].stats.update(size)
                # The progress callback will handle the UI update
                app_state["downloader"].update_progress(i + 1, total_items, ((i + 1) / total_items) * 100)

            update_status(f"Download complete! {total_items} items processed.")

        except Exception as e:
            update_status(f"An error occurred during download: {e}")
        finally:
            app_state["is_running"] = False
            page.run_thread_safe(lambda: setattr(prog_bar, "visible", False))
            page.run_thread_safe(lambda: setattr(prog_bar, "value", 0))
            page.run_thread_safe(lambda: page.update())

    # --- UI Event Handlers ---
    def handle_login_click(e):
        if not app_state["is_running"]:
            threading.Thread(target=auth_flow, daemon=True).start()

    def check_and_enable_download_button():
        if all([
            app_state["is_authenticated"],
            app_state["start_date"],
            app_state["end_date"],
            app_state["folder_path"]
        ]):
            download_button.disabled = False
        else:
            download_button.disabled = True
        page.update()

    def handle_start_date_change(e):
        app_state["start_date"] = start_date_picker.value
        start_date_text.value = f"Start Date: {app_state['start_date'].strftime('%Y-%m-%d')}"
        check_and_enable_download_button()
        page.update()

    def handle_end_date_change(e):
        app_state["end_date"] = end_date_picker.value
        end_date_text.value = f"End Date: {app_state['end_date'].strftime('%Y-%m-%d')}"
        check_and_enable_download_button()
        page.update()

    def get_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            app_state["folder_path"] = e.path
            folder_path_text.value = f"Output Folder: {e.path}"
        else:
            app_state["folder_path"] = None
            folder_path_text.value = "Output Folder: (Not selected)"
        check_and_enable_download_button()
        page.update()

    def handle_download_click(e):
        if not app_state["is_running"]:
            threading.Thread(target=download_flow, daemon=True).start()

    # --- Initialize UI and Assign Handlers ---
    login_button.on_click = handle_login_click
    download_button.on_click = handle_download_click

    app_state["downloader"].set_callbacks(status_callback=update_status, progress_callback=update_progress)

    start_date_picker = ft.DatePicker(on_change=handle_start_date_change, first_date=datetime(2000, 1, 1), last_date=datetime.now())
    end_date_picker = ft.DatePicker(on_change=handle_end_date_change, first_date=datetime(2000, 1, 1), last_date=datetime.now())
    directory_picker = ft.FilePicker(on_result=get_directory_result)
    page.overlay.extend([start_date_picker, end_date_picker, directory_picker])

    # --- UI Layout ---
    page.add(
        ft.Column(
            controls=[
                ft.Row([login_button, auth_status], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Text("1. Select Date Range", style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Row([
                    ft.ElevatedButton("Select Start Date", icon=ft.icons.CALENDAR_MONTH, on_click=lambda _: start_date_picker.pick_date()),
                    start_date_text
                ]),
                ft.Row([
                    ft.ElevatedButton("Select End Date", icon=ft.icons.CALENDAR_MONTH, on_click=lambda _: end_date_picker.pick_date()),
                    end_date_text
                ]),
                ft.Divider(),
                ft.Text("2. Select Output Folder", style=ft.TextThemeStyle.HEADLINE_SMALL),
                ft.Row([
                    ft.ElevatedButton("Choose Folder", icon=ft.icons.FOLDER_OPEN, on_click=lambda _: directory_picker.get_directory_path(dialog_title="Select Download Folder")),
                    folder_path_text
                ]),
                ft.Divider(),
                ft.Text("3. Start Download", style=ft.TextThemeStyle.HEADLINE_SMALL),
                download_button,
                ft.Column([status_text, prog_bar], spacing=5)
            ],
            spacing=15
        )
    )
    # Initial check
    check_and_enable_download_button()


if __name__ == "__main__":
    ft.app(target=main)
