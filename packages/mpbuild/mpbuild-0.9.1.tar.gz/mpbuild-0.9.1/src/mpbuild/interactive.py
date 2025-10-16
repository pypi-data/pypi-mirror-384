"""
Interactive TUI for mpbuild using Textual.
"""
from pathlib import Path
from typing import Any, Optional

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Footer, Header, Label, Static, Tree
from textual.widgets.tree import TreeNode
import subprocess

from . import board_database
from .board_database import Board, Port, Variant
from .build import docker_build_cmd


class BoardDetails(Static):
    """Widget to display details about a selected board."""

    def __init__(self, board: Optional[Board] = None) -> None:
        super().__init__()
        self.board = board

    def update_board(self, board: Optional[Board]) -> None:
        """Update the displayed board details."""
        self.board = board
        self.update_content()

    def update_content(self) -> None:
        """Update the content based on the current board."""
        if self.board is None:
            self.update(f"No board selected")
            return

        # Build details about the board
        content = f"# {self.board.product}\n\n"
        content += f"**Board:** {self.board.name}\n"
        content += f"**Port:** {self.board.port.name}\n"
        content += f"**MCU:** {self.board.mcu}\n"
        content += f"**Vendor:** {self.board.vendor}\n"
        
        if self.board.variants:
            content += f"\n**Variants:**\n"
            for variant in self.board.variants:
                content += f"- {variant.name}: {variant.text}\n"
        
        if self.board.url:
            content += f"\n**URL:** {self.board.url}\n"
        
        # Add pins information
        pins = self.board.pins
        if pins:
            content += f"\n**Pins:** ({len(pins)} pins)\n"
            
            # Group pins by type for better display
            cpu_pins = [p for p in pins if not p.functional_name or p.functional_name == p.mcu_pin]
            board_pins = [p for p in pins if p.functional_name and p.functional_name != p.mcu_pin]
            
            if board_pins:
                content += "\n*Board Pins:*\n"
                for pin in sorted(board_pins, key=lambda p: p.functional_name):
                    content += f"- {pin.functional_name} → {pin.mcu_pin}\n"
            
            if cpu_pins:
                content += "\n*CPU Pins:*\n"
                # Show only first 20 CPU pins to avoid overwhelming the display
                displayed_pins = sorted(cpu_pins, key=lambda p: p.mcu_pin)[:20]
                for pin in displayed_pins:
                    content += f"- {pin.mcu_pin}\n"
                
                if len(cpu_pins) > 20:
                    content += f"... and {len(cpu_pins) - 20} more CPU pins\n"
        else:
            content += f"\n**Pins:** No pins.csv file found\n"
        
        self.update(content)
        
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        self.update_content()
        yield from []


class BuildLog(Static):
    """Widget to display build logs."""
    
    def clear_log(self) -> None:
        """Clear the build log."""
        self.update("")
        
    def add_log(self, text: str) -> None:
        """Add text to the build log."""
        current = self.render()
        self.update(f"{current}\n{text}")


