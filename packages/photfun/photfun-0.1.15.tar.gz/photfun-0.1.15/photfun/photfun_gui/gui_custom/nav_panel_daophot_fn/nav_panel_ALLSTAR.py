from ....misc_tools import daophot_pbar
from ..plot_preview_tools import render_allstar_plots
from shiny import module, reactive, render, ui
from faicons import icon_svg  # Para iconos en botones

@module.ui
def nav_panel_ALLSTAR_ui():
    return ui.page_fillable(
        ui.layout_columns(
            # Columna izquierda - Controles principales
            ui.div(
                ui.input_select("fits_select", "Select FITS", choices={}, width="auto"),
                ui.input_select("table_psf_select", "Select PSF model", choices={}, width="auto"),
                ui.input_select("table_select", "Select Targets", choices={}, width="auto"),
                ui.input_action_button("allstar_btn", "ALLSTAR", icon=icon_svg("sun"), width="auto"),
                style="padding-right: 20px; border-right: 1px solid #dee2e6;"
            ),
            # Columna derecha - Parámetros ALLSTAR
            ui.div(
                ui.tooltip(
                    ui.input_numeric("param_fi", "Fitting Radius (px)", 
                                   value=4,  # Valor por defecto de 'fi' en opt_allstar_dict
                                   step=0.1,
                                   ),
                    "Fitting radius to fit the PSF model"
                ),
                ui.tooltip(
                    ui.input_numeric("param_is", "Inner Sky (px)", 
                                   value=5,  # Valor por defecto de 'is' en opt_allstar_dict
                                   step=0.5,
                                   ),
                    "Inner sky radius for the sky measure"
                ),
                ui.tooltip(
                    ui.input_numeric("param_os", "Outer Sky (px)", 
                                   value=25,  # Valor por defecto de 'is' en opt_allstar_dict
                                   step=0.5,
                                   ),
                    "Outer sky radius for the sky measure"
                ),
                ui.tooltip(
                    ui.input_switch("param_re", "Recentering", value=True),
                    "Automatic recentering on photometry"
                ),
                style="padding-left: 20px;"
            ),
            col_widths=(8, 4)
        )
    )

