import numpy as np

from ..JHTML import JHTML, HTML, HTMLWidgets
# from ..Apps import WrapperComponent
# import uuid

__all__ = [
    # "D3API",
    "NGLAPI"
]
__reload_hook__ = ["..JHTML", "..Apps"]

class NGLAPI:
    _api_versions = {}
    @classmethod
    def load(cls, version='v5'):
        if version not in cls._api_versions:
            cls._api_versions[version] = JHTML.JavascriptAPI(
    ngl_init="""
let model = this.model;
if (typeof(model) === 'undefined' || model === null){
    model = this;
}

if (typeof(model.ngl) === 'undefined' || model.ngl === null) {
    return import("https://unpkg.com/ngl")
      .then(() => (model.ngl = ngl));
} else {
    return Promise.resolve();
}""",

    ngl_stage="""
let model = this.model;
if (typeof(model) === 'undefined' || model === null){
    model = this;
}

model.callHandler("ngl_init").then(()=>{
    let ngl = model.ngl;
    let stage = model.stage;
    if (typeof(stage) === 'undefined' || stage === null) {
        if (event.content.hasOwnProperty('id')) {
            stage = new ngl.Stage(event.content['id']);
            model.stage = stage;
        } else {
            alert("no id for stage")
        }
    }
    return model.stage
})
    """,

    ngl_load="""

let model = this.model;
if (typeof(model) === 'undefined' || model === null){
    model = this;
}

model.callHandler("ngl_stage").then((stage)=>{
    return stage.loadFile(type=)
})
    """,

    ngl_call="""
let model = this.model;
if (typeof(model) === 'undefined' || model === null){
    model = this;
}

model.callHandler("ngl_stage").then((stage)=>{
    let methods = event.content['methods'];
    let args = event.content['args'];
    let debug = event.content['debug'];
    
    if (debug) { console.log(stage); }
    return methods.reduce(
        (acc, method, index) => {
            if (method in stage) {
                let fn = stage[method];
                if (debug) { console.log(method, args[index], fn); }
                let argl = [svg, ...args[index]];
                fn.call(...argl);
            } else {
                if (debug) { console.log("no attr", method); }
            }
        }, 
        []
    )
})
""",

    ngl_props="""
let model = this.model;
if (typeof(model) === 'undefined' || model === null){
    model = this;
}

model.callHandler("d3_init").then(()=>{
    let d3 = model.d3;
    let props = event.content['properties'];
    let debug = event.content['debug'];
    let el = this.el;
    if (typeof(el) === 'undefined' || el === null) {
        if (event.content.hasOwnProperty('id')) {
            el = "#" + event.content['id']
        }
    }

    if (typeof(el) === 'undefined' || el === null) {
        alert("no d3 object provided");
    } else {
        let svg = d3.select(el);
        if (debug) { console.log(el, svg); }
        let attrs = props.map(
            (prop) => svg.attr(prop)
        );
        this.send({type:"content", content:attrs});
    }
})
"""
)
        return cls._api_versions[version]