"""Defines the callbacks of the Spinal Tap application."""

import numpy as np
import spine.data.out
from dash import ctx, dcc, no_update
from dash.dependencies import Input, Output, State
from spine.vis import Drawer

from .utils import initialize_reader, load_data


def register_callbacks(app):
    """Registers the callbacks to the Dash application.

    Parameters
    ----------
    app : dash.Dash
         Dash application
    """

    @app.callback(
        [
            Output("div-evd", "children"),
            Output("input-entry", "value"),
            Output("input-run", "value"),
            Output("input-subrun", "value"),
            Output("input-event", "value"),
            Output("text-info", "value"),
        ],
        [
            Input("button-load", "n_clicks"),
            Input("button-previous", "n_clicks"),
            Input("button-next", "n_clicks"),
            Input("dropdown-attr-color", "value"),
        ],
        [
            State("input-file-path", "value"),
            State("input-entry", "value"),
            State("input-run", "value"),
            State("input-subrun", "value"),
            State("input-event", "value"),
            State("input-entry", "disabled"),
            State("radio-run-mode", "value"),
            State("radio-object-mode", "value"),
            State("dropdown-attr", "value"),
            State("checklist-draw-mode-1", "value"),
            State("checklist-draw-mode-2", "value"),
            State("dropdown-geo", "value"),
        ],
    )
    def update_graph(
        n_clicks_load,
        n_clicks_prev,
        n_clicks_next,
        draw_attr,
        file_path,
        entry,
        run,
        subrun,
        event,
        use_run,
        mode,
        obj,
        attrs,
        draw_mode_1,
        draw_mode_2,
        geo,
    ):
        """Callback which builds the graph given all the selections.

        Parameters
        ----------
        n_clicks_load : int
            Number of time the load button has been clicked
        n_clicks_prev : int
            Number of time the previous button has been clicked
        n_clicks_next : int
            Number of time the next button has been clicked
        file_path : str
            Path to the input file
        entry : int
            Entry number
        entry_prev : int
            Previous entry number
        run : int
            Run number
        subrun : int
            Subrun number
        event : int
            Event number
        use_run : bool
            If `True`, use (run, subrun, event) to load the entry
        mode : str
            Drawer run mode ('reco', 'truth' or 'both')
        obj : str
            Objects to be drawn ('fragments', 'particles' or 'interactions')
        attrs : List[str]
            List of attributes to draw in the graph
        draw_attr : str
            Attribute to use to fetch the colorscale
        draw_lmode : List[str]
            Drawing options
        geo : str
            Detector name

        Returns
        -------
        dcc.Graph
            Dash graph containing the event display(s)
        int
            Entry number currently loaded in the graph
        int
            Run number currently loaded in the graph
        int
            Subrun number currently loaded in the graph
        int
            Event number currently loaded in the graph
        str
            Message to be displayed in the text area
        """
        # If one of the button is yet to be pressed, supress update
        trigger = ctx.triggered_id
        if trigger is None:
            return [no_update] * 6

        # Initialize the reader (throw if the file is not specified/found)
        skip = [no_update] * 5
        if file_path is None or len(file_path) == 0:
            msg = "Must specify a file path..."
            return *skip, msg

        else:
            try:
                reader = initialize_reader(file_path, use_run)
                msg = f"File(s) found with {len(reader)} entries"
            except FileNotFoundError:
                msg = f"File(s) not found:\n{file_path}"
                return (*skip, msg)
            except Exception as e:
                msg = repr(e)
                return (*skip, msg)

        # Check that the appropriate information is provided, abort otherwise
        if not use_run and entry is None:
            msg += "\nMust provide an entry number"
            return (*skip, msg)

        elif use_run and (run is None or subrun is None or event is None):
            msg += "\nMust provide run, subrun and event numbers"
            return (*skip, msg)

        # If using the run info, translate the triplet to an entry number
        if use_run:
            try:
                entry = reader.get_run_event_index(run, subrun, event)
            except AssertionError:
                known_triplets = np.vstack(list(reader.run_map.keys()))
                msg += (
                    f"\n(run, subrun, event) = ({run}, {subrun}, {event}) "
                    "not found in the file(s) provided. Must be one of:"
                    f"{known_triplets}"
                )
                return (*skip, msg)

        # Update the entry number of the previous/next button was pressed
        # Supress updates entirely if we are out of range
        if "previous" in trigger:
            if entry == 0:
                return (*skip, no_update)
            entry -= 1

        elif "next" in trigger:
            if entry >= len(reader) - 1:
                return (*skip, no_update)
            entry += 1

        # Check on the entry number
        if entry >= len(reader):
            msg += f"\nEntry {entry} not found in file(s) provided"
            return (*skip, msg)

        msg += f"\nLoaded entry {entry}"

        # Load data for this entry
        data, run, subrun, event = load_data(reader, entry, mode, obj)
        if run is not None:
            msg += f"\nRun: {run}, subrun: {subrun}, event: {event}"

        # Intialize the drawer, fetch plot
        draw_mode = draw_mode_1 + draw_mode_2
        drawer = Drawer(
            data,
            draw_mode=mode,
            detector=geo,
            split_scene="split_scene" in draw_mode,
            show_crt="crt" in draw_mode,
        )

        # Process the attributes to draw
        if attrs is not None:
            if len(attrs) == 0:
                attrs = None

        # Fetch plot, return
        if attrs is not None and len(attrs) == 0:
            attrs = None
        figure = drawer.get(
            obj,
            attrs,
            color_attr=draw_attr,
            draw_raw="raw" in draw_mode,
            draw_end_points="point" in draw_mode,
            draw_directions="direction" in draw_mode,
            draw_vertices="vertex" in draw_mode,
            draw_flashes="flash" in draw_mode,
            matched_flash_only="flash_match_only" in draw_mode,
            draw_crthits="crt" in draw_mode,
            matched_crthit_only="crt_match_only" in draw_mode,
            synchronize="sync" in draw_mode,
            split_traces="split_traces" in draw_mode,
        )

        return (
            dcc.Graph(figure=figure, id="graph-evd"),
            entry,
            run,
            subrun,
            event,
            msg,
        )

    @app.callback(
        [
            Output("button-source", "children"),
            Output("input-entry", "style"),
            Output("input-run", "style"),
            Output("input-subrun", "style"),
            Output("input-event", "style"),
            Output("input-entry", "disabled"),
            Output("input-run", "disabled"),
            Output("input-subrun", "disabled"),
            Output("input-event", "disabled"),
        ],
        Input("button-source", "n_clicks"),
        State("button-source", "children"),
    )
    def update_entry_input(n_clicks, label):
        """Callback which updates the input entry source (file entry or
        (run, subrun, event) combination.

        Parameters
        ----------
        n_clicks : int
            Number of type the switch was pressed
        label : str
            Label on the button

        Returns
        -------
        str
            Name (purpose) of the button
        str
            Whether to display the entry box or not
        str
            Whether to display the run box or not
        str
            Whether to display the subrun box or not
        str
            Whether to display the event box or not
        bool
            Whether the entry box is disabled or not
        bool
            Whether the run box is disabled or not
        bool
            Whether the subrun box is disabled or not
        bool
            Whether the event box is disabled or not
        """
        # If the button is yet to be pressed, leave it alone
        if n_clicks is None:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        # Switch the button children
        name = "Entry #" if "Run" in label else "Run #"

        # If the toggle is on, switch to (run, subrun, event) input
        on = {"display": "block", "width": "100%"}
        off = {"display": "none", "width": "100%"}
        if "Run" in label:
            return name, on, off, off, off, False, True, True, True

        else:
            return name, off, on, on, on, True, False, False, False

    @app.callback(
        Output("dropdown-attr", "options"),
        [Input("radio-run-mode", "value"), Input("radio-object-mode", "value")],
    )
    def update_attr_list(mode, obj):
        """Callback which updates the set of recognized attributes when the
        object type being drawn changes.

        Parameters
        ----------
        mode : str
            Drawer run mode ('reco', 'truth' or 'both')
        obj : str
            Objects to be drawn ('fragments', 'particles' or 'interactions')

        Returns
        -------
        List[str]
            List of available attributes
        """
        # Based on what needs to drawn, figure out available attributes
        if mode != "truth":
            cls_name = f"Reco{obj[:-1].capitalize()}"
            cls = getattr(spine.data.out, cls_name)
            attrs = set({"depositions"})
            attrs.update(set(cls().as_dict().keys()))

        if mode != "reco":
            cls_name = f"Truth{obj[:-1].capitalize()}"
            cls = getattr(spine.data.out, cls_name)
            attrs = set(
                {
                    "depositions",
                    "depositions_q",
                    "depositions_adapt",
                    "depositions_adapt_q",
                    "depositions_g4",
                }
            )
            attrs.update(set(cls().as_dict().keys()))

        return np.sort(list(attrs))

    @app.callback(
        Output("dropdown-attr-color", "options"), Input("dropdown-attr", "value")
    )
    def update_attr_color_list(attrs):
        """Callback which updates the set of attributes which can be used as
        a colorscale on the plot.

        Parameters
        ----------
        attrs : List[str]
            List of attributes currently displayed as hovertext

        Returns
        -------
        List[str]
            List of attributes which may be used as a colorscale
        """
        # Select out the attributes which are known to be valid
        draw_attrs = []
        if attrs is not None:
            for attr in attrs:
                if (
                    attr.startswith("depositions")
                    or attr.startswith("is_")
                    or attr.endswith("id")
                    or attr in ["shape", "pid"]
                ):
                    draw_attrs.append(attr)

        return draw_attrs