@module.server
def nav_panel_ALLSTAR_server(input, output, session, photfun_client, nav_table_sideview_update, input_tabs_main, input_tabs_daophot):

    def update_select():
        fits_choices = {str(obj.id): f"[{obj.id}] {obj.alias}" for obj in photfun_client.fits_files}
        prev_selected_fits = str(selected_fits().id) if selected_fits() else None
        ui.update_select("fits_select", choices=fits_choices, selected=prev_selected_fits)
        table_psf_choices = {str(obj.id): f"[{obj.id}] {obj.alias}" for obj in photfun_client.psf_files}
        prev_selected_psf_table = str(selected_psf_table().id) if selected_psf_table() else None
        ui.update_select("table_psf_select", choices=table_psf_choices, selected=prev_selected_psf_table)
        table_choices = {str(obj.id): f"[{obj.id}] {obj.alias}" for obj in photfun_client.tables}
        prev_selected_table = str(selected_table().id) if selected_table() else None
        ui.update_select("table_select", choices=table_choices, selected=prev_selected_table)

    # Cargar opciones de FITS en el select_input
    @reactive.Effect
    @reactive.event(input_tabs_main)
    def _():
        if input_tabs_main()=="DAOPHOT":
            update_select()
            update_settings()
    
    # Cargar opciones de FITS en el select_input
    @reactive.Effect
    @reactive.event(input_tabs_daophot)
    def _():
        if input_tabs_daophot()=="ALLSTAR":
            update_select()
            update_settings()

    # Obtener el FITS seleccionado
    @reactive.Calc
    def selected_fits():
        selected_id = input.fits_select()
        return next((f for f in photfun_client.fits_files if str(f.id) == selected_id), None)

    # Obtener el Table seleccionado
    @reactive.Calc
    def selected_psf_table():
        selected_id = input.table_psf_select()
        return next((t for t in photfun_client.psf_files if str(t.id) == selected_id), None)

    # Obtener el Table seleccionado
    @reactive.Calc
    def selected_table():
        selected_id = input.table_select()
        return next((t for t in photfun_client.tables if str(t.id) == selected_id), None)


    # Modificamos los opt files
    def update_settings():
        # Sincronizar valores iniciales
        ui.update_numeric("param_fi", value=photfun_client.allstar_opt['fi'])
        ui.update_numeric("param_is", value=photfun_client.allstar_opt['is'])
        ui.update_numeric("param_os", value=photfun_client.allstar_opt['os'])
        ui.update_switch("param_re", value=photfun_client.allstar_recentering)

    @reactive.Effect
    @reactive.event(input.param_fi)
    def _():
        photfun_client.allstar_opt['fi'] = float(input.param_fi())
        
    @reactive.Effect
    @reactive.event(input.param_is)
    def _():
        photfun_client.allstar_opt['is'] = float(input.param_is())

    @reactive.Effect
    @reactive.event(input.param_os)
    def _():
        photfun_client.allstar_opt['os'] = float(input.param_os())

    @reactive.Effect
    @reactive.event(input.param_re)
    def _():
        photfun_client.allstar_recentering = input.param_re()

    # Ejecutar ALLSTAR al presionar el botón
    @reactive.Effect
    @reactive.event(input.allstar_btn)
    def allstar_action():
        fits_obj = selected_fits()
        psf_obj = selected_psf_table()
        table_obj = selected_table()
        if fits_obj and psf_obj and table_obj:
            try:
                with ui.Progress(min=0, max=1) as p:
                    pbar = daophot_pbar(p, "Allstar")
                    out_table_obj, out_fits_obj = photfun_client.allstar(fits_obj.id, psf_obj.id, table_obj.id, pbar=pbar)
                ui.notification_show(f"ALLSTAR PSF photometry complete\n -> [{out_table_obj.id}] {out_table_obj.alias}\n (Substracted: [{out_fits_obj.id}] {out_fits_obj.alias})")
            except Exception as e:
                ui.notification_show(f"Error: {str(e)}", type="error")
        else:
            ui.notification_show("Error: FITS not selected.", type="warning")
        
        nav_table_sideview_update()
        update_select()

    # Ejecutar ALLSTAR al presionar el botón
    def allstar_map_action(updates):
        fits_obj = selected_fits()
        psf_obj = selected_psf_table()
        table_obj = selected_table()
        if not (fits_obj and psf_obj and table_obj):
            ui.notification_show("Error: FITS not selected.", type="warning")
        try:
            with ui.Progress(min=0, max=1) as p:
                p.set(message="Preparing OPTs")
                pbar_params = daophot_pbar(p, "OPTs")
                with ui.Progress(min=0, max=1) as p2:
                    p2.set(message="Allstar mapping")
                    pbar = daophot_pbar(p2, "Allstar")
                    out_table_obj, out_fits_obj = photfun_client.allstar(fits_obj.id, psf_obj.id, table_obj.id, 
                                                            pbar=pbar, param_updates=updates, pbar_params=pbar_params)
            ui.notification_show(f"ALLSTAR PSF photometry complete\n -> [{out_table_obj.id}] {out_table_obj.alias}\n (Substracted: [{out_fits_obj.id}] {out_fits_obj.alias})")
            # Construir el diccionario de previews
            with ui.Progress(min=0, max=1) as p3:
                p3.set(message="Preparing previews")
                pbar_previews = daophot_pbar(p3, "Previews")
                d = {}
                for idx, upd in enumerate(pbar_previews(updates)):
                    # key legible, por ej. "fi=4.0;ps=20.0"
                    key = ";".join(f"{k}={v:.2f}" for k, v in upd.items())
                    if "ERROR" in out_table_obj.path[idx]:
                        continue
                    df = out_table_obj.df(idx)           # accede al array FITS
                    gif_b64 = render_allstar_plots(df, out_fits_obj.image(idx), dpi=100)             # tu función de GIF→base64
                    d[key] = gif_b64
            ui.notification_show(f"ALLSTAR map created\n -> [{out_table_obj.id}] {out_table_obj.alias}")
            nav_table_sideview_update(fits=False)
            update_select()
            return d
            
        except Exception as e:
            ui.notification_show(f"Error: {str(e)}", type="error")

        
        nav_table_sideview_update()
        update_select()
    
    return {"selected_fits":selected_fits,
            "selected_table":selected_table,
            "map_action":allstar_map_action}
