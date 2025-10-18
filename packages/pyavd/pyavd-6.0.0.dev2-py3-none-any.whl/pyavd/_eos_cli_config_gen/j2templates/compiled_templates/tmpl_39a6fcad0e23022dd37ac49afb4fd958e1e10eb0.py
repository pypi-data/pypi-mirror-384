from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/traffic-policies.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_traffic_policies = resolve('traffic_policies')
    try:
        t_1 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_2 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_3 = environment.filters['lower']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'lower' found.")
    try:
        t_4 = environment.filters['unique']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'unique' found.")
    try:
        t_5 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    try:
        t_6 = environment.tests['defined']
    except KeyError:
        @internalcode
        def t_6(*unused):
            raise TemplateRuntimeError("No test named 'defined' found.")
    pass
    if t_5((undefined(name='traffic_policies') if l_0_traffic_policies is missing else l_0_traffic_policies)):
        pass
        yield '!\ntraffic-policies\n'
        l_1_loop = missing
        for l_1_field_set_port, l_1_loop in LoopContext(t_1(environment.getattr(environment.getattr((undefined(name='traffic_policies') if l_0_traffic_policies is missing else l_0_traffic_policies), 'field_sets'), 'ports'), 'name'), undefined):
            _loop_vars = {}
            pass
            yield '   field-set l4-port '
            yield str(environment.getattr(l_1_field_set_port, 'name'))
            yield '\n'
            if t_5(environment.getattr(l_1_field_set_port, 'port_range')):
                pass
                yield '      '
                yield str(environment.getattr(l_1_field_set_port, 'port_range'))
                yield '\n'
            if (not environment.getattr(l_1_loop, 'last')):
                pass
                yield '   !\n'
        l_1_loop = l_1_field_set_port = missing
        l_1_loop = missing
        for l_1_field_set_ipv4, l_1_loop in LoopContext(t_1(environment.getattr(environment.getattr((undefined(name='traffic_policies') if l_0_traffic_policies is missing else l_0_traffic_policies), 'field_sets'), 'ipv4'), 'name'), undefined):
            _loop_vars = {}
            pass
            yield '   field-set ipv4 prefix '
            yield str(environment.getattr(l_1_field_set_ipv4, 'name'))
            yield '\n'
            if t_5(environment.getattr(l_1_field_set_ipv4, 'prefixes')):
                pass
                yield '      '
                yield str(t_2(context.eval_ctx, t_1(environment.getattr(l_1_field_set_ipv4, 'prefixes')), ' '))
                yield '\n'
            if t_5(environment.getattr(l_1_field_set_ipv4, 'except')):
                pass
                yield '      except '
                yield str(t_2(context.eval_ctx, t_1(environment.getattr(l_1_field_set_ipv4, 'except')), ' '))
                yield '\n'
            if (not environment.getattr(l_1_loop, 'last')):
                pass
                yield '   !\n'
        l_1_loop = l_1_field_set_ipv4 = missing
        l_1_loop = missing
        for l_1_field_set_ipv6, l_1_loop in LoopContext(t_1(environment.getattr(environment.getattr((undefined(name='traffic_policies') if l_0_traffic_policies is missing else l_0_traffic_policies), 'field_sets'), 'ipv6'), 'name'), undefined):
            _loop_vars = {}
            pass
            yield '   field-set ipv6 prefix '
            yield str(environment.getattr(l_1_field_set_ipv6, 'name'))
            yield '\n'
            if t_5(environment.getattr(l_1_field_set_ipv6, 'prefixes')):
                pass
                yield '      '
                yield str(t_2(context.eval_ctx, t_1(environment.getattr(l_1_field_set_ipv6, 'prefixes')), ' '))
                yield '\n'
            if t_5(environment.getattr(l_1_field_set_ipv6, 'except')):
                pass
                yield '      except '
                yield str(t_2(context.eval_ctx, t_1(environment.getattr(l_1_field_set_ipv6, 'except')), ' '))
                yield '\n'
            if (not environment.getattr(l_1_loop, 'last')):
                pass
                yield '   !\n'
        l_1_loop = l_1_field_set_ipv6 = missing
        if t_5(environment.getattr(environment.getattr((undefined(name='traffic_policies') if l_0_traffic_policies is missing else l_0_traffic_policies), 'options'), 'counter_per_interface'), True):
            pass
            yield '   counter interface per-interface ingress\n'
        if t_5(environment.getattr(environment.getattr((undefined(name='traffic_policies') if l_0_traffic_policies is missing else l_0_traffic_policies), 'options'), 'counter_interface_poll_interval')):
            pass
            yield '   counter interface poll interval '
            yield str(environment.getattr(environment.getattr((undefined(name='traffic_policies') if l_0_traffic_policies is missing else l_0_traffic_policies), 'options'), 'counter_interface_poll_interval'))
            yield ' seconds\n'
        for l_1_policy in t_1(environment.getattr((undefined(name='traffic_policies') if l_0_traffic_policies is missing else l_0_traffic_policies), 'policies'), 'name'):
            _loop_vars = {}
            pass
            yield '   !\n   traffic-policy '
            yield str(environment.getattr(l_1_policy, 'name'))
            yield '\n'
            if t_5(environment.getattr(l_1_policy, 'counters')):
                pass
                yield '      counter '
                yield str(t_2(context.eval_ctx, t_1(t_4(environment, environment.getattr(l_1_policy, 'counters'))), ' '))
                yield '\n      !\n'
            if t_5(environment.getattr(l_1_policy, 'matches')):
                pass
                for l_2_match in environment.getattr(l_1_policy, 'matches'):
                    l_2_bgp_flag = resolve('bgp_flag')
                    l_2_redirect_cli = resolve('redirect_cli')
                    l_2_next_hop_flag = resolve('next_hop_flag')
                    _loop_vars = {}
                    pass
                    yield '      match '
                    yield str(environment.getattr(l_2_match, 'name'))
                    yield ' '
                    yield str(t_3(environment.getattr(l_2_match, 'type')))
                    yield '\n'
                    if t_5(environment.getattr(environment.getattr(l_2_match, 'source'), 'prefixes')):
                        pass
                        yield '         source prefix '
                        yield str(t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(l_2_match, 'source'), 'prefixes')), ' '))
                        yield '\n'
                    elif t_5(environment.getattr(environment.getattr(l_2_match, 'source'), 'prefix_lists')):
                        pass
                        yield '         source prefix field-set '
                        yield str(t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(l_2_match, 'source'), 'prefix_lists')), ' '))
                        yield '\n'
                    if t_5(environment.getattr(environment.getattr(l_2_match, 'destination'), 'prefixes')):
                        pass
                        yield '         destination prefix '
                        yield str(t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(l_2_match, 'destination'), 'prefixes')), ' '))
                        yield '\n'
                    elif t_5(environment.getattr(environment.getattr(l_2_match, 'destination'), 'prefix_lists')):
                        pass
                        yield '         destination prefix field-set '
                        yield str(t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(l_2_match, 'destination'), 'prefix_lists')), ' '))
                        yield '\n'
                    if t_5(environment.getattr(l_2_match, 'protocols')):
                        pass
                        l_2_bgp_flag = True
                        _loop_vars['bgp_flag'] = l_2_bgp_flag
                        for l_3_protocol in environment.getattr(l_2_match, 'protocols'):
                            l_3_protocol_neighbors_cli = resolve('protocol_neighbors_cli')
                            l_3_bgp_flag = l_2_bgp_flag
                            l_3_protocol_cli = resolve('protocol_cli')
                            l_3_protocol_port_cli = resolve('protocol_port_cli')
                            l_3_protocol_field_cli = resolve('protocol_field_cli')
                            _loop_vars = {}
                            pass
                            if ((t_3(environment.getattr(l_3_protocol, 'protocol')) in ['neighbors', 'bgp']) and (undefined(name='bgp_flag') if l_3_bgp_flag is missing else l_3_bgp_flag)):
                                pass
                                if (t_3(environment.getattr(l_3_protocol, 'protocol')) == 'neighbors'):
                                    pass
                                    l_3_protocol_neighbors_cli = 'protocol neighbors bgp'
                                    _loop_vars['protocol_neighbors_cli'] = l_3_protocol_neighbors_cli
                                    if t_5(environment.getattr(l_3_protocol, 'enforce_gtsm'), True):
                                        pass
                                        l_3_protocol_neighbors_cli = str_join(((undefined(name='protocol_neighbors_cli') if l_3_protocol_neighbors_cli is missing else l_3_protocol_neighbors_cli), ' enforce ttl maximum-hops', ))
                                        _loop_vars['protocol_neighbors_cli'] = l_3_protocol_neighbors_cli
                                    yield '         '
                                    yield str((undefined(name='protocol_neighbors_cli') if l_3_protocol_neighbors_cli is missing else l_3_protocol_neighbors_cli))
                                    yield '\n'
                                else:
                                    pass
                                    yield '         protocol bgp\n'
                                break
                            else:
                                pass
                                l_3_bgp_flag = False
                                _loop_vars['bgp_flag'] = l_3_bgp_flag
                                l_3_protocol_cli = str_join(('protocol ', t_3(environment.getattr(l_3_protocol, 'protocol')), ))
                                _loop_vars['protocol_cli'] = l_3_protocol_cli
                                if (t_5(environment.getattr(l_3_protocol, 'flags')) and (t_3(environment.getattr(l_3_protocol, 'protocol')) == 'tcp')):
                                    pass
                                    for l_4_flag in environment.getattr(l_3_protocol, 'flags'):
                                        _loop_vars = {}
                                        pass
                                        yield '         '
                                        yield str((undefined(name='protocol_cli') if l_3_protocol_cli is missing else l_3_protocol_cli))
                                        yield ' flags '
                                        yield str(l_4_flag)
                                        yield '\n'
                                    l_4_flag = missing
                                if ((t_3(environment.getattr(l_3_protocol, 'protocol')) in ['tcp', 'udp']) and (((t_5(environment.getattr(l_3_protocol, 'src_port')) or t_5(environment.getattr(l_3_protocol, 'dst_port'))) or t_5(environment.getattr(l_3_protocol, 'src_field'))) or t_5(environment.getattr(l_3_protocol, 'dst_field')))):
                                    pass
                                    if (t_5(environment.getattr(l_3_protocol, 'src_port')) or t_5(environment.getattr(l_3_protocol, 'dst_port'))):
                                        pass
                                        l_3_protocol_port_cli = (undefined(name='protocol_cli') if l_3_protocol_cli is missing else l_3_protocol_cli)
                                        _loop_vars['protocol_port_cli'] = l_3_protocol_port_cli
                                        if t_5(environment.getattr(l_3_protocol, 'src_port')):
                                            pass
                                            l_3_protocol_port_cli = str_join(((undefined(name='protocol_port_cli') if l_3_protocol_port_cli is missing else l_3_protocol_port_cli), ' source port ', environment.getattr(l_3_protocol, 'src_port'), ))
                                            _loop_vars['protocol_port_cli'] = l_3_protocol_port_cli
                                        if t_5(environment.getattr(l_3_protocol, 'dst_port')):
                                            pass
                                            l_3_protocol_port_cli = str_join(((undefined(name='protocol_port_cli') if l_3_protocol_port_cli is missing else l_3_protocol_port_cli), ' destination port ', environment.getattr(l_3_protocol, 'dst_port'), ))
                                            _loop_vars['protocol_port_cli'] = l_3_protocol_port_cli
                                        yield '         '
                                        yield str((undefined(name='protocol_port_cli') if l_3_protocol_port_cli is missing else l_3_protocol_port_cli))
                                        yield '\n'
                                    if (t_5(environment.getattr(l_3_protocol, 'src_field')) or t_5(environment.getattr(l_3_protocol, 'dst_field'))):
                                        pass
                                        l_3_protocol_field_cli = (undefined(name='protocol_cli') if l_3_protocol_cli is missing else l_3_protocol_cli)
                                        _loop_vars['protocol_field_cli'] = l_3_protocol_field_cli
                                        if t_5(environment.getattr(l_3_protocol, 'src_field')):
                                            pass
                                            l_3_protocol_field_cli = str_join(((undefined(name='protocol_field_cli') if l_3_protocol_field_cli is missing else l_3_protocol_field_cli), ' source port field-set ', environment.getattr(l_3_protocol, 'src_field'), ))
                                            _loop_vars['protocol_field_cli'] = l_3_protocol_field_cli
                                        if t_5(environment.getattr(l_3_protocol, 'dst_field')):
                                            pass
                                            l_3_protocol_field_cli = str_join(((undefined(name='protocol_field_cli') if l_3_protocol_field_cli is missing else l_3_protocol_field_cli), ' destination port field-set ', environment.getattr(l_3_protocol, 'dst_field'), ))
                                            _loop_vars['protocol_field_cli'] = l_3_protocol_field_cli
                                        yield '         '
                                        yield str((undefined(name='protocol_field_cli') if l_3_protocol_field_cli is missing else l_3_protocol_field_cli))
                                        yield '\n'
                                elif (t_5(environment.getattr(l_3_protocol, 'icmp_type')) and (t_3(environment.getattr(l_3_protocol, 'protocol')) == 'icmp')):
                                    pass
                                    yield '         '
                                    yield str((undefined(name='protocol_cli') if l_3_protocol_cli is missing else l_3_protocol_cli))
                                    yield ' type '
                                    yield str(t_2(context.eval_ctx, t_1(environment.getattr(l_3_protocol, 'icmp_type')), ' '))
                                    yield ' code all\n'
                                else:
                                    pass
                                    yield '         '
                                    yield str((undefined(name='protocol_cli') if l_3_protocol_cli is missing else l_3_protocol_cli))
                                    yield '\n'
                        l_3_protocol = l_3_protocol_neighbors_cli = l_3_bgp_flag = l_3_protocol_cli = l_3_protocol_port_cli = l_3_protocol_field_cli = missing
                    if t_5(environment.getattr(environment.getattr(l_2_match, 'fragment'), 'offset')):
                        pass
                        yield '         fragment offset '
                        yield str(environment.getattr(environment.getattr(l_2_match, 'fragment'), 'offset'))
                        yield '\n'
                    elif t_6(environment.getattr(l_2_match, 'fragment')):
                        pass
                        yield '         fragment\n'
                    if t_5(environment.getattr(l_2_match, 'ttl')):
                        pass
                        yield '         ttl '
                        yield str(environment.getattr(l_2_match, 'ttl'))
                        yield '\n'
                    if ((((t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'count')) or t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'traffic_class'))) or t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'dscp'))) or t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'drop'), True)) or t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'))):
                        pass
                        yield '         !\n         actions\n'
                        if t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'count')):
                            pass
                            yield '            count '
                            yield str(environment.getattr(environment.getattr(l_2_match, 'actions'), 'count'))
                            yield '\n'
                        if t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'drop'), True):
                            pass
                            yield '            drop\n'
                            if t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'log'), True):
                                pass
                                yield '            log\n'
                        if t_5(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'aggregation_groups')):
                            pass
                            yield '            redirect aggregation group '
                            yield str(t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'aggregation_groups')), ' '))
                            yield '\n'
                        if t_5(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'interface')):
                            pass
                            yield '            redirect interface '
                            yield str(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'interface'))
                            yield '\n'
                        if ((not (t_5(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'interface')) or t_5(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'aggregation_groups')))) and t_5(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'))):
                            pass
                            l_2_redirect_cli = 'redirect next-hop '
                            _loop_vars['redirect_cli'] = l_2_redirect_cli
                            l_2_next_hop_flag = False
                            _loop_vars['next_hop_flag'] = l_2_next_hop_flag
                            if t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'ipv4_addresses')):
                                pass
                                l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'ipv4_addresses')), ' '), ))
                                _loop_vars['redirect_cli'] = l_2_redirect_cli
                                if t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'vrf')):
                                    pass
                                    l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), ' vrf ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'vrf'), ))
                                    _loop_vars['redirect_cli'] = l_2_redirect_cli
                                l_2_next_hop_flag = True
                                _loop_vars['next_hop_flag'] = l_2_next_hop_flag
                            elif t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'ipv6_addresses')):
                                pass
                                l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'ipv6_addresses')), ' '), ))
                                _loop_vars['redirect_cli'] = l_2_redirect_cli
                                if t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'vrf')):
                                    pass
                                    l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), ' vrf ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'vrf'), ))
                                    _loop_vars['redirect_cli'] = l_2_redirect_cli
                                l_2_next_hop_flag = True
                                _loop_vars['next_hop_flag'] = l_2_next_hop_flag
                            elif t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'groups')):
                                pass
                                l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), 'group ', t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'groups')), ' '), ))
                                _loop_vars['redirect_cli'] = l_2_redirect_cli
                                l_2_next_hop_flag = True
                                _loop_vars['next_hop_flag'] = l_2_next_hop_flag
                            elif t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'recursive_ipv4_addresses')):
                                pass
                                l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), 'recursive ', t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'recursive_ipv4_addresses')), ' '), ))
                                _loop_vars['redirect_cli'] = l_2_redirect_cli
                                if t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'vrf')):
                                    pass
                                    l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), ' vrf ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'vrf'), ))
                                    _loop_vars['redirect_cli'] = l_2_redirect_cli
                                l_2_next_hop_flag = True
                                _loop_vars['next_hop_flag'] = l_2_next_hop_flag
                            elif t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'recursive_ipv6_addresses')):
                                pass
                                l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), 'recursive ', t_2(context.eval_ctx, t_1(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'recursive_ipv6_addresses')), ' '), ))
                                _loop_vars['redirect_cli'] = l_2_redirect_cli
                                if t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'vrf')):
                                    pass
                                    l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), ' vrf ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'vrf'), ))
                                    _loop_vars['redirect_cli'] = l_2_redirect_cli
                                l_2_next_hop_flag = True
                                _loop_vars['next_hop_flag'] = l_2_next_hop_flag
                            if (t_5(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'ttl')) and (undefined(name='next_hop_flag') if l_2_next_hop_flag is missing else l_2_next_hop_flag)):
                                pass
                                l_2_redirect_cli = str_join(((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli), ' ttl ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_2_match, 'actions'), 'redirect'), 'next_hop'), 'ttl'), ))
                                _loop_vars['redirect_cli'] = l_2_redirect_cli
                            if ((undefined(name='next_hop_flag') if l_2_next_hop_flag is missing else l_2_next_hop_flag) == True):
                                pass
                                yield '            '
                                yield str((undefined(name='redirect_cli') if l_2_redirect_cli is missing else l_2_redirect_cli))
                                yield '\n'
                        if t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'dscp')):
                            pass
                            yield '            set dscp '
                            yield str(environment.getattr(environment.getattr(l_2_match, 'actions'), 'dscp'))
                            yield '\n'
                        if t_5(environment.getattr(environment.getattr(l_2_match, 'actions'), 'traffic_class')):
                            pass
                            yield '            set traffic class '
                            yield str(environment.getattr(environment.getattr(l_2_match, 'actions'), 'traffic_class'))
                            yield '\n'
                    yield '      !\n'
                l_2_match = l_2_bgp_flag = l_2_redirect_cli = l_2_next_hop_flag = missing
            yield '      match ipv4-all-default ipv4\n'
            if t_5(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv4')):
                pass
                yield '         actions\n'
                if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv4'), 'count')):
                    pass
                    yield '            count '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv4'), 'count'))
                    yield '\n'
                if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv4'), 'drop'), True):
                    pass
                    yield '            drop\n'
                    if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv4'), 'log'), True):
                        pass
                        yield '            log\n'
                if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv4'), 'dscp')):
                    pass
                    yield '            set dscp '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv4'), 'dscp'))
                    yield '\n'
                if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv4'), 'traffic_class')):
                    pass
                    yield '            set traffic class '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv4'), 'traffic_class'))
                    yield '\n'
            yield '      !\n      match ipv6-all-default ipv6\n'
            if t_5(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv6')):
                pass
                yield '         actions\n'
                if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv6'), 'count')):
                    pass
                    yield '            count '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv6'), 'count'))
                    yield '\n'
                if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv6'), 'drop'), True):
                    pass
                    yield '            drop\n'
                    if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv6'), 'log'), True):
                        pass
                        yield '            log\n'
                if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv6'), 'dscp')):
                    pass
                    yield '            set dscp '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv6'), 'dscp'))
                    yield '\n'
                if t_5(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv6'), 'traffic_class')):
                    pass
                    yield '            set traffic class '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_policy, 'default_actions'), 'ipv6'), 'traffic_class'))
                    yield '\n'
        l_1_policy = missing

