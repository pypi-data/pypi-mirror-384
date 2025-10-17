from .schema import RedisInfo
from fastpluggy_plugin.ui_tools.extra_widget.display.card import CardWidget


def make_memory_usage_card(info: RedisInfo) -> CardWidget:
    """
    Returns a CardWidget showing:
      • used_memory_human / total_system_memory_human
      • a Bootstrap progress bar indicating percent used.
      Tooltip (via title="…") combines descriptions of used_memory_human & total_system_memory_human.
    """
    # 1) Compute percentage
    used_bytes = info.used_memory or 0
    total_bytes = info.total_system_memory or 1
    pct_used = (used_bytes / total_bytes) * 100

    # 2) Progress-bar HTML
    progress_html = f"""
      <div class="progress" style="height: 1.5rem;">
        <div
          class="progress-bar"
          role="progressbar"
          style="width: {pct_used:.1f}%;"
          aria-valuenow="{pct_used:.1f}"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          {pct_used:.1f}%
        </div>
      </div>
    """

    # 3) Build the inner content (text + progress bar)
    inner_html = f"""
      <div>
        <h3 class="text-primary" style="margin-bottom: 0.25rem;">
          {info.used_memory_human} / {info.total_system_memory_human}
        </h3>
      </div>
    """

    # 4) Pull descriptions directly from RedisInfo.model_fields
    desc_used = RedisInfo.model_fields['used_memory_human'].description or ""
    desc_total = RedisInfo.model_fields['total_system_memory_human'].description or ""
    tooltip_text = f"{desc_used} | {desc_total}"

    # 5) Wrap inner_html in a div with title="…" so the entire card body shows a tooltip
    content_html = f'<div title="{tooltip_text}">{inner_html}</div>'

    return CardWidget(
        header="Memory Usage",
        content=content_html,
    )


def get_stats_cards(info: RedisInfo):
    """
    Build twelve CardWidget objects, each using the Pydantic Field.description as a title‐tooltip.
    Footer is left empty.
    """
    f = RedisInfo.model_fields  # shorthand for field metadata

    stats_cards = [
        # CPU Load (user+sys)
        CardWidget(
            header="CPU Load (user+sys)",
            content=(
                f'<div title="{f["used_cpu_user"].description or ""} | '
                f'{f["used_cpu_sys"].description or ""}">'
                f"<h3 class='text-primary'>{info.cpu_load:.2f}</h3>"
                "</div>"
            ),

        ),

        # Memory Usage (combined card)
        make_memory_usage_card(info=info),

        # Connected Clients
        CardWidget(
            header="Connected Clients",
            content=(
                f'<div title="{f["connected_clients"].description or ""}">'
                f"<h3 class='text-primary'>{info.connected_clients}</h3>"
                "</div>"
            ),

        ),

        # Ops/Sec
        CardWidget(
            header="Ops/Sec",
            content=(
                f'<div title="{f["instantaneous_ops_per_sec"].description or ""}">'
                f"<h3 class='text-primary'>{info.instantaneous_ops_per_sec}</h3>"
                "</div>"
            ),

        ),

        # Uptime
        CardWidget(
            header="Uptime",
            content=(
                f'<div title="{f["uptime_in_seconds"].description or ""}">'
                f"<h3 class='text-primary'>{info.uptime_text}</h3>"
                "</div>"
            ),

        ),

    ]

    return stats_cards