class MpbuildApp(App):
    """A Textual app for interactive mpbuild."""

    CSS = """
    #tree-view {
        width: 25%;
        min-width: 20;
        border: solid cornflowerblue;
    }
    
    #details-panel {
        border: solid cornflowerblue;
        height: 60%;
        padding: 1;
    }
    
    #log-panel {
        height: 40%;
        border: solid cornflowerblue;
        padding: 1;
        overflow: auto;
    }
    
    #build-button {
        margin: 1;
    }
    
    .build-controls {
        height: auto;
        align: center middle;
    }
    
    Tree {
        padding: 1;
    }
    
    Header {
        background: cornflowerblue;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("b", "build", "Build"),
    ]

    def __init__(self, mpy_dir: Optional[Path] = None) -> None:
        """Initialize the app."""
        super().__init__()
        self.db = board_database(mpy_dir)
        self.selected_board: Optional[Board] = None
        self.selected_variant: Optional[Variant] = None
        self.building = False

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)
        with Horizontal():
            yield Tree("MicroPython Boards", id="tree-view")
            with Vertical():
                yield BoardDetails(id="details-panel")
                with Container(classes="build-controls"):
                    yield Button("Build", id="build-button", disabled=True)
                yield BuildLog("", id="log-panel")
        yield Footer()

    def on_mount(self) -> None:
        """Event fired when the app is mounted."""
        # Populate the tree with ports and boards
        tree = self.query_one(Tree)
        
        # Create nodes for each port
        for port_name, port in sorted(self.db.ports.items()):
            port_node = tree.root.add(f"{port_name} ({len(port.boards)})", {"type": "port", "port": port})
            
            # Add boards for this port
            for board_name, board in sorted(port.boards.items()):
                variant_text = ""
                if board.variants:
                    variant_names = [v.name for v in board.variants]
                    variant_text = f" [{', '.join(variant_names)}]"
                board_node = port_node.add(f"{board_name}{variant_text}", {"type": "board", "board": board})
        
        tree.root.expand()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Event fired when a tree node is selected."""
        node_data = event.node.data
        if node_data and node_data.get("type") == "board":
            self.selected_board = node_data["board"]
            self.selected_variant = None
            self.query_one(BoardDetails).update_board(self.selected_board)
            self.query_one("#build-button").disabled = False
        else:
            self.selected_board = None
            self.selected_variant = None
            self.query_one(BoardDetails).update_board(None)
            self.query_one("#build-button").disabled = True

    @on(Button.Pressed, "#build-button")
    def on_build_button(self) -> None:
        """Event fired when the build button is pressed."""
        if self.selected_board and not self.building:
            self.action_build()

    def action_build(self) -> None:
        """Build the selected board."""
        if not self.selected_board or self.building:
            return
            
        self.building = True
        self.query_one("#build-button").disabled = True
        
        # Clear the log and show build starting
        log_widget = self.query_one(BuildLog)
        log_widget.clear_log()
        log_widget.add_log(f"Building {self.selected_board.name}...")
        
        # Start the build process
        self.start_build()
        
    def start_build(self) -> None:
        """Start the build process in the background."""
        if not self.selected_board:
            return
            
        log_widget = self.query_one(BuildLog)
        
        try:
            build_cmd = docker_build_cmd(
                board=self.selected_board,
                variant=self.selected_variant.name if self.selected_variant else None,
                extra_args=[],
                do_clean=False,
                docker_interactive=False,
            )
            
            log_widget.add_log(f"Running: {build_cmd}")
            
            # Start the process and set up to capture output
            self.set_interval(0.1, self.check_build_output)
            
            # Start the build process and capture output
            self.build_process = subprocess.Popen(
                build_cmd, 
                shell=True, 
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            
        except Exception as e:
            log_widget.add_log(f"Error starting build: {e}")
            self.building = False
            self.query_one("#build-button").disabled = False
    
    def check_build_output(self) -> None:
        """Check for output from the build process."""
        if not hasattr(self, "build_process"):
            return
            
        log_widget = self.query_one(BuildLog)
        
        # Read any available output
        if self.build_process.stdout:
            for line in iter(self.build_process.stdout.readline, ""):
                if not line:
                    break
                log_widget.add_log(line.rstrip())
        
        # Check if process has ended
        if self.build_process.poll() is not None:
            # Process has completed
            returncode = self.build_process.returncode
            log_widget.add_log(f"\nBuild finished with return code: {returncode}")
            
            if returncode == 0:
                log_widget.add_log("Build completed successfully!")
            else:
                log_widget.add_log("Build failed!")
                
            # Clean up
            self.building = False
            self.query_one("#build-button").disabled = False
            
            # Stop checking for output
            self.clear_interval()
            
            # Handle deployment instructions if build succeeded
            if returncode == 0 and self.selected_board.deploy:
                if self.selected_board.deploy_filename.is_file():
                    log_widget.add_log("\nDeployment instructions:")
                    log_widget.add_log(self.selected_board.deploy_filename.read_text())


def run_interactive(mpy_dir: Optional[Path] = None) -> None:
    """Run the interactive TUI application."""
    app = MpbuildApp(mpy_dir)
    app.run()