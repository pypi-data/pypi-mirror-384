import os
from abc import ABC, abstractmethod
from typing import Optional

from solidipes.utils import get_completed_stages

from .solidipes_buttons import SolidipesButtons as SPB
from .solidipes_widget import SolidipesWidget as SPW

css_path = os.path.join(os.path.dirname(__file__), "step_bar.css")
css = open(css_path, encoding="utf-8").read()


class Step(ABC):
    def __init__(
        self,
        label: str,
        url: str,
    ):
        self.label: str = label
        self.url: str = url
        self.reached: bool = False
        self.current: bool = False

    @abstractmethod
    def render(self) -> str:
        """Render the step as HTML."""


class MainStep(Step):
    def __init__(
        self,
        label: str,
        url: str,
        substeps: list["SubStep"] = [],
    ):
        super().__init__(label, url)
        self.substeps: list["SubStep"] = substeps or []
        self.completed: Optional[bool] = None

    def render(self) -> str:
        class_names = []

        if self.reached:
            class_names.append("reached")

        if self.current:
            class_names.append("current")

        if self.completed is not None:
            class_names.append("completed" if self.completed else "incomplete")

        class_names_str = " ".join(class_names)

        return f"""
<div class="step-container">
    <a class="main-step {class_names_str}" href={self.url} target="_self">{self.label}</a>
    <a class="icon {class_names_str}" href={self.url} target="_self"></a>
    <div class="substeps {class_names_str}">
        {"".join(substep.render() for substep in self.substeps)}
    </div>
</div>
        """


class SubStep(Step):
    def __init__(
        self,
        label: str,
        url: str,
    ):
        super().__init__(label, url)

    def render(self) -> str:
        class_names = []

        if self.reached:
            class_names.append("reached")

        if self.current:
            class_names.append("current")

        class_names_str = " ".join(class_names)

        return f"""<a class="substep {class_names_str}" href={self.url} target="_self">{self.label}</a>"""


class StepBar(SPW):
    def __init__(self, current_step: str, uploader: str | None, **kwargs):
        from solidipes.plugins.discovery import uploader_list

        super().__init__(**kwargs)

        main_steps_names = ["acquisition", "curation", "metadata", "export"]

        if current_step not in main_steps_names:
            raise ValueError(f"current_step must be one of the steps: {main_steps_names}")

        # Create step objects
        steps = [
            MainStep(
                "Acquisition",
                "?page=acquisition",
                [
                    SubStep("File Browser", "?page=acquisition"),
                ],
            ),
            MainStep(
                "Curation",
                "?page=curation",
                [
                    SubStep("Solidipes", "?page=curation"),
                ],
            ),
            MainStep("Metadata", "?page=metadata"),
            MainStep(
                "Export",
                "?page=export",
                [
                    SubStep("Zenodo", "?page=export"),
                ],
            ),
        ]

        # Add uploaders as plugins
        uploader_names = [u.parser_key for u in uploader_list]
        uploader_steps = []
        for names in uploader_names:
            if not isinstance(names, list):
                names = [names]
            for n in names:
                if n == "zenodo":
                    continue
                if "rclone" in n and n != "rclone":
                    continue
                uploader_steps.append(n)
        for n in sorted(uploader_steps):
            steps[3].substeps.append(SubStep(n.capitalize(), f"?page=export&uploader={n}"))

        # Add Jupyter link to Acquisition and Curation steps
        try:
            jupyter_url = SPB()._get_jupyter_link()
            for i in [0, 1]:
                steps[i].substeps.append(SubStep("Jupyter", jupyter_url))
        except Exception:
            pass

        # Mark reached, current, and completed steps
        completed_stages = get_completed_stages()
        reached_index = main_steps_names.index(current_step)

        for i, step in enumerate(steps):
            reached = i <= reached_index
            step.reached = reached
            step.current = i == reached_index
            step.completed = i in completed_stages if i != 3 else None

            for substep in step.substeps:
                substep.reached = reached
                if step.label == "Export" and current_step == "export":
                    substep.current = f"uploader={uploader}" in substep.url if uploader else substep.label == "Zenodo"
                else:
                    substep.current = substep.url == f"?page={current_step}"

        # Render step bar
        self.layout.html(f"""
<style>
    {css}
</style>

<div class="step-bar-container">
    {"".join(step.render() for step in steps)}
</div>
        """)
