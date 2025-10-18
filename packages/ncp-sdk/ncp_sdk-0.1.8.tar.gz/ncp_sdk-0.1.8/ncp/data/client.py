"""Metrics API type stubs for SDK.

This module provides type hints and method signatures for the Metrics API.
The actual implementation is provided by the NCP platform at runtime.
"""

from typing import Any, Dict, List, Optional, Union

try:
    import pandas as pd
except ImportError:
    # Pandas not required for type stubs
    pd = None  # type: ignore


class Metrics:
    """Main client for querying network metrics and device data.

    NOTE: This is a type stub for IDE autocomplete and type checking.
    The actual implementation is provided by the NCP platform when your
    agent runs in production.

    Provides simple, intuitive methods for querying various types of network
    data without needing to know SQL or table schemas.

    Example:
        >>> from ncp import Metrics
        >>> metrics = Metrics()  # Works only on platform
        >>> devices = metrics.get_devices(layer="spine", is_reachable=True)
        >>> cpu = metrics.get_cpu_utilization(hostname="leaf-01", hours=24)
    """

    def __init__(
        self,
        connection_url: Optional[str] = None,
        return_format: str = "dict",
        timezone: Optional[str] = None,
    ):
        """Initialize Metrics client.

        Args:
            connection_url: Database connection URL (provided by platform)
            return_format: Default return format - "dict" or "dataframe"
            timezone: Default timezone for timestamp columns in DataFrames

        Note:
            When running locally (not on platform), this will raise NotImplementedError.
            The platform provides the real implementation at runtime.
        """
        raise NotImplementedError(
            "Metrics API is only available when running on the NCP platform. "
            "This is a type stub for IDE support during development."
        )

    def get_devices(
        self,
        hostname: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        model: Optional[str] = None,
        os_version: Optional[str] = None,
        is_reachable: Optional[bool] = None,
        vendor: Optional[str] = None,
        serial_number: Optional[str] = None,
        management_ip: Optional[str] = None,
        device_type: Optional[str] = None,
        platform: Optional[str] = None,
        status: Optional[bool] = None,
        manufacturer: Optional[str] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query device inventory with flexible filtering.

        Args:
            hostname: Filter by hostname (supports wildcards with %)
            layer: Filter by layer (e.g., "spine", "leaf", "core")
            region: Filter by region
            model: Filter by device model
            os_version: Filter by OS version
            is_reachable: Filter by reachability status
            vendor: Filter by vendor
            serial_number: Filter by serial number
            management_ip: Filter by management IP
            device_type: Filter by device type
            platform: Filter by platform
            status: Filter by status
            manufacturer: Filter by manufacturer
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of device dictionaries or pandas DataFrame

        Examples:
            >>> # Get all spine devices
            >>> spines = metrics.get_devices(layer="spine")
            >>>
            >>> # Get unreachable devices
            >>> down = metrics.get_devices(is_reachable=False)
            >>>
            >>> # Get devices with hostname pattern
            >>> leafs = metrics.get_devices(hostname="leaf%")
        """
        ...

    def get_interfaces(
        self,
        hostname: Optional[str] = None,
        interface_name: Optional[str] = None,
        admin_status: Optional[str] = None,
        oper_status: Optional[str] = None,
        speed: Optional[int] = None,
        mtu: Optional[int] = None,
        description: Optional[str] = None,
        alias: Optional[str] = None,
        fec: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query interface inventory with filtering.

        Args:
            hostname: Filter by device hostname (supports wildcards with %)
            interface_name: Filter by interface name (supports wildcards)
            admin_status: Filter by admin status ("up", "down")
            oper_status: Filter by operational status ("up", "down")
            speed: Filter by speed in Mbps
            mtu: Filter by MTU
            description: Filter by interface description (supports wildcards)
            alias: Filter by interface alias (supports wildcards)
            fec: Filter by FEC setting
            layer: Filter by device layer
            region: Filter by device region
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of interface dictionaries or pandas DataFrame

        Examples:
            >>> # Get all up interfaces
            >>> up_interfaces = metrics.get_interfaces(oper_status="up")
            >>>
            >>> # Get 10G interfaces
            >>> ten_gig = metrics.get_interfaces(speed=10000)
        """
        ...

    def get_links(
        self,
        source_hostname: Optional[str] = None,
        dest_hostname: Optional[str] = None,
        source_interface: Optional[str] = None,
        dest_interface: Optional[str] = None,
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
        source_layer: Optional[str] = None,
        dest_layer: Optional[str] = None,
        source_region: Optional[str] = None,
        dest_region: Optional[str] = None,
        status: Optional[bool] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query physical network links between devices.

        Args:
            source_hostname: Filter by source hostname (supports wildcards)
            dest_hostname: Filter by destination hostname (supports wildcards)
            source_interface: Filter by source interface name (supports wildcards)
            dest_interface: Filter by destination interface name (supports wildcards)
            source_ip: Filter by source IP address
            dest_ip: Filter by destination IP address
            source_layer: Filter by source device layer
            dest_layer: Filter by destination device layer
            source_region: Filter by source device region
            dest_region: Filter by destination device region
            status: Filter by link status (True=up, False=down)
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of link dictionaries or pandas DataFrame

        Examples:
            >>> # Get all links from spine devices
            >>> links = metrics.get_links(source_layer="spine")
            >>>
            >>> # Get down links
            >>> down_links = metrics.get_links(status=False)
        """
        ...

    def get_fans(
        self,
        hostname: Optional[str] = None,
        name: Optional[str] = None,
        status: Optional[str] = None,
        presence: Optional[str] = None,
        model: Optional[str] = None,
        serial: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query fan hardware inventory.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            name: Filter by fan name (supports wildcards)
            status: Filter by fan status
            presence: Filter by presence status
            model: Filter by fan model
            serial: Filter by serial number
            layer: Filter by device layer
            region: Filter by device region
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of fan dictionaries or pandas DataFrame

        Examples:
            >>> # Get all fans for a device
            >>> fans = metrics.get_fans(hostname="spine-01")
            >>>
            >>> # Get fans with issues
            >>> bad_fans = metrics.get_fans(status="not ok")
        """
        ...

    def get_psus(
        self,
        hostname: Optional[str] = None,
        name: Optional[str] = None,
        status: Optional[str] = None,
        presence: Optional[str] = None,
        model: Optional[str] = None,
        serial: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        temp: Optional[float] = None,
        voltage: Optional[float] = None,
        current: Optional[float] = None,
        power: Optional[float] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query PSU (Power Supply Unit) hardware inventory.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            name: Filter by PSU name (supports wildcards)
            status: Filter by PSU status
            presence: Filter by presence status
            model: Filter by PSU model
            serial: Filter by serial number
            layer: Filter by device layer
            region: Filter by device region
            temp: Filter by temperature
            voltage: Filter by voltage
            current: Filter by current
            power: Filter by power
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of PSU dictionaries or pandas DataFrame

        Examples:
            >>> # Get all PSUs for a device
            >>> psus = metrics.get_psus(hostname="spine-01")
            >>>
            >>> # Get PSUs with issues
            >>> bad_psus = metrics.get_psus(status="not ok")
        """
        ...

    def get_transceivers(
        self,
        hostname: Optional[str] = None,
        interface_name: Optional[str] = None,
        type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query transceiver (SFP/QSFP) inventory.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            interface_name: Filter by interface name (supports wildcards)
            type: Filter by transceiver type (e.g., "QSFP28", "SFP+")
            manufacturer: Filter by manufacturer (supports wildcards)
            model: Filter by model (supports wildcards)
            serial_number: Filter by serial number
            layer: Filter by device layer
            region: Filter by device region
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of transceiver dictionaries or pandas DataFrame

        Examples:
            >>> # Get all transceivers for a device
            >>> transceivers = metrics.get_transceivers(hostname="leaf-01")
            >>>
            >>> # Get QSFP28 transceivers
            >>> qsfp28 = metrics.get_transceivers(type="QSFP28")
        """
        ...

    def get_transceiver_dom(
        self,
        hostname: Optional[str] = None,
        interface_name: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query transceiver DOM (Digital Optical Monitoring) metrics.

        Returns optical monitoring data including temperature, voltage, RX/TX power,
        and bias current along with alarm/warning thresholds for transceivers.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            interface_name: Filter by interface name (supports wildcards)
            layer: Filter by device layer
            region: Filter by device region
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of transceiver DOM dictionaries or pandas DataFrame

        Examples:
            >>> # Get DOM metrics for all transceivers on a device
            >>> dom = metrics.get_transceiver_dom(hostname="leaf-01")
            >>>
            >>> # Get as DataFrame for analysis
            >>> df = metrics.get_transceiver_dom(return_format="dataframe")
            >>> hot = df[df['temperature'] > df['temp_high_warning']]
        """
        ...

    def get_firewall_policies(
        self,
        device_ip: Optional[str] = None,
        name: Optional[str] = None,
        action: Optional[str] = None,
        from_zone: Optional[str] = None,
        to_zone: Optional[str] = None,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        application: Optional[str] = None,
        disabled: Optional[bool] = None,
        rule_type: Optional[str] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query firewall security policy rules.

        Args:
            device_ip: Filter by firewall device IP (supports wildcards)
            name: Filter by policy rule name (supports wildcards)
            action: Filter by action ("allow" or "deny")
            from_zone: Filter by source security zone (supports wildcards)
            to_zone: Filter by destination security zone (supports wildcards)
            source: Filter by source address/network (supports wildcards)
            destination: Filter by destination address/network (supports wildcards)
            application: Filter by application name (supports wildcards)
            disabled: Filter by disabled status (True/False)
            rule_type: Filter by rule type (supports wildcards)
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of firewall policy dictionaries or pandas DataFrame

        Examples:
            >>> # Get all firewall policies
            >>> policies = metrics.get_firewall_policies()
            >>>
            >>> # Get deny rules
            >>> deny_rules = metrics.get_firewall_policies(action="deny")
        """
        ...

    def get_cpu_utilization(
        self,
        hostname: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query CPU utilization time-series metrics.

        Returns CPU utilization data aggregated at 5-minute intervals including
        average, minimum, and maximum utilization percentages.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            layer: Filter by device layer (e.g., "spine", "leaf", "core")
            region: Filter by device region
            start_time: Start of time range (ISO format: "2024-01-01T00:00:00")
            end_time: End of time range (ISO format: "2024-01-01T23:59:59")
            hours: Get data for last N hours (alternative to start_time/end_time)
            days: Get data for last N days (alternative to start_time/end_time)
            limit: Maximum number of results (default: 1000)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of CPU utilization dictionaries or pandas DataFrame

        Examples:
            >>> # Get last 24 hours of CPU data for a device
            >>> cpu = metrics.get_cpu_utilization(hostname="spine-01", hours=24)
            >>>
            >>> # Get as DataFrame for analysis
            >>> df = metrics.get_cpu_utilization(
            ...     hostname="leaf%",
            ...     days=7,
            ...     return_format="dataframe"
            ... )
            >>> high_cpu = df[df['avg_util'] > 80]
        """
        ...

    def get_memory_utilization(
        self,
        hostname: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query memory utilization time-series metrics.

        Returns memory utilization data aggregated at 5-minute intervals including
        average, minimum, and maximum utilization percentages.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            layer: Filter by device layer (e.g., "spine", "leaf", "core")
            region: Filter by device region
            start_time: Start of time range (ISO format: "2024-01-01T00:00:00")
            end_time: End of time range (ISO format: "2024-01-01T23:59:59")
            hours: Get data for last N hours (alternative to start_time/end_time)
            days: Get data for last N days (alternative to start_time/end_time)
            limit: Maximum number of results (default: 1000)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of memory utilization dictionaries or pandas DataFrame

        Examples:
            >>> # Get last 24 hours of memory data for a device
            >>> mem = metrics.get_memory_utilization(hostname="spine-01", hours=24)
            >>>
            >>> # Find devices with memory pressure
            >>> high_mem = metrics.get_memory_utilization(
            ...     hours=1,
            ...     min_avg_util=90.0
            ... )
        """
        ...

    def get_interface_metrics(
        self,
        hostname: Optional[str] = None,
        interface_name: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query interface counter metrics with time-series aggregation.

        Returns interface traffic and error metrics aggregated at 5-minute intervals
        including RX/TX octets, packets, errors, and discards.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            interface_name: Filter by interface name (supports wildcards)
            layer: Filter by device layer (e.g., "spine", "leaf", "core")
            region: Filter by device region
            start_time: Start of time range (ISO format: "2024-01-01T00:00:00")
            end_time: End of time range (ISO format: "2024-01-01T23:59:59")
            hours: Get data for last N hours (alternative to start_time/end_time)
            days: Get data for last N days (alternative to start_time/end_time)
            limit: Maximum number of results (default: 1000)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of interface metric dictionaries or pandas DataFrame

        Examples:
            >>> # Get metrics for specific interface
            >>> intf = metrics.get_interface_metrics(
            ...     hostname="leaf-01",
            ...     interface_name="Ethernet0",
            ...     hours=24
            ... )
            >>>
            >>> # Get as DataFrame for analysis
            >>> df = metrics.get_interface_metrics(
            ...     hostname="leaf%",
            ...     days=7,
            ...     return_format="dataframe"
            ... )
            >>> with_errors = df[df['avg_rx_errors'] > 0]
        """
        ...

    def get_syslog_events(
        self,
        hostname: Optional[str] = None,
        host: Optional[str] = None,
        severity: Optional[str] = None,
        program: Optional[str] = None,
        message: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query syslog event messages.

        Returns syslog event data including severity, program, message content,
        and timestamps.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            host: Filter by host field (supports wildcards)
            severity: Filter by severity level (e.g., "critical", "error", "warning", "info")
            program: Filter by program/daemon name (supports wildcards)
            message: Filter by message text (supports wildcards)
            start_time: Filter events after this timestamp (ISO format)
            end_time: Filter events before this timestamp (ISO format)
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of syslog event dictionaries or pandas DataFrame

        Examples:
            >>> # Get all error and critical syslog events
            >>> errors = metrics.get_syslog_events(severity="error")
            >>>
            >>> # Search for specific message text
            >>> interface_logs = metrics.get_syslog_events(message="%interface%")
        """
        ...

    def get_reboot_events(
        self,
        hostname: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query device reboot event tracking data.

        Returns reboot events showing when devices restarted, including
        previous and current uptime information.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            layer: Filter by device layer (e.g., "spine", "leaf", "core")
            region: Filter by device region
            start_time: Start of time range (ISO format)
            end_time: End of time range (ISO format)
            hours: Get data for last N hours
            days: Get data for last N days (default: 7)
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of reboot event dictionaries or pandas DataFrame

        Examples:
            >>> # Get all reboots in the last week
            >>> reboots = metrics.get_reboot_events(days=7)
            >>>
            >>> # Get reboots for specific device
            >>> device_reboots = metrics.get_reboot_events(hostname="spine-01")
        """
        ...

    def get_os_version_changes(
        self,
        hostname: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query device OS version change events.

        Returns events tracking when devices had their OS version upgraded or changed,
        including previous and current version information.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            layer: Filter by device layer
            region: Filter by device region
            start_time: Start of time range (ISO format)
            end_time: End of time range (ISO format)
            hours: Get data for last N hours
            days: Get data for last N days (default: 30)
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of OS version change event dictionaries or pandas DataFrame

        Examples:
            >>> # Get all OS version changes in the last 30 days
            >>> changes = metrics.get_os_version_changes()
            >>>
            >>> # Get OS changes for specific device
            >>> device_changes = metrics.get_os_version_changes(hostname="spine-01")
        """
        ...

    def get_interface_transitions(
        self,
        hostname: Optional[str] = None,
        interface_name: Optional[str] = None,
        layer: Optional[str] = None,
        region: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query interface status transition events.

        Returns events tracking when interfaces changed status (admin up/down,
        operational up/down), useful for detecting flapping interfaces.

        Args:
            hostname: Filter by device hostname (supports wildcards)
            interface_name: Filter by interface name (supports wildcards)
            layer: Filter by device layer
            region: Filter by device region
            start_time: Start of time range (ISO format)
            end_time: End of time range (ISO format)
            hours: Get data for last N hours
            days: Get data for last N days (default: 7)
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of interface transition event dictionaries or pandas DataFrame

        Examples:
            >>> # Get all interface transitions in the last 7 days
            >>> transitions = metrics.get_interface_transitions()
            >>>
            >>> # Get as DataFrame for flapping detection
            >>> df = metrics.get_interface_transitions(
            ...     days=30,
            ...     return_format="dataframe"
            ... )
            >>> flap_counts = df.groupby(['hostname', 'if_name']).size()
        """
        ...

    def get_link_transitions(
        self,
        source_interface: Optional[str] = None,
        dest_interface: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query link status transition events.

        Returns events tracking when physical links between devices changed status,
        useful for detecting unstable links.

        Args:
            source_interface: Filter by source interface name (supports wildcards)
            dest_interface: Filter by destination interface name (supports wildcards)
            start_time: Start of time range (ISO format)
            end_time: End of time range (ISO format)
            hours: Get data for last N hours
            days: Get data for last N days (default: 7)
            limit: Maximum number of results (default: 100)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of link transition event dictionaries or pandas DataFrame

        Examples:
            >>> # Get all link transitions in the last 7 days
            >>> transitions = metrics.get_link_transitions()
            >>>
            >>> # Get as DataFrame for flapping link detection
            >>> df = metrics.get_link_transitions(
            ...     days=30,
            ...     return_format="dataframe"
            ... )
            >>> flapping = df.groupby(['src_if_name', 'dst_if_name']).size()
        """
        ...

    def get_flow_data(
        self,
        sampler_address: Optional[str] = None,
        protocol: Optional[str] = None,
        source_ip: Optional[str] = None,
        dest_ip: Optional[str] = None,
        source_port: Optional[int] = None,
        dest_port: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        hours: Optional[int] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
        return_format: Optional[str] = None,
        index_col: Optional[Union[str, List[str]]] = None,
        timezone: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], "pd.DataFrame"]:
        """Query network flow data (NetFlow/sFlow).

        Returns network flow records showing traffic between source and destination
        IP addresses with protocol, port, byte, and packet information.

        Args:
            sampler_address: Filter by sampler/collector device address (supports wildcards)
            protocol: Filter by protocol (e.g., "TCP", "UDP", "ICMP")
            source_ip: Filter by source IP address (supports wildcards)
            dest_ip: Filter by destination IP address (supports wildcards)
            source_port: Filter by source port number
            dest_port: Filter by destination port number
            start_time: Start of time range (ISO format)
            end_time: End of time range (ISO format)
            hours: Get data for last N hours
            days: Get data for last N days (default: 1)
            limit: Maximum number of results (default: 1000)
            return_format: Output format - "dict" or "dataframe"
            index_col: Column(s) to set as index (dataframe only)
            timezone: Timezone for timestamp columns (dataframe only)

        Returns:
            List of flow record dictionaries or pandas DataFrame

        Examples:
            >>> # Get recent flow data (last 1 hour by default)
            >>> flows = metrics.get_flow_data(hours=1)
            >>>
            >>> # Get TCP flows on port 443 (HTTPS)
            >>> https_flows = metrics.get_flow_data(
            ...     protocol="TCP",
            ...     dest_port=443,
            ...     hours=24
            ... )
            >>>
            >>> # Get as DataFrame for traffic analysis
            >>> df = metrics.get_flow_data(
            ...     hours=24,
            ...     return_format="dataframe"
            ... )
            >>> top_sources = df.groupby('src_addr')['bytes'].sum().sort_values(ascending=False)
        """
        ...

    def close(self):
        """Close database connections.

        Should be called when done using the Metrics client to free resources.
        """
        ...

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes database connections."""
        self.close()
