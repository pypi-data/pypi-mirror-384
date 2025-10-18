from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/management-api-models.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_management_api_models = resolve('management_api_models')
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_3 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_3((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models)):
        pass
        yield '\n### Management API Models\n\n#### Management API Models Summary\n'
        if t_3(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'smash'), 'paths')):
            pass
            yield '\n##### Smash Provider\n\n| Path | Disabled |\n| ---- | -------- |\n'
            for l_1_path in t_2(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'smash'), 'paths'), 'path'):
                _loop_vars = {}
                pass
                yield '| '
                yield str(environment.getattr(l_1_path, 'path'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_path, 'disabled'), '-'))
                yield ' |\n'
            l_1_path = missing
        if t_3(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'sysdb'), 'disabled_paths')):
            pass
            yield '\n##### Sysdb Provider\n\n| Disabled Path |\n| ------------- |\n'
            for l_1_path in t_2(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'sysdb'), 'disabled_paths')):
                _loop_vars = {}
                pass
                yield '| '
                yield str(l_1_path)
                yield ' |\n'
            l_1_path = missing
        if (t_3(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'macsec'), 'interfaces')) or t_3(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'macsec'), 'mka'))):
            pass
            yield '\n##### Macsec Provider\n\n| Interfaces | MKA |\n| ---------- | --- |\n| '
            yield str(t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'macsec'), 'interfaces'), '-'))
            yield ' | '
            yield str(t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='management_api_models') if l_0_management_api_models is missing else l_0_management_api_models), 'provider'), 'macsec'), 'mka'), '-'))
            yield ' |\n'
        yield '\n#### Management API Models Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/management-api-models.j2', 'documentation/management-api-models.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=30&12=33&18=36&19=40&22=45&28=48&29=52&32=55&38=58&44=63'