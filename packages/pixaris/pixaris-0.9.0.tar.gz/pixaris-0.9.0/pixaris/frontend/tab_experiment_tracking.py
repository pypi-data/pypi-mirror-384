import gradio as gr
from pixaris.experiment_handlers.base import ExperimentHandler
import pandas as pd

PROJECTS = []


def render_experiment_tracking_tab(
    experiment_handler: ExperimentHandler,
    results_directory: str,
):
    dataset_experiment_tracking_results = gr.State(pd.DataFrame())
    with gr.Row():
        # Sidebar on the left
        with gr.Column(scale=2, min_width=250):
            gr.Markdown("Experiments")
            # load all projects and corresponding datasets at the beginning
            PROJECTS_DICT = experiment_handler.load_projects_and_datasets()
            global PROJECTS
            PROJECTS = [""] + list(PROJECTS_DICT.keys())

            project_name = gr.Dropdown(
                choices=PROJECTS,
                label="Project",
                filterable=True,
            )

            # initialise hidden dataset and define updating function
            dataset = gr.Dropdown(visible=False)

            def update_dataset_choices(project_name, dataset):
                """Update choices of feedback iterations for selected project and display reload button."""
                dataset_choices = PROJECTS_DICT[project_name]
                dataset = gr.Dropdown(
                    label="Dataset",
                    choices=dataset_choices,
                    filterable=True,
                    multiselect=False,
                    interactive=True,
                    visible=True,
                )
                return dataset

            # change dataset choices upon project change
            project_name.change(
                fn=update_dataset_choices,
                inputs=[project_name, dataset],
                outputs=[dataset],
            )

            # initialise hidden experiments and define updating function
            experiments = gr.Dropdown(visible=False)

            def update_experiments_choices_and_load_table(
                project_name, dataset, experiments, dataset_experiment_tracking_results
            ):
                """Update choices of feedback iterations for selected project and display reload button."""
                dataset_experiment_tracking_results = (
                    experiment_handler.load_experiment_results_for_dataset(
                        project=project_name,
                        dataset=dataset,
                    )
                )
                experiment_choices = list(
                    dataset_experiment_tracking_results["experiment_run_name"]
                    .dropna()
                    .unique()
                )
                experiment_choices.sort()
                experiments = gr.Dropdown(
                    choices=experiment_choices,
                    label="Experiments",
                    filterable=True,
                    multiselect=True,
                    max_choices=100,
                    visible=True,
                )
                return experiments, dataset_experiment_tracking_results

            # change experiments choices and load table upon dataset change
            dataset.change(
                fn=update_experiments_choices_and_load_table,
                inputs=[
                    project_name,
                    dataset,
                    experiments,
                    dataset_experiment_tracking_results,
                ],
                outputs=[experiments, dataset_experiment_tracking_results],
            )

            reload_projects_button = gr.Button(
                "Reload projects",
                variant="secondary",
                interactive=True,
                size="sm",
            )

            def reload_projects(project_name):
                PROJECTS_DICT = experiment_handler.load_projects_and_datasets()
                global PROJECTS
                PROJECTS = [""] + list(PROJECTS_DICT.keys())
                return project_name

            reload_projects_button.click(
                fn=reload_projects,
                inputs=[project_name],
                outputs=[project_name],
            )

            # columns and gallery height sliders
            columns = gr.Slider(
                minimum=1,
                maximum=20,
                value=8,
                label="Number of images per row",
                step=1,
            )
            gallery_height = gr.Slider(
                minimum=100,
                maximum=1000,
                value=200,
                label="Gallery height",
                step=10,
            )

        # Main content on the right
        with gr.Column(scale=8):
            with gr.Tab("Images"):
                # Display images in a gallery

                @gr.render(
                    inputs=[project_name, dataset, experiments, columns, gallery_height]
                )
                def render_images_per_experiment(
                    project_name, dataset, experiments, columns, gallery_height
                ):
                    """
                    Renders one accordion with a gallery per experiment. Render decorator enables listening to experiments checkbox group.
                    """
                    if not experiments:
                        gr.Markdown("No experiment selected.")
                        return
                    for experiment_name in experiments:
                        with gr.Accordion(label=f"Experiment {experiment_name}"):
                            experiment_images = (
                                experiment_handler.load_images_for_experiment(
                                    project=project_name,
                                    dataset=dataset,
                                    experiment_run_name=experiment_name,
                                    local_results_directory=results_directory,
                                )
                            )
                            gr.Gallery(
                                value=experiment_images,
                                columns=columns,
                                rows=1,
                                show_download_button=True,
                                show_fullscreen_button=True,
                                height=gallery_height,
                                object_fit="contain",
                            )

            with gr.Tab("Table"):
                # Display experiment results in a table

                @gr.render(inputs=[experiments, dataset_experiment_tracking_results])
                def render_experiment_results_table(
                    experiments, dataset_experiment_tracking_results
                ):
                    if not experiments:
                        gr.Markdown("No experiment selected.")
                        return

                    table_data = dataset_experiment_tracking_results.copy()
                    table_data = table_data.loc[
                        dataset_experiment_tracking_results["experiment_run_name"].isin(
                            experiments
                        )
                    ]
                    gr.DataFrame(
                        table_data,
                        label="Experiment Results",
                        wrap=True,
                        show_search="filter",
                        max_height=1000,
                    )
