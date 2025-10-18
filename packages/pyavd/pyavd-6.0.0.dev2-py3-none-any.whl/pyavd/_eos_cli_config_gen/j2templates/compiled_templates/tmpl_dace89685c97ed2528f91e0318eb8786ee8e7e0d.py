from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/port-channel-interfaces.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_port_channel_interfaces = resolve('port_channel_interfaces')
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.filters['arista.avd.hide_passwords']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.hide_passwords' found.")
    try:
        t_3 = environment.filters['arista.avd.natural_sort']
    except KeyError:
        @internalcode
        def t_3(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.natural_sort' found.")
    try:
        t_4 = environment.filters['arista.avd.range_expand']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.range_expand' found.")
    try:
        t_5 = environment.filters['indent']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No filter named 'indent' found.")
    try:
        t_6 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_6(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_7 = environment.filters['replace']
    except KeyError:
        @internalcode
        def t_7(*unused):
            raise TemplateRuntimeError("No filter named 'replace' found.")
    try:
        t_8 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_8(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    pass
    for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
        l_1_encapsulation_dot1q_cli = resolve('encapsulation_dot1q_cli')
        l_1_client_encapsulation = resolve('client_encapsulation')
        l_1_network_flag = resolve('network_flag')
        l_1_encapsulation_cli = resolve('encapsulation_cli')
        l_1_network_encapsulation = resolve('network_encapsulation')
        l_1_dfe_algo_cli = resolve('dfe_algo_cli')
        l_1_dfe_hold_time_cli = resolve('dfe_hold_time_cli')
        l_1_host_proxy_cli = resolve('host_proxy_cli')
        l_1_interface_ip_nat = resolve('interface_ip_nat')
        l_1_hide_passwords = resolve('hide_passwords')
        l_1_sorted_vlans_cli = resolve('sorted_vlans_cli')
        l_1_isis_auth_cli = resolve('isis_auth_cli')
        l_1_both_key_ids = resolve('both_key_ids')
        l_1_backup_link_cli = resolve('backup_link_cli')
        l_1_tap_identity_cli = resolve('tap_identity_cli')
        l_1_tap_mac_address_cli = resolve('tap_mac_address_cli')
        l_1_tap_truncation_cli = resolve('tap_truncation_cli')
        l_1_tool_groups = resolve('tool_groups')
        _loop_vars = {}
        pass
        yield '!\ninterface '
        yield str(environment.getattr(l_1_port_channel_interface, 'name'))
        yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'comment')):
            pass
            for l_2_comment_line in t_1(context.call(environment.getattr(environment.getattr(l_1_port_channel_interface, 'comment'), 'splitlines'), _loop_vars=_loop_vars), []):
                _loop_vars = {}
                pass
                yield '   !! '
                yield str(l_2_comment_line)
                yield '\n'
            l_2_comment_line = missing
        if t_8(environment.getattr(l_1_port_channel_interface, 'profile')):
            pass
            yield '   profile '
            yield str(environment.getattr(l_1_port_channel_interface, 'profile'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_policy'), 'input')):
            pass
            yield '   traffic-policy input '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_policy'), 'input'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_policy'), 'output')):
            pass
            yield '   traffic-policy output '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_policy'), 'output'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'description')):
            pass
            yield '   description '
            yield str(environment.getattr(l_1_port_channel_interface, 'description'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'shutdown'), True):
            pass
            yield '   shutdown\n'
        elif t_8(environment.getattr(l_1_port_channel_interface, 'shutdown'), False):
            pass
            yield '   no shutdown\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'mtu')):
            pass
            yield '   mtu '
            yield str(environment.getattr(l_1_port_channel_interface, 'mtu'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'logging'), 'event'), 'link_status'), True):
            pass
            yield '   logging event link-status\n'
        elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'logging'), 'event'), 'link_status'), False):
            pass
            yield '   no logging event link-status\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bgp'), 'session_tracker')):
            pass
            yield '   bgp session tracker '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bgp'), 'session_tracker'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'l2_protocol'), 'forwarding_profile')):
            pass
            yield '   l2-protocol forwarding profile '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'l2_protocol'), 'forwarding_profile'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'access_vlan')):
            pass
            yield '   switchport access vlan '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'access_vlan'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'native_vlan_tag'), True):
            pass
            yield '   switchport trunk native vlan tag\n'
        elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'native_vlan')):
            pass
            yield '   switchport trunk native vlan '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'native_vlan'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'phone'), 'vlan')):
            pass
            yield '   switchport phone vlan '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'phone'), 'vlan'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'phone'), 'trunk')):
            pass
            yield '   switchport phone trunk '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'phone'), 'trunk'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'in_required'), True):
            pass
            yield '   switchport vlan translation in required\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'out_required'), True):
            pass
            yield '   switchport vlan translation out required\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'dot1q'), 'vlan_tag')):
            pass
            yield '   switchport dot1q vlan tag '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'dot1q'), 'vlan_tag'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'allowed_vlan')):
            pass
            yield '   switchport trunk allowed vlan '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'allowed_vlan'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'mode')):
            pass
            yield '   switchport mode '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'mode'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'dot1q'), 'ethertype')):
            pass
            yield '   switchport dot1q ethertype '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'dot1q'), 'ethertype'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_forwarding_accept_all'), True):
            pass
            yield '   switchport vlan forwarding accept all\n'
        for l_2_trunk_group in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'groups')):
            _loop_vars = {}
            pass
            yield '   switchport trunk group '
            yield str(l_2_trunk_group)
            yield '\n'
        l_2_trunk_group = missing
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'enabled'), True):
            pass
            yield '   switchport\n'
        elif t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'enabled'), False):
            pass
            yield '   no switchport\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_dot1q'), 'vlan')):
            pass
            l_1_encapsulation_dot1q_cli = str_join(('encapsulation dot1q vlan ', environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_dot1q'), 'vlan'), ))
            _loop_vars['encapsulation_dot1q_cli'] = l_1_encapsulation_dot1q_cli
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_dot1q'), 'inner_vlan')):
                pass
                l_1_encapsulation_dot1q_cli = str_join(((undefined(name='encapsulation_dot1q_cli') if l_1_encapsulation_dot1q_cli is missing else l_1_encapsulation_dot1q_cli), ' inner ', environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_dot1q'), 'inner_vlan'), ))
                _loop_vars['encapsulation_dot1q_cli'] = l_1_encapsulation_dot1q_cli
            yield '   '
            yield str((undefined(name='encapsulation_dot1q_cli') if l_1_encapsulation_dot1q_cli is missing else l_1_encapsulation_dot1q_cli))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'vlan_id')):
            pass
            yield '   vlan id '
            yield str(environment.getattr(l_1_port_channel_interface, 'vlan_id'))
            yield '\n'
        if (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'encapsulation')) and (not t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_dot1q'), 'vlan')))):
            pass
            l_1_client_encapsulation = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'encapsulation')
            _loop_vars['client_encapsulation'] = l_1_client_encapsulation
            l_1_network_flag = False
            _loop_vars['network_flag'] = l_1_network_flag
            if ((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) in ['dot1q', 'dot1ad']):
                pass
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'vlan')):
                    pass
                    l_1_encapsulation_cli = str_join(('client ', (undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'vlan'), ))
                    _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                elif (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'outer_vlan')) and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'inner_vlan'))):
                    pass
                    if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'inner_encapsulation')):
                        pass
                        l_1_encapsulation_cli = str_join(('client ', (undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation), ' outer ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'outer_vlan'), ' inner ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'inner_encapsulation'), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'inner_vlan'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    else:
                        pass
                        l_1_encapsulation_cli = str_join(('client ', (undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation), ' outer ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'outer_vlan'), ' inner ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'inner_vlan'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    if (t_1(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'encapsulation')) == 'client inner'):
                        pass
                        l_1_network_flag = True
                        _loop_vars['network_flag'] = l_1_network_flag
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'encapsulation'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
            elif ((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) in ['untagged', 'unmatched']):
                pass
                l_1_encapsulation_cli = str_join(('client ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'encapsulation'), ))
                _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
            if t_8((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli)):
                pass
                if ((((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) in ['dot1q', 'dot1ad', 'untagged']) and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'encapsulation'))) and (not (undefined(name='network_flag') if l_1_network_flag is missing else l_1_network_flag))):
                    pass
                    l_1_network_encapsulation = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'encapsulation')
                    _loop_vars['network_encapsulation'] = l_1_network_encapsulation
                    if ((undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation) in ['dot1q', 'dot1ad']):
                        pass
                        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'vlan')):
                            pass
                            l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network ', (undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'vlan'), ))
                            _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                        elif (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'outer_vlan')) and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'inner_vlan'))):
                            pass
                            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'inner_encapsulation')):
                                pass
                                l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network ', (undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation), ' outer ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'outer_vlan'), ' inner ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'inner_encapsulation'), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'inner_vlan'), ))
                                _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                            else:
                                pass
                                l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network ', (undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation), ' outer ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'outer_vlan'), ' inner ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'inner_vlan'), ))
                                _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    elif (((undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation) == 'untagged') and ((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) == 'untagged')):
                        pass
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network untagged', ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    elif (((undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation) == 'client') and ((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) != 'untagged')):
                        pass
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' network client', ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                yield '   !\n   encapsulation vlan\n      '
                yield str((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli))
                yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'source_interface')):
            pass
            yield '   switchport source-interface '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'source_interface'))
            yield '\n'
        for l_2_vlan_translation in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'direction_both'), 'from'):
            l_2_vlan_translation_both_cli = missing
            _loop_vars = {}
            pass
            l_2_vlan_translation_both_cli = str_join(('switchport vlan translation ', environment.getattr(l_2_vlan_translation, 'from'), ))
            _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
            if t_8(environment.getattr(l_2_vlan_translation, 'dot1q_tunnel'), True):
                pass
                l_2_vlan_translation_both_cli = str_join(((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli), ' dot1q-tunnel', ))
                _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
            elif t_8(environment.getattr(l_2_vlan_translation, 'inner_vlan_from')):
                pass
                l_2_vlan_translation_both_cli = str_join(((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli), ' inner ', environment.getattr(l_2_vlan_translation, 'inner_vlan_from'), ))
                _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
                if t_8(environment.getattr(l_2_vlan_translation, 'network'), True):
                    pass
                    l_2_vlan_translation_both_cli = str_join(((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli), ' network', ))
                    _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
            l_2_vlan_translation_both_cli = str_join(((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli), ' ', environment.getattr(l_2_vlan_translation, 'to'), ))
            _loop_vars['vlan_translation_both_cli'] = l_2_vlan_translation_both_cli
            yield '   '
            yield str((undefined(name='vlan_translation_both_cli') if l_2_vlan_translation_both_cli is missing else l_2_vlan_translation_both_cli))
            yield '\n'
        l_2_vlan_translation = l_2_vlan_translation_both_cli = missing
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'direction_in')):
            pass
            for l_2_vlan_translation in environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'direction_in'):
                l_2_vlan_translation_in_cli = missing
                _loop_vars = {}
                pass
                l_2_vlan_translation_in_cli = str_join(('switchport vlan translation in ', environment.getattr(l_2_vlan_translation, 'from'), ))
                _loop_vars['vlan_translation_in_cli'] = l_2_vlan_translation_in_cli
                if t_8(environment.getattr(l_2_vlan_translation, 'dot1q_tunnel'), True):
                    pass
                    l_2_vlan_translation_in_cli = str_join(((undefined(name='vlan_translation_in_cli') if l_2_vlan_translation_in_cli is missing else l_2_vlan_translation_in_cli), ' dot1q-tunnel', ))
                    _loop_vars['vlan_translation_in_cli'] = l_2_vlan_translation_in_cli
                elif t_8(environment.getattr(l_2_vlan_translation, 'inner_vlan_from')):
                    pass
                    l_2_vlan_translation_in_cli = str_join(((undefined(name='vlan_translation_in_cli') if l_2_vlan_translation_in_cli is missing else l_2_vlan_translation_in_cli), ' inner ', environment.getattr(l_2_vlan_translation, 'inner_vlan_from'), ))
                    _loop_vars['vlan_translation_in_cli'] = l_2_vlan_translation_in_cli
                l_2_vlan_translation_in_cli = str_join(((undefined(name='vlan_translation_in_cli') if l_2_vlan_translation_in_cli is missing else l_2_vlan_translation_in_cli), ' ', environment.getattr(l_2_vlan_translation, 'to'), ))
                _loop_vars['vlan_translation_in_cli'] = l_2_vlan_translation_in_cli
                yield '   '
                yield str((undefined(name='vlan_translation_in_cli') if l_2_vlan_translation_in_cli is missing else l_2_vlan_translation_in_cli))
                yield '\n'
            l_2_vlan_translation = l_2_vlan_translation_in_cli = missing
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'direction_out')):
            pass
            for l_2_vlan_translation in environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'direction_out'):
                l_2_vlan_translation_out_cli = resolve('vlan_translation_out_cli')
                _loop_vars = {}
                pass
                if t_8(environment.getattr(l_2_vlan_translation, 'dot1q_tunnel_to')):
                    pass
                    l_2_vlan_translation_out_cli = str_join(('switchport vlan translation out ', environment.getattr(l_2_vlan_translation, 'from'), ' dot1q-tunnel ', environment.getattr(l_2_vlan_translation, 'dot1q_tunnel_to'), ))
                    _loop_vars['vlan_translation_out_cli'] = l_2_vlan_translation_out_cli
                elif t_8(environment.getattr(l_2_vlan_translation, 'to')):
                    pass
                    l_2_vlan_translation_out_cli = str_join(('switchport vlan translation out ', environment.getattr(l_2_vlan_translation, 'from'), ' ', environment.getattr(l_2_vlan_translation, 'to'), ))
                    _loop_vars['vlan_translation_out_cli'] = l_2_vlan_translation_out_cli
                    if t_8(environment.getattr(l_2_vlan_translation, 'inner_vlan_to')):
                        pass
                        l_2_vlan_translation_out_cli = str_join(((undefined(name='vlan_translation_out_cli') if l_2_vlan_translation_out_cli is missing else l_2_vlan_translation_out_cli), ' inner ', environment.getattr(l_2_vlan_translation, 'inner_vlan_to'), ))
                        _loop_vars['vlan_translation_out_cli'] = l_2_vlan_translation_out_cli
                if t_8((undefined(name='vlan_translation_out_cli') if l_2_vlan_translation_out_cli is missing else l_2_vlan_translation_out_cli)):
                    pass
                    yield '   '
                    yield str((undefined(name='vlan_translation_out_cli') if l_2_vlan_translation_out_cli is missing else l_2_vlan_translation_out_cli))
                    yield '\n'
            l_2_vlan_translation = l_2_vlan_translation_out_cli = missing
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'private_vlan_secondary'), True):
            pass
            yield '   switchport trunk private-vlan secondary\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'pvlan_mapping')):
            pass
            yield '   switchport pvlan mapping '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'pvlan_mapping'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'l2_protocol'), 'encapsulation_dot1q_vlan')):
            pass
            yield '   l2-protocol encapsulation dot1q vlan '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'l2_protocol'), 'encapsulation_dot1q_vlan'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment')):
            pass
            yield '   !\n   evpn ethernet-segment\n'
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'identifier')):
                pass
                yield '      identifier '
                yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'identifier'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'redundancy')):
                pass
                yield '      redundancy '
                yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'redundancy'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election')):
                pass
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'algorithm'), 'modulus'):
                    pass
                    yield '      designated-forwarder election algorithm modulus\n'
                elif (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'algorithm'), 'preference') and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'preference_value'))):
                    pass
                    l_1_dfe_algo_cli = str_join(('designated-forwarder election algorithm preference ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'preference_value'), ))
                    _loop_vars['dfe_algo_cli'] = l_1_dfe_algo_cli
                    if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'dont_preempt'), True):
                        pass
                        l_1_dfe_algo_cli = str_join(((undefined(name='dfe_algo_cli') if l_1_dfe_algo_cli is missing else l_1_dfe_algo_cli), ' dont-preempt', ))
                        _loop_vars['dfe_algo_cli'] = l_1_dfe_algo_cli
                    yield '      '
                    yield str((undefined(name='dfe_algo_cli') if l_1_dfe_algo_cli is missing else l_1_dfe_algo_cli))
                    yield '\n'
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'hold_time')):
                    pass
                    l_1_dfe_hold_time_cli = str_join(('designated-forwarder election hold-time ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'hold_time'), ))
                    _loop_vars['dfe_hold_time_cli'] = l_1_dfe_hold_time_cli
                    if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'subsequent_hold_time')):
                        pass
                        l_1_dfe_hold_time_cli = str_join(((undefined(name='dfe_hold_time_cli') if l_1_dfe_hold_time_cli is missing else l_1_dfe_hold_time_cli), ' subsequent-hold-time ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'subsequent_hold_time'), ))
                        _loop_vars['dfe_hold_time_cli'] = l_1_dfe_hold_time_cli
                    yield '      '
                    yield str((undefined(name='dfe_hold_time_cli') if l_1_dfe_hold_time_cli is missing else l_1_dfe_hold_time_cli))
                    yield '\n'
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'candidate_reachability_required'), True):
                    pass
                    yield '      designated-forwarder election candidate reachability required\n'
                elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election'), 'candidate_reachability_required'), False):
                    pass
                    yield '      no designated-forwarder election candidate reachability required\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'mpls'), 'tunnel_flood_filter_time')):
                pass
                yield '      mpls tunnel flood filter time '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'mpls'), 'tunnel_flood_filter_time'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'mpls'), 'shared_index')):
                pass
                yield '      mpls shared index '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'mpls'), 'shared_index'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'route_target')):
                pass
                yield '      route-target import '
                yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'route_target'))
                yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'flow_tracker'), 'hardware')):
            pass
            yield '   flow tracker hardware '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'flow_tracker'), 'hardware'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'flow_tracker'), 'sampled')):
            pass
            yield '   flow tracker sampled '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'flow_tracker'), 'sampled'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'snmp_trap_link_change'), False):
            pass
            yield '   no snmp trap link-change\n'
        elif t_8(environment.getattr(l_1_port_channel_interface, 'snmp_trap_link_change'), True):
            pass
            yield '   snmp trap link-change\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'vrf')):
            pass
            yield '   vrf '
            yield str(environment.getattr(l_1_port_channel_interface, 'vrf'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ip_proxy_arp'), True):
            pass
            yield '   ip proxy-arp\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'arp_gratuitous_accept'), True):
            pass
            yield '   arp gratuitous accept\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ip_address')):
            pass
            yield '   ip address '
            yield str(environment.getattr(l_1_port_channel_interface, 'ip_address'))
            yield '\n'
        if (t_8(environment.getattr(l_1_port_channel_interface, 'ip_address'), 'dhcp') and t_8(environment.getattr(l_1_port_channel_interface, 'dhcp_client_accept_default_route'), True)):
            pass
            yield '   dhcp client accept default-route\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ip_verify_unicast_source_reachable_via')):
            pass
            yield '   ip verify unicast source reachable-via '
            yield str(environment.getattr(l_1_port_channel_interface, 'ip_verify_unicast_source_reachable_via'))
            yield '\n'
        if ((t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'interval')) and t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'min_rx'))) and t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'multiplier'))):
            pass
            yield '   bfd interval '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'interval'))
            yield ' min-rx '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'min_rx'))
            yield ' multiplier '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'multiplier'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'echo'), True):
            pass
            yield '   bfd echo\n'
        elif t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'echo'), False):
            pass
            yield '   no bfd echo\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'neighbor')):
            pass
            yield '   bfd neighbor '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'neighbor'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'per_link'), 'enabled'), True):
            pass
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'bfd'), 'per_link'), 'rfc_7130'), True):
                pass
                yield '   bfd per-link rfc-7130\n'
            else:
                pass
                yield '   bfd per-link\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'dhcp_server_ipv4'), True):
            pass
            yield '   dhcp server ipv4\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'dhcp_server_ipv6'), True):
            pass
            yield '   dhcp server ipv6\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_igmp_host_proxy'), 'enabled'), True):
            pass
            l_1_host_proxy_cli = 'ip igmp host-proxy'
            _loop_vars['host_proxy_cli'] = l_1_host_proxy_cli
            yield '   '
            yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
            yield '\n'
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_igmp_host_proxy'), 'groups')):
                pass
                for l_2_proxy_group in environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_igmp_host_proxy'), 'groups'):
                    _loop_vars = {}
                    pass
                    if (t_8(environment.getattr(l_2_proxy_group, 'exclude')) or t_8(environment.getattr(l_2_proxy_group, 'include'))):
                        pass
                        if t_8(environment.getattr(l_2_proxy_group, 'include')):
                            pass
                            for l_3_include_source in environment.getattr(l_2_proxy_group, 'include'):
                                _loop_vars = {}
                                pass
                                yield '   '
                                yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                                yield ' '
                                yield str(environment.getattr(l_2_proxy_group, 'group'))
                                yield ' include '
                                yield str(environment.getattr(l_3_include_source, 'source'))
                                yield '\n'
                            l_3_include_source = missing
                        if t_8(environment.getattr(l_2_proxy_group, 'exclude')):
                            pass
                            for l_3_exclude_source in environment.getattr(l_2_proxy_group, 'exclude'):
                                _loop_vars = {}
                                pass
                                yield '   '
                                yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                                yield ' '
                                yield str(environment.getattr(l_2_proxy_group, 'group'))
                                yield ' exclude '
                                yield str(environment.getattr(l_3_exclude_source, 'source'))
                                yield '\n'
                            l_3_exclude_source = missing
                    elif t_8(environment.getattr(l_2_proxy_group, 'group')):
                        pass
                        yield '   '
                        yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                        yield ' '
                        yield str(environment.getattr(l_2_proxy_group, 'group'))
                        yield '\n'
                l_2_proxy_group = missing
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_igmp_host_proxy'), 'access_lists')):
                pass
                for l_2_access_list in environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_igmp_host_proxy'), 'access_lists'):
                    _loop_vars = {}
                    pass
                    yield '   '
                    yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                    yield ' access-list '
                    yield str(environment.getattr(l_2_access_list, 'name'))
                    yield '\n'
                l_2_access_list = missing
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_igmp_host_proxy'), 'report_interval')):
                pass
                yield '   '
                yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                yield ' report-interval '
                yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_igmp_host_proxy'), 'report_interval'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_igmp_host_proxy'), 'version')):
                pass
                yield '   '
                yield str((undefined(name='host_proxy_cli') if l_1_host_proxy_cli is missing else l_1_host_proxy_cli))
                yield ' version '
                yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_igmp_host_proxy'), 'version'))
                yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ipv6_enable'), True):
            pass
            yield '   ipv6 enable\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ipv6_address')):
            pass
            yield '   ipv6 address '
            yield str(environment.getattr(l_1_port_channel_interface, 'ipv6_address'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ipv6_address_link_local')):
            pass
            yield '   ipv6 address '
            yield str(environment.getattr(l_1_port_channel_interface, 'ipv6_address_link_local'))
            yield ' link-local\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ipv6_nd_ra_disabled'), True):
            pass
            yield '   ipv6 nd ra disabled\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ipv6_nd_managed_config_flag'), True):
            pass
            yield '   ipv6 nd managed-config-flag\n'
        for l_2_ipv6_nd_prefix in t_3(environment.getattr(l_1_port_channel_interface, 'ipv6_nd_prefixes'), 'ipv6_prefix'):
            l_2_ipv6_nd_prefix_cli = missing
            _loop_vars = {}
            pass
            l_2_ipv6_nd_prefix_cli = str_join(('ipv6 nd prefix ', environment.getattr(l_2_ipv6_nd_prefix, 'ipv6_prefix'), ))
            _loop_vars['ipv6_nd_prefix_cli'] = l_2_ipv6_nd_prefix_cli
            if t_8(environment.getattr(l_2_ipv6_nd_prefix, 'valid_lifetime')):
                pass
                l_2_ipv6_nd_prefix_cli = str_join(((undefined(name='ipv6_nd_prefix_cli') if l_2_ipv6_nd_prefix_cli is missing else l_2_ipv6_nd_prefix_cli), ' ', environment.getattr(l_2_ipv6_nd_prefix, 'valid_lifetime'), ))
                _loop_vars['ipv6_nd_prefix_cli'] = l_2_ipv6_nd_prefix_cli
            if t_8(environment.getattr(l_2_ipv6_nd_prefix, 'preferred_lifetime')):
                pass
                l_2_ipv6_nd_prefix_cli = str_join(((undefined(name='ipv6_nd_prefix_cli') if l_2_ipv6_nd_prefix_cli is missing else l_2_ipv6_nd_prefix_cli), ' ', environment.getattr(l_2_ipv6_nd_prefix, 'preferred_lifetime'), ))
                _loop_vars['ipv6_nd_prefix_cli'] = l_2_ipv6_nd_prefix_cli
            if t_8(environment.getattr(l_2_ipv6_nd_prefix, 'no_autoconfig_flag'), True):
                pass
                l_2_ipv6_nd_prefix_cli = str_join(((undefined(name='ipv6_nd_prefix_cli') if l_2_ipv6_nd_prefix_cli is missing else l_2_ipv6_nd_prefix_cli), ' no-autoconfig', ))
                _loop_vars['ipv6_nd_prefix_cli'] = l_2_ipv6_nd_prefix_cli
            yield '   '
            yield str((undefined(name='ipv6_nd_prefix_cli') if l_2_ipv6_nd_prefix_cli is missing else l_2_ipv6_nd_prefix_cli))
            yield '\n'
        l_2_ipv6_nd_prefix = l_2_ipv6_nd_prefix_cli = missing
        if t_8(environment.getattr(l_1_port_channel_interface, 'access_group_in')):
            pass
            yield '   ip access-group '
            yield str(environment.getattr(l_1_port_channel_interface, 'access_group_in'))
            yield ' in\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'access_group_out')):
            pass
            yield '   ip access-group '
            yield str(environment.getattr(l_1_port_channel_interface, 'access_group_out'))
            yield ' out\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ipv6_access_group_in')):
            pass
            yield '   ipv6 access-group '
            yield str(environment.getattr(l_1_port_channel_interface, 'ipv6_access_group_in'))
            yield ' in\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ipv6_access_group_out')):
            pass
            yield '   ipv6 access-group '
            yield str(environment.getattr(l_1_port_channel_interface, 'ipv6_access_group_out'))
            yield ' out\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'mac_access_group_in')):
            pass
            yield '   mac access-group '
            yield str(environment.getattr(l_1_port_channel_interface, 'mac_access_group_in'))
            yield ' in\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'mac_access_group_out')):
            pass
            yield '   mac access-group '
            yield str(environment.getattr(l_1_port_channel_interface, 'mac_access_group_out'))
            yield ' out\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'min_links')):
            pass
            yield '   port-channel min-links '
            yield str(environment.getattr(l_1_port_channel_interface, 'min_links'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'lacp_fallback_mode')):
            pass
            yield '   port-channel lacp fallback '
            yield str(environment.getattr(l_1_port_channel_interface, 'lacp_fallback_mode'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'lacp_fallback_timeout')):
            pass
            yield '   port-channel lacp fallback timeout '
            yield str(environment.getattr(l_1_port_channel_interface, 'lacp_fallback_timeout'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'l2_mtu')):
            pass
            yield '   l2 mtu '
            yield str(environment.getattr(l_1_port_channel_interface, 'l2_mtu'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'l2_mru')):
            pass
            yield '   l2 mru '
            yield str(environment.getattr(l_1_port_channel_interface, 'l2_mru'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'lacp_id')):
            pass
            yield '   lacp system-id '
            yield str(environment.getattr(l_1_port_channel_interface, 'lacp_id'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'mpls'), 'ldp'), 'igp_sync'), True):
            pass
            yield '   mpls ldp igp sync\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'mpls'), 'ldp'), 'interface'), True):
            pass
            yield '   mpls ldp interface\n'
        elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'mpls'), 'ldp'), 'interface'), False):
            pass
            yield '   no mpls ldp interface\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'mlag')):
            pass
            yield '   mlag '
            yield str(environment.getattr(l_1_port_channel_interface, 'mlag'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'mpls'), 'ip'), True):
            pass
            yield '   mpls ip\n'
        elif t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'mpls'), 'ip'), False):
            pass
            yield '   no mpls ip\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ip_nat')):
            pass
            l_1_interface_ip_nat = environment.getattr(l_1_port_channel_interface, 'ip_nat')
            _loop_vars['interface_ip_nat'] = l_1_interface_ip_nat
            template = environment.get_template('eos/interface-ip-nat.j2', 'eos/port-channel-interfaces.j2')
            gen = template.root_render_func(template.new_context(context.get_all(), True, {'backup_link_cli': l_1_backup_link_cli, 'both_key_ids': l_1_both_key_ids, 'client_encapsulation': l_1_client_encapsulation, 'dfe_algo_cli': l_1_dfe_algo_cli, 'dfe_hold_time_cli': l_1_dfe_hold_time_cli, 'encapsulation_cli': l_1_encapsulation_cli, 'encapsulation_dot1q_cli': l_1_encapsulation_dot1q_cli, 'host_proxy_cli': l_1_host_proxy_cli, 'interface_ip_nat': l_1_interface_ip_nat, 'isis_auth_cli': l_1_isis_auth_cli, 'network_encapsulation': l_1_network_encapsulation, 'network_flag': l_1_network_flag, 'port_channel_interface': l_1_port_channel_interface, 'sorted_vlans_cli': l_1_sorted_vlans_cli, 'tap_identity_cli': l_1_tap_identity_cli, 'tap_mac_address_cli': l_1_tap_mac_address_cli, 'tap_truncation_cli': l_1_tap_truncation_cli, 'tool_groups': l_1_tool_groups}))
            try:
                for event in gen:
                    yield event
            finally: gen.close()
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_nat'), 'service_profile')):
                pass
                yield '   ip nat service-profile '
                yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ip_nat'), 'service_profile'))
                yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ntp_serve')):
            pass
            if environment.getattr(l_1_port_channel_interface, 'ntp_serve'):
                pass
                yield '   ntp serve\n'
            else:
                pass
                yield '   no ntp serve\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ospf_cost')):
            pass
            yield '   ip ospf cost '
            yield str(environment.getattr(l_1_port_channel_interface, 'ospf_cost'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ospf_network_point_to_point'), True):
            pass
            yield '   ip ospf network point-to-point\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ospf_authentication'), 'simple'):
            pass
            yield '   ip ospf authentication\n'
        elif t_8(environment.getattr(l_1_port_channel_interface, 'ospf_authentication'), 'message-digest'):
            pass
            yield '   ip ospf authentication message-digest\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ospf_authentication_key')):
            pass
            yield '   ip ospf authentication-key 7 '
            yield str(t_2(environment.getattr(l_1_port_channel_interface, 'ospf_authentication_key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'ospf_area')):
            pass
            yield '   ip ospf area '
            yield str(environment.getattr(l_1_port_channel_interface, 'ospf_area'))
            yield '\n'
        for l_2_ospf_message_digest_key in t_3(environment.getattr(l_1_port_channel_interface, 'ospf_message_digest_keys'), 'id'):
            _loop_vars = {}
            pass
            if (t_8(environment.getattr(l_2_ospf_message_digest_key, 'hash_algorithm')) and t_8(environment.getattr(l_2_ospf_message_digest_key, 'key'))):
                pass
                yield '   ip ospf message-digest-key '
                yield str(environment.getattr(l_2_ospf_message_digest_key, 'id'))
                yield ' '
                yield str(environment.getattr(l_2_ospf_message_digest_key, 'hash_algorithm'))
                yield ' 7 '
                yield str(t_2(environment.getattr(l_2_ospf_message_digest_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                yield '\n'
        l_2_ospf_message_digest_key = missing
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'service_policy'), 'pbr'), 'input')):
            pass
            yield '   service-policy type pbr input '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'service_policy'), 'pbr'), 'input'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'sparse_mode'), True):
            pass
            yield '   pim ipv4 sparse-mode\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'bidirectional'), True):
            pass
            yield '   pim ipv4 bidirectional\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'border_router'), True):
            pass
            yield '   pim ipv4 border-router\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'hello'), 'interval')):
            pass
            yield '   pim ipv4 hello interval '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'hello'), 'interval'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'hello'), 'count')):
            pass
            yield '   pim ipv4 hello count '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'hello'), 'count'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'dr_priority')):
            pass
            yield '   pim ipv4 dr-priority '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'dr_priority'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'neighbor_filter')):
            pass
            yield '   pim ipv4 neighbor filter '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'neighbor_filter'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'pim'), 'ipv4'), 'bfd'), True):
            pass
            yield '   pim ipv4 bfd\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security')):
            pass
            if (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'enabled'), True) or t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'violation'), 'mode'), 'shutdown')):
                pass
                yield '   switchport port-security\n'
            elif t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'violation'), 'mode'), 'protect'):
                pass
                if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'violation'), 'protect_log'), True):
                    pass
                    yield '   switchport port-security violation protect log\n'
                else:
                    pass
                    yield '   switchport port-security violation protect\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'mac_address_maximum'), 'disabled'), True):
                pass
                yield '   switchport port-security mac-address maximum disabled\n'
            elif t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'mac_address_maximum'), 'disabled'), False):
                pass
                yield '   no switchport port-security mac-address maximum disabled\n'
            elif t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'mac_address_maximum'), 'limit')):
                pass
                yield '   switchport port-security mac-address maximum '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'mac_address_maximum'), 'limit'))
                yield '\n'
            if (not t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'violation'), 'mode'), 'protect')):
                pass
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'vlans')):
                    pass
                    l_1_sorted_vlans_cli = []
                    _loop_vars['sorted_vlans_cli'] = l_1_sorted_vlans_cli
                    for l_2_vlan in environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'vlans'):
                        _loop_vars = {}
                        pass
                        if (t_8(environment.getattr(l_2_vlan, 'range')) and t_8(environment.getattr(l_2_vlan, 'mac_address_maximum'))):
                            pass
                            for l_3_id in t_4(environment.getattr(l_2_vlan, 'range')):
                                l_3_port_sec_cli = missing
                                _loop_vars = {}
                                pass
                                l_3_port_sec_cli = str_join(('switchport port-security vlan ', l_3_id, ' mac-address maximum ', environment.getattr(l_2_vlan, 'mac_address_maximum'), ))
                                _loop_vars['port_sec_cli'] = l_3_port_sec_cli
                                context.call(environment.getattr((undefined(name='sorted_vlans_cli') if l_1_sorted_vlans_cli is missing else l_1_sorted_vlans_cli), 'append'), (undefined(name='port_sec_cli') if l_3_port_sec_cli is missing else l_3_port_sec_cli), _loop_vars=_loop_vars)
                            l_3_id = l_3_port_sec_cli = missing
                    l_2_vlan = missing
                    for l_2_cli in t_3((undefined(name='sorted_vlans_cli') if l_1_sorted_vlans_cli is missing else l_1_sorted_vlans_cli)):
                        _loop_vars = {}
                        pass
                        yield '   '
                        yield str(l_2_cli)
                        yield '\n'
                    l_2_cli = missing
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'vlan_default_mac_address_maximum')):
                    pass
                    yield '   switchport port-security vlan default mac-address maximum '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'port_security'), 'vlan_default_mac_address_maximum'))
                    yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'enable'), True):
            pass
            yield '   ptp enable\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'mpass'), True):
            pass
            yield '   ptp mpass\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'announce'), 'interval')):
            pass
            yield '   ptp announce interval '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'announce'), 'interval'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'announce'), 'timeout')):
            pass
            yield '   ptp announce timeout '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'announce'), 'timeout'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'delay_mechanism')):
            pass
            yield '   ptp delay-mechanism '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'delay_mechanism'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'delay_req')):
            pass
            yield '   ptp delay-req interval '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'delay_req'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'profile'), 'g8275_1'), 'destination_mac_address')):
            pass
            yield '   ptp profile g8275.1 destination mac-address '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'profile'), 'g8275_1'), 'destination_mac_address'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'role')):
            pass
            yield '   ptp role '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'role'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'sync_message'), 'interval')):
            pass
            yield '   ptp sync-message interval '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'sync_message'), 'interval'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'transport')):
            pass
            yield '   ptp transport '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'transport'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'vlan')):
            pass
            yield '   ptp vlan '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'ptp'), 'vlan'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'service_policy'), 'qos'), 'input')):
            pass
            yield '   service-policy type qos input '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'service_policy'), 'qos'), 'input'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'service_profile')):
            pass
            yield '   service-profile '
            yield str(environment.getattr(l_1_port_channel_interface, 'service_profile'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'qos'), 'trust')):
            pass
            if (environment.getattr(environment.getattr(l_1_port_channel_interface, 'qos'), 'trust') == 'disabled'):
                pass
                yield '   no qos trust\n'
            else:
                pass
                yield '   qos trust '
                yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'qos'), 'trust'))
                yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'qos'), 'cos')):
            pass
            yield '   qos cos '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'qos'), 'cos'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'qos'), 'dscp')):
            pass
            yield '   qos dscp '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'qos'), 'dscp'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'shape'), 'rate')):
            pass
            yield '   shape rate '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'shape'), 'rate'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'sflow')):
            pass
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'sflow'), 'enable'), True):
                pass
                yield '   sflow enable\n'
            elif t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'sflow'), 'enable'), False):
                pass
                yield '   no sflow enable\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'sflow'), 'egress'), 'enable'), True):
                pass
                yield '   sflow egress enable\n'
            elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'sflow'), 'egress'), 'enable'), False):
                pass
                yield '   no sflow egress enable\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'sflow'), 'egress'), 'unmodified_enable'), True):
                pass
                yield '   sflow egress unmodified enable\n'
            elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'sflow'), 'egress'), 'unmodified_enable'), False):
                pass
                yield '   no sflow egress unmodified enable\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'isis_enable')):
            pass
            yield '   isis enable '
            yield str(environment.getattr(l_1_port_channel_interface, 'isis_enable'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'isis_bfd'), True):
            pass
            yield '   isis bfd\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'isis_circuit_type')):
            pass
            yield '   isis circuit-type '
            yield str(environment.getattr(l_1_port_channel_interface, 'isis_circuit_type'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'isis_metric')):
            pass
            yield '   isis metric '
            yield str(environment.getattr(l_1_port_channel_interface, 'isis_metric'))
            yield '\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'isis_passive'), True):
            pass
            yield '   isis passive\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'isis_hello_padding'), False):
            pass
            yield '   no isis hello padding\n'
        elif t_8(environment.getattr(l_1_port_channel_interface, 'isis_hello_padding'), True):
            pass
            yield '   isis hello padding\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'isis_network_point_to_point'), True):
            pass
            yield '   isis network point-to-point\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'isis_authentication')):
            pass
            if (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'mode')) and (((environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'mode') in ['md5', 'text']) or ((environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'mode') == 'sha') and t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'sha'), 'key_id')))) or ((environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'mode') == 'shared-secret') and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'shared_secret'))))):
                pass
                l_1_isis_auth_cli = str_join(('isis authentication mode ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'mode'), ))
                _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                if (environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'mode') == 'sha'):
                    pass
                    l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' key-id ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'sha'), 'key_id'), ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                elif (environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'mode') == 'shared-secret'):
                    pass
                    l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' profile ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'shared_secret'), 'profile'), ' algorithm ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'shared_secret'), 'algorithm'), ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'rx_disabled'), True):
                    pass
                    l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' rx-disabled', ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                yield '   '
                yield str((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli))
                yield '\n'
            else:
                pass
                if (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode')) and (((environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode') in ['md5', 'text']) or ((environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode') == 'sha') and t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'sha'), 'key_id')))) or ((environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode') == 'shared-secret') and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'shared_secret'))))):
                    pass
                    l_1_isis_auth_cli = str_join(('isis authentication mode ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode'), ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    if (environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode') == 'sha'):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' key-id ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'sha'), 'key_id'), ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    elif (environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode') == 'shared-secret'):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' profile ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'shared_secret'), 'profile'), ' algorithm ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'shared_secret'), 'algorithm'), ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'rx_disabled'), True):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' rx-disabled', ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    yield '   '
                    yield str((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli))
                    yield ' level-1\n'
                if (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode')) and (((environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode') in ['md5', 'text']) or ((environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode') == 'sha') and t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'sha'), 'key_id')))) or ((environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode') == 'shared-secret') and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'shared_secret'))))):
                    pass
                    l_1_isis_auth_cli = str_join(('isis authentication mode ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode'), ))
                    _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    if (environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode') == 'sha'):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' key-id ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'sha'), 'key_id'), ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    elif (environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode') == 'shared-secret'):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' profile ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'shared_secret'), 'profile'), ' algorithm ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'shared_secret'), 'algorithm'), ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'rx_disabled'), True):
                        pass
                        l_1_isis_auth_cli = str_join(((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli), ' rx-disabled', ))
                        _loop_vars['isis_auth_cli'] = l_1_isis_auth_cli
                    yield '   '
                    yield str((undefined(name='isis_auth_cli') if l_1_isis_auth_cli is missing else l_1_isis_auth_cli))
                    yield ' level-2\n'
            l_1_both_key_ids = []
            _loop_vars['both_key_ids'] = l_1_both_key_ids
            for l_2_auth_key in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'key_ids'), 'id'):
                _loop_vars = {}
                pass
                context.call(environment.getattr((undefined(name='both_key_ids') if l_1_both_key_ids is missing else l_1_both_key_ids), 'append'), environment.getattr(l_2_auth_key, 'id'), _loop_vars=_loop_vars)
                if t_8(environment.getattr(l_2_auth_key, 'rfc_5310'), True):
                    pass
                    yield '   isis authentication key-id '
                    yield str(environment.getattr(l_2_auth_key, 'id'))
                    yield ' algorithm '
                    yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                    yield ' rfc-5310 key '
                    yield str(environment.getattr(l_2_auth_key, 'key_type'))
                    yield ' '
                    yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                    yield '\n'
                else:
                    pass
                    yield '   isis authentication key-id '
                    yield str(environment.getattr(l_2_auth_key, 'id'))
                    yield ' algorithm '
                    yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                    yield ' key '
                    yield str(environment.getattr(l_2_auth_key, 'key_type'))
                    yield ' '
                    yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                    yield '\n'
            l_2_auth_key = missing
            for l_2_auth_key in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'key_ids'), 'id'):
                _loop_vars = {}
                pass
                if (environment.getattr(l_2_auth_key, 'id') not in (undefined(name='both_key_ids') if l_1_both_key_ids is missing else l_1_both_key_ids)):
                    pass
                    if t_8(environment.getattr(l_2_auth_key, 'rfc_5310'), True):
                        pass
                        yield '   isis authentication key-id '
                        yield str(environment.getattr(l_2_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                        yield ' rfc-5310 key '
                        yield str(environment.getattr(l_2_auth_key, 'key_type'))
                        yield ' '
                        yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                        yield ' level-1\n'
                    else:
                        pass
                        yield '   isis authentication key-id '
                        yield str(environment.getattr(l_2_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                        yield ' key '
                        yield str(environment.getattr(l_2_auth_key, 'key_type'))
                        yield ' '
                        yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                        yield ' level-1\n'
            l_2_auth_key = missing
            for l_2_auth_key in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'key_ids'), 'id'):
                _loop_vars = {}
                pass
                if (environment.getattr(l_2_auth_key, 'id') not in (undefined(name='both_key_ids') if l_1_both_key_ids is missing else l_1_both_key_ids)):
                    pass
                    if t_8(environment.getattr(l_2_auth_key, 'rfc_5310'), True):
                        pass
                        yield '   isis authentication key-id '
                        yield str(environment.getattr(l_2_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                        yield ' rfc-5310 key '
                        yield str(environment.getattr(l_2_auth_key, 'key_type'))
                        yield ' '
                        yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                        yield ' level-2\n'
                    else:
                        pass
                        yield '   isis authentication key-id '
                        yield str(environment.getattr(l_2_auth_key, 'id'))
                        yield ' algorithm '
                        yield str(environment.getattr(l_2_auth_key, 'algorithm'))
                        yield ' key '
                        yield str(environment.getattr(l_2_auth_key, 'key_type'))
                        yield ' '
                        yield str(t_2(environment.getattr(l_2_auth_key, 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                        yield ' level-2\n'
            l_2_auth_key = missing
            if (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'key_type')) and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'key'))):
                pass
                yield '   isis authentication key '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'key_type'))
                yield ' '
                yield str(t_2(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                yield '\n'
            else:
                pass
                if (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'key_type')) and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'key'))):
                    pass
                    yield '   isis authentication key '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'key_type'))
                    yield ' '
                    yield str(t_2(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                    yield ' level-1\n'
                if (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'key_type')) and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'key'))):
                    pass
                    yield '   isis authentication key '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'key_type'))
                    yield ' '
                    yield str(t_2(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                    yield ' level-2\n'
        for l_2_section in t_3(environment.getattr(l_1_port_channel_interface, 'storm_control')):
            _loop_vars = {}
            pass
            if (l_2_section != 'all'):
                pass
                if t_8(environment.getattr(environment.getitem(environment.getattr(l_1_port_channel_interface, 'storm_control'), l_2_section), 'level')):
                    pass
                    if t_8(environment.getattr(environment.getitem(environment.getattr(l_1_port_channel_interface, 'storm_control'), l_2_section), 'unit'), 'pps'):
                        pass
                        yield '   storm-control '
                        yield str(t_7(context.eval_ctx, l_2_section, '_', '-'))
                        yield ' level pps '
                        yield str(environment.getattr(environment.getitem(environment.getattr(l_1_port_channel_interface, 'storm_control'), l_2_section), 'level'))
                        yield '\n'
                    else:
                        pass
                        yield '   storm-control '
                        yield str(t_7(context.eval_ctx, l_2_section, '_', '-'))
                        yield ' level '
                        yield str(environment.getattr(environment.getitem(environment.getattr(l_1_port_channel_interface, 'storm_control'), l_2_section), 'level'))
                        yield '\n'
        l_2_section = missing
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'storm_control'), 'all')):
            pass
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'storm_control'), 'all'), 'level')):
                pass
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'storm_control'), 'all'), 'unit'), 'pps'):
                    pass
                    yield '   storm-control all level pps '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'storm_control'), 'all'), 'level'))
                    yield '\n'
                else:
                    pass
                    yield '   storm-control all level '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'storm_control'), 'all'), 'level'))
                    yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'logging'), 'event'), 'storm_control_discards'), True):
            pass
            yield '   logging event storm-control discards\n'
        elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'logging'), 'event'), 'storm_control_discards'), False):
            pass
            yield '   no logging event storm-control discards\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'spanning_tree_portfast'), 'edge'):
            pass
            yield '   spanning-tree portfast\n'
        elif t_8(environment.getattr(l_1_port_channel_interface, 'spanning_tree_portfast'), 'network'):
            pass
            yield '   spanning-tree portfast network\n'
        if (t_8(environment.getattr(l_1_port_channel_interface, 'spanning_tree_bpduguard')) and (environment.getattr(l_1_port_channel_interface, 'spanning_tree_bpduguard') in [True, 'True', 'enabled'])):
            pass
            yield '   spanning-tree bpduguard enable\n'
        elif t_8(environment.getattr(l_1_port_channel_interface, 'spanning_tree_bpduguard'), 'disabled'):
            pass
            yield '   spanning-tree bpduguard disable\n'
        if (t_8(environment.getattr(l_1_port_channel_interface, 'spanning_tree_bpdufilter')) and (environment.getattr(l_1_port_channel_interface, 'spanning_tree_bpdufilter') in [True, 'True', 'enabled'])):
            pass
            yield '   spanning-tree bpdufilter enable\n'
        elif t_8(environment.getattr(l_1_port_channel_interface, 'spanning_tree_bpdufilter'), 'disabled'):
            pass
            yield '   spanning-tree bpdufilter disable\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'spanning_tree_guard')):
            pass
            if (environment.getattr(l_1_port_channel_interface, 'spanning_tree_guard') == 'disabled'):
                pass
                yield '   spanning-tree guard none\n'
            else:
                pass
                yield '   spanning-tree guard '
                yield str(environment.getattr(l_1_port_channel_interface, 'spanning_tree_guard'))
                yield '\n'
        if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup_link'), 'interface')):
            pass
            l_1_backup_link_cli = str_join(('switchport backup-link ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup_link'), 'interface'), ))
            _loop_vars['backup_link_cli'] = l_1_backup_link_cli
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup_link'), 'prefer_vlan')):
                pass
                l_1_backup_link_cli = str_join(((undefined(name='backup_link_cli') if l_1_backup_link_cli is missing else l_1_backup_link_cli), ' prefer vlan ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup_link'), 'prefer_vlan'), ))
                _loop_vars['backup_link_cli'] = l_1_backup_link_cli
            yield '   '
            yield str((undefined(name='backup_link_cli') if l_1_backup_link_cli is missing else l_1_backup_link_cli))
            yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'preemption_delay')):
                pass
                yield '   switchport backup preemption-delay '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'preemption_delay'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'mac_move_burst')):
                pass
                yield '   switchport backup mac-move-burst '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'mac_move_burst'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'mac_move_burst_interval')):
                pass
                yield '   switchport backup mac-move-burst-interval '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'mac_move_burst_interval'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'initial_mac_move_delay')):
                pass
                yield '   switchport backup initial-mac-move-delay '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'initial_mac_move_delay'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'dest_macaddr')):
                pass
                yield '   switchport backup dest-macaddr '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'backup'), 'dest_macaddr'))
                yield '\n'
        if (t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap')) or t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'))):
            pass
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'native_vlan')):
                pass
                yield '   switchport tap native vlan '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'native_vlan'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'identity'), 'id')):
                pass
                l_1_tap_identity_cli = str_join(('switchport tap identity ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'identity'), 'id'), ))
                _loop_vars['tap_identity_cli'] = l_1_tap_identity_cli
                if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'identity'), 'inner_vlan')):
                    pass
                    l_1_tap_identity_cli = str_join(((undefined(name='tap_identity_cli') if l_1_tap_identity_cli is missing else l_1_tap_identity_cli), ' inner ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'identity'), 'inner_vlan'), ))
                    _loop_vars['tap_identity_cli'] = l_1_tap_identity_cli
                yield '   '
                yield str((undefined(name='tap_identity_cli') if l_1_tap_identity_cli is missing else l_1_tap_identity_cli))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'mac_address'), 'destination')):
                pass
                l_1_tap_mac_address_cli = str_join(('switchport tap mac-address dest ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'mac_address'), 'destination'), ))
                _loop_vars['tap_mac_address_cli'] = l_1_tap_mac_address_cli
                if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'mac_address'), 'source')):
                    pass
                    l_1_tap_mac_address_cli = str_join(((undefined(name='tap_mac_address_cli') if l_1_tap_mac_address_cli is missing else l_1_tap_mac_address_cli), ' src ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'mac_address'), 'source'), ))
                    _loop_vars['tap_mac_address_cli'] = l_1_tap_mac_address_cli
                yield '   '
                yield str((undefined(name='tap_mac_address_cli') if l_1_tap_mac_address_cli is missing else l_1_tap_mac_address_cli))
                yield '\n'
            if (t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'encapsulation'), 'vxlan_strip'), True) and (not t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'mpls_pop_all'), True))):
                pass
                yield '   switchport tap encapsulation vxlan strip\n'
            for l_2_protocol in t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'encapsulation'), 'gre'), 'protocols'), 'protocol'):
                l_2_tap_encapsulation_cli = resolve('tap_encapsulation_cli')
                _loop_vars = {}
                pass
                if t_8(environment.getattr(l_2_protocol, 'strip'), True):
                    pass
                    l_2_tap_encapsulation_cli = str_join(('switchport tap encapsulation gre protocol ', environment.getattr(l_2_protocol, 'protocol'), ))
                    _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    if t_8(environment.getattr(l_2_protocol, 'feature_header_length')):
                        pass
                        l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' feature header length ', environment.getattr(l_2_protocol, 'feature_header_length'), ))
                        _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' strip', ))
                    _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    if t_8(environment.getattr(l_2_protocol, 're_encapsulation_ethernet_header'), True):
                        pass
                        l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' re-encapsulation ethernet', ))
                        _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    yield '   '
                    yield str((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli))
                    yield '\n'
            l_2_protocol = l_2_tap_encapsulation_cli = missing
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'encapsulation'), 'gre'), 'strip'), True):
                pass
                yield '   switchport tap encapsulation gre strip\n'
            for l_2_destination in t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'encapsulation'), 'gre'), 'destinations'), 'destination'):
                l_2_tap_encapsulation_cli = missing
                _loop_vars = {}
                pass
                l_2_tap_encapsulation_cli = str_join(('switchport tap encapsulation gre destination ', environment.getattr(l_2_destination, 'destination'), ))
                _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                if t_8(environment.getattr(l_2_destination, 'source')):
                    pass
                    l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' source ', environment.getattr(l_2_destination, 'source'), ))
                    _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                for l_3_destination_protocol in t_3(environment.getattr(l_2_destination, 'protocols'), 'protocol'):
                    l_3_tap_encapsulation_protocol_cli = resolve('tap_encapsulation_protocol_cli')
                    _loop_vars = {}
                    pass
                    if t_8(environment.getattr(l_3_destination_protocol, 'strip'), True):
                        pass
                        l_3_tap_encapsulation_protocol_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' protocol ', environment.getattr(l_3_destination_protocol, 'protocol'), ))
                        _loop_vars['tap_encapsulation_protocol_cli'] = l_3_tap_encapsulation_protocol_cli
                        if t_8(environment.getattr(l_3_destination_protocol, 'feature_header_length')):
                            pass
                            l_3_tap_encapsulation_protocol_cli = str_join(((undefined(name='tap_encapsulation_protocol_cli') if l_3_tap_encapsulation_protocol_cli is missing else l_3_tap_encapsulation_protocol_cli), ' feature header length ', environment.getattr(l_3_destination_protocol, 'feature_header_length'), ))
                            _loop_vars['tap_encapsulation_protocol_cli'] = l_3_tap_encapsulation_protocol_cli
                        l_3_tap_encapsulation_protocol_cli = str_join(((undefined(name='tap_encapsulation_protocol_cli') if l_3_tap_encapsulation_protocol_cli is missing else l_3_tap_encapsulation_protocol_cli), ' strip', ))
                        _loop_vars['tap_encapsulation_protocol_cli'] = l_3_tap_encapsulation_protocol_cli
                        if t_8(environment.getattr(l_3_destination_protocol, 're_encapsulation_ethernet_header'), True):
                            pass
                            l_3_tap_encapsulation_protocol_cli = str_join(((undefined(name='tap_encapsulation_protocol_cli') if l_3_tap_encapsulation_protocol_cli is missing else l_3_tap_encapsulation_protocol_cli), ' re-encapsulation ethernet', ))
                            _loop_vars['tap_encapsulation_protocol_cli'] = l_3_tap_encapsulation_protocol_cli
                        yield '   '
                        yield str((undefined(name='tap_encapsulation_protocol_cli') if l_3_tap_encapsulation_protocol_cli is missing else l_3_tap_encapsulation_protocol_cli))
                        yield '\n'
                l_3_destination_protocol = l_3_tap_encapsulation_protocol_cli = missing
                if t_8(environment.getattr(l_2_destination, 'strip'), True):
                    pass
                    l_2_tap_encapsulation_cli = str_join(((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli), ' strip', ))
                    _loop_vars['tap_encapsulation_cli'] = l_2_tap_encapsulation_cli
                    yield '   '
                    yield str((undefined(name='tap_encapsulation_cli') if l_2_tap_encapsulation_cli is missing else l_2_tap_encapsulation_cli))
                    yield '\n'
            l_2_destination = l_2_tap_encapsulation_cli = missing
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'mpls_pop_all'), True):
                pass
                yield '   switchport tap mpls pop all\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'mpls_pop_all'), True):
                pass
                yield '   switchport tool mpls pop all\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'encapsulation'), 'vn_tag_strip'), True):
                pass
                yield '   switchport tool encapsulation vn-tag strip\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'encapsulation'), 'dot1br_strip'), True):
                pass
                yield '   switchport tool encapsulation dot1br strip\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'allowed_vlan')):
                pass
                yield '   switchport tap allowed vlan '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'allowed_vlan'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'allowed_vlan')):
                pass
                yield '   switchport tool allowed vlan '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'allowed_vlan'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'identity'), 'tag')):
                pass
                yield '   switchport tool identity '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'identity'), 'tag'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'identity'), 'dot1q_dzgre_source')):
                pass
                yield '   switchport tool identity dot1q source dzgre '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'identity'), 'dot1q_dzgre_source'))
                yield '\n'
            elif t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'identity'), 'qinq_dzgre_source')):
                pass
                yield '   switchport tool identity qinq source dzgre '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'identity'), 'qinq_dzgre_source'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'truncation'), 'enabled'), True):
                pass
                l_1_tap_truncation_cli = 'switchport tap truncation'
                _loop_vars['tap_truncation_cli'] = l_1_tap_truncation_cli
                if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'truncation'), 'size')):
                    pass
                    l_1_tap_truncation_cli = str_join(((undefined(name='tap_truncation_cli') if l_1_tap_truncation_cli is missing else l_1_tap_truncation_cli), ' ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'truncation'), 'size'), ))
                    _loop_vars['tap_truncation_cli'] = l_1_tap_truncation_cli
                yield '   '
                yield str((undefined(name='tap_truncation_cli') if l_1_tap_truncation_cli is missing else l_1_tap_truncation_cli))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'default'), 'groups')):
                pass
                yield '   switchport tap default group '
                yield str(t_6(context.eval_ctx, t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'default'), 'groups')), ' group '))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'default'), 'nexthop_groups')):
                pass
                yield '   switchport tap default nexthop-group '
                yield str(t_6(context.eval_ctx, t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'default'), 'nexthop_groups')), ' '))
                yield '\n'
            for l_2_interface in t_3(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tap'), 'default'), 'interfaces')):
                _loop_vars = {}
                pass
                yield '   switchport tap default interface '
                yield str(l_2_interface)
                yield '\n'
            l_2_interface = missing
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'groups')):
                pass
                l_1_tool_groups = t_6(context.eval_ctx, t_3(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'groups')), ' ')
                _loop_vars['tool_groups'] = l_1_tool_groups
                yield '   switchport tool group set '
                yield str((undefined(name='tool_groups') if l_1_tool_groups is missing else l_1_tool_groups))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'dot1q_remove_outer_vlan_tag')):
                pass
                yield '   switchport tool dot1q remove outer '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'tool'), 'dot1q_remove_outer_vlan_tag'))
                yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'enabled'), True):
            pass
            yield '   traffic-engineering\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'bandwidth')):
            pass
            yield '   traffic-engineering bandwidth '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'bandwidth'), 'number'))
            yield ' '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'bandwidth'), 'unit'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'administrative_groups')):
            pass
            yield '   traffic-engineering administrative-group '
            yield str(t_6(context.eval_ctx, environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'administrative_groups'), ','))
            yield '\n'
        for l_2_srlg in t_3(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'srlgs')):
            _loop_vars = {}
            pass
            yield '   traffic-engineering srlg '
            yield str(l_2_srlg)
            yield '\n'
        l_2_srlg = missing
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'metric')):
            pass
            yield '   traffic-engineering metric '
            yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'metric'))
            yield '\n'
        if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'min_delay_static')):
            pass
            yield '   traffic-engineering min-delay static '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'min_delay_static'), 'number'))
            yield ' '
            yield str(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'min_delay_static'), 'unit'))
            yield '\n'
        elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'min_delay_dynamic'), 'twamp_light_fallback')):
            pass
            yield '   traffic-engineering min-delay dynamic twamp-light fallback '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'min_delay_dynamic'), 'twamp_light_fallback'), 'number'))
            yield ' '
            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'min_delay_dynamic'), 'twamp_light_fallback'), 'unit'))
            yield '\n'
        for l_2_link_tracking_group in t_3(environment.getattr(l_1_port_channel_interface, 'link_tracking_groups'), 'name'):
            _loop_vars = {}
            pass
            if (t_8(environment.getattr(l_2_link_tracking_group, 'name')) and t_8(environment.getattr(l_2_link_tracking_group, 'direction'))):
                pass
                yield '   link tracking group '
                yield str(environment.getattr(l_2_link_tracking_group, 'name'))
                yield ' '
                yield str(environment.getattr(l_2_link_tracking_group, 'direction'))
                yield '\n'
        l_2_link_tracking_group = missing
        if (t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'link_tracking'), 'direction')) and t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'link_tracking'), 'groups'))):
            pass
            for l_2_group_name in environment.getattr(environment.getattr(l_1_port_channel_interface, 'link_tracking'), 'groups'):
                _loop_vars = {}
                pass
                yield '   link tracking group '
                yield str(l_2_group_name)
                yield ' '
                yield str(environment.getattr(environment.getattr(l_1_port_channel_interface, 'link_tracking'), 'direction'))
                yield '\n'
            l_2_group_name = missing
        if t_8(environment.getattr(l_1_port_channel_interface, 'vmtracer'), True):
            pass
            yield '   vmtracer vmware-esx\n'
        if t_8(environment.getattr(l_1_port_channel_interface, 'eos_cli')):
            pass
            yield '   '
            yield str(t_5(environment.getattr(l_1_port_channel_interface, 'eos_cli'), 3, False))
            yield '\n'
        for l_2_vrid in t_3(environment.getattr(l_1_port_channel_interface, 'vrrp_ids'), 'id'):
            l_2_delay_cli = resolve('delay_cli')
            l_2_peer_auth_cli = resolve('peer_auth_cli')
            _loop_vars = {}
            pass
            if t_8(environment.getattr(l_2_vrid, 'priority_level')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' priority-level '
                yield str(environment.getattr(l_2_vrid, 'priority_level'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(l_2_vrid, 'advertisement'), 'interval')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' advertisement interval '
                yield str(environment.getattr(environment.getattr(l_2_vrid, 'advertisement'), 'interval'))
                yield '\n'
            if (t_8(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'enabled'), True) and (t_8(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'minimum')) or t_8(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'reload')))):
                pass
                l_2_delay_cli = str_join(('vrrp ', environment.getattr(l_2_vrid, 'id'), ' preempt delay', ))
                _loop_vars['delay_cli'] = l_2_delay_cli
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'minimum')):
                    pass
                    l_2_delay_cli = str_join(((undefined(name='delay_cli') if l_2_delay_cli is missing else l_2_delay_cli), ' minimum ', environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'minimum'), ))
                    _loop_vars['delay_cli'] = l_2_delay_cli
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'reload')):
                    pass
                    l_2_delay_cli = str_join(((undefined(name='delay_cli') if l_2_delay_cli is missing else l_2_delay_cli), ' reload ', environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'delay'), 'reload'), ))
                    _loop_vars['delay_cli'] = l_2_delay_cli
                yield '   '
                yield str((undefined(name='delay_cli') if l_2_delay_cli is missing else l_2_delay_cli))
                yield '\n'
            elif t_8(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'enabled'), False):
                pass
                yield '   no vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' preempt\n'
            if t_8(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'timers'), 'delay'), 'reload')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' timers delay reload '
                yield str(environment.getattr(environment.getattr(environment.getattr(l_2_vrid, 'timers'), 'delay'), 'reload'))
                yield '\n'
            if t_8(environment.getattr(l_2_vrid, 'peer_authentication')):
                pass
                l_2_peer_auth_cli = str_join(('vrrp ', environment.getattr(l_2_vrid, 'id'), ' peer authentication', ))
                _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                if (environment.getattr(environment.getattr(l_2_vrid, 'peer_authentication'), 'mode') == 'ietf-md5'):
                    pass
                    l_2_peer_auth_cli = str_join(((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli), ' ietf-md5 key-string', ))
                    _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                else:
                    pass
                    l_2_peer_auth_cli = str_join(((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli), ' text', ))
                    _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                if t_8(environment.getattr(environment.getattr(l_2_vrid, 'peer_authentication'), 'key_type')):
                    pass
                    l_2_peer_auth_cli = str_join(((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli), ' ', environment.getattr(environment.getattr(l_2_vrid, 'peer_authentication'), 'key_type'), ))
                    _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                l_2_peer_auth_cli = str_join(((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli), ' ', t_2(environment.getattr(environment.getattr(l_2_vrid, 'peer_authentication'), 'key'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)), ))
                _loop_vars['peer_auth_cli'] = l_2_peer_auth_cli
                yield '   '
                yield str((undefined(name='peer_auth_cli') if l_2_peer_auth_cli is missing else l_2_peer_auth_cli))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'address')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' ipv4 '
                yield str(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'address'))
                yield '\n'
            for l_3_secondary_ip in t_3(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'secondary_addresses')):
                _loop_vars = {}
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' ipv4 '
                yield str(l_3_secondary_ip)
                yield ' secondary\n'
            l_3_secondary_ip = missing
            if t_8(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'version')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' ipv4 version '
                yield str(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'version'))
                yield '\n'
            if t_8(environment.getattr(environment.getattr(l_2_vrid, 'ipv6'), 'addresses')):
                pass
                for l_3_ipv6_address in t_3(environment.getattr(environment.getattr(l_2_vrid, 'ipv6'), 'addresses')):
                    _loop_vars = {}
                    pass
                    yield '   vrrp '
                    yield str(environment.getattr(l_2_vrid, 'id'))
                    yield ' ipv6 '
                    yield str(l_3_ipv6_address)
                    yield '\n'
                l_3_ipv6_address = missing
            elif t_8(environment.getattr(environment.getattr(l_2_vrid, 'ipv6'), 'address')):
                pass
                yield '   vrrp '
                yield str(environment.getattr(l_2_vrid, 'id'))
                yield ' ipv6 '
                yield str(environment.getattr(environment.getattr(l_2_vrid, 'ipv6'), 'address'))
                yield '\n'
        l_2_vrid = l_2_delay_cli = l_2_peer_auth_cli = missing
    l_1_port_channel_interface = l_1_encapsulation_dot1q_cli = l_1_client_encapsulation = l_1_network_flag = l_1_encapsulation_cli = l_1_network_encapsulation = l_1_dfe_algo_cli = l_1_dfe_hold_time_cli = l_1_host_proxy_cli = l_1_interface_ip_nat = l_1_hide_passwords = l_1_sorted_vlans_cli = l_1_isis_auth_cli = l_1_both_key_ids = l_1_backup_link_cli = l_1_tap_identity_cli = l_1_tap_mac_address_cli = l_1_tap_truncation_cli = l_1_tool_groups = missing

