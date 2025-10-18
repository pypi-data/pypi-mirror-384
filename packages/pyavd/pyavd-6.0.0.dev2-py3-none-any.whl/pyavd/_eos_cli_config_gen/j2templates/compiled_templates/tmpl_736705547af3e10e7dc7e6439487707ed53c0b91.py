from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/aaa-accounting.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_aaa_accounting = resolve('aaa_accounting')
    l_0_exec_console_list = resolve('exec_console_list')
    l_0_exec_console_cli = resolve('exec_console_cli')
    l_0_exec_default_list = resolve('exec_default_list')
    l_0_exec_default_cli = resolve('exec_default_cli')
    l_0_system_default_list = resolve('system_default_list')
    l_0_system_default_cli = resolve('system_default_cli')
    l_0_dot1x_default_list = resolve('dot1x_default_list')
    l_0_dot1x_default_cli = resolve('dot1x_default_cli')
    try:
        t_1 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_1((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting)):
        pass
        if t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'console'), 'type'), 'none'):
            pass
            yield 'aaa accounting exec console none\n'
        elif t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'console'), 'methods')):
            pass
            l_0_exec_console_list = []
            context.vars['exec_console_list'] = l_0_exec_console_list
            context.exported_vars.add('exec_console_list')
            for l_1_method in environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'console'), 'methods'):
                l_1_group_cli = resolve('group_cli')
                _loop_vars = {}
                pass
                if (environment.getattr(l_1_method, 'method') == 'logging'):
                    pass
                    context.call(environment.getattr((undefined(name='exec_console_list') if l_0_exec_console_list is missing else l_0_exec_console_list), 'append'), environment.getattr(l_1_method, 'method'), _loop_vars=_loop_vars)
                elif ((environment.getattr(l_1_method, 'method') == 'group') and t_1(environment.getattr(l_1_method, 'group'))):
                    pass
                    l_1_group_cli = str_join(('group ', environment.getattr(l_1_method, 'group'), ))
                    _loop_vars['group_cli'] = l_1_group_cli
                    context.call(environment.getattr((undefined(name='exec_console_list') if l_0_exec_console_list is missing else l_0_exec_console_list), 'append'), (undefined(name='group_cli') if l_1_group_cli is missing else l_1_group_cli), _loop_vars=_loop_vars)
            l_1_method = l_1_group_cli = missing
            l_0_exec_console_cli = context.call(environment.getattr(' ', 'join'), (undefined(name='exec_console_list') if l_0_exec_console_list is missing else l_0_exec_console_list))
            context.vars['exec_console_cli'] = l_0_exec_console_cli
            context.exported_vars.add('exec_console_cli')
            if (undefined(name='exec_console_cli') if l_0_exec_console_cli is missing else l_0_exec_console_cli):
                pass
                yield 'aaa accounting exec console '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'console'), 'type'))
                yield ' '
                yield str((undefined(name='exec_console_cli') if l_0_exec_console_cli is missing else l_0_exec_console_cli))
                yield '\n'
        if t_1(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'commands'), 'console')):
            pass
            for l_1_command_console in environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'commands'), 'console'):
                l_1_command_console_list = resolve('command_console_list')
                l_1_command_console_cli = resolve('command_console_cli')
                _loop_vars = {}
                pass
                if t_1(environment.getattr(l_1_command_console, 'commands')):
                    pass
                    if (environment.getattr(l_1_command_console, 'type') == 'none'):
                        pass
                        yield 'aaa accounting commands '
                        yield str(environment.getattr(l_1_command_console, 'commands'))
                        yield ' console none\n'
                    elif t_1(environment.getattr(l_1_command_console, 'methods')):
                        pass
                        l_1_command_console_list = []
                        _loop_vars['command_console_list'] = l_1_command_console_list
                        for l_2_method in environment.getattr(l_1_command_console, 'methods'):
                            l_2_group_cli = resolve('group_cli')
                            _loop_vars = {}
                            pass
                            if (environment.getattr(l_2_method, 'method') == 'logging'):
                                pass
                                context.call(environment.getattr((undefined(name='command_console_list') if l_1_command_console_list is missing else l_1_command_console_list), 'append'), environment.getattr(l_2_method, 'method'), _loop_vars=_loop_vars)
                            elif ((environment.getattr(l_2_method, 'method') == 'group') and t_1(environment.getattr(l_2_method, 'group'))):
                                pass
                                l_2_group_cli = str_join(('group ', environment.getattr(l_2_method, 'group'), ))
                                _loop_vars['group_cli'] = l_2_group_cli
                                context.call(environment.getattr((undefined(name='command_console_list') if l_1_command_console_list is missing else l_1_command_console_list), 'append'), (undefined(name='group_cli') if l_2_group_cli is missing else l_2_group_cli), _loop_vars=_loop_vars)
                        l_2_method = l_2_group_cli = missing
                        l_1_command_console_cli = context.call(environment.getattr(' ', 'join'), (undefined(name='command_console_list') if l_1_command_console_list is missing else l_1_command_console_list), _loop_vars=_loop_vars)
                        _loop_vars['command_console_cli'] = l_1_command_console_cli
                        if (undefined(name='command_console_cli') if l_1_command_console_cli is missing else l_1_command_console_cli):
                            pass
                            yield 'aaa accounting commands '
                            yield str(environment.getattr(l_1_command_console, 'commands'))
                            yield ' console '
                            yield str(environment.getattr(l_1_command_console, 'type'))
                            yield ' '
                            yield str((undefined(name='command_console_cli') if l_1_command_console_cli is missing else l_1_command_console_cli))
                            yield '\n'
            l_1_command_console = l_1_command_console_list = l_1_command_console_cli = missing
        if t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'default'), 'type'), 'none'):
            pass
            yield 'aaa accounting exec default none\n'
        elif t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'default'), 'methods')):
            pass
            l_0_exec_default_list = []
            context.vars['exec_default_list'] = l_0_exec_default_list
            context.exported_vars.add('exec_default_list')
            for l_1_method in environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'default'), 'methods'):
                l_1_group_cli = resolve('group_cli')
                _loop_vars = {}
                pass
                if (environment.getattr(l_1_method, 'method') == 'logging'):
                    pass
                    context.call(environment.getattr((undefined(name='exec_default_list') if l_0_exec_default_list is missing else l_0_exec_default_list), 'append'), environment.getattr(l_1_method, 'method'), _loop_vars=_loop_vars)
                elif ((environment.getattr(l_1_method, 'method') == 'group') and t_1(environment.getattr(l_1_method, 'group'))):
                    pass
                    l_1_group_cli = str_join(('group ', environment.getattr(l_1_method, 'group'), ))
                    _loop_vars['group_cli'] = l_1_group_cli
                    context.call(environment.getattr((undefined(name='exec_default_list') if l_0_exec_default_list is missing else l_0_exec_default_list), 'append'), (undefined(name='group_cli') if l_1_group_cli is missing else l_1_group_cli), _loop_vars=_loop_vars)
            l_1_method = l_1_group_cli = missing
            l_0_exec_default_cli = context.call(environment.getattr(' ', 'join'), (undefined(name='exec_default_list') if l_0_exec_default_list is missing else l_0_exec_default_list))
            context.vars['exec_default_cli'] = l_0_exec_default_cli
            context.exported_vars.add('exec_default_cli')
            if (undefined(name='exec_default_cli') if l_0_exec_default_cli is missing else l_0_exec_default_cli):
                pass
                yield 'aaa accounting exec default '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'exec'), 'default'), 'type'))
                yield ' '
                yield str((undefined(name='exec_default_cli') if l_0_exec_default_cli is missing else l_0_exec_default_cli))
                yield '\n'
        if t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'system'), 'default'), 'type'), 'none'):
            pass
            yield 'aaa accounting system default none\n'
        elif t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'system'), 'default'), 'methods')):
            pass
            l_0_system_default_list = []
            context.vars['system_default_list'] = l_0_system_default_list
            context.exported_vars.add('system_default_list')
            for l_1_method in environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'system'), 'default'), 'methods'):
                l_1_group_cli = resolve('group_cli')
                _loop_vars = {}
                pass
                if (environment.getattr(l_1_method, 'method') == 'logging'):
                    pass
                    context.call(environment.getattr((undefined(name='system_default_list') if l_0_system_default_list is missing else l_0_system_default_list), 'append'), environment.getattr(l_1_method, 'method'), _loop_vars=_loop_vars)
                elif ((environment.getattr(l_1_method, 'method') == 'group') and t_1(environment.getattr(l_1_method, 'group'))):
                    pass
                    l_1_group_cli = str_join(('group ', environment.getattr(l_1_method, 'group'), ))
                    _loop_vars['group_cli'] = l_1_group_cli
                    context.call(environment.getattr((undefined(name='system_default_list') if l_0_system_default_list is missing else l_0_system_default_list), 'append'), (undefined(name='group_cli') if l_1_group_cli is missing else l_1_group_cli), _loop_vars=_loop_vars)
            l_1_method = l_1_group_cli = missing
            l_0_system_default_cli = context.call(environment.getattr(' ', 'join'), (undefined(name='system_default_list') if l_0_system_default_list is missing else l_0_system_default_list))
            context.vars['system_default_cli'] = l_0_system_default_cli
            context.exported_vars.add('system_default_cli')
            if (undefined(name='system_default_cli') if l_0_system_default_cli is missing else l_0_system_default_cli):
                pass
                yield 'aaa accounting system default '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'system'), 'default'), 'type'))
                yield ' '
                yield str((undefined(name='system_default_cli') if l_0_system_default_cli is missing else l_0_system_default_cli))
                yield '\n'
        if t_1(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'dot1x'), 'default'), 'methods')):
            pass
            l_0_dot1x_default_list = []
            context.vars['dot1x_default_list'] = l_0_dot1x_default_list
            context.exported_vars.add('dot1x_default_list')
            for l_1_method in environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'dot1x'), 'default'), 'methods'):
                l_1_group_cli = resolve('group_cli')
                _loop_vars = {}
                pass
                if (environment.getattr(l_1_method, 'method') == 'logging'):
                    pass
                    context.call(environment.getattr((undefined(name='dot1x_default_list') if l_0_dot1x_default_list is missing else l_0_dot1x_default_list), 'append'), environment.getattr(l_1_method, 'method'), _loop_vars=_loop_vars)
                elif ((environment.getattr(l_1_method, 'method') == 'group') and t_1(environment.getattr(l_1_method, 'group'))):
                    pass
                    l_1_group_cli = str_join(('group ', environment.getattr(l_1_method, 'group'), ))
                    _loop_vars['group_cli'] = l_1_group_cli
                    if t_1(environment.getattr(l_1_method, 'multicast'), True):
                        pass
                        l_1_group_cli = str_join(((undefined(name='group_cli') if l_1_group_cli is missing else l_1_group_cli), ' multicast', ))
                        _loop_vars['group_cli'] = l_1_group_cli
                    context.call(environment.getattr((undefined(name='dot1x_default_list') if l_0_dot1x_default_list is missing else l_0_dot1x_default_list), 'append'), (undefined(name='group_cli') if l_1_group_cli is missing else l_1_group_cli), _loop_vars=_loop_vars)
            l_1_method = l_1_group_cli = missing
            l_0_dot1x_default_cli = context.call(environment.getattr(' ', 'join'), (undefined(name='dot1x_default_list') if l_0_dot1x_default_list is missing else l_0_dot1x_default_list))
            context.vars['dot1x_default_cli'] = l_0_dot1x_default_cli
            context.exported_vars.add('dot1x_default_cli')
            if (undefined(name='dot1x_default_cli') if l_0_dot1x_default_cli is missing else l_0_dot1x_default_cli):
                pass
                yield 'aaa accounting dot1x default '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'dot1x'), 'default'), 'type'))
                yield ' '
                yield str((undefined(name='dot1x_default_cli') if l_0_dot1x_default_cli is missing else l_0_dot1x_default_cli))
                yield '\n'
        if t_1(environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'commands'), 'default')):
            pass
            for l_1_command_default in environment.getattr(environment.getattr((undefined(name='aaa_accounting') if l_0_aaa_accounting is missing else l_0_aaa_accounting), 'commands'), 'default'):
                l_1_commands_default_list = resolve('commands_default_list')
                l_1_command_default_cli = resolve('command_default_cli')
                _loop_vars = {}
                pass
                if t_1(environment.getattr(l_1_command_default, 'commands')):
                    pass
                    if (environment.getattr(l_1_command_default, 'type') == 'none'):
                        pass
                        yield 'aaa accounting commands '
                        yield str(environment.getattr(l_1_command_default, 'commands'))
                        yield ' default none\n'
                    elif t_1(environment.getattr(l_1_command_default, 'methods')):
                        pass
                        l_1_commands_default_list = []
                        _loop_vars['commands_default_list'] = l_1_commands_default_list
                        for l_2_method in environment.getattr(l_1_command_default, 'methods'):
                            l_2_group_cli = resolve('group_cli')
                            _loop_vars = {}
                            pass
                            if (environment.getattr(l_2_method, 'method') == 'logging'):
                                pass
                                context.call(environment.getattr((undefined(name='commands_default_list') if l_1_commands_default_list is missing else l_1_commands_default_list), 'append'), environment.getattr(l_2_method, 'method'), _loop_vars=_loop_vars)
                            elif ((environment.getattr(l_2_method, 'method') == 'group') and t_1(environment.getattr(l_2_method, 'group'))):
                                pass
                                l_2_group_cli = str_join(('group ', environment.getattr(l_2_method, 'group'), ))
                                _loop_vars['group_cli'] = l_2_group_cli
                                context.call(environment.getattr((undefined(name='commands_default_list') if l_1_commands_default_list is missing else l_1_commands_default_list), 'append'), (undefined(name='group_cli') if l_2_group_cli is missing else l_2_group_cli), _loop_vars=_loop_vars)
                        l_2_method = l_2_group_cli = missing
                        l_1_command_default_cli = context.call(environment.getattr(' ', 'join'), (undefined(name='commands_default_list') if l_1_commands_default_list is missing else l_1_commands_default_list), _loop_vars=_loop_vars)
                        _loop_vars['command_default_cli'] = l_1_command_default_cli
                        if (undefined(name='command_default_cli') if l_1_command_default_cli is missing else l_1_command_default_cli):
                            pass
                            yield 'aaa accounting commands '
                            yield str(environment.getattr(l_1_command_default, 'commands'))
                            yield ' default '
                            yield str(environment.getattr(l_1_command_default, 'type'))
                            yield ' '
                            yield str((undefined(name='command_default_cli') if l_1_command_default_cli is missing else l_1_command_default_cli))
                            yield '\n'
            l_1_command_default = l_1_commands_default_list = l_1_command_default_cli = missing

blocks = {}
debug_info = '7=26&8=28&10=31&11=33&12=36&13=40&14=42&15=43&16=45&17=47&20=49&21=52&22=55&25=59&26=61&27=66&28=68&29=71&30=73&31=75&32=77&33=81&34=83&35=84&36=86&37=88&40=90&41=92&42=95&48=102&50=105&51=107&52=110&53=114&54=116&55=117&56=119&57=121&60=123&61=126&62=129&65=133&67=136&68=138&69=141&70=145&71=147&72=148&73=150&74=152&77=154&78=157&79=160&82=164&83=166&84=169&85=173&86=175&87=176&88=178&89=180&90=182&92=184&95=186&96=189&97=192&100=196&101=198&102=203&103=205&104=208&105=210&106=212&107=214&108=218&109=220&110=221&111=223&112=225&115=227&116=229&117=232'