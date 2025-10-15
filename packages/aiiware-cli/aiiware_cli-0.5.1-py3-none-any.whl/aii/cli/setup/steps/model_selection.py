"""
Model selection step for setup wizard.

Allows users to choose which model to use for their selected provider.
"""

from typing import Any
from aii.cli.setup.steps.base import WizardStep, StepResult


class ModelSelectionStep(WizardStep):
    """
    Step 1.5: Choose Model (optional customization).

    Shows available models for the selected provider and lets
    user choose or accept the recommended default.
    """

    title = "Choose Model (Optional)"

    MODELS = {
        "anthropic": {
            "default": "claude-sonnet-4-5-20250929",
            "models": {
                "1": {
                    "name": "Claude Sonnet 4.5",
                    "id": "claude-sonnet-4-5-20250929",
                    "description": "Best for complex agents and coding (200k context)",
                    "recommended": True
                },
                "2": {
                    "name": "Claude Opus 4.1",
                    "id": "claude-opus-4-1-20250805",
                    "description": "Exceptional for specialized complex tasks (200k context)"
                },
                "3": {
                    "name": "Claude Sonnet 4",
                    "id": "claude-sonnet-4-20250514",
                    "description": "High-performance model (200k context)"
                },
                "4": {
                    "name": "Claude Sonnet 3.7",
                    "id": "claude-3-7-sonnet-20250219",
                    "description": "Extended thinking capabilities (200k context)"
                },
                "5": {
                    "name": "Claude Haiku 3.5",
                    "id": "claude-3-5-haiku-20241022",
                    "description": "Fastest, most economical (200k context)"
                }
            }
        },
        "openai": {
            "default": "gpt-5",
            "models": {
                "1": {
                    "name": "GPT-5",
                    "id": "gpt-5",
                    "description": "Best for coding and agentic tasks across domains (Recommended)",
                    "recommended": True
                },
                "2": {
                    "name": "GPT-5 mini",
                    "id": "gpt-5-mini",
                    "description": "Faster, cost-efficient GPT-5 for well-defined tasks"
                },
                "3": {
                    "name": "GPT-5 nano",
                    "id": "gpt-5-nano",
                    "description": "Fastest, most cost-efficient version of GPT-5"
                },
                "4": {
                    "name": "GPT-4.1",
                    "id": "gpt-4.1",
                    "description": "Smartest non-reasoning model (1M context)"
                },
                "5": {
                    "name": "GPT-4o",
                    "id": "gpt-4o",
                    "description": "Multimodal with vision, audio, real-time"
                },
                "6": {
                    "name": "GPT-4o mini",
                    "id": "gpt-4o-mini",
                    "description": "Fast, affordable, good balance"
                },
                "7": {
                    "name": "GPT-4.1 mini",
                    "id": "gpt-4.1-mini",
                    "description": "Compact, efficient GPT-4.1"
                },
                "8": {
                    "name": "GPT-4 Turbo",
                    "id": "gpt-4-turbo",
                    "description": "Previous generation (legacy)"
                }
            }
        },
        "gemini": {
            "default": "gemini-2.5-flash",
            "models": {
                "1": {
                    "name": "Gemini 2.5 Flash",
                    "id": "gemini-2.5-flash",
                    "description": "Great, well-rounded capabilities (Recommended)",
                    "recommended": True
                },
                "2": {
                    "name": "Gemini 2.5 Pro",
                    "id": "gemini-2.5-pro",
                    "description": "Most advanced reasoning for complex problems"
                },
                "3": {
                    "name": "Gemini 2.5 Flash-Lite",
                    "id": "gemini-2.5-flash-lite",
                    "description": "Optimized for low-latency, cost-conscious apps"
                },
                "4": {
                    "name": "Gemini 2.0 Flash",
                    "id": "gemini-2.0-flash-001",
                    "description": "Next-gen multimodal with superior speed"
                },
                "5": {
                    "name": "Gemini 2.0 Flash-Lite",
                    "id": "gemini-2.0-flash-lite-001",
                    "description": "Fastest and most cost-efficient"
                }
            }
        }
    }

    async def execute(self, context: Any) -> StepResult:
        """
        Display model options and capture selection.

        Args:
            context: WizardContext with provider already selected

        Returns:
            StepResult with success=True if model selected
        """
        if not context.provider:
            return StepResult(
                success=False,
                message="No provider selected",
                fix_suggestion="This is a bug - provider should be selected first"
            )

        provider_models = self.MODELS.get(context.provider)
        if not provider_models:
            # Provider has no model options, use default
            return StepResult(
                success=True,
                message=f"Using default model for {context.provider}"
            )

        default_model = provider_models["default"]
        models = provider_models["models"]

        # Build choices for interactive menu
        menu_choices = []
        default_index = 0

        for num, info in models.items():
            model_desc = f"{info['name']}"
            if info.get("recommended"):
                model_desc += " (Recommended)"
                default_index = len(menu_choices)
            model_desc += f" - {info['description']}"
            menu_choices.append((num, model_desc))

        # Add custom option
        max_choice = len(models)
        custom_choice = str(max_choice + 1)
        menu_choices.append((custom_choice, "Custom model ID - Enter your own model ID"))

        # Use interactive menu with arrow keys
        choice = self._interactive_menu(
            "Which model would you like to use?",
            menu_choices,
            default_index=default_index
        )

        # Use default if empty
        if not choice:
            selected_model = default_model
            model_name = next(
                (m["name"] for m in models.values() if m["id"] == default_model),
                "Default"
            )
        elif choice == custom_choice:
            # Custom model ID
            self.console.print("\n📝 Enter custom model ID:", style="yellow bold")
            self.console.print(
                f"   Examples for {context.provider}:",
                style="dim"
            )

            # Show provider-specific examples
            examples = {
                "anthropic": "claude-opus-5-20260101, claude-sonnet-5-20260101",
                "openai": "gpt-6, gpt-5.5-turbo, o3-mini",
                "gemini": "gemini-3.0-flash, gemini-2.5-pro-exp"
            }

            if context.provider in examples:
                self.console.print(f"   {examples[context.provider]}", style="cyan dim")

            custom_model = input("\nModel ID: ").strip()

            if not custom_model:
                self.console.print("\n⚠️  No model ID provided, using default", style="yellow")
                selected_model = default_model
                model_name = "Default"
            else:
                selected_model = custom_model
                model_name = f"Custom ({custom_model})"
                self.console.print(
                    f"\n⚠️  Using custom model: {custom_model}",
                    style="yellow bold"
                )
                self.console.print(
                    "   Note: Ensure this model ID is valid for your provider",
                    style="dim"
                )
        else:
            model_info = models[choice]
            selected_model = model_info["id"]
            model_name = model_info["name"]

        # Store in context
        context.selected_model = selected_model

        self.console.print(
            f"\n✓ Selected model: {model_name}",
            style="green bold"
        )

        return StepResult(
            success=True,
            message=f"Selected model: {selected_model}",
            data={"model": selected_model}
        )

    def _display_models(self, models: dict):
        """Display model options."""
        for choice, info in models.items():
            recommended = " ← Recommended" if info.get("recommended") else ""
            self.console.print(
                f"\n  {choice}. {info['name']}{recommended}",
                style="cyan bold" if info.get("recommended") else "cyan"
            )
            self.console.print(f"     {info['description']}", style="dim")