blocks = {}
debug_info = '7=60&9=82&10=84&11=86&12=90&15=93&16=96&18=98&19=101&21=103&22=106&24=108&25=111&27=113&29=116&32=119&33=122&35=124&37=127&40=130&41=133&43=135&44=138&46=140&47=143&49=145&51=148&52=151&54=153&55=156&57=158&58=161&60=163&63=166&66=169&67=172&69=174&70=177&72=179&73=182&75=184&76=187&78=189&81=192&82=196&84=199&86=202&89=205&90=207&91=209&92=211&94=214&96=216&97=219&99=221&100=223&101=225&102=227&103=229&104=231&105=233&106=235&107=237&109=241&111=243&112=245&113=247&116=249&117=251&119=253&120=255&121=257&122=259&123=261&124=263&125=265&126=267&127=269&129=273&132=275&133=277&134=279&135=281&140=284&143=286&144=289&146=291&147=295&148=297&149=299&150=301&151=303&152=305&153=307&156=309&157=312&159=315&160=317&161=321&162=323&163=325&164=327&165=329&167=331&168=334&171=337&172=339&173=343&174=345&175=347&176=349&177=351&178=353&181=355&182=358&186=361&189=364&190=367&192=369&193=372&195=374&198=377&199=380&201=382&202=385&204=387&205=389&207=392&208=394&209=396&210=398&212=401&214=403&215=405&216=407&217=409&219=412&221=414&223=417&227=420&228=423&230=425&231=428&233=430&234=433&237=435&238=438&240=440&241=443&243=445&245=448&248=451&249=454&251=456&254=459&257=462&258=465&260=467&263=470&264=473&266=475&269=478&271=484&273=487&276=490&277=493&279=495&280=497&286=503&289=506&292=509&293=511&294=514&295=516&296=518&297=521&298=523&299=525&300=529&303=536&304=538&305=542&308=549&309=552&313=557&314=559&315=563&318=568&319=571&321=575&322=578&325=582&328=585&329=588&331=590&332=593&334=595&337=598&340=601&341=605&342=607&343=609&345=611&346=613&348=615&349=617&351=620&353=623&354=626&356=628&357=631&359=633&360=636&362=638&363=641&365=643&366=646&368=648&369=651&371=653&372=656&374=658&375=661&377=663&378=666&380=668&381=671&383=673&384=676&386=678&387=681&389=683&392=686&394=689&397=692&398=695&400=697&402=700&405=703&406=705&407=707&408=713&409=716&412=718&413=720&419=726&420=729&422=731&425=734&427=737&430=740&431=743&433=745&434=748&436=750&437=753&438=756&441=763&442=766&444=768&447=771&450=774&453=777&454=780&456=782&457=785&459=787&460=790&462=792&463=795&465=797&468=800&469=802&471=805&472=807&478=813&480=816&482=819&483=822&485=824&486=826&487=828&488=830&489=833&490=835&491=839&492=841&496=844&497=848&500=851&501=854&505=856&508=859&511=862&512=865&514=867&515=870&517=872&518=875&520=877&521=880&523=882&524=885&526=887&527=890&529=892&530=895&532=897&533=900&535=902&536=905&538=907&539=910&541=912&542=915&544=917&545=919&548=925&551=927&552=930&554=932&555=935&557=937&558=940&560=942&561=944&563=947&566=950&568=953&571=956&573=959&577=962&578=965&580=967&583=970&584=973&586=975&587=978&589=980&592=983&594=986&597=989&600=992&601=994&605=996&606=998&607=1000&608=1002&609=1004&611=1006&612=1008&614=1011&616=1015&620=1017&621=1019&622=1021&623=1023&624=1025&626=1027&627=1029&629=1032&631=1034&635=1036&636=1038&637=1040&638=1042&639=1044&641=1046&642=1048&644=1051&647=1053&648=1055&649=1058&650=1059&651=1062&653=1073&656=1082&657=1085&658=1087&659=1090&661=1101&665=1110&666=1113&667=1115&668=1118&670=1129&674=1138&675=1141&677=1147&678=1150&680=1154&681=1157&685=1161&686=1164&687=1166&688=1168&689=1171&691=1178&696=1183&697=1185&698=1187&699=1190&701=1195&705=1197&707=1200&710=1203&712=1206&715=1209&717=1212&720=1215&722=1218&725=1221&726=1223&729=1229&732=1231&733=1233&734=1235&735=1237&737=1240&738=1242&739=1245&741=1247&742=1250&744=1252&745=1255&747=1257&748=1260&750=1262&751=1265&754=1267&755=1269&756=1272&758=1274&759=1276&760=1278&761=1280&763=1283&765=1285&766=1287&767=1289&768=1291&770=1294&772=1296&775=1299&776=1303&777=1305&778=1307&779=1309&781=1311&782=1313&783=1315&785=1318&788=1321&791=1324&792=1328&793=1330&794=1332&796=1334&797=1338&798=1340&799=1342&800=1344&802=1346&803=1348&804=1350&806=1353&809=1356&810=1358&811=1361&814=1364&817=1367&820=1370&823=1373&826=1376&827=1379&829=1381&830=1384&832=1386&833=1389&835=1391&836=1394&837=1396&838=1399&840=1401&841=1403&842=1405&843=1407&845=1410&847=1412&848=1415&850=1417&851=1420&853=1422&854=1426&856=1429&857=1431&858=1434&860=1436&861=1439&864=1441&867=1444&868=1447&870=1451&871=1454&873=1456&874=1460&876=1463&877=1466&879=1468&880=1471&881=1475&882=1478&884=1482&885=1485&886=1488&889=1493&890=1495&891=1499&894=1504&897=1507&898=1510&900=1512&901=1517&902=1520&904=1524&905=1527&907=1531&910=1533&911=1535&912=1537&914=1539&915=1541&917=1544&918=1546&919=1549&921=1551&922=1554&924=1558&925=1560&926=1562&927=1564&929=1568&931=1570&932=1572&934=1574&935=1577&937=1579&938=1582&940=1586&941=1590&943=1595&944=1598&946=1602&947=1604&948=1608&950=1613&951=1616'