import typer
import webbrowser


def open_browser(url: str) -> bool:
    try:
        opened = webbrowser.open(url)
        if opened:
            typer.echo("已成功打开浏览器.")
            return True
        else:
            typer.echo("Failed to open the browser.")
            return False
    except Exception as e:
        typer.echo(f"An error occurred when open browser: {e}")
        return False
