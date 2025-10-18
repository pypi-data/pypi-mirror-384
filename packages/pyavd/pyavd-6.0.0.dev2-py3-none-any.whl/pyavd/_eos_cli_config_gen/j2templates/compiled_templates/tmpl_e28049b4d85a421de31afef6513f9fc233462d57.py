from jinja2.runtime import LoopContext, Macro, Markup, Namespace, TemplateNotFound, TemplateReference, TemplateRuntimeError, Undefined, escape, identity, internalcode, markup_join, missing, str_join
name = 'eos/router-bgp.j2'

def root(context, missing=missing):
    resolve = context.resolve_or_missing
    undefined = environment.undefined
    concat = environment.concat
    cond_expr_undefined = Undefined
    if 0: yield None
    l_0_router_bgp = resolve('router_bgp')
    l_0_timers_bgp_cli = resolve('timers_bgp_cli')
    l_0_distance_cli = resolve('distance_cli')
    l_0_rr_preserve_attributes_cli = resolve('rr_preserve_attributes_cli')
    l_0_paths_cli = resolve('paths_cli')
    l_0_redistribute_var = resolve('redistribute_var')
    l_0_redistribute_conn = resolve('redistribute_conn')
    l_0_redistribute_isis = resolve('redistribute_isis')
    l_0_redistribute_ospf = resolve('redistribute_ospf')
    l_0_redistribute_ospf_match = resolve('redistribute_ospf_match')
    l_0_redistribute_ospfv3 = resolve('redistribute_ospfv3')
    l_0_redistribute_ospfv3_match = resolve('redistribute_ospfv3_match')
    l_0_redistribute_static = resolve('redistribute_static')
    l_0_redistribute_rip = resolve('redistribute_rip')
    l_0_redistribute_host = resolve('redistribute_host')
    l_0_redistribute_dynamic = resolve('redistribute_dynamic')
    l_0_redistribute_bgp = resolve('redistribute_bgp')
    l_0_redistribute_user = resolve('redistribute_user')
    l_0_encapsulation_cli = resolve('encapsulation_cli')
    l_0_evpn_mpls_resolution_ribs = resolve('evpn_mpls_resolution_ribs')
    l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli = resolve('evpn_neighbor_default_nhs_received_evpn_routes_cli')
    l_0_hostflap_detection_cli = resolve('hostflap_detection_cli')
    l_0_layer2_cli = resolve('layer2_cli')
    l_0_v4_bgp_lu_resolution_ribs = resolve('v4_bgp_lu_resolution_ribs')
    l_0_redistribute_dhcp = resolve('redistribute_dhcp')
    l_0_path_selection_roles = resolve('path_selection_roles')
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
        t_4 = environment.filters['indent']
    except KeyError:
        @internalcode
        def t_4(*unused):
            raise TemplateRuntimeError("No filter named 'indent' found.")
    try:
        t_5 = environment.filters['join']
    except KeyError:
        @internalcode
        def t_5(*unused):
            raise TemplateRuntimeError("No filter named 'join' found.")
    try:
        t_6 = environment.tests['arista.avd.defined']
    except KeyError:
        @internalcode
        def t_6(*unused):
            raise TemplateRuntimeError("No test named 'arista.avd.defined' found.")
    try:
        t_7 = environment.tests['defined']
    except KeyError:
        @internalcode
        def t_7(*unused):
            raise TemplateRuntimeError("No test named 'defined' found.")
    try:
        t_8 = environment.tests['number']
    except KeyError:
        @internalcode
        def t_8(*unused):
            raise TemplateRuntimeError("No test named 'number' found.")
    pass
    if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'as')):
        pass
        yield '!\nrouter bgp '
        yield str(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'as'))
        yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'as_notation')):
            pass
            yield '   bgp asn notation '
            yield str(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'as_notation'))
            yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'router_id')):
            pass
            yield '   router-id '
            yield str(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'router_id'))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'updates'), 'wait_for_convergence'), True):
            pass
            yield '   update wait-for-convergence\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'updates'), 'wait_install'), True):
            pass
            yield '   update wait-install\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'default'), 'ipv4_unicast'), True):
            pass
            yield '   bgp default ipv4-unicast\n'
        elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'default'), 'ipv4_unicast'), False):
            pass
            yield '   no bgp default ipv4-unicast\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'default'), 'ipv4_unicast_transport_ipv6'), True):
            pass
            yield '   bgp default ipv4-unicast transport ipv6\n'
        elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'default'), 'ipv4_unicast_transport_ipv6'), False):
            pass
            yield '   no bgp default ipv4-unicast transport ipv6\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers')):
            pass
            l_0_timers_bgp_cli = 'timers bgp'
            context.vars['timers_bgp_cli'] = l_0_timers_bgp_cli
            context.exported_vars.add('timers_bgp_cli')
            if (t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'keepalive_time')) and t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'hold_time'))):
                pass
                l_0_timers_bgp_cli = str_join(((undefined(name='timers_bgp_cli') if l_0_timers_bgp_cli is missing else l_0_timers_bgp_cli), ' ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'keepalive_time'), ' ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'hold_time'), ))
                context.vars['timers_bgp_cli'] = l_0_timers_bgp_cli
                context.exported_vars.add('timers_bgp_cli')
            if (t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'min_hold_time')) or t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'send_failure_hold_time'))):
                pass
                if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'min_hold_time')):
                    pass
                    l_0_timers_bgp_cli = str_join(((undefined(name='timers_bgp_cli') if l_0_timers_bgp_cli is missing else l_0_timers_bgp_cli), ' min-hold-time ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'min_hold_time'), ))
                    context.vars['timers_bgp_cli'] = l_0_timers_bgp_cli
                    context.exported_vars.add('timers_bgp_cli')
                if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'send_failure_hold_time')):
                    pass
                    l_0_timers_bgp_cli = str_join(((undefined(name='timers_bgp_cli') if l_0_timers_bgp_cli is missing else l_0_timers_bgp_cli), ' send-failure hold-time ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'timers'), 'send_failure_hold_time'), ))
                    context.vars['timers_bgp_cli'] = l_0_timers_bgp_cli
                    context.exported_vars.add('timers_bgp_cli')
            yield '   '
            yield str((undefined(name='timers_bgp_cli') if l_0_timers_bgp_cli is missing else l_0_timers_bgp_cli))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'external_routes')):
            pass
            l_0_distance_cli = str_join(('distance bgp ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'external_routes'), ))
            context.vars['distance_cli'] = l_0_distance_cli
            context.exported_vars.add('distance_cli')
            if (t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'internal_routes')) and t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'local_routes'))):
                pass
                l_0_distance_cli = str_join(((undefined(name='distance_cli') if l_0_distance_cli is missing else l_0_distance_cli), ' ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'internal_routes'), ' ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'distance'), 'local_routes'), ))
                context.vars['distance_cli'] = l_0_distance_cli
                context.exported_vars.add('distance_cli')
            yield '   '
            yield str((undefined(name='distance_cli') if l_0_distance_cli is missing else l_0_distance_cli))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'enabled'), True):
            pass
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'restart_time')):
                pass
                yield '   graceful-restart restart-time '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'restart_time'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'stalepath_time')):
                pass
                yield '   graceful-restart stalepath-time '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart'), 'stalepath_time'))
                yield '\n'
            yield '   graceful-restart\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp_cluster_id')):
            pass
            yield '   bgp cluster-id '
            yield str(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp_cluster_id'))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'enabled'), False):
            pass
            yield '   no graceful-restart-helper\n'
        elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'enabled'), True):
            pass
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'restart_time')):
                pass
                yield '   graceful-restart-helper restart-time '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'restart_time'))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'graceful_restart_helper'), 'long_lived'), True):
                pass
                yield '   graceful-restart-helper long-lived\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'route_reflector_preserve_attributes'), 'enabled'), True):
            pass
            l_0_rr_preserve_attributes_cli = 'bgp route-reflector preserve-attributes'
            context.vars['rr_preserve_attributes_cli'] = l_0_rr_preserve_attributes_cli
            context.exported_vars.add('rr_preserve_attributes_cli')
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'route_reflector_preserve_attributes'), 'always'), True):
                pass
                l_0_rr_preserve_attributes_cli = str_join(((undefined(name='rr_preserve_attributes_cli') if l_0_rr_preserve_attributes_cli is missing else l_0_rr_preserve_attributes_cli), ' always', ))
                context.vars['rr_preserve_attributes_cli'] = l_0_rr_preserve_attributes_cli
                context.exported_vars.add('rr_preserve_attributes_cli')
            yield '   '
            yield str((undefined(name='rr_preserve_attributes_cli') if l_0_rr_preserve_attributes_cli is missing else l_0_rr_preserve_attributes_cli))
            yield '\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'maximum_paths'), 'paths')):
            pass
            l_0_paths_cli = str_join(('maximum-paths ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'maximum_paths'), 'paths'), ))
            context.vars['paths_cli'] = l_0_paths_cli
            context.exported_vars.add('paths_cli')
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'maximum_paths'), 'ecmp')):
                pass
                l_0_paths_cli = str_join(((undefined(name='paths_cli') if l_0_paths_cli is missing else l_0_paths_cli), ' ecmp ', environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'maximum_paths'), 'ecmp'), ))
                context.vars['paths_cli'] = l_0_paths_cli
                context.exported_vars.add('paths_cli')
            yield '   '
            yield str((undefined(name='paths_cli') if l_0_paths_cli is missing else l_0_paths_cli))
            yield '\n'
        for l_1_bgp_default in t_1(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp_defaults'), []):
            _loop_vars = {}
            pass
            yield '   '
            yield str(l_1_bgp_default)
            yield '\n'
        l_1_bgp_default = missing
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'receive'), True):
            pass
            yield '   bgp additional-paths receive\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'receive'), False):
            pass
            yield '   no bgp additional-paths receive\n'
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send')):
            pass
            if (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                pass
                yield '   no bgp additional-paths send\n'
            elif (t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                pass
                yield '   bgp additional-paths send ecmp limit '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send_limit'))
                yield '\n'
            elif (environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                pass
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send_limit')):
                    pass
                    yield '   bgp additional-paths send limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
            else:
                pass
                yield '   bgp additional-paths send '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'additional_paths'), 'send'))
                yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'listen_ranges')):
            pass
            def t_9(fiter):
                for l_1_listen_range in fiter:
                    if ((t_6(environment.getattr(l_1_listen_range, 'peer_group')) and t_6(environment.getattr(l_1_listen_range, 'prefix'))) and (t_6(environment.getattr(l_1_listen_range, 'peer_filter')) or t_6(environment.getattr(l_1_listen_range, 'remote_as')))):
                        yield l_1_listen_range
            for l_1_listen_range in t_9(t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'listen_ranges'), 'peer_group')):
                l_1_listen_range_cli = missing
                _loop_vars = {}
                pass
                l_1_listen_range_cli = str_join(('bgp listen range ', environment.getattr(l_1_listen_range, 'prefix'), ))
                _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                if t_6(environment.getattr(l_1_listen_range, 'peer_id_include_router_id'), True):
                    pass
                    l_1_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli), ' peer-id include router-id', ))
                    _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                l_1_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli), ' peer-group ', environment.getattr(l_1_listen_range, 'peer_group'), ))
                _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                if t_6(environment.getattr(l_1_listen_range, 'peer_filter')):
                    pass
                    l_1_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli), ' peer-filter ', environment.getattr(l_1_listen_range, 'peer_filter'), ))
                    _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                elif t_6(environment.getattr(l_1_listen_range, 'remote_as')):
                    pass
                    l_1_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli), ' remote-as ', environment.getattr(l_1_listen_range, 'remote_as'), ))
                    _loop_vars['listen_range_cli'] = l_1_listen_range_cli
                yield '   '
                yield str((undefined(name='listen_range_cli') if l_1_listen_range_cli is missing else l_1_listen_range_cli))
                yield '\n'
            l_1_listen_range = l_1_listen_range_cli = missing
        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'bestpath'), 'd_path'), True):
            pass
            yield '   bgp bestpath d-path\n'
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbor_default'), 'send_community'), 'all'):
            pass
            yield '   neighbor default send-community\n'
        elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbor_default'), 'send_community')):
            pass
            yield '   neighbor default send-community '
            yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbor_default'), 'send_community'))
            yield '\n'
        for l_1_peer_group in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'peer_groups'), 'name'):
            l_1_remove_private_as_cli = resolve('remove_private_as_cli')
            l_1_allowas_in_cli = resolve('allowas_in_cli')
            l_1_neighbor_rib_in_pre_policy_retain_cli = resolve('neighbor_rib_in_pre_policy_retain_cli')
            l_1_hide_passwords = resolve('hide_passwords')
            l_1_default_originate_cli = resolve('default_originate_cli')
            l_1_maximum_routes_cli = resolve('maximum_routes_cli')
            l_1_link_bandwidth_cli = resolve('link_bandwidth_cli')
            l_1_remove_private_as_ingress_cli = resolve('remove_private_as_ingress_cli')
            _loop_vars = {}
            pass
            yield '   neighbor '
            yield str(environment.getattr(l_1_peer_group, 'name'))
            yield ' peer group\n'
            if t_6(environment.getattr(l_1_peer_group, 'remote_as')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' remote-as '
                yield str(environment.getattr(l_1_peer_group, 'remote_as'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'next_hop_self'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' next-hop-self\n'
            if t_6(environment.getattr(l_1_peer_group, 'next_hop_peer'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' next-hop-peer\n'
            if t_6(environment.getattr(l_1_peer_group, 'next_hop_unchanged'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' next-hop-unchanged\n'
            if t_6(environment.getattr(l_1_peer_group, 'shutdown'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' shutdown\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as'), 'enabled'), True):
                pass
                l_1_remove_private_as_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' remove-private-as', ))
                _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as'), 'all'), True):
                    pass
                    l_1_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli), ' all', ))
                    _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as'), 'replace_as'), True):
                        pass
                        l_1_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli), ' replace-as', ))
                        _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                yield '   '
                yield str((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as'), 'enabled'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' remove-private-as\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'as_path'), 'prepend_own_disabled'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' as-path prepend-own disabled\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'as_path'), 'remote_as_replace_out'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' as-path remote-as replace out\n'
            if t_6(environment.getattr(l_1_peer_group, 'local_as')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' local-as '
                yield str(environment.getattr(l_1_peer_group, 'local_as'))
                yield ' no-prepend replace-as\n'
            if t_6(environment.getattr(l_1_peer_group, 'weight')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' weight '
                yield str(environment.getattr(l_1_peer_group, 'weight'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'passive'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' passive\n'
            if t_6(environment.getattr(l_1_peer_group, 'update_source')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' update-source '
                yield str(environment.getattr(l_1_peer_group, 'update_source'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'bfd'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' bfd\n'
                if ((t_6(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'interval')) and t_6(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'min_rx'))) and t_6(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'multiplier'))):
                    pass
                    yield '   neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' bfd interval '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'interval'))
                    yield ' min-rx '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'min_rx'))
                    yield ' multiplier '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'bfd_timers'), 'multiplier'))
                    yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'description')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' description '
                yield str(environment.getattr(l_1_peer_group, 'description'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'allowas_in'), 'enabled'), True):
                pass
                l_1_allowas_in_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' allowas-in', ))
                _loop_vars['allowas_in_cli'] = l_1_allowas_in_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'allowas_in'), 'times')):
                    pass
                    l_1_allowas_in_cli = str_join(((undefined(name='allowas_in_cli') if l_1_allowas_in_cli is missing else l_1_allowas_in_cli), ' ', environment.getattr(environment.getattr(l_1_peer_group, 'allowas_in'), 'times'), ))
                    _loop_vars['allowas_in_cli'] = l_1_allowas_in_cli
                yield '   '
                yield str((undefined(name='allowas_in_cli') if l_1_allowas_in_cli is missing else l_1_allowas_in_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'rib_in_pre_policy_retain'), 'enabled'), True):
                pass
                l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' rib-in pre-policy retain', ))
                _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'rib_in_pre_policy_retain'), 'all'), True):
                    pass
                    l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli), ' all', ))
                    _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                yield '   '
                yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'rib_in_pre_policy_retain'), 'enabled'), False):
                pass
                l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(('no neighbor ', environment.getattr(l_1_peer_group, 'name'), ' rib-in pre-policy retain', ))
                _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                yield '   '
                yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'ebgp_multihop')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' ebgp-multihop '
                yield str(environment.getattr(l_1_peer_group, 'ebgp_multihop'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'ttl_maximum_hops')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' ttl maximum-hops '
                yield str(environment.getattr(l_1_peer_group, 'ttl_maximum_hops'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'route_reflector_client'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' route-reflector-client\n'
            if t_6(environment.getattr(l_1_peer_group, 'session_tracker')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' session tracker '
                yield str(environment.getattr(l_1_peer_group, 'session_tracker'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'timers')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' timers '
                yield str(environment.getattr(l_1_peer_group, 'timers'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' route-map '
                yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                yield ' in\n'
            if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' route-map '
                yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                yield ' out\n'
            if t_6(environment.getattr(l_1_peer_group, 'password')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' password 7 '
                yield str(t_2(environment.getattr(l_1_peer_group, 'password'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                yield '\n'
            if (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'shared_secret'), 'profile')) and t_6(environment.getattr(environment.getattr(l_1_peer_group, 'shared_secret'), 'hash_algorithm'))):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' password shared-secret profile '
                yield str(environment.getattr(environment.getattr(l_1_peer_group, 'shared_secret'), 'profile'))
                yield ' algorithm '
                yield str(environment.getattr(environment.getattr(l_1_peer_group, 'shared_secret'), 'hash_algorithm'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'enabled'), True):
                pass
                l_1_default_originate_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-originate', ))
                _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'route_map')):
                    pass
                    l_1_default_originate_cli = str_join(((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'route_map'), ))
                    _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'always'), True):
                    pass
                    l_1_default_originate_cli = str_join(((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli), ' always', ))
                    _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                yield '   '
                yield str((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'send_community'), 'all'):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' send-community\n'
            elif t_6(environment.getattr(l_1_peer_group, 'send_community')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' send-community '
                yield str(environment.getattr(l_1_peer_group, 'send_community'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'maximum_routes')):
                pass
                l_1_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' maximum-routes ', environment.getattr(l_1_peer_group, 'maximum_routes'), ))
                _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                if t_6(environment.getattr(l_1_peer_group, 'maximum_routes_warning_limit')):
                    pass
                    l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-limit ', environment.getattr(l_1_peer_group, 'maximum_routes_warning_limit'), ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                if t_6(environment.getattr(l_1_peer_group, 'maximum_routes_warning_only'), True):
                    pass
                    l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-only', ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                yield '   '
                yield str((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'missing_policy')):
                pass
                for l_2_direction in ['in', 'out']:
                    l_2_missing_policy_cli = resolve('missing_policy_cli')
                    l_2_dir = l_2_policy = missing
                    _loop_vars = {}
                    pass
                    l_2_dir = str_join(('direction_', l_2_direction, ))
                    _loop_vars['dir'] = l_2_dir
                    l_2_policy = environment.getitem(environment.getattr(l_1_peer_group, 'missing_policy'), (undefined(name='dir') if l_2_dir is missing else l_2_dir))
                    _loop_vars['policy'] = l_2_policy
                    if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action')):
                        pass
                        l_2_missing_policy_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' missing-policy address-family all', ))
                        _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        if ((t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True)):
                            pass
                            l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' include', ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' community-list', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' prefix-list', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' sub-route-map', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' direction ', l_2_direction, ' action ', environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action'), ))
                        _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        yield '   '
                        yield str((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli))
                        yield '\n'
                l_2_direction = l_2_dir = l_2_policy = l_2_missing_policy_cli = missing
            if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' peer-tag in '
                yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                yield '\n'
            if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' peer-tag out discard '
                yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'link_bandwidth'), 'enabled'), True):
                pass
                l_1_link_bandwidth_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' link-bandwidth', ))
                _loop_vars['link_bandwidth_cli'] = l_1_link_bandwidth_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'link_bandwidth'), 'default')):
                    pass
                    l_1_link_bandwidth_cli = str_join(((undefined(name='link_bandwidth_cli') if l_1_link_bandwidth_cli is missing else l_1_link_bandwidth_cli), ' default ', environment.getattr(environment.getattr(l_1_peer_group, 'link_bandwidth'), 'default'), ))
                    _loop_vars['link_bandwidth_cli'] = l_1_link_bandwidth_cli
                yield '   '
                yield str((undefined(name='link_bandwidth_cli') if l_1_link_bandwidth_cli is missing else l_1_link_bandwidth_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as_ingress'), 'enabled'), True):
                pass
                l_1_remove_private_as_ingress_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' remove-private-as ingress', ))
                _loop_vars['remove_private_as_ingress_cli'] = l_1_remove_private_as_ingress_cli
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as_ingress'), 'replace_as'), True):
                    pass
                    l_1_remove_private_as_ingress_cli = str_join(((undefined(name='remove_private_as_ingress_cli') if l_1_remove_private_as_ingress_cli is missing else l_1_remove_private_as_ingress_cli), ' replace-as', ))
                    _loop_vars['remove_private_as_ingress_cli'] = l_1_remove_private_as_ingress_cli
                yield '   '
                yield str((undefined(name='remove_private_as_ingress_cli') if l_1_remove_private_as_ingress_cli is missing else l_1_remove_private_as_ingress_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'remove_private_as_ingress'), 'enabled'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_peer_group, 'name'))
                yield ' remove-private-as ingress\n'
        l_1_peer_group = l_1_remove_private_as_cli = l_1_allowas_in_cli = l_1_neighbor_rib_in_pre_policy_retain_cli = l_1_hide_passwords = l_1_default_originate_cli = l_1_maximum_routes_cli = l_1_link_bandwidth_cli = l_1_remove_private_as_ingress_cli = missing
        for l_1_neighbor in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbors'), 'ip_address'):
            l_1_remove_private_as_cli = resolve('remove_private_as_cli')
            l_1_allowas_in_cli = resolve('allowas_in_cli')
            l_1_neighbor_rib_in_pre_policy_retain_cli = resolve('neighbor_rib_in_pre_policy_retain_cli')
            l_1_hide_passwords = resolve('hide_passwords')
            l_1_default_originate_cli = resolve('default_originate_cli')
            l_1_maximum_routes_cli = resolve('maximum_routes_cli')
            l_1_link_bandwidth_cli = resolve('link_bandwidth_cli')
            l_1_remove_private_as_ingress_cli = resolve('remove_private_as_ingress_cli')
            _loop_vars = {}
            pass
            if t_6(environment.getattr(l_1_neighbor, 'peer_group')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' peer group '
                yield str(environment.getattr(l_1_neighbor, 'peer_group'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'remote_as')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' remote-as '
                yield str(environment.getattr(l_1_neighbor, 'remote_as'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'next_hop_self'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' next-hop-self\n'
            if t_6(environment.getattr(l_1_neighbor, 'next_hop_peer'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' next-hop-peer\n'
            if t_6(environment.getattr(l_1_neighbor, 'shutdown'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' shutdown\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as'), 'enabled'), True):
                pass
                l_1_remove_private_as_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' remove-private-as', ))
                _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as'), 'all'), True):
                    pass
                    l_1_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli), ' all', ))
                    _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as'), 'replace_as'), True):
                        pass
                        l_1_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli), ' replace-as', ))
                        _loop_vars['remove_private_as_cli'] = l_1_remove_private_as_cli
                yield '   '
                yield str((undefined(name='remove_private_as_cli') if l_1_remove_private_as_cli is missing else l_1_remove_private_as_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as'), 'enabled'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' remove-private-as\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'as_path'), 'prepend_own_disabled'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' as-path prepend-own disabled\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'as_path'), 'remote_as_replace_out'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' as-path remote-as replace out\n'
            if t_6(environment.getattr(l_1_neighbor, 'local_as')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' local-as '
                yield str(environment.getattr(l_1_neighbor, 'local_as'))
                yield ' no-prepend replace-as\n'
            if t_6(environment.getattr(l_1_neighbor, 'weight')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' weight '
                yield str(environment.getattr(l_1_neighbor, 'weight'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'passive'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' passive\n'
            if t_6(environment.getattr(l_1_neighbor, 'update_source')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' update-source '
                yield str(environment.getattr(l_1_neighbor, 'update_source'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'bfd'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' bfd\n'
                if ((t_6(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'interval')) and t_6(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'min_rx'))) and t_6(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'multiplier'))):
                    pass
                    yield '   neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' bfd interval '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'interval'))
                    yield ' min-rx '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'min_rx'))
                    yield ' multiplier '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'bfd_timers'), 'multiplier'))
                    yield '\n'
            elif (t_6(environment.getattr(l_1_neighbor, 'bfd'), False) and t_6(environment.getattr(l_1_neighbor, 'peer_group'))):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' bfd\n'
            if t_6(environment.getattr(l_1_neighbor, 'description')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' description '
                yield str(environment.getattr(l_1_neighbor, 'description'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'allowas_in'), 'enabled'), True):
                pass
                l_1_allowas_in_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' allowas-in', ))
                _loop_vars['allowas_in_cli'] = l_1_allowas_in_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'allowas_in'), 'times')):
                    pass
                    l_1_allowas_in_cli = str_join(((undefined(name='allowas_in_cli') if l_1_allowas_in_cli is missing else l_1_allowas_in_cli), ' ', environment.getattr(environment.getattr(l_1_neighbor, 'allowas_in'), 'times'), ))
                    _loop_vars['allowas_in_cli'] = l_1_allowas_in_cli
                yield '   '
                yield str((undefined(name='allowas_in_cli') if l_1_allowas_in_cli is missing else l_1_allowas_in_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'rib_in_pre_policy_retain'), 'enabled'), True):
                pass
                l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' rib-in pre-policy retain', ))
                _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'rib_in_pre_policy_retain'), 'all'), True):
                    pass
                    l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli), ' all', ))
                    _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                yield '   '
                yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'rib_in_pre_policy_retain'), 'enabled'), False):
                pass
                l_1_neighbor_rib_in_pre_policy_retain_cli = str_join(('no neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' rib-in pre-policy retain', ))
                _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_1_neighbor_rib_in_pre_policy_retain_cli
                yield '   '
                yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_1_neighbor_rib_in_pre_policy_retain_cli is missing else l_1_neighbor_rib_in_pre_policy_retain_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'ebgp_multihop')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' ebgp-multihop '
                yield str(environment.getattr(l_1_neighbor, 'ebgp_multihop'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'ttl_maximum_hops')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' ttl maximum-hops '
                yield str(environment.getattr(l_1_neighbor, 'ttl_maximum_hops'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'route_reflector_client'), True):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' route-reflector-client\n'
            elif t_6(environment.getattr(l_1_neighbor, 'route_reflector_client'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' route-reflector-client\n'
            if t_6(environment.getattr(l_1_neighbor, 'session_tracker')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' session tracker '
                yield str(environment.getattr(l_1_neighbor, 'session_tracker'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'timers')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' timers '
                yield str(environment.getattr(l_1_neighbor, 'timers'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' route-map '
                yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                yield ' in\n'
            if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' route-map '
                yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                yield ' out\n'
            if (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'shared_secret'), 'profile')) and t_6(environment.getattr(environment.getattr(l_1_neighbor, 'shared_secret'), 'hash_algorithm'))):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' password shared-secret profile '
                yield str(environment.getattr(environment.getattr(l_1_neighbor, 'shared_secret'), 'profile'))
                yield ' algorithm '
                yield str(environment.getattr(environment.getattr(l_1_neighbor, 'shared_secret'), 'hash_algorithm'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'password')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' password 7 '
                yield str(t_2(environment.getattr(l_1_neighbor, 'password'), (undefined(name='hide_passwords') if l_1_hide_passwords is missing else l_1_hide_passwords)))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'enabled'), True):
                pass
                l_1_default_originate_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-originate', ))
                _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'route_map')):
                    pass
                    l_1_default_originate_cli = str_join(((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'route_map'), ))
                    _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'always'), True):
                    pass
                    l_1_default_originate_cli = str_join(((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli), ' always', ))
                    _loop_vars['default_originate_cli'] = l_1_default_originate_cli
                yield '   '
                yield str((undefined(name='default_originate_cli') if l_1_default_originate_cli is missing else l_1_default_originate_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'send_community'), 'all'):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' send-community\n'
            elif t_6(environment.getattr(l_1_neighbor, 'send_community')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' send-community '
                yield str(environment.getattr(l_1_neighbor, 'send_community'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'maximum_routes')):
                pass
                l_1_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' maximum-routes ', environment.getattr(l_1_neighbor, 'maximum_routes'), ))
                _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                if t_6(environment.getattr(l_1_neighbor, 'maximum_routes_warning_limit')):
                    pass
                    l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-limit ', environment.getattr(l_1_neighbor, 'maximum_routes_warning_limit'), ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                if t_6(environment.getattr(l_1_neighbor, 'maximum_routes_warning_only'), True):
                    pass
                    l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-only', ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                yield '   '
                yield str((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'missing_policy')):
                pass
                for l_2_direction in ['in', 'out']:
                    l_2_missing_policy_cli = resolve('missing_policy_cli')
                    l_2_dir = l_2_policy = missing
                    _loop_vars = {}
                    pass
                    l_2_dir = str_join(('direction_', l_2_direction, ))
                    _loop_vars['dir'] = l_2_dir
                    l_2_policy = environment.getitem(environment.getattr(l_1_neighbor, 'missing_policy'), (undefined(name='dir') if l_2_dir is missing else l_2_dir))
                    _loop_vars['policy'] = l_2_policy
                    if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action')):
                        pass
                        l_2_missing_policy_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' missing-policy address-family all', ))
                        _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        if ((t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True)):
                            pass
                            l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' include', ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' community-list', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' prefix-list', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' sub-route-map', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' direction ', l_2_direction, ' action ', environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action'), ))
                        _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                        yield '   '
                        yield str((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli))
                        yield '\n'
                l_2_direction = l_2_dir = l_2_policy = l_2_missing_policy_cli = missing
            if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' peer-tag in '
                yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                yield '\n'
            if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                pass
                yield '   neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' peer-tag out discard '
                yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'link_bandwidth'), 'enabled'), True):
                pass
                l_1_link_bandwidth_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' link-bandwidth', ))
                _loop_vars['link_bandwidth_cli'] = l_1_link_bandwidth_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'link_bandwidth'), 'default')):
                    pass
                    l_1_link_bandwidth_cli = str_join(((undefined(name='link_bandwidth_cli') if l_1_link_bandwidth_cli is missing else l_1_link_bandwidth_cli), ' default ', environment.getattr(environment.getattr(l_1_neighbor, 'link_bandwidth'), 'default'), ))
                    _loop_vars['link_bandwidth_cli'] = l_1_link_bandwidth_cli
                yield '   '
                yield str((undefined(name='link_bandwidth_cli') if l_1_link_bandwidth_cli is missing else l_1_link_bandwidth_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as_ingress'), 'enabled'), True):
                pass
                l_1_remove_private_as_ingress_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' remove-private-as ingress', ))
                _loop_vars['remove_private_as_ingress_cli'] = l_1_remove_private_as_ingress_cli
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as_ingress'), 'replace_as'), True):
                    pass
                    l_1_remove_private_as_ingress_cli = str_join(((undefined(name='remove_private_as_ingress_cli') if l_1_remove_private_as_ingress_cli is missing else l_1_remove_private_as_ingress_cli), ' replace-as', ))
                    _loop_vars['remove_private_as_ingress_cli'] = l_1_remove_private_as_ingress_cli
                yield '   '
                yield str((undefined(name='remove_private_as_ingress_cli') if l_1_remove_private_as_ingress_cli is missing else l_1_remove_private_as_ingress_cli))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'remove_private_as_ingress'), 'enabled'), False):
                pass
                yield '   no neighbor '
                yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                yield ' remove-private-as ingress\n'
        l_1_neighbor = l_1_remove_private_as_cli = l_1_allowas_in_cli = l_1_neighbor_rib_in_pre_policy_retain_cli = l_1_hide_passwords = l_1_default_originate_cli = l_1_maximum_routes_cli = l_1_link_bandwidth_cli = l_1_remove_private_as_ingress_cli = missing
        if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'redistribute_internal'), True):
            pass
            yield '   bgp redistribute-internal\n'
        elif t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'bgp'), 'redistribute_internal'), False):
            pass
            yield '   no bgp redistribute-internal\n'
        for l_1_aggregate_address in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'aggregate_addresses'), 'prefix'):
            l_1_aggregate_address_cli = missing
            _loop_vars = {}
            pass
            l_1_aggregate_address_cli = str_join(('aggregate-address ', environment.getattr(l_1_aggregate_address, 'prefix'), ))
            _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'as_set'), True):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' as-set', ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'summary_only'), True):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' summary-only', ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'attribute_map')):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' attribute-map ', environment.getattr(l_1_aggregate_address, 'attribute_map'), ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'match_map')):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' match-map ', environment.getattr(l_1_aggregate_address, 'match_map'), ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            if t_6(environment.getattr(l_1_aggregate_address, 'advertise_only'), True):
                pass
                l_1_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli), ' advertise-only', ))
                _loop_vars['aggregate_address_cli'] = l_1_aggregate_address_cli
            yield '   '
            yield str((undefined(name='aggregate_address_cli') if l_1_aggregate_address_cli is missing else l_1_aggregate_address_cli))
            yield '\n'
        l_1_aggregate_address = l_1_aggregate_address_cli = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'redistribute')):
            pass
            l_0_redistribute_var = environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'redistribute')
            context.vars['redistribute_var'] = l_0_redistribute_var
            context.exported_vars.add('redistribute_var')
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                pass
                l_0_redistribute_conn = 'redistribute connected'
                context.vars['redistribute_conn'] = l_0_redistribute_conn
                context.exported_vars.add('redistribute_conn')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' include leaked', ))
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                    pass
                    l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf')):
                    pass
                    l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf'), ))
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                yield '   '
                yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                pass
                l_0_redistribute_isis = 'redistribute isis'
                context.vars['redistribute_isis'] = l_0_redistribute_isis
                context.exported_vars.add('redistribute_isis')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                    pass
                    l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                    pass
                    l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                    pass
                    l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                yield '   '
                yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'enabled'), True):
                pass
                l_0_redistribute_ospf = 'redistribute ospf'
                context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                context.exported_vars.add('redistribute_ospf')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' include leaked', ))
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map')):
                    pass
                    l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map'), ))
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                yield '   '
                yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                pass
                l_0_redistribute_ospf = 'redistribute ospf match internal'
                context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                context.exported_vars.add('redistribute_ospf')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' include leaked', ))
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                    pass
                    l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                yield '   '
                yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                pass
                l_0_redistribute_ospf_match = 'redistribute ospf match external'
                context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' include leaked', ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                yield '   '
                yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                pass
                l_0_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' include leaked', ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                    pass
                    l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                yield '   '
                yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                pass
                l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                context.exported_vars.add('redistribute_ospfv3')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                    pass
                    l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                yield '   '
                yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                yield '\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                pass
                l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                context.exported_vars.add('redistribute_ospfv3')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                    pass
                    l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                yield '   '
                yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                pass
                l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                yield '   '
                yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                pass
                l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                    pass
                    l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                yield '   '
                yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                pass
                l_0_redistribute_static = 'redistribute static'
                context.vars['redistribute_static'] = l_0_redistribute_static
                context.exported_vars.add('redistribute_static')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'include_leaked'), True):
                    pass
                    l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' include leaked', ))
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                    pass
                    l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf')):
                    pass
                    l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf'), ))
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                yield '   '
                yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'enabled'), True):
                pass
                l_0_redistribute_rip = 'redistribute rip'
                context.vars['redistribute_rip'] = l_0_redistribute_rip
                context.exported_vars.add('redistribute_rip')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'route_map')):
                    pass
                    l_0_redistribute_rip = str_join(((undefined(name='redistribute_rip') if l_0_redistribute_rip is missing else l_0_redistribute_rip), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'route_map'), ))
                    context.vars['redistribute_rip'] = l_0_redistribute_rip
                    context.exported_vars.add('redistribute_rip')
                yield '   '
                yield str((undefined(name='redistribute_rip') if l_0_redistribute_rip is missing else l_0_redistribute_rip))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'enabled'), True):
                pass
                l_0_redistribute_host = 'redistribute attached-host'
                context.vars['redistribute_host'] = l_0_redistribute_host
                context.exported_vars.add('redistribute_host')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map')):
                    pass
                    l_0_redistribute_host = str_join(((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map'), ))
                    context.vars['redistribute_host'] = l_0_redistribute_host
                    context.exported_vars.add('redistribute_host')
                yield '   '
                yield str((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'enabled'), True):
                pass
                l_0_redistribute_dynamic = 'redistribute dynamic'
                context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                context.exported_vars.add('redistribute_dynamic')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map')):
                    pass
                    l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map'), ))
                    context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                    context.exported_vars.add('redistribute_dynamic')
                elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf')):
                    pass
                    l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf'), ))
                    context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                    context.exported_vars.add('redistribute_dynamic')
                yield '   '
                yield str((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'enabled'), True):
                pass
                l_0_redistribute_bgp = 'redistribute bgp leaked'
                context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                context.exported_vars.add('redistribute_bgp')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map')):
                    pass
                    l_0_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map'), ))
                    context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                    context.exported_vars.add('redistribute_bgp')
                yield '   '
                yield str((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'enabled'), True):
                pass
                l_0_redistribute_user = 'redistribute user'
                context.vars['redistribute_user'] = l_0_redistribute_user
                context.exported_vars.add('redistribute_user')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf')):
                    pass
                    l_0_redistribute_user = str_join(((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf'), ))
                    context.vars['redistribute_user'] = l_0_redistribute_user
                    context.exported_vars.add('redistribute_user')
                yield '   '
                yield str((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user))
                yield '\n'
        for l_1_neighbor_interface in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'neighbor_interfaces'), 'name'):
            _loop_vars = {}
            pass
            if (t_6(environment.getattr(l_1_neighbor_interface, 'peer_group')) and t_6(environment.getattr(l_1_neighbor_interface, 'remote_as'))):
                pass
                yield '   neighbor interface '
                yield str(environment.getattr(l_1_neighbor_interface, 'name'))
                yield ' peer-group '
                yield str(environment.getattr(l_1_neighbor_interface, 'peer_group'))
                yield ' remote-as '
                yield str(environment.getattr(l_1_neighbor_interface, 'remote_as'))
                yield '\n'
            elif (t_6(environment.getattr(l_1_neighbor_interface, 'peer_group')) and t_6(environment.getattr(l_1_neighbor_interface, 'peer_filter'))):
                pass
                yield '   neighbor interface '
                yield str(environment.getattr(l_1_neighbor_interface, 'name'))
                yield ' peer-group '
                yield str(environment.getattr(l_1_neighbor_interface, 'peer_group'))
                yield ' peer-filter '
                yield str(environment.getattr(l_1_neighbor_interface, 'peer_filter'))
                yield '\n'
        l_1_neighbor_interface = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vlans')):
            pass
            for l_1_vlan in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vlans')):
                _loop_vars = {}
                pass
                yield '   !\n   vlan '
                yield str(environment.getattr(l_1_vlan, 'id'))
                yield '\n'
                if t_6(environment.getattr(l_1_vlan, 'rd')):
                    pass
                    yield '      rd '
                    yield str(environment.getattr(l_1_vlan, 'rd'))
                    yield '\n'
                if (t_6(environment.getattr(environment.getattr(l_1_vlan, 'rd_evpn_domain'), 'domain')) and t_6(environment.getattr(environment.getattr(l_1_vlan, 'rd_evpn_domain'), 'rd'))):
                    pass
                    yield '      rd evpn domain '
                    yield str(environment.getattr(environment.getattr(l_1_vlan, 'rd_evpn_domain'), 'domain'))
                    yield ' '
                    yield str(environment.getattr(environment.getattr(l_1_vlan, 'rd_evpn_domain'), 'rd'))
                    yield '\n'
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'both')):
                    _loop_vars = {}
                    pass
                    yield '      route-target both '
                    yield str(l_2_route_target)
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'import')):
                    _loop_vars = {}
                    pass
                    yield '      route-target import '
                    yield str(l_2_route_target)
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'export')):
                    _loop_vars = {}
                    pass
                    yield '      route-target export '
                    yield str(l_2_route_target)
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'import_evpn_domains')):
                    _loop_vars = {}
                    pass
                    yield '      route-target import evpn domain '
                    yield str(environment.getattr(l_2_route_target, 'domain'))
                    yield ' '
                    yield str(environment.getattr(l_2_route_target, 'route_target'))
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'export_evpn_domains')):
                    _loop_vars = {}
                    pass
                    yield '      route-target export evpn domain '
                    yield str(environment.getattr(l_2_route_target, 'domain'))
                    yield ' '
                    yield str(environment.getattr(l_2_route_target, 'route_target'))
                    yield '\n'
                l_2_route_target = missing
                for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan, 'route_targets'), 'import_export_evpn_domains')):
                    _loop_vars = {}
                    pass
                    yield '      route-target import export evpn domain '
                    yield str(environment.getattr(l_2_route_target, 'domain'))
                    yield ' '
                    yield str(environment.getattr(l_2_route_target, 'route_target'))
                    yield '\n'
                l_2_route_target = missing
                for l_2_redistribute_route in t_3(environment.getattr(l_1_vlan, 'redistribute_routes')):
                    _loop_vars = {}
                    pass
                    yield '      redistribute '
                    yield str(l_2_redistribute_route)
                    yield '\n'
                l_2_redistribute_route = missing
                for l_2_no_redistribute_route in t_3(environment.getattr(l_1_vlan, 'no_redistribute_routes')):
                    _loop_vars = {}
                    pass
                    yield '      no redistribute '
                    yield str(l_2_no_redistribute_route)
                    yield '\n'
                l_2_no_redistribute_route = missing
                if t_6(environment.getattr(l_1_vlan, 'eos_cli')):
                    pass
                    yield '      !\n      '
                    yield str(t_4(environment.getattr(l_1_vlan, 'eos_cli'), 6, False))
                    yield '\n'
            l_1_vlan = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vpws')):
            pass
            for l_1_vpws_service in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vpws'), 'name'):
                _loop_vars = {}
                pass
                yield '   !\n'
                if t_6(environment.getattr(l_1_vpws_service, 'name')):
                    pass
                    yield '   vpws '
                    yield str(environment.getattr(l_1_vpws_service, 'name'))
                    yield '\n'
                    if t_6(environment.getattr(l_1_vpws_service, 'rd')):
                        pass
                        yield '      rd '
                        yield str(environment.getattr(l_1_vpws_service, 'rd'))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(l_1_vpws_service, 'route_targets'), 'import_export')):
                        pass
                        yield '      route-target import export evpn '
                        yield str(environment.getattr(environment.getattr(l_1_vpws_service, 'route_targets'), 'import_export'))
                        yield '\n'
                    if t_6(environment.getattr(l_1_vpws_service, 'mpls_control_word'), True):
                        pass
                        yield '      mpls control-word\n'
                    if t_6(environment.getattr(l_1_vpws_service, 'label_flow'), True):
                        pass
                        yield '      label flow\n'
                    if t_6(environment.getattr(l_1_vpws_service, 'mtu')):
                        pass
                        yield '      mtu '
                        yield str(environment.getattr(l_1_vpws_service, 'mtu'))
                        yield '\n'
                    for l_2_pw in t_3(environment.getattr(l_1_vpws_service, 'pseudowires'), 'name'):
                        _loop_vars = {}
                        pass
                        if ((t_6(environment.getattr(l_2_pw, 'name')) and t_6(environment.getattr(l_2_pw, 'id_local'))) and t_6(environment.getattr(l_2_pw, 'id_remote'))):
                            pass
                            yield '      !\n      pseudowire '
                            yield str(environment.getattr(l_2_pw, 'name'))
                            yield '\n         evpn vpws id local '
                            yield str(environment.getattr(l_2_pw, 'id_local'))
                            yield ' remote '
                            yield str(environment.getattr(l_2_pw, 'id_remote'))
                            yield '\n'
                    l_2_pw = missing
            l_1_vpws_service = missing
        for l_1_vlan_aware_bundle in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vlan_aware_bundles'), 'name'):
            _loop_vars = {}
            pass
            yield '   !\n   vlan-aware-bundle '
            yield str(environment.getattr(l_1_vlan_aware_bundle, 'name'))
            yield '\n'
            if t_6(environment.getattr(l_1_vlan_aware_bundle, 'rd')):
                pass
                yield '      rd '
                yield str(environment.getattr(l_1_vlan_aware_bundle, 'rd'))
                yield '\n'
            if (t_6(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'rd_evpn_domain'), 'domain')) and t_6(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'rd_evpn_domain'), 'rd'))):
                pass
                yield '      rd evpn domain '
                yield str(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'rd_evpn_domain'), 'domain'))
                yield ' '
                yield str(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'rd_evpn_domain'), 'rd'))
                yield '\n'
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'both')):
                _loop_vars = {}
                pass
                yield '      route-target both '
                yield str(l_2_route_target)
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'import')):
                _loop_vars = {}
                pass
                yield '      route-target import '
                yield str(l_2_route_target)
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'export')):
                _loop_vars = {}
                pass
                yield '      route-target export '
                yield str(l_2_route_target)
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'import_evpn_domains')):
                _loop_vars = {}
                pass
                yield '      route-target import evpn domain '
                yield str(environment.getattr(l_2_route_target, 'domain'))
                yield ' '
                yield str(environment.getattr(l_2_route_target, 'route_target'))
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'export_evpn_domains')):
                _loop_vars = {}
                pass
                yield '      route-target export evpn domain '
                yield str(environment.getattr(l_2_route_target, 'domain'))
                yield ' '
                yield str(environment.getattr(l_2_route_target, 'route_target'))
                yield '\n'
            l_2_route_target = missing
            for l_2_route_target in t_3(environment.getattr(environment.getattr(l_1_vlan_aware_bundle, 'route_targets'), 'import_export_evpn_domains')):
                _loop_vars = {}
                pass
                yield '      route-target import export evpn domain '
                yield str(environment.getattr(l_2_route_target, 'domain'))
                yield ' '
                yield str(environment.getattr(l_2_route_target, 'route_target'))
                yield '\n'
            l_2_route_target = missing
            for l_2_redistribute_route in t_3(environment.getattr(l_1_vlan_aware_bundle, 'redistribute_routes')):
                _loop_vars = {}
                pass
                yield '      redistribute '
                yield str(l_2_redistribute_route)
                yield '\n'
            l_2_redistribute_route = missing
            for l_2_no_redistribute_route in t_3(environment.getattr(l_1_vlan_aware_bundle, 'no_redistribute_routes')):
                _loop_vars = {}
                pass
                yield '      no redistribute '
                yield str(l_2_no_redistribute_route)
                yield '\n'
            l_2_no_redistribute_route = missing
            yield '      vlan '
            yield str(environment.getattr(l_1_vlan_aware_bundle, 'vlan'))
            yield '\n'
            if t_6(environment.getattr(l_1_vlan_aware_bundle, 'eos_cli')):
                pass
                yield '      !\n      '
                yield str(t_4(environment.getattr(l_1_vlan_aware_bundle, 'eos_cli'), 6, False))
                yield '\n'
        l_1_vlan_aware_bundle = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn')):
            pass
            yield '   !\n   address-family evpn\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'route'), 'export_ethernet_segment_ip_mass_withdraw'), True):
                pass
                yield '      route export ethernet-segment ip mass-withdraw\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'route'), 'import_ethernet_segment_ip_mass_withdraw'), True):
                pass
                yield '      route import ethernet-segment ip mass-withdraw\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'next_hop_unchanged'), True):
                pass
                yield '      bgp next-hop-unchanged\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'encapsulation')):
                pass
                l_0_encapsulation_cli = str_join(('neighbor default encapsulation ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'encapsulation'), ))
                context.vars['encapsulation_cli'] = l_0_encapsulation_cli
                context.exported_vars.add('encapsulation_cli')
                if (t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'encapsulation'), 'mpls') and t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'next_hop_self_source_interface'))):
                    pass
                    l_0_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_0_encapsulation_cli is missing else l_0_encapsulation_cli), ' next-hop-self source-interface ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'next_hop_self_source_interface'), ))
                    context.vars['encapsulation_cli'] = l_0_encapsulation_cli
                    context.exported_vars.add('encapsulation_cli')
                yield '      '
                yield str((undefined(name='encapsulation_cli') if l_0_encapsulation_cli is missing else l_0_encapsulation_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'next_hop_mpls_resolution_ribs')):
                pass
                l_0_evpn_mpls_resolution_ribs = []
                context.vars['evpn_mpls_resolution_ribs'] = l_0_evpn_mpls_resolution_ribs
                context.exported_vars.add('evpn_mpls_resolution_ribs')
                for l_1_rib in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'next_hop_mpls_resolution_ribs'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_1_rib, 'rib_type'), 'tunnel-rib-colored'):
                        pass
                        context.call(environment.getattr((undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs), 'append'), 'tunnel-rib colored system-colored-tunnel-rib', _loop_vars=_loop_vars)
                    elif (t_6(environment.getattr(l_1_rib, 'rib_type'), 'tunnel-rib') and t_6(environment.getattr(l_1_rib, 'rib_name'))):
                        pass
                        context.call(environment.getattr((undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs), 'append'), str_join(('tunnel-rib ', environment.getattr(l_1_rib, 'rib_name'), )), _loop_vars=_loop_vars)
                    elif t_6(environment.getattr(l_1_rib, 'rib_type')):
                        pass
                        context.call(environment.getattr((undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs), 'append'), environment.getattr(l_1_rib, 'rib_type'), _loop_vars=_loop_vars)
                l_1_rib = missing
                if (undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs):
                    pass
                    yield '      next-hop mpls resolution ribs '
                    yield str(t_5(context.eval_ctx, (undefined(name='evpn_mpls_resolution_ribs') if l_0_evpn_mpls_resolution_ribs is missing else l_0_evpn_mpls_resolution_ribs), ' '))
                    yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'peer_groups'), 'name'):
                l_1_peer_group_default_route_cli = resolve('peer_group_default_route_cli')
                l_1_encapsulation_cli = l_0_encapsulation_cli
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'enabled'), True):
                    pass
                    l_1_peer_group_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-route', ))
                    _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    yield '      '
                    yield str((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_peer_group, 'name'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'encapsulation')):
                    pass
                    l_1_encapsulation_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' encapsulation ', environment.getattr(l_1_peer_group, 'encapsulation'), ))
                    _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    if ((environment.getattr(l_1_peer_group, 'encapsulation') == 'mpls') and t_6(environment.getattr(l_1_peer_group, 'next_hop_self_source_interface'))):
                        pass
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' next-hop-self source-interface ', environment.getattr(l_1_peer_group, 'next_hop_self_source_interface'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    yield '      '
                    yield str((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'domain_remote'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' domain remote\n'
            l_1_peer_group = l_1_peer_group_default_route_cli = l_1_encapsulation_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbors'), 'ip_address'):
                l_1_neighbor_default_route_cli = resolve('neighbor_default_route_cli')
                l_1_encapsulation_cli = l_0_encapsulation_cli
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'enabled'), True):
                    pass
                    l_1_neighbor_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-route', ))
                    _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'encapsulation')):
                    pass
                    l_1_encapsulation_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' encapsulation ', environment.getattr(l_1_neighbor, 'encapsulation'), ))
                    _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    if ((environment.getattr(l_1_neighbor, 'encapsulation') == 'mpls') and t_6(environment.getattr(l_1_neighbor, 'next_hop_self_source_interface'))):
                        pass
                        l_1_encapsulation_cli = str_join(((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli), ' next-hop-self source-interface ', environment.getattr(l_1_neighbor, 'next_hop_self_source_interface'), ))
                        _loop_vars['encapsulation_cli'] = l_1_encapsulation_cli
                    yield '      '
                    yield str((undefined(name='encapsulation_cli') if l_1_encapsulation_cli is missing else l_1_encapsulation_cli))
                    yield '\n'
            l_1_neighbor = l_1_neighbor_default_route_cli = l_1_encapsulation_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'domain_identifier')):
                pass
                yield '      domain identifier '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'domain_identifier'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'domain_identifier_remote')):
                pass
                yield '      domain identifier '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'domain_identifier_remote'))
                yield ' remote\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'next_hop'), 'resolution_disabled'), True):
                pass
                yield '      next-hop resolution disabled\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'route'), 'import_match_failure_action'), 'discard'):
                pass
                yield '      route import match-failure action discard\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'next_hop_self_received_evpn_routes'), 'enable'), True):
                pass
                l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli = 'neighbor default next-hop-self received-evpn-routes route-type ip-prefix'
                context.vars['evpn_neighbor_default_nhs_received_evpn_routes_cli'] = l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli
                context.exported_vars.add('evpn_neighbor_default_nhs_received_evpn_routes_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'neighbor_default'), 'next_hop_self_received_evpn_routes'), 'inter_domain'), True):
                    pass
                    l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli = str_join(((undefined(name='evpn_neighbor_default_nhs_received_evpn_routes_cli') if l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli is missing else l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli), ' inter-domain', ))
                    context.vars['evpn_neighbor_default_nhs_received_evpn_routes_cli'] = l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli
                    context.exported_vars.add('evpn_neighbor_default_nhs_received_evpn_routes_cli')
                yield '      '
                yield str((undefined(name='evpn_neighbor_default_nhs_received_evpn_routes_cli') if l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli is missing else l_0_evpn_neighbor_default_nhs_received_evpn_routes_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'enabled'), False):
                pass
                yield '      no host-flap detection\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'enabled'), True):
                pass
                l_0_hostflap_detection_cli = ''
                context.vars['hostflap_detection_cli'] = l_0_hostflap_detection_cli
                context.exported_vars.add('hostflap_detection_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'window')):
                    pass
                    l_0_hostflap_detection_cli = str_join(((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli), ' window ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'window'), ))
                    context.vars['hostflap_detection_cli'] = l_0_hostflap_detection_cli
                    context.exported_vars.add('hostflap_detection_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'threshold')):
                    pass
                    l_0_hostflap_detection_cli = str_join(((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli), ' threshold ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'threshold'), ))
                    context.vars['hostflap_detection_cli'] = l_0_hostflap_detection_cli
                    context.exported_vars.add('hostflap_detection_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'expiry_timeout')):
                    pass
                    l_0_hostflap_detection_cli = str_join(((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli), ' expiry timeout ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_hostflap_detection'), 'expiry_timeout'), ' seconds', ))
                    context.vars['hostflap_detection_cli'] = l_0_hostflap_detection_cli
                    context.exported_vars.add('hostflap_detection_cli')
                if ((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli) != ''):
                    pass
                    yield '      host-flap detection'
                    yield str((undefined(name='hostflap_detection_cli') if l_0_hostflap_detection_cli is missing else l_0_hostflap_detection_cli))
                    yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'layer_2_fec_in_place_update'), 'enabled'), True):
                pass
                l_0_layer2_cli = 'layer-2 fec in-place update'
                context.vars['layer2_cli'] = l_0_layer2_cli
                context.exported_vars.add('layer2_cli')
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'layer_2_fec_in_place_update'), 'timeout')):
                    pass
                    l_0_layer2_cli = str_join(((undefined(name='layer2_cli') if l_0_layer2_cli is missing else l_0_layer2_cli), ' timeout ', environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'layer_2_fec_in_place_update'), 'timeout'), ' seconds', ))
                    context.vars['layer2_cli'] = l_0_layer2_cli
                    context.exported_vars.add('layer2_cli')
                yield '      '
                yield str((undefined(name='layer2_cli') if l_0_layer2_cli is missing else l_0_layer2_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'route'), 'import_overlay_index_gateway'), True):
                pass
                yield '      route import overlay-index gateway\n'
            for l_1_segment in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_evpn'), 'evpn_ethernet_segment'), 'domain'):
                _loop_vars = {}
                pass
                yield '      !\n      evpn ethernet-segment domain '
                yield str(environment.getattr(l_1_segment, 'domain'))
                yield '\n'
                if t_6(environment.getattr(l_1_segment, 'identifier')):
                    pass
                    yield '         identifier '
                    yield str(environment.getattr(l_1_segment, 'identifier'))
                    yield '\n'
                if t_6(environment.getattr(l_1_segment, 'route_target_import')):
                    pass
                    yield '         route-target import '
                    yield str(environment.getattr(l_1_segment, 'route_target_import'))
                    yield '\n'
            l_1_segment = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4')):
            pass
            yield '   !\n   address-family flow-spec ipv4\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                pass
                yield '      bgp missing-policy direction in action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                pass
                yield '      bgp missing-policy direction out action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv4'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6')):
            pass
            yield '   !\n   address-family flow-spec ipv6\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                pass
                yield '      bgp missing-policy direction in action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                pass
                yield '      bgp missing-policy direction out action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_flow_spec_ipv6'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4')):
            pass
            yield '   !\n   address-family ipv4\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'install'), True):
                pass
                yield '      bgp additional-paths install\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                pass
                yield '      bgp additional-paths install ecmp-primary\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'peer_groups'), 'name'):
                l_1_neighbor_default_originate_cli = resolve('neighbor_default_originate_cli')
                l_1_add_path_cli = resolve('add_path_cli')
                l_1_nexthop_v6_cli = resolve('nexthop_v6_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'prefix_list_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_peer_group, 'prefix_list_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'prefix_list_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_peer_group, 'prefix_list_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'default_originate')):
                    pass
                    l_1_neighbor_default_originate_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-originate', ))
                    _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'route_map')):
                        pass
                        l_1_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'route_map'), ))
                        _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_originate'), 'always'), True):
                        pass
                        l_1_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli), ' always', ))
                        _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send\n'
                    else:
                        pass
                        if (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send ecmp limit ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        elif (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')):
                                pass
                                l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send limit ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'), ))
                                _loop_vars['add_path_cli'] = l_1_add_path_cli
                        else:
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'prefix_list')) and t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))):
                            pass
                            l_1_add_path_cli = str_join(((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli), ' prefix-list ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'prefix_list'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli)):
                            pass
                            yield '      '
                            yield str((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))
                            yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_peer_group, 'next_hop'), 'address_family_ipv6'), 'enabled'), True):
                    pass
                    l_1_nexthop_v6_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' next-hop address-family ipv6', ))
                    _loop_vars['nexthop_v6_cli'] = l_1_nexthop_v6_cli
                    if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_peer_group, 'next_hop'), 'address_family_ipv6'), 'originate'), True):
                        pass
                        l_1_nexthop_v6_cli = str_join(((undefined(name='nexthop_v6_cli') if l_1_nexthop_v6_cli is missing else l_1_nexthop_v6_cli), ' originate', ))
                        _loop_vars['nexthop_v6_cli'] = l_1_nexthop_v6_cli
                    yield '      '
                    yield str((undefined(name='nexthop_v6_cli') if l_1_nexthop_v6_cli is missing else l_1_nexthop_v6_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = l_1_neighbor_default_originate_cli = l_1_add_path_cli = l_1_nexthop_v6_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'neighbors'), 'ip_address'):
                l_1_neighbor_default_originate_cli = resolve('neighbor_default_originate_cli')
                l_1_add_path_cli = resolve('add_path_cli')
                l_1_ipv6_originate_cli = resolve('ipv6_originate_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'prefix_list_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_neighbor, 'prefix_list_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'prefix_list_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_neighbor, 'prefix_list_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'default_originate')):
                    pass
                    l_1_neighbor_default_originate_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-originate', ))
                    _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'route_map')):
                        pass
                        l_1_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'route_map'), ))
                        _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_originate'), 'always'), True):
                        pass
                        l_1_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli), ' always', ))
                        _loop_vars['neighbor_default_originate_cli'] = l_1_neighbor_default_originate_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_originate_cli') if l_1_neighbor_default_originate_cli is missing else l_1_neighbor_default_originate_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    else:
                        pass
                        if (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send ecmp limit ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                                pass
                                l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send limit ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'), ))
                                _loop_vars['add_path_cli'] = l_1_add_path_cli
                        else:
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'prefix_list')):
                            pass
                            l_1_add_path_cli = str_join(((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli), ' prefix-list ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'prefix_list'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli)):
                            pass
                            yield '      '
                            yield str((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))
                            yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_neighbor, 'next_hop'), 'address_family_ipv6'), 'enabled')):
                    pass
                    if environment.getattr(environment.getattr(environment.getattr(l_1_neighbor, 'next_hop'), 'address_family_ipv6'), 'enabled'):
                        pass
                        l_1_ipv6_originate_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' next-hop address-family ipv6', ))
                        _loop_vars['ipv6_originate_cli'] = l_1_ipv6_originate_cli
                        if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_neighbor, 'next_hop'), 'address_family_ipv6'), 'originate'), True):
                            pass
                            l_1_ipv6_originate_cli = str_join(((undefined(name='ipv6_originate_cli') if l_1_ipv6_originate_cli is missing else l_1_ipv6_originate_cli), ' originate', ))
                            _loop_vars['ipv6_originate_cli'] = l_1_ipv6_originate_cli
                        yield '      '
                        yield str((undefined(name='ipv6_originate_cli') if l_1_ipv6_originate_cli is missing else l_1_ipv6_originate_cli))
                        yield '\n'
                    else:
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' next-hop address-family ipv6\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = l_1_neighbor_default_originate_cli = l_1_add_path_cli = l_1_ipv6_originate_cli = missing
            for l_1_network in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'networks'), 'prefix'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_network, 'route_map')):
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_1_network, 'prefix'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_network, 'route_map'))
                    yield '\n'
                else:
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_1_network, 'prefix'))
                    yield '\n'
            l_1_network = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'redistribute_internal'), True):
                pass
                yield '      bgp redistribute-internal\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'bgp'), 'redistribute_internal'), False):
                pass
                yield '      no bgp redistribute-internal\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'redistribute')):
                pass
                l_0_redistribute_var = environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4'), 'redistribute')
                context.vars['redistribute_var'] = l_0_redistribute_var
                context.exported_vars.add('redistribute_var')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'enabled'), True):
                    pass
                    l_0_redistribute_host = 'redistribute attached-host'
                    context.vars['redistribute_host'] = l_0_redistribute_host
                    context.exported_vars.add('redistribute_host')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map')):
                        pass
                        l_0_redistribute_host = str_join(((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map'), ))
                        context.vars['redistribute_host'] = l_0_redistribute_host
                        context.exported_vars.add('redistribute_host')
                    yield '      '
                    yield str((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'enabled'), True):
                    pass
                    l_0_redistribute_bgp = 'redistribute bgp leaked'
                    context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                    context.exported_vars.add('redistribute_bgp')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map')):
                        pass
                        l_0_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map'), ))
                        context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                        context.exported_vars.add('redistribute_bgp')
                    yield '      '
                    yield str((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_0_redistribute_conn = 'redistribute connected'
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' include leaked', ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'enabled'), True):
                    pass
                    l_0_redistribute_dynamic = 'redistribute dynamic'
                    context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                    context.exported_vars.add('redistribute_dynamic')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map')):
                        pass
                        l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map'), ))
                        context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                        context.exported_vars.add('redistribute_dynamic')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf')):
                        pass
                        l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf'), ))
                        context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                        context.exported_vars.add('redistribute_dynamic')
                    yield '      '
                    yield str((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'enabled'), True):
                    pass
                    l_0_redistribute_user = 'redistribute user'
                    context.vars['redistribute_user'] = l_0_redistribute_user
                    context.exported_vars.add('redistribute_user')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf')):
                        pass
                        l_0_redistribute_user = str_join(((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf'), ))
                        context.vars['redistribute_user'] = l_0_redistribute_user
                        context.exported_vars.add('redistribute_user')
                    yield '      '
                    yield str((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_0_redistribute_isis = 'redistribute isis'
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' include leaked', ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf match internal'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' include leaked', ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' include leaked', ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' include leaked', ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'enabled'), True):
                    pass
                    l_0_redistribute_rip = 'redistribute rip'
                    context.vars['redistribute_rip'] = l_0_redistribute_rip
                    context.exported_vars.add('redistribute_rip')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'route_map')):
                        pass
                        l_0_redistribute_rip = str_join(((undefined(name='redistribute_rip') if l_0_redistribute_rip is missing else l_0_redistribute_rip), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'rip'), 'route_map'), ))
                        context.vars['redistribute_rip'] = l_0_redistribute_rip
                        context.exported_vars.add('redistribute_rip')
                    yield '      '
                    yield str((undefined(name='redistribute_rip') if l_0_redistribute_rip is missing else l_0_redistribute_rip))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_0_redistribute_static = 'redistribute static'
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' include leaked', ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                    yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast')):
            pass
            yield '   !\n   address-family ipv4 labeled-unicast\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'update_wait_for_convergence'), True):
                pass
                yield '      update wait-for-convergence\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'missing_policy')):
                pass
                for l_1_direction in ['in', 'out']:
                    l_1_missing_policy_cli = resolve('missing_policy_cli')
                    l_1_dir = l_1_policy = missing
                    _loop_vars = {}
                    pass
                    l_1_dir = str_join(('direction_', l_1_direction, ))
                    _loop_vars['dir'] = l_1_dir
                    l_1_policy = environment.getitem(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'missing_policy'), (undefined(name='dir') if l_1_dir is missing else l_1_dir))
                    _loop_vars['policy'] = l_1_policy
                    if t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'action')):
                        pass
                        l_1_missing_policy_cli = 'bgp missing-policy'
                        _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                        if ((t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_sub_route_map'), True)):
                            pass
                            l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' include', ))
                            _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_community_list'), True):
                                pass
                                l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' community-list', ))
                                _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_prefix_list'), True):
                                pass
                                l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' prefix-list', ))
                                _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                            if t_6(environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'include_sub_route_map'), True):
                                pass
                                l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' sub-route-map', ))
                                _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                        l_1_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli), ' direction ', l_1_direction, ' action ', environment.getattr((undefined(name='policy') if l_1_policy is missing else l_1_policy), 'action'), ))
                        _loop_vars['missing_policy_cli'] = l_1_missing_policy_cli
                        yield '      '
                        yield str((undefined(name='missing_policy_cli') if l_1_missing_policy_cli is missing else l_1_missing_policy_cli))
                        yield '\n'
                l_1_direction = l_1_dir = l_1_policy = l_1_missing_policy_cli = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'bgp'), 'next_hop_unchanged'), True):
                pass
                yield '      bgp next-hop-unchanged\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'neighbor_default'), 'next_hop_self'), True):
                pass
                yield '      neighbor default next-hop-self\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'next_hop_resolution_ribs')):
                pass
                l_0_v4_bgp_lu_resolution_ribs = []
                context.vars['v4_bgp_lu_resolution_ribs'] = l_0_v4_bgp_lu_resolution_ribs
                context.exported_vars.add('v4_bgp_lu_resolution_ribs')
                for l_1_rib in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'next_hop_resolution_ribs'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_1_rib, 'rib_type'), 'tunnel-rib-colored'):
                        pass
                        context.call(environment.getattr((undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs), 'append'), 'tunnel-rib colored system-colored-tunnel-rib', _loop_vars=_loop_vars)
                    elif t_6(environment.getattr(l_1_rib, 'rib_type'), 'tunnel-rib'):
                        pass
                        if t_6(environment.getattr(l_1_rib, 'rib_name')):
                            pass
                            context.call(environment.getattr((undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs), 'append'), str_join(('tunnel-rib ', environment.getattr(l_1_rib, 'rib_name'), )), _loop_vars=_loop_vars)
                    elif t_6(environment.getattr(l_1_rib, 'rib_type')):
                        pass
                        context.call(environment.getattr((undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs), 'append'), environment.getattr(l_1_rib, 'rib_type'), _loop_vars=_loop_vars)
                l_1_rib = missing
                if (undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs):
                    pass
                    yield '      next-hop resolution ribs '
                    yield str(t_5(context.eval_ctx, (undefined(name='v4_bgp_lu_resolution_ribs') if l_0_v4_bgp_lu_resolution_ribs is missing else l_0_v4_bgp_lu_resolution_ribs), ' '))
                    yield '\n'
            for l_1_peer in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'peer_groups'), 'name'):
                l_1_maximum_routes_cli = resolve('maximum_routes_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' activate\n'
                else:
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer, 'graceful_restart'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' graceful-restart\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer, 'graceful_restart_helper'), 'stale_route_map')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' graceful-restart-helper stale-route route-map '
                    yield str(environment.getattr(environment.getattr(l_1_peer, 'graceful_restart_helper'), 'stale_route_map'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer, 'name'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer, 'name'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_peer, 'name'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer, 'name'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_peer, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_1_peer, 'next_hop_unchanged'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' next-hop-unchanged\n'
                if t_6(environment.getattr(l_1_peer, 'next_hop_self'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' next-hop-self\n'
                if t_6(environment.getattr(l_1_peer, 'next_hop_self_v4_mapped_v6_source_interface')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' next-hop-self v4-mapped-v6 source-interface '
                    yield str(environment.getattr(l_1_peer, 'next_hop_self_v4_mapped_v6_source_interface'))
                    yield '\n'
                elif t_6(environment.getattr(l_1_peer, 'next_hop_self_source_interface')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' next-hop-self source-interface '
                    yield str(environment.getattr(l_1_peer, 'next_hop_self_source_interface'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'maximum_advertised_routes')):
                    pass
                    l_1_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_1_peer, 'name'), ' maximum-advertised-routes ', environment.getattr(l_1_peer, 'maximum_advertised_routes'), ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                    if t_6(environment.getattr(l_1_peer, 'maximum_advertised_routes_warning_limit')):
                        pass
                        l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-limit ', environment.getattr(l_1_peer, 'maximum_advertised_routes_warning_limit'), ))
                        _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                    yield '      '
                    yield str((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'missing_policy')):
                    pass
                    for l_2_direction in ['in', 'out']:
                        l_2_missing_policy_cli = resolve('missing_policy_cli')
                        l_2_dir = l_2_policy = missing
                        _loop_vars = {}
                        pass
                        l_2_dir = str_join(('direction_', l_2_direction, ))
                        _loop_vars['dir'] = l_2_dir
                        l_2_policy = environment.getitem(environment.getattr(l_1_peer, 'missing_policy'), (undefined(name='dir') if l_2_dir is missing else l_2_dir))
                        _loop_vars['policy'] = l_2_policy
                        if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action')):
                            pass
                            l_2_missing_policy_cli = str_join(('neighbor ', environment.getattr(l_1_peer, 'name'), ' missing-policy', ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if ((t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True)):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' include', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' community-list', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' prefix-list', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' sub-route-map', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' direction ', l_2_direction, ' action ', environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action'), ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            yield '      '
                            yield str((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli))
                            yield '\n'
                    l_2_direction = l_2_dir = l_2_policy = l_2_missing_policy_cli = missing
                if t_6(environment.getattr(l_1_peer, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer, 'aigp_session'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' aigp-session\n'
                if t_6(environment.getattr(l_1_peer, 'multi_path'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer, 'name'))
                    yield ' multi-path\n'
            l_1_peer = l_1_maximum_routes_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'neighbors'), 'ip_address'):
                l_1_maximum_routes_cli = resolve('maximum_routes_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                else:
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'graceful_restart'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' graceful-restart\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'graceful_restart_helper'), 'stale_route_map')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' graceful-restart-helper stale-route route-map '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'graceful_restart_helper'), 'stale_route_map'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'next_hop_unchanged'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' next-hop-unchanged\n'
                if t_6(environment.getattr(l_1_neighbor, 'next_hop_self'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' next-hop-self\n'
                if t_6(environment.getattr(l_1_neighbor, 'next_hop_self_v4_mapped_v6_source_interface')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' next-hop-self v4-mapped-v6 source-interface '
                    yield str(environment.getattr(l_1_neighbor, 'next_hop_self_v4_mapped_v6_source_interface'))
                    yield '\n'
                elif t_6(environment.getattr(l_1_neighbor, 'next_hop_self_source_interface')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' next-hop-self source-interface '
                    yield str(environment.getattr(l_1_neighbor, 'next_hop_self_source_interface'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'maximum_advertised_routes')):
                    pass
                    l_1_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' maximum-advertised-routes ', environment.getattr(l_1_neighbor, 'maximum_advertised_routes'), ))
                    _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                    if t_6(environment.getattr(l_1_neighbor, 'maximum_advertised_routes_warning_limit')):
                        pass
                        l_1_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli), ' warning-limit ', environment.getattr(l_1_neighbor, 'maximum_advertised_routes_warning_limit'), ))
                        _loop_vars['maximum_routes_cli'] = l_1_maximum_routes_cli
                    yield '      '
                    yield str((undefined(name='maximum_routes_cli') if l_1_maximum_routes_cli is missing else l_1_maximum_routes_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'missing_policy')):
                    pass
                    for l_2_direction in ['in', 'out']:
                        l_2_missing_policy_cli = resolve('missing_policy_cli')
                        l_2_dir = l_2_policy = missing
                        _loop_vars = {}
                        pass
                        l_2_dir = str_join(('direction_', l_2_direction, ))
                        _loop_vars['dir'] = l_2_dir
                        l_2_policy = environment.getitem(environment.getattr(l_1_neighbor, 'missing_policy'), (undefined(name='dir') if l_2_dir is missing else l_2_dir))
                        _loop_vars['policy'] = l_2_policy
                        if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action')):
                            pass
                            l_2_missing_policy_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' missing-policy ', ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            if ((t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True)) or t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True)):
                                pass
                                l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' include', ))
                                _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_community_list'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' community-list', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_prefix_list'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' prefix-list', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                                if t_6(environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'include_sub_route_map'), True):
                                    pass
                                    l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' sub-route-map', ))
                                    _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            l_2_missing_policy_cli = str_join(((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli), ' direction ', l_2_direction, ' action ', environment.getattr((undefined(name='policy') if l_2_policy is missing else l_2_policy), 'action'), ))
                            _loop_vars['missing_policy_cli'] = l_2_missing_policy_cli
                            yield '      '
                            yield str((undefined(name='missing_policy_cli') if l_2_missing_policy_cli is missing else l_2_missing_policy_cli))
                            yield '\n'
                    l_2_direction = l_2_dir = l_2_policy = l_2_missing_policy_cli = missing
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'aigp_session'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' aigp-session\n'
                if t_6(environment.getattr(l_1_neighbor, 'multi_path'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' multi-path\n'
            l_1_neighbor = l_1_maximum_routes_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'networks')):
                pass
                for l_1_network in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'networks'):
                    l_1_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_network_cli = str_join(('network ', environment.getattr(l_1_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_1_network_cli
                    if t_6(environment.getattr(l_1_network, 'route_map')):
                        pass
                        l_1_network_cli = str_join(((undefined(name='network_cli') if l_1_network_cli is missing else l_1_network_cli), ' route-map ', environment.getattr(l_1_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_1_network_cli
                    yield '      '
                    yield str((undefined(name='network_cli') if l_1_network_cli is missing else l_1_network_cli))
                    yield '\n'
                l_1_network = l_1_network_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'next_hops')):
                pass
                for l_1_next_hop in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'next_hops'):
                    l_1_next_hop_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_next_hop_cli = str_join(('next-hop ', environment.getattr(l_1_next_hop, 'ip_address'), ' originate', ))
                    _loop_vars['next_hop_cli'] = l_1_next_hop_cli
                    if t_6(environment.getattr(l_1_next_hop, 'lfib_backup_ip_forwarding'), True):
                        pass
                        l_1_next_hop_cli = str_join(((undefined(name='next_hop_cli') if l_1_next_hop_cli is missing else l_1_next_hop_cli), ' lfib-backup ip-forwarding', ))
                        _loop_vars['next_hop_cli'] = l_1_next_hop_cli
                    yield '      '
                    yield str((undefined(name='next_hop_cli') if l_1_next_hop_cli is missing else l_1_next_hop_cli))
                    yield '\n'
                l_1_next_hop = l_1_next_hop_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'lfib_entry_installation_skipped'), True):
                pass
                yield '      lfib entry installation skipped\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'label_local_termination')):
                pass
                yield '      label local-termination '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'label_local_termination'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'graceful_restart'), True):
                pass
                yield '      graceful-restart\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'tunnel_source_protocols')):
                pass
                for l_1_tunnel_source_protocol in environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'tunnel_source_protocols'):
                    l_1_tunnel_source_protocol_cli = missing
                    _loop_vars = {}
                    pass
                    l_1_tunnel_source_protocol_cli = str_join(('tunnel source-protocol ', environment.getattr(l_1_tunnel_source_protocol, 'protocol'), ))
                    _loop_vars['tunnel_source_protocol_cli'] = l_1_tunnel_source_protocol_cli
                    if t_6(environment.getattr(l_1_tunnel_source_protocol, 'rcf')):
                        pass
                        l_1_tunnel_source_protocol_cli = str_join(((undefined(name='tunnel_source_protocol_cli') if l_1_tunnel_source_protocol_cli is missing else l_1_tunnel_source_protocol_cli), ' rcf ', environment.getattr(l_1_tunnel_source_protocol, 'rcf'), ))
                        _loop_vars['tunnel_source_protocol_cli'] = l_1_tunnel_source_protocol_cli
                    yield '      '
                    yield str((undefined(name='tunnel_source_protocol_cli') if l_1_tunnel_source_protocol_cli is missing else l_1_tunnel_source_protocol_cli))
                    yield '\n'
                l_1_tunnel_source_protocol = l_1_tunnel_source_protocol_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'aigp_session')):
                pass
                for l_1_aigp_session_type in ['ibgp', 'confederation', 'ebgp']:
                    _loop_vars = {}
                    pass
                    if t_6(environment.getitem(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_labeled_unicast'), 'aigp_session'), l_1_aigp_session_type), True):
                        pass
                        yield '      aigp-session '
                        yield str(l_1_aigp_session_type)
                        yield '\n'
                l_1_aigp_session_type = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast')):
            pass
            yield '   !\n   address-family ipv4 multicast\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'redistribute')):
                pass
                l_0_redistribute_var = environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_multicast'), 'redistribute')
                context.vars['redistribute_var'] = l_0_redistribute_var
                context.exported_vars.add('redistribute_var')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'enabled'), True):
                    pass
                    l_0_redistribute_host = 'redistribute attached-host'
                    context.vars['redistribute_host'] = l_0_redistribute_host
                    context.exported_vars.add('redistribute_host')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map')):
                        pass
                        l_0_redistribute_host = str_join(((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map'), ))
                        context.vars['redistribute_host'] = l_0_redistribute_host
                        context.exported_vars.add('redistribute_host')
                    yield '      '
                    yield str((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_0_redistribute_conn = 'redistribute connected'
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_0_redistribute_isis = 'redistribute isis'
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf match internal'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_0_redistribute_static = 'redistribute static'
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                    yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_sr_te')):
            pass
            yield '   !\n   address-family ipv4 sr-te\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_sr_te'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv4_sr_te'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6')):
            pass
            yield '   !\n   address-family ipv6\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'install'), True):
                pass
                yield '      bgp additional-paths install\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                pass
                yield '      bgp additional-paths install ecmp-primary\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'peer_groups'), 'name'):
                l_1_add_path_cli = resolve('add_path_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'prefix_list_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_peer_group, 'prefix_list_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'prefix_list_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_peer_group, 'prefix_list_out'))
                    yield ' out\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send\n'
                    else:
                        pass
                        if (t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send ecmp limit ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        elif (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')):
                                pass
                                l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send limit ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'), ))
                                _loop_vars['add_path_cli'] = l_1_add_path_cli
                        else:
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' additional-paths send ', environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'prefix_list')):
                            pass
                            l_1_add_path_cli = str_join(((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli), ' prefix-list ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'prefix_list'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli)):
                            pass
                            yield '      '
                            yield str((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))
                            yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = l_1_add_path_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'neighbors'), 'ip_address'):
                l_1_add_path_cli = resolve('add_path_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'prefix_list_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_neighbor, 'prefix_list_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'prefix_list_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' prefix-list '
                    yield str(environment.getattr(l_1_neighbor, 'prefix_list_out'))
                    yield ' out\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    else:
                        pass
                        if (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send ecmp limit ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                                pass
                                l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send limit ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'), ))
                                _loop_vars['add_path_cli'] = l_1_add_path_cli
                        else:
                            pass
                            l_1_add_path_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' additional-paths send ', environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'prefix_list')):
                            pass
                            l_1_add_path_cli = str_join(((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli), ' prefix-list ', environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'prefix_list'), ))
                            _loop_vars['add_path_cli'] = l_1_add_path_cli
                        if t_6((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli)):
                            pass
                            yield '      '
                            yield str((undefined(name='add_path_cli') if l_1_add_path_cli is missing else l_1_add_path_cli))
                            yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = l_1_add_path_cli = missing
            for l_1_network in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'networks'), 'prefix'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_network, 'route_map')):
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_1_network, 'prefix'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_network, 'route_map'))
                    yield '\n'
                else:
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_1_network, 'prefix'))
                    yield '\n'
            l_1_network = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'redistribute_internal'), True):
                pass
                yield '      bgp redistribute-internal\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'bgp'), 'redistribute_internal'), False):
                pass
                yield '      no bgp redistribute-internal\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'redistribute')):
                pass
                l_0_redistribute_var = environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6'), 'redistribute')
                context.vars['redistribute_var'] = l_0_redistribute_var
                context.exported_vars.add('redistribute_var')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'enabled'), True):
                    pass
                    l_0_redistribute_host = 'redistribute attached-host'
                    context.vars['redistribute_host'] = l_0_redistribute_host
                    context.exported_vars.add('redistribute_host')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map')):
                        pass
                        l_0_redistribute_host = str_join(((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'attached_host'), 'route_map'), ))
                        context.vars['redistribute_host'] = l_0_redistribute_host
                        context.exported_vars.add('redistribute_host')
                    yield '      '
                    yield str((undefined(name='redistribute_host') if l_0_redistribute_host is missing else l_0_redistribute_host))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'enabled'), True):
                    pass
                    l_0_redistribute_bgp = 'redistribute bgp leaked'
                    context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                    context.exported_vars.add('redistribute_bgp')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map')):
                        pass
                        l_0_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'bgp'), 'route_map'), ))
                        context.vars['redistribute_bgp'] = l_0_redistribute_bgp
                        context.exported_vars.add('redistribute_bgp')
                    yield '      '
                    yield str((undefined(name='redistribute_bgp') if l_0_redistribute_bgp is missing else l_0_redistribute_bgp))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dhcp'), 'enabled'), True):
                    pass
                    l_0_redistribute_dhcp = 'redistribute dhcp'
                    context.vars['redistribute_dhcp'] = l_0_redistribute_dhcp
                    context.exported_vars.add('redistribute_dhcp')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dhcp'), 'route_map')):
                        pass
                        l_0_redistribute_dhcp = str_join(((undefined(name='redistribute_dhcp') if l_0_redistribute_dhcp is missing else l_0_redistribute_dhcp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dhcp'), 'route_map'), ))
                        context.vars['redistribute_dhcp'] = l_0_redistribute_dhcp
                        context.exported_vars.add('redistribute_dhcp')
                    yield '      '
                    yield str((undefined(name='redistribute_dhcp') if l_0_redistribute_dhcp is missing else l_0_redistribute_dhcp))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_0_redistribute_conn = 'redistribute connected'
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' include leaked', ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'rcf'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'enabled'), True):
                    pass
                    l_0_redistribute_dynamic = 'redistribute dynamic'
                    context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                    context.exported_vars.add('redistribute_dynamic')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map')):
                        pass
                        l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'route_map'), ))
                        context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                        context.exported_vars.add('redistribute_dynamic')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf')):
                        pass
                        l_0_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'dynamic'), 'rcf'), ))
                        context.vars['redistribute_dynamic'] = l_0_redistribute_dynamic
                        context.exported_vars.add('redistribute_dynamic')
                    yield '      '
                    yield str((undefined(name='redistribute_dynamic') if l_0_redistribute_dynamic is missing else l_0_redistribute_dynamic))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'enabled'), True):
                    pass
                    l_0_redistribute_user = 'redistribute user'
                    context.vars['redistribute_user'] = l_0_redistribute_user
                    context.exported_vars.add('redistribute_user')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf')):
                        pass
                        l_0_redistribute_user = str_join(((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'user'), 'rcf'), ))
                        context.vars['redistribute_user'] = l_0_redistribute_user
                        context.exported_vars.add('redistribute_user')
                    yield '      '
                    yield str((undefined(name='redistribute_user') if l_0_redistribute_user is missing else l_0_redistribute_user))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_0_redistribute_isis = 'redistribute isis'
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' include leaked', ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' include leaked', ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_0_redistribute_static = 'redistribute static'
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' include leaked', ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'rcf'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                    yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast')):
            pass
            yield '   !\n   address-family ipv6 multicast\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                pass
                yield '      bgp missing-policy direction in action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                pass
                yield '      bgp missing-policy direction out action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = missing
            for l_1_network in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'networks'), 'prefix'):
                l_1_network_cli = missing
                _loop_vars = {}
                pass
                l_1_network_cli = str_join(('network ', environment.getattr(l_1_network, 'prefix'), ))
                _loop_vars['network_cli'] = l_1_network_cli
                if t_6(environment.getattr(l_1_network, 'route_map')):
                    pass
                    l_1_network_cli = str_join(((undefined(name='network_cli') if l_1_network_cli is missing else l_1_network_cli), ' route-map ', environment.getattr(l_1_network, 'route_map'), ))
                    _loop_vars['network_cli'] = l_1_network_cli
                yield '      '
                yield str((undefined(name='network_cli') if l_1_network_cli is missing else l_1_network_cli))
                yield '\n'
            l_1_network = l_1_network_cli = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'redistribute')):
                pass
                l_0_redistribute_var = environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_multicast'), 'redistribute')
                context.vars['redistribute_var'] = l_0_redistribute_var
                context.exported_vars.add('redistribute_var')
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_0_redistribute_conn = 'redistribute connected'
                    context.vars['redistribute_conn'] = l_0_redistribute_conn
                    context.exported_vars.add('redistribute_conn')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_0_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'connected'), 'route_map'), ))
                        context.vars['redistribute_conn'] = l_0_redistribute_conn
                        context.exported_vars.add('redistribute_conn')
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_0_redistribute_conn is missing else l_0_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_0_redistribute_isis = 'redistribute isis'
                    context.vars['redistribute_isis'] = l_0_redistribute_isis
                    context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'isis_level'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' include leaked', ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'route_map'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_0_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'isis'), 'rcf'), ))
                        context.vars['redistribute_isis'] = l_0_redistribute_isis
                        context.exported_vars.add('redistribute_isis')
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_0_redistribute_isis is missing else l_0_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf = 'redistribute ospf match internal'
                    context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                    context.exported_vars.add('redistribute_ospf')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospf'] = l_0_redistribute_ospf
                        context.exported_vars.add('redistribute_ospf')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_0_redistribute_ospf is missing else l_0_redistribute_ospf))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                    context.exported_vars.add('redistribute_ospfv3')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        context.vars['redistribute_ospfv3'] = l_0_redistribute_ospfv3
                        context.exported_vars.add('redistribute_ospfv3')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_0_redistribute_ospfv3 is missing else l_0_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                    context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospfv3_match'] = l_0_redistribute_ospfv3_match
                        context.exported_vars.add('redistribute_ospfv3_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_0_redistribute_ospfv3_match is missing else l_0_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_0_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                    context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                    context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_0_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                        context.vars['redistribute_ospf_match'] = l_0_redistribute_ospf_match
                        context.exported_vars.add('redistribute_ospf_match')
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_0_redistribute_ospf_match is missing else l_0_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_0_redistribute_static = 'redistribute static'
                    context.vars['redistribute_static'] = l_0_redistribute_static
                    context.exported_vars.add('redistribute_static')
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_0_redistribute_static = str_join(((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_0_redistribute_var is missing else l_0_redistribute_var), 'static'), 'route_map'), ))
                        context.vars['redistribute_static'] = l_0_redistribute_static
                        context.exported_vars.add('redistribute_static')
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_0_redistribute_static is missing else l_0_redistribute_static))
                    yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_sr_te')):
            pass
            yield '   !\n   address-family ipv6 sr-te\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_sr_te'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_ipv6_sr_te'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state')):
            pass
            yield '   !\n   address-family link-state\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                pass
                yield '      bgp missing-policy direction in action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                pass
                yield '      bgp missing-policy direction out action '
                yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(l_1_peer_group, 'missing_policy'), 'direction_out_action'))
                    yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(l_1_neighbor, 'missing_policy'), 'direction_out_action'))
                    yield '\n'
            l_1_neighbor = missing
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection')):
                pass
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'producer'), True):
                    pass
                    yield '      path-selection\n'
                if (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'consumer'), True) or t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'propagator'), True)):
                    pass
                    l_0_path_selection_roles = 'path-selection role'
                    context.vars['path_selection_roles'] = l_0_path_selection_roles
                    context.exported_vars.add('path_selection_roles')
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'consumer'), True):
                        pass
                        l_0_path_selection_roles = str_join(((undefined(name='path_selection_roles') if l_0_path_selection_roles is missing else l_0_path_selection_roles), ' consumer', ))
                        context.vars['path_selection_roles'] = l_0_path_selection_roles
                        context.exported_vars.add('path_selection_roles')
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_link_state'), 'path_selection'), 'roles'), 'propagator'), True):
                        pass
                        l_0_path_selection_roles = str_join(((undefined(name='path_selection_roles') if l_0_path_selection_roles is missing else l_0_path_selection_roles), ' propagator', ))
                        context.vars['path_selection_roles'] = l_0_path_selection_roles
                        context.exported_vars.add('path_selection_roles')
                    yield '      '
                    yield str((undefined(name='path_selection_roles') if l_0_path_selection_roles is missing else l_0_path_selection_roles))
                    yield '\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection')):
            pass
            yield '   !\n   address-family path-selection\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send\n'
                    elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit')):
                        pass
                        if (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'ecmp'):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_peer_group, 'name'))
                            yield ' additional-paths send ecmp limit '
                            yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'))
                            yield '\n'
                        elif (environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send') == 'limit'):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_peer_group, 'name'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_peer_group, 'additional_paths'), 'send'))
                        yield '\n'
            l_1_peer_group = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_path_selection'), 'neighbors'), 'ip_address'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_1_neighbor, 'additional_paths'), 'send'))
                        yield '\n'
            l_1_neighbor = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_rtc')):
            pass
            yield '   !\n   address-family rt-membership\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_rtc'), 'peer_groups'), 'name'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_7(environment.getattr(l_1_peer_group, 'default_route_target')):
                    pass
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route_target'), 'only'), True):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' default-route-target only\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_1_peer_group, 'name'))
                        yield ' default-route-target\n'
                if t_7(environment.getattr(environment.getattr(l_1_peer_group, 'default_route_target'), 'encoding_origin_as_omit')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' default-route-target encoding origin-as omit\n'
            l_1_peer_group = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4')):
            pass
            yield '   !\n   address-family vpn-ipv4\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'peer_groups'), 'name'):
                l_1_peer_group_default_route_cli = resolve('peer_group_default_route_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'enabled'), True):
                    pass
                    l_1_peer_group_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-route', ))
                    _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    yield '      '
                    yield str((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = l_1_peer_group_default_route_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'neighbors'), 'ip_address'):
                l_1_neighbor_default_route_cli = resolve('neighbor_default_route_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'enabled'), True):
                    pass
                    l_1_neighbor_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-route', ))
                    _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = l_1_neighbor_default_route_cli = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'neighbor_default_encapsulation_mpls_next_hop_self'), 'source_interface')):
                pass
                yield '      neighbor default encapsulation mpls next-hop-self source-interface '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'neighbor_default_encapsulation_mpls_next_hop_self'), 'source_interface'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'domain_identifier')):
                pass
                yield '      domain identifier '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'domain_identifier'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv4'), 'route'), 'import_match_failure_action'), 'discard'):
                pass
                yield '      route import match-failure action discard\n'
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6')):
            pass
            yield '   !\n   address-family vpn-ipv6\n'
            for l_1_peer_group in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'peer_groups'), 'name'):
                l_1_peer_group_default_route_cli = resolve('peer_group_default_route_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_peer_group, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_peer_group, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_peer_group, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_peer_group, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_peer_group, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'enabled'), True):
                    pass
                    l_1_peer_group_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_peer_group, 'name'), ' default-route', ))
                    _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'rcf'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map')):
                        pass
                        l_1_peer_group_default_route_cli = str_join(((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_peer_group, 'default_route'), 'route_map'), ))
                        _loop_vars['peer_group_default_route_cli'] = l_1_peer_group_default_route_cli
                    yield '      '
                    yield str((undefined(name='peer_group_default_route_cli') if l_1_peer_group_default_route_cli is missing else l_1_peer_group_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_peer_group, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_peer_group, 'name'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_peer_group, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_peer_group = l_1_peer_group_default_route_cli = missing
            for l_1_neighbor in t_3(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'neighbors'), 'ip_address'):
                l_1_neighbor_default_route_cli = resolve('neighbor_default_route_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_1_neighbor, 'activate'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                elif t_6(environment.getattr(l_1_neighbor, 'activate'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' activate\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(l_1_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_1_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf in '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'rcf_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' rcf out '
                    yield str(environment.getattr(l_1_neighbor, 'rcf_out'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'enabled'), True):
                    pass
                    l_1_neighbor_default_route_cli = str_join(('neighbor ', environment.getattr(l_1_neighbor, 'ip_address'), ' default-route', ))
                    _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    if t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' rcf ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'rcf'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    elif t_6(environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map')):
                        pass
                        l_1_neighbor_default_route_cli = str_join(((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli), ' route-map ', environment.getattr(environment.getattr(l_1_neighbor, 'default_route'), 'route_map'), ))
                        _loop_vars['neighbor_default_route_cli'] = l_1_neighbor_default_route_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_route_cli') if l_1_neighbor_default_route_cli is missing else l_1_neighbor_default_route_cli))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_1_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_1_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_1_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
            l_1_neighbor = l_1_neighbor_default_route_cli = missing
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'neighbor_default_encapsulation_mpls_next_hop_self'), 'source_interface')):
                pass
                yield '      neighbor default encapsulation mpls next-hop-self source-interface '
                yield str(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'neighbor_default_encapsulation_mpls_next_hop_self'), 'source_interface'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'domain_identifier')):
                pass
                yield '      domain identifier '
                yield str(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'domain_identifier'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'address_family_vpn_ipv6'), 'route'), 'import_match_failure_action'), 'discard'):
                pass
                yield '      route import match-failure action discard\n'
        for l_1_vrf in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'vrfs'), 'name'):
            l_1_paths_cli = l_0_paths_cli
            l_1_redistribute_var = l_0_redistribute_var
            l_1_redistribute_conn = l_0_redistribute_conn
            l_1_redistribute_isis = l_0_redistribute_isis
            l_1_redistribute_ospf = l_0_redistribute_ospf
            l_1_redistribute_ospf_match = l_0_redistribute_ospf_match
            l_1_redistribute_ospfv3 = l_0_redistribute_ospfv3
            l_1_redistribute_ospfv3_match = l_0_redistribute_ospfv3_match
            l_1_redistribute_static = l_0_redistribute_static
            l_1_redistribute_rip = l_0_redistribute_rip
            l_1_redistribute_host = l_0_redistribute_host
            l_1_redistribute_dynamic = l_0_redistribute_dynamic
            l_1_redistribute_bgp = l_0_redistribute_bgp
            l_1_redistribute_user = l_0_redistribute_user
            l_1_redistribute_dhcp = l_0_redistribute_dhcp
            _loop_vars = {}
            pass
            yield '   !\n   vrf '
            yield str(environment.getattr(l_1_vrf, 'name'))
            yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'rd')):
                pass
                yield '      rd '
                yield str(environment.getattr(l_1_vrf, 'rd'))
                yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'default_route_exports')):
                pass
                for l_2_default_route_export in t_3(environment.getattr(l_1_vrf, 'default_route_exports'), 'address_family'):
                    l_2_vrf_default_route_export_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_vrf_default_route_export_cli = str_join(('default-route export ', environment.getattr(l_2_default_route_export, 'address_family'), ))
                    _loop_vars['vrf_default_route_export_cli'] = l_2_vrf_default_route_export_cli
                    if t_6(environment.getattr(l_2_default_route_export, 'always'), True):
                        pass
                        l_2_vrf_default_route_export_cli = str_join(((undefined(name='vrf_default_route_export_cli') if l_2_vrf_default_route_export_cli is missing else l_2_vrf_default_route_export_cli), ' always', ))
                        _loop_vars['vrf_default_route_export_cli'] = l_2_vrf_default_route_export_cli
                    if t_6(environment.getattr(l_2_default_route_export, 'rcf')):
                        pass
                        l_2_vrf_default_route_export_cli = str_join(((undefined(name='vrf_default_route_export_cli') if l_2_vrf_default_route_export_cli is missing else l_2_vrf_default_route_export_cli), ' rcf ', environment.getattr(l_2_default_route_export, 'rcf'), ))
                        _loop_vars['vrf_default_route_export_cli'] = l_2_vrf_default_route_export_cli
                    elif t_6(environment.getattr(l_2_default_route_export, 'route_map')):
                        pass
                        l_2_vrf_default_route_export_cli = str_join(((undefined(name='vrf_default_route_export_cli') if l_2_vrf_default_route_export_cli is missing else l_2_vrf_default_route_export_cli), ' route-map ', environment.getattr(l_2_default_route_export, 'route_map'), ))
                        _loop_vars['vrf_default_route_export_cli'] = l_2_vrf_default_route_export_cli
                    yield '      '
                    yield str((undefined(name='vrf_default_route_export_cli') if l_2_vrf_default_route_export_cli is missing else l_2_vrf_default_route_export_cli))
                    yield '\n'
                l_2_default_route_export = l_2_vrf_default_route_export_cli = missing
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'route_targets'), 'import')):
                pass
                for l_2_address_family in environment.getattr(environment.getattr(l_1_vrf, 'route_targets'), 'import'):
                    _loop_vars = {}
                    pass
                    for l_3_route_target in environment.getattr(l_2_address_family, 'route_targets'):
                        _loop_vars = {}
                        pass
                        yield '      route-target import '
                        yield str(environment.getattr(l_2_address_family, 'address_family'))
                        yield ' '
                        yield str(l_3_route_target)
                        yield '\n'
                    l_3_route_target = missing
                    if (environment.getattr(l_2_address_family, 'address_family') in ['evpn', 'vpn-ipv4', 'vpn-ipv6']):
                        pass
                        if t_6(environment.getattr(l_2_address_family, 'rcf')):
                            pass
                            if (t_6(environment.getattr(l_2_address_family, 'vpn_route_filter_rcf')) and (environment.getattr(l_2_address_family, 'address_family') in ['vpn-ipv4', 'vpn-ipv6'])):
                                pass
                                yield '      route-target import '
                                yield str(environment.getattr(l_2_address_family, 'address_family'))
                                yield ' rcf '
                                yield str(environment.getattr(l_2_address_family, 'rcf'))
                                yield ' vpn-route filter-rcf '
                                yield str(environment.getattr(l_2_address_family, 'vpn_route_filter_rcf'))
                                yield '\n'
                            else:
                                pass
                                yield '      route-target import '
                                yield str(environment.getattr(l_2_address_family, 'address_family'))
                                yield ' rcf '
                                yield str(environment.getattr(l_2_address_family, 'rcf'))
                                yield '\n'
                        if t_6(environment.getattr(l_2_address_family, 'route_map')):
                            pass
                            yield '      route-target import '
                            yield str(environment.getattr(l_2_address_family, 'address_family'))
                            yield ' route-map '
                            yield str(environment.getattr(l_2_address_family, 'route_map'))
                            yield '\n'
                l_2_address_family = missing
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'route_targets'), 'export')):
                pass
                for l_2_address_family in environment.getattr(environment.getattr(l_1_vrf, 'route_targets'), 'export'):
                    _loop_vars = {}
                    pass
                    for l_3_route_target in environment.getattr(l_2_address_family, 'route_targets'):
                        _loop_vars = {}
                        pass
                        yield '      route-target export '
                        yield str(environment.getattr(l_2_address_family, 'address_family'))
                        yield ' '
                        yield str(l_3_route_target)
                        yield '\n'
                    l_3_route_target = missing
                    if (environment.getattr(l_2_address_family, 'address_family') in ['evpn', 'vpn-ipv4', 'vpn-ipv6']):
                        pass
                        if t_6(environment.getattr(l_2_address_family, 'rcf')):
                            pass
                            if (t_6(environment.getattr(l_2_address_family, 'vrf_route_filter_rcf')) and (environment.getattr(l_2_address_family, 'address_family') in ['vpn-ipv4', 'vpn-ipv6'])):
                                pass
                                yield '      route-target export '
                                yield str(environment.getattr(l_2_address_family, 'address_family'))
                                yield ' rcf '
                                yield str(environment.getattr(l_2_address_family, 'rcf'))
                                yield ' vrf-route filter-rcf '
                                yield str(environment.getattr(l_2_address_family, 'vrf_route_filter_rcf'))
                                yield '\n'
                            else:
                                pass
                                yield '      route-target export '
                                yield str(environment.getattr(l_2_address_family, 'address_family'))
                                yield ' rcf '
                                yield str(environment.getattr(l_2_address_family, 'rcf'))
                                yield '\n'
                        if t_6(environment.getattr(l_2_address_family, 'route_map')):
                            pass
                            yield '      route-target export '
                            yield str(environment.getattr(l_2_address_family, 'address_family'))
                            yield ' route-map '
                            yield str(environment.getattr(l_2_address_family, 'route_map'))
                            yield '\n'
                l_2_address_family = missing
            if t_6(environment.getattr(l_1_vrf, 'router_id')):
                pass
                yield '      router-id '
                yield str(environment.getattr(l_1_vrf, 'router_id'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'updates'), 'wait_for_convergence'), True):
                pass
                yield '      update wait-for-convergence\n'
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'updates'), 'wait_install'), True):
                pass
                yield '      update wait-install\n'
            if t_6(environment.getattr(l_1_vrf, 'timers')):
                pass
                yield '      timers bgp '
                yield str(environment.getattr(l_1_vrf, 'timers'))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'enabled'), True):
                pass
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'restart_time')):
                    pass
                    yield '      graceful-restart restart-time '
                    yield str(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'restart_time'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'stalepath_time')):
                    pass
                    yield '      graceful-restart stalepath-time '
                    yield str(environment.getattr(environment.getattr(l_1_vrf, 'graceful_restart'), 'stalepath_time'))
                    yield '\n'
                yield '      graceful-restart\n'
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'maximum_paths'), 'paths')):
                pass
                l_1_paths_cli = str_join(('maximum-paths ', environment.getattr(environment.getattr(l_1_vrf, 'maximum_paths'), 'paths'), ))
                _loop_vars['paths_cli'] = l_1_paths_cli
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'maximum_paths'), 'ecmp')):
                    pass
                    l_1_paths_cli = str_join(((undefined(name='paths_cli') if l_1_paths_cli is missing else l_1_paths_cli), ' ecmp ', environment.getattr(environment.getattr(l_1_vrf, 'maximum_paths'), 'ecmp'), ))
                    _loop_vars['paths_cli'] = l_1_paths_cli
                yield '      '
                yield str((undefined(name='paths_cli') if l_1_paths_cli is missing else l_1_paths_cli))
                yield '\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'install'), True):
                pass
                yield '      bgp additional-paths install\n'
            elif t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                pass
                yield '      bgp additional-paths install ecmp-primary\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'receive'), True):
                pass
                yield '      bgp additional-paths receive\n'
            if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send')):
                pass
                if (environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                    pass
                    yield '      no bgp additional-paths send\n'
                elif (t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                    pass
                    yield '      bgp additional-paths send ecmp limit '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send_limit'))
                    yield '\n'
                elif (environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send') == 'limit'):
                    pass
                    if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send_limit')):
                        pass
                        yield '      bgp additional-paths send limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                else:
                    pass
                    yield '      bgp additional-paths send '
                    yield str(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'additional_paths'), 'send'))
                    yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'listen_ranges')):
                pass
                def t_10(fiter):
                    for l_2_listen_range in fiter:
                        if ((t_6(environment.getattr(l_2_listen_range, 'peer_group')) and t_6(environment.getattr(l_2_listen_range, 'prefix'))) and (t_6(environment.getattr(l_2_listen_range, 'peer_filter')) or t_6(environment.getattr(l_2_listen_range, 'remote_as')))):
                            yield l_2_listen_range
                for l_2_listen_range in t_10(t_3(environment.getattr(l_1_vrf, 'listen_ranges'), 'peer_group')):
                    l_2_listen_range_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_listen_range_cli = str_join(('bgp listen range ', environment.getattr(l_2_listen_range, 'prefix'), ))
                    _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    if t_6(environment.getattr(l_2_listen_range, 'peer_id_include_router_id'), True):
                        pass
                        l_2_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli), ' peer-id include router-id', ))
                        _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    l_2_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli), ' peer-group ', environment.getattr(l_2_listen_range, 'peer_group'), ))
                    _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    if t_6(environment.getattr(l_2_listen_range, 'peer_filter')):
                        pass
                        l_2_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli), ' peer-filter ', environment.getattr(l_2_listen_range, 'peer_filter'), ))
                        _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    elif t_6(environment.getattr(l_2_listen_range, 'remote_as')):
                        pass
                        l_2_listen_range_cli = str_join(((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli), ' remote-as ', environment.getattr(l_2_listen_range, 'remote_as'), ))
                        _loop_vars['listen_range_cli'] = l_2_listen_range_cli
                    yield '      '
                    yield str((undefined(name='listen_range_cli') if l_2_listen_range_cli is missing else l_2_listen_range_cli))
                    yield '\n'
                l_2_listen_range = l_2_listen_range_cli = missing
            for l_2_neighbor in t_3(environment.getattr(l_1_vrf, 'neighbors'), 'ip_address'):
                l_2_remove_private_as_cli = resolve('remove_private_as_cli')
                l_2_allowas_in_cli = resolve('allowas_in_cli')
                l_2_neighbor_rib_in_pre_policy_retain_cli = resolve('neighbor_rib_in_pre_policy_retain_cli')
                l_2_neighbor_ebgp_multihop_cli = resolve('neighbor_ebgp_multihop_cli')
                l_2_hide_passwords = resolve('hide_passwords')
                l_2_neighbor_default_originate_cli = resolve('neighbor_default_originate_cli')
                l_2_maximum_routes_cli = resolve('maximum_routes_cli')
                l_2_remove_private_as_ingress_cli = resolve('remove_private_as_ingress_cli')
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_2_neighbor, 'peer_group')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' peer group '
                    yield str(environment.getattr(l_2_neighbor, 'peer_group'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'remote_as')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' remote-as '
                    yield str(environment.getattr(l_2_neighbor, 'remote_as'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'next_hop_self'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' next-hop-self\n'
                if t_6(environment.getattr(l_2_neighbor, 'next_hop_peer'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' next-hop-peer\n'
                if t_6(environment.getattr(l_2_neighbor, 'shutdown'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' shutdown\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as'), 'enabled'), True):
                    pass
                    l_2_remove_private_as_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' remove-private-as', ))
                    _loop_vars['remove_private_as_cli'] = l_2_remove_private_as_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as'), 'all'), True):
                        pass
                        l_2_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_2_remove_private_as_cli is missing else l_2_remove_private_as_cli), ' all', ))
                        _loop_vars['remove_private_as_cli'] = l_2_remove_private_as_cli
                        if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as'), 'replace_as'), True):
                            pass
                            l_2_remove_private_as_cli = str_join(((undefined(name='remove_private_as_cli') if l_2_remove_private_as_cli is missing else l_2_remove_private_as_cli), ' replace-as', ))
                            _loop_vars['remove_private_as_cli'] = l_2_remove_private_as_cli
                    yield '      '
                    yield str((undefined(name='remove_private_as_cli') if l_2_remove_private_as_cli is missing else l_2_remove_private_as_cli))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as'), 'enabled'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' remove-private-as\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'as_path'), 'prepend_own_disabled'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' as-path prepend-own disabled\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'as_path'), 'remote_as_replace_out'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' as-path remote-as replace out\n'
                if t_6(environment.getattr(l_2_neighbor, 'local_as')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' local-as '
                    yield str(environment.getattr(l_2_neighbor, 'local_as'))
                    yield ' no-prepend replace-as\n'
                if t_6(environment.getattr(l_2_neighbor, 'weight')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' weight '
                    yield str(environment.getattr(l_2_neighbor, 'weight'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'passive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' passive\n'
                if t_6(environment.getattr(l_2_neighbor, 'update_source')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' update-source '
                    yield str(environment.getattr(l_2_neighbor, 'update_source'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'bfd'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' bfd\n'
                    if ((t_6(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'interval')) and t_6(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'min_rx'))) and t_6(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'multiplier'))):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' bfd interval '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'interval'))
                        yield ' min-rx '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'min_rx'))
                        yield ' multiplier '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'bfd_timers'), 'multiplier'))
                        yield '\n'
                elif (t_6(environment.getattr(l_2_neighbor, 'bfd'), False) and t_6(environment.getattr(l_2_neighbor, 'peer_group'))):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' bfd\n'
                if t_6(environment.getattr(l_2_neighbor, 'description')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' description '
                    yield str(environment.getattr(l_2_neighbor, 'description'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'allowas_in'), 'enabled'), True):
                    pass
                    l_2_allowas_in_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' allowas-in', ))
                    _loop_vars['allowas_in_cli'] = l_2_allowas_in_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'allowas_in'), 'times')):
                        pass
                        l_2_allowas_in_cli = str_join(((undefined(name='allowas_in_cli') if l_2_allowas_in_cli is missing else l_2_allowas_in_cli), ' ', environment.getattr(environment.getattr(l_2_neighbor, 'allowas_in'), 'times'), ))
                        _loop_vars['allowas_in_cli'] = l_2_allowas_in_cli
                    yield '      '
                    yield str((undefined(name='allowas_in_cli') if l_2_allowas_in_cli is missing else l_2_allowas_in_cli))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'rib_in_pre_policy_retain'), 'enabled'), True):
                    pass
                    l_2_neighbor_rib_in_pre_policy_retain_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' rib-in pre-policy retain', ))
                    _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_2_neighbor_rib_in_pre_policy_retain_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'rib_in_pre_policy_retain'), 'all'), True):
                        pass
                        l_2_neighbor_rib_in_pre_policy_retain_cli = str_join(((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_2_neighbor_rib_in_pre_policy_retain_cli is missing else l_2_neighbor_rib_in_pre_policy_retain_cli), ' all', ))
                        _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_2_neighbor_rib_in_pre_policy_retain_cli
                    yield '      '
                    yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_2_neighbor_rib_in_pre_policy_retain_cli is missing else l_2_neighbor_rib_in_pre_policy_retain_cli))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_2_neighbor, 'rib_in_pre_policy_retain'), 'enabled'), False):
                    pass
                    l_2_neighbor_rib_in_pre_policy_retain_cli = str_join(('no neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' rib-in pre-policy retain', ))
                    _loop_vars['neighbor_rib_in_pre_policy_retain_cli'] = l_2_neighbor_rib_in_pre_policy_retain_cli
                    yield '      '
                    yield str((undefined(name='neighbor_rib_in_pre_policy_retain_cli') if l_2_neighbor_rib_in_pre_policy_retain_cli is missing else l_2_neighbor_rib_in_pre_policy_retain_cli))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'ebgp_multihop')):
                    pass
                    l_2_neighbor_ebgp_multihop_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' ebgp-multihop', ))
                    _loop_vars['neighbor_ebgp_multihop_cli'] = l_2_neighbor_ebgp_multihop_cli
                    if t_8(environment.getattr(l_2_neighbor, 'ebgp_multihop')):
                        pass
                        l_2_neighbor_ebgp_multihop_cli = str_join(((undefined(name='neighbor_ebgp_multihop_cli') if l_2_neighbor_ebgp_multihop_cli is missing else l_2_neighbor_ebgp_multihop_cli), ' ', environment.getattr(l_2_neighbor, 'ebgp_multihop'), ))
                        _loop_vars['neighbor_ebgp_multihop_cli'] = l_2_neighbor_ebgp_multihop_cli
                    yield '      '
                    yield str((undefined(name='neighbor_ebgp_multihop_cli') if l_2_neighbor_ebgp_multihop_cli is missing else l_2_neighbor_ebgp_multihop_cli))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'route_reflector_client'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' route-reflector-client\n'
                elif t_6(environment.getattr(l_2_neighbor, 'route_reflector_client'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' route-reflector-client\n'
                if t_6(environment.getattr(l_2_neighbor, 'timers')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' timers '
                    yield str(environment.getattr(l_2_neighbor, 'timers'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                    yield ' in\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '      no neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')):
                            pass
                            yield '      neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '      neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths send '
                        yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send'))
                        yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' route-map '
                    yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                    yield ' out\n'
                if t_6(environment.getattr(l_2_neighbor, 'password')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' password 7 '
                    yield str(t_2(environment.getattr(l_2_neighbor, 'password'), (undefined(name='hide_passwords') if l_2_hide_passwords is missing else l_2_hide_passwords)))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'default_originate')):
                    pass
                    l_2_neighbor_default_originate_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' default-originate', ))
                    _loop_vars['neighbor_default_originate_cli'] = l_2_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'default_originate'), 'route_map')):
                        pass
                        l_2_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_2_neighbor_default_originate_cli is missing else l_2_neighbor_default_originate_cli), ' route-map ', environment.getattr(environment.getattr(l_2_neighbor, 'default_originate'), 'route_map'), ))
                        _loop_vars['neighbor_default_originate_cli'] = l_2_neighbor_default_originate_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'default_originate'), 'always'), True):
                        pass
                        l_2_neighbor_default_originate_cli = str_join(((undefined(name='neighbor_default_originate_cli') if l_2_neighbor_default_originate_cli is missing else l_2_neighbor_default_originate_cli), ' always', ))
                        _loop_vars['neighbor_default_originate_cli'] = l_2_neighbor_default_originate_cli
                    yield '      '
                    yield str((undefined(name='neighbor_default_originate_cli') if l_2_neighbor_default_originate_cli is missing else l_2_neighbor_default_originate_cli))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'send_community'), 'all'):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' send-community\n'
                elif t_6(environment.getattr(l_2_neighbor, 'send_community')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' send-community '
                    yield str(environment.getattr(l_2_neighbor, 'send_community'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'maximum_routes')):
                    pass
                    l_2_maximum_routes_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' maximum-routes ', environment.getattr(l_2_neighbor, 'maximum_routes'), ))
                    _loop_vars['maximum_routes_cli'] = l_2_maximum_routes_cli
                    if t_6(environment.getattr(l_2_neighbor, 'maximum_routes_warning_limit')):
                        pass
                        l_2_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_2_maximum_routes_cli is missing else l_2_maximum_routes_cli), ' warning-limit ', environment.getattr(l_2_neighbor, 'maximum_routes_warning_limit'), ))
                        _loop_vars['maximum_routes_cli'] = l_2_maximum_routes_cli
                    if t_6(environment.getattr(l_2_neighbor, 'maximum_routes_warning_only'), True):
                        pass
                        l_2_maximum_routes_cli = str_join(((undefined(name='maximum_routes_cli') if l_2_maximum_routes_cli is missing else l_2_maximum_routes_cli), ' warning-only', ))
                        _loop_vars['maximum_routes_cli'] = l_2_maximum_routes_cli
                    yield '      '
                    yield str((undefined(name='maximum_routes_cli') if l_2_maximum_routes_cli is missing else l_2_maximum_routes_cli))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' peer-tag in '
                    yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                    yield '\n'
                if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                    pass
                    yield '      neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' peer-tag out discard '
                    yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as_ingress'), 'enabled'), True):
                    pass
                    l_2_remove_private_as_ingress_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' remove-private-as ingress', ))
                    _loop_vars['remove_private_as_ingress_cli'] = l_2_remove_private_as_ingress_cli
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as_ingress'), 'replace_as'), True):
                        pass
                        l_2_remove_private_as_ingress_cli = str_join(((undefined(name='remove_private_as_ingress_cli') if l_2_remove_private_as_ingress_cli is missing else l_2_remove_private_as_ingress_cli), ' replace-as', ))
                        _loop_vars['remove_private_as_ingress_cli'] = l_2_remove_private_as_ingress_cli
                    yield '      '
                    yield str((undefined(name='remove_private_as_ingress_cli') if l_2_remove_private_as_ingress_cli is missing else l_2_remove_private_as_ingress_cli))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(l_2_neighbor, 'remove_private_as_ingress'), 'enabled'), False):
                    pass
                    yield '      no neighbor '
                    yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                    yield ' remove-private-as ingress\n'
            l_2_neighbor = l_2_remove_private_as_cli = l_2_allowas_in_cli = l_2_neighbor_rib_in_pre_policy_retain_cli = l_2_neighbor_ebgp_multihop_cli = l_2_hide_passwords = l_2_neighbor_default_originate_cli = l_2_maximum_routes_cli = l_2_remove_private_as_ingress_cli = missing
            for l_2_network in t_3(environment.getattr(l_1_vrf, 'networks'), 'prefix'):
                _loop_vars = {}
                pass
                if t_6(environment.getattr(l_2_network, 'route_map')):
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_2_network, 'prefix'))
                    yield ' route-map '
                    yield str(environment.getattr(l_2_network, 'route_map'))
                    yield '\n'
                else:
                    pass
                    yield '      network '
                    yield str(environment.getattr(l_2_network, 'prefix'))
                    yield '\n'
            l_2_network = missing
            if t_6(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'redistribute_internal'), True):
                pass
                yield '      bgp redistribute-internal\n'
            elif t_6(environment.getattr(environment.getattr(l_1_vrf, 'bgp'), 'redistribute_internal'), False):
                pass
                yield '      no bgp redistribute-internal\n'
            for l_2_aggregate_address in t_3(environment.getattr(l_1_vrf, 'aggregate_addresses'), 'prefix'):
                l_2_aggregate_address_cli = missing
                _loop_vars = {}
                pass
                l_2_aggregate_address_cli = str_join(('aggregate-address ', environment.getattr(l_2_aggregate_address, 'prefix'), ))
                _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'as_set'), True):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' as-set', ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'summary_only'), True):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' summary-only', ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'attribute_map')):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' attribute-map ', environment.getattr(l_2_aggregate_address, 'attribute_map'), ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'match_map')):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' match-map ', environment.getattr(l_2_aggregate_address, 'match_map'), ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                if t_6(environment.getattr(l_2_aggregate_address, 'advertise_only'), True):
                    pass
                    l_2_aggregate_address_cli = str_join(((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli), ' advertise-only', ))
                    _loop_vars['aggregate_address_cli'] = l_2_aggregate_address_cli
                yield '      '
                yield str((undefined(name='aggregate_address_cli') if l_2_aggregate_address_cli is missing else l_2_aggregate_address_cli))
                yield '\n'
            l_2_aggregate_address = l_2_aggregate_address_cli = missing
            if t_6(environment.getattr(l_1_vrf, 'redistribute')):
                pass
                l_1_redistribute_var = environment.getattr(l_1_vrf, 'redistribute')
                _loop_vars['redistribute_var'] = l_1_redistribute_var
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                    pass
                    l_1_redistribute_conn = 'redistribute connected'
                    _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' include leaked', ))
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                        pass
                        l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf')):
                        pass
                        l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf'), ))
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                    yield '      '
                    yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                    pass
                    l_1_redistribute_isis = 'redistribute isis'
                    _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                        pass
                        l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                        pass
                        l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                        pass
                        l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                    yield '      '
                    yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospf = 'redistribute ospf'
                    _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' include leaked', ))
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map')):
                        pass
                        l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map'), ))
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospf = 'redistribute ospf match internal'
                    _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' include leaked', ))
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                        pass
                        l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                    yield '      '
                    yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospf_match = 'redistribute ospf match external'
                    _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' include leaked', ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                    _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' include leaked', ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                    yield '      '
                    yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                    _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                        pass
                        l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                    yield '\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                    _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                        pass
                        l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                    _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                    pass
                    l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                    _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                        pass
                        l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                    yield '      '
                    yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                    pass
                    l_1_redistribute_static = 'redistribute static'
                    _loop_vars['redistribute_static'] = l_1_redistribute_static
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'include_leaked'), True):
                        pass
                        l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' include leaked', ))
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                        pass
                        l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf')):
                        pass
                        l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf'), ))
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                    yield '      '
                    yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'enabled'), True):
                    pass
                    l_1_redistribute_rip = 'redistribute rip'
                    _loop_vars['redistribute_rip'] = l_1_redistribute_rip
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'route_map')):
                        pass
                        l_1_redistribute_rip = str_join(((undefined(name='redistribute_rip') if l_1_redistribute_rip is missing else l_1_redistribute_rip), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'route_map'), ))
                        _loop_vars['redistribute_rip'] = l_1_redistribute_rip
                    yield '      '
                    yield str((undefined(name='redistribute_rip') if l_1_redistribute_rip is missing else l_1_redistribute_rip))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'enabled'), True):
                    pass
                    l_1_redistribute_host = 'redistribute attached-host'
                    _loop_vars['redistribute_host'] = l_1_redistribute_host
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map')):
                        pass
                        l_1_redistribute_host = str_join(((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map'), ))
                        _loop_vars['redistribute_host'] = l_1_redistribute_host
                    yield '      '
                    yield str((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'enabled'), True):
                    pass
                    l_1_redistribute_dynamic = 'redistribute dynamic'
                    _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map')):
                        pass
                        l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map'), ))
                        _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                    elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf')):
                        pass
                        l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf'), ))
                        _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                    yield '      '
                    yield str((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'enabled'), True):
                    pass
                    l_1_redistribute_bgp = 'redistribute bgp leaked'
                    _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map')):
                        pass
                        l_1_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map'), ))
                        _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                    yield '      '
                    yield str((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'enabled'), True):
                    pass
                    l_1_redistribute_user = 'redistribute user'
                    _loop_vars['redistribute_user'] = l_1_redistribute_user
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf')):
                        pass
                        l_1_redistribute_user = str_join(((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf'), ))
                        _loop_vars['redistribute_user'] = l_1_redistribute_user
                    yield '      '
                    yield str((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user))
                    yield '\n'
            for l_2_neighbor_interface in t_3(environment.getattr(l_1_vrf, 'neighbor_interfaces'), 'name'):
                _loop_vars = {}
                pass
                if (t_6(environment.getattr(l_2_neighbor_interface, 'peer_group')) and t_6(environment.getattr(l_2_neighbor_interface, 'remote_as'))):
                    pass
                    yield '      neighbor interface '
                    yield str(environment.getattr(l_2_neighbor_interface, 'name'))
                    yield ' peer-group '
                    yield str(environment.getattr(l_2_neighbor_interface, 'peer_group'))
                    yield ' remote-as '
                    yield str(environment.getattr(l_2_neighbor_interface, 'remote_as'))
                    yield '\n'
                elif (t_6(environment.getattr(l_2_neighbor_interface, 'peer_group')) and t_6(environment.getattr(l_2_neighbor_interface, 'peer_filter'))):
                    pass
                    yield '      neighbor interface '
                    yield str(environment.getattr(l_2_neighbor_interface, 'name'))
                    yield ' peer-group '
                    yield str(environment.getattr(l_2_neighbor_interface, 'peer_group'))
                    yield ' peer-filter '
                    yield str(environment.getattr(l_2_neighbor_interface, 'peer_filter'))
                    yield '\n'
            l_2_neighbor_interface = missing
            if t_6(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4')):
                pass
                yield '      !\n      address-family flow-spec ipv4\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv4'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                l_2_neighbor = missing
            if t_6(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6')):
                pass
                yield '      !\n      address-family flow-spec ipv6\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_flow_spec_ipv6'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                l_2_neighbor = missing
            if t_6(environment.getattr(l_1_vrf, 'address_family_ipv4')):
                pass
                yield '      !\n      address-family ipv4\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'install'), True):
                    pass
                    yield '         bgp additional-paths install\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                    pass
                    yield '         bgp additional-paths install ecmp-primary\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'receive'), True):
                    pass
                    yield '         bgp additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '         no bgp additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '         bgp additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit')):
                            pass
                            yield '         bgp additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '         bgp additional-paths send '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'additional_paths'), 'send'))
                        yield '\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'neighbors'), 'ip_address'):
                    l_2_ipv6_originate_cli = resolve('ipv6_originate_cli')
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths receive\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(l_2_neighbor, 'rcf_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' rcf in '
                        yield str(environment.getattr(l_2_neighbor, 'rcf_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'rcf_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' rcf out '
                        yield str(environment.getattr(l_2_neighbor, 'rcf_out'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'prefix_list_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' prefix-list '
                        yield str(environment.getattr(l_2_neighbor, 'prefix_list_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'prefix_list_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' prefix-list '
                        yield str(environment.getattr(l_2_neighbor, 'prefix_list_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send')):
                        pass
                        if (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'disabled'):
                            pass
                            yield '         no neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send\n'
                        elif (t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            yield '         neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send ecmp limit '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                        elif (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')):
                                pass
                                yield '         neighbor '
                                yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                                yield ' additional-paths send limit '
                                yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                                yield '\n'
                        else:
                            pass
                            yield '         neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send'))
                            yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr(l_2_neighbor, 'next_hop'), 'address_family_ipv6'), 'enabled')):
                        pass
                        if environment.getattr(environment.getattr(environment.getattr(l_2_neighbor, 'next_hop'), 'address_family_ipv6'), 'enabled'):
                            pass
                            l_2_ipv6_originate_cli = str_join(('neighbor ', environment.getattr(l_2_neighbor, 'ip_address'), ' next-hop address-family ipv6', ))
                            _loop_vars['ipv6_originate_cli'] = l_2_ipv6_originate_cli
                            if t_6(environment.getattr(environment.getattr(environment.getattr(l_2_neighbor, 'next_hop'), 'address_family_ipv6'), 'originate'), True):
                                pass
                                l_2_ipv6_originate_cli = str_join(((undefined(name='ipv6_originate_cli') if l_2_ipv6_originate_cli is missing else l_2_ipv6_originate_cli), ' originate', ))
                                _loop_vars['ipv6_originate_cli'] = l_2_ipv6_originate_cli
                            yield '         '
                            yield str((undefined(name='ipv6_originate_cli') if l_2_ipv6_originate_cli is missing else l_2_ipv6_originate_cli))
                            yield '\n'
                        else:
                            pass
                            yield '         no neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' next-hop address-family ipv6\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag in '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag out discard '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                        yield '\n'
                l_2_neighbor = l_2_ipv6_originate_cli = missing
                for l_2_network in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'networks'), 'prefix'):
                    l_2_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_network_cli = str_join(('network ', environment.getattr(l_2_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_2_network_cli
                    if t_6(environment.getattr(l_2_network, 'route_map')):
                        pass
                        l_2_network_cli = str_join(((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli), ' route-map ', environment.getattr(l_2_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_2_network_cli
                    yield '         '
                    yield str((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli))
                    yield '\n'
                l_2_network = l_2_network_cli = missing
                if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'redistribute_internal'), True):
                    pass
                    yield '         bgp redistribute-internal\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'bgp'), 'redistribute_internal'), False):
                    pass
                    yield '         no bgp redistribute-internal\n'
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'redistribute')):
                    pass
                    l_1_redistribute_var = environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4'), 'redistribute')
                    _loop_vars['redistribute_var'] = l_1_redistribute_var
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'enabled'), True):
                        pass
                        l_1_redistribute_host = 'redistribute attached-host'
                        _loop_vars['redistribute_host'] = l_1_redistribute_host
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map')):
                            pass
                            l_1_redistribute_host = str_join(((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map'), ))
                            _loop_vars['redistribute_host'] = l_1_redistribute_host
                        yield '         '
                        yield str((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'enabled'), True):
                        pass
                        l_1_redistribute_bgp = 'redistribute bgp leaked'
                        _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map')):
                            pass
                            l_1_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map'), ))
                            _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                        yield '         '
                        yield str((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                        pass
                        l_1_redistribute_conn = 'redistribute connected'
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' include leaked', ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        yield '         '
                        yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'enabled'), True):
                        pass
                        l_1_redistribute_dynamic = 'redistribute dynamic'
                        _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map')):
                            pass
                            l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map'), ))
                            _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf')):
                            pass
                            l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf'), ))
                            _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        yield '         '
                        yield str((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'enabled'), True):
                        pass
                        l_1_redistribute_user = 'redistribute user'
                        _loop_vars['redistribute_user'] = l_1_redistribute_user
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf')):
                            pass
                            l_1_redistribute_user = str_join(((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf'), ))
                            _loop_vars['redistribute_user'] = l_1_redistribute_user
                        yield '         '
                        yield str((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                        pass
                        l_1_redistribute_isis = 'redistribute isis'
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        yield '         '
                        yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' include leaked', ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf match internal'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' include leaked', ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' include leaked', ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' include leaked', ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'enabled'), True):
                        pass
                        l_1_redistribute_rip = 'redistribute rip'
                        _loop_vars['redistribute_rip'] = l_1_redistribute_rip
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'route_map')):
                            pass
                            l_1_redistribute_rip = str_join(((undefined(name='redistribute_rip') if l_1_redistribute_rip is missing else l_1_redistribute_rip), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'rip'), 'route_map'), ))
                            _loop_vars['redistribute_rip'] = l_1_redistribute_rip
                        yield '         '
                        yield str((undefined(name='redistribute_rip') if l_1_redistribute_rip is missing else l_1_redistribute_rip))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                        pass
                        l_1_redistribute_static = 'redistribute static'
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' include leaked', ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        yield '         '
                        yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                        yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast')):
                pass
                yield '      !\n      address-family ipv4 multicast\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                    pass
                    yield '         bgp additional-paths receive\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths receive\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag in '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag out discard '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                        yield '\n'
                l_2_neighbor = missing
                for l_2_network in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'networks'), 'prefix'):
                    l_2_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_network_cli = str_join(('network ', environment.getattr(l_2_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_2_network_cli
                    if t_6(environment.getattr(l_2_network, 'route_map')):
                        pass
                        l_2_network_cli = str_join(((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli), ' route-map ', environment.getattr(l_2_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_2_network_cli
                    yield '         '
                    yield str((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli))
                    yield '\n'
                l_2_network = l_2_network_cli = missing
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'redistribute')):
                    pass
                    l_1_redistribute_var = environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv4_multicast'), 'redistribute')
                    _loop_vars['redistribute_var'] = l_1_redistribute_var
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'enabled'), True):
                        pass
                        l_1_redistribute_host = 'redistribute attached-host'
                        _loop_vars['redistribute_host'] = l_1_redistribute_host
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map')):
                            pass
                            l_1_redistribute_host = str_join(((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map'), ))
                            _loop_vars['redistribute_host'] = l_1_redistribute_host
                        yield '         '
                        yield str((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                        pass
                        l_1_redistribute_conn = 'redistribute connected'
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        yield '         '
                        yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                        pass
                        l_1_redistribute_isis = 'redistribute isis'
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        yield '         '
                        yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf match internal'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                        pass
                        l_1_redistribute_static = 'redistribute static'
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        yield '         '
                        yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                        yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'address_family_ipv6')):
                pass
                yield '      !\n      address-family ipv6\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'install'), True):
                    pass
                    yield '         bgp additional-paths install\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'install_ecmp_primary'), True):
                    pass
                    yield '         bgp additional-paths install ecmp-primary\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'receive'), True):
                    pass
                    yield '         bgp additional-paths receive\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send')):
                    pass
                    if (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'disabled'):
                        pass
                        yield '         no bgp additional-paths send\n'
                    elif (t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'ecmp')):
                        pass
                        yield '         bgp additional-paths send ecmp limit '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit'))
                        yield '\n'
                    elif (environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send') == 'limit'):
                        pass
                        if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit')):
                            pass
                            yield '         bgp additional-paths send limit '
                            yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send_limit'))
                            yield '\n'
                    else:
                        pass
                        yield '         bgp additional-paths send '
                        yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'additional_paths'), 'send'))
                        yield '\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths receive\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(l_2_neighbor, 'rcf_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' rcf in '
                        yield str(environment.getattr(l_2_neighbor, 'rcf_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'rcf_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' rcf out '
                        yield str(environment.getattr(l_2_neighbor, 'rcf_out'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'prefix_list_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' prefix-list '
                        yield str(environment.getattr(l_2_neighbor, 'prefix_list_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'prefix_list_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' prefix-list '
                        yield str(environment.getattr(l_2_neighbor, 'prefix_list_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send')):
                        pass
                        if (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'disabled'):
                            pass
                            yield '         no neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send\n'
                        elif (t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')) and (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'ecmp')):
                            pass
                            yield '         neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send ecmp limit '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                            yield '\n'
                        elif (environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send') == 'limit'):
                            pass
                            if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit')):
                                pass
                                yield '         neighbor '
                                yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                                yield ' additional-paths send limit '
                                yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send_limit'))
                                yield '\n'
                        else:
                            pass
                            yield '         neighbor '
                            yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                            yield ' additional-paths send '
                            yield str(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'send'))
                            yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag in '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag out discard '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                        yield '\n'
                l_2_neighbor = missing
                for l_2_network in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'networks'), 'prefix'):
                    l_2_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_network_cli = str_join(('network ', environment.getattr(l_2_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_2_network_cli
                    if t_6(environment.getattr(l_2_network, 'route_map')):
                        pass
                        l_2_network_cli = str_join(((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli), ' route-map ', environment.getattr(l_2_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_2_network_cli
                    yield '         '
                    yield str((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli))
                    yield '\n'
                l_2_network = l_2_network_cli = missing
                if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'redistribute_internal'), True):
                    pass
                    yield '         bgp redistribute-internal\n'
                elif t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'bgp'), 'redistribute_internal'), False):
                    pass
                    yield '         no bgp redistribute-internal\n'
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'redistribute')):
                    pass
                    l_1_redistribute_var = environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6'), 'redistribute')
                    _loop_vars['redistribute_var'] = l_1_redistribute_var
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'enabled'), True):
                        pass
                        l_1_redistribute_host = 'redistribute attached-host'
                        _loop_vars['redistribute_host'] = l_1_redistribute_host
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map')):
                            pass
                            l_1_redistribute_host = str_join(((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'attached_host'), 'route_map'), ))
                            _loop_vars['redistribute_host'] = l_1_redistribute_host
                        yield '         '
                        yield str((undefined(name='redistribute_host') if l_1_redistribute_host is missing else l_1_redistribute_host))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'enabled'), True):
                        pass
                        l_1_redistribute_bgp = 'redistribute bgp leaked'
                        _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map')):
                            pass
                            l_1_redistribute_bgp = str_join(((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'bgp'), 'route_map'), ))
                            _loop_vars['redistribute_bgp'] = l_1_redistribute_bgp
                        yield '         '
                        yield str((undefined(name='redistribute_bgp') if l_1_redistribute_bgp is missing else l_1_redistribute_bgp))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dhcp'), 'enabled'), True):
                        pass
                        l_1_redistribute_dhcp = 'redistribute dhcp'
                        _loop_vars['redistribute_dhcp'] = l_1_redistribute_dhcp
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dhcp'), 'route_map')):
                            pass
                            l_1_redistribute_dhcp = str_join(((undefined(name='redistribute_dhcp') if l_1_redistribute_dhcp is missing else l_1_redistribute_dhcp), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dhcp'), 'route_map'), ))
                            _loop_vars['redistribute_dhcp'] = l_1_redistribute_dhcp
                        yield '         '
                        yield str((undefined(name='redistribute_dhcp') if l_1_redistribute_dhcp is missing else l_1_redistribute_dhcp))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                        pass
                        l_1_redistribute_conn = 'redistribute connected'
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' include leaked', ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'rcf'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        yield '         '
                        yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'enabled'), True):
                        pass
                        l_1_redistribute_dynamic = 'redistribute dynamic'
                        _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map')):
                            pass
                            l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'route_map'), ))
                            _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf')):
                            pass
                            l_1_redistribute_dynamic = str_join(((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'dynamic'), 'rcf'), ))
                            _loop_vars['redistribute_dynamic'] = l_1_redistribute_dynamic
                        yield '         '
                        yield str((undefined(name='redistribute_dynamic') if l_1_redistribute_dynamic is missing else l_1_redistribute_dynamic))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'enabled'), True):
                        pass
                        l_1_redistribute_user = 'redistribute user'
                        _loop_vars['redistribute_user'] = l_1_redistribute_user
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf')):
                            pass
                            l_1_redistribute_user = str_join(((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'user'), 'rcf'), ))
                            _loop_vars['redistribute_user'] = l_1_redistribute_user
                        yield '         '
                        yield str((undefined(name='redistribute_user') if l_1_redistribute_user is missing else l_1_redistribute_user))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                        pass
                        l_1_redistribute_isis = 'redistribute isis'
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        yield '         '
                        yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' include leaked', ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                        pass
                        l_1_redistribute_static = 'redistribute static'
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' include leaked', ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'rcf'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        yield '         '
                        yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                        yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast')):
                pass
                yield '      !\n      address-family ipv6 multicast\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action')):
                    pass
                    yield '         bgp missing-policy direction in action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_in_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action')):
                    pass
                    yield '         bgp missing-policy direction out action '
                    yield str(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'missing_policy'), 'direction_out_action'))
                    yield '\n'
                if t_6(environment.getattr(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'bgp'), 'additional_paths'), 'receive'), True):
                    pass
                    yield '         bgp additional-paths receive\n'
                for l_2_neighbor in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'neighbors'), 'ip_address'):
                    _loop_vars = {}
                    pass
                    if t_6(environment.getattr(l_2_neighbor, 'activate'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' activate\n'
                    if t_6(environment.getattr(environment.getattr(l_2_neighbor, 'additional_paths'), 'receive'), True):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' additional-paths receive\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_in'))
                        yield ' in\n'
                    if t_6(environment.getattr(l_2_neighbor, 'route_map_out')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' route-map '
                        yield str(environment.getattr(l_2_neighbor, 'route_map_out'))
                        yield ' out\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_in')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag in '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_in'))
                        yield '\n'
                    if t_6(environment.getattr(l_2_neighbor, 'peer_tag_out_discard')):
                        pass
                        yield '         neighbor '
                        yield str(environment.getattr(l_2_neighbor, 'ip_address'))
                        yield ' peer-tag out discard '
                        yield str(environment.getattr(l_2_neighbor, 'peer_tag_out_discard'))
                        yield '\n'
                l_2_neighbor = missing
                for l_2_network in t_3(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'networks'), 'prefix'):
                    l_2_network_cli = missing
                    _loop_vars = {}
                    pass
                    l_2_network_cli = str_join(('network ', environment.getattr(l_2_network, 'prefix'), ))
                    _loop_vars['network_cli'] = l_2_network_cli
                    if t_6(environment.getattr(l_2_network, 'route_map')):
                        pass
                        l_2_network_cli = str_join(((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli), ' route-map ', environment.getattr(l_2_network, 'route_map'), ))
                        _loop_vars['network_cli'] = l_2_network_cli
                    yield '         '
                    yield str((undefined(name='network_cli') if l_2_network_cli is missing else l_2_network_cli))
                    yield '\n'
                l_2_network = l_2_network_cli = missing
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'redistribute')):
                    pass
                    l_1_redistribute_var = environment.getattr(environment.getattr(l_1_vrf, 'address_family_ipv6_multicast'), 'redistribute')
                    _loop_vars['redistribute_var'] = l_1_redistribute_var
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'enabled'), True):
                        pass
                        l_1_redistribute_conn = 'redistribute connected'
                        _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map')):
                            pass
                            l_1_redistribute_conn = str_join(((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'connected'), 'route_map'), ))
                            _loop_vars['redistribute_conn'] = l_1_redistribute_conn
                        yield '         '
                        yield str((undefined(name='redistribute_conn') if l_1_redistribute_conn is missing else l_1_redistribute_conn))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'enabled'), True):
                        pass
                        l_1_redistribute_isis = 'redistribute isis'
                        _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'isis_level'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'include_leaked'), True):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' include leaked', ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'route_map'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        elif t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf')):
                            pass
                            l_1_redistribute_isis = str_join(((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis), ' rcf ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'isis'), 'rcf'), ))
                            _loop_vars['redistribute_isis'] = l_1_redistribute_isis
                        yield '         '
                        yield str((undefined(name='redistribute_isis') if l_1_redistribute_isis is missing else l_1_redistribute_isis))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf = 'redistribute ospf match internal'
                        _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospf = str_join(((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospf'] = l_1_redistribute_ospf
                        yield '         '
                        yield str((undefined(name='redistribute_ospf') if l_1_redistribute_ospf is missing else l_1_redistribute_ospf))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    elif t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3 = 'redistribute ospfv3 match internal'
                        _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3 = str_join(((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_internal'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3'] = l_1_redistribute_ospfv3
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3') if l_1_redistribute_ospfv3 is missing else l_1_redistribute_ospfv3))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospfv3_match = 'redistribute ospfv3 match nssa-external'
                        _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospfv3_match = str_join(((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospfv3'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospfv3_match'] = l_1_redistribute_ospfv3_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospfv3_match') if l_1_redistribute_ospfv3_match is missing else l_1_redistribute_ospfv3_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'enabled'), True):
                        pass
                        l_1_redistribute_ospf_match = 'redistribute ospf match nssa-external'
                        _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'nssa_type'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        if t_6(environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map')):
                            pass
                            l_1_redistribute_ospf_match = str_join(((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match), ' route-map ', environment.getattr(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'ospf'), 'match_nssa_external'), 'route_map'), ))
                            _loop_vars['redistribute_ospf_match'] = l_1_redistribute_ospf_match
                        yield '         '
                        yield str((undefined(name='redistribute_ospf_match') if l_1_redistribute_ospf_match is missing else l_1_redistribute_ospf_match))
                        yield '\n'
                    if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'enabled'), True):
                        pass
                        l_1_redistribute_static = 'redistribute static'
                        _loop_vars['redistribute_static'] = l_1_redistribute_static
                        if t_6(environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map')):
                            pass
                            l_1_redistribute_static = str_join(((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static), ' route-map ', environment.getattr(environment.getattr((undefined(name='redistribute_var') if l_1_redistribute_var is missing else l_1_redistribute_var), 'static'), 'route_map'), ))
                            _loop_vars['redistribute_static'] = l_1_redistribute_static
                        yield '         '
                        yield str((undefined(name='redistribute_static') if l_1_redistribute_static is missing else l_1_redistribute_static))
                        yield '\n'
            if t_6(environment.getattr(l_1_vrf, 'evpn_multicast'), True):
                pass
                yield '      evpn multicast\n'
                if t_6(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'algorithm')):
                    pass
                    if (environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'algorithm') == 'preference'):
                        pass
                        if t_6(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'preference_value')):
                            pass
                            yield '         gateway dr election algorithm preference '
                            yield str(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'preference_value'))
                            yield '\n'
                    else:
                        pass
                        yield '         gateway dr election algorithm '
                        yield str(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_gateway_dr_election'), 'algorithm'))
                        yield '\n'
                if (t_6(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_address_family'), 'ipv4')) and t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_address_family'), 'ipv4'), 'transit'), True)):
                    pass
                    yield '         address-family ipv4\n'
                    if t_6(environment.getattr(environment.getattr(environment.getattr(l_1_vrf, 'evpn_multicast_address_family'), 'ipv4'), 'transit'), True):
                        pass
                        yield '            transit\n'
            if t_6(environment.getattr(l_1_vrf, 'eos_cli')):
                pass
                yield '      !\n      '
                yield str(t_4(environment.getattr(l_1_vrf, 'eos_cli'), 6, False))
                yield '\n'
        l_1_vrf = l_1_paths_cli = l_1_redistribute_var = l_1_redistribute_conn = l_1_redistribute_isis = l_1_redistribute_ospf = l_1_redistribute_ospf_match = l_1_redistribute_ospfv3 = l_1_redistribute_ospfv3_match = l_1_redistribute_static = l_1_redistribute_rip = l_1_redistribute_host = l_1_redistribute_dynamic = l_1_redistribute_bgp = l_1_redistribute_user = l_1_redistribute_dhcp = missing
        for l_1_session_tracker in t_3(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'session_trackers'), 'name'):
            _loop_vars = {}
            pass
            yield '   session tracker '
            yield str(environment.getattr(l_1_session_tracker, 'name'))
            yield '\n'
            if t_6(environment.getattr(l_1_session_tracker, 'recovery_delay')):
                pass
                yield '      recovery delay '
                yield str(environment.getattr(l_1_session_tracker, 'recovery_delay'))
                yield ' seconds\n'
        l_1_session_tracker = missing
        if t_6(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'eos_cli')):
            pass
            yield '   !\n   '
            yield str(t_4(environment.getattr((undefined(name='router_bgp') if l_0_router_bgp is missing else l_0_router_bgp), 'eos_cli'), 3, False))
            yield '\n'

