from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/errdisable.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_errdisable = resolve('errdisable')
    l_0_causes = resolve('causes')
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
    if t_3((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable)):
        pass
        yield '\n## Errdisable\n\n### Errdisable Summary\n'
        if t_3(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'recovery'), 'interval')):
            pass
            yield '\nErrdisable recovery timer interval: '
            yield str(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'recovery'), 'interval'))
            yield ' seconds\n'
        if (t_3(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'detect'), 'causes')) or t_3(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'recovery'), 'causes'))):
            pass
            l_0_causes = {}
            context.vars['causes'] = l_0_causes
            context.exported_vars.add('causes')
            for l_1_detect_cause in t_1(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'detect'), 'causes'), []):
                _loop_vars = {}
                pass
                context.call(environment.getattr((undefined(name='causes') if l_0_causes is missing else l_0_causes), 'update'), {l_1_detect_cause: {'detect_status': True}}, _loop_vars=_loop_vars)
            l_1_detect_cause = missing
            for l_1_recovery_cause in t_1(environment.getattr(environment.getattr((undefined(name='errdisable') if l_0_errdisable is missing else l_0_errdisable), 'recovery'), 'causes'), []):
                _loop_vars = {}
                pass
                if context.call(environment.getattr((undefined(name='causes') if l_0_causes is missing else l_0_causes), 'get'), environment.getattr(l_1_recovery_cause, 'name'), _loop_vars=_loop_vars):
                    pass
                    context.call(environment.getattr(environment.getitem((undefined(name='causes') if l_0_causes is missing else l_0_causes), environment.getattr(l_1_recovery_cause, 'name')), 'update'), {'recovery_status': True}, _loop_vars=_loop_vars)
                else:
                    pass
                    context.call(environment.getattr((undefined(name='causes') if l_0_causes is missing else l_0_causes), 'update'), {environment.getattr(l_1_recovery_cause, 'name'): {'recovery_status': True}}, _loop_vars=_loop_vars)
                if t_3(environment.getattr(l_1_recovery_cause, 'interval')):
                    pass
                    context.call(environment.getattr(environment.getitem((undefined(name='causes') if l_0_causes is missing else l_0_causes), environment.getattr(l_1_recovery_cause, 'name')), 'update'), {'recovery_interval': environment.getattr(l_1_recovery_cause, 'interval')}, _loop_vars=_loop_vars)
            l_1_recovery_cause = missing
            yield '\n|  Cause | Detection Enabled | Recovery Enabled | Recovery Interval (seconds) |\n| ------ | ----------------- | ---------------- | -------------------------- |\n'
            for (l_1_cause, l_1_status) in t_2(context.call(environment.getattr((undefined(name='causes') if l_0_causes is missing else l_0_causes), 'items'))):
                _loop_vars = {}
                pass
                yield '| '
                yield str(l_1_cause)
                yield ' | '
                yield str(t_1(environment.getattr(l_1_status, 'detect_status'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_status, 'recovery_status'), '-'))
                yield ' | '
                yield str(t_1(environment.getattr(l_1_status, 'recovery_interval'), '-'))
                yield ' |\n'
            l_1_cause = l_1_status = missing
        yield '\n```eos\n'
        template = environment.get_template('eos/errdisable.j2', 'documentation/errdisable.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {'causes': l_0_causes}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=31&12=34&14=37&16=39&17=41&18=44&19=47&21=49&22=52&23=54&25=57&27=58&28=60&34=63&35=67&40=77'