blocks = {}
debug_info = '7=48&12=52&13=56&14=58&15=61&17=63&22=68&23=72&24=74&25=77&27=79&28=82&30=84&35=89&36=93&37=95&38=98&40=100&41=103&43=105&48=109&51=112&52=115&55=117&57=121&59=123&60=126&63=128&65=130&66=137&68=141&69=144&70=146&71=149&74=151&75=154&76=156&77=159&80=161&81=163&82=165&83=173&84=175&85=177&86=179&87=181&89=184&93=189&95=192&96=194&97=196&98=198&99=202&102=207&108=209&109=211&110=213&111=215&113=217&114=219&116=222&119=224&120=226&121=228&122=230&124=232&125=234&127=237&129=239&130=242&132=249&138=252&139=255&140=257&144=260&145=263&148=265&152=268&153=271&156=273&159=276&163=279&164=282&166=284&167=287&169=289&170=291&171=293&172=295&173=297&174=299&175=301&177=303&178=305&179=307&180=309&181=311&183=313&184=315&185=317&186=319&187=321&188=323&189=325&190=327&192=329&193=331&194=333&195=335&196=337&198=339&200=341&201=343&203=345&204=348&208=350&209=353&212=355&213=358&222=363&225=366&226=369&229=371&232=374&237=377&238=380&241=382&242=385&247=388&250=391&251=394&254=396&257=399&262=402&263=405&266=407&267=410'