from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'documentation/port-channel-interfaces.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_port_channel_interfaces = resolve('port_channel_interfaces')
    l_0_encapsulation_dot1q_interfaces = resolve('encapsulation_dot1q_interfaces')
    l_0_flexencap_interfaces = resolve('flexencap_interfaces')
    l_0_namespace = resolve('namespace')
    l_0_port_channel_interface_pvlan = resolve('port_channel_interface_pvlan')
    l_0_port_channel_interface_vlan_xlate = resolve('port_channel_interface_vlan_xlate')
    l_0_evpn_es_po_interfaces = resolve('evpn_es_po_interfaces')
    l_0_evpn_dfe_po_interfaces = resolve('evpn_dfe_po_interfaces')
    l_0_evpn_mpls_po_interfaces = resolve('evpn_mpls_po_interfaces')
    l_0_link_tracking_interfaces = resolve('link_tracking_interfaces')
    l_0_port_channel_interface_ipv4 = resolve('port_channel_interface_ipv4')
    l_0_ip_nat_interfaces = resolve('ip_nat_interfaces')
    l_0_port_channel_interface_ipv6 = resolve('port_channel_interface_ipv6')
    l_0_port_channel_interfaces_vrrp_details = resolve('port_channel_interfaces_vrrp_details')
    l_0_port_channel_interfaces_isis = resolve('port_channel_interfaces_isis')
    l_0_port_channel_te_interfaces = resolve('port_channel_te_interfaces')
    try:
        t_1 = environment.filters['arista.avd.default']
    except KeyError:
        @internalcode
        def t_1(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.default' found.")
    try:
        t_2 = environment.filters['arista.avd.list_compress']
    except KeyError:
        @internalcode
        def t_2(*unused):
            raise TemplateRuntimeError("No filter named 'arista.avd.list_compress' found.")
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
        t_5 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_6 = environment.filters['length']
    except KeyError:
        @internalcode
        def t_6(*unused):
            raise TemplateRuntimeError("No filter named 'length' found.")
    try:
        t_7 = environment.filters['map']
    except KeyError:
        @internalcode
        def t_7(*unused):
            raise TemplateRuntimeError("No filter named 'map' found.")
    try:
        t_8 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_8(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    try:
        t_9 = environment.tests['defined']
    except KeyError:
        @internalcode
        def t_9(*unused):
            raise TemplateRuntimeError("No test named 'defined' found.")
    pass
    if t_8((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces)):
        pass
        yield '\n### Port-Channel Interfaces\n\n#### Port-Channel Interfaces Summary\n\n##### L2\n\n| Interface | Description | Mode | VLANs | Native VLAN | Trunk Group | LACP Fallback Timeout | LACP Fallback Mode | MLAG ID | EVPN ESI |\n| --------- | ----------- | ---- | ----- | ----------- | ------------| --------------------- | ------------------ | ------- | -------- |\n'
        for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
            l_1_description = resolve('description')
            l_1_mode = resolve('mode')
            l_1_switchport_vlans = resolve('switchport_vlans')
            l_1_native_vlan = resolve('native_vlan')
            l_1_trunk_groups = resolve('trunk_groups')
            l_1_lacp_fallback_timeout = resolve('lacp_fallback_timeout')
            l_1_lacp_fallback_mode = resolve('lacp_fallback_mode')
            l_1_mlag = resolve('mlag')
            l_1_esi = resolve('esi')
            _loop_vars = {}
            pass
            if ((((((t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'mode')) or t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'access_vlan'))) or t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'allowed_vlan'))) or t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'native_vlan_tag'), True)) or t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'native_vlan'))) or t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'groups'))) or t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'enabled'), True)):
                pass
                l_1_description = t_1(environment.getattr(l_1_port_channel_interface, 'description'), '-')
                _loop_vars['description'] = l_1_description
                l_1_mode = t_1(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'mode'), '-')
                _loop_vars['mode'] = l_1_mode
                if (t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'access_vlan')) or t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'allowed_vlan'))):
                    pass
                    l_1_switchport_vlans = []
                    _loop_vars['switchport_vlans'] = l_1_switchport_vlans
                    if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'access_vlan')):
                        pass
                        context.call(environment.getattr((undefined(name='switchport_vlans') if l_1_switchport_vlans is missing else l_1_switchport_vlans), 'append'), environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'access_vlan'), _loop_vars=_loop_vars)
                    if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'allowed_vlan')):
                        pass
                        context.call(environment.getattr((undefined(name='switchport_vlans') if l_1_switchport_vlans is missing else l_1_switchport_vlans), 'extend'), t_7(context, t_4(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'allowed_vlan')), 'int'), _loop_vars=_loop_vars)
                    if (undefined(name='switchport_vlans') if l_1_switchport_vlans is missing else l_1_switchport_vlans):
                        pass
                        l_1_switchport_vlans = t_2((undefined(name='switchport_vlans') if l_1_switchport_vlans is missing else l_1_switchport_vlans))
                        _loop_vars['switchport_vlans'] = l_1_switchport_vlans
                    else:
                        pass
                        l_1_switchport_vlans = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'allowed_vlan')
                        _loop_vars['switchport_vlans'] = l_1_switchport_vlans
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'native_vlan_tag'), True):
                    pass
                    l_1_native_vlan = 'tag'
                    _loop_vars['native_vlan'] = l_1_native_vlan
                else:
                    pass
                    l_1_native_vlan = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'native_vlan'), '-')
                    _loop_vars['native_vlan'] = l_1_native_vlan
                l_1_trunk_groups = t_5(context.eval_ctx, t_1(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'groups'), ['-']), ', ')
                _loop_vars['trunk_groups'] = l_1_trunk_groups
                l_1_lacp_fallback_timeout = t_1(environment.getattr(l_1_port_channel_interface, 'lacp_fallback_timeout'), '-')
                _loop_vars['lacp_fallback_timeout'] = l_1_lacp_fallback_timeout
                l_1_lacp_fallback_mode = t_1(environment.getattr(l_1_port_channel_interface, 'lacp_fallback_mode'), '-')
                _loop_vars['lacp_fallback_mode'] = l_1_lacp_fallback_mode
                l_1_mlag = t_1(environment.getattr(l_1_port_channel_interface, 'mlag'), '-')
                _loop_vars['mlag'] = l_1_mlag
                l_1_esi = t_1(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'identifier'), '-')
                _loop_vars['esi'] = l_1_esi
                yield '| '
                yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                yield ' | '
                yield str((undefined(name='description') if l_1_description is missing else l_1_description))
                yield ' | '
                yield str((undefined(name='mode') if l_1_mode is missing else l_1_mode))
                yield ' | '
                yield str(t_1((undefined(name='switchport_vlans') if l_1_switchport_vlans is missing else l_1_switchport_vlans), '-'))
                yield ' | '
                yield str((undefined(name='native_vlan') if l_1_native_vlan is missing else l_1_native_vlan))
                yield ' | '
                yield str((undefined(name='trunk_groups') if l_1_trunk_groups is missing else l_1_trunk_groups))
                yield ' | '
                yield str((undefined(name='lacp_fallback_timeout') if l_1_lacp_fallback_timeout is missing else l_1_lacp_fallback_timeout))
                yield ' | '
                yield str((undefined(name='lacp_fallback_mode') if l_1_lacp_fallback_mode is missing else l_1_lacp_fallback_mode))
                yield ' | '
                yield str((undefined(name='mlag') if l_1_mlag is missing else l_1_mlag))
                yield ' | '
                yield str((undefined(name='esi') if l_1_esi is missing else l_1_esi))
                yield ' |\n'
        l_1_port_channel_interface = l_1_description = l_1_mode = l_1_switchport_vlans = l_1_native_vlan = l_1_trunk_groups = l_1_lacp_fallback_timeout = l_1_lacp_fallback_mode = l_1_mlag = l_1_esi = missing
        l_0_encapsulation_dot1q_interfaces = []
        context.vars['encapsulation_dot1q_interfaces'] = l_0_encapsulation_dot1q_interfaces
        context.exported_vars.add('encapsulation_dot1q_interfaces')
        l_0_flexencap_interfaces = []
        context.vars['flexencap_interfaces'] = l_0_flexencap_interfaces
        context.exported_vars.add('flexencap_interfaces')
        for l_1_port_channel_interface in (undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces):
            _loop_vars = {}
            pass
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_dot1q'), 'vlan')):
                pass
                context.call(environment.getattr((undefined(name='encapsulation_dot1q_interfaces') if l_0_encapsulation_dot1q_interfaces is missing else l_0_encapsulation_dot1q_interfaces), 'append'), l_1_port_channel_interface, _loop_vars=_loop_vars)
            elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'encapsulation')):
                pass
                context.call(environment.getattr((undefined(name='flexencap_interfaces') if l_0_flexencap_interfaces is missing else l_0_flexencap_interfaces), 'append'), l_1_port_channel_interface, _loop_vars=_loop_vars)
        l_1_port_channel_interface = missing
        if (t_6((undefined(name='encapsulation_dot1q_interfaces') if l_0_encapsulation_dot1q_interfaces is missing else l_0_encapsulation_dot1q_interfaces)) > 0):
            pass
            yield '\n##### Encapsulation Dot1q\n\n| Interface | Description | Vlan ID | Dot1q VLAN Tag | Dot1q Inner VLAN Tag |\n| --------- | ----------- | ------- | -------------- | -------------------- |\n'
            for l_1_port_channel_interface in t_3((undefined(name='encapsulation_dot1q_interfaces') if l_0_encapsulation_dot1q_interfaces is missing else l_0_encapsulation_dot1q_interfaces), 'name'):
                l_1_description = l_1_vlan_id = l_1_encapsulation_dot1q_vlan = l_1_encapsulation_dot1q_inner_vlan = missing
                _loop_vars = {}
                pass
                l_1_description = t_1(environment.getattr(l_1_port_channel_interface, 'description'), '-')
                _loop_vars['description'] = l_1_description
                l_1_vlan_id = t_1(environment.getattr(l_1_port_channel_interface, 'vlan_id'), '-')
                _loop_vars['vlan_id'] = l_1_vlan_id
                l_1_encapsulation_dot1q_vlan = t_1(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_dot1q'), 'vlan'), '-')
                _loop_vars['encapsulation_dot1q_vlan'] = l_1_encapsulation_dot1q_vlan
                l_1_encapsulation_dot1q_inner_vlan = t_1(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_dot1q'), 'inner_vlan'), '-')
                _loop_vars['encapsulation_dot1q_inner_vlan'] = l_1_encapsulation_dot1q_inner_vlan
                yield '| '
                yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                yield ' | '
                yield str((undefined(name='description') if l_1_description is missing else l_1_description))
                yield ' | '
                yield str((undefined(name='vlan_id') if l_1_vlan_id is missing else l_1_vlan_id))
                yield ' | '
                yield str((undefined(name='encapsulation_dot1q_vlan') if l_1_encapsulation_dot1q_vlan is missing else l_1_encapsulation_dot1q_vlan))
                yield ' | '
                yield str((undefined(name='encapsulation_dot1q_inner_vlan') if l_1_encapsulation_dot1q_inner_vlan is missing else l_1_encapsulation_dot1q_inner_vlan))
                yield ' |\n'
            l_1_port_channel_interface = l_1_description = l_1_vlan_id = l_1_encapsulation_dot1q_vlan = l_1_encapsulation_dot1q_inner_vlan = missing
        if (t_6((undefined(name='flexencap_interfaces') if l_0_flexencap_interfaces is missing else l_0_flexencap_interfaces)) > 0):
            pass
            yield '\n##### Flexible Encapsulation Interfaces\n\n| Interface | Description | Vlan ID | Client Encapsulation | Client Inner Encapsulation | Client VLAN | Client Outer VLAN Tag | Client Inner VLAN Tag | Network Encapsulation | Network Inner Encapsulation | Network VLAN | Network Outer VLAN Tag | Network Inner VLAN Tag |\n| --------- | ----------- | ------- | --------------- | --------------------- | ----------- | --------------------- | --------------------- | ---------------- | ---------------------- | ------------ | ---------------------- | ---------------------- |\n'
            for l_1_port_channel_interface in (undefined(name='flexencap_interfaces') if l_0_flexencap_interfaces is missing else l_0_flexencap_interfaces):
                l_1_client_inner_encapsulation = resolve('client_inner_encapsulation')
                l_1_client_vlan = resolve('client_vlan')
                l_1_client_outer_vlan = resolve('client_outer_vlan')
                l_1_client_inner_vlan = resolve('client_inner_vlan')
                l_1_network_inner_encapsulation = resolve('network_inner_encapsulation')
                l_1_network_vlan = resolve('network_vlan')
                l_1_network_outer_vlan = resolve('network_outer_vlan')
                l_1_network_inner_vlan = resolve('network_inner_vlan')
                l_1_description = l_1_vlan_id = l_1_client_encapsulation = l_1_network_encapsulation = missing
                _loop_vars = {}
                pass
                l_1_description = t_1(environment.getattr(l_1_port_channel_interface, 'description'), '-')
                _loop_vars['description'] = l_1_description
                l_1_vlan_id = t_1(environment.getattr(l_1_port_channel_interface, 'vlan_id'), '-')
                _loop_vars['vlan_id'] = l_1_vlan_id
                l_1_client_encapsulation = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'encapsulation'), '-')
                _loop_vars['client_encapsulation'] = l_1_client_encapsulation
                if ((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation) in ['dot1q', 'dot1ad']):
                    pass
                    l_1_client_inner_encapsulation = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'inner_encapsulation'), '-')
                    _loop_vars['client_inner_encapsulation'] = l_1_client_inner_encapsulation
                    l_1_client_vlan = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'vlan')
                    _loop_vars['client_vlan'] = l_1_client_vlan
                    l_1_client_outer_vlan = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'outer_vlan')
                    _loop_vars['client_outer_vlan'] = l_1_client_outer_vlan
                    l_1_client_inner_vlan = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'client'), 'inner_vlan')
                    _loop_vars['client_inner_vlan'] = l_1_client_inner_vlan
                l_1_network_encapsulation = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'encapsulation'), '-')
                _loop_vars['network_encapsulation'] = l_1_network_encapsulation
                if ((undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation) in ['dot1q', 'dot1ad']):
                    pass
                    l_1_network_inner_encapsulation = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'inner_encapsulation'), '-')
                    _loop_vars['network_inner_encapsulation'] = l_1_network_inner_encapsulation
                    l_1_network_vlan = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'vlan')
                    _loop_vars['network_vlan'] = l_1_network_vlan
                    l_1_network_outer_vlan = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'outer_vlan')
                    _loop_vars['network_outer_vlan'] = l_1_network_outer_vlan
                    l_1_network_inner_vlan = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'encapsulation_vlan'), 'network'), 'inner_vlan')
                    _loop_vars['network_inner_vlan'] = l_1_network_inner_vlan
                yield '| '
                yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                yield ' | '
                yield str((undefined(name='description') if l_1_description is missing else l_1_description))
                yield ' | '
                yield str((undefined(name='vlan_id') if l_1_vlan_id is missing else l_1_vlan_id))
                yield ' | '
                yield str((undefined(name='client_encapsulation') if l_1_client_encapsulation is missing else l_1_client_encapsulation))
                yield ' | '
                yield str(t_1((undefined(name='client_inner_encapsulation') if l_1_client_inner_encapsulation is missing else l_1_client_inner_encapsulation), '-'))
                yield ' | '
                yield str(t_1((undefined(name='client_vlan') if l_1_client_vlan is missing else l_1_client_vlan), '-'))
                yield ' | '
                yield str(t_1((undefined(name='client_outer_vlan') if l_1_client_outer_vlan is missing else l_1_client_outer_vlan), '-'))
                yield ' | '
                yield str(t_1((undefined(name='client_inner_vlan') if l_1_client_inner_vlan is missing else l_1_client_inner_vlan), '-'))
                yield ' | '
                yield str((undefined(name='network_encapsulation') if l_1_network_encapsulation is missing else l_1_network_encapsulation))
                yield ' | '
                yield str(t_1((undefined(name='network_inner_encapsulation') if l_1_network_inner_encapsulation is missing else l_1_network_inner_encapsulation), '-'))
                yield ' | '
                yield str(t_1((undefined(name='network_vlan') if l_1_network_vlan is missing else l_1_network_vlan), '-'))
                yield ' | '
                yield str(t_1((undefined(name='network_outer_vlan') if l_1_network_outer_vlan is missing else l_1_network_outer_vlan), '-'))
                yield ' | '
                yield str(t_1((undefined(name='network_inner_vlan') if l_1_network_inner_vlan is missing else l_1_network_inner_vlan), '-'))
                yield ' |\n'
            l_1_port_channel_interface = l_1_description = l_1_vlan_id = l_1_client_encapsulation = l_1_client_inner_encapsulation = l_1_client_vlan = l_1_client_outer_vlan = l_1_client_inner_vlan = l_1_network_encapsulation = l_1_network_inner_encapsulation = l_1_network_vlan = l_1_network_outer_vlan = l_1_network_inner_vlan = missing
        l_0_port_channel_interface_pvlan = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace))
        context.vars['port_channel_interface_pvlan'] = l_0_port_channel_interface_pvlan
        context.exported_vars.add('port_channel_interface_pvlan')
        if not isinstance(l_0_port_channel_interface_pvlan, Namespace):
            raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
        l_0_port_channel_interface_pvlan['configured'] = False
        for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
            _loop_vars = {}
            pass
            if (t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'pvlan_mapping')) or t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'private_vlan_secondary'))):
                pass
                if not isinstance(l_0_port_channel_interface_pvlan, Namespace):
                    raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                l_0_port_channel_interface_pvlan['configured'] = True
                break
        l_1_port_channel_interface = missing
        if environment.getattr((undefined(name='port_channel_interface_pvlan') if l_0_port_channel_interface_pvlan is missing else l_0_port_channel_interface_pvlan), 'configured'):
            pass
            yield '\n##### Private VLAN\n\n| Interface | PVLAN Mapping | Secondary Trunk |\n| --------- | ------------- | ----------------|\n'
            for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
                l_1_row_pvlan_mapping = l_1_row_trunk_private_vlan_secondary = missing
                _loop_vars = {}
                pass
                l_1_row_pvlan_mapping = t_1(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'pvlan_mapping'), '-')
                _loop_vars['row_pvlan_mapping'] = l_1_row_pvlan_mapping
                l_1_row_trunk_private_vlan_secondary = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'trunk'), 'private_vlan_secondary'), '-')
                _loop_vars['row_trunk_private_vlan_secondary'] = l_1_row_trunk_private_vlan_secondary
                if (((undefined(name='row_pvlan_mapping') if l_1_row_pvlan_mapping is missing else l_1_row_pvlan_mapping) != '-') or ((undefined(name='row_trunk_private_vlan_secondary') if l_1_row_trunk_private_vlan_secondary is missing else l_1_row_trunk_private_vlan_secondary) != '-')):
                    pass
                    yield '| '
                    yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                    yield ' | '
                    yield str((undefined(name='row_pvlan_mapping') if l_1_row_pvlan_mapping is missing else l_1_row_pvlan_mapping))
                    yield ' | '
                    yield str((undefined(name='row_trunk_private_vlan_secondary') if l_1_row_trunk_private_vlan_secondary is missing else l_1_row_trunk_private_vlan_secondary))
                    yield ' |\n'
            l_1_port_channel_interface = l_1_row_pvlan_mapping = l_1_row_trunk_private_vlan_secondary = missing
        l_0_port_channel_interface_vlan_xlate = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace))
        context.vars['port_channel_interface_vlan_xlate'] = l_0_port_channel_interface_vlan_xlate
        context.exported_vars.add('port_channel_interface_vlan_xlate')
        if not isinstance(l_0_port_channel_interface_vlan_xlate, Namespace):
            raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
        l_0_port_channel_interface_vlan_xlate['configured'] = False
        for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
            _loop_vars = {}
            pass
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations')):
                pass
                if not isinstance(l_0_port_channel_interface_vlan_xlate, Namespace):
                    raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                l_0_port_channel_interface_vlan_xlate['configured'] = True
                break
        l_1_port_channel_interface = missing
        if environment.getattr((undefined(name='port_channel_interface_vlan_xlate') if l_0_port_channel_interface_vlan_xlate is missing else l_0_port_channel_interface_vlan_xlate), 'configured'):
            pass
            yield '\n##### VLAN Translations\n\n| Interface |  Direction | From VLAN ID(s) | To VLAN ID | From Inner VLAN ID | To Inner VLAN ID | Network | Dot1q-tunnel |\n| --------- |  --------- | --------------- | ---------- | ------------------ | ---------------- | ------- | ------------ |\n'
            for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
                _loop_vars = {}
                pass
                if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations')):
                    pass
                    for l_2_vlan_translation in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'direction_both'), 'from'):
                        _loop_vars = {}
                        pass
                        yield '| '
                        yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                        yield ' | both | '
                        yield str(environment.getattr(l_2_vlan_translation, 'from'))
                        yield ' | '
                        yield str(environment.getattr(l_2_vlan_translation, 'to'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_vlan_translation, 'inner_vlan_from'), '-'))
                        yield ' | - | '
                        yield str(t_1(environment.getattr(l_2_vlan_translation, 'network'), '-'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_vlan_translation, 'dot1q_tunnel'), '-'))
                        yield ' |\n'
                    l_2_vlan_translation = missing
                    for l_2_vlan_translation in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'direction_in'), 'from'):
                        _loop_vars = {}
                        pass
                        yield '| '
                        yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                        yield ' | in | '
                        yield str(environment.getattr(l_2_vlan_translation, 'from'))
                        yield ' | '
                        yield str(environment.getattr(l_2_vlan_translation, 'to'))
                        yield ' | - | '
                        yield str(t_1(environment.getattr(l_2_vlan_translation, 'inner_vlan_from'), '-'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_vlan_translation, 'network'), '-'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_vlan_translation, 'dot1q_tunnel'), '-'))
                        yield ' |\n'
                    l_2_vlan_translation = missing
                    for l_2_vlan_translation in t_3(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'switchport'), 'vlan_translations'), 'direction_out'), 'from'):
                        l_2_dot1q_tunnel = resolve('dot1q_tunnel')
                        l_2_to_vlan_id = resolve('to_vlan_id')
                        _loop_vars = {}
                        pass
                        if t_8(environment.getattr(l_2_vlan_translation, 'dot1q_tunnel_to')):
                            pass
                            l_2_dot1q_tunnel = 'True'
                            _loop_vars['dot1q_tunnel'] = l_2_dot1q_tunnel
                            l_2_to_vlan_id = environment.getattr(l_2_vlan_translation, 'dot1q_tunnel_to')
                            _loop_vars['to_vlan_id'] = l_2_to_vlan_id
                        else:
                            pass
                            l_2_to_vlan_id = t_1(environment.getattr(l_2_vlan_translation, 'to'), '-')
                            _loop_vars['to_vlan_id'] = l_2_to_vlan_id
                        yield '| '
                        yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                        yield ' | out | '
                        yield str(environment.getattr(l_2_vlan_translation, 'from'))
                        yield ' | '
                        yield str((undefined(name='to_vlan_id') if l_2_to_vlan_id is missing else l_2_to_vlan_id))
                        yield ' | - | '
                        yield str(t_1(environment.getattr(l_2_vlan_translation, 'inner_vlan_to'), '-'))
                        yield ' | '
                        yield str(t_1(environment.getattr(l_2_vlan_translation, 'network'), '-'))
                        yield ' | '
                        yield str(t_1((undefined(name='dot1q_tunnel') if l_2_dot1q_tunnel is missing else l_2_dot1q_tunnel), '-'))
                        yield ' |\n'
                    l_2_vlan_translation = l_2_dot1q_tunnel = l_2_to_vlan_id = missing
            l_1_port_channel_interface = missing
        l_0_evpn_es_po_interfaces = []
        context.vars['evpn_es_po_interfaces'] = l_0_evpn_es_po_interfaces
        context.exported_vars.add('evpn_es_po_interfaces')
        l_0_evpn_dfe_po_interfaces = []
        context.vars['evpn_dfe_po_interfaces'] = l_0_evpn_dfe_po_interfaces
        context.exported_vars.add('evpn_dfe_po_interfaces')
        l_0_evpn_mpls_po_interfaces = []
        context.vars['evpn_mpls_po_interfaces'] = l_0_evpn_mpls_po_interfaces
        context.exported_vars.add('evpn_mpls_po_interfaces')
        l_0_link_tracking_interfaces = []
        context.vars['link_tracking_interfaces'] = l_0_link_tracking_interfaces
        context.exported_vars.add('link_tracking_interfaces')
        for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
            _loop_vars = {}
            pass
            if t_8(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment')):
                pass
                context.call(environment.getattr((undefined(name='evpn_es_po_interfaces') if l_0_evpn_es_po_interfaces is missing else l_0_evpn_es_po_interfaces), 'append'), l_1_port_channel_interface, _loop_vars=_loop_vars)
                if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election')):
                    pass
                    context.call(environment.getattr((undefined(name='evpn_dfe_po_interfaces') if l_0_evpn_dfe_po_interfaces is missing else l_0_evpn_dfe_po_interfaces), 'append'), l_1_port_channel_interface, _loop_vars=_loop_vars)
                if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'evpn_ethernet_segment'), 'mpls')):
                    pass
                    context.call(environment.getattr((undefined(name='evpn_mpls_po_interfaces') if l_0_evpn_mpls_po_interfaces is missing else l_0_evpn_mpls_po_interfaces), 'append'), l_1_port_channel_interface, _loop_vars=_loop_vars)
            if t_8(environment.getattr(l_1_port_channel_interface, 'link_tracking_groups')):
                pass
                context.call(environment.getattr((undefined(name='link_tracking_interfaces') if l_0_link_tracking_interfaces is missing else l_0_link_tracking_interfaces), 'append'), l_1_port_channel_interface, _loop_vars=_loop_vars)
        l_1_port_channel_interface = missing
        if (t_6((undefined(name='evpn_es_po_interfaces') if l_0_evpn_es_po_interfaces is missing else l_0_evpn_es_po_interfaces)) > 0):
            pass
            yield '\n##### EVPN Multihoming\n\n####### EVPN Multihoming Summary\n\n| Interface | Ethernet Segment Identifier | Multihoming Redundancy Mode | Route Target |\n| --------- | --------------------------- | --------------------------- | ------------ |\n'
            for l_1_evpn_es_po_interface in t_3((undefined(name='evpn_es_po_interfaces') if l_0_evpn_es_po_interfaces is missing else l_0_evpn_es_po_interfaces), 'name'):
                l_1_esi = l_1_redundancy = l_1_rt = missing
                _loop_vars = {}
                pass
                l_1_esi = t_1(environment.getattr(environment.getattr(l_1_evpn_es_po_interface, 'evpn_ethernet_segment'), 'identifier'), environment.getattr(l_1_evpn_es_po_interface, 'esi'), '-')
                _loop_vars['esi'] = l_1_esi
                l_1_redundancy = t_1(environment.getattr(environment.getattr(l_1_evpn_es_po_interface, 'evpn_ethernet_segment'), 'redundancy'), 'all-active')
                _loop_vars['redundancy'] = l_1_redundancy
                l_1_rt = t_1(environment.getattr(environment.getattr(l_1_evpn_es_po_interface, 'evpn_ethernet_segment'), 'route_target'), '-')
                _loop_vars['rt'] = l_1_rt
                yield '| '
                yield str(environment.getattr(l_1_evpn_es_po_interface, 'name'))
                yield ' | '
                yield str((undefined(name='esi') if l_1_esi is missing else l_1_esi))
                yield ' | '
                yield str((undefined(name='redundancy') if l_1_redundancy is missing else l_1_redundancy))
                yield ' | '
                yield str((undefined(name='rt') if l_1_rt is missing else l_1_rt))
                yield ' |\n'
            l_1_evpn_es_po_interface = l_1_esi = l_1_redundancy = l_1_rt = missing
            if (t_6((undefined(name='evpn_dfe_po_interfaces') if l_0_evpn_dfe_po_interfaces is missing else l_0_evpn_dfe_po_interfaces)) > 0):
                pass
                yield '\n####### Designated Forwarder Election Summary\n\n| Interface | Algorithm | Preference Value | Dont Preempt | Hold time | Subsequent Hold Time | Candidate Reachability Required |\n| --------- | --------- | ---------------- | ------------ | --------- | -------------------- | ------------------------------- |\n'
                for l_1_evpn_dfe_po_interface in t_3((undefined(name='evpn_dfe_po_interfaces') if l_0_evpn_dfe_po_interfaces is missing else l_0_evpn_dfe_po_interfaces), 'name'):
                    l_1_df_po_settings = l_1_algorithm = l_1_pref_value = l_1_dont_preempt = l_1_hold_time = l_1_subsequent_hold_time = l_1_candidate_reachability = missing
                    _loop_vars = {}
                    pass
                    l_1_df_po_settings = environment.getattr(environment.getattr(l_1_evpn_dfe_po_interface, 'evpn_ethernet_segment'), 'designated_forwarder_election')
                    _loop_vars['df_po_settings'] = l_1_df_po_settings
                    l_1_algorithm = t_1(environment.getattr((undefined(name='df_po_settings') if l_1_df_po_settings is missing else l_1_df_po_settings), 'algorithm'), 'modulus')
                    _loop_vars['algorithm'] = l_1_algorithm
                    l_1_pref_value = t_1(environment.getattr((undefined(name='df_po_settings') if l_1_df_po_settings is missing else l_1_df_po_settings), 'preference_value'), '-')
                    _loop_vars['pref_value'] = l_1_pref_value
                    l_1_dont_preempt = t_1(environment.getattr((undefined(name='df_po_settings') if l_1_df_po_settings is missing else l_1_df_po_settings), 'dont_preempt'), False)
                    _loop_vars['dont_preempt'] = l_1_dont_preempt
                    l_1_hold_time = t_1(environment.getattr((undefined(name='df_po_settings') if l_1_df_po_settings is missing else l_1_df_po_settings), 'hold_time'), '-')
                    _loop_vars['hold_time'] = l_1_hold_time
                    l_1_subsequent_hold_time = t_1(environment.getattr((undefined(name='df_po_settings') if l_1_df_po_settings is missing else l_1_df_po_settings), 'subsequent_hold_time'), '-')
                    _loop_vars['subsequent_hold_time'] = l_1_subsequent_hold_time
                    l_1_candidate_reachability = t_1(environment.getattr((undefined(name='df_po_settings') if l_1_df_po_settings is missing else l_1_df_po_settings), 'candidate_reachability_required'), False)
                    _loop_vars['candidate_reachability'] = l_1_candidate_reachability
                    yield '| '
                    yield str(environment.getattr(l_1_evpn_dfe_po_interface, 'name'))
                    yield ' | '
                    yield str((undefined(name='algorithm') if l_1_algorithm is missing else l_1_algorithm))
                    yield ' | '
                    yield str((undefined(name='pref_value') if l_1_pref_value is missing else l_1_pref_value))
                    yield ' | '
                    yield str((undefined(name='dont_preempt') if l_1_dont_preempt is missing else l_1_dont_preempt))
                    yield ' | '
                    yield str((undefined(name='hold_time') if l_1_hold_time is missing else l_1_hold_time))
                    yield ' | '
                    yield str((undefined(name='subsequent_hold_time') if l_1_subsequent_hold_time is missing else l_1_subsequent_hold_time))
                    yield ' | '
                    yield str((undefined(name='candidate_reachability') if l_1_candidate_reachability is missing else l_1_candidate_reachability))
                    yield ' |\n'
                l_1_evpn_dfe_po_interface = l_1_df_po_settings = l_1_algorithm = l_1_pref_value = l_1_dont_preempt = l_1_hold_time = l_1_subsequent_hold_time = l_1_candidate_reachability = missing
            if (t_6((undefined(name='evpn_mpls_po_interfaces') if l_0_evpn_mpls_po_interfaces is missing else l_0_evpn_mpls_po_interfaces)) > 0):
                pass
                yield '\n####### EVPN-MPLS summary\n\n| Interface | Shared Index | Tunnel Flood Filter Time |\n| --------- | ------------ | ------------------------ |\n'
                for l_1_evpn_mpls_po_interface in t_3((undefined(name='evpn_mpls_po_interfaces') if l_0_evpn_mpls_po_interfaces is missing else l_0_evpn_mpls_po_interfaces)):
                    l_1_shared_index = l_1_tff_time = missing
                    _loop_vars = {}
                    pass
                    l_1_shared_index = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_evpn_mpls_po_interface, 'evpn_ethernet_segment'), 'mpls'), 'shared_index'), '-')
                    _loop_vars['shared_index'] = l_1_shared_index
                    l_1_tff_time = t_1(environment.getattr(environment.getattr(environment.getattr(l_1_evpn_mpls_po_interface, 'evpn_ethernet_segment'), 'mpls'), 'tunnel_flood_filter_time'), '-')
                    _loop_vars['tff_time'] = l_1_tff_time
                    yield '| '
                    yield str(environment.getattr(l_1_evpn_mpls_po_interface, 'name'))
                    yield ' | '
                    yield str((undefined(name='shared_index') if l_1_shared_index is missing else l_1_shared_index))
                    yield ' | '
                    yield str((undefined(name='tff_time') if l_1_tff_time is missing else l_1_tff_time))
                    yield ' |\n'
                l_1_evpn_mpls_po_interface = l_1_shared_index = l_1_tff_time = missing
        if (t_6((undefined(name='link_tracking_interfaces') if l_0_link_tracking_interfaces is missing else l_0_link_tracking_interfaces)) > 0):
            pass
            yield '\n##### Link Tracking Groups\n\n| Interface | Group Name | Direction |\n| --------- | ---------- | --------- |\n'
            for l_1_link_tracking_interface in t_3((undefined(name='link_tracking_interfaces') if l_0_link_tracking_interfaces is missing else l_0_link_tracking_interfaces), 'name'):
                _loop_vars = {}
                pass
                for l_2_link_tracking_group in t_3(environment.getattr(l_1_link_tracking_interface, 'link_tracking_groups'), 'name'):
                    _loop_vars = {}
                    pass
                    if (t_8(environment.getattr(l_2_link_tracking_group, 'name')) and t_8(environment.getattr(l_2_link_tracking_group, 'direction'))):
                        pass
                        yield '| '
                        yield str(environment.getattr(l_1_link_tracking_interface, 'name'))
                        yield ' | '
                        yield str(environment.getattr(l_2_link_tracking_group, 'name'))
                        yield ' | '
                        yield str(environment.getattr(l_2_link_tracking_group, 'direction'))
                        yield ' |\n'
                l_2_link_tracking_group = missing
                if (t_8(environment.getattr(environment.getattr(l_1_link_tracking_interface, 'link_tracking'), 'direction')) and t_8(environment.getattr(environment.getattr(l_1_link_tracking_interface, 'link_tracking'), 'groups'))):
                    pass
                    yield '| '
                    yield str(environment.getattr(l_1_link_tracking_interface, 'name'))
                    yield ' | '
                    yield str(t_5(context.eval_ctx, environment.getattr(environment.getattr(l_1_link_tracking_interface, 'link_tracking'), 'groups'), ', '))
                    yield ' | '
                    yield str(environment.getattr(environment.getattr(l_1_link_tracking_interface, 'link_tracking'), 'direction'))
                    yield ' |\n'
            l_1_link_tracking_interface = missing
        l_0_port_channel_interface_ipv4 = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace))
        context.vars['port_channel_interface_ipv4'] = l_0_port_channel_interface_ipv4
        context.exported_vars.add('port_channel_interface_ipv4')
        if not isinstance(l_0_port_channel_interface_ipv4, Namespace):
            raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
        l_0_port_channel_interface_ipv4['configured'] = False
        for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
            _loop_vars = {}
            pass
            if t_9(environment.getattr(l_1_port_channel_interface, 'ip_address')):
                pass
                if not isinstance(l_0_port_channel_interface_ipv4, Namespace):
                    raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                l_0_port_channel_interface_ipv4['configured'] = True
                break
        l_1_port_channel_interface = missing
        if environment.getattr((undefined(name='port_channel_interface_ipv4') if l_0_port_channel_interface_ipv4 is missing else l_0_port_channel_interface_ipv4), 'configured'):
            pass
            yield '\n##### IPv4\n\n| Interface | Description | MLAG ID | IP Address | VRF | MTU | Shutdown | ACL In | ACL Out |\n| --------- | ----------- | ------- | ---------- | --- | --- | -------- | ------ | ------- |\n'
            for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
                l_1_description = resolve('description')
                l_1_mlag = resolve('mlag')
                l_1_ip_address = resolve('ip_address')
                l_1_vrf = resolve('vrf')
                l_1_mtu = resolve('mtu')
                l_1_shutdown = resolve('shutdown')
                l_1_acl_in = resolve('acl_in')
                l_1_acl_out = resolve('acl_out')
                _loop_vars = {}
                pass
                if t_8(environment.getattr(l_1_port_channel_interface, 'ip_address')):
                    pass
                    l_1_description = t_1(environment.getattr(l_1_port_channel_interface, 'description'), '-')
                    _loop_vars['description'] = l_1_description
                    l_1_mlag = t_1(environment.getattr(l_1_port_channel_interface, 'mlag'), '-')
                    _loop_vars['mlag'] = l_1_mlag
                    l_1_ip_address = t_1(environment.getattr(l_1_port_channel_interface, 'ip_address'), '-')
                    _loop_vars['ip_address'] = l_1_ip_address
                    l_1_vrf = t_1(environment.getattr(l_1_port_channel_interface, 'vrf'), 'default')
                    _loop_vars['vrf'] = l_1_vrf
                    l_1_mtu = t_1(environment.getattr(l_1_port_channel_interface, 'mtu'), '-')
                    _loop_vars['mtu'] = l_1_mtu
                    l_1_shutdown = t_1(environment.getattr(l_1_port_channel_interface, 'shutdown'), '-')
                    _loop_vars['shutdown'] = l_1_shutdown
                    l_1_acl_in = t_1(environment.getattr(l_1_port_channel_interface, 'access_group_in'), '-')
                    _loop_vars['acl_in'] = l_1_acl_in
                    l_1_acl_out = t_1(environment.getattr(l_1_port_channel_interface, 'access_group_out'), '-')
                    _loop_vars['acl_out'] = l_1_acl_out
                    yield '| '
                    yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                    yield ' | '
                    yield str((undefined(name='description') if l_1_description is missing else l_1_description))
                    yield ' | '
                    yield str((undefined(name='mlag') if l_1_mlag is missing else l_1_mlag))
                    yield ' | '
                    yield str((undefined(name='ip_address') if l_1_ip_address is missing else l_1_ip_address))
                    yield ' | '
                    yield str((undefined(name='vrf') if l_1_vrf is missing else l_1_vrf))
                    yield ' | '
                    yield str((undefined(name='mtu') if l_1_mtu is missing else l_1_mtu))
                    yield ' | '
                    yield str((undefined(name='shutdown') if l_1_shutdown is missing else l_1_shutdown))
                    yield ' | '
                    yield str((undefined(name='acl_in') if l_1_acl_in is missing else l_1_acl_in))
                    yield ' | '
                    yield str((undefined(name='acl_out') if l_1_acl_out is missing else l_1_acl_out))
                    yield ' |\n'
            l_1_port_channel_interface = l_1_description = l_1_mlag = l_1_ip_address = l_1_vrf = l_1_mtu = l_1_shutdown = l_1_acl_in = l_1_acl_out = missing
        l_0_ip_nat_interfaces = (undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces)
        context.vars['ip_nat_interfaces'] = l_0_ip_nat_interfaces
        context.exported_vars.add('ip_nat_interfaces')
        template = environment.get_template('documentation/interfaces-ip-nat.j2', 'documentation/port-channel-interfaces.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {'encapsulation_dot1q_interfaces': l_0_encapsulation_dot1q_interfaces, 'evpn_dfe_po_interfaces': l_0_evpn_dfe_po_interfaces, 'evpn_es_po_interfaces': l_0_evpn_es_po_interfaces, 'evpn_mpls_po_interfaces': l_0_evpn_mpls_po_interfaces, 'flexencap_interfaces': l_0_flexencap_interfaces, 'ip_nat_interfaces': l_0_ip_nat_interfaces, 'link_tracking_interfaces': l_0_link_tracking_interfaces, 'port_channel_interface_ipv4': l_0_port_channel_interface_ipv4, 'port_channel_interface_ipv6': l_0_port_channel_interface_ipv6, 'port_channel_interface_pvlan': l_0_port_channel_interface_pvlan, 'port_channel_interface_vlan_xlate': l_0_port_channel_interface_vlan_xlate, 'port_channel_interfaces_isis': l_0_port_channel_interfaces_isis, 'port_channel_interfaces_vrrp_details': l_0_port_channel_interfaces_vrrp_details, 'port_channel_te_interfaces': l_0_port_channel_te_interfaces}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        l_0_port_channel_interface_ipv6 = context.call((undefined(name='namespace') if l_0_namespace is missing else l_0_namespace))
        context.vars['port_channel_interface_ipv6'] = l_0_port_channel_interface_ipv6
        context.exported_vars.add('port_channel_interface_ipv6')
        if not isinstance(l_0_port_channel_interface_ipv6, Namespace):
            raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
        l_0_port_channel_interface_ipv6['configured'] = False
        for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
            _loop_vars = {}
            pass
            if t_9(environment.getattr(l_1_port_channel_interface, 'ipv6_address')):
                pass
                if not isinstance(l_0_port_channel_interface_ipv6, Namespace):
                    raise TemplateRuntimeError("cannot assign attribute on non-namespace object")
                l_0_port_channel_interface_ipv6['configured'] = True
                break
        l_1_port_channel_interface = missing
        if environment.getattr((undefined(name='port_channel_interface_ipv6') if l_0_port_channel_interface_ipv6 is missing else l_0_port_channel_interface_ipv6), 'configured'):
            pass
            yield '\n##### IPv6\n\n| Interface | Description | MLAG ID | IPv6 Address | VRF | MTU | Shutdown | ND RA Disabled | Managed Config Flag | IPv6 ACL In | IPv6 ACL Out |\n| --------- | ----------- | ------- | -------------| --- | --- | -------- | -------------- | ------------------- | ----------- | ------------ |\n'
            for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
                l_1_description = resolve('description')
                l_1_mlag = resolve('mlag')
                l_1_ipv6_address = resolve('ipv6_address')
                l_1_vrf = resolve('vrf')
                l_1_mtu = resolve('mtu')
                l_1_shutdown = resolve('shutdown')
                l_1_ipv6_nd_ra_disabled = resolve('ipv6_nd_ra_disabled')
                l_1_ipv6_nd_managed_config_flag = resolve('ipv6_nd_managed_config_flag')
                l_1_ipv6_acl_in = resolve('ipv6_acl_in')
                l_1_ipv6_acl_out = resolve('ipv6_acl_out')
                _loop_vars = {}
                pass
                if t_8(environment.getattr(l_1_port_channel_interface, 'ipv6_address')):
                    pass
                    l_1_description = t_1(environment.getattr(l_1_port_channel_interface, 'description'), '-')
                    _loop_vars['description'] = l_1_description
                    l_1_mlag = t_1(environment.getattr(l_1_port_channel_interface, 'mlag'), '-')
                    _loop_vars['mlag'] = l_1_mlag
                    l_1_ipv6_address = t_1(environment.getattr(l_1_port_channel_interface, 'ipv6_address'), '-')
                    _loop_vars['ipv6_address'] = l_1_ipv6_address
                    l_1_vrf = t_1(environment.getattr(l_1_port_channel_interface, 'vrf'), 'default')
                    _loop_vars['vrf'] = l_1_vrf
                    l_1_mtu = t_1(environment.getattr(l_1_port_channel_interface, 'mtu'), '-')
                    _loop_vars['mtu'] = l_1_mtu
                    l_1_shutdown = t_1(environment.getattr(l_1_port_channel_interface, 'shutdown'), '-')
                    _loop_vars['shutdown'] = l_1_shutdown
                    l_1_ipv6_nd_ra_disabled = t_1(environment.getattr(l_1_port_channel_interface, 'ipv6_nd_ra_disabled'), '-')
                    _loop_vars['ipv6_nd_ra_disabled'] = l_1_ipv6_nd_ra_disabled
                    if t_8(environment.getattr(l_1_port_channel_interface, 'ipv6_nd_managed_config_flag')):
                        pass
                        l_1_ipv6_nd_managed_config_flag = environment.getattr(l_1_port_channel_interface, 'ipv6_nd_managed_config_flag')
                        _loop_vars['ipv6_nd_managed_config_flag'] = l_1_ipv6_nd_managed_config_flag
                    else:
                        pass
                        l_1_ipv6_nd_managed_config_flag = '-'
                        _loop_vars['ipv6_nd_managed_config_flag'] = l_1_ipv6_nd_managed_config_flag
                    l_1_ipv6_acl_in = t_1(environment.getattr(l_1_port_channel_interface, 'ipv6_access_group_in'), '-')
                    _loop_vars['ipv6_acl_in'] = l_1_ipv6_acl_in
                    l_1_ipv6_acl_out = t_1(environment.getattr(l_1_port_channel_interface, 'ipv6_access_group_out'), '-')
                    _loop_vars['ipv6_acl_out'] = l_1_ipv6_acl_out
                    yield '| '
                    yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                    yield ' | '
                    yield str((undefined(name='description') if l_1_description is missing else l_1_description))
                    yield ' | '
                    yield str((undefined(name='mlag') if l_1_mlag is missing else l_1_mlag))
                    yield ' | '
                    yield str((undefined(name='ipv6_address') if l_1_ipv6_address is missing else l_1_ipv6_address))
                    yield ' | '
                    yield str((undefined(name='vrf') if l_1_vrf is missing else l_1_vrf))
                    yield ' | '
                    yield str((undefined(name='mtu') if l_1_mtu is missing else l_1_mtu))
                    yield ' | '
                    yield str((undefined(name='shutdown') if l_1_shutdown is missing else l_1_shutdown))
                    yield ' | '
                    yield str((undefined(name='ipv6_nd_ra_disabled') if l_1_ipv6_nd_ra_disabled is missing else l_1_ipv6_nd_ra_disabled))
                    yield ' | '
                    yield str((undefined(name='ipv6_nd_managed_config_flag') if l_1_ipv6_nd_managed_config_flag is missing else l_1_ipv6_nd_managed_config_flag))
                    yield ' | '
                    yield str((undefined(name='ipv6_acl_in') if l_1_ipv6_acl_in is missing else l_1_ipv6_acl_in))
                    yield ' | '
                    yield str((undefined(name='ipv6_acl_out') if l_1_ipv6_acl_out is missing else l_1_ipv6_acl_out))
                    yield ' |\n'
            l_1_port_channel_interface = l_1_description = l_1_mlag = l_1_ipv6_address = l_1_vrf = l_1_mtu = l_1_shutdown = l_1_ipv6_nd_ra_disabled = l_1_ipv6_nd_managed_config_flag = l_1_ipv6_acl_in = l_1_ipv6_acl_out = missing
        l_0_port_channel_interfaces_vrrp_details = []
        context.vars['port_channel_interfaces_vrrp_details'] = l_0_port_channel_interfaces_vrrp_details
        context.exported_vars.add('port_channel_interfaces_vrrp_details')
        for l_1_port_channel_interface in t_1((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), []):
            _loop_vars = {}
            pass
            if t_8(environment.getattr(l_1_port_channel_interface, 'vrrp_ids')):
                pass
                context.call(environment.getattr((undefined(name='port_channel_interfaces_vrrp_details') if l_0_port_channel_interfaces_vrrp_details is missing else l_0_port_channel_interfaces_vrrp_details), 'append'), l_1_port_channel_interface, _loop_vars=_loop_vars)
        l_1_port_channel_interface = missing
        if (t_6((undefined(name='port_channel_interfaces_vrrp_details') if l_0_port_channel_interfaces_vrrp_details is missing else l_0_port_channel_interfaces_vrrp_details)) > 0):
            pass
            yield '\n##### VRRP Details\n\n| Interface | VRRP-ID | Priority | Advertisement Interval | Preempt | Tracked Object Name(s) | Tracked Object Action(s) | IPv4 Virtual IPs | IPv4 VRRP Version | IPv6 Virtual IPs | Peer Authentication Mode |\n| --------- | ------- | -------- | ---------------------- | --------| ---------------------- | ------------------------ | ---------------- | ----------------- | ---------------- | ------------------------ |\n'
            for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces_vrrp_details') if l_0_port_channel_interfaces_vrrp_details is missing else l_0_port_channel_interfaces_vrrp_details), 'name'):
                _loop_vars = {}
                pass
                for l_2_vrid in t_3(environment.getattr(l_1_port_channel_interface, 'vrrp_ids'), 'id'):
                    l_2_row_tracked_object_name = resolve('row_tracked_object_name')
                    l_2_row_tracked_object_action = resolve('row_tracked_object_action')
                    l_2_row_id = l_2_row_prio_level = l_2_row_ad_interval = l_2_row_preempt = l_2_peer_auth_mode = l_2_row_ipv4_virtual_ips = l_2_row_ipv4_version = l_2_row_ipv6_virtual_ips = missing
                    _loop_vars = {}
                    pass
                    l_2_row_id = environment.getattr(l_2_vrid, 'id')
                    _loop_vars['row_id'] = l_2_row_id
                    l_2_row_prio_level = t_1(environment.getattr(l_2_vrid, 'priority_level'), '-')
                    _loop_vars['row_prio_level'] = l_2_row_prio_level
                    l_2_row_ad_interval = t_1(environment.getattr(environment.getattr(l_2_vrid, 'advertisement'), 'interval'), '-')
                    _loop_vars['row_ad_interval'] = l_2_row_ad_interval
                    l_2_row_preempt = 'Enabled'
                    _loop_vars['row_preempt'] = l_2_row_preempt
                    if t_8(environment.getattr(environment.getattr(l_2_vrid, 'preempt'), 'enabled'), False):
                        pass
                        l_2_row_preempt = 'Disabled'
                        _loop_vars['row_preempt'] = l_2_row_preempt
                    if t_8(environment.getattr(l_2_vrid, 'tracked_object')):
                        pass
                        l_2_row_tracked_object_name = []
                        _loop_vars['row_tracked_object_name'] = l_2_row_tracked_object_name
                        l_2_row_tracked_object_action = []
                        _loop_vars['row_tracked_object_action'] = l_2_row_tracked_object_action
                        for l_3_tracked_obj in t_3(environment.getattr(l_2_vrid, 'tracked_object'), 'name'):
                            _loop_vars = {}
                            pass
                            context.call(environment.getattr((undefined(name='row_tracked_object_name') if l_2_row_tracked_object_name is missing else l_2_row_tracked_object_name), 'append'), environment.getattr(l_3_tracked_obj, 'name'), _loop_vars=_loop_vars)
                            if t_8(environment.getattr(l_3_tracked_obj, 'shutdown'), True):
                                pass
                                context.call(environment.getattr((undefined(name='row_tracked_object_action') if l_2_row_tracked_object_action is missing else l_2_row_tracked_object_action), 'append'), 'Shutdown', _loop_vars=_loop_vars)
                            elif t_8(environment.getattr(l_3_tracked_obj, 'decrement')):
                                pass
                                context.call(environment.getattr((undefined(name='row_tracked_object_action') if l_2_row_tracked_object_action is missing else l_2_row_tracked_object_action), 'append'), str_join(('Decrement ', environment.getattr(l_3_tracked_obj, 'decrement'), )), _loop_vars=_loop_vars)
                        l_3_tracked_obj = missing
                        l_2_row_tracked_object_name = t_5(context.eval_ctx, (undefined(name='row_tracked_object_name') if l_2_row_tracked_object_name is missing else l_2_row_tracked_object_name), ', ')
                        _loop_vars['row_tracked_object_name'] = l_2_row_tracked_object_name
                        l_2_row_tracked_object_action = t_5(context.eval_ctx, (undefined(name='row_tracked_object_action') if l_2_row_tracked_object_action is missing else l_2_row_tracked_object_action), ', ')
                        _loop_vars['row_tracked_object_action'] = l_2_row_tracked_object_action
                    l_2_peer_auth_mode = t_1(environment.getattr(environment.getattr(l_2_vrid, 'peer_authentication'), 'mode'), '-')
                    _loop_vars['peer_auth_mode'] = l_2_peer_auth_mode
                    l_2_row_ipv4_virtual_ips = []
                    _loop_vars['row_ipv4_virtual_ips'] = l_2_row_ipv4_virtual_ips
                    if t_8(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'address')):
                        pass
                        context.call(environment.getattr((undefined(name='row_ipv4_virtual_ips') if l_2_row_ipv4_virtual_ips is missing else l_2_row_ipv4_virtual_ips), 'append'), environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'address'), _loop_vars=_loop_vars)
                    if t_8(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'secondary_addresses')):
                        pass
                        context.call(environment.getattr((undefined(name='row_ipv4_virtual_ips') if l_2_row_ipv4_virtual_ips is missing else l_2_row_ipv4_virtual_ips), 'extend'), environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'secondary_addresses'), _loop_vars=_loop_vars)
                    l_2_row_ipv4_version = t_1(environment.getattr(environment.getattr(l_2_vrid, 'ipv4'), 'version'), '2')
                    _loop_vars['row_ipv4_version'] = l_2_row_ipv4_version
                    l_2_row_ipv6_virtual_ips = t_5(context.eval_ctx, t_1(environment.getattr(environment.getattr(l_2_vrid, 'ipv6'), 'addresses'), environment.getattr(environment.getattr(l_2_vrid, 'ipv6'), 'address'), '-'), ', ')
                    _loop_vars['row_ipv6_virtual_ips'] = l_2_row_ipv6_virtual_ips
                    yield '| '
                    yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                    yield ' | '
                    yield str((undefined(name='row_id') if l_2_row_id is missing else l_2_row_id))
                    yield ' | '
                    yield str((undefined(name='row_prio_level') if l_2_row_prio_level is missing else l_2_row_prio_level))
                    yield ' | '
                    yield str((undefined(name='row_ad_interval') if l_2_row_ad_interval is missing else l_2_row_ad_interval))
                    yield ' | '
                    yield str((undefined(name='row_preempt') if l_2_row_preempt is missing else l_2_row_preempt))
                    yield ' | '
                    yield str(t_1((undefined(name='row_tracked_object_name') if l_2_row_tracked_object_name is missing else l_2_row_tracked_object_name), '-'))
                    yield ' | '
                    yield str(t_1((undefined(name='row_tracked_object_action') if l_2_row_tracked_object_action is missing else l_2_row_tracked_object_action), '-'))
                    yield ' | '
                    yield str(t_1(t_5(context.eval_ctx, (undefined(name='row_ipv4_virtual_ips') if l_2_row_ipv4_virtual_ips is missing else l_2_row_ipv4_virtual_ips), ', '), '-'))
                    yield ' | '
                    yield str((undefined(name='row_ipv4_version') if l_2_row_ipv4_version is missing else l_2_row_ipv4_version))
                    yield ' | '
                    yield str((undefined(name='row_ipv6_virtual_ips') if l_2_row_ipv6_virtual_ips is missing else l_2_row_ipv6_virtual_ips))
                    yield ' | '
                    yield str((undefined(name='peer_auth_mode') if l_2_peer_auth_mode is missing else l_2_peer_auth_mode))
                    yield ' |\n'
                l_2_vrid = l_2_row_id = l_2_row_prio_level = l_2_row_ad_interval = l_2_row_preempt = l_2_row_tracked_object_name = l_2_row_tracked_object_action = l_2_peer_auth_mode = l_2_row_ipv4_virtual_ips = l_2_row_ipv4_version = l_2_row_ipv6_virtual_ips = missing
            l_1_port_channel_interface = missing
        l_0_port_channel_interfaces_isis = []
        context.vars['port_channel_interfaces_isis'] = l_0_port_channel_interfaces_isis
        context.exported_vars.add('port_channel_interfaces_isis')
        for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
            _loop_vars = {}
            pass
            if (((((((t_8(environment.getattr(l_1_port_channel_interface, 'isis_enable')) or t_8(environment.getattr(l_1_port_channel_interface, 'isis_bfd'))) or t_8(environment.getattr(l_1_port_channel_interface, 'isis_metric'))) or t_8(environment.getattr(l_1_port_channel_interface, 'isis_circuit_type'))) or t_8(environment.getattr(l_1_port_channel_interface, 'isis_network_point_to_point'))) or t_8(environment.getattr(l_1_port_channel_interface, 'isis_passive'))) or t_8(environment.getattr(l_1_port_channel_interface, 'isis_hello_padding'))) or t_8(environment.getattr(l_1_port_channel_interface, 'isis_authentication'))):
                pass
                context.call(environment.getattr((undefined(name='port_channel_interfaces_isis') if l_0_port_channel_interfaces_isis is missing else l_0_port_channel_interfaces_isis), 'append'), l_1_port_channel_interface, _loop_vars=_loop_vars)
        l_1_port_channel_interface = missing
        if (t_6((undefined(name='port_channel_interfaces_isis') if l_0_port_channel_interfaces_isis is missing else l_0_port_channel_interfaces_isis)) > 0):
            pass
            yield '\n##### ISIS\n\n| Interface | ISIS Instance | ISIS BFD | ISIS Metric | Mode | ISIS Circuit Type | Hello Padding | ISIS Authentication Mode |\n| --------- | ------------- | -------- | ----------- | ---- | ----------------- | ------------- | ------------------------ |\n'
            for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces_isis') if l_0_port_channel_interfaces_isis is missing else l_0_port_channel_interfaces_isis), 'name'):
                l_1_isis_authentication_mode = resolve('isis_authentication_mode')
                l_1_mode = resolve('mode')
                l_1_isis_instance = l_1_isis_bfd = l_1_isis_metric = l_1_isis_circuit_type = l_1_isis_hello_padding = missing
                _loop_vars = {}
                pass
                l_1_isis_instance = t_1(environment.getattr(l_1_port_channel_interface, 'isis_enable'), '-')
                _loop_vars['isis_instance'] = l_1_isis_instance
                l_1_isis_bfd = t_1(environment.getattr(l_1_port_channel_interface, 'isis_bfd'), '-')
                _loop_vars['isis_bfd'] = l_1_isis_bfd
                l_1_isis_metric = t_1(environment.getattr(l_1_port_channel_interface, 'isis_metric'), '-')
                _loop_vars['isis_metric'] = l_1_isis_metric
                l_1_isis_circuit_type = t_1(environment.getattr(l_1_port_channel_interface, 'isis_circuit_type'), '-')
                _loop_vars['isis_circuit_type'] = l_1_isis_circuit_type
                l_1_isis_hello_padding = t_1(environment.getattr(l_1_port_channel_interface, 'isis_hello_padding'), '-')
                _loop_vars['isis_hello_padding'] = l_1_isis_hello_padding
                if t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'mode')):
                    pass
                    l_1_isis_authentication_mode = environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'both'), 'mode')
                    _loop_vars['isis_authentication_mode'] = l_1_isis_authentication_mode
                elif (t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode')) and t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode'))):
                    pass
                    l_1_isis_authentication_mode = str_join(('Level-1: ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode'), '<br>', 'Level-2: ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode'), ))
                    _loop_vars['isis_authentication_mode'] = l_1_isis_authentication_mode
                elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode')):
                    pass
                    l_1_isis_authentication_mode = str_join(('Level-1: ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_1'), 'mode'), ))
                    _loop_vars['isis_authentication_mode'] = l_1_isis_authentication_mode
                elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode')):
                    pass
                    l_1_isis_authentication_mode = str_join(('Level-2: ', environment.getattr(environment.getattr(environment.getattr(l_1_port_channel_interface, 'isis_authentication'), 'level_2'), 'mode'), ))
                    _loop_vars['isis_authentication_mode'] = l_1_isis_authentication_mode
                else:
                    pass
                    l_1_isis_authentication_mode = '-'
                    _loop_vars['isis_authentication_mode'] = l_1_isis_authentication_mode
                if t_8(environment.getattr(l_1_port_channel_interface, 'isis_network_point_to_point'), True):
                    pass
                    l_1_mode = 'point-to-point'
                    _loop_vars['mode'] = l_1_mode
                elif t_8(environment.getattr(l_1_port_channel_interface, 'isis_passive'), True):
                    pass
                    l_1_mode = 'passive'
                    _loop_vars['mode'] = l_1_mode
                else:
                    pass
                    l_1_mode = '-'
                    _loop_vars['mode'] = l_1_mode
                yield '| '
                yield str(environment.getattr(l_1_port_channel_interface, 'name'))
                yield ' | '
                yield str((undefined(name='isis_instance') if l_1_isis_instance is missing else l_1_isis_instance))
                yield ' | '
                yield str((undefined(name='isis_bfd') if l_1_isis_bfd is missing else l_1_isis_bfd))
                yield ' | '
                yield str((undefined(name='isis_metric') if l_1_isis_metric is missing else l_1_isis_metric))
                yield ' | '
                yield str((undefined(name='mode') if l_1_mode is missing else l_1_mode))
                yield ' | '
                yield str((undefined(name='isis_circuit_type') if l_1_isis_circuit_type is missing else l_1_isis_circuit_type))
                yield ' | '
                yield str((undefined(name='isis_hello_padding') if l_1_isis_hello_padding is missing else l_1_isis_hello_padding))
                yield ' | '
                yield str((undefined(name='isis_authentication_mode') if l_1_isis_authentication_mode is missing else l_1_isis_authentication_mode))
                yield ' |\n'
            l_1_port_channel_interface = l_1_isis_instance = l_1_isis_bfd = l_1_isis_metric = l_1_isis_circuit_type = l_1_isis_hello_padding = l_1_isis_authentication_mode = l_1_mode = missing
        l_0_port_channel_te_interfaces = []
        context.vars['port_channel_te_interfaces'] = l_0_port_channel_te_interfaces
        context.exported_vars.add('port_channel_te_interfaces')
        for l_1_port_channel_interface in t_3((undefined(name='port_channel_interfaces') if l_0_port_channel_interfaces is missing else l_0_port_channel_interfaces), 'name'):
            _loop_vars = {}
            pass
            if t_8(environment.getattr(environment.getattr(l_1_port_channel_interface, 'traffic_engineering'), 'enabled'), True):
                pass
                context.call(environment.getattr((undefined(name='port_channel_te_interfaces') if l_0_port_channel_te_interfaces is missing else l_0_port_channel_te_interfaces), 'append'), l_1_port_channel_interface, _loop_vars=_loop_vars)
        l_1_port_channel_interface = missing
        if (t_6((undefined(name='port_channel_te_interfaces') if l_0_port_channel_te_interfaces is missing else l_0_port_channel_te_interfaces)) > 0):
            pass
            yield '\n#### Traffic Engineering\n\n| Interface | Enabled | Administrative Groups | Metric | Max Reservable Bandwidth | Min-delay | SRLGs |\n| --------- | ------- | --------------------- | ------ | ------------------------ | --------- | ---- |\n'
            for l_1_po_te_interface in (undefined(name='port_channel_te_interfaces') if l_0_port_channel_te_interfaces is missing else l_0_port_channel_te_interfaces):
                l_1_te_bandwidth = resolve('te_bandwidth')
                l_1_te_min_del = resolve('te_min_del')
                l_1_admin_groups = l_1_te_enabled = l_1_te_srlgs = l_1_te_metric = missing
                _loop_vars = {}
                pass
                l_1_admin_groups = t_5(context.eval_ctx, t_1(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'administrative_groups'), ['-']), ',')
                _loop_vars['admin_groups'] = l_1_admin_groups
                l_1_te_enabled = t_1(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'enabled'), '-')
                _loop_vars['te_enabled'] = l_1_te_enabled
                l_1_te_srlgs = t_1(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'srlgs'), ['-'])
                _loop_vars['te_srlgs'] = l_1_te_srlgs
                l_1_te_metric = t_1(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'metric'), '-')
                _loop_vars['te_metric'] = l_1_te_metric
                if t_8(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'bandwidth')):
                    pass
                    l_1_te_bandwidth = str_join((environment.getattr(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'bandwidth'), 'number'), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'bandwidth'), 'unit'), ))
                    _loop_vars['te_bandwidth'] = l_1_te_bandwidth
                else:
                    pass
                    l_1_te_bandwidth = '-'
                    _loop_vars['te_bandwidth'] = l_1_te_bandwidth
                if t_8(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'min_delay_static')):
                    pass
                    l_1_te_min_del = str_join((environment.getattr(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'min_delay_static'), 'number'), ' ', environment.getattr(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'min_delay_static'), 'unit'), ))
                    _loop_vars['te_min_del'] = l_1_te_min_del
                elif t_8(environment.getattr(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'min_delay_dynamic'), 'twamp_light_fallback')):
                    pass
                    l_1_te_min_del = str_join(('twamp-light, fallback ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'min_delay_dynamic'), 'twamp_light_fallback'), 'number'), ' ', environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_po_te_interface, 'traffic_engineering'), 'min_delay_dynamic'), 'twamp_light_fallback'), 'unit'), ))
                    _loop_vars['te_min_del'] = l_1_te_min_del
                else:
                    pass
                    l_1_te_min_del = '-'
                    _loop_vars['te_min_del'] = l_1_te_min_del
                yield '| '
                yield str(environment.getattr(l_1_po_te_interface, 'name'))
                yield ' | '
                yield str((undefined(name='te_enabled') if l_1_te_enabled is missing else l_1_te_enabled))
                yield ' | '
                yield str((undefined(name='admin_groups') if l_1_admin_groups is missing else l_1_admin_groups))
                yield ' | '
                yield str((undefined(name='te_metric') if l_1_te_metric is missing else l_1_te_metric))
                yield ' | '
                yield str((undefined(name='te_bandwidth') if l_1_te_bandwidth is missing else l_1_te_bandwidth))
                yield ' | '
                yield str((undefined(name='te_min_del') if l_1_te_min_del is missing else l_1_te_min_del))
                yield ' | '
                yield str(t_5(context.eval_ctx, (undefined(name='te_srlgs') if l_1_te_srlgs is missing else l_1_te_srlgs), ','))
                yield ' |\n'
            l_1_po_te_interface = l_1_admin_groups = l_1_te_enabled = l_1_te_srlgs = l_1_te_metric = l_1_te_bandwidth = l_1_te_min_del = missing
        yield '\n#### Port-Channel Interfaces Device Configuration\n\n```eos\n'
        template = environment.get_template('eos/port-channel-interfaces.j2', 'documentation/port-channel-interfaces.j2')
        gen = template.root_render_func(template.new_context(context.get_all(), True, {'encapsulation_dot1q_interfaces': l_0_encapsulation_dot1q_interfaces, 'evpn_dfe_po_interfaces': l_0_evpn_dfe_po_interfaces, 'evpn_es_po_interfaces': l_0_evpn_es_po_interfaces, 'evpn_mpls_po_interfaces': l_0_evpn_mpls_po_interfaces, 'flexencap_interfaces': l_0_flexencap_interfaces, 'ip_nat_interfaces': l_0_ip_nat_interfaces, 'link_tracking_interfaces': l_0_link_tracking_interfaces, 'port_channel_interface_ipv4': l_0_port_channel_interface_ipv4, 'port_channel_interface_ipv6': l_0_port_channel_interface_ipv6, 'port_channel_interface_pvlan': l_0_port_channel_interface_pvlan, 'port_channel_interface_vlan_xlate': l_0_port_channel_interface_vlan_xlate, 'port_channel_interfaces_isis': l_0_port_channel_interfaces_isis, 'port_channel_interfaces_vrrp_details': l_0_port_channel_interfaces_vrrp_details, 'port_channel_te_interfaces': l_0_port_channel_te_interfaces}))
        try:
            for event in gen:
                yield event
        finally: gen.close()
        yield '```\n'

blocks = {}
debug_info = '7=81&17=84&18=96&25=98&26=100&27=102&29=104&30=106&31=108&33=109&34=111&36=112&37=114&39=118&42=120&43=122&45=126&47=128&48=130&49=132&50=134&51=136&52=139&56=160&57=163&58=166&59=169&60=171&61=172&62=174&65=176&71=179&72=183&73=185&74=187&75=189&76=192&79=203&85=206&86=218&87=220&88=222&89=224&90=226&91=228&92=230&93=232&95=234&96=236&97=238&98=240&99=242&100=244&102=247&106=274&107=279&108=280&109=283&111=287&112=288&115=290&121=293&122=297&123=299&124=301&125=304&130=311&131=316&132=317&133=320&134=324&135=325&138=327&144=330&145=333&146=335&147=339&149=352&150=356&152=369&153=374&154=376&155=378&157=382&159=385&165=399&166=402&167=405&168=408&169=411&170=414&171=416&172=417&173=419&175=420&176=422&179=423&180=425&184=427&192=430&193=434&194=436&195=438&196=441&198=450&204=453&205=457&206=459&207=461&208=463&209=465&210=467&211=469&212=472&215=487&221=490&222=494&223=496&224=499&229=506&235=509&236=512&237=515&238=518&241=525&242=528&247=535&248=540&249=541&250=544&251=548&252=549&255=551&261=554&262=565&263=567&264=569&265=571&266=573&267=575&268=577&269=579&270=581&271=584&276=603&277=606&279=612&280=617&281=618&282=621&283=625&284=626&287=628&293=631&294=644&295=646&296=648&297=650&298=652&299=654&300=656&301=658&302=660&303=662&305=666&307=668&308=670&309=673&314=696&315=699&316=702&317=704&320=706&326=709&327=712&328=718&329=720&330=722&331=724&332=726&333=728&335=730&336=732&337=734&338=736&339=739&340=740&341=742&342=743&343=745&346=747&347=749&349=751&350=753&351=755&352=757&354=758&355=760&357=761&358=763&359=766&364=790&365=793&366=796&374=798&377=800&383=803&384=809&385=811&386=813&387=815&388=817&389=819&390=821&391=823&392=825&393=827&394=829&395=831&396=833&398=837&400=839&401=841&402=843&403=845&405=849&407=852&410=869&411=872&412=875&413=877&416=879&422=882&423=888&424=890&425=892&426=894&427=896&428=898&430=902&432=904&433=906&434=908&435=910&437=914&439=917&446=933'