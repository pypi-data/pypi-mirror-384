from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/aaa-accounting.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_aaa_accounting = resolve('aaa_accounting')
    l_0_methods_list = resolve('methods_list')
    l_0_namespace = resolve('namespace')
    l_0_logging_namespace = resolve('logging_namespace')
    try:
        t_1 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_1((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting)):
        pass
        yield '\n### AAA Accounting\n\n#### AAA Accounting Summary\n\n| Type | Commands | Record type | Groups | Logging |\n| ---- | -------- | ----------- | ------ | ------- |\n'
        if (environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'console'), 'type') == 'none'):
            pass
            yield '| Exec - Console | - | none | - | - |\n'
        elif t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'console'), 'methods')):
            pass
            l_0_methods_list = []
            context.vars['methods_list'] = l_0_methods_list
            context.exported_vars.add('methods_list')
            l_0_logging_namespace = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace), method_logging=False)
            context.vars['logging_namespace'] = l_0_logging_namespace
            context.exported_vars.add('logging_namespace')
            for l_1_method in environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'console'), 'methods'):
                _loop_vars = {}
                pass
                if (t_1(environment.getattr(l_1_method, 'group')) and (environment.getattr(l_1_method, 'method') == 'group')):
                    pass
                    context.call(environment.getattr((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list), 'append'), environment.getattr(l_1_method, 'group'), _loop_vars=_loop_vars)
                elif (environment.getattr(l_1_method, 'method') == 'logging'):
                    pass
                    if not isinstance(l_0_logging_namespace, Namespace):
                        raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                    l_0_logging_namespace['method_logging'] = True
            l_1_method = missing
            if ((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list) == []):
                pass
                context.call(environment.getattr((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list), 'append'), '-')
            yield '| Exec - Console | - | '
            yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'console'), 'type'))
            yield ' | '
            yield str(context.call(environment.getattr(', ', 'join'), (undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list)))
            yield ' | '
            yield str(environment.getattr((undefined(name='logging_namespace') if l_0_logging_namespace is missing else l_0_logging_namespace), 'method_logging'))
            yield ' |\n'
        if t_1(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'commands'), 'console')):
            pass
            for l_1_command_console in environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'commands'), 'console'):
                l_1_methods_list = l_0_methods_list
                l_1_logging_namespace = l_0_logging_namespace
                _loop_vars = {}
                pass
                if t_1(environment.getattr(l_1_command_console, 'commands')):
                    pass
                    if (environment.getattr(l_1_command_console, 'type') == 'none'):
                        pass
                        yield '| Commands - Console | '
                        yield str(environment.getattr(l_1_command_console, 'commands'))
                        yield ' | none | - | - |\n'
                    elif t_1(environment.getattr(l_1_command_console, 'methods')):
                        pass
                        l_1_methods_list = []
                        _loop_vars['methods_list'] = l_1_methods_list
                        l_1_logging_namespace = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace), method_logging=False, _loop_vars=_loop_vars)
                        _loop_vars['logging_namespace'] = l_1_logging_namespace
                        for l_2_method in environment.getattr(l_1_command_console, 'methods'):
                            _loop_vars = {}
                            pass
                            if (t_1(environment.getattr(l_2_method, 'group')) and (environment.getattr(l_2_method, 'method') == 'group')):
                                pass
                                context.call(environment.getattr((undefined(name='methods_list') if l_1_methods_list is missing else l_1_methods_list), 'append'), environment.getattr(l_2_method, 'group'), _loop_vars=_loop_vars)
                            elif (environment.getattr(l_2_method, 'method') == 'logging'):
                                pass
                                if not isinstance(l_1_logging_namespace, Namespace):
                                    raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                                l_1_logging_namespace['method_logging'] = True
                        l_2_method = missing
                        if ((undefined(name='methods_list') if l_1_methods_list is missing else l_1_methods_list) == []):
                            pass
                            context.call(environment.getattr((undefined(name='methods_list') if l_1_methods_list is missing else l_1_methods_list), 'append'), '-', _loop_vars=_loop_vars)
                        yield '| Commands - Console | '
                        yield str(environment.getattr(l_1_command_console, 'commands'))
                        yield ' | '
                        yield str(environment.getattr(l_1_command_console, 'type'))
                        yield ' | '
                        yield str(context.call(environment.getattr(', ', 'join'), (undefined(name='methods_list') if l_1_methods_list is missing else l_1_methods_list), _loop_vars=_loop_vars))
                        yield ' | '
                        yield str(environment.getattr((undefined(name='logging_namespace') if l_1_logging_namespace is missing else l_1_logging_namespace), 'method_logging'))
                        yield ' |\n'
            l_1_command_console = l_1_methods_list = l_1_logging_namespace = missing
        if (environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'default'), 'type') == 'none'):
            pass
            yield '| Exec - Default | - | none | - | - |\n'
        elif t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'default'), 'methods')):
            pass
            l_0_methods_list = []
            context.vars['methods_list'] = l_0_methods_list
            context.exported_vars.add('methods_list')
            l_0_logging_namespace = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace), method_logging=False)
            context.vars['logging_namespace'] = l_0_logging_namespace
            context.exported_vars.add('logging_namespace')
            for l_1_method in environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'default'), 'methods'):
                _loop_vars = {}
                pass
                if (t_1(environment.getattr(l_1_method, 'group')) and (environment.getattr(l_1_method, 'method') == 'group')):
                    pass
                    context.call(environment.getattr((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list), 'append'), environment.getattr(l_1_method, 'group'), _loop_vars=_loop_vars)
                elif (environment.getattr(l_1_method, 'method') == 'logging'):
                    pass
                    if not isinstance(l_0_logging_namespace, Namespace):
                        raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                    l_0_logging_namespace['method_logging'] = True
            l_1_method = missing
            if ((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list) == []):
                pass
                context.call(environment.getattr((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list), 'append'), '-')
            yield '| Exec - Default | - | '
            yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'default'), 'type'))
            yield ' | '
            yield str(context.call(environment.getattr(', ', 'join'), (undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list)))
            yield ' | '
            yield str(environment.getattr((undefined(name='logging_namespace') if l_0_logging_namespace is missing else l_0_logging_namespace), 'method_logging'))
            yield ' |\n'
        if (environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'system'), 'default'), 'type') == 'none'):
            pass
            yield '| System - Default | - | none | - | - |\n'
        elif t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'system'), 'default'), 'methods')):
            pass
            l_0_methods_list = []
            context.vars['methods_list'] = l_0_methods_list
            context.exported_vars.add('methods_list')
            l_0_logging_namespace = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace), method_logging=False)
            context.vars['logging_namespace'] = l_0_logging_namespace
            context.exported_vars.add('logging_namespace')
            for l_1_method in environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'system'), 'default'), 'methods'):
                _loop_vars = {}
                pass
                if (t_1(environment.getattr(l_1_method, 'group')) and (environment.getattr(l_1_method, 'method') == 'group')):
                    pass
                    context.call(environment.getattr((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list), 'append'), environment.getattr(l_1_method, 'group'), _loop_vars=_loop_vars)
                elif (environment.getattr(l_1_method, 'method') == 'logging'):
                    pass
                    if not isinstance(l_0_logging_namespace, Namespace):
                        raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                    l_0_logging_namespace['method_logging'] = True
            l_1_method = missing
            if ((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list) == []):
                pass
                context.call(environment.getattr((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list), 'append'), '-')
            yield '| System - Default | - | '
            yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'system'), 'default'), 'type'))
            yield ' | '
            yield str(context.call(environment.getattr(', ', 'join'), (undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list)))
            yield ' | '
            yield str(environment.getattr((undefined(name='logging_namespace') if l_0_logging_namespace is missing else l_0_logging_namespace), 'method_logging'))
            yield ' |\n'
        if (environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'dot1x'), 'default'), 'type') == 'none'):
            pass
            yield '| Dot1x - Default | - | none | - | - |\n'
        elif t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'dot1x'), 'default'), 'methods')):
            pass
            l_0_methods_list = []
            context.vars['methods_list'] = l_0_methods_list
            context.exported_vars.add('methods_list')
            l_0_logging_namespace = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace), method_logging=False)
            context.vars['logging_namespace'] = l_0_logging_namespace
            context.exported_vars.add('logging_namespace')
            for l_1_method in environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'dot1x'), 'default'), 'methods'):
                l_1_method_group_cli = resolve('method_group_cli')
                _loop_vars = {}
                pass
                if (t_1(environment.getattr(l_1_method, 'group')) and (environment.getattr(l_1_method, 'method') == 'group')):
                    pass
                    l_1_method_group_cli = environment.getattr(l_1_method, 'group')
                    _loop_vars['method_group_cli'] = l_1_method_group_cli
                    if t_1(environment.getattr(l_1_method, 'multicast')):
                        pass
                        l_1_method_group_cli = str_join(((undefined(name='method_group_cli') if l_1_method_group_cli is missing else l_1_method_group_cli), '(multicast)', ))
                        _loop_vars['method_group_cli'] = l_1_method_group_cli
                    context.call(environment.getattr((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list), 'append'), (undefined(name='method_group_cli') if l_1_method_group_cli is missing else l_1_method_group_cli), _loop_vars=_loop_vars)
                elif (environment.getattr(l_1_method, 'method') == 'logging'):
                    pass
                    if not isinstance(l_0_logging_namespace, Namespace):
                        raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                    l_0_logging_namespace['method_logging'] = True
            l_1_method = l_1_method_group_cli = missing
            if ((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list) == []):
                pass
                context.call(environment.getattr((undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list), 'append'), '-')
            yield '| Dot1x - Default | - | '
            yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'dot1x'), 'default'), 'type'))
            yield ' | '
            yield str(context.call(environment.getattr(', ', 'join'), (undefined(name='methods_list') if l_0_methods_list is missing else l_0_methods_list)))
            yield ' | '
            yield str(environment.getattr((undefined(name='logging_namespace') if l_0_logging_namespace is missing else l_0_logging_namespace), 'method_logging'))
            yield ' |\n'
        if t_1(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'commands'), 'default')):
            pass
            for l_1_command_default in environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'commands'), 'default'):
                l_1_methods_list = l_0_methods_list
                l_1_logging_namespace = l_0_logging_namespace
                _loop_vars = {}
                pass
                if (environment.getattr(l_1_command_default, 'type') == 'none'):
                    pass
                    yield '| Commands - Default | '
                    yield str(environment.getattr(l_1_command_default, 'commands'))
                    yield ' | none | - | - |\n'
                elif t_1(environment.getattr(l_1_command_default, 'methods')):
                    pass
                    l_1_methods_list = []
                    _loop_vars['methods_list'] = l_1_methods_list
                    l_1_logging_namespace = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace), method_logging=False, _loop_vars=_loop_vars)
                    _loop_vars['logging_namespace'] = l_1_logging_namespace
                    for l_2_method in environment.getattr(l_1_command_default, 'methods'):
                        _loop_vars = {}
                        pass
                        if (t_1(environment.getattr(l_2_method, 'group')) and (environment.getattr(l_2_method, 'method') == 'group')):
                            pass
                            context.call(environment.getattr((undefined(name='methods_list') if l_1_methods_list is missing else l_1_methods_list), 'append'), environment.getattr(l_2_method, 'group'), _loop_vars=_loop_vars)
                        elif (environment.getattr(l_2_method, 'method') == 'logging'):
                            pass
                            if not isinstance(l_1_logging_namespace, Namespace):
                                raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                            l_1_logging_namespace['method_logging'] = True
                    l_2_method = missing
                    if ((undefined(name='methods_list') if l_1_methods_list is missing else l_1_methods_list) == []):
                        pass
                        context.call(environment.getattr((undefined(name='methods_list') if l_1_methods_list is missing else l_1_methods_list), 'append'), '-', _loop_vars=_loop_vars)
                    yield '| Commands - Default | '
                    yield str(environment.getattr(l_1_command_default, 'commands'))
                    yield ' | '
                    yield str(environment.getattr(l_1_command_default, 'type'))
                    yield ' | '
                    yield str(context.call(environment.getattr(', ', 'join'), (undefined(name='methods_list') if l_1_methods_list is missing else l_1_methods_list), _loop_vars=_loop_vars))
                    yield ' | '
                    yield str(environment.getattr((undefined(name='logging_namespace') if l_1_logging_namespace is missing else l_1_logging_namespace), 'method_logging'))
                    yield ' |\n'
            l_1_command_default = l_1_methods_list = l_1_logging_namespace = missing
        yield '\n#### AAA Accounting Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/aaa-accounting.j2', 'documentation/aaa-accounting.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {'logging_namespace': l_0_logging_namespace, 'methods_list': l_0_methods_list}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=21&15=24&17=27&18=29&19=32&20=35&21=38&22=40&23=41&24=45&27=47&28=49&30=51&32=57&33=59&34=64&35=66&36=69&37=71&38=73&39=75&40=77&41=80&42=82&43=83&44=87&47=89&48=91&50=93&55=102&57=105&58=107&59=110&60=113&61=116&62=118&63=119&64=123&67=125&68=127&70=129&72=135&74=138&75=140&76=143&77=146&78=149&79=151&80=152&81=156&84=158&85=160&87=162&89=168&91=171&92=173&93=176&94=179&95=183&96=185&97=187&98=189&100=191&101=192&102=196&105=198&106=200&108=202&110=208&111=210&112=215&113=218&114=220&115=222&116=224&117=226&118=229&119=231&120=232&121=236&124=238&125=240&127=242&135=252'