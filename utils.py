def format_summary(data: dict) -> str:
    """Generate a concise summary string from the monitoring data.
    This is a simple placeholder implementation that can be expanded.
    """
    if not data:
        return "No data available."
    # Example summary: website, status, latency, SSL days left
    website = data.get('Website', 'N/A')
    status = data.get('Final Status', 'N/A')
    latency = data.get('Avg Response Time (ms)', 'N/A')
    ssl_days = data.get('SSL Days Left', 'N/A')
    return f"{website} – Status: {status}, Latency: {latency} ms, SSL days left: {ssl_days}"
