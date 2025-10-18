from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/management-ssh.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_management_ssh = resolve('management_ssh')
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
        t_4 = environment.filters['selectattr']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'selectattr' found.")
    try:
        t_5 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    if t_5((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh)):
        pass
        yield '!\nmanagement ssh\n'
        for l_1_vrf in t_4(context, t_1(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'vrfs'), []), 'ip_access_group_in', 'arista.avd.defined'):
            _loop_vars = {}
            pass
            yield '   ip access-group '
            yield str(environment.getattr(l_1_vrf, 'ip_access_group_in'))
            yield ' vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield ' in\n'
        l_1_vrf = missing
        if t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'ip_access_group_in')):
            pass
            yield '   ip access-group '
            yield str(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'ip_access_group_in'))
            yield ' in\n'
        for l_1_vrf in t_4(context, t_1(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'vrfs'), []), 'ipv6_access_group_in', 'arista.avd.defined'):
            _loop_vars = {}
            pass
            yield '   ipv6 access-group '
            yield str(environment.getattr(l_1_vrf, 'ipv6_access_group_in'))
            yield ' vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield ' in\n'
        l_1_vrf = missing
        if t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'ipv6_access_group_in')):
            pass
            yield '   ipv6 access-group '
            yield str(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'ipv6_access_group_in'))
            yield ' in\n'
        if t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'idle_timeout')):
            pass
            yield '   idle-timeout '
            yield str(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'idle_timeout'))
            yield '\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'authentication'), 'protocols')):
            pass
            yield '   authentication protocol '
            yield str(t_3(context.eval_ctx, environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'authentication'), 'protocols'), ' '))
            yield '\n'
        if t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'cipher')):
            pass
            yield '   cipher '
            yield str(t_3(context.eval_ctx, environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'cipher'), ' '))
            yield '\n'
        if t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'key_exchange')):
            pass
            yield '   key-exchange '
            yield str(t_3(context.eval_ctx, environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'key_exchange'), ' '))
            yield '\n'
        if t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'mac')):
            pass
            yield '   mac '
            yield str(t_3(context.eval_ctx, environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'mac'), ' '))
            yield '\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'hostkey'), 'server')):
            pass
            yield '   hostkey server '
            yield str(t_3(context.eval_ctx, environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'hostkey'), 'server'), ' '))
            yield '\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'connection'), 'per_host')):
            pass
            yield '   connection per-host '
            yield str(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'connection'), 'per_host'))
            yield '\n'
        if t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'fips_restrictions'), True):
            pass
            yield '   fips restrictions\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'hostkey'), 'client_strict_checking'), True):
            pass
            yield '   hostkey client strict-checking\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'connection'), 'limit')):
            pass
            yield '   connection limit '
            yield str(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'connection'), 'limit'))
            yield '\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'authentication'), 'empty_passwords')):
            pass
            yield '   authentication empty-passwords '
            yield str(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'authentication'), 'empty_passwords'))
            yield '\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'client_alive'), 'interval')):
            pass
            yield '   client-alive interval '
            yield str(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'client_alive'), 'interval'))
            yield '\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'client_alive'), 'count_max')):
            pass
            yield '   client-alive count-max '
            yield str(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'client_alive'), 'count_max'))
            yield '\n'
        if t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'enable'), False):
            pass
            yield '   shutdown\n'
        elif t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'enable'), True):
            pass
            yield '   no shutdown\n'
        if t_5(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'log_level')):
            pass
            yield '   log-level '
            yield str(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'log_level'))
            yield '\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'hostkey'), 'server_cert')):
            pass
            yield '   hostkey server cert '
            yield str(environment.getattr(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'hostkey'), 'server_cert'))
            yield '\n'
        for l_1_vrf in t_2(environment.getattr((undefined(name='management_ssh') if l_0_management_ssh is missing else l_0_management_ssh), 'vrfs'), 'name'):
            _loop_vars = {}
            pass
            yield '   !\n   vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
            if t_5(environment.getattr(l_1_vrf, 'enable'), True):
                pass
                yield '      no shutdown\n'
            elif t_5(environment.getattr(l_1_vrf, 'enable'), False):
                pass
                yield '      shutdown\n'
        l_1_vrf = missing

blocks = {}
debug_info = '7=42&10=45&11=49&13=54&14=57&16=59&17=63&19=68&20=71&22=73&23=76&25=78&26=81&28=83&29=86&31=88&32=91&34=93&35=96&37=98&38=101&40=103&41=106&43=108&46=111&49=114&50=117&52=119&53=122&55=124&56=127&58=129&59=132&61=134&63=137&66=140&67=143&69=145&70=148&72=150&74=154&75=156&77=159'