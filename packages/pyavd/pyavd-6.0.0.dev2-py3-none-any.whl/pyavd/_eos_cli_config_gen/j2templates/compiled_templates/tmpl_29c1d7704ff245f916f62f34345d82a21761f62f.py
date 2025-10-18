from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/errdisable.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_errdisable = resolve('errdisable')
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
    if t_2((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable)):
        pass
        yield '!\n'
        for l_1_cause in t_1(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'detect'), 'causes')):
            _loop_vars = {}
            pass
            yield 'errdisable detect cause '
            yield str(l_1_cause)
            yield '\n'
        l_1_cause = missing
        for l_1_cause in t_1(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'recovery'), 'causes')):
            l_1_cause_cli = missing
            _loop_vars = {}
            pass
            l_1_cause_cli = str_join(('errdisable recovery cause ', environment.getattr(l_1_cause, 'name'), ))
            _loop_vars['cause_cli'] = l_1_cause_cli
            if t_2(environment.getattr(l_1_cause, 'interval')):
                pass
                l_1_cause_cli = str_join(((undefined(name='cause_cli') if l_1_cause_cli is missing else l_1_cause_cli), ' interval ', environment.getattr(l_1_cause, 'interval'), ))
                _loop_vars['cause_cli'] = l_1_cause_cli
            yield str((undefined(name='cause_cli') if l_1_cause_cli is missing else l_1_cause_cli))
            yield '\n'
        l_1_cause = l_1_cause_cli = missing
        if t_2(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'recovery'), 'interval')):
            pass
            yield 'errdisable recovery interval '
            yield str(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'recovery'), 'interval'))
            yield '\n'

blocks = {}
debug_info = '7=24&9=27&10=31&12=34&13=38&14=40&15=42&17=44&19=47&20=50'