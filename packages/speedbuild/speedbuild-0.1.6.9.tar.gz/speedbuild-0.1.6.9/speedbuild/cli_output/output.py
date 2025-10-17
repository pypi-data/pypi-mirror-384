from rich.console import Console

class StatusManager:
    def __init__(self):
        self.console = Console()
        self.status = None

    def start_status(self,msg):
        self.status = self.console.status(f"[bold cyan]{msg}[/bold cyan]")
        self.status.start()
        return self.status

    def update_status(self, message):
        if self.status:
            self.status.update(f"[bold cyan]{message}[/bold cyan]")

    def stop_status(self, msg=None):
        if self.status:
            self.status.stop()
            if msg:
                self.console.print(f"[bold cyan]{msg}[/bold cyan]")

    def print_message(self,msg):
        self.console.print(f"[cyan]{msg}[/cyan]")