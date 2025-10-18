from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/ntp.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_ntp = resolve('ntp')
    l_0_ntp_int_cli = resolve('ntp_int_cli')
    l_0_ntp_vrf = resolve('ntp_vrf')
    try:
        t_1 = environment.filters['arista.avd.hide_passwords']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.hide_passwords' found.")
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
    if t_3((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp)):
        pass
        yield '!\n'
        for l_1_authentication_key in t_2(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'authentication_keys'), 'id'):
            l_1_hide_passwords = resolve('hide_passwords')
            l_1_ntp_auth_key_cli = missing
            _loop_vars = {}
            pass
            l_1_ntp_auth_key_cli = str_join(('ntp authentication-key ', environment.getattr(l_1_authentication_key, 'id'), ' ', environment.getattr(l_1_authentication_key, 'hash_algorithm'), ))
            _loop_vars['ntp_auth_key_cli'] = l_1_ntp_auth_key_cli
            if t_3(environment.getattr(l_1_authentication_key, 'key_type')):
                pass
                l_1_ntp_auth_key_cli = str_join(((undefined(name='ntp_auth_key_cli') if l_1_ntp_auth_key_cli is missing else l_1_ntp_auth_key_cli), ' ', environment.getattr(l_1_authentication_key, 'key_type'), ))
                _loop_vars['ntp_auth_key_cli'] = l_1_ntp_auth_key_cli
            l_1_ntp_auth_key_cli = str_join(((undefined(name='ntp_auth_key_cli') if l_1_ntp_auth_key_cli is missing else l_1_ntp_auth_key_cli), ' ', t_1(environment.getattr(l_1_authentication_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)), ))
            _loop_vars['ntp_auth_key_cli'] = l_1_ntp_auth_key_cli
            yield str((undefined(name='ntp_auth_key_cli') if l_1_ntp_auth_key_cli is missing else l_1_ntp_auth_key_cli))
            yield '\n'
        l_1_authentication_key = l_1_ntp_auth_key_cli = l_1_hide_passwords = missing
        if t_3(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'trusted_keys')):
            pass
            yield 'ntp trusted-key '
            yield str(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'trusted_keys'))
            yield '\n'
        if t_3(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'authenticate_servers_only'), True):
            pass
            yield 'ntp authenticate servers\n'
        elif t_3(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'authenticate'), True):
            pass
            yield 'ntp authenticate\n'
        if t_3(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'local_interface'), 'name')):
            pass
            l_0_ntp_int_cli = 'ntp local-interface'
            context.vars['ntp_int_cli'] = l_0_ntp_int_cli
            context.exported_vars.add('ntp_int_cli')
            if (t_3(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'local_interface'), 'vrf')) and (environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'local_interface'), 'vrf') != 'default')):
                pass
                l_0_ntp_int_cli = str_join(((undefined(name='ntp_int_cli') if l_0_ntp_int_cli is missing else l_0_ntp_int_cli), ' vrf ', environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'local_interface'), 'vrf'), ))
                context.vars['ntp_int_cli'] = l_0_ntp_int_cli
                context.exported_vars.add('ntp_int_cli')
            l_0_ntp_int_cli = str_join(((undefined(name='ntp_int_cli') if l_0_ntp_int_cli is missing else l_0_ntp_int_cli), ' ', environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'local_interface'), 'name'), ))
            context.vars['ntp_int_cli'] = l_0_ntp_int_cli
            context.exported_vars.add('ntp_int_cli')
            yield str((undefined(name='ntp_int_cli') if l_0_ntp_int_cli is missing else l_0_ntp_int_cli))
            yield '\n'
        l_0_ntp_vrf = ''
        context.vars['ntp_vrf'] = l_0_ntp_vrf
        context.exported_vars.add('ntp_vrf')
        if (t_3(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'vrf')) and (environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'vrf') != 'default')):
            pass
            l_0_ntp_vrf = environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'vrf')
            context.vars['ntp_vrf'] = l_0_ntp_vrf
            context.exported_vars.add('ntp_vrf')
        for l_1_server in t_2(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'servers'), 'name'):
            l_1_hide_passwords = resolve('hide_passwords')
            l_1_ntp_server_cli = missing
            _loop_vars = {}
            pass
            l_1_ntp_server_cli = 'ntp server'
            _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            if (undefined(name='ntp_vrf') if l_0_ntp_vrf is missing else l_0_ntp_vrf):
                pass
                l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' vrf ', (undefined(name='ntp_vrf') if l_0_ntp_vrf is missing else l_0_ntp_vrf), ))
                _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' ', environment.getattr(l_1_server, 'name'), ))
            _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            if t_3(environment.getattr(l_1_server, 'preferred'), True):
                pass
                l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' prefer', ))
                _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            if t_3(environment.getattr(l_1_server, 'burst'), True):
                pass
                l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' burst', ))
                _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            if t_3(environment.getattr(l_1_server, 'iburst'), True):
                pass
                l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' iburst', ))
                _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            if t_3(environment.getattr(l_1_server, 'version')):
                pass
                l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' version ', environment.getattr(l_1_server, 'version'), ))
                _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            if t_3(environment.getattr(l_1_server, 'minpoll')):
                pass
                l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' minpoll ', environment.getattr(l_1_server, 'minpoll'), ))
                _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            if t_3(environment.getattr(l_1_server, 'maxpoll')):
                pass
                l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' maxpoll ', environment.getattr(l_1_server, 'maxpoll'), ))
                _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            if t_3(environment.getattr(l_1_server, 'local_interface')):
                pass
                l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' local-interface ', environment.getattr(l_1_server, 'local_interface'), ))
                _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            if t_3(environment.getattr(l_1_server, 'key')):
                pass
                l_1_ntp_server_cli = str_join(((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli), ' key ', t_1(environment.getattr(l_1_server, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)), ))
                _loop_vars['ntp_server_cli'] = l_1_ntp_server_cli
            yield str((undefined(name='ntp_server_cli') if l_1_ntp_server_cli is missing else l_1_ntp_server_cli))
            yield '\n'
        l_1_server = l_1_ntp_server_cli = l_1_hide_passwords = missing
        if t_3(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'serve')):
            pass
            if t_3(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'serve'), 'serve_all'), True):
                pass
                yield 'ntp serve all\n'
            for l_1_vrf in t_2(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'serve'), 'vrfs'), sort_key='name', ignore_case=False):
                _loop_vars = {}
                pass
                if t_3(environment.getattr(l_1_vrf, 'serve_all'), True):
                    pass
                    yield 'ntp serve all vrf '
                    yield str(environment.getattr(l_1_vrf, 'name'))
                    yield '\n'
            l_1_vrf = missing
            for l_1_vrf in t_2(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'serve'), 'vrfs'), sort_key='name', ignore_case=False):
                _loop_vars = {}
                pass
                if t_3(environment.getattr(l_1_vrf, 'access_group')):
                    pass
                    yield 'ntp serve ip access-group '
                    yield str(environment.getattr(l_1_vrf, 'access_group'))
                    yield ' vrf '
                    yield str(environment.getattr(l_1_vrf, 'name'))
                    yield ' in\n'
            l_1_vrf = missing
            if t_3(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'serve'), 'access_group')):
                pass
                yield 'ntp serve ip access-group '
                yield str(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'serve'), 'access_group'))
                yield ' in\n'
            for l_1_vrf in t_2(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'serve'), 'vrfs'), sort_key='name', ignore_case=False):
                _loop_vars = {}
                pass
                if t_3(environment.getattr(l_1_vrf, 'ipv6_access_group')):
                    pass
                    yield 'ntp serve ipv6 access-group '
                    yield str(environment.getattr(l_1_vrf, 'ipv6_access_group'))
                    yield ' vrf '
                    yield str(environment.getattr(l_1_vrf, 'name'))
                    yield ' in\n'
            l_1_vrf = missing
            if t_3(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'serve'), 'ipv6_access_group')):
                pass
                yield 'ntp serve ipv6 access-group '
                yield str(environment.getattr(environment.getattr((undefined(name='ntp') if l_0_ntp is missing else l_0_ntp), 'serve'), 'ipv6_access_group'))
                yield ' in\n'

blocks = {}
debug_info = '7=32&9=35&10=40&11=42&12=44&14=46&15=48&17=51&18=54&20=56&22=59&25=62&26=64&27=67&28=69&30=72&31=75&33=77&34=80&35=82&37=85&38=90&39=92&40=94&42=96&43=98&44=100&46=102&47=104&49=106&50=108&52=110&53=112&55=114&56=116&58=118&59=120&61=122&62=124&64=126&65=128&67=130&69=133&70=135&73=138&74=141&75=144&78=147&79=150&80=153&83=158&84=161&86=163&87=166&88=169&91=174&92=177'