blocks = {}
debug_info = '7=85&9=88&10=90&11=93&13=95&14=98&16=100&19=103&22=106&24=109&27=112&29=115&32=118&33=120&34=123&35=125&37=128&38=130&39=132&41=135&42=137&45=141&47=143&48=145&49=148&50=150&52=154&54=156&55=158&56=161&58=163&59=166&63=169&64=172&66=174&68=177&69=179&70=182&71=184&75=187&76=189&77=192&78=194&80=198&82=200&83=202&84=205&85=207&87=211&89=213&90=217&92=220&95=223&98=226&99=228&101=231&102=234&103=236&104=238&105=241&108=246&111=248&113=250&112=254&114=258&115=260&116=262&118=264&119=266&120=268&121=270&122=272&124=275&127=278&130=281&132=284&133=287&135=289&136=301&137=303&138=306&140=310&141=313&143=315&144=318&146=320&147=323&149=325&150=328&152=330&153=332&154=334&155=336&156=338&157=340&160=343&161=345&162=348&164=350&165=353&167=355&168=358&170=360&171=363&173=367&174=370&176=374&177=377&179=379&180=382&182=386&183=389&184=391&187=394&190=402&191=405&193=409&194=411&195=413&196=415&198=418&200=420&201=422&202=424&203=426&205=429&206=431&207=433&208=436&210=438&211=441&213=445&214=448&216=452&217=455&219=457&220=460&222=464&223=467&225=471&226=474&228=478&229=481&231=485&232=488&234=492&235=495&237=501&238=503&239=505&240=507&242=509&243=511&245=514&247=516&248=519&249=521&250=524&252=528&253=530&254=532&255=534&257=536&258=538&260=541&262=543&263=545&264=550&265=552&266=554&267=556&268=558&269=560&270=562&271=564&273=566&274=568&276=570&277=572&280=574&281=577&285=580&286=583&288=587&289=590&291=594&292=596&293=598&294=600&296=603&298=605&299=607&300=609&301=611&303=614&304=616&305=619&308=622&309=633&310=636&312=640&313=643&315=647&316=650&318=652&319=655&321=657&322=660&324=662&325=664&326=666&327=668&328=670&329=672&332=675&333=677&334=680&336=682&337=685&339=687&340=690&342=692&343=695&345=699&346=702&348=706&349=709&351=711&352=714&354=718&355=721&356=723&359=726&361=734&362=737&364=739&365=742&367=746&368=748&369=750&370=752&372=755&374=757&375=759&376=761&377=763&379=766&380=768&381=770&382=773&384=775&385=778&387=782&388=785&390=789&391=792&392=794&393=797&395=799&396=802&398=806&399=809&401=813&402=816&404=820&405=823&407=827&408=830&410=836&411=839&413=843&414=845&415=847&416=849&418=851&419=853&421=856&423=858&424=861&425=863&426=866&428=870&429=872&430=874&431=876&433=878&434=880&436=883&438=885&439=887&440=892&441=894&442=896&443=898&444=900&445=902&446=904&447=906&449=908&450=910&452=912&453=914&456=916&457=919&461=922&462=925&464=929&465=932&467=936&468=938&469=940&470=942&472=945&474=947&475=949&476=951&477=953&479=956&480=958&481=961&484=964&486=967&489=970&490=974&491=976&492=978&494=980&495=982&497=984&498=986&500=988&501=990&503=992&504=994&506=997&508=1000&509=1002&510=1005&511=1007&512=1010&513=1012&515=1015&516=1017&517=1020&518=1022&520=1026&522=1028&523=1030&524=1033&525=1035&527=1038&528=1040&530=1043&531=1045&532=1048&533=1050&535=1054&537=1056&538=1058&539=1061&540=1063&542=1066&543=1068&545=1072&546=1074&547=1076&548=1079&549=1081&551=1084&552=1086&554=1090&556=1092&557=1094&558=1097&559=1099&561=1102&562=1104&564=1108&566=1110&567=1112&568=1115&569=1117&571=1120&572=1122&574=1125&575=1127&577=1131&579=1133&580=1135&581=1138&582=1140&584=1143&585=1145&587=1149&588=1151&589=1153&590=1156&591=1158&593=1161&594=1163&596=1167&598=1169&599=1171&600=1174&601=1176&603=1179&604=1181&606=1185&608=1187&609=1189&610=1192&611=1194&613=1197&614=1199&616=1202&617=1204&619=1208&621=1210&622=1212&623=1215&624=1217&626=1220&627=1222&628=1225&629=1227&631=1231&633=1233&634=1235&635=1238&636=1240&638=1244&640=1246&641=1248&642=1251&643=1253&645=1257&647=1259&648=1261&649=1264&650=1266&651=1269&652=1271&654=1275&656=1277&657=1279&658=1282&659=1284&661=1288&663=1290&664=1292&665=1295&666=1297&668=1301&671=1303&672=1306&673=1309&674=1315&675=1318&679=1325&680=1327&682=1331&683=1333&684=1336&686=1338&687=1341&689=1345&690=1349&692=1352&693=1356&695=1359&696=1363&698=1366&699=1370&701=1375&702=1379&704=1384&705=1388&707=1393&708=1397&710=1400&711=1404&713=1407&715=1410&720=1413&721=1415&723=1419&724=1422&725=1424&726=1427&728=1429&729=1432&731=1434&734=1437&737=1440&738=1443&740=1445&741=1448&743=1451&744=1453&751=1459&753=1463&754=1465&755=1468&757=1470&758=1473&760=1477&761=1481&763=1484&764=1488&766=1491&767=1495&769=1498&770=1502&772=1507&773=1511&775=1516&776=1520&778=1525&779=1529&781=1532&782=1536&784=1540&785=1542&787=1545&792=1548&795=1551&798=1554&801=1557&804=1560&805=1562&807=1565&808=1568&809=1570&810=1572&811=1575&814=1580&817=1582&820=1585&821=1587&822=1590&823=1592&825=1596&827=1598&828=1600&829=1603&830=1606&831=1608&832=1609&833=1611&834=1612&835=1614&838=1616&839=1619&842=1621&843=1626&844=1629&845=1631&846=1634&848=1636&849=1639&851=1641&852=1644&854=1648&855=1651&857=1655&858=1658&860=1662&861=1665&863=1669&864=1671&865=1673&866=1675&867=1677&868=1679&870=1682&872=1684&873=1686&874=1689&875=1691&876=1694&877=1698&878=1700&879=1703&882=1710&885=1714&886=1717&888=1721&889=1724&891=1728&892=1730&893=1732&894=1734&896=1737&898=1739&899=1742&902=1745&903=1750&904=1753&905=1755&906=1758&908=1760&909=1763&911=1765&912=1768&914=1772&915=1775&917=1779&918=1782&920=1786&921=1789&923=1793&924=1795&925=1797&926=1799&927=1801&928=1803&930=1806&932=1808&933=1810&934=1813&935=1815&936=1818&937=1822&938=1824&939=1827&942=1834&945=1838&946=1841&948=1845&949=1848&951=1852&952=1854&953=1856&954=1858&956=1861&959=1864&960=1867&962=1869&963=1872&965=1874&968=1877&971=1880&972=1882&973=1885&974=1887&976=1891&978=1893&980=1896&981=1898&982=1901&983=1903&985=1906&986=1908&988=1911&989=1913&991=1916&992=1919&995=1921&996=1923&997=1926&998=1928&1000=1932&1002=1934&1005=1937&1007=1941&1008=1943&1009=1946&1011=1948&1012=1951&1017=1954&1020=1957&1021=1960&1023=1962&1024=1965&1026=1967&1027=1970&1028=1973&1029=1975&1030=1978&1033=1981&1034=1984&1035=1987&1040=1990&1043=1993&1044=1996&1046=1998&1047=2001&1049=2003&1050=2006&1051=2009&1052=2011&1053=2014&1056=2017&1057=2020&1058=2023&1063=2026&1066=2029&1068=2032&1071=2035&1074=2038&1075=2040&1077=2043&1078=2046&1079=2048&1080=2050&1081=2053&1084=2058&1087=2060&1088=2066&1089=2069&1090=2071&1091=2074&1093=2076&1094=2079&1096=2081&1097=2084&1099=2088&1100=2091&1102=2095&1103=2098&1105=2102&1106=2105&1108=2109&1109=2112&1111=2116&1112=2119&1114=2123&1115=2125&1116=2127&1117=2129&1119=2131&1120=2133&1122=2136&1124=2138&1125=2140&1126=2143&1128=2147&1129=2149&1130=2151&1131=2153&1132=2155&1135=2159&1137=2161&1138=2163&1140=2165&1141=2168&1145=2170&1146=2172&1147=2174&1148=2176&1150=2179&1152=2181&1153=2184&1155=2188&1156=2191&1159=2196&1160=2202&1161=2205&1162=2207&1163=2210&1165=2212&1166=2215&1168=2217&1169=2220&1171=2224&1172=2227&1174=2231&1175=2234&1177=2238&1178=2241&1180=2245&1181=2248&1183=2252&1184=2255&1186=2259&1187=2261&1188=2263&1189=2265&1191=2267&1192=2269&1194=2272&1196=2274&1197=2276&1198=2279&1200=2283&1201=2285&1202=2287&1203=2289&1204=2291&1207=2295&1209=2297&1210=2299&1212=2301&1213=2304&1217=2306&1218=2308&1219=2310&1220=2312&1221=2314&1223=2317&1225=2322&1228=2324&1229=2327&1231=2331&1232=2334&1235=2339&1236=2342&1237=2345&1239=2352&1242=2355&1244=2358&1247=2361&1248=2363&1249=2366&1250=2368&1251=2371&1252=2373&1254=2377&1256=2379&1257=2381&1258=2384&1259=2386&1261=2390&1263=2392&1264=2394&1265=2397&1266=2399&1268=2402&1269=2404&1270=2407&1271=2409&1273=2413&1275=2415&1276=2417&1277=2420&1278=2422&1279=2425&1280=2427&1282=2431&1284=2433&1285=2435&1286=2438&1287=2440&1289=2444&1291=2446&1292=2448&1293=2451&1294=2453&1296=2456&1297=2458&1299=2461&1300=2463&1301=2466&1302=2468&1304=2472&1306=2474&1307=2476&1308=2479&1309=2481&1311=2484&1312=2486&1314=2490&1315=2492&1316=2494&1317=2497&1318=2499&1320=2502&1321=2504&1323=2508&1325=2510&1326=2512&1327=2515&1328=2517&1330=2520&1331=2522&1333=2526&1334=2528&1335=2530&1336=2533&1337=2535&1339=2538&1340=2540&1342=2544&1344=2546&1345=2548&1346=2551&1347=2553&1349=2556&1350=2558&1352=2562&1354=2564&1355=2566&1356=2569&1357=2571&1359=2574&1360=2576&1362=2579&1363=2581&1365=2585&1367=2587&1368=2589&1369=2592&1370=2594&1372=2597&1373=2599&1375=2603&1377=2605&1378=2607&1379=2610&1380=2612&1382=2615&1383=2617&1385=2620&1386=2622&1388=2626&1390=2628&1391=2630&1392=2633&1393=2635&1395=2639&1397=2641&1398=2643&1399=2646&1400=2648&1402=2651&1403=2653&1404=2656&1405=2658&1407=2662&1412=2664&1415=2667&1418=2670&1419=2672&1420=2677&1421=2679&1422=2681&1423=2683&1424=2685&1425=2687&1426=2689&1427=2691&1429=2693&1430=2695&1432=2697&1433=2699&1436=2701&1437=2704&1441=2707&1444=2710&1445=2712&1447=2715&1448=2718&1449=2720&1450=2722&1451=2725&1454=2730&1457=2732&1460=2735&1463=2738&1464=2740&1465=2743&1466=2746&1467=2748&1468=2749&1469=2751&1470=2753&1472=2754&1473=2756&1476=2758&1477=2761&1480=2763&1481=2767&1482=2770&1484=2775&1486=2777&1487=2780&1489=2782&1490=2785&1492=2787&1493=2790&1495=2794&1496=2797&1498=2801&1499=2804&1501=2808&1502=2811&1504=2815&1505=2818&1507=2822&1508=2824&1509=2827&1510=2829&1511=2832&1512=2836&1513=2838&1514=2841&1517=2848&1520=2852&1521=2855&1523=2857&1524=2860&1526=2862&1527=2865&1528=2869&1529=2872&1531=2876&1532=2878&1533=2880&1534=2882&1536=2885&1538=2887&1539=2889&1540=2894&1541=2896&1542=2898&1543=2900&1544=2902&1545=2904&1546=2906&1547=2908&1549=2910&1550=2912&1552=2914&1553=2916&1556=2918&1557=2921&1561=2924&1562=2927&1564=2931&1565=2934&1567=2938&1568=2941&1570=2943&1571=2946&1574=2949&1575=2953&1576=2956&1578=2961&1580=2963&1581=2966&1583=2968&1584=2971&1586=2973&1587=2976&1589=2980&1590=2983&1592=2987&1593=2990&1595=2994&1596=2997&1598=3001&1599=3004&1601=3008&1602=3010&1603=3013&1604=3015&1605=3018&1606=3022&1607=3024&1608=3027&1611=3034&1614=3038&1615=3041&1617=3043&1618=3046&1620=3048&1621=3051&1622=3055&1623=3058&1625=3062&1626=3064&1627=3066&1628=3068&1630=3071&1632=3073&1633=3075&1634=3080&1635=3082&1636=3084&1637=3086&1638=3088&1639=3090&1640=3092&1641=3094&1643=3096&1644=3098&1646=3100&1647=3102&1650=3104&1651=3107&1655=3110&1656=3113&1658=3117&1659=3120&1661=3124&1662=3127&1664=3129&1665=3132&1668=3135&1669=3137&1670=3141&1671=3143&1672=3145&1674=3148&1677=3151&1678=3153&1679=3157&1680=3159&1681=3161&1683=3164&1686=3167&1689=3170&1690=3173&1692=3175&1695=3178&1696=3180&1697=3184&1698=3186&1699=3188&1701=3191&1704=3194&1705=3196&1706=3199&1707=3202&1713=3205&1716=3208&1719=3211&1720=3214&1721=3217&1722=3219&1723=3222&1725=3224&1726=3227&1728=3229&1729=3232&1731=3236&1732=3239&1734=3243&1735=3246&1737=3250&1738=3253&1741=3258&1742=3261&1743=3264&1744=3266&1745=3269&1747=3271&1748=3274&1750=3276&1751=3279&1753=3283&1754=3286&1756=3290&1757=3293&1759=3297&1760=3300&1763=3305&1764=3307&1765=3310&1766=3312&1767=3315&1768=3317&1770=3321&1772=3323&1773=3325&1774=3328&1775=3330&1777=3334&1779=3336&1780=3338&1781=3341&1782=3343&1784=3346&1785=3348&1787=3351&1788=3353&1789=3356&1790=3358&1792=3362&1794=3364&1795=3366&1796=3369&1797=3371&1799=3375&1800=3377&1801=3379&1802=3382&1803=3384&1805=3388&1807=3390&1808=3392&1809=3395&1810=3397&1812=3401&1813=3403&1814=3405&1815=3408&1816=3410&1818=3414&1820=3416&1821=3418&1822=3421&1823=3423&1825=3427&1827=3429&1828=3431&1829=3434&1830=3436&1832=3439&1833=3441&1835=3445&1837=3447&1838=3449&1839=3452&1840=3454&1842=3458&1844=3460&1845=3462&1846=3465&1847=3467&1849=3470&1850=3472&1852=3476&1854=3478&1855=3480&1856=3483&1857=3485&1859=3489&1864=3491&1867=3494&1868=3497&1869=3500&1870=3502&1871=3505&1873=3507&1874=3510&1876=3514&1877=3517&1879=3521&1880=3524&1882=3528&1883=3531&1886=3536&1887=3539&1888=3542&1889=3544&1890=3547&1892=3549&1893=3552&1895=3556&1896=3559&1898=3563&1899=3566&1901=3570&1902=3573&1907=3578&1910=3581&1912=3584&1915=3587&1918=3590&1919=3592&1921=3595&1922=3598&1923=3600&1924=3602&1925=3605&1928=3610&1931=3612&1932=3616&1933=3619&1934=3621&1935=3624&1937=3626&1938=3629&1940=3631&1941=3634&1943=3638&1944=3641&1946=3645&1947=3648&1949=3652&1950=3655&1952=3659&1953=3662&1955=3666&1956=3669&1958=3673&1959=3675&1960=3678&1962=3682&1963=3684&1964=3686&1965=3688&1966=3690&1969=3694&1971=3696&1972=3698&1974=3700&1975=3703&1979=3705&1980=3708&1982=3712&1983=3715&1986=3720&1987=3724&1988=3727&1989=3729&1990=3732&1992=3734&1993=3737&1995=3739&1996=3742&1998=3746&1999=3749&2001=3753&2002=3756&2004=3760&2005=3763&2007=3767&2008=3770&2010=3774&2011=3777&2013=3781&2014=3783&2015=3786&2017=3790&2018=3792&2019=3794&2020=3796&2021=3798&2024=3802&2026=3804&2027=3806&2029=3808&2030=3811&2034=3813&2035=3816&2037=3820&2038=3823&2041=3828&2042=3831&2043=3834&2045=3841&2048=3844&2050=3847&2053=3850&2054=3852&2055=3855&2056=3857&2057=3860&2058=3862&2060=3866&2062=3868&2063=3870&2064=3873&2065=3875&2067=3879&2069=3881&2070=3883&2071=3886&2072=3888&2074=3892&2076=3894&2077=3896&2078=3899&2079=3901&2081=3904&2082=3906&2083=3909&2084=3911&2086=3915&2088=3917&2089=3919&2090=3922&2091=3924&2092=3927&2093=3929&2095=3933&2097=3935&2098=3937&2099=3940&2100=3942&2102=3946&2104=3948&2105=3950&2106=3953&2107=3955&2109=3958&2110=3960&2112=3963&2113=3965&2114=3968&2115=3970&2117=3974&2119=3976&2120=3978&2121=3981&2122=3983&2124=3986&2125=3988&2127=3992&2128=3994&2129=3996&2130=3999&2131=4001&2133=4004&2134=4006&2136=4010&2138=4012&2139=4014&2140=4017&2141=4019&2143=4022&2144=4024&2146=4028&2148=4030&2149=4032&2150=4035&2151=4037&2153=4040&2154=4042&2156=4045&2157=4047&2159=4051&2161=4053&2162=4055&2163=4058&2164=4060&2166=4063&2167=4065&2168=4068&2169=4070&2171=4074&2176=4076&2179=4079&2180=4082&2182=4084&2183=4087&2185=4089&2188=4092&2189=4095&2190=4098&2191=4100&2192=4103&2194=4105&2195=4108&2198=4111&2199=4114&2200=4117&2202=4119&2203=4122&2205=4124&2206=4127&2208=4131&2209=4134&2211=4138&2212=4141&2214=4145&2215=4148&2218=4153&2219=4157&2220=4159&2221=4161&2223=4164&2225=4167&2226=4169&2227=4172&2228=4174&2229=4177&2230=4179&2232=4183&2234=4185&2235=4187&2236=4190&2237=4192&2239=4195&2240=4197&2242=4200&2243=4202&2244=4205&2245=4207&2247=4211&2249=4213&2250=4215&2251=4218&2252=4220&2254=4224&2255=4226&2256=4228&2257=4231&2258=4233&2260=4237&2262=4239&2263=4241&2264=4244&2265=4246&2267=4250&2268=4252&2269=4254&2270=4257&2271=4259&2273=4263&2275=4265&2276=4267&2277=4270&2278=4272&2280=4276&2282=4278&2283=4280&2284=4283&2285=4285&2287=4288&2288=4290&2290=4294&2292=4296&2293=4298&2294=4301&2295=4303&2297=4307&2299=4309&2300=4311&2301=4314&2302=4316&2304=4319&2305=4321&2307=4325&2309=4327&2310=4329&2311=4332&2312=4334&2314=4338&2319=4340&2322=4343&2323=4346&2324=4349&2325=4351&2326=4354&2328=4356&2329=4359&2331=4363&2332=4366&2334=4370&2335=4373&2337=4377&2338=4380&2341=4385&2342=4388&2343=4391&2344=4393&2345=4396&2347=4398&2348=4401&2350=4405&2351=4408&2353=4412&2354=4415&2356=4419&2357=4422&2362=4427&2365=4430&2366=4433&2368=4435&2369=4438&2371=4440&2372=4443&2373=4446&2374=4448&2375=4451&2377=4453&2378=4456&2380=4460&2381=4463&2384=4468&2385=4471&2386=4474&2388=4476&2389=4479&2391=4483&2392=4486&2395=4491&2396=4493&2399=4496&2400=4498&2401=4501&2402=4503&2404=4506&2405=4508&2407=4512&2412=4514&2415=4517&2418=4520&2419=4522&2421=4525&2422=4528&2423=4530&2424=4532&2425=4535&2428=4540&2431=4542&2432=4545&2433=4548&2434=4550&2435=4553&2437=4555&2438=4558&2440=4560&2441=4562&2442=4565&2443=4567&2444=4569&2445=4572&2446=4576&2447=4579&2450=4586&2454=4591&2455=4594&2456=4597&2457=4599&2458=4602&2460=4604&2461=4607&2463=4609&2464=4611&2465=4614&2466=4616&2467=4619&2468=4623&2469=4625&2470=4628&2473=4635&2479=4640&2482=4643&2483=4646&2484=4649&2485=4651&2486=4654&2488=4656&2489=4658&2490=4661&2492=4666&2495=4668&2496=4671&2501=4674&2504=4677&2505=4681&2506=4684&2507=4686&2508=4689&2510=4691&2511=4694&2513=4698&2514=4701&2516=4705&2517=4708&2519=4712&2520=4715&2522=4719&2523=4721&2524=4723&2525=4725&2526=4727&2527=4729&2529=4732&2531=4734&2532=4737&2534=4741&2535=4744&2538=4749&2539=4753&2540=4756&2541=4758&2542=4761&2544=4763&2545=4766&2547=4770&2548=4773&2550=4777&2551=4780&2553=4784&2554=4787&2556=4791&2557=4793&2558=4795&2559=4797&2560=4799&2561=4801&2563=4804&2565=4806&2566=4809&2568=4813&2569=4816&2572=4821&2573=4824&2575=4826&2576=4829&2578=4831&2583=4834&2586=4837&2587=4841&2588=4844&2589=4846&2590=4849&2592=4851&2593=4854&2595=4858&2596=4861&2598=4865&2599=4868&2601=4872&2602=4875&2604=4879&2605=4881&2606=4883&2607=4885&2608=4887&2609=4889&2611=4892&2613=4894&2614=4897&2616=4901&2617=4904&2620=4909&2621=4913&2622=4916&2623=4918&2624=4921&2626=4923&2627=4926&2629=4930&2630=4933&2632=4937&2633=4940&2635=4944&2636=4947&2638=4951&2639=4953&2640=4955&2641=4957&2642=4959&2643=4961&2645=4964&2647=4966&2648=4969&2650=4973&2651=4976&2654=4981&2655=4984&2657=4986&2658=4989&2660=4991&2665=4994&2667=5013&2668=5015&2669=5018&2671=5020&2672=5022&2673=5026&2674=5028&2675=5030&2677=5032&2678=5034&2679=5036&2680=5038&2682=5041&2685=5044&2686=5046&2687=5049&2688=5053&2690=5058&2691=5060&2692=5062&2693=5065&2695=5074&2698=5078&2699=5081&2704=5086&2705=5088&2706=5091&2707=5095&2709=5100&2710=5102&2711=5104&2712=5107&2714=5116&2717=5120&2718=5123&2723=5128&2724=5131&2726=5133&2729=5136&2732=5139&2733=5142&2735=5144&2736=5146&2737=5149&2739=5151&2740=5154&2744=5157&2745=5159&2746=5161&2747=5163&2749=5166&2751=5168&2753=5171&2756=5174&2759=5177&2760=5179&2762=5182&2763=5185&2764=5187&2765=5189&2766=5192&2769=5197&2772=5199&2774=5201&2773=5205&2775=5209&2776=5211&2777=5213&2779=5215&2780=5217&2781=5219&2782=5221&2783=5223&2785=5226&2788=5229&2789=5240&2790=5243&2792=5247&2793=5250&2795=5254&2796=5257&2798=5259&2799=5262&2801=5264&2802=5267&2804=5269&2805=5271&2806=5273&2807=5275&2808=5277&2809=5279&2812=5282&2813=5284&2814=5287&2816=5289&2817=5292&2819=5294&2820=5297&2822=5299&2823=5302&2825=5306&2826=5309&2828=5313&2829=5316&2831=5318&2832=5321&2834=5325&2835=5328&2836=5330&2839=5333&2841=5341&2842=5344&2844=5346&2845=5349&2847=5353&2848=5355&2849=5357&2850=5359&2852=5362&2854=5364&2855=5366&2856=5368&2857=5370&2859=5373&2860=5375&2861=5377&2862=5380&2864=5382&2865=5384&2866=5386&2867=5388&2869=5391&2871=5393&2872=5396&2873=5398&2874=5401&2876=5403&2877=5406&2879=5410&2880=5413&2882=5417&2883=5420&2885=5422&2886=5424&2887=5427&2888=5429&2889=5432&2890=5436&2891=5438&2892=5441&2895=5448&2898=5452&2899=5455&2901=5459&2902=5462&2904=5466&2905=5468&2906=5470&2907=5472&2909=5474&2910=5476&2912=5479&2914=5481&2915=5484&2916=5486&2917=5489&2919=5493&2920=5495&2921=5497&2922=5499&2924=5501&2925=5503&2927=5506&2929=5508&2930=5511&2932=5515&2933=5518&2935=5522&2936=5524&2937=5526&2938=5528&2940=5531&2941=5533&2942=5536&2945=5539&2946=5542&2947=5545&2949=5552&2952=5555&2954=5558&2957=5561&2958=5565&2959=5567&2960=5569&2962=5571&2963=5573&2965=5575&2966=5577&2968=5579&2969=5581&2971=5583&2972=5585&2974=5588&2976=5591&2977=5593&2978=5595&2979=5597&2980=5599&2981=5601&2983=5603&2984=5605&2985=5607&2986=5609&2988=5612&2990=5614&2991=5616&2992=5618&2993=5620&2995=5622&2996=5624&2998=5626&2999=5628&3000=5630&3001=5632&3003=5635&3005=5637&3006=5639&3007=5641&3008=5643&3010=5645&3011=5647&3013=5650&3014=5652&3015=5654&3016=5656&3017=5658&3019=5660&3020=5662&3022=5665&3024=5667&3025=5669&3026=5671&3027=5673&3029=5675&3030=5677&3032=5680&3034=5682&3035=5684&3036=5686&3037=5688&3039=5690&3040=5692&3042=5694&3043=5696&3045=5699&3047=5701&3048=5703&3049=5705&3050=5707&3052=5709&3053=5711&3055=5714&3056=5716&3057=5718&3058=5720&3059=5722&3061=5724&3062=5726&3064=5729&3066=5731&3067=5733&3068=5735&3069=5737&3071=5739&3072=5741&3074=5744&3076=5746&3077=5748&3078=5750&3079=5752&3081=5754&3082=5756&3084=5758&3085=5760&3087=5763&3089=5765&3090=5767&3091=5769&3092=5771&3094=5773&3095=5775&3096=5777&3097=5779&3099=5782&3101=5784&3102=5786&3103=5788&3104=5790&3106=5793&3108=5795&3109=5797&3110=5799&3111=5801&3113=5804&3115=5806&3116=5808&3117=5810&3118=5812&3119=5814&3120=5816&3122=5819&3124=5821&3125=5823&3126=5825&3127=5827&3129=5830&3131=5832&3132=5834&3133=5836&3134=5838&3136=5841&3139=5843&3140=5846&3141=5849&3142=5855&3143=5858&3146=5865&3149=5868&3150=5871&3152=5873&3153=5876&3155=5878&3156=5881&3157=5884&3161=5887&3164=5890&3165=5893&3167=5895&3168=5898&3170=5900&3171=5903&3172=5906&3176=5909&3179=5912&3181=5915&3184=5918&3185=5921&3187=5923&3188=5926&3190=5928&3193=5931&3194=5933&3196=5936&3197=5939&3198=5941&3199=5943&3200=5946&3203=5951&3206=5953&3207=5957&3208=5960&3210=5962&3211=5965&3213=5967&3214=5970&3216=5974&3217=5977&3219=5981&3220=5984&3222=5988&3223=5991&3225=5995&3226=5998&3228=6002&3229=6005&3231=6009&3232=6011&3233=6014&3234=6016&3235=6019&3236=6023&3237=6025&3238=6028&3241=6035&3244=6039&3245=6041&3246=6043&3247=6045&3248=6047&3250=6050&3252=6055&3255=6057&3256=6060&3258=6064&3259=6067&3262=6072&3263=6076&3264=6078&3265=6080&3267=6083&3269=6086&3271=6089&3274=6092&3275=6094&3276=6096&3277=6098&3278=6100&3279=6102&3281=6105&3283=6107&3284=6109&3285=6111&3286=6113&3288=6116&3290=6118&3291=6120&3292=6122&3293=6124&3295=6126&3296=6128&3297=6130&3298=6132&3300=6135&3302=6137&3303=6139&3304=6141&3305=6143&3306=6145&3307=6147&3309=6150&3311=6152&3312=6154&3313=6156&3314=6158&3316=6161&3318=6163&3319=6165&3320=6167&3321=6169&3323=6171&3324=6173&3326=6175&3327=6177&3328=6179&3329=6181&3331=6184&3333=6186&3334=6188&3335=6190&3336=6192&3338=6194&3339=6196&3341=6199&3342=6201&3343=6203&3344=6205&3345=6207&3347=6209&3348=6211&3350=6214&3352=6216&3353=6218&3354=6220&3355=6222&3357=6224&3358=6226&3360=6229&3361=6231&3362=6233&3363=6235&3364=6237&3366=6239&3367=6241&3369=6244&3371=6246&3372=6248&3373=6250&3374=6252&3376=6254&3377=6256&3379=6259&3381=6261&3382=6263&3383=6265&3384=6267&3386=6269&3387=6271&3389=6273&3390=6275&3392=6278&3394=6280&3395=6282&3396=6284&3397=6286&3399=6288&3400=6290&3402=6293&3404=6295&3405=6297&3406=6299&3407=6301&3409=6303&3410=6305&3412=6307&3413=6309&3415=6312&3417=6314&3418=6316&3419=6318&3420=6320&3422=6323&3424=6325&3425=6327&3426=6329&3427=6331&3429=6333&3430=6335&3431=6337&3432=6339&3434=6342&3438=6344&3441=6347&3442=6350&3444=6352&3445=6355&3447=6357&3450=6360&3451=6363&3452=6366&3454=6368&3455=6371&3457=6373&3458=6376&3460=6380&3461=6383&3463=6387&3464=6390&3466=6394&3467=6397&3470=6402&3471=6406&3472=6408&3473=6410&3475=6413&3477=6416&3478=6418&3479=6420&3480=6422&3481=6424&3482=6426&3484=6429&3486=6431&3487=6433&3488=6435&3489=6437&3491=6440&3493=6442&3494=6444&3495=6446&3496=6448&3498=6450&3499=6452&3501=6454&3502=6456&3503=6458&3504=6460&3506=6463&3508=6465&3509=6467&3510=6469&3511=6471&3513=6474&3514=6476&3515=6478&3516=6480&3517=6482&3519=6485&3521=6487&3522=6489&3523=6491&3524=6493&3526=6496&3527=6498&3528=6500&3529=6502&3530=6504&3532=6507&3534=6509&3535=6511&3536=6513&3537=6515&3539=6518&3541=6520&3542=6522&3543=6524&3544=6526&3546=6528&3547=6530&3549=6533&3551=6535&3552=6537&3553=6539&3554=6541&3556=6544&3558=6546&3559=6548&3560=6550&3561=6552&3563=6554&3564=6556&3566=6559&3568=6561&3569=6563&3570=6565&3571=6567&3573=6570&3577=6572&3580=6575&3582=6578&3585=6581&3586=6584&3588=6586&3589=6589&3591=6591&3594=6594&3595=6596&3597=6599&3598=6602&3599=6604&3600=6606&3601=6609&3604=6614&3607=6616&3608=6619&3609=6622&3611=6624&3612=6627&3614=6629&3615=6632&3617=6636&3618=6639&3620=6643&3621=6646&3623=6650&3624=6653&3626=6657&3627=6660&3629=6664&3630=6667&3632=6671&3633=6673&3634=6676&3635=6678&3636=6681&3637=6685&3638=6687&3639=6690&3642=6697&3645=6701&3646=6704&3648=6708&3649=6711&3652=6716&3653=6720&3654=6722&3655=6724&3657=6727&3659=6730&3661=6733&3664=6736&3665=6738&3666=6740&3667=6742&3668=6744&3669=6746&3671=6749&3673=6751&3674=6753&3675=6755&3676=6757&3678=6760&3680=6762&3681=6764&3682=6766&3683=6768&3685=6771&3687=6773&3688=6775&3689=6777&3690=6779&3692=6781&3693=6783&3694=6785&3695=6787&3697=6790&3699=6792&3700=6794&3701=6796&3702=6798&3703=6800&3704=6802&3706=6805&3708=6807&3709=6809&3710=6811&3711=6813&3713=6816&3715=6818&3716=6820&3717=6822&3718=6824&3720=6826&3721=6828&3723=6830&3724=6832&3725=6834&3726=6836&3728=6839&3730=6841&3731=6843&3732=6845&3733=6847&3735=6849&3736=6851&3738=6854&3739=6856&3740=6858&3741=6860&3742=6862&3744=6864&3745=6866&3747=6869&3749=6871&3750=6873&3751=6875&3752=6877&3754=6879&3755=6881&3757=6884&3759=6886&3760=6888&3761=6890&3762=6892&3764=6894&3765=6896&3767=6898&3768=6900&3770=6903&3772=6905&3773=6907&3774=6909&3775=6911&3777=6913&3778=6915&3779=6917&3780=6919&3782=6922&3786=6924&3789=6927&3790=6930&3792=6932&3793=6935&3795=6937&3798=6940&3799=6943&3800=6946&3802=6948&3803=6951&3805=6953&3806=6956&3808=6960&3809=6963&3811=6967&3812=6970&3814=6974&3815=6977&3818=6982&3819=6986&3820=6988&3821=6990&3823=6993&3825=6996&3826=6998&3827=7000&3828=7002&3829=7004&3830=7006&3832=7009&3834=7011&3835=7013&3836=7015&3837=7017&3839=7019&3840=7021&3842=7023&3843=7025&3844=7027&3845=7029&3847=7032&3849=7034&3850=7036&3851=7038&3852=7040&3854=7043&3855=7045&3856=7047&3857=7049&3858=7051&3860=7054&3862=7056&3863=7058&3864=7060&3865=7062&3867=7065&3868=7067&3869=7069&3870=7071&3871=7073&3873=7076&3875=7078&3876=7080&3877=7082&3878=7084&3880=7087&3882=7089&3883=7091&3884=7093&3885=7095&3887=7097&3888=7099&3890=7102&3892=7104&3893=7106&3894=7108&3895=7110&3897=7113&3899=7115&3900=7117&3901=7119&3902=7121&3904=7123&3905=7125&3907=7128&3909=7130&3910=7132&3911=7134&3912=7136&3914=7139&3918=7141&3920=7144&3921=7146&3922=7148&3923=7151&3926=7156&3929=7158&3932=7161&3937=7164&3939=7167&3943=7170&3944=7174&3945=7176&3946=7179&3949=7182&3951=7185'