from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/router-rip.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_rip = resolve('router_rip')
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
        t_3 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_4 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_4((undefined(name='router_rip') if l_0_router_rip is missing else l_0_router_rip)):
        pass
        yield '\n### Router RIP\n\n#### Router RIP Summary\n'
        for l_1_rip_vrf in t_2(environment.getattr((undefined(name='router_rip') if l_0_router_rip is missing else l_0_router_rip), 'vrfs'), sort_key='vrf', ignore_case=False):
            l_1_networks = missing
            _loop_vars = {}
            pass
            yield '\n##### VRF: '
            yield str(environment.getattr(l_1_rip_vrf, 'vrf'))
            yield '\n\n| Enabled | Default Metric | Networks |\n| ------- | -------------- | -------- |\n'
            l_1_networks = t_3(context.eval_ctx, t_1(environment.getattr(l_1_rip_vrf, 'networks'), ['-']), ', ')
            _loop_vars['networks'] = l_1_networks
            yield '| '
            yield str(t_1(environment.getattr(l_1_rip_vrf, 'enabled'), '-'))
            yield ' | '
            yield str(t_1(environment.getattr(l_1_rip_vrf, 'metric_default'), '-'))
            yield ' | '
            yield str((undefined(name='networks') if l_1_networks is missing else l_1_networks))
            yield ' |\n'
        l_1_rip_vrf = l_1_networks = missing
        yield '\n#### Router RIP Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/router-rip.j2', 'documentation/router-rip.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=36&12=39&14=44&18=46&19=49&25=57'