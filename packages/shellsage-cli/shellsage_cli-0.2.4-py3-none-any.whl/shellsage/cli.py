from __future__ import annotations
import subprocess
import textwrap
import typer
from rich.console import Console
from rich.panel import Panel
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from shellsage.utils import retrieve_context, build_or_load_index

app = typer.Typer(
    add_completion=False,
    help="ShellSage: Explain Linux commands using docs + AI"
)
console = Console()
_generator = None
_tokenizer = None


def _get_generator():
    """Lazy-load the instruction-tuned LM (Qwen2.5-0.5B-Instruct, CPU)."""
    global _generator, _tokenizer
    if _generator is None or _tokenizer is None:
        console.print("[yellow]Loading Qwen2.5-0.5B-Instruct on CPU...[/yellow]")
        model_name = "Qwen/Qwen2.5-0.5B-Instruct"
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        _generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=_tokenizer,
            device=-1,
        )
    return _generator, _tokenizer


def _format_context(docs, max_chars: int = 500) -> str:
    parts = []
    for d in docs:
        header = f"[Source: {d.get('path', 'unknown')}]"
        body = (d.get("text") or "").strip()
        if len(body) > max_chars:
            body = body[:max_chars] + " ..."
        parts.append(f"{header}\n{body}")
    return "\n\n".join(parts)


def _clean_explanation(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    # Find the first sentence ending with ., !, or ?
    for i, char in enumerate(text):
        if char in '.!?':
            return text[:i+1].strip()
    # If no punctuation found, take the first line and add a period
    lines = text.splitlines()
    if lines:
        first_line = lines[0].strip()
        if not first_line.endswith('.'):
            first_line += '.'
        return first_line
    return ""


@app.command()
def main(
    command: List[str] = typer.Argument(..., help="The shell command to run and explain."),
    top_k: int = typer.Option(3, "--top-k", help="Number of docs to retrieve for context"),
):
    """
    Run a Linux command and explain it using ShellSage AI.
    Usage: shellsage "ls -la"
    """
    raw_command = " ".join(command)
    if not raw_command:
        console.print("[red]No command provided.[/red]")
        raise typer.Exit(1)

    console.rule("[b]ShellSage[/b]")
    console.print(f"[bold cyan]Running Command:[/bold cyan] {raw_command}\n")

    # Run the command
    try:
        result = subprocess.run(raw_command, shell=True, check=False, text=True, capture_output=True)
        console.print(result.stdout or "[dim]No output[/dim]")
        if result.stderr:
            console.print(f"[red]{result.stderr}[/red]")
    except Exception as e:
        console.print(f"[red]Failed to run command: {e}[/red]")

    # Load FAISS index
    build_or_load_index(force_rebuild=False)

    # Retrieve context
    docs = retrieve_context(raw_command, top_k=top_k)
    context_str = _format_context(docs) if docs else ""

    # Prepare prompt
    prompt = textwrap.dedent(f"""
        Explain this Linux command in clear, beginner-friendly English.
        Include what it does, option breakdown, practical example, and any caveats.
        Context:
        {context_str}

        Command:
        {raw_command}

        Explanation:
    """).strip()

    # Generate explanation
    try:
        generator, _ = _get_generator()
        out = generator(prompt, max_new_tokens=256, num_beams=4)
        explanation = out[0]["generated_text"].split("Explanation:", 1)[-1].strip()
        console.print(Panel(explanation, title="ShellSage Explanation"))
    except Exception as e:
        console.print(f"[red]Failed to generate AI explanation: {e}[/red]")
        console.print("[yellow]Make sure you have internet connection for first-time model download.[/yellow]")


if __name__ == "__main__":
    app()

