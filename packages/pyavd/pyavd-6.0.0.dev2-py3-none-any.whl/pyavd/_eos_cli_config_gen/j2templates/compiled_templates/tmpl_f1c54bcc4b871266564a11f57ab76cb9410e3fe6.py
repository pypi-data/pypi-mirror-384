from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/router-rip.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_rip = resolve('router_rip')
    try:
        t_1 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_2 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_2(environment.getattr((undefined(name='router_rip') if l_0_router_rip is missing else l_0_router_rip), 'vrfs')):
        pass
        for l_1_rip_vrf in t_1(environment.getattr((undefined(name='router_rip') if l_0_router_rip is missing else l_0_router_rip), 'vrfs'), sort_key='vrf', ignore_case=False):
            _loop_vars = {}
            pass
            yield '!\n'
            if (environment.getattr(l_1_rip_vrf, 'vrf') == 'default'):
                pass
                yield 'router rip\n'
            else:
                pass
                yield 'router rip vrf '
                yield str(environment.getattr(l_1_rip_vrf, 'vrf'))
                yield '\n'
            if t_2(environment.getattr(l_1_rip_vrf, 'metric_default')):
                pass
                yield '   metric default '
                yield str(environment.getattr(l_1_rip_vrf, 'metric_default'))
                yield '\n'
            for l_2_network in t_1(environment.getattr(l_1_rip_vrf, 'networks')):
                _loop_vars = {}
                pass
                yield '   network '
                yield str(l_2_network)
                yield '\n'
            l_2_network = missing
            if t_2(environment.getattr(l_1_rip_vrf, 'enabled'), True):
                pass
                yield '   no shutdown\n'
            elif t_2(environment.getattr(l_1_rip_vrf, 'enabled'), False):
                pass
                yield '   shutdown\n'
        l_1_rip_vrf = missing

blocks = {}
debug_info = '7=24&8=26&10=30&13=36&15=38&16=41&18=43&19=47&21=50&23=53'