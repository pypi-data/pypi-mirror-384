import uuid

from .JHTML import HTML

__all__ = [
    "JSMol"
]

__reload_hooks__ = [".JHTML"]

class JSMol:
    class Applet(HTML.Div):
        version = "16.3.7.9"
        jsmol_source = f"https://cdn.jsdelivr.net/gh/b3m2a1/jsmol-cdn@{version}/jsmol/JSmol.min.js"
        jmol2_source = f"https://cdn.jsdelivr.net/gh/b3m2a1/jsmol-cdn@{version}/jsmol/js/Jmol2.js"
        patch_script = f"""
        if (typeof Jmol._patched === 'undefined') {{
            Jmol._patched = true;
            Jmol._serverUrl = Jmol.Info["serverURL"];
            Jmol._appletNameMap = {{}};
            jmolInitialize('https://cdn.jsdelivr.net/gh/b3m2a1/jsmol-cdn@{version}/jsmol/');
        }};
        """
        @classmethod
        def load_applet_script(cls, id, loader,
                               include_script_interface=False,
                               interface_target="",
                               target=None):
            if target is None:
                target = id

            injection = "''"
            if include_script_interface:
                from ..Plots.X3DInterface import X3D

                input_tag = id + "-script-input"

                elems = []
                console = HTML.Textarea(id=input_tag, width='100%')
                elems.append(console)
                button = HTML.Button("Run Script", id=id + "-button-input",
                                onclick=f"""
                (function() {{
                    const script = document.getElementById('{input_tag}').value;
                    const app = Jmol._appletNameMap['{id}'];
                    app._script(script);
                    document.getElementById('{input_tag}').value = '';
                }})()
                """
                                )

                new_id = 'jmolApplet_' + id.split("-")[-2]
                elems.append(button)
                elems.append(
                    HTML.Div([
                        HTML.Button("Save Figure", onclick=X3D.get_export_script(new_id + '_appletdiv')),
                        HTML.Button("Record Animation", onclick=X3D.get_record_screen_script(new_id+ '_appletdiv')),
                        HTML.Input(value="2", id=id + '-duration-input',
                                   oninput=X3D.set_animation_duration_script(id))
                    ], style='display:flex')
                )

                strings = "\n\n".join([e.tostring() for e in elems])

                injection = f"`<div style='display:block'>\n{strings}\n</div>`"
            load_script = f"""
(function() {{
   $.getScript('{cls.jmol2_source}').then(
   () => {{
       {cls.patch_script}
       let loaded = false;
        if (!loaded) {{
            if (typeof Jmol._appletNameMap === "undefined") {{
                Jmol._appletNameMap = {{}}
            }};
            loaded = true;
            let applet = {loader};
            applet.serverURL = Jmol.Info.serverURL;
            let wrapper = document.getElementById('{id}');
            wrapper.innerHTML = applet._code;
            Jmol._appletNameMap['{id}'] = applet;
            wrapper.ondelete = function() {{ delete Jmol._appletNameMap['{id}'] }};
            if ('{interface_target}'.length > 0) {{
                document.getElementById('{interface_target}').innerHTML = {injection};
            }}
        }}
    }})
}})();
"""
            base_script = HTML.Script(src=cls.jsmol_source,
                               onload=load_script
                               )
            return base_script

        def __init__(self, *model_etc, width=500, height=500,
                     animate=False, vibrate=False,
                     load_script=None,
                     suffix=None,
                     dynamic_loading=None,
                     include_script_interface=True,
                     **attrs):
            if suffix is None:
                suffix = str(uuid.uuid4())[:6].replace("-", "")
            self.suffix = suffix
            self.id = "jsmol-applet-" + self.suffix
            if len(model_etc) > 0 and isinstance(model_etc[0], str):
                model_file = model_etc[0]
                rest = model_etc[1:]
            else:
                model_file = None
                rest = model_etc

            if load_script is None:
                load_script = []
            if isinstance(load_script, str):
                load_script = [load_script]
            load_script = list(load_script)

            if animate:
                load_script.extend(["anim mode palindrome", "anim on"])
            elif vibrate:
                load_script.append("vibration on")

            if dynamic_loading is None:
                from ..Jupyter.JHTML import JupyterAPIs
                dynamic_loading = JupyterAPIs().in_jupyter_environment()

            self.dynamic_loading = dynamic_loading

            self.load_script = load_script
            self.width, self.height = width, height
            elems = self.create_applet(model_file, include_script_interface=include_script_interface) + list(rest)
            if include_script_interface:
                height = height + 200
            super().__init__(*elems, id=self.id, width=f'{width}px', height=f'{height}px', **attrs)

        @property
        def applet_target(self):
            return f"_{self.suffix}"
        def prep_load_script(self):
            return '; '.join(self.load_script)
        def create_applet(self, model_file, include_script_interface=False):
            targ = self.applet_target
            width, height = self.width, self.height
            load_script = self.prep_load_script()
            if model_file is None:
                loader = f"jmolApplet([{width}, {height}], 'load {model_file}; {load_script}', '{targ}')"
            elif (
                    model_file.startswith("https://")
                    or model_file.startswith("file://")
                    or model_file.startswith("http://")
            ):
                loader = f"jmolApplet([{width}, {height}], 'load {model_file}; {load_script}', '{targ}')"
            else:
                loader = f"jmolAppletInline([{width}, {height}], `{model_file}`, '{load_script}', '{targ}')"

            kill_id = "tmp-" + str(uuid.uuid4())[:10]
            if include_script_interface:
                replacement_target = self.id+'-applet'
                interface_target = self.id+'-interface'
            else:
                replacement_target = self.id
                interface_target = ""
            load_script = self.load_applet_script(replacement_target,
                                                  loader,
                                                  target=targ,
                                                  interface_target=interface_target,
                                                  include_script_interface=include_script_interface)

            if self.dynamic_loading:
                load_script = load_script.tostring().replace("`", "\`")
                loader = HTML.Image(
                        src='data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
                        id=kill_id,
                        onload=f"""
                            (function() {{
                                document.getElementById('{kill_id}').remove();
                                const frag = document.createRange().createContextualFragment(`{load_script}`);
                                document.head.appendChild(frag);
                            }})()"""
                    )
            else:
                loader = load_script

            if include_script_interface:
                loader = [
                    HTML.Div(loader, width='100%', height=f'{self.height}px', id=replacement_target),
                    HTML.Div(height='200px', width='100%', padding='2rem', id=interface_target)
                ]
            else:
                loader = [loader]

            return loader

        def show(self):
            return self.display()